/** Stufe einer vorgefertigten Vorlage. normal leuchtet nicht. */

export type VorgefertigtSignifikanz = "normal" | "hervorheben" | "wichtig";

const RANG: Record<string, number> = { wichtig: 0, hervorheben: 1, normal: 2 };

export function signifikanzWert(wert: string | null | undefined): VorgefertigtSignifikanz {
  if (wert === "wichtig" || wert === "hervorheben") return wert;
  return "normal";
}

/** Nur gesetzte Vorlagen leuchten. Gespielte PCs und „Normal“ bleiben dunkel. */
export function glanzStufe(person: {
  istVorgefertigt?: boolean;
  vorgefertigtSignifikanz?: string | null;
}): "hervorheben" | "wichtig" | null {
  if (!person.istVorgefertigt) return null;
  const stufe = signifikanzWert(person.vorgefertigtSignifikanz);
  return stufe === "normal" ? null : stufe;
}

/**
 * SL-Kacheln: wichtige Vorlagen, dann hervorgehobene, dann der Rest
 * in der bisherigen Reihenfolge (stabile Sortierung).
 */
export function pcKachelRang(person: {
  istVorgefertigt?: boolean;
  vorgefertigtSignifikanz?: string | null;
}): number {
  if (!person.istVorgefertigt) return 2;
  return RANG[signifikanzWert(person.vorgefertigtSignifikanz)] ?? 2;
}

export function rangDerSignifikanz(wert: string | null | undefined): number {
  return RANG[signifikanzWert(wert)] ?? 2;
}
