/**
 * Zufällige Fundstücke der digitalen Welt (Mark, 26.11.2026): „In Digimon
 * stehen ab und zu zufällige Gegenstände herum — Telefonzellen,
 * Kühlschränke, Disketten, CD-Player, Videorekorder, Fernseher … vor allem
 * Elektronikzeug.“ Hier als leuchtende Linienzeichnungen im Stil des
 * Gitters, eigene Zeichnungen (keine fremde Vorlage).
 *
 * viewBox 0 0 48 60, Unterkante y=60 = steht auf dem Gitterboden. Linie und
 * Füllung kommen aus Theme-Tokens (.gm-ding in gridmonster.css), die
 * Füllung verdeckt das Gitter dahinter.
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
] as const;

export type DingArt = (typeof DING_ARTEN)[number];

export const DING_NAMEN: Record<DingArt, string> = {
  telefonzelle: "Telefonzelle",
  kuehlschrank: "Kühlschrank",
  diskette: "Diskette",
  cdplayer: "CD-Player",
  videorekorder: "Videorekorder",
  fernseher: "Röhrenfernseher",
  ghettoblaster: "Ghettoblaster",
  monitor: "Computer-Monitor",
};

export function DingBild({ art }: { art: DingArt }) {
  return (
    <svg viewBox="0 0 48 60" className="gm-ding-svg" aria-hidden="true">
      {FORMEN[art]}
    </svg>
  );
}

const FORMEN: Record<DingArt, React.ReactNode> = {
  telefonzelle: (
    <>
      <rect x="10" y="6" width="28" height="54" rx="2" />
      <path d="M8 6h32" />
      <rect x="13" y="10" width="22" height="5" />
      <rect x="14" y="19" width="20" height="37" />
      <path d="M24 19v37M14 31h20M14 43h20" />
    </>
  ),
  kuehlschrank: (
    <>
      <rect x="11" y="4" width="26" height="56" rx="3" />
      <path d="M11 24h26M15 10v8M15 30v12" />
    </>
  ),
  diskette: (
    <>
      <path d="M4 20h34l6 6v34H4z" />
      <rect x="12" y="20" width="20" height="12" />
      <path d="M26 23v6" />
      <rect x="10" y="40" width="28" height="16" rx="1" />
    </>
  ),
  cdplayer: (
    <>
      <rect x="4" y="24" width="40" height="36" rx="6" />
      <circle cx="24" cy="42" r="13" />
      <circle cx="24" cy="42" r="3" />
      <path d="M36 28h4" />
    </>
  ),
  videorekorder: (
    <>
      <rect x="2" y="42" width="44" height="18" rx="2" />
      <rect x="6" y="47" width="20" height="4" />
      <path d="M6 55h8" />
      <rect x="32" y="46" width="10" height="5" />
      <circle cx="34" cy="56" r="1.2" />
      <circle cx="39" cy="56" r="1.2" />
    </>
  ),
  fernseher: (
    <>
      <path d="M24 16 16 4M24 16 32 4M10 54v6M38 54v6" />
      <rect x="4" y="16" width="40" height="38" rx="4" />
      <rect x="8" y="20" width="26" height="29" rx="6" />
      <circle cx="39.5" cy="26" r="2" />
      <circle cx="39.5" cy="34" r="2" />
    </>
  ),
  ghettoblaster: (
    <>
      <path d="M12 28v-6h24v6" />
      <rect x="2" y="28" width="44" height="32" rx="3" />
      <circle cx="12" cy="46" r="7" />
      <circle cx="36" cy="46" r="7" />
      <rect x="19" y="38" width="10" height="7" />
      <path d="M19 52h10" />
    </>
  ),
  monitor: (
    <>
      <path d="M14 50h20l4 10H10z" />
      <path d="M20 42v8M28 42v8" />
      <rect x="6" y="8" width="36" height="34" rx="3" />
      <rect x="10" y="12" width="28" height="24" rx="2" />
      <path d="M14 18h8M14 23h12" />
    </>
  ),
};
