import { api, ApiError } from "../api/client";
import type { SichtbarkeitModus } from "../entities/api";

export interface Gegenstand {
  id: string;
  name: string;
  description: string;
  notes: string;
  typ: string;
  preis: number;
  kraft: number;
  eigenschaften: Record<string, string>;
  zeigeInGraph: boolean;
  einzigartig: boolean;
  hatMenge: boolean;
  menge: number;
  istVorlage: boolean;
  seltenheit: number;
  automatischImShop: boolean;
  bildUrl: string;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
  /** Wo der Gegenstand steckt. GELAGERT verweist zusätzlich auf ein Ziel. */
  /** Eigengewicht in kg; 0 = vernachlässigbar. */
  gewicht: number;
  /** Wie viel dieser Gegenstand fasst, in kg; 0 = kein Behälter. */
  kapazitaet: number;
  /** Kann etwas aufnehmen. Steht am Gegenstand, wird nicht aus dem Typ geraten. */
  istBehaelter: boolean;
  /** Blatt für Drohne/Fahrzeug/Sprite/Geist — 0 heisst "kein Blatt geführt". */
  stufe: number;
  widerstand: number;
  angriff: number;
  agilitaet: number;
  fahrzeugFertigkeiten: Record<string, number>;
  ablage: Ablage;
  ablageZielId: string | null;
  ablageZielName: string | null;
  ablageZielKind: string | null;
}

export type Ablage = "AUSGERUESTET" | "RUCKSACK" | "GELAGERT";

/** Reihenfolge und Beschriftung der Ablagen — von "am Körper" nach "weit weg". */
export const ABLAGEN: { wert: Ablage; label: string; symbol: string }[] = [
  { wert: "AUSGERUESTET", label: "Ausgerüstet", symbol: "⚔" },
  { wert: "RUCKSACK", label: "Rucksack", symbol: "🎒" },
  { wert: "GELAGERT", label: "Gelagert", symbol: "⌂" },
];

export interface TraglastZeile {
  id: string;
  name: string;
  art: "Person" | "Gegenstand";
  personType: string | null;
  last: number;
  /** 0 = keine Grenze bekannt (z.B. Attribut nicht gesetzt). */
  kapazitaet: number;
  /** Kann etwas aufnehmen. Steht am Gegenstand, wird nicht aus dem Typ geraten. */
  istBehaelter: boolean;
  /** Blatt für Drohne/Fahrzeug/Sprite/Geist — 0 heisst "kein Blatt geführt". */
  stufe: number;
  widerstand: number;
  angriff: number;
  agilitaet: number;
  fahrzeugFertigkeiten: Record<string, number>;
}

export interface AblageZiel {
  id: string;
  name: string;
  kind: string;
}

export interface GegenstandMitBesitzer extends Gegenstand {
  // Vorlagen haben keinen Besitzer (siehe VORLAGE_SENTINEL) — daher nullable.
  ownerId: string | null;
  ownerName: string | null;
  ownerPersonType: "PC" | "NPC" | null;
}

// Pseudo-Wert für Besitzer-Dropdowns: "kein Besitzer, dieser Gegenstand ist
// eine Vorlage" statt einer echten Person-ID.
export const VORLAGE_SENTINEL = "__VORLAGE__";

function base(campaignId: string, personId: string) {
  return `/api/campaigns/${campaignId}/personen/${personId}/gegenstaende`;
}

function campaignBase(campaignId: string) {
  return `/api/campaigns/${campaignId}/gegenstaende`;
}

function itemBase(campaignId: string, itemId: string) {
  return `${campaignBase(campaignId)}/${itemId}`;
}

export interface GegenstandUpdate {
  name?: string;
  description?: string;
  notes?: string;
  typ?: string;
  preis?: number;
  kraft?: number;
  eigenschaften?: Record<string, string>;
  zeigeInGraph?: boolean;
  einzigartig?: boolean;
  hatMenge?: boolean;
  menge?: number;
  // istVorlage bewusst nicht editierbar (siehe Backend-Kommentar in
  // schemas.py) — ergibt sich ausschließlich aus Besitzer wechseln/Vorlage
  // machen/Zuweisen.
  seltenheit?: number;
  automatischImShop?: boolean;
  bildUrl?: string;
  sichtbarkeit?: SichtbarkeitModus;
  sichtbarFuer?: string[];  gewicht?: number;
  kapazitaet?: number;
  istBehaelter?: boolean;
  stufe?: number;
  widerstand?: number;
  angriff?: number;
  agilitaet?: number;
  fahrzeugFertigkeiten?: Record<string, number>;
}

type NeuerGegenstand = {
  name: string;
  description?: string;
  notes?: string;
  typ?: string;
  eigenschaften?: Record<string, string>;
  zeigeInGraph?: boolean;
};

export const itemsApi = {
  // Person-gescopt: nur für Gegenstände MIT Besitzer (Anlegen/Auflisten im
  // Kontext einer Person). Alle anderen Operationen sind campaign-gescopt,
  // da Vorlagen keinen Besitzer haben.
  list: (cid: string, personId: string) => api.get<Gegenstand[]>(base(cid, personId)),
  create: (cid: string, personId: string, body: NeuerGegenstand) => api.post<Gegenstand>(base(cid, personId), body),

  listAlle: (cid: string) => api.get<GegenstandMitBesitzer[]>(campaignBase(cid)),
  setAblage: (cid: string, itemId: string, ablage: Ablage, zielId?: string | null) =>
    api.post<Gegenstand>(`${campaignBase(cid)}/${itemId}/ablage`, { ablage, zielId: zielId ?? null }),
  traglast: (cid: string) => api.get<TraglastZeile[]>(`${campaignBase(cid)}/traglast`),
  ablageziele: (cid: string, itemId: string) =>
    api.get<AblageZiel[]>(`${campaignBase(cid)}/${itemId}/ablageziele`),

  createVorlage: (cid: string, body: NeuerGegenstand) => api.post<Gegenstand>(campaignBase(cid), body),
  update: (cid: string, itemId: string, body: GegenstandUpdate) =>
    api.patch<Gegenstand>(itemBase(cid, itemId), body),
  remove: (cid: string, itemId: string) => api.delete<void>(itemBase(cid, itemId)),
  assign: (cid: string, itemId: string, zielPersonId: string) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/zuweisen`, { zielPersonId }),
  changeOwner: (cid: string, itemId: string, zielPersonId: string) =>
    api.post<Gegenstand>(`${itemBase(cid, itemId)}/besitzer`, { zielPersonId }),
  removeOwner: (cid: string, itemId: string) => api.post<Gegenstand>(`${itemBase(cid, itemId)}/vorlage`, {}),
  uploadBild: async (cid: string, itemId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${itemBase(cid, itemId)}/bild`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, body.detail ?? "Upload fehlgeschlagen");
    }
    return (await response.json()) as Gegenstand;
  },
};
