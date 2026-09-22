/**
 * ✨ KI-Textvorschlag-Popup — neben „SL-geheim" im RichTextEditor jeder
 * Entität (Beschreibung UND Notizen, siehe RichTextEditor.tsx).
 *
 * Wunsch eintippen → „Generieren" → Vorschau des Vorschlags → erst nach
 * „✓ Übernehmen" landet der Text im Editor (Marks Wunsch, 22.09.2026: nicht
 * direkt reinschreiben, wie bei der Wiki-Prüfung erst zur Kontrolle
 * anzeigen). Übernehmen hängt den Text ans Ende des bisherigen Inhalts an,
 * der bisherige Inhalt bleibt erhalten (Marks Wunsch).
 */
import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import { kiObjektText } from "./api";
import "./ki.css";

export function KiTextPopup({
  offen,
  campaignId,
  objektTyp,
  objektName,
  bisherigerText,
  feldLabel,
  onSchliessen,
  onUebernehmen,
}: {
  offen: boolean;
  campaignId: string;
  /** z.B. "Person", "Ort", "Event", "Fraktion", "Gegenstand" — geht 1:1 an die KI. */
  objektTyp: string;
  objektName: string;
  /** Reiner Text des Feldes, für den Anschluss an den bisherigen Inhalt. */
  bisherigerText: string;
  /** "Beschreibung" oder "Notizen" — nur für die Kopfzeile. */
  feldLabel: string;
  onSchliessen: () => void;
  /** Hängt den übernommenen Text ans Editor-Ende an. */
  onUebernehmen: (text: string) => void;
}) {
  const [prompt, setPrompt] = useState("");
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [vorschlag, setVorschlag] = useState<string | null>(null);

  function schliessenUndZuruecksetzen() {
    setPrompt("");
    setFehler(null);
    setVorschlag(null);
    onSchliessen();
  }

  async function generieren() {
    if (!prompt.trim()) return;
    setLaeuft(true);
    setFehler(null);
    try {
      const text = await kiObjektText(campaignId, {
        objektTyp,
        objektName,
        bisherigerText,
        prompt: prompt.trim(),
      });
      if (!text) {
        setFehler("Die KI hat keinen Text geliefert — anderen Wunsch versuchen?");
        return;
      }
      setVorschlag(text);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Generieren fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  function uebernehmen() {
    if (!vorschlag) return;
    onUebernehmen(vorschlag);
    schliessenUndZuruecksetzen();
  }

  return (
    <Fenster
      offen={offen}
      titel="✨ KI-Text generieren"
      unterzeile={`${objektTyp} „${objektName}" — ${feldLabel}`}
      kennung={`ki-objekt-text:${objektTyp}:${objektName}`}
      onSchliessen={schliessenUndZuruecksetzen}
    >
      <div className="ki-popup">
        {!vorschlag && (
          <>
            <label className="ki-label">
              Wunsch
              <textarea
                className="ki-input"
                rows={4}
                style={{ resize: "vertical", minHeight: 80, width: "100%" }}
                placeholder="z.B. Schreib mehr über die Kindheit dieser Person."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                autoFocus
              />
            </label>

            {fehler && <p className="ki-fehler">{fehler}</p>}

            <div className="ki-aktionen">
              <button
                type="button"
                className="ki-btn-primaer"
                disabled={laeuft || !prompt.trim()}
                onClick={generieren}
              >
                {laeuft ? "Generiert…" : "✨ Generieren"}
              </button>
              <button type="button" className="ki-btn-sekundaer" onClick={schliessenUndZuruecksetzen}>
                Abbrechen
              </button>
            </div>
          </>
        )}

        {vorschlag && (
          <>
            <p className="ki-vorschau-hinweis">Vorschlag — wird beim Übernehmen ans Ende des Felds angehängt:</p>
            <div className="ki-vorschau-text">{vorschlag}</div>

            {fehler && <p className="ki-fehler">{fehler}</p>}

            <div className="ki-aktionen">
              <button type="button" className="ki-btn-primaer" onClick={uebernehmen}>
                ✓ Übernehmen
              </button>
              <button
                type="button"
                className="ki-btn-sekundaer"
                onClick={() => {
                  setVorschlag(null);
                }}
              >
                ↺ Neu versuchen
              </button>
              <button type="button" className="ki-btn-sekundaer" onClick={schliessenUndZuruecksetzen}>
                Verwerfen
              </button>
            </div>
          </>
        )}
      </div>
    </Fenster>
  );
}
