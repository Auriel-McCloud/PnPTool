import { api } from "../api/client";

export type LexikonKategorie = "welt" | "fauna" | "flora" | "objekte";

export interface LexikonEintrag {
  id: string;
  kategorie: LexikonKategorie;
  name: string;
  bildUrl: string;
  beschreibung: string;
  beschreibungSichtbar: boolean;
  favorisiert: boolean;
  entdecktSeit: string;
  naehe: number;
}

export const lexikonApi = {
  liste: () => api.get<LexikonEintrag[]>("/api/spieler/lexikon"),
  favorisieren: (zielId: string) => api.post<void>("/api/spieler/lexikon/favoriten", { zielId }),
  favorisierenEntfernen: (zielId: string) => api.delete(`/api/spieler/lexikon/favoriten/${zielId}`),
};
