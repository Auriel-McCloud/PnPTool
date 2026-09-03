/**
 * Theme-Zugriff aus TypeScript.
 *
 * Hintergrund: Cytoscape zeichnet auf Canvas und kennt keine CSS-Variablen.
 * Frueher standen die Graphfarben deshalb ein zweites Mal als Hexwerte in
 * `CampaignGraphView.tsx` — mit dem handschriftlichen Hinweis "beim Aendern
 * dort nachziehen". Genau das vergisst man, und beim zweiten Theme faellt es
 * auseinander.
 *
 * Statt zu spiegeln, liest `token()` den Wert zur Laufzeit aus dem
 * document-Element. Damit gibt es weiterhin nur eine Quelle der Wahrheit
 * (theme/tokens.css), auch fuer Canvas.
 */

/** Alle waehlbaren Themes. Erweitern = hier eintragen und CSS-Datei anlegen. */
export const THEMES = ["cyberpunk", "hextechpunk"] as const;
export type ThemeName = (typeof THEMES)[number];

export const THEME_LABELS: Record<ThemeName, string> = {
  cyberpunk: "Cyberpunk",
  hextechpunk: "Hextechpunk",
};

/**
 * Liest ein CSS-Token aus dem aktiven Theme.
 *
 * `getPropertyValue` liefert bei verketteten Variablen (`--neon: var(--p-cyan)`)
 * den *aufgeloesten* Wert, weil getComputedStyle rechnet — genau das brauchen
 * wir fuer Canvas.
 */
export function token(name: string, fallback = "#888"): string {
  if (typeof window === "undefined") return fallback;
  const wert = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return wert || fallback;
}

/** Mehrere Tokens auf einmal — spart wiederholtes getComputedStyle. */
export function tokens<T extends Record<string, string>>(namen: T): Record<keyof T, string> {
  if (typeof window === "undefined") {
    return Object.fromEntries(Object.keys(namen).map((k) => [k, "#888"])) as Record<keyof T, string>;
  }
  const stil = getComputedStyle(document.documentElement);
  const raus = {} as Record<keyof T, string>;
  for (const [schluessel, variable] of Object.entries(namen)) {
    raus[schluessel as keyof T] = stil.getPropertyValue(variable).trim() || "#888";
  }
  return raus;
}

const SPEICHER_SCHLUESSEL = "pnptool-theme";

/** Aktives Theme setzen. Wirkt sofort auf die ganze Oberflaeche. */
export function themeSetzen(name: ThemeName) {
  document.documentElement.dataset.theme = name;
  try {
    localStorage.setItem(SPEICHER_SCHLUESSEL, name);
  } catch {
    // Privater Modus o.ae. — Theme gilt dann nur fuer diese Sitzung.
  }
}

/** Gespeichertes Theme oder der Standard. */
export function themeLesen(): ThemeName {
  try {
    const gespeichert = localStorage.getItem(SPEICHER_SCHLUESSEL);
    if (gespeichert && (THEMES as readonly string[]).includes(gespeichert)) {
      return gespeichert as ThemeName;
    }
  } catch {
    /* ignorieren */
  }
  return "cyberpunk";
}

/**
 * Kampagnenbezogene Anpassungen, die ueber die Themewahl hinausgehen:
 * eigenes Hintergrundbild, eigene Leitfarbe, ruhigeres Leuchten.
 *
 * Bewusst getrennt vom Theme: das Theme ist die Grundstimmung
 * (Cyberpunk/Hextechpunk), das hier die Handschrift EINER Kampagne.
 */
export interface KampagnenOptik {
  hintergrundBild?: string;
  hintergrundPosition?: string;
  hintergrundSchleier?: number;
  akzent?: string;
  signal?: string;
  ladebalken?: string;
}

/** Uebersetzt die Kampagnenoptik in Inline-CSS-Variablen fuer die Huelle. */
export function optikStil(optik?: KampagnenOptik): React.CSSProperties {
  if (!optik) return {};
  const stil: Record<string, string> = {};
  if (optik.hintergrundBild) stil["--hintergrund-bild"] = `url("${optik.hintergrundBild}")`;
  if (optik.hintergrundPosition) stil["--hintergrund-position"] = optik.hintergrundPosition;
  if (optik.hintergrundSchleier !== undefined) {
    stil["--hintergrund-schleier"] = String(optik.hintergrundSchleier);
  }
  if (optik.akzent) stil["--neon"] = optik.akzent;
  if (optik.signal) stil["--signal"] = optik.signal;
  if (optik.ladebalken) stil["--ladebalken"] = optik.ladebalken;
  return stil as React.CSSProperties;
}
