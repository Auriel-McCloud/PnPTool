import { schalteErklaerungen, useErklaerungen } from "./erklaerungen";
import "./infotipp.css";

/**
 * Der Schieberegler aus dem UI-Konzept: blendet die Erklärungszeichen
 * überall zugleich ein oder aus.
 *
 * Sitzt in der oberen Leiste und gilt für die ganze Oberfläche — ein
 * Fragezeichen neben jedem Begriff wäre dauerhaft zu viel, aber wer ein
 * Regelwerk gerade lernt, will es überall haben.
 */
export function ErklaerungSchalter() {
  const { an } = useErklaerungen(null);
  return (
    <button
      type="button"
      className="it-schalter"
      data-an={an ? "true" : "false"}
      onClick={schalteErklaerungen}
      aria-pressed={an}
      title={an ? "Erklärungen ausblenden" : "Erklärungen einblenden"}
    >
      <span className="it-regler" aria-hidden="true" />
      <span className="it-schalter-text">Erklärungen</span>
    </button>
  );
}
