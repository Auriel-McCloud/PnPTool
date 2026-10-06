import { useEffect, useMemo, useState } from "react";
import type { CritterEintrag, Gewaechs, LebtInEintrag } from "./api";
import { entitiesApi } from "./api";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { GewaechsDetail } from "./GewaechsDetail";
import { CritterFenster } from "../begleiter/CritterFenster";
import type { PersonOption } from "./VisibilitySelector";
import "./pc-detail.css";

/**
 * Flora & Fauna — Tab im Ort-Detail-Popup (06.10.2026).
 *
 * Zeigt alle Critter und Gewächse, die über die `LEBT_IN`-Kante mit diesem
 * Ort verknüpft sind, und lässt neue Verknüpfungen anlegen (bestehende Art
 * wählen oder gleich neu anlegen) sowie bestehende lösen. Dasselbe
 * Such-+Radio-Auswahlmuster wie `BesitzerAuswahl` in BegleiterVerwaltung.tsx
 * statt einer neu erfundenen Picker-UI.
 */
const ART_ICON: Record<string, string> = {
  Person: "❖", // Critter — selbes Symbol wie in BegleiterVerwaltung.tsx
  Gewaechs: "🌿",
};

export function FloraFaunaListe({
  campaignId,
  ortId,
  ortName,
  pcOptions,
}: {
  campaignId: string;
  ortId: string;
  ortName: string;
  pcOptions: PersonOption[];
}) {
  const [eintraege, setEintraege] = useState<LebtInEintrag[]>([]);
  const [laden, setLaden] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  const [hinzufuegenOffen, setHinzufuegenOffen] = useState(false);
  const [loeschKandidat, setLoeschKandidat] = useState<LebtInEintrag | null>(null);
  const [critterOffen, setCritterOffen] = useState<LebtInEintrag | null>(null);
  const [gewaechsOffen, setGewaechsOffen] = useState<Gewaechs | null>(null);

  async function neuLaden() {
    try {
      setEintraege(await entitiesApi.floraFaunaListe(campaignId, ortId));
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Flora & Fauna konnte nicht geladen werden");
    }
  }

  useEffect(() => {
    setLaden(true);
    neuLaden().finally(() => setLaden(false));
  }, [campaignId, ortId]);

  async function entfernen() {
    if (!loeschKandidat) return;
    try {
      setEintraege(await entitiesApi.floraFaunaEntfernen(campaignId, ortId, loeschKandidat.id));
      setLoeschKandidat(null);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht gelöst werden");
    }
  }

  async function oeffnen(eintrag: LebtInEintrag) {
    if (eintrag.kind === "Gewaechs") {
      try {
        setGewaechsOffen(await entitiesApi.getGewaechs(campaignId, eintrag.id));
      } catch (e) {
        setFehler(e instanceof Error ? e.message : "Gewächs konnte nicht geladen werden");
      }
    } else {
      setCritterOffen(eintrag);
    }
  }

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Flora & Fauna…</p>;

  return (
    <div className="pcd-editor-bereich">
      <p className="pcd-hinweis">
        Critter und Gewächse, die an diesem Ort vorkommen. Dieselbe Art kann an mehreren Orten vorkommen —
        die Verknüpfung hier entfernt nur die Verbindung, nicht die Art selbst.
      </p>

      {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}

      <div className="ziel-liste">
        {eintraege.length === 0 && (
          <p style={{ color: "var(--text-leise)", fontStyle: "italic" }}>
            Noch nichts verknüpft.
          </p>
        )}
        {eintraege.map((e) => (
          <button key={`${e.kind}-${e.id}`} type="button" className="ziel-eintrag" onClick={() => oeffnen(e)}>
            <span className="ziel-titel">
              {ART_ICON[e.kind] ?? "·"} {e.name}
              <span style={{ color: "var(--text-leise)", fontSize: 12, marginLeft: 6 }}>
                {e.kind === "Gewaechs" ? "Gewächs" : "Critter"}
              </span>
            </span>
            <span
              className="ziel-wegwerfen"
              title="Verknüpfung lösen"
              onClick={(ev) => {
                ev.stopPropagation();
                setLoeschKandidat(e);
              }}
            >
              ✕
            </span>
          </button>
        ))}

        <button type="button" className="ziel-neu" onClick={() => setHinzufuegenOffen(true)}>
          + Critter/Gewächs verknüpfen
        </button>
      </div>

      {hinzufuegenOffen && (
        <FloraFaunaHinzufuegenFenster
          campaignId={campaignId}
          ortId={ortId}
          ortName={ortName}
          bereitsVerknuepft={new Set(eintraege.map((e) => e.id))}
          onSchliessen={() => setHinzufuegenOffen(false)}
          onHinzugefuegt={async (neu) => {
            setEintraege(neu);
            setHinzufuegenOffen(false);
          }}
        />
      )}

      {loeschKandidat && (
        <Bestaetigung
          titel="Verknüpfung lösen?"
          text={`„${loeschKandidat.name}“ wird nicht mehr als an diesem Ort lebend geführt. Die Art selbst bleibt bestehen.`}
          jaText="Ja, lösen"
          neinText="Abbrechen"
          onJa={entfernen}
          onNein={() => setLoeschKandidat(null)}
        />
      )}

      {critterOffen && (
        <CritterFenster
          campaignId={campaignId}
          critterId={critterOffen.id}
          besitzerId={null}
          personen={[]}
          onSchliessen={() => setCritterOffen(null)}
          onGeaendert={async () => {
            await neuLaden();
            setCritterOffen(null);
          }}
        />
      )}

      {gewaechsOffen && (
        <GewaechsDetail
          campaignId={campaignId}
          gewaechs={gewaechsOffen}
          pcOptions={pcOptions}
          onSchliessen={() => setGewaechsOffen(null)}
          onGeaendert={async () => {
            await neuLaden();
            setGewaechsOffen(await entitiesApi.getGewaechs(campaignId, gewaechsOffen.id));
          }}
        />
      )}
    </div>
  );
}

/** Popup zum Verknüpfen: bestehenden Critter/bestehendes Gewächs wählen,
 * oder per Namen gleich neu anlegen. Mirrors BesitzerAuswahl's
 * Such-+Radio-Muster statt einer neuen Picker-Komponente. */
function FloraFaunaHinzufuegenFenster({
  campaignId,
  ortId,
  ortName,
  bereitsVerknuepft,
  onSchliessen,
  onHinzugefuegt,
}: {
  campaignId: string;
  ortId: string;
  ortName: string;
  bereitsVerknuepft: Set<string>;
  onSchliessen: () => void;
  onHinzugefuegt: (neu: LebtInEintrag[]) => void;
}) {
  const [art, setArt] = useState<"CRITTER" | "GEWAECHS">("CRITTER");
  const [critter, setCritter] = useState<CritterEintrag[]>([]);
  const [gewaechse, setGewaechse] = useState<Gewaechs[]>([]);
  const [suche, setSuche] = useState("");
  const [gewaehlt, setGewaehlt] = useState("");
  const [neuName, setNeuName] = useState("");
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([entitiesApi.listCritter(campaignId), entitiesApi.listGewaechse(campaignId)]).then(
      ([c, g]) => {
        setCritter(c);
        setGewaechse(g);
      },
    );
  }, [campaignId]);

  const optionen = useMemo(() => {
    const quelle =
      art === "CRITTER"
        ? critter.map((c) => ({ id: c.id, label: c.name }))
        : gewaechse.map((g) => ({ id: g.id, label: g.name }));
    const unverknuepft = quelle.filter((o) => !bereitsVerknuepft.has(o.id));
    const s = suche.trim().toLowerCase();
    return s ? unverknuepft.filter((o) => o.label.toLowerCase().includes(s)) : unverknuepft;
  }, [art, critter, gewaechse, bereitsVerknuepft, suche]);

  async function verknuepfen(artId: string) {
    setLaeuft(true);
    setFehler(null);
    try {
      const neu = await entitiesApi.floraFaunaHinzufuegen(campaignId, ortId, artId);
      onHinzugefuegt(neu);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Verknüpfen fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  async function bestehendeVerknuepfen() {
    if (!gewaehlt) return;
    await verknuepfen(gewaehlt);
  }

  async function neuAnlegenUndVerknuepfen(e: React.FormEvent) {
    e.preventDefault();
    if (!neuName.trim() || laeuft) return;
    setLaeuft(true);
    setFehler(null);
    try {
      if (art === "CRITTER") {
        const neuerCritter = await entitiesApi.createPerson(campaignId, {
          name: neuName.trim(),
          personType: "NPC",
          description: "",
          notes: "",
          istCritter: true,
          sichtbarkeit: "GM",
          sichtbarFuer: [],
          notizenSichtbarkeit: "GM",
          notizenSichtbarFuer: [],
        });
        const neu = await entitiesApi.floraFaunaHinzufuegen(campaignId, ortId, neuerCritter.id);
        onHinzugefuegt(neu);
      } else {
        const neuesGewaechs = await entitiesApi.createGewaechs(campaignId, {
          name: neuName.trim(),
          description: "",
          notes: "",
          sichtbarkeit: "GM",
          sichtbarFuer: [],
          notizenSichtbarkeit: "GM",
          notizenSichtbarFuer: [],
        });
        const neu = await entitiesApi.floraFaunaHinzufuegen(campaignId, ortId, neuesGewaechs.id);
        onHinzugefuegt(neu);
      }
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Anlegen fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <Fenster
      offen
      titel="Flora & Fauna verknüpfen"
      unterzeile={`Mit „${ortName}“ verbinden`}
      kennung={`flora-fauna-hinzufuegen:${ortId}`}
      ton="var(--bereich-orte, var(--neon))"
      onSchliessen={onSchliessen}
    >
      <div className="pcd-editor-bereich" style={{ padding: 8 }}>
        {fehler && <p style={{ color: "var(--signal)", margin: 0 }}>{fehler}</p>}

        <div className="bg-zeile">
          <span style={{ fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--neon)" }}>
            Art
          </span>
          <select
            value={art}
            onChange={(e) => {
              setArt(e.target.value as "CRITTER" | "GEWAECHS");
              setGewaehlt("");
            }}
          >
            <option value="CRITTER">❖ Critter</option>
            <option value="GEWAECHS">🌿 Gewächs</option>
          </select>
        </div>

        <div>
          <label className="pcd-label">Bestehende(s) {art === "CRITTER" ? "Critter" : "Gewächs"} wählen</label>
          <input
            type="search"
            className="bg-suchfeld"
            placeholder="Suchen…"
            value={suche}
            onChange={(e) => setSuche(e.target.value)}
            style={{ marginBottom: 6 }}
          />
          <div className="bg-auswahl-liste">
            {optionen.length === 0 && <p className="pcd-hinweis">Nichts gefunden — unten neu anlegen.</p>}
            {optionen.map((o) => (
              <label key={o.id} className="bg-auswahl-zeile">
                <input
                  type="radio"
                  name="flora-fauna-auswahl"
                  checked={gewaehlt === o.id}
                  onChange={() => setGewaehlt(o.id)}
                />
                <span>{o.label}</span>
              </label>
            ))}
          </div>
          <button
            type="button"
            className="pcd-speichern"
            style={{ marginTop: 8 }}
            disabled={!gewaehlt || laeuft}
            onClick={bestehendeVerknuepfen}
          >
            {laeuft ? "Verknüpft…" : "Verknüpfen"}
          </button>
        </div>

        <form onSubmit={neuAnlegenUndVerknuepfen} style={{ borderTop: "1px solid var(--linie)", paddingTop: 10, marginTop: 4 }}>
          <label className="pcd-label">Oder neu anlegen und gleich verknüpfen</label>
          <input
            type="text"
            className="ziel-input"
            placeholder={art === "CRITTER" ? "Name des neuen Critters" : "Name des neuen Gewächses"}
            value={neuName}
            onChange={(e) => setNeuName(e.target.value)}
          />
          <div className="ziel-editor-aktionen">
            <button type="button" className="pcd-abbrechen" onClick={onSchliessen}>
              Abbrechen
            </button>
            <button type="submit" className="pcd-speichern" disabled={laeuft || !neuName.trim()}>
              {laeuft ? "Legt an…" : "Anlegen & verknüpfen"}
            </button>
          </div>
        </form>
      </div>
    </Fenster>
  );
}
