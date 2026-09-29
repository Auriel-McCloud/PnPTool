import { api } from "../api/client";

export type MenueSlot = { ordnung: string[]; ausgeblendet: string[] };
export type MenueLayouts = { pc: MenueSlot; tablet: MenueSlot };
export type Geraet = "handy" | "tablet" | "pc";

export const LEER_SLOT: MenueSlot = { ordnung: [], ausgeblendet: [] };
export const LEER_LAYOUTS: MenueLayouts = {
  pc: { ordnung: [], ausgeblendet: [] },
  tablet: { ordnung: [], ausgeblendet: [] },
};

export const menueApi = {
  laden: () => api.get<MenueLayouts>("/api/auth/gm/menue"),
  speichern: (layouts: MenueLayouts) => api.patch<MenueLayouts>("/api/auth/gm/menue", layouts),
};

export function erkenneGeraet(): Geraet {
  if (window.matchMedia("(max-width: 599px)").matches) return "handy";
  if (window.matchMedia("(pointer: coarse)").matches) return "tablet";
  return "pc";
}

/** Handy scrollt die volle Liste. PC/Tablet wenden das gespeicherte Layout an. */
export function sichtbareBereiche<T extends { id: string }>(
  alle: T[],
  layout: MenueSlot | undefined,
  geraet: Geraet,
  aktiv: string,
): T[] {
  if (geraet === "handy" || !layout) return alle;
  const hidden = new Set(layout.ausgeblendet);
  const byId = new Map(alle.map((b) => [b.id, b]));
  const ordered: T[] = [];
  for (const id of layout.ordnung) {
    const b = byId.get(id);
    if (b && !hidden.has(id)) ordered.push(b);
    byId.delete(id);
  }
  for (const b of alle) {
    if (byId.has(b.id) && !hidden.has(b.id)) ordered.push(b);
  }
  if (aktiv && !ordered.some((b) => b.id === aktiv)) {
    const b = alle.find((x) => x.id === aktiv);
    if (b) ordered.push(b);
  }
  return ordered;
}
