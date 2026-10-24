/**
 * ✨ Kantentypen normalisieren — Popup im Graph-Filter.
 *
 * Lässt die KI alle in der Kampagne verwendeten Beziehungstyp-Strings
 * vergleichen und vorschlagen, welche sinngemäß dasselbe bedeuten (z.B.
 * "kennt" und "kennt sich"). Dasselbe Muster wie AutoVerknuepfungPopup:
 * zweistufig, jede Gruppe einzeln bestätigt, kein Autocommit.
 */
import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import {
  verbindungstypenNormalisierungAnwenden,
  verbindungstypenNormalisierungsVorschlaege,
  type VerbindungstypNormalisierungsGruppe,
} from "../ki/api";
import "../ki/ki.css";

function gruppenSchluessel(g: VerbindungstypNormalisierungsGruppe): string {
  return `${g.kanonisch}:${g.varianten.join(",")}`;
}

export function KantentypenNormalisierenPopup({
  offen,
  campaignId,
  onSchliessen,
  onUebernommen,
}: {
  offen: boolean;
  campaignId: string;
  onSchliessen: () => void;
  /** Nach jeder angewandten Gruppe — Aufrufer lädt den Graphen neu. */
  onUebernommen: () => void;
}) {
  const [laedt, setLaedt] = useState(false);
  const [angewandt, setAngewandt] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [gruppen, setGruppen] = useState<VerbindungstypNormalisierungsGruppe[] | null>(null);
  const [erledigt, setErledigt] = useState<Set<string>>(new Set());

  if (!offen) return null;

  async function holen() {
    setLaedt(true);
    setFehler(null);
    try {
      const antwort = await verbindungstypenNormalisierungsVorschlaege(campaignId);
      setGruppen(antwort.gruppen);
      setErledigt(new Set());
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Erkennung fehlgeschlagen");
    } finally {
      setLaedt(false);
    }
  }

  async function anwenden(g: VerbindungstypNormalisierungsGruppe) {
    const key = gruppenSchluessel(g);
    setAngewandt(key);
    setFehler(null);
    try {
      await verbindungstypenNormalisierungAnwenden(campaignId, { kanonisch: g.kanonisch, varianten: g.varianten });
      setErledigt((alt) => new Set(alt).add(key));
      onUebernommen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Normalisieren fehlgeschlagen");
    } finally {
      setAngewandt(null);
    }
  }

  function schliessenUndZuruecksetzen() {
    setGruppen(null);
    setErledigt(new Set());
    setFehler(null);
    onSchliessen();
  }

  const offeneGruppen = (gruppen ?? []).filter((g) => !erledigt.has(gruppenSchluessel(g)));

  return (
    <Fenster
      offen={offen}
      titel="✨ Kantentypen normalisieren"
      unterzeile="Fasst sinngemäß gleiche Beziehungstypen zu einem einzigen Namen zusammen"
      kennung={`kantentypen-normalisierung:${campaignId}`}
      onSchliessen={schliessenUndZuruecksetzen}
    >
      <div className="ki-popup">
        {gruppen === null && (
          <>
            <p className="ki-vorschau-hinweis">
              Vergleicht alle in dieser Kampagne verwendeten Kantenbezeichnungen und schlägt vor, welche
              dasselbe Konzept meinen (z.B. „kennt" und „kennt sich"). Jede Gruppe wird einzeln bestätigt —
              das Übernehmen benennt ALLE betroffenen Kanten auf den kanonischen Namen um.
            </p>
            {fehler && <p className="ki-fehler">{fehler}</p>}
            <div className="ki-aktionen">
              <button type="button" className="ki-btn-primaer" disabled={laedt} onClick={holen}>
                {laedt ? "Vergleicht…" : "✨ Vorschläge holen"}
              </button>
              <button type="button" className="ki-btn-sekundaer" onClick={schliessenUndZuruecksetzen}>
                Abbrechen
              </button>
            </div>
          </>
        )}

        {gruppen !== null && (
          <>
            {fehler && <p className="ki-fehler">{fehler}</p>}

            {offeneGruppen.length === 0 && (
              <p className="ki-vorschau-hinweis">
                {gruppen.length === 0 ? "Keine sinnvollen Zusammenlegungen gefunden." : "Alles übernommen."}
              </p>
            )}

            {offeneGruppen.map((g) => {
              const key = gruppenSchluessel(g);
              return (
                <div key={key} className="av-vorschlag">
                  <div className="av-vorschlag-kopf">
                    <span className="av-name">{g.varianten.join(" / ")}</span>
                    <span className="av-beziehungspfeil">→</span>
                    <strong>{g.kanonisch}</strong>
                    <span style={{ marginLeft: "auto", color: "var(--text-leise)", fontSize: "0.8rem" }}>
                      {g.anzahl} Kante{g.anzahl === 1 ? "" : "n"}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="ki-btn-primaer"
                    disabled={angewandt === key}
                    onClick={() => anwenden(g)}
                  >
                    {angewandt === key ? "…" : "✓ Übernehmen"}
                  </button>
                </div>
              );
            })}

            <div className="ki-aktionen">
              <button type="button" className="ki-btn-sekundaer" disabled={laedt} onClick={holen}>
                {laedt ? "Vergleicht…" : "↺ Erneut prüfen"}
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
