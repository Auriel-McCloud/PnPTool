import { useCallback, useEffect, useRef, useState } from "react";
import { WikiEditor } from "./WikiEditor";
import {
  bisHierherFreigeben,
  getBaum,
  getSeite,
  seiteAnlegen,
  seiteLoeschen,
  seiteSpeichern,
  type BaumKnoten,
  type SeiteMitVerzeichnis,
} from "./api";
import "./wiki.css";

/** Wie lange nach der letzten Eingabe gespeichert wird. */
const AUTOSAVE_MS = 1200;

type Zustand = "ruhig" | "speichert" | "gespeichert" | "fehler";

function Zweig({
  knoten,
  aktiv,
  tiefe,
  onWaehlen,
}: {
  knoten: BaumKnoten;
  aktiv: string | null;
  tiefe: number;
  onWaehlen: (id: string) => void;
}) {
  // Oberste zwei Ebenen offen: der Einstieg soll den Aufbau zeigen, ohne
  // dass tiefe Kapitel die Liste überschwemmen.
  const [offen, setOffen] = useState(tiefe < 2);
  const hatKinder = knoten.kinder.length > 0;

  return (
    <div>
      <div className="wk-zweig">
        {hatKinder ? (
          <button
            type="button"
            className="wk-klapp"
            onClick={() => setOffen((o) => !o)}
            aria-label={offen ? "Zuklappen" : "Aufklappen"}
          >
            {offen ? "▼" : "▶"}
          </button>
        ) : (
          <span className="wk-klapp-leer" />
        )}
        <button
          type="button"
          className="wk-eintrag"
          aria-current={knoten.id === aktiv ? "true" : undefined}
          onClick={() => onWaehlen(knoten.id)}
          title={knoten.titel}
        >
          {knoten.symbol && <span aria-hidden="true">{knoten.symbol}</span>}
          <span className="wk-eintrag-titel">{knoten.titel}</span>
          {knoten.sichtbarkeit !== "GM" && (
            <span
              className="wk-freigabe"
              data-modus={knoten.sichtbarkeit}
              title={
                knoten.sichtbarkeit === "ALLE"
                  ? "Für die ganze Gruppe freigegeben"
                  : "Für einzelne Spieler freigegeben"
              }
            >
              {knoten.sichtbarkeit === "ALLE" ? "offen" : "teils"}
            </span>
          )}
        </button>
      </div>

      {hatKinder && offen && (
        <div className="wk-kinder">
          {knoten.kinder.map((k) => (
            <Zweig key={k.id} knoten={k} aktiv={aktiv} tiefe={tiefe + 1} onWaehlen={onWaehlen} />
          ))}
        </div>
      )}
    </div>
  );
}

export function WikiAnsicht({ campaignId, nurLesen = false }: { campaignId: string; nurLesen?: boolean }) {
  const [baum, setBaum] = useState<BaumKnoten[]>([]);
  const [aktiv, setAktiv] = useState<string | null>(null);
  const [seite, setSeite] = useState<SeiteMitVerzeichnis | null>(null);
  const [zustand, setZustand] = useState<Zustand>("ruhig");
  const [fehler, setFehler] = useState<string | null>(null);

  const speicherTimer = useRef<number | undefined>(undefined);
  // Was noch nicht geschrieben ist. Als Ref, damit ein Seitenwechsel den
  // ausstehenden Stand noch wegschreiben kann, bevor er verworfen wird.
  const offen = useRef<{ id: string; inhalt?: string; titel?: string } | null>(null);

  const baumLaden = useCallback(async () => {
    try {
      setBaum(await getBaum(campaignId));
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Seitenbaum konnte nicht geladen werden");
    }
  }, [campaignId]);

  useEffect(() => {
    baumLaden();
  }, [baumLaden]);

  // Erste Seite automatisch öffnen, damit man nicht vor einer leeren Fläche steht.
  useEffect(() => {
    if (!aktiv && baum.length > 0) setAktiv(baum[0].id);
  }, [baum, aktiv]);

  useEffect(() => {
    if (!aktiv) {
      setSeite(null);
      return;
    }
    let abgebrochen = false;
    getSeite(campaignId, aktiv)
      .then((s) => !abgebrochen && setSeite(s))
      .catch((e) => !abgebrochen && setFehler(e instanceof Error ? e.message : "Seite nicht ladbar"));
    return () => {
      abgebrochen = true;
    };
  }, [campaignId, aktiv]);

  const jetztSpeichern = useCallback(async () => {
    const auftrag = offen.current;
    if (!auftrag) return;
    offen.current = null;
    setZustand("speichert");
    try {
      await seiteSpeichern(campaignId, auftrag.id, {
        ...(auftrag.inhalt !== undefined ? { inhalt: auftrag.inhalt } : {}),
        ...(auftrag.titel !== undefined ? { titel: auftrag.titel } : {}),
      });
      setZustand("gespeichert");
      // Der Titel steht auch im Baum — sonst hinkt die Seitenleiste hinterher.
      if (auftrag.titel !== undefined) await baumLaden();
    } catch (e) {
      setZustand("fehler");
      setFehler(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
    }
  }, [campaignId, baumLaden]);

  function merken(aenderung: { inhalt?: string; titel?: string }) {
    if (!aktiv) return;
    offen.current = { id: aktiv, ...offen.current, ...aenderung };
    setZustand("speichert");
    window.clearTimeout(speicherTimer.current);
    speicherTimer.current = window.setTimeout(jetztSpeichern, AUTOSAVE_MS);
  }

  // Ausstehendes wegschreiben, bevor die Komponente verschwindet.
  useEffect(() => {
    return () => {
      window.clearTimeout(speicherTimer.current);
      if (offen.current) jetztSpeichern();
    };
  }, [jetztSpeichern]);

  async function neueSeite(parentId: string | null) {
    const titel = window.prompt(parentId ? "Titel der Unterseite" : "Titel der neuen Seite");
    if (!titel?.trim()) return;
    try {
      const s = await seiteAnlegen(campaignId, { titel: titel.trim(), parentId });
      await baumLaden();
      setAktiv(s.id);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Seite konnte nicht angelegt werden");
    }
  }

  async function seiteEntfernen() {
    if (!seite) return;
    // Löschen ist unumkehrbar — deshalb Rückfrage, wie überall im Werkzeug.
    if (!window.confirm(`„${seite.titel}" wirklich löschen?\n\nUnterseiten bleiben erhalten und rücken eine Ebene nach oben.`)) {
      return;
    }
    try {
      await seiteLoeschen(campaignId, seite.id);
      setAktiv(null);
      setSeite(null);
      await baumLaden();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Löschen fehlgeschlagen");
    }
  }

  async function bisHierFreigeben() {
    if (!seite) return;
    if (
      !window.confirm(
        `Alle Seiten bis einschließlich „${seite.titel}" für die Gruppe freigeben?\n\n` +
          "Gemeint ist die Reihenfolge im Seitenbaum von oben bis hierher — das „was bisher geschah\".\n" +
          "SL-geheim markierte Absätze bleiben weiterhin verborgen.",
      )
    ) {
      return;
    }
    try {
      const { freigegeben } = await bisHierherFreigeben(campaignId, seite.id);
      await baumLaden();
      const frisch = await getSeite(campaignId, seite.id);
      setSeite(frisch);
      setFehler(null);
      alert(`${freigegeben} Seite${freigegeben === 1 ? "" : "n"} freigegeben.`);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Freigabe fehlgeschlagen");
    }
  }

  async function sichtbarkeitUmschalten() {
    if (!seite) return;
    const neu = seite.sichtbarkeit === "GM" ? "ALLE" : "GM";
    try {
      await seiteSpeichern(campaignId, seite.id, { sichtbarkeit: neu, sichtbarFuer: [] });
      setSeite({ ...seite, sichtbarkeit: neu, sichtbarFuer: [] });
      await baumLaden();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Sichtbarkeit nicht änderbar");
    }
  }

  function springe(anker: string) {
    document.getElementById(anker)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const zustandText: Record<Zustand, string> = {
    ruhig: "",
    speichert: "speichert…",
    gespeichert: "gespeichert",
    fehler: "nicht gespeichert",
  };

  return (
    <div className="wk">
      <aside className="wk-baum">
        <div className="wk-baum-kopf">
          <span className="wk-baum-titel">Seiten</span>
          {!nurLesen && (
            <button type="button" className="wk-werkzeug" onClick={() => neueSeite(null)} title="Neue Seite">
              +
            </button>
          )}
        </div>
        <div className="wk-baum-liste">
          {baum.length === 0 && (
            <p style={{ color: "var(--text-leise)", fontSize: 12 }}>
              {nurLesen ? "Noch nichts freigegeben." : "Noch keine Seite. Mit + anfangen."}
            </p>
          )}
          {baum.map((k) => (
            <Zweig key={k.id} knoten={k} aktiv={aktiv} tiefe={0} onWaehlen={setAktiv} />
          ))}
        </div>
      </aside>

      <section className="wk-mitte">
        {fehler && (
          <p style={{ color: "var(--signal)", fontSize: 12, marginBottom: 8 }}>
            {fehler} <button type="button" className="wk-werkzeug" onClick={() => setFehler(null)}>ok</button>
          </p>
        )}

        {!seite && <p style={{ color: "var(--text-leise)" }}>Keine Seite gewählt.</p>}

        {seite && (
          <>
            <div className="wk-kopf">
              <input
                className="wk-titel-feld"
                value={seite.titel}
                readOnly={nurLesen}
                onChange={(e) => {
                  setSeite({ ...seite, titel: e.target.value });
                  merken({ titel: e.target.value });
                }}
              />
              <span className="wk-zustand" data-zustand={zustand}>
                {zustandText[zustand]}
              </span>

              {!nurLesen && (
                <>
                  <button type="button" className="wk-werkzeug" onClick={() => neueSeite(seite.id)} title="Unterseite anlegen">
                    + Unterseite
                  </button>
                  <button
                    type="button"
                    className="wk-werkzeug"
                    onClick={sichtbarkeitUmschalten}
                    title={
                      seite.sichtbarkeit === "GM"
                        ? "Diese Seite für die Gruppe freigeben"
                        : "Diese Seite wieder SL-geheim machen"
                    }
                    style={{
                      color: seite.sichtbarkeit === "GM" ? "var(--text-leise)" : "var(--gut)",
                      borderColor: seite.sichtbarkeit === "GM" ? "var(--linie)" : "var(--gut)",
                    }}
                  >
                    {seite.sichtbarkeit === "GM" ? "🔒 nur SL" : "👁 freigegeben"}
                  </button>
                  <button
                    type="button"
                    className="wk-werkzeug"
                    onClick={bisHierFreigeben}
                    title="Alles bis hierher für die Gruppe freigeben — „was bisher geschah“"
                  >
                    ⇥ bis hierher
                  </button>
                  <button
                    type="button"
                    className="wk-werkzeug"
                    onClick={seiteEntfernen}
                    title="Seite löschen"
                    style={{ color: "var(--signal)", borderColor: "var(--linie)" }}
                  >
                    ✕
                  </button>
                </>
              )}
            </div>

            <WikiEditor
              campaignId={campaignId}
              seitenId={seite.id}
              inhalt={seite.inhalt}
              nurLesen={nurLesen}
              onChange={(json) => merken({ inhalt: json })}
            />
          </>
        )}
      </section>

      <aside className="wk-verzeichnis">
        <div className="wk-verzeichnis-titel">Inhalt</div>
        <div className="wk-verzeichnis-liste">
          {(!seite || seite.inhaltsverzeichnis.length === 0) && (
            <p style={{ color: "var(--text-leise)", fontSize: 12 }}>
              Überschriften erscheinen hier automatisch.
            </p>
          )}
          {seite?.inhaltsverzeichnis.map((e) => (
            <button
              key={e.anker}
              type="button"
              className="wk-sprung"
              data-stufe={e.stufe}
              onClick={() => springe(e.anker)}
            >
              {e.text}
            </button>
          ))}
        </div>
      </aside>
    </div>
  );
}
