/** Pets auf demselben Bildschirm sehen einander (Mark, 11.11.2026:
 *  anniesen und verwandeln, verkohlen, vollschleimen). Reiner Speicher,
 *  kein DOM — die Komponente meldet jede Figur pro Frame. */

export interface Nachbar {
  id: string;
  art: string;
  /** Mitte in Bildschirm-Pixeln. */
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Angriff {
  art: "feuer" | "blitz" | "schleim";
  x: number;
  y: number;
  r: number;
}

const koerper = new Map<string, Nachbar>();
const makelBis = new Map<string, { art: Angriff["art"]; bis: number }>();

const DAUER: Record<Angriff["art"], number> = { feuer: 2200, blitz: 4500, schleim: 5500 };

export function melde(n: Nachbar) {
  koerper.set(n.id, n);
}

export function vergiss(id: string) {
  koerper.delete(id);
  makelBis.delete(id);
}

export function alle(): Nachbar[] {
  return [...koerper.values()];
}

/** Trifft der Angriff jemanden? Neu Getroffene kommen zurück, damit die
 *  Verwandlung nur einmal zündet und nicht in jedem Frame. */
export function treffe(angriff: Angriff, taeter: string, jetzt: number): { id: string; art: Angriff["art"] }[] {
  const neu: { id: string; art: Angriff["art"] }[] = [];
  for (const k of koerper.values()) {
    if (k.id === taeter) continue;
    const dx = k.x - angriff.x;
    const dy = k.y - angriff.y;
    const reichweite = angriff.r + Math.max(k.w, k.h) * 0.35;
    if (dx * dx + dy * dy > reichweite * reichweite) continue;
    const alt = makelBis.get(k.id);
    if (alt && alt.bis > jetzt && alt.art === angriff.art) continue;
    makelBis.set(k.id, { art: angriff.art, bis: jetzt + DAUER[angriff.art] });
    neu.push({ id: k.id, art: angriff.art });
  }
  return neu;
}

export function makel(id: string, jetzt: number): Angriff["art"] | null {
  const t = makelBis.get(id);
  if (!t || t.bis < jetzt) return null;
  return t.art;
}
