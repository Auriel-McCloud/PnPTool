import { api } from "../api/client";

/** Shop-System — siehe backend/app/haendler/ und docs/api/haendler.md. */

export interface SortimentEintrag {
  gegenstandId: string;
  name: string;
  bildUrl: string;
  typ: string;
  preis: number;
  istVorlage: boolean;
  automatisch: boolean;
  /** Sonderangebot (24.09.2026): 0 = kein Rabatt. Der tatsächliche Kaufpreis
   * kommt bereits vom Server berechnet — hier nur zur Anzeige (Grundpreis
   * durchgestrichen + Rabattzeile). */
  rabattProzent: number;
  rabattHinweis: string;
}

export interface HaendlerEintrag {
  id: string;
  name: string;
  bildUrl: string;
  beschreibung: string;
  spezialisierung: string[];
  vertriebsart: "PHYSISCH" | "DIGITAL";
  shopHintergrundUrl: string;
  ortId: string | null;
  ortName: string | null;
  sichtbarkeit: string;
  sichtbarFuer: string[];
}

export interface KaufResponse {
  gegenstand: Record<string, unknown> | null;
  kapitalNeu: number;
  bestellung: BestellungResponse | null;
}

export interface BestellungResponse {
  id: string;
  haendlerId: string;
  haendlerName: string;
  kaeuferPersonId: string;
  gegenstandId: string;
  gegenstandName: string;
  preis: number;
  status: "OFFEN" | "GELIEFERT";
  bestelltAm: string;
  geliefertAm: string;
}

function base(cid: string, haendlerId: string) {
  return `/api/campaigns/${cid}/haendler/${haendlerId}`;
}

export const haendlerApi = {
  alle: (cid: string) => api.get<HaendlerEintrag[]>(`/api/campaigns/${cid}/haendler`),
  einzeln: (cid: string, haendlerId: string) => api.get<HaendlerEintrag>(base(cid, haendlerId)),
  sortiment: (cid: string, haendlerId: string) =>
    api.get<SortimentEintrag[]>(`${base(cid, haendlerId)}/sortiment`),
  sortimentHinzufuegen: (cid: string, haendlerId: string, gegenstandId: string, preis?: number) =>
    api.post<SortimentEintrag[]>(`${base(cid, haendlerId)}/sortiment`, { gegenstandId, preis }),
  sortimentEntfernen: (cid: string, haendlerId: string, gegenstandId: string) =>
    api.delete<SortimentEintrag[]>(`${base(cid, haendlerId)}/sortiment/${gegenstandId}`),
  rabattSetzen: (cid: string, haendlerId: string, gegenstandId: string, prozent: number, hinweis: string) =>
    api.put<SortimentEintrag[]>(`${base(cid, haendlerId)}/sortiment/${gegenstandId}/rabatt`, {
      prozent,
      hinweis,
    }),
  standortSetzen: (cid: string, haendlerId: string, ortId: string | null) =>
    api.put<HaendlerEintrag>(`${base(cid, haendlerId)}/standort`, { ortId }),
  kaufen: (cid: string, haendlerId: string, gegenstandId: string, kaeuferPersonId?: string) =>
    api.post<KaufResponse>(`${base(cid, haendlerId)}/kaufen`, { gegenstandId, kaeuferPersonId }),

  /** SL-Liste: alle offenen Online-Bestellungen über alle Händler hinweg. */
  bestellungenOffen: (cid: string) =>
    api.get<BestellungResponse[]>(`/api/campaigns/${cid}/haendler/bestellungen/offen`),
  /** Eigene Bestellungen (Spieler-Sicht): was noch unterwegs ist / schon da war. */
  bestellungenEigene: (cid: string) =>
    api.get<BestellungResponse[]>(`/api/campaigns/${cid}/haendler/bestellungen/eigene`),
  bestellungLiefern: (cid: string, bestellungId: string) =>
    api.post<BestellungResponse>(`/api/campaigns/${cid}/haendler/bestellungen/${bestellungId}/liefern`),
};
