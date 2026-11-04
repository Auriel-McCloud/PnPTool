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
 *
 * @param mitMontiert Fügt einen eigenen "Montiert"-Bereich für Augments/
 *   Ki-Tamas hinzu, die an einem Trägergegenstand montiert sind, statt sie
 *   wie bisher komplett zu verschlucken (Mark-Bugreport 31.10.2026: "als SL
 *   kann ich sie nicht mehr sehen"). Bewusst standardmäßig AUS — die
 *   Spieler-Ansicht ruft diese Funktion ohne das Flag auf und soll ihr
 *   bisheriges Verhalten (montierte Stücke nur als Fähnchen am Träger,
 *   keine eigene Auswahl) unverändert behalten; nur die SL-Übersicht
 *   schaltet es gezielt ein.
 *
 * @param _einBesitzer Historisch: steuerte, ob ein getragener Behälter allein
 *   schon den "Mitgeführt"-Reiter zeigt. Seit 04.11.2026 zeigt der Reiter
 *   sich nur noch bei tatsächlichem Inhalt (wie das Depot) — der Parameter
 *   bleibt nur noch der Signatur wegen stehen, ohne Wirkung.
 */
export function ermittleBereiche(items: Gegenstand[], _einBesitzer = true, mitMontiert = false): Bereich[] {
  // Montierte Augments (Zielfernrohr & Co., 29.10.2026) sind kein eigener
  // Ablageplatz mehr — sie stecken an ihrem Trägergegenstand (MONTIERT_AN)
  // und werden dort schon als "montierte Upgrades" angezeigt. Ihr altes
  // `ablage`-Feld bleibt beim Montieren unverändert stehen, ohne diesen
  // Filter tauchten sie deshalb weiterhin einzeln im Rucksack/Ausgerüstet
  // auf, obwohl sie physisch Teil der Waffe/Rüstung sind (Mark-Bugreport).
  const alleItems = items;
  items = items.filter((g) => !g.montiertAnId);
  const bereiche: Bereich[] = [
    {
      id: "AUSGERUESTET",
      name: "Am Körper",
      symbol: "⚔",
      greifbar: true,
      passt: (g) => g.ablage === "AUSGERUESTET",
    },
  ];

  // Bleibt neutral "Mitgeführt" / ▣ — genau wie die gleichnamige Option im
  // Umlegen-Dialog der Kachel (GegenstandKachel::grundAblagen). Hieß der
  // Bereich früher nach dem getragenen Behälter, kollidierte das mit dessen
  // eigenem Fach weiter unten: zwei Reiter namens "Rucksack", einer mit dem
  // Behälter-Symbol 🎒 für lose mitgeführte Sachen, der andere mit dem
  // Mitgeführt-Symbol ▣ für das, was tatsächlich im Rucksack steckt — exakt
  // vertauscht (Mark-Bugreport 31.10.2026). Trägt jemand zudem mehr als
  // einen Behälter (seit GegenstandKachel dasselbe erlaubt), gäbe es ohnehin
  // keinen einzelnen Namen mehr, der passt.
  //
  // Nur sichtbar, wenn tatsächlich etwas lose (ohne bestimmtes Ziel) darin
  // liegt — genau dieselbe Regel wie beim Depot weiter unten (Mark,
  // 04.11.2026: "wird ja auch ausgeblendet wenn nichts daran ist"). Vorher
  // reichte schon ein getragener Behälter allein, um den Reiter zu zeigen,
  // auch wenn er leer war — das wirkte unaufgeräumt und widersprach genau
  // dem Depot-Vorbild, das Mark hier als Maßstab wollte.
  const mitgefuehrt = items.some((g) => g.ablage === "RUCKSACK");
  if (mitgefuehrt) {
    bereiche.push({
      id: "MITGEFUEHRT",
      name: "Mitgeführt",
      symbol: "▣",
      greifbar: false,
      passt: (g) => g.ablage === "RUCKSACK",
    });
  }

  // Je Lagerort ein eigenes Fach — genau das erlaubt "ich sitze im Auto"
  // gegen "ich bin im Versteck".
  // ▣ für Behälter — deckungsgleich mit dem Typ-Katalog (TYP_KATALOG, Behälter
  // = ▣) und dem "Hineinsehen"-Knopf der eigenen Kachel. Dasselbe Symbol wie
  // beim neutralen "Mitgeführt" oben ist hier bewusst in Kauf genommen: die
  // Reiter unterscheiden sich über den Namen ("Mitgeführt" vs. "Rucksack"),
  // und beide meinen ohnehin verwandte Dinge (kein bestimmter Behälter / ein
  // bestimmter Behälter) — anders als die alte Namens-Kollision war das nie
  // das eigentliche Problem (Mark-Bugreport 31.10.2026).
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

  // Ein eigener Behälter wird **immer** zum eigenen Fach — getragen oder
  // nicht, leer oder voll — genau wie ein Fahrzeug oder eine Kiste. Galt das
  // vorher nur für NICHT getragene bzw. gesperrte Behälter (Begründung: der
  // getragene wäre schon über "Mitgeführt" abgedeckt), stimmte das nur,
  // solange "Mitgeführt" nach dem getragenen Behälter benannt war und dessen
  // Inhalt zeigte. Seit das wieder neutral ist (siehe oben), fehlte dem
  // getragenen Behälter ohne dieses Fach ein eigener Platz — sein
  // "Hineinsehen"-Knopf landete über eine Sonderregel in
  // SpielerAnsicht.tsx::fachIdFuer zwangsweise bei "Mitgeführt" statt bei
  // seinem eigenen Inhalt, und das auch nur für GENAU EINEN getragenen
  // Behälter (den ersten gefundenen) — jeder weitere zeigte zufällig schon
  // richtig, weil er über `ablageZielId` ohnehin ein eigenes Fach bekam
  // (Mark-Bugreport 31.10.2026: "beim ersten Behälter falscher Inhalt, beim
  // zweiten passt's"). Mit dieser Zeile bekommt JEDER Behälter sein Fach
  // direkt hier, die Sonderregel in SpielerAnsicht.tsx ist damit überflüssig
  // und raus.
  for (const g of items) {
    if (istBehaelter(g)) {
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

  // Montierte Upgrades (Ki-Tama, Zielfernrohr & Co.) bekommen nur dann einen
  // eigenen, wählbaren Bereich, wenn der Aufrufer das ausdrücklich will
  // (siehe Doku oben) UND tatsächlich welche vorhanden sind — sonst ein
  // leerer Reiter, der nie etwas zeigt.
  if (mitMontiert && alleItems.some((g) => g.montiertAnId)) {
    bereiche.push({
      id: "MONTIERT",
      name: "Montiert",
      symbol: "🔩",
      greifbar: false,
      passt: (g) => Boolean(g.montiertAnId),
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
  // Siehe ermittleBereiche oben: montierte Augments gehören keinem normalen
  // Ablage-Bereich mehr, egal was ihr `ablage`-Feld historisch noch sagt —
  // AUSSER der Aufrufer hat per `mitMontiert` einen eigenen "Montiert"-
  // Bereich angefordert und genau den gerade angewählt.
  const ohneMontage = items.filter((g) => !g.montiertAnId);
  if (auswahl.size === 0) return ohneMontage;
  const aktive = bereiche.filter((b) => auswahl.has(b.id));
  const ergebnis = ohneMontage.filter((g) => aktive.some((b) => b.passt(g)));
  if (auswahl.has("MONTIERT")) {
    ergebnis.push(...items.filter((g) => g.montiertAnId));
  }
  return ergebnis;
}
