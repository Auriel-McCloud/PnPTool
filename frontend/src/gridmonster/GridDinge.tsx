/**
 * Zufällige Fundstücke der digitalen Welt (Mark, 26.11.2026): „In Digimon
 * stehen ab und zu zufällige Gegenstände herum … vor allem Elektronikzeug.“
 * Nachschärfung (gleicher Tag): „nicht blau — mehr so Störfaktoren im Bild,
 * wie in der Digiwelt: ein Wald, wo plötzlich ein Fernseher steht.“
 *
 * Darum KEINE Leuchtlinien im Gitter-Stil, sondern echte Gegenstände: flache
 * Illustration in Materialfarben (rotes Blech, Holz, Beige-Plastik, Chrom)
 * mit dunkler Kontur — sie sollen bewusst NICHT zur Spiel-Optik passen.
 * Eigene Zeichnungen, keine fremde Vorlage, keine Marken/Logos (das Handheld
 * ist ein generisches Gerät, kein Nachbau).
 *
 * Farben kommen aus Theme-Tokens (--gm-ding-*), zugeordnet über Klassen
 * (f-rot, f-holz …) in gridmonster.css. Jede Zeichnung hat ihre eigene
 * viewBox, Unterkante = steht auf dem Boden. `hoehe` = Höhe in px auf der
 * Bodenebene, damit eine Telefonzelle größer ist als eine Diskette (kleine
 * Dinge leicht übertrieben, sonst sieht man sie nicht).
 */
export const DING_ARTEN = [
  "telefonzelle",
  "kuehlschrank",
  "diskette",
  "cdplayer",
  "videorekorder",
  "fernseher",
  "ghettoblaster",
  "monitor",
  "kassettenrekorder",
  "ampel",
  "handheld",
] as const;

export type DingArt = (typeof DING_ARTEN)[number];

interface DingDef {
  name: string;
  /** viewBox-Breite und -Höhe */
  vb: [number, number];
  /** Höhe auf dem Boden in px */
  hoehe: number;
  form: React.ReactNode;
}

export const DINGE: Record<DingArt, DingDef> = {
  telefonzelle: {
    name: "Telefonzelle",
    vb: [40, 90],
    hoehe: 110,
    form: (
      <>
        <path className="f-rot-dunkel" d="M4 10 Q20 2 36 10 V14 H4 Z" />
        <rect className="f-rot" x="5" y="14" width="30" height="72" />
        <rect className="f-weiss" x="8" y="16.5" width="24" height="6" />
        <path className="l" d="M12 19.5h16" />
        <rect className="f-glas-hell" x="9" y="26" width="22" height="56" />
        <rect className="f-schwarz" x="12" y="44" width="6" height="9" rx="1" />
        <path className="l-rot" d="M20 26v56M9 40h22M9 54h22M9 68h22" />
        <rect className="f-rot-dunkel" x="3" y="86" width="34" height="4" />
      </>
    ),
  },
  kuehlschrank: {
    name: "Kühlschrank",
    vb: [40, 72],
    hoehe: 92,
    form: (
      <>
        <rect className="f-schwarz" x="7" y="66" width="4" height="5" />
        <rect className="f-schwarz" x="29" y="66" width="4" height="5" />
        <rect className="f-weiss" x="4" y="2" width="32" height="66" rx="6" />
        <path className="f-weiss-dunkel" d="M30 2.6h0.5a5.5 5.5 0 0 1 5.5 5.5v54a5.5 5.5 0 0 1-5.5 5.5H30z" />
        <path className="l" d="M4 24h32" />
        <rect className="f-chrom" x="8" y="9" width="3" height="11" rx="1.5" />
        <rect className="f-chrom" x="8" y="28" width="3" height="18" rx="1.5" />
      </>
    ),
  },
  diskette: {
    name: "Diskette",
    vb: [40, 40],
    hoehe: 34,
    form: (
      <>
        <path className="f-schwarz" d="M2 2H34L38 6V38H2Z" />
        <rect className="f-chrom" x="10" y="2" width="18" height="13" />
        <rect className="f-schwarz" x="21" y="4" width="4" height="9" />
        <rect className="f-weiss" x="6" y="20" width="28" height="16" rx="1" />
        <path className="l-grau" d="M10 25h20M10 29h14" />
      </>
    ),
  },
  cdplayer: {
    name: "CD-Player",
    vb: [44, 44],
    hoehe: 36,
    form: (
      <>
        <rect className="f-chrom" x="2" y="2" width="40" height="40" rx="14" />
        <circle className="f-grau" cx="22" cy="21" r="15" />
        <circle className="l" cx="22" cy="21" r="9" />
        <circle className="f-grau-dunkel" cx="22" cy="21" r="3.5" />
        <rect className="f-schwarz" x="14" y="38" width="4" height="2" />
        <rect className="f-schwarz" x="20" y="38" width="4" height="2" />
        <rect className="f-schwarz" x="26" y="38" width="4" height="2" />
      </>
    ),
  },
  videorekorder: {
    name: "Videorekorder",
    vb: [70, 22],
    hoehe: 26,
    form: (
      <>
        <rect className="f-schwarz" x="6" y="18" width="5" height="3" />
        <rect className="f-schwarz" x="59" y="18" width="5" height="3" />
        <rect className="f-schwarz" x="1" y="2" width="68" height="16" rx="2" />
        <rect className="f-grau" x="4" y="5" width="62" height="10" />
        <rect className="f-schwarz" x="8" y="7" width="28" height="4" />
        <rect className="f-display" x="42" y="6.5" width="12" height="5" />
        <circle className="f-chrom" cx="59" cy="9" r="1.4" />
        <circle className="f-chrom" cx="63" cy="9" r="1.4" />
      </>
    ),
  },
  fernseher: {
    name: "Röhrenfernseher",
    vb: [60, 58],
    hoehe: 62,
    form: (
      <>
        <path className="l-dick" d="M30 14 18 2M30 14 42 2" />
        <rect className="f-schwarz" x="8" y="49" width="4" height="8" />
        <rect className="f-schwarz" x="48" y="49" width="4" height="8" />
        <ellipse className="f-schwarz" cx="30" cy="14" rx="6" ry="3" />
        <rect className="f-holz" x="2" y="14" width="56" height="36" rx="4" />
        <rect className="f-grau-dunkel" x="5.5" y="17.5" width="37" height="29" rx="7" />
        <rect className="f-glas" x="7" y="19" width="34" height="26" rx="6" />
        <path className="l-glas" d="M11 23q6-2.5 13-1" />
        <rect className="f-holz-dunkel" x="45" y="18" width="10" height="28" rx="1" />
        <circle className="f-chrom" cx="50" cy="24" r="3" />
        <circle className="f-chrom" cx="50" cy="32" r="3" />
        <path className="l" d="M46.5 39h7M46.5 41.5h7M46.5 44h7" />
      </>
    ),
  },
  ghettoblaster: {
    name: "Ghettoblaster",
    vb: [70, 44],
    hoehe: 44,
    form: (
      <>
        <path className="l-chrom" d="M14 12V6q0-3 3-3h36q3 0 3 3v6" />
        <rect className="f-chrom" x="1" y="12" width="68" height="30" rx="4" />
        <circle className="f-schwarz" cx="15" cy="28" r="10" />
        <circle className="f-grau-dunkel" cx="15" cy="28" r="4" />
        <circle className="f-schwarz" cx="55" cy="28" r="10" />
        <circle className="f-grau-dunkel" cx="55" cy="28" r="4" />
        <rect className="f-grau-dunkel" x="27" y="17" width="16" height="12" rx="1" />
        <rect className="f-glas" x="30" y="20" width="10" height="5" />
        <rect className="f-schwarz" x="27" y="33" width="3.5" height="3" />
        <rect className="f-schwarz" x="33.25" y="33" width="3.5" height="3" />
        <rect className="f-rot" x="39.5" y="33" width="3.5" height="3" />
      </>
    ),
  },
  monitor: {
    name: "Computer mit Röhrenmonitor",
    vb: [56, 60],
    hoehe: 60,
    form: (
      <>
        <rect className="f-beige-dunkel" x="22" y="37" width="12" height="6" />
        <rect className="f-beige" x="14" y="42" width="28" height="4" rx="1" />
        <rect className="f-beige" x="6" y="2" width="44" height="36" rx="3" />
        <rect className="f-beige-dunkel" x="10.5" y="5.5" width="35" height="27" rx="3" />
        <rect className="f-glas" x="13" y="8" width="30" height="22" rx="2" />
        <path className="l-display" d="M16 13h11M16 17h17M16 21h7M16 25h3" />
        <path className="f-beige" d="M4 49H52L55 58H1Z" />
        <path className="l" d="M8 52.5h40M6.5 55.5h43" />
      </>
    ),
  },
  kassettenrekorder: {
    name: "Kassettenrekorder",
    vb: [50, 36],
    hoehe: 38,
    form: (
      <>
        <path className="l-chrom" d="M15 8V4h20v4" />
        <rect className="f-grau" x="6" y="5" width="5" height="3.5" />
        <rect className="f-grau" x="12.5" y="5" width="5" height="3.5" />
        <rect className="f-rot" x="19" y="5" width="5" height="3.5" />
        <rect className="f-grau" x="25.5" y="5" width="5" height="3.5" />
        <rect className="f-schwarz" x="1" y="8" width="48" height="26" rx="3" />
        <rect className="f-grau-dunkel" x="5" y="13" width="23" height="16" rx="1" />
        <rect className="f-glas" x="8" y="16" width="17" height="8" rx="1" />
        <circle className="f-weiss" cx="12.5" cy="20" r="2.5" />
        <circle className="f-weiss" cx="20.5" cy="20" r="2.5" />
        <rect className="f-grau-dunkel" x="32" y="12" width="13" height="18" rx="2" />
        <path className="l-grau" d="M34.5 16h8M34.5 19.5h8M34.5 23h8M34.5 26.5h8" />
      </>
    ),
  },
  ampel: {
    name: "Ampel",
    vb: [24, 100],
    hoehe: 120,
    form: (
      <>
        <rect className="f-grau-dunkel" x="10" y="40" width="4" height="57" />
        <rect className="f-grau-dunkel" x="6" y="96" width="12" height="4" />
        <rect className="f-schwarz" x="4" y="2" width="16" height="40" rx="3" />
        <circle className="f-rot-an" cx="12" cy="10" r="4.5" />
        <circle className="f-aus" cx="12" cy="22" r="4.5" />
        <circle className="f-aus" cx="12" cy="34" r="4.5" />
      </>
    ),
  },
  handheld: {
    name: "Handheld-Konsole",
    vb: [34, 54],
    hoehe: 42,
    form: (
      <>
        <path className="f-grau-hell" d="M1 4a3 3 0 0 1 3-3h26a3 3 0 0 1 3 3v40a9 9 0 0 1-9 9H4a3 3 0 0 1-3-3Z" />
        <rect className="f-grau-dunkel" x="4" y="5" width="26" height="21" rx="2" />
        <rect className="f-lcd" x="8" y="8" width="18" height="15" />
        <path className="f-schwarz" d="M8 32h4v3h3v4h-3v3H8v-3H5v-4h3Z" />
        <circle className="f-rot-dunkel" cx="23" cy="39" r="2.6" />
        <circle className="f-rot-dunkel" cx="28.5" cy="35.5" r="2.6" />
        <path className="l-grau" d="M12 47.5l3-1.2M17 47.5l3-1.2M23 49l4-4M26 50.5l4-4" />
      </>
    ),
  },
};

export function DingBild({ art }: { art: DingArt }) {
  const d = DINGE[art];
  return (
    <svg viewBox={`0 0 ${d.vb[0]} ${d.vb[1]}`} className="gm-ding-svg" aria-hidden="true">
      {d.form}
    </svg>
  );
}

/** Breite in px auf dem Boden, aus Höhe und Seitenverhältnis. */
export function dingBreite(art: DingArt): number {
  const d = DINGE[art];
  return Math.round((d.hoehe * d.vb[0]) / d.vb[1]);
}
