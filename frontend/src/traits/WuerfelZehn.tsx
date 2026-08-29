/**
 * Zehnseiter als Symbol.
 *
 * Gedacht für Stellen, an denen eine Zahl *Würfel* meint und nicht einen
 * Wert — "7" allein liest sich sonst als Wert 7. Ausgeschrieben ("7 Würfel")
 * sprengt die Zeile, das Symbol nicht.
 *
 * Ein W10 ist ein Trapezoeder: von vorn eine sechseckige Silhouette mit einer
 * drachenförmigen Fläche in der Mitte. Bewusst als Umriss gezeichnet, damit er
 * bei 16px noch erkennbar bleibt und die Farbe vom Text erbt.
 */
export function WuerfelZehn({ groesse = 16 }: { groesse?: number }) {
  return (
    <svg
      width={groesse}
      height={groesse}
      viewBox="0 0 100 100"
      fill="none"
      stroke="currentColor"
      strokeWidth="6"
      strokeLinejoin="round"
      // Rein schmückend: die Zahl daneben sagt bereits alles.
      aria-hidden="true"
      focusable="false"
    >
      <path d="M50 5 L96 35 L81 85 L50 96 L19 85 L4 35 Z" />
      <path d="M50 5 L26 49 L50 70 L74 49 Z" />
      <path d="M26 49 L19 85 M74 49 L81 85 M50 70 L50 96" strokeWidth="4" />
    </svg>
  );
}
