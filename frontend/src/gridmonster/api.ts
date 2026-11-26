import { api } from "../api/client";

/** GridMonster-Grundgerüst (26.11.2026): Figuren = Menschen und Monster. */

export interface GmFertigkeit {
  id: string;
  name: string;
  nurFuer: "monster" | "mensch" | null;
}

export interface GmAttribut {
  id: string;
  name: string;
  fertigkeiten: GmFertigkeit[];
}

export interface GmWertDef {
  id: string;
  name: string;
  nurFuer: "monster" | "mensch" | null;
  min: number;
  max: number | null;
}

export interface GmStufe {
  stufe: number;
  angriff: number;
  verteidigung: number;
}

export interface GmKatalog {
  wuerfel: number[];
  stufen: GmStufe[];
  attribute: GmAttribut[];
  werte: GmWertDef[];
}

export interface GmFigur {
  id: string;
  name: string;
  personType: "PC" | "NPC";
  istMonster: boolean;
  description: string;
  /** TraitDef-ID → Würfelgröße (0 = nicht gelernt) bzw. Zahl. */
  werte: Record<string, number>;
}

const basis = (cid: string) => `/api/campaigns/${cid}/gridmonster`;

export const gridApi = {
  katalog: (cid: string) => api.get<GmKatalog>(`${basis(cid)}/katalog`),
  figuren: (cid: string) => api.get<GmFigur[]>(`${basis(cid)}/figuren`),
  anlegen: (cid: string, daten: { name: string; istMonster: boolean; personType: "PC" | "NPC" }) =>
    api.post<GmFigur>(`${basis(cid)}/figuren`, daten),
  aendern: (cid: string, id: string, daten: Partial<Pick<GmFigur, "name" | "personType" | "description">>) =>
    api.patch<GmFigur>(`${basis(cid)}/figuren/${id}`, daten),
  wertSetzen: (cid: string, id: string, traitId: string, wert: number) =>
    api.put<GmFigur>(`${basis(cid)}/figuren/${id}/werte/${encodeURIComponent(traitId)}`, { wert }),
  wegwerfen: (cid: string, id: string) => api.delete<void>(`${basis(cid)}/figuren/${id}`),
};

/** Gilt ein Katalogeintrag für diese Figurenart? */
export function giltFuer(nurFuer: GmWertDef["nurFuer"], istMonster: boolean): boolean {
  return nurFuer === null || nurFuer === (istMonster ? "monster" : "mensch");
}

export function wertVon(figur: GmFigur, katalog: GmKatalog, name: string): number | undefined {
  const def = katalog.werte.find((w) => w.name === name);
  return def ? figur.werte[def.id] : undefined;
}
