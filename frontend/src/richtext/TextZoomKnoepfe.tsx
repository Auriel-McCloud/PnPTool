import { useTextZoom } from "./textzoom";

/**
 * Zoom-Knöpfe für Beschreibungs-/Notizen-Boxen (A− / A+).
 *
 * Erscheint sowohl in `RichTextEditor` (Werkzeugleiste) als auch in
 * `RichTextView` (reine Leseansicht, z.B. Spieler-Ansicht/Kachel-Vorschau)
 * — Mark wollte beides. Wirkt global über `textzoom.ts`: ein Klick hier
 * vergrößert auch jede andere gerade offene Box.
 */
export function TextZoomKnoepfe() {
  const { stufe, istMin, istMax, vergroessern, verkleinern } = useTextZoom();

  return (
    <span className="rt-zoom" title={`Lesegröße ${stufe}%`}>
      <button
        type="button"
        className="rt-zoom-knopf"
        onMouseDown={(e) => e.preventDefault()}
        onClick={verkleinern}
        disabled={istMin}
        title="Schrift verkleinern"
        aria-label="Schrift verkleinern"
      >
        A−
      </button>
      <span className="rt-zoom-wert">{stufe}%</span>
      <button
        type="button"
        className="rt-zoom-knopf"
        onMouseDown={(e) => e.preventDefault()}
        onClick={vergroessern}
        disabled={istMax}
        title="Schrift vergrößern"
        aria-label="Schrift vergrößern"
      >
        A+
      </button>
    </span>
  );
}
