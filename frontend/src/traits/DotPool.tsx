// Generische Punkte-Anzeige (wie im Neotopia-Charakterbogen: gefüllte/leere
// Kreise statt Zahlen). Funktioniert für beliebige Maxima — normale Werte
// gehen bis 5/6, aber ein einzelner besonders mächtiger Charakter kann für
// einen Wert auch 15 oder 20 haben, ohne dass die Komponente das einschränkt.
export function DotPool({
  value,
  max,
  onChange,
  size,
}: {
  value: number;
  max: number;
  onChange?: (value: number) => void;
  /** Ohne Angabe aus --dot-groesse, damit enge Ansichten sie verkleinern können. */
  size?: number;
}) {
  const dots = Array.from({ length: Math.max(max, 0) }, (_, i) => i + 1);

  function handleClick(n: number) {
    if (!onChange) return;
    // Klick auf den aktuell obersten gefüllten Punkt reduziert um 1 (Standard
    // WoD-Bogen-UX), Klick woanders setzt den Wert direkt.
    onChange(n === value ? n - 1 : n);
  }

  return (
    <span style={{ display: "inline-flex", gap: 3, flexWrap: "nowrap", verticalAlign: "middle" }}>
      {dots.map((n) => (
        <span
          key={n}
          onClick={() => handleClick(n)}
          role={onChange ? "button" : undefined}
          style={{
            width: size ?? "var(--dot-groesse, 14px)",
            height: size ?? "var(--dot-groesse, 14px)",
            borderRadius: "50%",
            border: n <= value
              ? "1.5px solid var(--cb-ton, var(--neon))"
              : "1.5px solid var(--linie-hell)",
            // --cb-ton setzt die jeweilige Wertegruppe (Charakterblatt);
            // ohne Vorgabe bleibt es beim Cyan der Oberfläche.
            background: n <= value ? "var(--cb-ton, var(--neon))" : "transparent",
            cursor: onChange ? "pointer" : "default",
            display: "inline-block",
            flexShrink: 0,
          }}
        />
      ))}
    </span>
  );
}
