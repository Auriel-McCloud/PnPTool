import { api, ApiError } from "../api/client";
import type { SichtbarkeitModus } from "../entities/api";

export interface Gegenstand {
  id: string;
  name: string;
  description: string;
  notes: string;
  typ: string;
  eigenschaften: Record<string, string>;
  zeigeInGraph: boolean;
  bildUrl: string;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
}

function base(campaignId: string, personId: string) {
  return `/api/campaigns/${campaignId}/personen/${personId}/gegenstaende`;
}

export interface GegenstandUpdate {
  name?: string;
  description?: string;
  notes?: string;
  typ?: string;
  eigenschaften?: Record<string, string>;
  zeigeInGraph?: boolean;
  sichtbarkeit?: SichtbarkeitModus;
  sichtbarFuer?: string[];
}

export const itemsApi = {
  list: (cid: string, personId: string) => api.get<Gegenstand[]>(base(cid, personId)),
  create: (
    cid: string,
    personId: string,
    body: { name: string; description?: string; notes?: string; typ?: string; eigenschaften?: Record<string, string>; zeigeInGraph?: boolean }
  ) => api.post<Gegenstand>(base(cid, personId), body),
  update: (cid: string, personId: string, itemId: string, body: GegenstandUpdate) =>
    api.patch<Gegenstand>(`${base(cid, personId)}/${itemId}`, body),
  remove: (cid: string, personId: string, itemId: string) => api.delete<void>(`${base(cid, personId)}/${itemId}`),
  uploadBild: async (cid: string, personId: string, itemId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${base(cid, personId)}/${itemId}/bild`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, body.detail ?? "Upload fehlgeschlagen");
    }
    return (await response.json()) as Gegenstand;
  },
};
