import { api } from "../api/client";

export interface Sitzung {
  id: string;
  datum: string;
  ingameDatum: string;
  titel: string;
  notiz: string;
  erstelltAm: string;
  nummer: number | null;
  /** Leer = läuft noch. */
  beendetAm: string;
  aktiv: boolean;
}

/** „Session 3“, sonst Titel oder Datum. */
export function sitzungName(s: Sitzung): string {
  if (s.nummer != null) return `Session ${s.nummer}`;
  return s.titel || s.datum;
}

export interface ZeitleisteEintrag {
  id: string;
  kategorie: string;
  zeitpunkt: string;
  ingameZeitpunkt: string;
  sitzungId: string | null;
  slNotiz: string;
  kurz: string;
  /** Nur KI-Einträge. Leer bei den anderen Kategorien. */
  anlass?: string;
  prompt?: string;
  antwort?: string;
  /** Kampf-Einträge: Events der Kampfkarte zum Zeitpunkt der Aktion. */
  eventIds?: string[];
  eventNamen?: string[];
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
  anlegen: (
    campaignId: string,
    body: { datum: string; titel?: string; ingameDatum?: string; notiz?: string; nummer?: number | null },
  ) => api.post<Sitzung>(`/api/campaigns/${campaignId}/ereignisprotokoll/sitzungen`, body),
  aktivSetzen: (campaignId: string, sitzungId: string, aktiv: boolean) =>
    api.put<Sitzung>(`/api/campaigns/${campaignId}/ereignisprotokoll/sitzungen/${sitzungId}/aktiv`, { aktiv }),
  zeitleiste: (campaignId: string, sitzungId?: string) => {
    const q = sitzungId ? `?sitzung_id=${encodeURIComponent(sitzungId)}` : "";
    return api.get<ZeitleisteEintrag[]>(`/api/campaigns/${campaignId}/ereignisprotokoll/zeitleiste${q}`);
  },
};
