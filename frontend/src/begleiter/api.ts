import { api } from "../api/client";

/**
 * Begleiter — Sprites, Geister und alles, was jemandem zur Seite steht.
 *
 * Teilen sich ein Blatt mit Drohnen und Fahrzeugen: das Papierblatt ist mit
 * "Drohne / Fahrzeug / Sprite / Geist" überschrieben. Trotzdem kein
 * Gegenstand — einen Geist trägt man nicht im Rucksack, er hat kein Gewicht
 * und keinen Aufbewahrungsort.
 *
 * **KI und CRITTER sind seit 20.09.2026 KEINE Begleiter-Arten mehr** — erst
 * Mark: "wir machen critter zu richtigen NPCs", dann "mach jetzt das Gleiche
 * für die KI". Beide sind echte NPCs (`Person` mit `istCritter`/`istKI`,
 * siehe `entities/api.ts`) mit dem vollen Charakterblatt statt dieses
 * Drohne/Fahrzeug-Blatts — Einfluss-Kanten, KI-Attribute (inkl.
 * Matrix-Präsenz) liegen entsprechend dort.
 */

export type BegleiterArt = "SPRITE" | "GEIST" | "BEGLEITER";

export const ART_NAMEN: Record<BegleiterArt, string> = {
  SPRITE: "Sprite",
  GEIST: "Geist",
  BEGLEITER: "Begleiter",
};

export const ART_SYMBOLE: Record<BegleiterArt, string> = {
  SPRITE: "❊",
  GEIST: "☁",
  BEGLEITER: "☗",
};

export interface Begleiter {
  id: string;
  name: string;
  art: BegleiterArt;
  /** Wie er zu seinem Menschen steht — Feld "Beziehnung" auf dem Blatt. */
  beziehung: string;
  beschreibung: string;
  notizen: string;
  /** Aussehen; per Blitz an alle Spieler zeigbar. */
  bildUrl: string;
  /** Zugleich die Gesundheit. Wird beim Erschaffen frei verteilt. */
  stufe: number;
  widerstand: number;
  angriff: number;
  agilitaet: number;
  fertigkeiten: Record<string, number>;
  waffe: string;
  waffenSchaden: number;
  schadensart: string;
  /** Reine Budget-Anzeige, keine Kostenrechnung wie bei Personen. */
  erfahrung: number;
  erfahrungAusgegeben: number;
  besitzerId: string | null;
  besitzerName: string | null;
  sichtbarkeit: string;
  sichtbarFuer: string[];
}

export type BegleiterEingabe = Partial<Omit<Begleiter, "id" | "besitzerId" | "besitzerName">>;

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
  entfernen: (cid: string, id: string) => api.delete<void>(`${basis(cid)}/${id}`),
};
