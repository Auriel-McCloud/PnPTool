import "./kaestchen.css";

/** Schadensarten nach World of Darkness, von leicht nach schwer. */
export type Schadensart = "schlag" | "schwer" | "aggraviert";

/** Reihenfolge beim Weiterschalten — und zugleich, was ein Klick durchläuft. */
export const SCHADENSARTEN: { art: Schadensart; zeichen: string; name: string }[] = [
  { art: "schlag", zeichen: "/", name: "Schlagschaden" },
  { art: "schwer", zeichen: "X", name: "Schwerer Schaden" },
  { art: "aggraviert", zeichen: "✳", name: "Aggravierter Schaden" },
];

/**
 * Kästchenreihe für Zustandswerte — Gesundheit, Willenskraft, I.C.E.
 *
 * Auf dem Papierblatt zehn Kästchen in zwei Fünfergruppen; hier genauso.
 * Die ersten `max` zählen, der Rest bleibt angedeutet stehen, damit man
 * sieht wie viel Luft nach oben wäre.
 *
 * Bei Gesundheit wird nach Art unterschieden. **Schwererer Schaden steht
 * links**, wie beim Ausfüllen von Hand: aggraviert, dann schwer, dann Schlag.
 * Die Zeichen sind gezeichnet statt getippt — für aggravierten Schaden gibt
 * es kein passendes Schriftzeichen, das durchgestrichene X entsteht deshalb
 * aus drei Strichen in CSS.
 */
export function Kaestchen({
  max,
  verbraucht = 0,
  schaden,
  gesamt = 10,
  ton = "var(--neon)",
  onKlick,
}: {
  max: number;
  /** Einfacher Verbrauch ohne Arten (Willenskraft, I.C.E.). */
  verbraucht?: number;
  /** Nach Art getrennt (Gesundheit). Hat Vorrang vor `verbraucht`. */
  schaden?: { schlag: number; schwer: number; aggraviert: number };
  gesamt?: number;
  ton?: string;
  /** Klick auf ein Kästchen — Position von links, 0-basiert. */
  onKlick?: (index: number) => void;
}) {
  const felder = Array.from({ length: Math.max(gesamt, max) }, (_, i) => {
    if (i >= max) return { art: "ungenutzt" as const };
    if (schaden) {
      // Schwererer Schaden zuerst — so wird er auch von Hand eingetragen.
      if (i < schaden.aggraviert) return { art: "aggraviert" as const };
      if (i < schaden.aggraviert + schaden.schwer) return { art: "schwer" as const };
      if (i < schaden.aggraviert + schaden.schwer + schaden.schlag) return { art: "schlag" as const };
      return { art: "frei" as const };
    }
    return { art: i < max - verbraucht ? ("frei" as const) : ("verbraucht" as const) };
  });

  const belegt = schaden ? schaden.aggraviert + schaden.schwer + schaden.schlag : verbraucht;

  return (
    <div className="kt-reihe" style={{ "--kt-ton": ton } as React.CSSProperties}>
      {felder.map((f, i) => {
        const anklickbar = onKlick && f.art !== "ungenutzt";
        return (
          <span
            key={i}
            className="kt-feld"
            data-art={f.art}
            data-luecke={i > 0 && i % 5 === 0 ? "true" : undefined}
            data-klickbar={anklickbar ? "true" : undefined}
            role={anklickbar ? "button" : undefined}
            tabIndex={anklickbar ? 0 : undefined}
            title={anklickbar ? "Antippen: Schadensart weiterschalten" : undefined}
            onClick={anklickbar ? () => onKlick(i) : undefined}
            onKeyDown={
              anklickbar
                ? (e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onKlick(i);
                    }
                  }
                : undefined
            }
          />
        );
      })}
      <span className="kt-zahl">
        {max - belegt} / {max}
      </span>
    </div>
  );
}
