/**
 * Generisches Verhandlungs-Popup — SL macht einen Preisvorschlag (eine oder
 * mehrere Positionen), der Spieler nimmt an oder lehnt ab.
 *
 * Backend bewusst generisch gehalten (siehe app/verhandlung/schemas.py):
 * heute nur RUESTUNG_REPARATUR, später auch Kaufverhandlungen im Shop mit
 * mehreren Positionen (Warenkorb-Konzept, noch nicht gebaut). Deshalb hier
 * ebenfalls eine Liste von Positionen statt eines einzelnen Preisfelds.
 */
import { api } from "../api/client";

export type VerhandlungsArt = "RUESTUNG_REPARATUR" | "SHOP_KAUF";

export interface VerhandlungPosition {
  bezeichnung: string;
  betrag: number;
}

export interface Verhandlung {
  id: string;
  empfaengerPersonId: string;
  art: VerhandlungsArt;
  positionen: VerhandlungPosition[];
  gesamtbetrag: number;
  kontext: Record<string, unknown>;
  status: "OFFEN" | "ANGENOMMEN" | "ABGELEHNT";
  erstelltAm: string;
  /** Nur gesetzt, wenn Annahme etwas verändert hat — für die Erfolgsmeldung. */
  ergebnis: { kapitalNeu?: number; gegenstand?: unknown } | null;
}

const basis = (campaignId: string) => `/api/campaigns/${campaignId}/verhandlungen`;

export const verhandlungApi = {
  /** SL: schickt ein Angebot an einen Spieler. */
  anbieten: (
    campaignId: string,
    body: {
      empfaengerPersonId: string;
      art: VerhandlungsArt;
      positionen: VerhandlungPosition[];
      kontext: Record<string, unknown>;
    },
  ) => api.post<Verhandlung>(basis(campaignId), body),
  /** Offene Angebote am eigenen Charakter — Aufhol-Liste beim Laden. */
  offene: (campaignId: string) => api.get<Verhandlung[]>(basis(campaignId)),
  einzeln: (campaignId: string, verhandlungId: string) =>
    api.get<Verhandlung>(`${basis(campaignId)}/${verhandlungId}`),
  /** Spieler antwortet — nur am eigenen Charakter. */
  antworten: (campaignId: string, verhandlungId: string, angenommen: boolean) =>
    api.post<Verhandlung>(`${basis(campaignId)}/${verhandlungId}/antwort`, { angenommen }),
  /** SL zieht ein noch offenes Angebot zurück. */
  zurueckziehen: (campaignId: string, verhandlungId: string) =>
    api.delete<void>(`${basis(campaignId)}/${verhandlungId}`),
};
