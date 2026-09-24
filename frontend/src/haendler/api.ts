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

/** KI-Alltagsgegenstand-Wunsch (24.09.2026) — Spieler fragt einen Verkäufer
 * nach etwas, das nicht im Sortiment steht (Marks Beispiel: Panzerklebeband).
 * Die KI schätzt Preis + Typ, geht sofort als Popup an die SL. NIE für
 * Waffen/Rüstung — technisch erzwungen, siehe app/haendler/alltagswunsch.py. */
export interface AlltagswunschResponse {
  id: string;
  haendlerId: string;
  haendlerName: string;
  spielerPersonId: string;
  spielerName: string;
  wunschText: string;
  vorschlagName: string;
  vorschlagBeschreibung: string;
  vorschlagPreis: number;
  vorschlagTyp: string;
  status: "OFFEN" | "ANGENOMMEN" | "ABGELEHNT" | "AUTO_ABGELEHNT";
  ablehnungsGrund: string | null;
  gegenstandId: string | null;
  erstelltAm: string;
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

  /** Spieler fragt nach einem Alltagsgegenstand, der nicht im Sortiment
   * steht — KI erzeugt sofort einen Vorschlag inkl. Preis, geht als Popup
   * an die SL. Eine erkannte Waffen-/Rüstungsanfrage kommt automatisch mit
   * status "AUTO_ABGELEHNT" zurück, ohne die SL zu behelligen. */
  alltagswunschStellen: (cid: string, haendlerId: string, text: string) =>
    api.post<AlltagswunschResponse>(`${base(cid, haendlerId)}/alltagswunsch`, { text }),
  /** SL-Liste: alle offenen KI-Wünsche über alle Händler hinweg (Popup-
   * Aufholliste beim Laden, analog zu Verhandlungen). */
  alltagswuenscheOffen: (cid: string) =>
    api.get<AlltagswunschResponse[]>(`/api/campaigns/${cid}/haendler/alltagswuensche/offen`),
  /** Eigene Wünsche (alle Status) — Spieler sieht, was gerade geprüft wird. */
  alltagswuenscheEigene: (cid: string) =>
    api.get<AlltagswunschResponse[]>(`/api/campaigns/${cid}/haendler/alltagswuensche/eigene`),
  /** SL entscheidet: annehmen (Gegenstand entsteht sofort im Sortiment)
   * oder ablehnen (mit optionalem Grund für den Spieler). */
  alltagswunschBeantworten: (
    cid: string,
    wunschId: string,
    angenommen: boolean,
    ueberschreibung?: { name?: string; beschreibung?: string; preis?: number },
    ablehnungsGrund?: string,
  ) =>
    api.post<AlltagswunschResponse>(`/api/campaigns/${cid}/haendler/alltagswuensche/${wunschId}/antwort`, {
      angenommen,
      name: ueberschreibung?.name,
      beschreibung: ueberschreibung?.beschreibung,
      preis: ueberschreibung?.preis,
      ablehnungsGrund,
    }),
};
