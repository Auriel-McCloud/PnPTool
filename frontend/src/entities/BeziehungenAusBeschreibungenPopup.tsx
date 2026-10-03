/**
 * ✨ Beziehungen aus Beschreibungen — liest Beschreibung + SL-Notizen ALLER
 * Personen/Orte/Events/Fraktionen der Kampagne in einem KI-Aufruf und
 * schlägt daraus neue VERBINDUNG-Kanten vor (03.10.2026, Marks Wunsch).
 *
 * Anders als die Wiki-Auto-Verknüpfung (`AutoVerknuepfungPopup.tsx`) gibt es
 * hier keinen Text/keine Seite, nur Entitäten, die sich bereits gegenseitig
 * in ihren Feldern beschreiben — "Kez schuldet dem Zaibatsu Geld" steht z.B.
 * oft schon in der Beschreibung, ohne dass je eine Kante dafür angelegt
 * wurde. Beide Seiten jeder vorgeschlagenen Beziehung sind bestehende
 * Entitäten (zielId nie `null`), trotzdem einzeln bestätigt wie überall
 * sonst — kein Autocommit (Marks Vorgabe).
 */
import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import {
  beziehungenAusBeschreibungen,
  verknuepfungBeziehungAnwenden,
  type BeziehungsVorschlag,
} from "../ki/api";
import "../ki/ki.css";

const TYP_ICON: Record<string, string> = {
  Person: "👤",
  Ort: "📍",
  Event: "📅",
  Fraktion: "⬡",
};

function beziehungSchluessel(v: BeziehungsVorschlag) {
  return `${v.typ1}:${v.name1}:${v.beziehungstyp}:${v.typ2}:${v.name2}`;
}

export function BeziehungenAusBeschreibungenPopup({
  offen,
  campaignId,
  onSchliessen,
  onGeaendert,
}: {
  offen: boolean;
  campaignId: string;
  onSchliessen: () => void;
  /** Nach jeder angewandten Beziehung — Aufrufer lädt die Verbindungsliste neu. */
  onGeaendert: () => void;
}) {
  const [laedt, setLaedt] = useState(false);
  const [angewandt, setAngewandt] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [beziehungen, setBeziehungen] = useState<BeziehungsVorschlag[] | null>(null);
  const [erledigt, setErledigt] = useState<Set<string>>(new Set());

  if (!offen) return null;

  async function holen() {
    setLaedt(true);
    setFehler(null);
    try {
      const antwort = await beziehungenAusBeschreibungen(campaignId);
      setBeziehungen(antwort.beziehungen);
      setErledigt(new Set());
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Erkennung fehlgeschlagen");
    } finally {
      setLaedt(false);
    }
  }

  async function beziehungAnwenden(v: BeziehungsVorschlag) {
    const key = beziehungSchluessel(v);
    setAngewandt(key);
    setFehler(null);
    try {
      // seitenId ist bei dieser Route nur Teil des URL-Pfads (die Kante hängt
      // an den zwei Entitäten, nicht an einer Wiki-Seite) — Platzhalter reicht.
      await verknuepfungBeziehungAnwenden(campaignId, "beziehungen-aus-beschreibungen", v);
      setErledigt((alt) => new Set(alt).add(key));
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Beziehung anlegen fehlgeschlagen");
    } finally {
      setAngewandt(null);
    }
  }

  function schliessenUndZuruecksetzen() {
    setBeziehungen(null);
    setErledigt(new Set());
    setFehler(null);
    onSchliessen();
  }

  const offeneBeziehungen = (beziehungen ?? []).filter((v) => !erledigt.has(beziehungSchluessel(v)));

  return (
    <Fenster
      offen={offen}
      titel="✨ Beziehungen aus Beschreibungen"
      unterzeile="Durchsucht Beschreibung und Notizen aller Personen/Orte/Events/Fraktionen"
      kennung="beziehungen-aus-beschreibungen"
      onSchliessen={schliessenUndZuruecksetzen}
    >
      <div className="ki-popup">
        {beziehungen === null && (
          <>
            <p className="ki-vorschau-hinweis">
              Liest Beschreibung und SL-Notizen aller bestehenden Personen, Orte, Events und Fraktionen
              in einem Durchgang und schlägt daraus neue Verbindungen vor — bereits bestehende Kanten
              werden ausgelassen.
            </p>
            {fehler && <p className="ki-fehler">{fehler}</p>}
            <div className="ki-aktionen">
              <button type="button" className="ki-btn-primaer" disabled={laedt} onClick={holen}>
                {laedt ? "Erkennt…" : "✨ Vorschläge holen"}
              </button>
              <button type="button" className="ki-btn-sekundaer" onClick={schliessenUndZuruecksetzen}>
                Abbrechen
              </button>
            </div>
          </>
        )}

        {beziehungen !== null && (
          <>
            {fehler && <p className="ki-fehler">{fehler}</p>}

            {offeneBeziehungen.length === 0 && (
              <p className="ki-vorschau-hinweis">
                {beziehungen.length === 0 ? "Keine neuen Beziehungen gefunden." : "Alles verknüpft."}
              </p>
            )}

            {offeneBeziehungen.length > 0 && (
              <div className="av-gruppe">
                {offeneBeziehungen.map((v) => {
                  const key = beziehungSchluessel(v);
                  return (
                    <div key={key} className="av-vorschlag">
                      <div className="av-vorschlag-kopf">
                        <span className="av-icon">{TYP_ICON[v.typ1] ?? "❔"}</span>
                        <span className="av-name">{v.name1}</span>
                        <span className="av-beziehungspfeil">— {v.beziehungstyp} →</span>
                        <span className="av-icon">{TYP_ICON[v.typ2] ?? "❔"}</span>
                        <span className="av-name">{v.name2}</span>
                      </div>
                      {v.beschreibung && <div className="av-zitat">{v.beschreibung}</div>}
                      <button
                        type="button"
                        className="ki-btn-primaer"
                        disabled={angewandt === key}
                        onClick={() => beziehungAnwenden(v)}
                      >
                        {angewandt === key ? "…" : "✓ Beziehung anlegen"}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="ki-aktionen">
              <button type="button" className="ki-btn-sekundaer" disabled={laedt} onClick={holen}>
                {laedt ? "Erkennt…" : "↺ Erneut prüfen"}
              </button>
              <button type="button" className="ki-btn-sekundaer" onClick={schliessenUndZuruecksetzen}>
                Schließen
              </button>
            </div>
          </>
        )}
      </div>
    </Fenster>
  );
}
