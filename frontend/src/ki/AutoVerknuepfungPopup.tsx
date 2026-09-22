/**
 * ⧉✨ Auto-Verknüpfung — Popup mit den von der KI erkannten Erwähnungen
 * einer Wiki-Seite (Personen/Orte/Events/Fraktionen).
 *
 * Zweistufig wie die Rechtschreib-/Logikprüfung: „Vorschläge holen" listet
 * Treffer, jeder einzeln mit „✓ Verknüpfen" bestätigt. Ein Treffer ohne
 * passende bestehende Entität zeigt „Neu anlegen" — Klick legt einen
 * SL-geheimen Entwurf in der Ideenschmiede an und verknüpft direkt dorthin
 * (Marks Vorgabe: Entwurf zur Prüfung, kein Autocommit in die Kampagne).
 */
import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import { verknuepfungAnwenden, verknuepfungsVorschlaege, type VerknuepfungsVorschlag } from "./api";

const TYP_ICON: Record<string, string> = {
  Person: "👤",
  Ort: "📍",
  Event: "📅",
  Fraktion: "⬡",
};

export function AutoVerknuepfungPopup({
  offen,
  campaignId,
  seitenId,
  onSchliessen,
  onUebernommen,
}: {
  offen: boolean;
  campaignId: string;
  seitenId: string;
  onSchliessen: () => void;
  /** Nach jeder Anwendung — Aufrufer aktualisiert den Editor mit dem neuen Inhalt. */
  onUebernommen: (neuerInhalt: string) => void;
}) {
  const [laedt, setLaedt] = useState(false);
  const [angewandt, setAngewandt] = useState<string | null>(null); // Schlüssel des laufenden Vorschlags
  const [fehler, setFehler] = useState<string | null>(null);
  const [vorschlaege, setVorschlaege] = useState<VerknuepfungsVorschlag[] | null>(null);
  const [erledigt, setErledigt] = useState<Set<string>>(new Set());

  if (!offen) return null;

  function schluessel(v: VerknuepfungsVorschlag) {
    return `${v.zitat}:${v.typ}:${v.name}`;
  }

  async function holen() {
    setLaedt(true);
    setFehler(null);
    try {
      const treffer = await verknuepfungsVorschlaege(campaignId, seitenId);
      setVorschlaege(treffer);
      setErledigt(new Set());
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Erkennung fehlgeschlagen");
    } finally {
      setLaedt(false);
    }
  }

  async function anwenden(v: VerknuepfungsVorschlag) {
    const key = schluessel(v);
    setAngewandt(key);
    setFehler(null);
    try {
      const ergebnis = await verknuepfungAnwenden(campaignId, seitenId, v);
      if (!ergebnis.ersetzt) {
        setFehler(`„${v.zitat}" wurde im Text nicht mehr gefunden — schon geändert?`);
        return;
      }
      setErledigt((alt) => new Set(alt).add(key));
      onUebernommen(ergebnis.inhalt);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Verknüpfen fehlgeschlagen");
    } finally {
      setAngewandt(null);
    }
  }

  function schliessenUndZuruecksetzen() {
    setVorschlaege(null);
    setErledigt(new Set());
    setFehler(null);
    onSchliessen();
  }

  const offeneVorschlaege = (vorschlaege ?? []).filter((v) => !erledigt.has(schluessel(v)));

  return (
    <Fenster
      offen={offen}
      titel="⧉✨ Auto-Verknüpfung"
      unterzeile="Erkennt erwähnte Personen/Orte/Events/Fraktionen und verknüpft sie"
      kennung={`auto-verknuepfung:${seitenId}`}
      onSchliessen={schliessenUndZuruecksetzen}
    >
      <div className="ki-popup">
        {vorschlaege === null && (
          <>
            <p className="ki-vorschau-hinweis">
              Durchsucht den Text dieser Seite nach Personen, Orten, Ereignissen und Fraktionen — bekannte
              werden direkt verknüpft, unbekannte als Entwurf zur Prüfung angelegt.
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

        {vorschlaege !== null && (
          <>
            {fehler && <p className="ki-fehler">{fehler}</p>}

            {offeneVorschlaege.length === 0 && (
              <p className="ki-vorschau-hinweis">
                {vorschlaege.length === 0
                  ? "Keine Erwähnungen gefunden."
                  : "Alle gefundenen Erwähnungen sind verknüpft."}
              </p>
            )}

            {offeneVorschlaege.map((v) => {
              const key = schluessel(v);
              const neu = v.zielId === null;
              return (
                <div key={key} className="av-vorschlag">
                  <div className="av-vorschlag-kopf">
                    <span className="av-icon">{TYP_ICON[v.typ] ?? "❔"}</span>
                    <span className="av-name">{v.name}</span>
                    <span className="av-typ">{v.typ}</span>
                    {neu && <span className="av-neu">neu</span>}
                  </div>
                  <div className="av-zitat">„{v.zitat}"</div>
                  <button
                    type="button"
                    className="ki-btn-primaer"
                    disabled={angewandt === key}
                    onClick={() => anwenden(v)}
                  >
                    {angewandt === key ? "…" : neu ? "+ Entwurf anlegen & verknüpfen" : "✓ Verknüpfen"}
                  </button>
                </div>
              );
            })}

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
