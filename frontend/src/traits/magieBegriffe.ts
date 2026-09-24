/**
 * Häretiker-Flavor (24.09.2026, Marks Konzept, siehe CLAUDE.md Punkt 14).
 *
 * "Häretiker" ist keine eigene Mechanik — nur ein zweites Vokabular für
 * exakt denselben Magier-Weg (siehe backend/app/traits/erstellung.py::
 * normalisiere_weg). Diese Datei ist die EINZIGE Frontend-Quelle für die
 * Zuordnung Magier-Begriff → Häretiker-Begriff, damit sie nicht an jeder
 * Anzeigestelle einzeln dupliziert wird. Spiegelt HAERETIKER_LABELS in
 * backend/app/traits/seed.py 1:1 — bei einer Änderung dort auch hier
 * nachziehen.
 */

/** Trait-Name (Magier-Vokabular) → Häretiker-Vokabular. */
export const HAERETIKER_LABELS: Record<string, string> = {
  Hexkraft: "Glauben",
  Korrespondenz: "Ehecatl",
  Gedanken: "Tezcatlipoca",
  Entropie: "Kali",
  Kräfte: "Donar",
  Leben: "Enki",
  Materie: "Ogun",
  Ursprung: "Atum",
  Geister: "Izanami",
  Zeit: "Chronos",
};

/** "Wilde Magie" ist kein Trait-Name, sondern ein reiner UI-Begriff
 * (Probe.tsx/magie.ts/WillenskraftFrage.tsx) — eigene Konstante. */
export const HAERETIKER_BLASPHEMIE = "Blasphemie";

export type MagieFlavor = "MAGIER" | "HAERETIKER";

/**
 * Übersetzt einen Magier-Begriff (Trait-Name oder "Wilde Magie") in den
 * passenden Häretiker-Begriff, falls `flavor === "HAERETIKER"` — sonst
 * unverändert. Zentrale Stelle für jede UI-Anzeige, die Hexkraft/Wilde
 * Magie/Sphärennamen zeigt.
 */
export function magieBegriff(flavor: MagieFlavor | undefined, magierBegriff: string): string {
  if (flavor !== "HAERETIKER") return magierBegriff;
  if (magierBegriff === "Wilde Magie") return HAERETIKER_BLASPHEMIE;
  return HAERETIKER_LABELS[magierBegriff] ?? magierBegriff;
}
