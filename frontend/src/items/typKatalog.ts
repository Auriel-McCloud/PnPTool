/**
 * Gemeinsamer Typ-Katalog für Gegenstände — ein Symbol je Typ für die
 * Kachel-Auswahl beim Anlegen (siehe TypKachelAuswahl.tsx).
 *
 * Der Typ ist seit 22.09.2026 nach dem Anlegen fix (Marks Entscheidung:
 * "wer's falsch gewählt hat, löscht und legt neu an") — deshalb bekommt das
 * Anlegen-Popup diese große Kachel-Auswahl statt eines kleinen Dropdowns,
 * das man später sowieso nicht mehr korrigieren kann.
 */
export interface TypEintrag {
  typ: string;
  symbol: string;
}

export const TYP_KATALOG: TypEintrag[] = [
  { typ: "Waffe", symbol: "⚔" },
  { typ: "Rüstung", symbol: "🛡" },
  { typ: "Cyberware", symbol: "⚙" },
  { typ: "Bioware", symbol: "🧬" },
  { typ: "Hexware", symbol: "✦" },
  { typ: "Droge", symbol: "💊" },
  { typ: "Verbrauchsgegenstand", symbol: "◐" },
  { typ: "Werkzeug", symbol: "🔧" },
  { typ: "Fahrzeug", symbol: "⛭" },
  { typ: "Drohne", symbol: "◭" },
  { typ: "Behälter", symbol: "▣" },
  { typ: "Commlink", symbol: "📱" },
  { typ: "Cyberdeck", symbol: "💻" },
  { typ: "Riggerkonsole", symbol: "🎮" },
  { typ: "Sonstiges", symbol: "◈" },
];

export const TYP_OPTIONEN = TYP_KATALOG.map((t) => t.typ);

export function symbolFuerTyp(typ: string): string {
  return TYP_KATALOG.find((t) => t.typ === typ)?.symbol ?? "◈";
}
