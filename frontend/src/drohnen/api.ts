/** Drohnen & Fahrzeuge: Kachelliste, Rigger-Bindung, Aktiv-Slots, Nuyen-Kauf.
 *
 * Eigenes schlankes Modul statt Erweiterung von entities/api.ts — dieselbe
 * Begründung wie beim Whiteboard: eigener, in sich geschlossener Bereich
 * mit eigenen Routen (siehe backend/app/entities/routes.py, Abschnitt
 * "/drohnen"). Siehe docs/wiki/concepts/drohnen-fahrzeuge.md.
 */
import { api } from "../api/client";
import type { SichtbarkeitModus } from "../entities/api";
import type { Gegenstand } from "../items/api";

export interface DrohnenEintrag {
  id: string;
  name: string;
  bildUrl: string;
  istDrohne: boolean;
  istFahrzeug: boolean;
  riggerAktiv: boolean;
  riggerId: string | null;
  riggerName: string | null;
  /** Aktive Drohnen/Fahrzeuge des gebundenen Riggers gerade jetzt, bzw. die
   *  Obergrenze aus dessen ausgerüsteter Riggerkonsole — null ohne Rigger
   *  bzw. ohne Konsole (26.10.2026, Mark: "ich seh die freien Slots nirgends"). */
  riggerSlotsBelegt: number | null;
  riggerSlotsMax: number | null;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
}

export interface DrohnenPreisEintrag {
  traitDefId: string;
  name: string;
  /** "AttributDrohne" | "AttributDrohneAussenhuelle" | "Fertigkeit" |
   *  "Zusatzfertigkeit" (26.10.2026, campaign-gebundener Katalog, Id-Präfix
   *  "zf:" in traitDefId). */
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
  /** Umrechnungsfaktor XP→¥ (Kampagneneinstellung nuyenProXp) — fürs lokale
   *  Nachrechnen eines zweiten/dritten Kaufs derselben Kategorie im
   *  Warenkorb, bevor "Speichern" den Server erneut fragt. */
  nuyenProXp: number;
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

  /** `materialGegenstandId` gesetzt: bezahlt ein Maschinenteil des Riggers
   *  statt Nuyen-Abzug (26.10.2026) — siehe `maschinenteile`. */
  steigern: (campaignId: string, drohneId: string, traitDefId: string, materialGegenstandId?: string | null) =>
    api.post<{ drohne: unknown; riggerKapitalBasis: number }>(
      `${basis(campaignId)}/drohnen/${drohneId}/steigern`,
      { traitDefId, materialGegenstandId: materialGegenstandId ?? null },
    ),

  /** Maschinenteile im Besitz DES RIGGERS — für die Zahlungsauswahl beim Umbau. */
  maschinenteile: (campaignId: string, drohneId: string) =>
    api.get<Gegenstand[]>(`${basis(campaignId)}/drohnen/${drohneId}/maschinenteile`),
};
