import { api } from "../api/client";
import type { SichtbarkeitModus } from "../entities/api";

export interface Gegenstand {
  id: string;
  name: string;
  description: string;
  notes: string;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
}

function base(campaignId: string, personId: string) {
  return `/api/campaigns/${campaignId}/personen/${personId}/gegenstaende`;
}

export const itemsApi = {
  list: (cid: string, personId: string) => api.get<Gegenstand[]>(base(cid, personId)),
  create: (cid: string, personId: string, body: { name: string; description?: string; notes?: string }) =>
    api.post<Gegenstand>(base(cid, personId), body),
  remove: (cid: string, personId: string, itemId: string) => api.delete<void>(`${base(cid, personId)}/${itemId}`),
};
