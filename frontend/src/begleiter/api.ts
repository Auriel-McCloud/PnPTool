import { api } from "../api/client";
import type { EntityKind } from "../entities/api";

/**
 * Begleiter — Sprites, Geister und alles, was jemandem zur Seite steht.
 *
 * Teilen sich ein Blatt mit Drohnen und Fahrzeugen: das Papierblatt ist mit
 * "Drohne / Fahrzeug / Sprite / Geist" überschrieben. Trotzdem kein
 * Gegenstand — einen Geist trägt man nicht im Rucksack, er hat kein Gewicht
 * und keinen Aufbewahrungsort.
 *
 * **KI und CRITTER (19.09.2026):** zwei weitere Arten auf demselben Blatt.
 * KI (z.B. eine Stadt-KI wie Babel) trägt zusätzlich die sechs
 * nicht-körperlichen Person-Attribute plus Matrix-Präsenz und kann echten
 * Entitäten (Ort/Fraktion/Event/Gegenstand) Einfluss-Stufen zuweisen —
 * siehe `einfluss`. CRITTER (Tiere/Haustiere, Shadowrun-Anlehnung) trägt
 * zusätzlich Loyalität und Ausbildung/Tricks.
 */

export type BegleiterArt = "SPRITE" | "GEIST" | "BEGLEITER" | "KI" | "CRITTER";

export const ART_NAMEN: Record<BegleiterArt, string> = {
  SPRITE: "Sprite",
  GEIST: "Geist",
  BEGLEITER: "Begleiter",
  KI: "KI",
  CRITTER: "Critter",
};

export const ART_SYMBOLE: Record<BegleiterArt, string> = {
  SPRITE: "❊",
  GEIST: "☁",
  BEGLEITER: "☗",
  KI: "⌬",
  CRITTER: "❖",
};

/** Ziele, denen ein Begleiter (typischerweise eine KI) Einfluss zuweisen
 * kann — echte Graphkante statt Freitext, siehe `EinflussZielKind` im
 * Backend. Keine Personen: Einfluss auf einen Menschen ist im Tool bereits
 * Beziehung/Handlung, kein Ressourcenwert. */
export type EinflussZielKind = Exclude<EntityKind, "Person">;

export interface EinflussEintrag {
  zielKind: EinflussZielKind;
  zielId: string;
  zielName: string;
  stufe: number;
}

export interface Begleiter {
  id: string;
  name: string;
  art: BegleiterArt;
  /** Wie er zu seinem Menschen steht — Feld "Beziehnung" auf dem Blatt. */
  beziehung: string;
  beschreibung: string;
  notizen: string;
  /** Zugleich die Gesundheit. Wird beim Erschaffen frei verteilt. */
  stufe: number;
  widerstand: number;
  angriff: number;
  agilitaet: number;
  fertigkeiten: Record<string, number>;
  waffe: string;
  waffenSchaden: number;
  schadensart: string;
  /** Zusatzblatt KI: dieselbe Skala 1-6 wie bei Person, nur nicht-körperlich. */
  charisma: number;
  manipulation: number;
  fassung: number;
  intelligenz: number;
  geistesschaerfe: number;
  entschlossenheit: number;
  matrixPraesenz: number;
  /** Zusatzblatt CRITTER: Bindung zum Besitzer und antrainierte Kunststücke. */
  loyalitaet: number;
  ausbildung: number;
  /** Reine Budget-Anzeige, keine Kostenrechnung wie bei Personen. */
  erfahrung: number;
  erfahrungAusgegeben: number;
  /** Nur bei KI sinnvoll befüllt, technisch bei jedem Begleiter möglich. */
  einfluss: EinflussEintrag[];
  besitzerId: string | null;
  besitzerName: string | null;
  sichtbarkeit: string;
  sichtbarFuer: string[];
}

export type BegleiterEingabe = Partial<
  Omit<Begleiter, "id" | "besitzerId" | "besitzerName" | "einfluss">
>;

function basis(campaignId: string) {
  return `/api/campaigns/${campaignId}/begleiter`;
}

export const begleiterApi = {
  liste: (cid: string) => api.get<Begleiter[]>(basis(cid)),
  anlegen: (cid: string, daten: BegleiterEingabe & { besitzerId?: string | null }) =>
    api.post<Begleiter>(basis(cid), daten),
  aendern: (cid: string, id: string, daten: BegleiterEingabe) =>
    api.patch<Begleiter>(`${basis(cid)}/${id}`, daten),
  besitzer: (cid: string, id: string, personId: string | null) =>
    api.post<Begleiter>(`${basis(cid)}/${id}/besitzer`, { personId }),
  /** Setzt (oder aktualisiert) die Einfluss-Stufe auf ein Ziel — GM-only. */
  einflussSetzen: (cid: string, id: string, zielKind: EinflussZielKind, zielId: string, stufe: number) =>
    api.post<Begleiter>(`${basis(cid)}/${id}/einfluss`, { zielKind, zielId, stufe }),
  /** Kappt den Einfluss ganz — z.B. wenn die SL ihr im Kampf den Ort wegnimmt. */
  einflussEntfernen: (cid: string, id: string, zielKind: EinflussZielKind, zielId: string) =>
    api.delete<Begleiter>(`${basis(cid)}/${id}/einfluss/${zielKind}/${zielId}`),
  entfernen: (cid: string, id: string) => api.delete<void>(`${basis(cid)}/${id}`),
};
