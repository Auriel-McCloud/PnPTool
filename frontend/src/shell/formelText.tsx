import type { ReactNode } from "react";
import "./formelText.css";

/**
 * Kleine $-Mathe in Namen (Mark, 30.09.2026: Gegenstand „$\beta^+$-Isotop“
 * soll wie β⁺-Isotop aussehen, nicht als `$ \ beta ^+$ - istop`).
 *
 * Kein KaTeX — nur die üblichen griechischen Buchstaben und Hoch-/Tiefstellung,
 * die in Gegenstands- und Entitätsnamen vorkommen. Unbekannte Befehle bleiben
 * stehen. Leerzeichen in `$...$` werden geschluckt, damit `$ \ beta ^+$`
 * dasselbe ergibt wie `$\beta^+$`.
 */

const BEFEHLE: [RegExp, string][] = [
  [/\\beta/gi, "β"],
  [/\\alpha/gi, "α"],
  [/\\gamma/gi, "γ"],
  [/\\delta/gi, "δ"],
  [/\\epsilon/gi, "ε"],
  [/\\theta/gi, "θ"],
  [/\\lambda/gi, "λ"],
  [/\\mu/gi, "μ"],
  [/\\pi/gi, "π"],
  [/\\sigma/gi, "σ"],
  [/\\phi/gi, "φ"],
  [/\\omega/gi, "ω"],
  [/\\pm/g, "±"],
  [/\\times/g, "×"],
  [/\\cdot/g, "·"],
];

const HOCH: Record<string, string> = {
  "+": "⁺",
  "-": "⁻",
  "0": "⁰",
  "1": "¹",
  "2": "²",
  "3": "³",
  "4": "⁴",
  "5": "⁵",
  "6": "⁶",
  "7": "⁷",
  "8": "⁸",
  "9": "⁹",
};

const TIEF: Record<string, string> = {
  "+": "₊",
  "-": "₋",
  "0": "₀",
  "1": "₁",
  "2": "₂",
  "3": "₃",
  "4": "₄",
  "5": "₅",
  "6": "₆",
  "7": "₇",
  "8": "₈",
  "9": "₉",
};

function ersetzeZeichen(text: string, tabelle: Record<string, string>): string {
  return [...text].map((c) => tabelle[c] ?? c).join("");
}

export function mathZuSchrift(src: string): string {
  let s = src.replace(/\s+/g, "");
  for (const [re, zu] of BEFEHLE) s = s.replace(re, zu);
  s = s.replace(/\^\{([^}]+)\}/g, (_g, x: string) => ersetzeZeichen(x, HOCH));
  s = s.replace(/\^([+\-0-9])/g, (_g, c: string) => HOCH[c] ?? c);
  s = s.replace(/_\{([^}]+)\}/g, (_g, x: string) => ersetzeZeichen(x, TIEF));
  s = s.replace(/_([+\-0-9])/g, (_g, c: string) => TIEF[c] ?? c);
  return s;
}

/** Name ohne `$`, für title/aria und Fenster-Titel als Klartext. */
export function formelKlartext(text: string): string {
  return text.replace(/\$([^$]*)\$/g, (_g, m: string) => mathZuSchrift(m));
}

export function FormelText({ text }: { text: string }): ReactNode {
  if (!text.includes("$")) return text;
  const teile: ReactNode[] = [];
  const re = /\$([^$]*)\$/g;
  let last = 0;
  let treffer: RegExpExecArray | null;
  let i = 0;
  while ((treffer = re.exec(text))) {
    if (treffer.index > last) teile.push(text.slice(last, treffer.index));
    teile.push(
      <span key={i++} className="formel-math">
        {mathZuSchrift(treffer[1])}
      </span>,
    );
    last = treffer.index + treffer[0].length;
  }
  if (last < text.length) teile.push(text.slice(last));
  return teile;
}
