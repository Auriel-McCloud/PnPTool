/**
 * Maschinen-Rassen (Mark, 16.11.2026: „bei Æ und Automata soll es nur
 * anders heißen, das reicht, das ist nur optisch“). Geistesschärfe heißt
 * dort CPU, Fassung heißt Arbeitsspeicher — Werte, Regeln und Erklärungen
 * bleiben die der eigentlichen Attribute. Erkannt am Rassennamen; wird eine
 * dieser Rassen im Baukasten umbenannt, hier mitziehen.
 */
const MASCHINEN_RASSEN = new Set(["æ", "automata"]);

const MASCHINEN_NAMEN: Record<string, string> = {
  Geistesschärfe: "CPU",
  Fassung: "Arbeitsspeicher",
};

export function istMaschinenRasse(rasse: string | null | undefined): boolean {
  return MASCHINEN_RASSEN.has((rasse ?? "").trim().toLowerCase());
}

/** Anzeigename eines Attributs für diese Rasse; sonst unverändert. */
export function rassenBegriff(rasse: string | null | undefined, name: string): string {
  return istMaschinenRasse(rasse) ? (MASCHINEN_NAMEN[name] ?? name) : name;
}
