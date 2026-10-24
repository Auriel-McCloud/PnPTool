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
  gruppenMax,
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
  /**
   * Höchstes `max` innerhalb der ganzen Attributgruppe (Charakterblatt.tsx::
   * reihe) — Mark, 24.10.2026: "auf den gleichen Nenner bringen". Damit alle
   * Werte einer Gruppe gleich lang aussehen, auch wenn z.B. Geschicklichkeit
   * durch Erfahrung schon höher steigen durfte als Körperkraft. Kreise
   * zwischen `max` und hier gehören NICHT zu diesem Wert — rein zur
   * Gruppen-Ausrichtung, durchgestrichen und nie anklickbar (ein Augment
   * könnte das eigene `max` später trotzdem noch anheben).
   */
  gruppenMax?: number;
}) {
  const gesamt = Math.max(max, gruppenMax ?? 0, 0);
  const dots = Array.from({ length: gesamt }, (_, i) => i + 1);
  const grenze = waehlbarBis ?? max;

  function handleClick(n: number) {
    if (!onChange) return;
    // Jenseits des eigenen Maximums (reine Gruppen-Ausrichtung), über der
    // Grenze oder im festen Sockel wird nichts entschieden.
    if (n > max || n > grenze || n <= fest) return;
    // Klick auf den aktuell obersten gefüllten Punkt reduziert um 1 (Standard
    // WoD-Bogen-UX), Klick woanders setzt den Wert direkt.
    onChange(n === value ? n - 1 : n);
  }

  return (
    <span style={{ display: "inline-flex", gap: 3, flexWrap: "nowrap", verticalAlign: "middle" }}>
      {dots.map((n) => {
        const gefuellt = n <= value;
        const istFest = n <= fest;
        // Jenseits des eigenen Maximums: existiert nur, damit die Gruppe
        // gleich lang aussieht — gehört diesem Wert gar nicht, daher immer
        // gesperrt und optisch klar von "gesperrt" (eigenes, aber noch nicht
        // wählbares Potenzial) unterschieden.
        const istPotential = n > max;
        const gesperrt = !istPotential && n > grenze;
        const anklickbar = Boolean(onChange) && !istFest && !gesperrt && !istPotential;

        // Vier Zustände, die sich nicht überlagern dürfen: der feste Sockel
        // ist grau (da hat die Rasse entschieden), das Wählbare trägt die
        // Farbe der Wertegruppe, das Gesperrte ist nur angedeutet, und das
        // Gruppen-Potenzial trägt ein × statt Füllung.
        const farbe = istFest ? "var(--text-aus)" : "var(--cb-ton, var(--neon))";
        return (
          <span
            key={n}
            onClick={() => handleClick(n)}
            role={anklickbar ? "button" : undefined}
            title={
              istFest
                ? "Kommt von deiner Rasse — steht fest"
                : istPotential
                  ? "Nur zur Ausrichtung mit der Attributgruppe — mit Augments eventuell nutzbar"
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
                : `1.5px ${gesperrt || istPotential ? "dashed" : "solid"} var(--linie-hell)`,
              // --cb-ton setzt die jeweilige Wertegruppe (Charakterblatt);
              // ohne Vorgabe bleibt es beim Cyan der Oberfläche.
              background: gefuellt ? farbe : "transparent",
              // Gesperrtes und Gruppen-Potenzial sollen erkennbar bleiben,
              // aber nicht mitreden — Potenzial noch blasser als Gesperrtes,
              // weil es noch nicht mal zu diesem Wert gehört.
              opacity: istPotential ? 0.3 : gesperrt ? 0.35 : 1,
              cursor: anklickbar ? "pointer" : "default",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.65em",
              lineHeight: 1,
              color: "var(--text-aus)",
              flexShrink: 0,
            }}
          >
            {istPotential ? "✕" : null}
          </span>
        );
      })}
    </span>
  );
}
