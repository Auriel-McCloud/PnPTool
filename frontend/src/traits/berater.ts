/**
 * Charaktererstellungs-Berater — Karl-Klammer-artige Live-Warnungen.
 *
 * Spiegelt backend/app/traits/berater.py 1:1 (Python ist die getestete
 * Quelle der Wahrheit — bei einer Änderung dort auch hier nachziehen).
 * Läuft rein clientseitig statt über einen Netzwerk-Roundtrip, weil der
 * Assistent bei JEDEM Klick reagieren soll (Punkt setzen → sofort
 * Kommentar) — dieselbe Wahl wie magieBegriffe.ts für die Häretiker-Texte.
 *
 * 27.09.2026, zweite Rückmeldung: auf GENAU DREI Warnungen reduziert, in
 * fester Priorität (siehe PRIORITAET) — 1. Magie-Überladung, 2. keine
 * Wahrnehmung, 3. kein Kampfwert. Sozial/Wissen/schiefe Attribute waren zu
 * viele Popups und sind raus; die Magie-Schwelle war fälschlich 10 statt
 * der gewünschten 6, wodurch die eigentlich wichtigste Warnung nie auftauchte.
 *
 * Bewusst ohne KI: reine Reaktion auf messbare Zahlen, kein Sprachmodell,
 * keine Kosten, funktioniert auch offline/wenn die KI-Anbindung down ist.
 */

export const KAMPF_FERTIGKEITEN = new Set([
  "Handgemenge",
  "Nahkampf",
  "Schusswaffen",
  "Sportlichkeit",
  "Überleben",
  "Fahren",
  "Riggen",
]);

const SPHAEREN_NAMEN = ["Korrespondenz", "Entropie", "Kräfte", "Leben", "Materie", "Gedanken", "Ursprung", "Geister", "Zeit"];
const NEUROWEAVING_FERTIGKEITEN_NAMEN = [
  "Brute Force",
  "Schleichen",
  "Daten Verarbeiten",
  "Kompilieren",
  "Electronic Warfare",
  "Matrix-Navigation",
];

/** Deckt sich mit berater.py::MAGIE_SUMME_WARNSCHWELLE. */
export const MAGIE_SUMME_WARNSCHWELLE = 6;

/** Deckt sich mit berater.py::_PRIORITAET — niedrigste Zahl zuerst gezeigt. */
const PRIORITAET: Record<string, number> = { MAGIE_UEBERLADEN: 0, KEINE_WAHRNEHMUNG: 1, KEIN_KAMPFWERT: 2 };

export interface BeraterHinweis {
  code: string;
  text: string;
}

function summe(werte: Record<string, number>, namen: Iterable<string>): number {
  let s = 0;
  for (const n of namen) s += werte[n] || 0;
  return s;
}

/**
 * Prüft die aktuellen Werte einer LAUFENDEN Erstellung auf Lücken.
 *
 * Gibt sortiert nach Priorität zurück (Magie-Überladung zuerst). Der
 * `attributKategorien`-Parameter ist aus Kompatibilitätsgründen noch da,
 * wird aber nicht mehr ausgewertet (ATTRIBUTE_SCHIEF ist entfallen).
 */
export function berate(
  werte: Record<string, number>,
  weg: string,
  _attributKategorien?: { id: string; attribute: string[] }[],
): BeraterHinweis[] {
  const hinweise: BeraterHinweis[] = [];

  if (weg === "MAGIER" || weg === "HAERETIKER" || weg === "NEUROWEAVER") {
    const zusatzNamen = weg === "MAGIER" || weg === "HAERETIKER" ? SPHAEREN_NAMEN : NEUROWEAVING_FERTIGKEITEN_NAMEN;
    const zusatzSumme = summe(werte, zusatzNamen);
    if (zusatzSumme > MAGIE_SUMME_WARNSCHWELLE) {
      const begriff = weg === "MAGIER" || weg === "HAERETIKER" ? "Sphären" : "NeuroWeaving-Fertigkeiten";
      hinweise.push({
        code: "MAGIE_UEBERLADEN",
        text: `Du hast schon ${zusatzSumme} Punkte in ${begriff} versenkt — empfohlen sind nicht mehr als ${MAGIE_SUMME_WARNSCHWELLE}.`,
      });
    }
  }

  if ((werte["Wahrnehmung"] || 0) === 0) {
    hinweise.push({
      code: "KEINE_WAHRNEHMUNG",
      text: "0 auf Wahrnehmung? Du merkst nicht mal, wenn dir wer die Cyberware klaut.",
    });
  }

  if (summe(werte, KAMPF_FERTIGKEITEN) === 0) {
    hinweise.push({
      code: "KEIN_KAMPFWERT",
      text: "Komplett wehrlos, wenn's kracht. Mit dem Wert hast du wohl noch nicht mal einen Bud-Spencer-Film gesehen.",
    });
  }

  hinweise.sort((a, b) => (PRIORITAET[a.code] ?? 99) - (PRIORITAET[b.code] ?? 99));
  return hinweise;
}
