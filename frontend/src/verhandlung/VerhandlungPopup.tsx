import { useState } from "react";
import { createPortal } from "react-dom";
import { useMitteilungen } from "../mitteilungen/MitteilungenKontext";
import type { Verhandlung } from "./api";
import "./verhandlung.css";

/**
 * Das Popup eines eingehenden Verhandlungsangebots (SL-Vorschlag).
 *
 * Gebaut nach dem Vorbild von `mitteilungen/MitteilungPopup.tsx` — Portal an
 * `document.body`, liegt über allem, auch über offenen Fenstern.
 *
 * **Zwei Zustände in einer Komponente:** solange offen (Status "OFFEN")
 * zeigt es die Positionen mit Annehmen/Ablehnen; nach der Antwort zeigt
 * dieselbe Fläche kurz das Ergebnis (angenommen/abgelehnt), bevor sie sich
 * schließt — genau wie die Erfolgsmeldung nach `logic.ausfuehren` es dem SL
 * verspricht. Der Kontext (`useMitteilungen`) entfernt das Angebot schon aus
 * seiner eigenen Schlange, sobald die Antwort abgeschickt ist; das Ergebnis
 * lebt deshalb kurz in einem lokalen State weiter.
 */
export function VerhandlungPopup() {
  const { verhandlungAktuell, verhandlungenWartend, verhandlungAntworten } = useMitteilungen();
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [ergebnis, setErgebnis] = useState<Verhandlung | null>(null);

  const angezeigt = ergebnis ?? verhandlungAktuell;
  if (!angezeigt) return null;

  async function antworten(angenommen: boolean) {
    setLaeuft(true);
    setFehler(null);
    try {
      const aktualisiert = await verhandlungAntworten(angenommen);
      if (aktualisiert) setErgebnis(aktualisiert);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Antwort konnte nicht gesendet werden");
    } finally {
      setLaeuft(false);
    }
  }

  const entschieden = angezeigt.status !== "OFFEN";
  const angenommenErgebnis = angezeigt.status === "ANGENOMMEN";

  return createPortal(
    <div className="vh-popup-huelle">
      <div
        className={`vh-popup${entschieden ? " vh-popup-entschieden" : ""}`}
        role="alertdialog"
        aria-live="assertive"
        tabIndex={-1}
        ref={(el) => el?.focus()}
      >
        <div className="vh-popup-kopf">
          <span className="vh-popup-zeichen" aria-hidden="true">
            {entschieden ? (angenommenErgebnis ? "✓" : "✕") : "¥"}
          </span>
          <span className="vh-popup-titel">
            {entschieden
              ? angenommenErgebnis
                ? "Angebot angenommen"
                : "Angebot abgelehnt"
              : "Angebot der Spielleitung"}
          </span>
        </div>

        <div className="vh-popup-inhalt">
          {!entschieden && (
            <ul className="vh-positionen">
              {angezeigt.positionen.map((p, i) => (
                <li key={i} className="vh-position">
                  <span className="vh-position-bezeichnung">{p.bezeichnung}</span>
                  <span className="vh-position-betrag">{p.betrag.toLocaleString("de-AT")}¥</span>
                </li>
              ))}
            </ul>
          )}
          <div className="vh-gesamt">
            <span>{entschieden ? (angenommenErgebnis ? "Bezahlt" : "Nicht bezahlt") : "Gesamt"}</span>
            <strong>{angezeigt.gesamtbetrag.toLocaleString("de-AT")}¥</strong>
          </div>
          {angenommenErgebnis && angezeigt.ergebnis?.kapitalNeu != null && (
            <p className="vh-restguthaben">
              Verbleibendes Guthaben: <strong>{Number(angezeigt.ergebnis.kapitalNeu).toLocaleString("de-AT")}¥</strong>
            </p>
          )}
          {fehler && <p className="vh-fehler">{fehler}</p>}
        </div>

        <div className="vh-popup-fuss">
          {verhandlungenWartend > 0 && !entschieden && (
            <span className="vh-popup-rest">noch {verhandlungenWartend} weitere</span>
          )}
          {entschieden ? (
            <button type="button" className="vh-btn-ok" onClick={() => setErgebnis(null)}>
              OK
            </button>
          ) : (
            <>
              <button type="button" className="vh-btn-ablehnen" disabled={laeuft} onClick={() => antworten(false)}>
                Ablehnen
              </button>
              <button type="button" className="vh-btn-annehmen" disabled={laeuft} onClick={() => antworten(true)}>
                {laeuft ? "Sendet…" : "Annehmen"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}
