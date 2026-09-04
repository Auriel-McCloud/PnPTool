import { createPortal } from "react-dom";
import "./bestaetigung.css";

/**
 * Bestätigungsdialog im Commlink-Stil.
 *
 * Ersetzt `window.confirm()` — das native Popup passt nicht zum Theme.
 */
export function Bestaetigung({
  titel,
  text,
  onJa,
  onNein,
  jaText = "Ja",
  neinText = "Abbrechen",
}: {
  titel: string;
  text: string;
  onJa: () => void;
  onNein: () => void;
  jaText?: string;
  neinText?: string;
}) {
  return createPortal(
    <div className="best-huelle" onClick={onNein}>
      <div className="best-kasten" onClick={(e) => e.stopPropagation()}>
        <h2 className="best-titel">{titel}</h2>
        <p className="best-text">{text}</p>
        <div className="best-knoepfe">
          <button type="button" className="best-nein" onClick={onNein}>
            {neinText}
          </button>
          <button type="button" className="best-ja" onClick={onJa}>
            {jaText}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
