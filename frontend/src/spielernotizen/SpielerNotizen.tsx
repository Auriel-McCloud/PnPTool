import { useEffect, useMemo, useState, type FormEvent } from "react";
import type { JSONContent } from "@tiptap/react";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { useAutosave } from "../shell/autosave";
import { parseRichText, serializeRichText } from "../richtext/content";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { spielernotizenApi, type SpielerNotiz } from "./api";
import "./spielernotizen.css";

function formatDatum(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });
}

function NotizEditor({
  notiz,
  onAktualisiert,
  onLoeschen,
}: {
  notiz: SpielerNotiz;
  onAktualisiert: (n: SpielerNotiz) => void;
  onLoeschen: () => void;
}) {
  const [titel, setTitel] = useState(notiz.titel);
  const [doc, setDoc] = useState<JSONContent>(() => parseRichText(notiz.inhalt));

  useEffect(() => {
    setTitel(notiz.titel);
    setDoc(parseRichText(notiz.inhalt));
  }, [notiz.id]);

  // Nach jedem Autosave den frischen Stand an den Elternzustand zurückgeben —
  // sonst bleibt `liste`/`offen` beim letzten Ladezeitpunkt stehen. Beim
  // nächsten Öffnen (Zeile klicken -> setOffen(n) mit dem alten `n` aus
  // `liste`) initialisiert NotizEditor seinen State dann aus dem veralteten
  // `notiz.inhalt` und zeigt scheinbar "nichts" an, obwohl das PATCH oben
  // längst durch ist (Mark, 04.10.2026: Text weg beim Verlassen+Reinklicken).
  const merken = useAutosave(async (wert: JSONContent) => {
    const aktualisiert = await spielernotizenApi.aendern(notiz.id, { inhalt: serializeRichText(wert) });
    onAktualisiert(aktualisiert);
  });

  async function titelSpeichern() {
    const sauber = titel.trim();
    if (!sauber) {
      setTitel(notiz.titel);
      return;
    }
    if (sauber === notiz.titel) return;
    const aktualisiert = await spielernotizenApi.aendern(notiz.id, { titel: sauber });
    onAktualisiert(aktualisiert);
  }

  return (
    <div className="sn-editor">
      <label className="sn-label">Titel</label>
      <input
        className="sn-titel"
        value={titel}
        onChange={(e) => setTitel(e.target.value)}
        onBlur={() => void titelSpeichern()}
      />
      <label className="sn-label">Text</label>
      <RichTextEditor
        content={doc}
        versteckenErlaubt={false}
        onChange={(naechstes) => {
          setDoc(naechstes);
          merken(naechstes);
        }}
        minHeight={180}
      />
      <div className="sn-editor-fuss">
        <button type="button" className="sn-loeschen" onClick={onLoeschen}>
          Löschen
        </button>
      </div>
    </div>
  );
}

/**
 * Privater Schmierzettel des Spielers. Kein Wiki, keine Freigabe —
 * die Spielleitung sieht diese Einträge nicht.
 */
export function SpielerNotizen() {
  const [liste, setListe] = useState<SpielerNotiz[]>([]);
  const [laedt, setLaedt] = useState(true);
  const [suche, setSuche] = useState("");
  const [offen, setOffen] = useState<SpielerNotiz | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [neuTitel, setNeuTitel] = useState("");
  const [loeschKandidat, setLoeschKandidat] = useState<SpielerNotiz | null>(null);

  async function neuLaden() {
    const daten = await spielernotizenApi.liste();
    setListe(daten);
    setOffen((alt) => (alt ? daten.find((n) => n.id === alt.id) ?? null : null));
  }

  useEffect(() => {
    setLaedt(true);
    neuLaden().finally(() => setLaedt(false));
  }, []);

  const gefiltert = useMemo(() => {
    const q = suche.trim().toLowerCase();
    if (!q) return liste;
    return liste.filter((n) => n.titel.toLowerCase().includes(q));
  }, [liste, suche]);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!neuTitel.trim()) return;
    const neu = await spielernotizenApi.anlegen(neuTitel.trim());
    setNeuTitel("");
    setAnlegenOffen(false);
    await neuLaden();
    setOffen(neu);
  }

  async function loeschen() {
    if (!loeschKandidat) return;
    await spielernotizenApi.loeschen(loeschKandidat.id);
    setLoeschKandidat(null);
    setOffen(null);
    await neuLaden();
  }

  if (laedt) return <p className="sn-leer">Lade Notizen…</p>;

  return (
    <div className="sn-seite">
      <div className="sn-kopf">
        <input
          type="search"
          className="sn-suche"
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
          placeholder="Suchen…"
          aria-label="Notizen durchsuchen"
        />
        <button type="button" onClick={() => setAnlegenOffen(true)}>
          + Neue Notiz
        </button>
        <span className="sn-anzahl">
          {gefiltert.length} {gefiltert.length === 1 ? "Notiz" : "Notizen"}
        </span>
      </div>

      {liste.length === 0 && <p className="sn-leer">Noch keine Notizen. Nur du siehst sie.</p>}

      {liste.length > 0 && gefiltert.length === 0 && (
        <p className="sn-leer">Keine Notiz passt zu „{suche.trim()}“.</p>
      )}

      {gefiltert.length > 0 && (
        <table className="sn-tabelle">
          <thead>
            <tr>
              <th>Titel</th>
              <th>Geändert</th>
            </tr>
          </thead>
          <tbody>
            {gefiltert.map((n) => (
              <tr key={n.id} className="sn-zeile" onClick={() => setOffen(n)}>
                <td className="sn-zeile-titel">{n.titel}</td>
                <td className="sn-zeile-datum">{formatDatum(n.geaendertAm)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <Fenster
        offen={anlegenOffen}
        titel="Neue Notiz"
        kennung="notiz-anlegen"
        onSchliessen={() => setAnlegenOffen(false)}
      >
        <form className="sn-anlegen" onSubmit={anlegen}>
          <label className="sn-label">Titel</label>
          <input
            className="sn-titel"
            value={neuTitel}
            onChange={(e) => setNeuTitel(e.target.value)}
            autoFocus
            required
          />
          <div className="sn-editor-fuss">
            <button type="button" onClick={() => setAnlegenOffen(false)}>
              Abbrechen
            </button>
            <button type="submit" disabled={!neuTitel.trim()}>
              Anlegen
            </button>
          </div>
        </form>
      </Fenster>

      {offen && (
        <Fenster
          offen
          titel={offen.titel}
          unterzeile="Nur du siehst das"
          kennung={`notiz-${offen.id}`}
          onSchliessen={() => setOffen(null)}
        >
          <NotizEditor
            notiz={offen}
            onAktualisiert={(n) => {
              // `offen` nur aktualisieren, wenn es noch dieselbe Notiz ist —
              // sonst reisst ein verspäteter Autosave-Flush (z.B. der
              // Unmount-Flush aus autosave.ts beim Schliessen) das Fenster
              // wieder auf, nachdem der Spieler es längst zugemacht hat.
              setListe((alt) => alt.map((x) => (x.id === n.id ? n : x)));
              setOffen((alt) => (alt && alt.id === n.id ? n : alt));
            }}
            onLoeschen={() => setLoeschKandidat(offen)}
          />
        </Fenster>
      )}

      {loeschKandidat && (
        <Bestaetigung
          titel="Notiz löschen?"
          text={`„${loeschKandidat.titel}“ wird entfernt. Das lässt sich nicht rückgängig machen.`}
          jaText="Ja, löschen"
          neinText="Abbrechen"
          onJa={() => void loeschen()}
          onNein={() => setLoeschKandidat(null)}
        />
      )}
    </div>
  );
}
