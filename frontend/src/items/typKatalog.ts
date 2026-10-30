/**
 * Gemeinsamer Typ-Katalog für Gegenstände — ein Symbol je Typ für die
 * Kachel-Auswahl beim Anlegen (siehe TypKachelAuswahl.tsx).
 *
 * Der Typ ist seit 22.09.2026 nach dem Anlegen fix (Marks Entscheidung:
 * "wer's falsch gewählt hat, löscht und legt neu an") — deshalb bekommt das
 * Anlegen-Popup diese große Kachel-Auswahl statt eines kleinen Dropdowns,
 * das man später sowieso nicht mehr korrigieren kann.
 */
import kiTamaBild from "../assets/ki-tama.png";

export interface TypEintrag {
  typ: string;
  symbol: string;
  /** Echtes Bild statt Emoji-Symbol (30.10.2026, Mark: eigenes Bild fürs
   *  Ki-Tama) — nur in der Kachel-Auswahl verwendet, `symbol` bleibt der
   *  Fallback für Stellen, die nur einen Text-/Emoji-String brauchen
   *  (`symbolFuerTyp`, Shop-Listen etc.). */
  symbolBild?: string;
  /** Anzeigetext, falls er vom `typ` abweichen soll — z.B. mit weichem
   *  Trennzeichen (\u00AD) an einer sinnvollen Stelle, damit lange
   *  zusammengesetzte Wörter in der Kachel zweizeilig umbrechen, ohne dass
   *  der gespeicherte `typ`-Wert selbst ein unsichtbares Zeichen bekommt. */
  label?: string;
}

export const TYP_KATALOG: TypEintrag[] = [
  { typ: "Waffe", symbol: "⚔" },
  { typ: "Rüstung", symbol: "🛡" },
  { typ: "Cyberware", symbol: "⚙" },
  { typ: "Bioware", symbol: "🧬" },
  { typ: "Hexware", symbol: "✦" },
  { typ: "Droge", symbol: "💊" },
  { typ: "Verbrauchsgegenstand", symbol: "◐", label: "Verbrauchs\u00ADgegenstand" },
  { typ: "Werkzeug", symbol: "🔧" },
  { typ: "Fahrzeug", symbol: "⛭" },
  { typ: "Drohne", symbol: "◭" },
  { typ: "Behälter", symbol: "▣" },
  { typ: "Commlink", symbol: "📱" },
  { typ: "Cyberdeck", symbol: "💻" },
  { typ: "Riggerkonsole", symbol: "🎮" },
  { typ: "Upgrade-Material", symbol: "🔩" },
  { typ: "Ki-Tama", symbol: "🔮", symbolBild: kiTamaBild },
  { typ: "Sonstiges", symbol: "◈" },
];

export const TYP_OPTIONEN = TYP_KATALOG.map((t) => t.typ);

export function symbolFuerTyp(typ: string): string {
  return TYP_KATALOG.find((t) => t.typ === typ)?.symbol ?? "◈";
}
