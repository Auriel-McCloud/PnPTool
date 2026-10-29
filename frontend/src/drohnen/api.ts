/** Drohnen & Fahrzeuge: Kachelliste, Rigger-Bindung, Aktiv-Slots, Nuyen-Kauf.
 *
 * Eigenes schlankes Modul statt Erweiterung von entities/api.ts — dieselbe
 * Begründung wie beim Whiteboard: eigener, in sich geschlossener Bereich
 * mit eigenen Routen (siehe backend/app/entities/routes.py, Abschnitt
 * "/drohnen"). Siehe docs/wiki/concepts/drohnen-fahrzeuge.md.
 */
import { api } from "../api/client";
import type { Person, SichtbarkeitModus } from "../entities/api";
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
  /** Diese Drohne ist die eine Hot-Verbindung des Riggers. */
  istHot: boolean;
  /** Waffen-/Rüstungs-/Drohnen-Augments (29.10.2026): wie viele Augments
   * montierbar sind, siehe docs/wiki/concepts/augments-ausruestung.md. */
  upgradeSlots: number;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
  /** Gesundheit (29.10.2026, Mark: "ich sehe bei der Reparatur nicht den
   *  Gesundheitszustand der Drohnen"): live berechnet wie am Charakterblatt,
   *  Drohnen/Fahrzeuge heilen nur über die Werkbank-Material-Reparatur. */
  gesundheitAktuell: number;
  gesundheitMax: number;
  /** Außenhülle = das `istNatuerlich`-Rüstungsteil der Drohne selbst (wie
   *  natürliche Rassen-Rüstung, siehe kampf/ruestung.py::
   *  anwende_natuerliche_ruestung) — null, falls (noch) keins existiert. */
  aussenhuelleAktuell: number | null;
  aussenhuelleMax: number | null;
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

/** "ja"/"nein"/"patzer" — Ergebnis der am Tisch gewürfelten Maker-Probe
 *  (26.10.2026, siehe MakerProbePopup.tsx). */
export type MakerProbenErgebnis = "ja" | "nein" | "patzer";

export interface MakerProbePool {
  name: string;
  /** = aktueller Wert des Ziels + 1 (traits/drohnen.py::benoetigte_erfolge_maker_probe). */
  benoetigteErfolge: number;
  /** Maker (Hardware)-Wert DES RIGGERS. */
  maker: number;
  /** Alle Attribute des Riggers zur freien Partnerwahl. */
  attribute: { name: string; wert: number }[];
}

/** Pool-Infos fürs Reparatur-Popup — Pendant zu `items/api.ts::ReparaturProbePool`
 * für Rüstung, siehe docs/wiki/concepts/drohnen-fahrzeuge.md "Reparatur". */
export interface ReparaturProbePool {
  skill: string;
  skillWert: number;
  attribute: { name: string; wert: number }[];
  benoetigteErfolge: number;
  heilungBeiErfolg: number;
  fehlendeKaestchen: number;
}

/** Auswertung der Selbst-Reparatur einer Drohne/eines Fahrzeugs. */
export interface ReparaturMaterialErgebnisDrohne {
  qualitaet: string;
  menge: number;
  repariert: number;
  materialName: string;
  materialVerbraucht: number;
  materialRestmenge: number;
  drohne: DrohnenEintrag;
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

  /** Umbenennen — darf der gebundene Rigger selbst, nicht nur die SL
   *  (29.10.2026, Mark: "es ist ja auch seine Drohne"). */
  nameSetzen: (campaignId: string, drohneId: string, name: string) =>
    api.post<Person>(`${basis(campaignId)}/drohnen/${drohneId}/name`, { name }),

  steigerungspreise: (campaignId: string, drohneId: string) =>
    api.get<DrohnenSteigerungspreise>(`${basis(campaignId)}/drohnen/${drohneId}/steigern`),

  /** `materialGegenstandId` gesetzt: bezahlt ein Maschinenteil des Riggers
   *  statt Nuyen-Abzug (26.10.2026) — siehe `maschinenteile`. Dann ist
   *  `probenErgebnis` Pflicht (Maker-Probe am Tisch, siehe `makerProbePool`). */
  steigern: (
    campaignId: string,
    drohneId: string,
    traitDefId: string,
    materialGegenstandId?: string | null,
    probenErgebnis?: MakerProbenErgebnis | null,
  ) =>
    api.post<{ drohne: unknown; riggerKapitalBasis: number; erfolgreich: boolean; materialVerbraucht: boolean }>(
      `${basis(campaignId)}/drohnen/${drohneId}/steigern`,
      { traitDefId, materialGegenstandId: materialGegenstandId ?? null, probenErgebnis: probenErgebnis ?? null },
    ),

  /** Maschinenteile im Besitz DES RIGGERS — für die Zahlungsauswahl beim Umbau. */
  maschinenteile: (campaignId: string, drohneId: string) =>
    api.get<Gegenstand[]>(`${basis(campaignId)}/drohnen/${drohneId}/maschinenteile`),

  /** Maker-Probe-Pool vorm Material-Umbau. */
  makerProbePool: (campaignId: string, drohneId: string, traitDefId: string) =>
    api.get<MakerProbePool>(
      `${basis(campaignId)}/drohnen/${drohneId}/maker-probe-pool?traitDefId=${encodeURIComponent(traitDefId)}`,
    ),

  /**
   * Pool-Infos fürs Reparatur-Popup: Skill-Wert DES RIGGERS (Handwerk ODER
   * Maker (Hardware), je nach Zieltyp — siehe kampf/ruestung.py::
   * REPARATUR_SKILLS) + alle Attribute zur freien Partnerwahl, benötigte
   * Erfolge für `menge` Stück und voraussichtliche Heilung.
   */
  reparaturPool: (campaignId: string, drohneId: string, skill: string, materialGegenstandId: string, menge: number) =>
    api.get<ReparaturProbePool>(
      `${basis(campaignId)}/drohnen/${drohneId}/reparatur-pool?skill=${encodeURIComponent(
        skill,
      )}&materialGegenstandId=${encodeURIComponent(materialGegenstandId)}&menge=${menge}`,
    ),

  /**
   * Selbst-Reparieren: Maschinenteil + selbstberichtete Probe, heilt
   * Gesundheitsschaden der Drohne/des Fahrzeugs (ihr einziger Heilweg, sie
   * können bisher nicht rasten). "ja" heilt + verbraucht `menge` Material,
   * "patzer" verbraucht nur das Material, "nein" lässt beides unangetastet.
   */
  reparierenMaterial: (
    campaignId: string,
    drohneId: string,
    materialGegenstandId: string,
    menge: number,
    probenErgebnis: MakerProbenErgebnis,
  ) =>
    api.post<ReparaturMaterialErgebnisDrohne>(`${basis(campaignId)}/drohnen/${drohneId}/reparieren-material`, {
      materialGegenstandId,
      menge,
      probenErgebnis,
    }),
};
