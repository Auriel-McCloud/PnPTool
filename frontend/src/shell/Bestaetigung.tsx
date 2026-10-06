import { createPortal } from "react-dom";
import { useHintergrundSchliessen } from "./hintergrundSchliessen";
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
  // Nur schliessen, wenn der Klick auch daneben BEGONNEN hat — sonst
  // schliesst eine über den Rand gezogene Textauswahl im Bestätigungstext
  // versehentlich den Dialog (siehe hintergrundSchliessen.ts).
  const hintergrundProps = useHintergrundSchliessen(onNein);
  return createPortal(
    <div className="best-huelle" {...hintergrundProps}>
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
