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
  /**
   * Am Körper und sofort greifbar. Nur der ausgerüstete Bereich ist das —
   * alles andere muss man erst aufmachen, und genau so wird es auch gezeigt
   * (Spielersicht: Ausrüstung steht offen, der Rest sind Fächer, die als
   * Fenster aufgehen).
   */
  greifbar: boolean;
  /** Trifft zu, wenn dieser Gegenstand in diesen Bereich gehört. */
  passt: (g: Gegenstand) => boolean;
}

/**
 * Ob dieser Gegenstand etwas aufnehmen kann.
 *
 * Steht am Gegenstand und wird **nicht** aus dem Typ geraten: ein Motorrad
 * ist ein Fahrzeug ohne Stauraum, eine Kiste hat Stauraum ohne Räder. Wer
 * ein Fahrzeug beladen können will, hakt das in den Optionen an.
 */
const istBehaelter = (g: Gegenstand) => g.istBehaelter;

/**
 * Leitet die Bereiche aus den vorhandenen Gegenständen ab.
 *
 * Bewusst datengetrieben statt einer festen Liste: wer keinen Rucksack
 * trägt, bekommt auch keinen Rucksack-Reiter, und ein Fahrzeug taucht erst
 * auf, wenn tatsächlich etwas darin liegt. So bildet die Auswahl ab, worauf
 * die Person gerade wirklich Zugriff hat.
 */
export function ermittleBereiche(items: Gegenstand[], einBesitzer = true): Bereich[] {
  const bereiche: Bereich[] = [
    {
      id: "AUSGERUESTET",
      name: "Am Körper",
      symbol: "⚔",
      greifbar: true,
      passt: (g) => g.ablage === "AUSGERUESTET",
    },
  ];

  // Ein getragener Behälter gibt dem "mitgeführt"-Bereich seinen Namen —
  // sonst heißt er neutral, denn ohne Rucksack trägt man Dinge trotzdem
  // am Gürtel oder in der Hand.
  //
  // Nur sinnvoll, solange die Gegenstände einer einzigen Person gehören. In
  // der kampagnenweiten Übersicht der Spielleitung liegen sie quer über alle
  // Charaktere; dort hieße der Reiter sonst nach dem Rucksack irgendeines
  // Spielers, obwohl darin die Sachen aller stecken.
  const getragenerBehaelter = einBesitzer
    ? items.find((g) => istBehaelter(g) && g.ablage === "AUSGERUESTET")
    : undefined;
  const mitgefuehrt = items.some((g) => g.ablage === "RUCKSACK");
  if (mitgefuehrt || getragenerBehaelter) {
    bereiche.push({
      id: "MITGEFUEHRT",
      name: getragenerBehaelter ? getragenerBehaelter.name : "Mitgeführt",
      symbol: "🎒",
      greifbar: false,
      passt: (g) => g.ablage === "RUCKSACK",
    });
  }

  // Je Lagerort ein eigenes Fach — genau das erlaubt "ich sitze im Auto"
  // gegen "ich bin im Versteck".
  const symbolFuer = (typ?: string) =>
    typ === "Fahrzeug" ? "⛭" : typ === "Drohne" ? "◭" : typ === "Behälter" ? "▣" : "⌂";
  const typVonZiel = new Map(items.map((g) => [g.id, g.typ]));
  const faecher = new Map<string, { name: string; symbol: string }>();

  for (const g of items) {
    if (g.ablage === "GELAGERT" && g.ablageZielId && g.ablageZielName) {
      faecher.set(g.ablageZielId, {
        name: g.ablageZielName,
        symbol: symbolFuer(typVonZiel.get(g.ablageZielId)),
      });
    }
  }

  // Ein eigenes Fahrzeug oder eine Kiste wird **auch dann** zum Fach, wenn
  // gerade nichts darin liegt: man will hineinsehen können, statt sich zu
  // fragen, ob das Auto verschwunden ist. Getragene Behälter sind schon
  // oben als "mitgeführt" abgehandelt.
  for (const g of items) {
    if (istBehaelter(g) && g.ablage !== "AUSGERUESTET") {
      faecher.set(g.id, { name: g.name, symbol: symbolFuer(g.typ) });
    }
  }

  for (const [id, fach] of faecher) {
    bereiche.push({
      id,
      name: fach.name,
      symbol: fach.symbol,
      greifbar: false,
      passt: (g) => g.ablageZielId === id,
    });
  }

  // Weggelegtes ohne festen Platz nicht verschlucken — **auch Behälter und
  // Fahrzeuge**. Sie sind zwar selbst Fächer, aber sie liegen zugleich
  // irgendwo, und nur hier kommt man an sie als Gegenstand heran: Gewicht,
  // Beschreibung, Umlegen. Das Fach zeigt bloss, was darin ist.
  if (items.some((g) => g.ablage === "GELAGERT" && !g.ablageZielId)) {
    bereiche.push({
      id: "GELAGERT_OFFEN",
      // Hiess "Sonst gelagert" — das klang nach Restposten.
      name: "Depot",
      symbol: "⌷",
      greifbar: false,
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
