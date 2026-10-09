import { api } from "../api/client";

/** Privater Schmierzettel des Spielers — kein Wiki, SL sieht nichts.
 *
 * Seit 09.10.2026: optionaler Bezug auf einen Lexikon-Eintrag — genau eine
 * laufende Notiz pro Objekt und Spieler, siehe
 * docs/wiki/entities/spieler-lexikon.md.
 */
export interface SpielerNotiz {
  id: string;
  titel: string;
  inhalt: string;
  bezugTyp: "Ort" | "Event" | "Fraktion" | "Person" | "Gewaechs" | "Gegenstand" | null;
  bezugId: string | null;
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
  fuerLexikonEintrag: (bezugTyp: string, bezugId: string, standardTitel: string) =>
    api.get<SpielerNotiz>(
      `/api/spieler/notizen/zu/${bezugTyp}/${bezugId}?standardTitel=${encodeURIComponent(standardTitel)}`,
    ),
};
