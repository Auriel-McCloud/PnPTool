import { api } from "../api/client";

export interface TraitDef {
  id: string;
  name: string;
  category: string;
  defaultMax: number;
  sortOrder: number;
}

export interface TraitRating {
  traitDefId: string;
  name: string;
  category: string;
  rating: number;
  max: number;
}

function base(campaignId: string) {
  return `/api/campaigns/${campaignId}`;
}

export const traitsApi = {
  getKatalog: (cid: string) => api.get<TraitDef[]>(`${base(cid)}/traitkatalog`),
  getWerte: (cid: string, personId: string) => api.get<TraitRating[]>(`${base(cid)}/personen/${personId}/werte`),
  setWert: (cid: string, personId: string, traitDefId: string, rating: number, maxOverride: number | null) =>
    api.put<TraitRating>(`${base(cid)}/personen/${personId}/werte/${encodeURIComponent(traitDefId)}`, {
      rating,
      maxOverride,
    }),
};
