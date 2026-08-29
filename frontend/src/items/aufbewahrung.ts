import type { Gegenstand } from "./api";

/**
 * Ein anwählbarer Aufbewahrungsbereich.
 *
 * Nicht die drei festen Ablage-Arten, sondern was tatsächlich existiert:
 * "Ausgerüstet" gibt es immer, ein Rucksack nur wenn einer getragen wird,
 * und jeder Lagerort (Fahrzeug, Versteck) wird ein eigener Bereich.
 */
export interface Bereich {
  /** "AUSGERUESTET", "MITGEFUEHRT" oder die ID des Lagerziels. */
  id: string;
  name: string;
  symbol: string;
  /** Trifft zu, wenn dieser Gegenstand in diesen Bereich gehört. */
  passt: (g: Gegenstand) => boolean;
}

/** Gegenstände, die selbst etwas aufnehmen können. */
const BEHAELTER_TYPEN = new Set(["Behälter", "Fahrzeug"]);

/**
 * Leitet die Bereiche aus den vorhandenen Gegenständen ab.
 *
 * Bewusst datengetrieben statt einer festen Liste: wer keinen Rucksack
 * trägt, bekommt auch keinen Rucksack-Reiter, und ein Fahrzeug taucht erst
 * auf, wenn tatsächlich etwas darin liegt. So bildet die Auswahl ab, worauf
 * die Person gerade wirklich Zugriff hat.
 */
export function ermittleBereiche(items: Gegenstand[]): Bereich[] {
  const bereiche: Bereich[] = [
    {
      id: "AUSGERUESTET",
      name: "Ausgerüstet",
      symbol: "⚔",
      passt: (g) => g.ablage === "AUSGERUESTET",
    },
  ];

  // Ein getragener Behälter gibt dem "mitgeführt"-Bereich seinen Namen —
  // sonst heißt er neutral, denn ohne Rucksack trägt man Dinge trotzdem
  // am Gürtel oder in der Hand.
  const getragenerBehaelter = items.find(
    (g) => BEHAELTER_TYPEN.has(g.typ) && g.ablage === "AUSGERUESTET",
  );
  const mitgefuehrt = items.some((g) => g.ablage === "RUCKSACK");
  if (mitgefuehrt || getragenerBehaelter) {
    bereiche.push({
      id: "MITGEFUEHRT",
      name: getragenerBehaelter ? getragenerBehaelter.name : "Mitgeführt",
      symbol: "🎒",
      passt: (g) => g.ablage === "RUCKSACK",
    });
  }

  // Je Lagerort ein eigener Bereich — genau das erlaubt "ich sitze im Auto"
  // gegen "ich bin im Versteck".
  const ziele = new Map<string, string>();
  for (const g of items) {
    if (g.ablage === "GELAGERT" && g.ablageZielId && g.ablageZielName) {
      ziele.set(g.ablageZielId, g.ablageZielName);
    }
  }
  for (const [id, name] of ziele) {
    bereiche.push({ id, name, symbol: "⌂", passt: (g) => g.ablageZielId === id });
  }

  // Gelagertes ohne festen Platz nicht verschlucken
  if (items.some((g) => g.ablage === "GELAGERT" && !g.ablageZielId)) {
    bereiche.push({
      id: "GELAGERT_OFFEN",
      name: "Sonst gelagert",
      symbol: "⌂",
      passt: (g) => g.ablage === "GELAGERT" && !g.ablageZielId,
    });
  }

  return bereiche;
}

/** Standardauswahl: was man am Körper hat — der übliche Blick aufs Inventar. */
export function standardAuswahl(bereiche: Bereich[]): Set<string> {
  return new Set(bereiche.filter((b) => b.id === "AUSGERUESTET" || b.id === "MITGEFUEHRT").map((b) => b.id));
}

/** Filtert nach mehreren gleichzeitig angewählten Bereichen. */
export function filtereNachBereichen<T extends Gegenstand>(
  items: T[],
  bereiche: Bereich[],
  auswahl: Set<string>,
): T[] {
  if (auswahl.size === 0) return items;
  const aktive = bereiche.filter((b) => auswahl.has(b.id));
  return items.filter((g) => aktive.some((b) => b.passt(g)));
}
