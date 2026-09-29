import { api } from "../api/client";

export interface Sitzung {
  id: string;
  datum: string;
  ingameDatum: string;
  titel: string;
  notiz: string;
  erstelltAm: string;
}

export interface ZeitleisteEintrag {
  id: string;
  kategorie: string;
  zeitpunkt: string;
  ingameZeitpunkt: string;
  sitzungId: string | null;
  slNotiz: string;
  kurz: string;
}

export const KATEGORIE_TITEL: Record<string, string> = {
  ki: "KI",
  gegenstand: "Gegenstand",
  geld: "Geld",
  aufenthalt: "Aufenthalt",
  npcwissen: "NPC-Wissen",
  kampf: "Kampf",
  verhandlung: "Verhandlung",
  charakterentwicklung: "Entwicklung",
};

export const protokollApi = {
  sitzungen: (campaignId: string) =>
    api.get<Sitzung[]>(`/api/campaigns/${campaignId}/ereignisprotokoll/sitzungen`),
  anlegen: (campaignId: string, body: { datum: string; titel?: string; ingameDatum?: string; notiz?: string }) =>
    api.post<Sitzung>(`/api/campaigns/${campaignId}/ereignisprotokoll/sitzungen`, body),
  zeitleiste: (campaignId: string, sitzungId?: string) => {
    const q = sitzungId ? `?sitzung_id=${encodeURIComponent(sitzungId)}` : "";
    return api.get<ZeitleisteEintrag[]>(`/api/campaigns/${campaignId}/ereignisprotokoll/zeitleiste${q}`);
  },
};
