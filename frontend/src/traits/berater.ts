/**
 * Charaktererstellungs-Berater — Karl-Klammer-artige Live-Warnungen.
 *
 * Spiegelt backend/app/traits/berater.py 1:1 (Python ist die getestete
 * Quelle der Wahrheit — bei einer Änderung dort auch hier nachziehen).
 * Läuft rein clientseitig statt über einen Netzwerk-Roundtrip, weil der
 * Assistent bei JEDEM Klick reagieren soll (Punkt setzen → sofort
 * Kommentar) — dieselbe Wahl wie magieBegriffe.ts für die Häretiker-Texte.
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

export const SOZIALE_FERTIGKEITEN = new Set([
  "Anführen",
  "Ausflüchte",
  "Darbietung",
  "Einschüchtern",
  "Etiketten",
  "Menschenkenntnis",
  "Überzeugen",
  "Szenenkenntnis",
]);

export const WISSENS_FERTIGKEITEN = new Set([
  "Diebeshandwerk",
  "Handwerk",
  "Heimlichkeit",
  "Maker (Hardware)",
  "Ermitteln",
  "Finanzen",
  "Geisteswissenschaften",
  "Medizin",
  "Naturwissenschaften",
  "Okkultismus",
  "Politik",
  "Technologie",
  "Matrix",
  "Tierkunde",
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
export const MAGIE_SUMME_WARNSCHWELLE = 10;

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
 * `attributKategorien` bildet Kategorie-Id → Attributnamen ab (aus
 * `Erstellungsregeln.attributKategorien`) — ohne sie entfällt nur die
 * ATTRIBUTE_SCHIEF-Prüfung, der Rest funktioniert trotzdem.
 */
export function berate(
  werte: Record<string, number>,
  weg: string,
  attributKategorien?: { id: string; attribute: string[] }[],
): BeraterHinweis[] {
  const hinweise: BeraterHinweis[] = [];

  if (summe(werte, KAMPF_FERTIGKEITEN) === 0) {
    hinweise.push({
      code: "KEIN_KAMPFWERT",
      text: "Komplett wehrlos, wenn's kracht. Mit dem Wert hast du wohl noch nicht mal einen Bud-Spencer-Film gesehen.",
    });
  }

  if ((werte["Wahrnehmung"] || 0) === 0) {
    hinweise.push({
      code: "KEINE_WAHRNEHMUNG",
      text: "0 auf Wahrnehmung? Du merkst nicht mal, wenn dir wer die Cyberware klaut.",
    });
  }

  if (summe(werte, SOZIALE_FERTIGKEITEN) === 0) {
    hinweise.push({
      code: "KEIN_SOZIALWERT",
      text: "Kein einziger sozialer Wert. Viel Spaß, das mit Fäusten zu verhandeln.",
    });
  }

  if (summe(werte, WISSENS_FERTIGKEITEN) === 0) {
    hinweise.push({
      code: "KEIN_WISSENSWERT",
      text: "Nichts an Wissen oder Technik. Frag lieber nicht, wie ein Kühlschrank von innen aussieht.",
    });
  }

  if (attributKategorien) {
    const summen = attributKategorien.map((k) => summe(werte, k.attribute)).filter((s) => s > 0);
    if (summen.length >= 2) {
      const hoch = Math.max(...summen);
      const niedrig = Math.min(...summen);
      if (hoch >= niedrig + 5) {
        hinweise.push({
          code: "ATTRIBUTE_SCHIEF",
          text: "Sehr einseitig unterwegs — auf der einen Seite stark, auf der anderen kaum vorhanden. Sehr schwach, aber schlau, was?",
        });
      }
    }
  }

  if (weg === "MAGIER" || weg === "NEUROWEAVER") {
    const zusatzNamen = weg === "MAGIER" ? SPHAEREN_NAMEN : NEUROWEAVING_FERTIGKEITEN_NAMEN;
    const zusatzSumme = summe(werte, zusatzNamen);
    if (zusatzSumme > MAGIE_SUMME_WARNSCHWELLE) {
      const begriff = weg === "MAGIER" ? "Sphären" : "NeuroWeaving-Fertigkeiten";
      hinweise.push({
        code: "MAGIE_UEBERLADEN",
        text: `Du hast schon ${zusatzSumme} Punkte in ${begriff} versenkt — empfohlen sind nicht mehr als ${MAGIE_SUMME_WARNSCHWELLE}.`,
      });
    }
  }

  return hinweise;
}
