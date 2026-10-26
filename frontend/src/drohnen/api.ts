/** Drohnen & Fahrzeuge: Kachelliste, Rigger-Bindung, Aktiv-Slots, Nuyen-Kauf.
 *
 * Eigenes schlankes Modul statt Erweiterung von entities/api.ts — dieselbe
 * Begründung wie beim Whiteboard: eigener, in sich geschlossener Bereich
 * mit eigenen Routen (siehe backend/app/entities/routes.py, Abschnitt
 * "/drohnen"). Siehe docs/wiki/concepts/drohnen-fahrzeuge.md.
 */
import { api } from "../api/client";
import type { SichtbarkeitModus } from "../entities/api";

export interface DrohnenEintrag {
  id: string;
  name: string;
  bildUrl: string;
  istDrohne: boolean;
  istFahrzeug: boolean;
  riggerAktiv: boolean;
  riggerId: string | null;
  riggerName: string | null;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
}

export interface DrohnenPreisEintrag {
  traitDefId: string;
  name: string;
  category: string;
  aktuell: number;
  max: number;
  kosten: number;
}

export interface DrohnenSteigerungspreise {
  /** null = kein Rigger gebunden — dann ist nichts kaufbar. */
  riggerId: string | null;
  /** Kapital DES RIGGERS, nicht der Drohne — die hat keins (Mark,
   *  25.10.2026, siehe docs/wiki/concepts/drohnen-fahrzeuge.md). */
  verfuegbar: number;
  werte: DrohnenPreisEintrag[];
}

const basis = (campaignId: string) => `/api/campaigns/${campaignId}`;

export const drohnenApi = {
  liste: (campaignId: string) => api.get<DrohnenEintrag[]>(`${basis(campaignId)}/drohnen`),

  riggerSetzen: (campaignId: string, drohneId: string, personId: string | null) =>
    api.post<{ id: string; name: string; bildUrl: string; riggerId: string | null; riggerName: string | null }>(
      `${basis(campaignId)}/drohnen/${drohneId}/rigger`,
      { personId },
    ),

  aktivSetzen: (campaignId: string, drohneId: string, aktiv: boolean) =>
    api.post<unknown>(`${basis(campaignId)}/drohnen/${drohneId}/aktiv`, { aktiv }),

  steigerungspreise: (campaignId: string, drohneId: string) =>
    api.get<DrohnenSteigerungspreise>(`${basis(campaignId)}/drohnen/${drohneId}/steigern`),

  steigern: (campaignId: string, drohneId: string, traitDefId: string) =>
    api.post<{ drohne: unknown; riggerKapitalBasis: number }>(
      `${basis(campaignId)}/drohnen/${drohneId}/steigern`,
      { traitDefId },
    ),
};
