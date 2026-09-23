/**
 * 🔍 Rechtschreib-/Grammatik-/Logikprüfung für ein einzelnes Beschreibungs-
 * oder Notizen-Feld (Person/Ort/Event/Fraktion/Gegenstand/Begleiter) — der
 * kleine Bruder von wiki/PruefungPopup.tsx, ohne Seitenbezug: die Befunde
 * kommen aus einem reinen Textfeld statt einer Wiki-Seite, deshalb wird
 * beim „Übernehmen“ auch nichts über die API gespeichert. Der Aufrufer
 * (RichTextEditor) ersetzt die Textstelle direkt im offenen Editor —
 * funktioniert nur, solange das Feld gerade offen ist (anders als beim
 * Wiki-Sweep gibt es hier keinen Hintergrund-Lauf über geschlossene Felder).
 */
import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import type { PruefBefund } from "./api";
import "./ki.css";

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

export function ObjektPruefungPopup({
  offen,
  befunde,
  onSchliessen,
  onUebernehmen,
}: {
  offen: boolean;
  befunde: PruefBefund[];
  onSchliessen: () => void;
  /** Ersetzt die Textstelle direkt im Editor; Rückgabe false = Zitat nicht
   * mehr im Text gefunden (z.B. zwischenzeitlich von Hand geändert). */
  onUebernehmen: (befund: PruefBefund) => boolean;
}) {
  const [fehler, setFehler] = useState<string | null>(null);

  if (!offen) return null;

  function uebernehmen(befund: PruefBefund) {
    setFehler(null);
    const ok = onUebernehmen(befund);
    if (!ok) {
      setFehler(`„${befund.zitat}“ wurde im Text nicht mehr gefunden — schon geändert?`);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel="🔍 Prüfung"
      unterzeile={befunde.length === 0 ? "Keine Befunde." : `${befunde.length} Fund${befunde.length === 1 ? "" : "e"}`}
      kennung="objekt-pruefung"
      onSchliessen={onSchliessen}
    >
      {fehler && (
        <p style={{ color: "var(--signal)", fontSize: 12, margin: "0 0 8px" }}>
          {fehler} <button type="button" className="ki-btn-sekundaer" style={{ padding: "2px 8px" }} onClick={() => setFehler(null)}>ok</button>
        </p>
      )}

      {befunde.length === 0 && (
        <p style={{ color: "var(--text-leise)", fontSize: 13 }}>
          Keine Rechtschreib-, Grammatik- oder Logikfehler gefunden.
        </p>
      )}

      {befunde.map((befund, i) => (
        <div key={i} className="op-pr-befund">
          <span className="op-pr-art" style={{ color: ART_TON[befund.art] ?? "var(--text-leise)" }}>
            {ART_LABEL[befund.art] ?? befund.art}
          </span>
          <div className="op-pr-text">
            <span className="op-pr-zitat">„{befund.zitat}“</span>
            <span className="op-pr-pfeil">→</span>
            <span className="op-pr-vorschlag">„{befund.vorschlag}“</span>
          </div>
          {befund.begruendung && <p className="op-pr-begruendung">{befund.begruendung}</p>}
          <div className="op-pr-aktionen">
            <button type="button" className="op-pr-uebernehmen" onClick={() => uebernehmen(befund)}>
              ✓ Übernehmen
            </button>
          </div>
        </div>
      ))}
    </Fenster>
  );
}
