import type { SortimentEintrag } from "./api";

/**
 * Dynamische Sortierung fürs Shop-Sortiment (24.10.2026, Marks Wunsch: nach
 * den Steckbrief-Werten sortieren/filtern können, die in der jeweils
 * gewählten Kategorie überhaupt vorkommen). Die Rohwerte stecken schon im
 * SortimentEintrag (siehe api.ts) — hier nur die Auswahl, welche Felder pro
 * Typ sinnvoll sind. Spiegelt bewusst dieselbe Fallunterscheidung wie
 * `items/steckbrief.ts::steckbriefZeilen`, nur mit rohem Zahlenwert statt
 * fertig formatiertem Text, damit sortiert statt nur angezeigt werden kann.
 */

const CHROM_TYPEN = new Set(["Cyberware", "Bioware", "Hexware"]);
const FAHRZEUG_TYPEN = new Set(["Fahrzeug", "Drohne"]);

export interface SortierFeld {
  /** Property-Name auf SortimentEintrag (oder "name" als Sonderfall). */
  key: string;
  label: string;
}

/** Immer verfügbar, unabhängig von der gewählten Kategorie. */
export const BASIS_SORTIERFELDER: SortierFeld[] = [
  { key: "preis", label: "Preis" },
  { key: "name", label: "Name" },
  { key: "seltenheit", label: "Seltenheit" },
];

/**
 * Zusätzliche, kategorie-spezifische Felder. Bei "Alle" (typ === null) bleibt
 * das leer — ein Feld wie "Schaden" ergibt über Kategorien hinweg keinen
 * Sinn, weil nicht jeder Typ es trägt.
 */
export function dynamischeSortierfelder(typ: string | null, sortiment: SortimentEintrag[]): SortierFeld[] {
  if (typ === null) return [];
  const relevante = sortiment.filter((w) => w.typ === typ);
  const felder: SortierFeld[] = [];

  if (typ === "Waffe") {
    felder.push({ key: "kraft", label: "Schaden" });
  }
  if (relevante.some((w) => w.typ !== "Waffe" && w.istWaffe)) {
    felder.push({ key: "schaden", label: "Schaden" });
  }
  if (typ === "Rüstung") {
    felder.push({ key: "ruestungReduktionBasis", label: "Reduktion" });
    felder.push({ key: "ruestungKaestchenMax", label: "Kästchen" });
  }
  if (CHROM_TYPEN.has(typ)) {
    felder.push({ key: "kraft", label: "Stufe" });
    if (relevante.some((w) => w.wVerlust > 0)) felder.push({ key: "wVerlust", label: "Willenskraft" });
  }
  if (typ === "Cyberdeck") {
    felder.push(
      { key: "deckBruteForce", label: "Brute Force" },
      { key: "deckSchleichen", label: "Schleichen" },
      { key: "deckDaten", label: "Daten" },
      { key: "deckKompilieren", label: "Kompilieren" },
      { key: "deckElectronicWarfare", label: "Electronic Warfare" },
      { key: "deckMatrixNavigation", label: "Matrix-Navigation" },
    );
  }
  if (typ === "Riggerkonsole") {
    felder.push({ key: "riggerBonus", label: "Rigger-Bonus" });
    felder.push({ key: "maxDrohnen", label: "Max. Drohnen" });
  }
  if (FAHRZEUG_TYPEN.has(typ)) {
    felder.push({ key: "stufe", label: "Stufe" });
  }
  if (typ === "Commlink") {
    felder.push({ key: "cyberwall", label: "I.C.E." });
  }
  if (relevante.some((w) => w.istBehaelter && w.kapazitaet > 0)) {
    felder.push({ key: "kapazitaet", label: "Kapazität" });
  }
  if (relevante.some((w) => w.initiativeBonus !== 0)) {
    felder.push({ key: "initiativeBonus", label: "Initiative" });
  }
  if (relevante.some((w) => w.zusatzaktionen !== 0)) {
    felder.push({ key: "zusatzaktionen", label: "Zusatzaktion" });
  }

  // Gleicher Key kann über mehrere Zweige auftauchen (z.B. "kraft" bei
  // Waffe vs. Chrom würde nie gleichzeitig greifen, aber zur Sicherheit).
  const gesehen = new Set<string>();
  return felder.filter((f) => {
    if (gesehen.has(f.key)) return false;
    gesehen.add(f.key);
    return true;
  });
}

export type SortierRichtung = "auf" | "ab";

/** Default-Richtung beim erstmaligen Wählen eines Feldes: Preis/Name
 * aufsteigend (günstigstes/A zuerst), Werte/Seltenheit absteigend (stärkstes
 * zuerst — das sucht man beim Stöbern typischerweise zuerst). */
export function standardRichtung(feldKey: string): SortierRichtung {
  return feldKey === "preis" || feldKey === "name" ? "auf" : "ab";
}

export function sortimentSortieren(
  sortiment: SortimentEintrag[],
  feld: string,
  richtung: SortierRichtung,
): SortimentEintrag[] {
  const kopie = [...sortiment];
  kopie.sort((a, b) => {
    const diff =
      feld === "name"
        ? a.name.localeCompare(b.name, "de")
        : Number((a as unknown as Record<string, number>)[feld] ?? 0) -
          Number((b as unknown as Record<string, number>)[feld] ?? 0);
    return richtung === "auf" ? diff : -diff;
  });
  return kopie;
}

/**
 * Sortierleiste als Commlink-Pillen, analog zu ShopKategorien. Feld bleibt
 * nur gültig, solange es zur aktuellen Kategorie passt — den Reset bei
 * Kategoriewechsel übernimmt der Aufrufer (useGueltigesSortierfeld unten).
 */
export function ShopSortierleiste({
  sortiment,
  kategorie,
  feld,
  richtung,
  onAendern,
}: {
  sortiment: SortimentEintrag[];
  kategorie: string | null;
  feld: string;
  richtung: SortierRichtung;
  onAendern: (feld: string, richtung: SortierRichtung) => void;
}) {
  if (sortiment.length <= 1) return null;
  const felder = [...BASIS_SORTIERFELDER, ...dynamischeSortierfelder(kategorie, sortiment)];

  function waehlen(key: string) {
    if (feld === key) {
      onAendern(key, richtung === "auf" ? "ab" : "auf");
    } else {
      onAendern(key, standardRichtung(key));
    }
  }

  return (
    <div className="shop-sortier-leiste">
      <span className="shop-sortier-label">Sortieren</span>
      {felder.map((f) => (
        <button
          key={f.key}
          type="button"
          className="shop-sortier-pille"
          data-aktiv={feld === f.key}
          onClick={() => waehlen(f.key)}
        >
          {f.label}
          {feld === f.key && <span aria-hidden="true">{richtung === "auf" ? " ↑" : " ↓"}</span>}
        </button>
      ))}
    </div>
  );
}

/** Fällt auf "Preis aufsteigend" zurück, sobald das gewählte Feld zur neuen
 * Kategorie nicht mehr passt (z.B. Wechsel von Waffe auf Rüstung). */
export function gueltigesFeld(
  feld: string,
  kategorie: string | null,
  sortiment: SortimentEintrag[],
): string {
  const felder = [...BASIS_SORTIERFELDER, ...dynamischeSortierfelder(kategorie, sortiment)];
  return felder.some((f) => f.key === feld) ? feld : "preis";
}
