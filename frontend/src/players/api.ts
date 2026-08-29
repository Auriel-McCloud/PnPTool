import { api } from "../api/client";

export interface SpielerMe {
  sessionId: string;
  name: string;
  campaignId: string;
  campaignName: string;
  personId: string | null;
  personName: string | null;
}

export interface FreierCharakter {
  id: string;
  name: string;
}

export interface Sitzung {
  id: string;
  name: string;
  createdAt: string | null;
  personId: string | null;
  personName: string | null;
}

export const playersApi = {
  beitreten: (code: string, name: string) => api.post<SpielerMe>("/api/beitritt", { code, name }),
  me: () => api.get<SpielerMe>("/api/spieler/me"),
  freieCharaktere: () => api.get<FreierCharakter[]>("/api/spieler/charaktere"),
  charakterWaehlen: (personId: string) => api.post<SpielerMe>("/api/spieler/charakter", { personId }),
  abmelden: () => api.post("/api/spieler/abmelden"),

  // Verwaltung durch den Spielleiter
  codeLesen: (cid: string) => api.get<{ code: string | null }>(`/api/campaigns/${cid}/zugang/code`),
  codeErzeugen: (cid: string) => api.post<{ code: string | null }>(`/api/campaigns/${cid}/zugang/code`),
  codeEntfernen: (cid: string) => api.delete<{ code: string | null }>(`/api/campaigns/${cid}/zugang/code`),
  sitzungen: (cid: string) => api.get<Sitzung[]>(`/api/campaigns/${cid}/zugang/sitzungen`),
  sitzungEntfernen: (cid: string, sid: string) => api.delete<void>(`/api/campaigns/${cid}/zugang/sitzungen/${sid}`),
};
