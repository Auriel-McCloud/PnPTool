import { useEffect, useRef, useState } from "react";
import { entitiesApi, type FilterOptionen, type ListenFilter, type Sortierung } from "./api";
import "./filterleiste.css";

/**
 * Suchen, Sortieren und nach Beziehungen filtern — für NPCs, Orte und Events.
 *
 * **Der Beziehungsfilter arbeitet auf echten Graphkanten.** Was er anbietet,
 * kommt aus `GET .../filteroptionen` und damit aus den `VERBINDUNG`-Kanten,
 * die die Spielleitung ohnehin pflegt. Es gibt kein Sonderfeld "Ort" oder
 * "Fraktion" an der Person: "wer ist in der 3Heavens Bar", "welche Gegner beim
 * Überfall" und "wer gehört zur Party" sind dieselbe Abfrage mit anderem Ziel.
 *
 * Angeboten wird nur, was wirklich existiert. Ein Dropdown, das ins Leere
 * führt, ist schlimmer als keins — man sucht dann den Fehler bei sich.
 */

const SORTIERUNGEN: { wert: Sortierung; text: string }[] = [
  { wert: "name", text: "A → Z" },
  { wert: "name-ab", text: "Z → A" },
  { wert: "sichtbarkeit", text: "Geheim zuerst" },
  { wert: "verbindungen", text: "Meiste Verbindungen" },
];

const ZEITPUNKT: { wert: Sortierung; text: string } = { wert: "zeitpunkt", text: "Nach Zeitpunkt" };

// Kurzzeichen je Entitätsart, damit man im Dropdown auf einen Blick sieht,
// ob man gerade nach einem Ort oder einem Event filtert. Gleiche Symbole wie
// die Bereiche in der Menüspalte (App.tsx).
const ART_SYMBOL: Record<string, string> = {
  Person: "◌",
  Ort: "⌖",
  Event: "◆",
  Gegenstand: "◈",
};

export interface FilterleisteProps {
  campaignId: string;
  /** Welche Liste gefiltert wird — bestimmt die angebotenen Optionen. */
  art: "personen" | "orte" | "events";
  /** Nur bei Personen: schränkt die Optionen auf PCs bzw. NPCs ein. */
  personType?: "PC" | "NPC";
  filter: ListenFilter;
  onFilter: (filter: ListenFilter) => void;
  /** Wie viele Einträge die aktuelle Auswahl liefert. */
  trefferzahl: number;
  /** Farbe des Bereichs, z.B. "var(--bereich-npcs)". */
  farbe: string;
  /** Zeitpunkt-Sortierung anbieten (nur sinnvoll bei Events). */
  mitZeitpunkt?: boolean;
}

export function Filterleiste({
  campaignId,
  art,
  personType,
  filter,
  onFilter,
  trefferzahl,
  farbe,
  mitZeitpunkt = false,
}: FilterleisteProps) {
  const [optionen, setOptionen] = useState<FilterOptionen | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  // Eigener Zustand fürs Eingabefeld: die Suche wird verzögert abgeschickt,
  // das Feld muss aber sofort reagieren. Ohne das ruckelt jede Eingabe.
  const [sucheRoh, setSucheRoh] = useState(filter.suche ?? "");
  const ersterLauf = useRef(true);

  useEffect(() => {
    let abgebrochen = false;
    entitiesApi
      .filteroptionen(campaignId, art, personType)
      .then((o) => {
        if (!abgebrochen) {
          setOptionen(o);
          setFehler(null);
        }
      })
      .catch(() => {
        // Kein Grund, die Liste unbenutzbar zu machen: Suche und Sortierung
        // laufen weiter, nur der Beziehungsfilter fehlt dann.
        if (!abgebrochen) setFehler("Beziehungsfilter nicht verfügbar");
      });
    return () => {
      abgebrochen = true;
    };
    // trefferzahl als Abhängigkeit: nach dem Anlegen oder Löschen einer
    // Verbindung sollen die Optionen nachziehen, ohne dass man neu lädt.
  }, [campaignId, art, personType, trefferzahl]);

  // Verzögertes Suchen (300 ms). Sonst geht bei jedem Tastendruck eine
  // Anfrage raus, und auf dem Tablet über WLAN überholen die Antworten
  // einander — dann steht am Ende das Ergebnis der vorletzten Eingabe da.
  useEffect(() => {
    if (ersterLauf.current) {
      ersterLauf.current = false;
      return;
    }
    const zeitgeber = window.setTimeout(() => {
      onFilter({ ...filter, suche: sucheRoh });
    }, 300);
    return () => window.clearTimeout(zeitgeber);
    // filter/onFilter bewusst nicht in der Liste: sonst startet der Zeitgeber
    // bei jeder Filteränderung neu und die Suche feuert doppelt.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sucheRoh]);

  const sortierungen = mitZeitpunkt ? [ZEITPUNKT, ...SORTIERUNGEN] : SORTIERUNGEN;
  const hatBeziehungen = (optionen?.ziele.length ?? 0) > 0 || (optionen?.typen.length ?? 0) > 0;
  const istGefiltert = Boolean(
    filter.suche?.trim() || filter.verbundenMit || filter.verbindungsTyp || filter.sortierung
  );

  function zuruecksetzen() {
    setSucheRoh("");
    onFilter({ personType: filter.personType });
  }

  return (
    <div className="fl-leiste" style={{ ["--fl-farbe" as string]: farbe }}>
      <div className="fl-zeile">
        <div className="fl-suchfeld">
          <span className="fl-lupe" aria-hidden="true">
            ⌕
          </span>
          <input
            type="search"
            value={sucheRoh}
            onChange={(e) => setSucheRoh(e.target.value)}
            placeholder="Suchen — Name, Beschreibung, Notizen…"
            aria-label="Suchen"
          />
          {sucheRoh && (
            <button type="button" className="fl-loeschen" onClick={() => setSucheRoh("")} title="Suche leeren">
              ✕
            </button>
          )}
        </div>

        <label className="fl-wahl">
          <span className="fl-wahl-text">Reihenfolge</span>
          <select
            value={filter.sortierung ?? "name"}
            onChange={(e) => onFilter({ ...filter, sortierung: e.target.value as Sortierung })}
          >
            {sortierungen.map((s) => (
              <option key={s.wert} value={s.wert}>
                {s.text}
              </option>
            ))}
          </select>
        </label>
      </div>

      {hatBeziehungen && (
        <div className="fl-zeile">
          <label className="fl-wahl fl-wahl-breit">
            <span className="fl-wahl-text">Verbunden mit</span>
            <select
              value={filter.verbundenMit ?? ""}
              onChange={(e) => onFilter({ ...filter, verbundenMit: e.target.value || undefined })}
            >
              <option value="">— beliebig —</option>
              {optionen?.ziele.map((z) => (
                <option key={z.id} value={z.id}>
                  {ART_SYMBOL[z.kind] ?? "·"} {z.label} ({z.anzahl})
                </option>
              ))}
            </select>
          </label>

          <label className="fl-wahl fl-wahl-breit">
            <span className="fl-wahl-text">Art der Beziehung</span>
            <select
              value={filter.verbindungsTyp ?? ""}
              onChange={(e) => onFilter({ ...filter, verbindungsTyp: e.target.value || undefined })}
            >
              <option value="">— beliebig —</option>
              {optionen?.typen.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      <div className="fl-fuss">
        <span className="fl-treffer mono">
          {trefferzahl} {trefferzahl === 1 ? "Eintrag" : "Einträge"}
          {istGefiltert && " (gefiltert)"}
        </span>
        {fehler && <span className="fl-fehler">{fehler}</span>}
        {istGefiltert && (
          <button type="button" className="fl-zuruecksetzen" onClick={zuruecksetzen}>
            Filter zurücksetzen
          </button>
        )}
      </div>
    </div>
  );
}
