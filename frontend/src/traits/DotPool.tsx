// Generische Punkte-Anzeige (wie im Neotopia-Charakterbogen: gefüllte/leere
// Kreise statt Zahlen). Funktioniert für beliebige Maxima — normale Werte
// gehen bis 5/6, aber ein einzelner besonders mächtiger Charakter kann für
// einen Wert auch 15 oder 20 haben, ohne dass die Komponente das einschränkt.
export function DotPool({
  value,
  max,
  onChange,
  size,
  fest = 0,
  waehlbarBis,
}: {
  value: number;
  /** Wie viele Punkte überhaupt gezeichnet werden. */
  max: number;
  onChange?: (value: number) => void;
  /** Ohne Angabe aus --dot-groesse, damit enge Ansichten sie verkleinern können. */
  size?: number;
  /**
   * Die ersten `fest` Punkte sind gesetzt und **nicht wegklickbar** — in der
   * Charaktererstellung der Startwert aus der Rasse. Sie werden grau
   * gezeichnet: sichtbar vorhanden, aber nichts, worüber man entscheidet.
   */
  fest?: number;
  /**
   * Bis hierher darf gewählt werden; alles darüber wird **blass** gezeichnet
   * und ist nicht anklickbar. So zeigt die Reihe das volle Potenzial eines
   * Wertes, ohne zu suggerieren, dass man es jetzt schon kaufen könnte
   * (Mark, 11.09.2026: "dann sieht man die Wahrheit und man kann nur das
   * vergeben was vergebbar ist"). Ohne Angabe ist alles bis `max` wählbar.
   */
  waehlbarBis?: number;
}) {
  const dots = Array.from({ length: Math.max(max, 0) }, (_, i) => i + 1);
  const grenze = waehlbarBis ?? max;

  function handleClick(n: number) {
    if (!onChange) return;
    // Über der Grenze und im festen Sockel wird nichts entschieden.
    if (n > grenze || n <= fest) return;
    // Klick auf den aktuell obersten gefüllten Punkt reduziert um 1 (Standard
    // WoD-Bogen-UX), Klick woanders setzt den Wert direkt.
    onChange(n === value ? n - 1 : n);
  }

  return (
    <span style={{ display: "inline-flex", gap: 3, flexWrap: "nowrap", verticalAlign: "middle" }}>
      {dots.map((n) => {
        const gefuellt = n <= value;
        const istFest = n <= fest;
        const gesperrt = n > grenze;
        const anklickbar = Boolean(onChange) && !istFest && !gesperrt;

        // Drei Zustände, die sich nicht überlagern dürfen: der feste Sockel
        // ist grau (da hat die Rasse entschieden), das Wählbare trägt die
        // Farbe der Wertegruppe, das Gesperrte ist nur angedeutet.
        const farbe = istFest ? "var(--text-aus)" : "var(--cb-ton, var(--neon))";
        return (
          <span
            key={n}
            onClick={() => handleClick(n)}
            role={anklickbar ? "button" : undefined}
            title={
              istFest
                ? "Kommt von deiner Rasse — steht fest"
                : gesperrt
                  ? "Über dem Erstellungsmaximum: später mit Erfahrung erreichbar"
                  : undefined
            }
            style={{
              width: size ?? "var(--dot-groesse, 14px)",
              height: size ?? "var(--dot-groesse, 14px)",
              borderRadius: "50%",
              border: gefuellt
                ? `1.5px solid ${farbe}`
                : `1.5px ${gesperrt ? "dashed" : "solid"} var(--linie-hell)`,
              // --cb-ton setzt die jeweilige Wertegruppe (Charakterblatt);
              // ohne Vorgabe bleibt es beim Cyan der Oberfläche.
              background: gefuellt ? farbe : "transparent",
              // Das Gesperrte soll erkennbar bleiben, aber nicht mitreden.
              opacity: gesperrt ? 0.35 : 1,
              cursor: anklickbar ? "pointer" : "default",
              display: "inline-block",
              flexShrink: 0,
            }}
          />
        );
      })}
    </span>
  );
}
