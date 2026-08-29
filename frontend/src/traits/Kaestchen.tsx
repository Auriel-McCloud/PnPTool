import "./kaestchen.css";

/**
 * Kästchenreihe für Zustandswerte — Gesundheit, Willenskraft, I.C.E.
 *
 * Auf dem Papierblatt sind das zehn Kästchen in zwei Fünfergruppen. Hier
 * genauso: die ersten `max` Kästchen zählen, davon sind `verbraucht` abgehakt.
 * Was über `max` hinausgeht, bleibt sichtbar aber leer — auf dem Papier kann
 * man die Reihe ja auch nicht abschneiden, und man sieht auf einen Blick,
 * wie viel Luft nach oben wäre.
 */
export function Kaestchen({
  max,
  verbraucht,
  gesamt = 10,
  ton = "var(--neon)",
  titel,
}: {
  max: number;
  verbraucht: number;
  /** Wie viele Kästchen gezeichnet werden, auch die ungenutzten. */
  gesamt?: number;
  ton?: string;
  titel?: string;
}) {
  const felder = Array.from({ length: Math.max(gesamt, max) }, (_, i) => {
    if (i >= max) return "ungenutzt";
    return i < max - verbraucht ? "frei" : "verbraucht";
  });

  return (
    <div className="kt-reihe" style={{ "--kt-ton": ton } as React.CSSProperties} title={titel}>
      {felder.map((art, i) => (
        <span
          key={i}
          className="kt-feld"
          data-art={art}
          // Fünfergruppen wie auf dem Blatt: nach dem fünften Kästchen Luft
          data-luecke={i > 0 && i % 5 === 0 ? "true" : undefined}
          aria-hidden="true"
        />
      ))}
      <span className="kt-zahl">
        {max - verbraucht} / {max}
      </span>
    </div>
  );
}
