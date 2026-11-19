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
  art: "feuer" | "eis" | "blitz" | "schleim";
  x: number;
  y: number;
  r: number;
}

const koerper = new Map<string, Nachbar>();
const makelBis = new Map<string, { art: Angriff["art"]; bis: number }>();

const DAUER: Record<Angriff["art"], number> = { feuer: 2200, eis: 3500, blitz: 4500, schleim: 5500 };

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

/** Vampir-Fledermaus (17.11.2026): Bärbel will sie unbedingt fressen. Jede
 *  Fledermaus auf diesem Bildschirm meldet sich hier an; Bärbel (flug.ts) jagt
 *  sie, verschluckt sie manchmal und spuckt sie wieder aus. */
export interface Beute {
  /** Körpermitte in Bildschirm-Pixeln. */
  mitte(): { x: number; y: number };
  /** Bärbel kommt (von x/y) — fliehen. */
  bedroht(jetzt: number, x: number, y: number): void;
  /** Erwischt! true = sie ist jetzt im Buch (unsichtbar). */
  verschlucken(jetzt: number): boolean;
  /** Wieder raus, an dieser Stelle (Bildschirm-Pixel). */
  ausspucken(jetzt: number, x: number, y: number): void;
}

export const beuteTiere = new Map<string, Beute>();

/** Bärbels Flattermäuse (Mark, 18.11.2026): die Fledermäuse, die Bärbel ausniest.
 *  Sie bleiben als Spur auf dem Tablet, flattern herum und hängen kopfüber unter
 *  Kanten; Bärbel (flug.ts) jagt sie, holt sie mit der Tentakel zurück ins Buch
 *  oder verkohlt sie mit dem Blitz. Bewusst NICHT in `koerper`: Feuer, Eis und
 *  Laser der anderen Pets treffen sie (noch) nicht. Schlüssel = Spur-id. */
export interface Flattermaus {
  /** Körpermitte in Bildschirm-Pixeln. */
  mitte(): { x: number; y: number };
  /** Hängt sie still unter einer Kante (gutes Ziel für die Tentakel)? */
  haengt(): boolean;
  /** Weder gepackt noch getroffen — noch zu haben. */
  frei(): boolean;
  /** Bärbel kommt von (x, y): schnell weg, weit weg. */
  bedroht(jetzt: number, x: number, y: number): void;
  /** Tentakel greift zu. true = erwischt (folgt ab jetzt der Spitze ins Buch). */
  packen(jetzt: number): boolean;
  /** Vom Blitz getroffen: verkohlt, trudelt, verpufft. */
  getroffen(jetzt: number): void;
}

export const flattermaeuse = new Map<string, Flattermaus>();

/** KI-Laser (Mark, 18.11.2026): Tummy-Acher auf diesem Bildschirm. Die Entität
 *  kitzelt ihn mit dem Strahl; true = er hat gerülpst (Punkte fliegen zurück). */
export const kitzelbar = new Map<string, () => boolean>();

/** Spuren, die ein Pet gerade gepackt hat (Drache schnappt eine Seite, Bärbels
 *  Tentakel holt ein Häufchen, der Traktorstrahl der KI trägt es weg) — Mitte
 *  in Bildschirm-Pixeln, `dreh` in Grad (Wurf). Die Spur folgt dann diesem
 *  Punkt statt ihrem Element. `los` = losgelassen: sie fällt von dort hinunter
 *  und bleibt liegen, wo sie landet (Traktorstrahl unterbrochen). */
export const gegriffen = new Map<string, { x: number; y: number; skala: number; dreh?: number; los?: boolean }>();

export function makel(id: string, jetzt: number): Angriff["art"] | null {
  const t = makelBis.get(id);
  if (!t || t.bis < jetzt) return null;
  return t.art;
}
