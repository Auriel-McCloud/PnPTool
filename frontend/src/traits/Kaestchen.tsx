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
/**
 * Ab hier wird die Reihe zu lang zum Zählen und kippt in die Leisten-Form.
 * Zehn ist die Zahl vom Papierblatt (zwei Fünfergruppen) — darunter ändert
 * sich also nichts an dem, was Mark gewohnt ist.
 */
export const OVERFLOW_AB = 10;

/** So viele Kästchen bleiben am Ende immer einzeln stehen. */
export const ENDKAESTCHEN = 5;

export function Kaestchen({
  max,
  verbraucht = 0,
  schaden,
  gesamt = 10,
  ton = "var(--neon)",
  onKlick,
  onOeffnen,
  einzeln = false,
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
  /**
   * Die ganze Leiste antippen, um die Vollansicht zu öffnen. Ab
   * `OVERFLOW_AB` ist das der einzige sinnvolle Weg: die Pufferzellen sind
   * zu schmal, um einzeln getroffen zu werden — gezählt und eingetragen
   * wird dann im Fenster.
   */
  onOeffnen?: () => void;
  /**
   * Immer alle Kästchen einzeln zeichnen, auch über `OVERFLOW_AB`. Genau
   * dafür gibt es die Vollansicht im Zustandsfenster — dort wäre eine
   * Leiste sinnlos, sie ist ja der Grund, warum man das Fenster geöffnet hat.
   */
  einzeln?: boolean;
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

  // --- Lange Leisten: Puffer als Zellen, die letzten fünf als Kästchen ---
  //
  // Genau dort genau, wo es zählt: bei 16 von 18 interessiert "fast voll",
  // bei 2 von 18 zählt man. Deshalb ist der vordere Teil eine Zellenleiste
  // (Schadensart über die Füllhöhe: ein Drittel Schlag, zwei Drittel
  // tödlich, ganz unheilbar) und das Ende bleibt bei den gewohnten Zeichen
  // vom Papierblatt. Läuft der Puffer leer, kippt die Anzeige sichtbar in
  // den Ernstfall — und das ist genau der Moment, in dem es das soll.
  if (max > OVERFLOW_AB && !einzeln) {
    const pufferAnzahl = max - ENDKAESTCHEN;
    const inhalt = (
      <>
        <span className="kt-puffer">
          {felder.slice(0, pufferAnzahl).map((f, i) => (
            <i
              key={i}
              data-art={f.art}
              data-luecke={i > 0 && (i + 1) % 5 === 0 ? "true" : undefined}
            />
          ))}
        </span>
        <span className="kt-enden">
          {felder.slice(pufferAnzahl, max).map((f, i) => (
            <span key={i} className="kt-feld" data-art={f.art} />
          ))}
        </span>
        <span className="kt-zahl">
          {max - belegt} / {max}
        </span>
      </>
    );
    if (!onOeffnen) {
      return (
        <div className="kt-reihe kt-lang" style={{ "--kt-ton": ton } as React.CSSProperties}>
          {inhalt}
        </div>
      );
    }
    return (
      <button
        type="button"
        className="kt-reihe kt-lang kt-oeffner"
        style={{ "--kt-ton": ton } as React.CSSProperties}
        onClick={onOeffnen}
        title="Antippen: alle Kästchen, Schaden und Heilung eintragen"
      >
        {inhalt}
      </button>
    );
  }

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
