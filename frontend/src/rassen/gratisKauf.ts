/** Muss mit backend/app/rassen/gratis_kauf.py::ALLE_TYPEN übereinstimmen. */
export const GRATIS_KAUF_ALLE_TYPEN = "alle Typen";

export function gratisKaufKurz(typ: string): string {
  if (typ === GRATIS_KAUF_ALLE_TYPEN) return "1. Kauf gratis";
  return `1. ${typ} gratis`;
}

export function ersterKaufTrifft(featureTyp: string, gegenstandTyp: string): boolean {
  if (!featureTyp) return false;
  if (featureTyp === GRATIS_KAUF_ALLE_TYPEN) return true;
  return gegenstandTyp === featureTyp;
}

export function gratisKaufLang(typ: string): string {
  if (typ === GRATIS_KAUF_ALLE_TYPEN) {
    return "Der erste Kauf im Shop ist kostenlos — egal welcher Typ";
  }
  return `Der erste ${typ}-Kauf im Shop ist kostenlos`;
}
