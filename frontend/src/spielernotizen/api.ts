import { api } from "../api/client";

/** Privater Schmierzettel des Spielers — kein Wiki, SL sieht nichts. */
export interface SpielerNotiz {
  id: string;
  titel: string;
  inhalt: string;
  erstelltAm: string;
  geaendertAm: string;
}

export const spielernotizenApi = {
  liste: () => api.get<SpielerNotiz[]>("/api/spieler/notizen"),
  anlegen: (titel: string, inhalt?: string) =>
    api.post<SpielerNotiz>("/api/spieler/notizen", { titel, inhalt }),
  aendern: (id: string, body: { titel?: string; inhalt?: string }) =>
    api.patch<SpielerNotiz>(`/api/spieler/notizen/${id}`, body),
  loeschen: (id: string) => api.delete(`/api/spieler/notizen/${id}`),
};
