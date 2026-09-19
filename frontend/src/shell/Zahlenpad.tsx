import "./zahlenpad.css";

/**
 * Eigenes Zahlenpad statt Systemtastatur — wiederverwendet in
 * `ZustandFenster` (Schaden/Heilen als Zahl) und `RuestungsTreffer`
 * (Stärke eines Treffers). Vorher gab es zwei verschiedene Eingabewege für
 * dieselbe Sache: hier das große Pad, dort ein rohes `<input type="number">`
 * mit Systemtastatur — Mark hat das zurecht als inkonsistent bemängelt.
 *
 * Reiner Anzeige-/Eingabebaustein: hält keinen eigenen Zustand, der
 * Aufrufer verwaltet die Zeichenkette (damit er sie z.B. beim Öffnen des
 * Fensters zurücksetzen oder in eine Zahl umwandeln kann).
 */
export function Zahlenpad({
  wert,
  onZiffer,
  onLoeschen,
  onAlleLoeschen,
  ton,
  maxStellen = 2,
}: {
  /** Aktuelle Eingabe als Zeichenkette — leer heisst "0". */
  wert: string;
  onZiffer: (ziffer: string) => void;
  /** Rücktaste — letztes Zeichen entfernen. */
  onLoeschen: () => void;
  /** "C" — Eingabe komplett leeren. */
  onAlleLoeschen: () => void;
  /** Leitfarbe der Anzeige, standardmässig Textfarbe. */
  ton?: string;
  /** Wie viele Stellen die Eingabe höchstens haben darf. */
  maxStellen?: number;
}) {
  function ziffer(z: string) {
    if (wert.length >= maxStellen && wert !== "0") return;
    onZiffer(z);
  }

  return (
    <div className="zp-padzeile" style={ton ? ({ "--zp-ton": ton } as React.CSSProperties) : undefined}>
      <div className="zp-pad">
        {["7", "8", "9", "4", "5", "6", "1", "2", "3"].map((z) => (
          <button key={z} type="button" onClick={() => ziffer(z)}>
            {z}
          </button>
        ))}
        <button type="button" onClick={() => ziffer("0")}>
          0
        </button>
        <button type="button" onClick={onLoeschen}>
          ⌫
        </button>
        <button type="button" onClick={onAlleLoeschen}>
          C
        </button>
      </div>
      <div className="zp-anzeige" aria-live="polite">
        {wert || "0"}
      </div>
    </div>
  );
}
