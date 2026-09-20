/**
 * Ergebnis-Popup der Rechtschreib-/Grammatik-/Logikprüfung.
 *
 * Wird sowohl vom einzelnen "🔍 Prüfen"-Knopf im Wiki-Editor (eine Seite,
 * ein Eintrag in `ergebnisse`) als auch vom kampagnenweiten Sweep-Knopf in
 * den Einstellungen (viele Seiten) verwendet — dieselbe Darstellung, nur
 * mit mehr Gruppen.
 *
 * Jeder Befund hat zwei Aktionen: "✓ Übernehmen" ersetzt die Textstelle
 * direkt im gespeicherten Dokument (funktioniert auch, wenn die Seite
 * gerade nicht offen ist — wichtig beim Sweep), "↷ Zur Textstelle" ruft
 * `onSpringen` auf, das den Aufrufer entscheiden lässt, was "hinspringen"
 * bedeutet (im offenen Editor scrollen, oder erst die Seite öffnen).
 */
import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import { befundUebernehmen, type SweepSeite } from "../ideenschmiede/api";

const ART_LABEL: Record<string, string> = {
  rechtschreibung: "Rechtschreibung",
  grammatik: "Grammatik",
  logik: "Logik",
};

const ART_TON: Record<string, string> = {
  rechtschreibung: "var(--text-leise)",
  grammatik: "var(--warn)",
  logik: "var(--signal)",
};

export function PruefungPopup({
  offen,
  campaignId,
  ergebnisse,
  onSchliessen,
  onSpringen,
  onUebernommen,
}: {
  offen: boolean;
  campaignId: string;
  ergebnisse: SweepSeite[];
  onSchliessen: () => void;
  /** Aufrufer entscheidet, was "zur Textstelle springen" bedeutet. */
  onSpringen?: (seitenId: string, zitat: string) => void;
  /** Nach erfolgreichem Übernehmen — z.B. um den Editor mit dem neuen Inhalt zu aktualisieren. */
  onUebernommen?: (seitenId: string, neuerInhalt: string) => void;
}) {
  // Eigener Zustand statt direkt auf `ergebnisse` zu rendern: übernommene
  // Befunde sollen sofort aus der Liste verschwinden, ohne einen erneuten
  // Prüflauf. WICHTIG für Aufrufer: bei einem NEUEN Prüfergebnis muss diese
  // Komponente neu gemountet werden (z.B. `key={pruefStamp}` mit einem bei
  // jedem Lauf hochzählenden Wert) — sonst bleibt hier der alte Stand
  // stehen, weil `useState(ergebnisse)` nur beim ersten Mount greift.
  const [seiten, setSeiten] = useState<SweepSeite[]>(ergebnisse);
  const [laeuft, setLaeuft] = useState<string | null>(null); // Schlüssel des gerade laufenden Übernehmens
  const [fehler, setFehler] = useState<string | null>(null);

  if (!offen) return null;

  async function uebernehmen(seitenId: string, index: number) {
    const seite = seiten.find((s) => s.seitenId === seitenId);
    const befund = seite?.befunde[index];
    if (!befund) return;
    const schluessel = `${seitenId}:${index}`;
    setLaeuft(schluessel);
    setFehler(null);
    try {
      const ergebnis = await befundUebernehmen(campaignId, seitenId, befund.zitat, befund.vorschlag);
      if (!ergebnis.ersetzt) {
        setFehler(`„${befund.zitat}\" wurde im Text nicht mehr gefunden — schon geändert?`);
        return;
      }
      setSeiten((vorher) =>
        vorher
          .map((s) =>
            s.seitenId === seitenId ? { ...s, befunde: s.befunde.filter((_, i) => i !== index) } : s,
          )
          .filter((s) => s.befunde.length > 0),
      );
      onUebernommen?.(seitenId, ergebnis.inhalt);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Übernehmen fehlgeschlagen");
    } finally {
      setLaeuft(null);
    }
  }

  const gesamt = seiten.reduce((n, s) => n + s.befunde.length, 0);

  return (
    <Fenster
      offen={offen}
      titel="🔍 Prüfung"
      unterzeile={gesamt === 0 ? "Keine Befunde." : `${gesamt} Fund${gesamt === 1 ? "" : "e"}`}
      kennung="wiki-pruefung"
      onSchliessen={onSchliessen}
    >
      {fehler && (
        <p style={{ color: "var(--signal)", fontSize: 12, margin: 0 }}>
          {fehler} <button type="button" className="wk-werkzeug" onClick={() => setFehler(null)}>ok</button>
        </p>
      )}

      {gesamt === 0 && (
        <p style={{ color: "var(--text-leise)", fontSize: 13 }}>
          Keine Rechtschreib-, Grammatik- oder Logikfehler gefunden.
        </p>
      )}

      {seiten.map((seite) => (
        <div key={seite.seitenId} className="wk-pr-seite">
          {seiten.length > 1 && <h4 className="wk-pr-seitentitel">{seite.titel}</h4>}
          {seite.befunde.map((befund, i) => {
            const schluessel = `${seite.seitenId}:${i}`;
            return (
              <div key={schluessel} className="wk-pr-befund">
                <span className="wk-pr-art" style={{ color: ART_TON[befund.art] ?? "var(--text-leise)" }}>
                  {ART_LABEL[befund.art] ?? befund.art}
                </span>
                <div className="wk-pr-text">
                  <span className="wk-pr-zitat">„{befund.zitat}"</span>
                  <span className="wk-pr-pfeil">→</span>
                  <span className="wk-pr-vorschlag">„{befund.vorschlag}"</span>
                </div>
                {befund.begruendung && <p className="wk-pr-begruendung">{befund.begruendung}</p>}
                <div className="wk-pr-aktionen">
                  <button
                    type="button"
                    className="wk-pr-uebernehmen"
                    disabled={laeuft === schluessel}
                    onClick={() => uebernehmen(seite.seitenId, i)}
                  >
                    {laeuft === schluessel ? "…" : "✓ Übernehmen"}
                  </button>
                  {onSpringen && (
                    <button
                      type="button"
                      className="wk-pr-springen"
                      onClick={() => onSpringen(seite.seitenId, befund.zitat)}
                    >
                      ↷ Zur Textstelle
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ))}
    </Fenster>
  );
}
