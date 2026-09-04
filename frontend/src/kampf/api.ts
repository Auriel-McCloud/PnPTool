import { api } from "../api/client";

/**
 * Kampfmodus — die Initiativliste, die alle am Tisch sehen.
 *
 * Reihenfolge nach Regelblatt (Zeilen 57-59): Initiative absteigend, bei
 * Gleichstand Matrixnutzer vor Nahkämpfern vor Fernkämpfern. Sortiert wird
 * **serverseitig**, damit alle dieselbe Reihenfolge sehen.
 */

export type Kampfart = "MATRIX" | "NAHKAMPF" | "FERNKAMPF";

export const KAMPFARTEN: { wert: Kampfart; name: string; symbol: string; erklaerung: string }[] = [
  { wert: "MATRIX", name: "Matrix", symbol: "⌬", erklaerung: "Handelt bei Gleichstand zuerst." },
  { wert: "NAHKAMPF", name: "Nahkampf", symbol: "⚔", erklaerung: "Nach den Matrixnutzern." },
  { wert: "FERNKAMPF", name: "Fernkampf", symbol: "➶", erklaerung: "Zuletzt bei Gleichstand." },
];

export interface Teilnehmer {
  id: string;
  name: string;
  initiative: number;
  kampfart: Kampfart;
  /** Zusatzzug aus dem Reflex-Booster; verschwindet nach seinem Zug. */
  zusatzzug?: boolean;
  stammtId?: string | null;
  /** Überhitzung Stufe 3: 0-3 wie eine Ampel. */
  ampel?: number;
  zusatzGenutzt?: number;
  /** Nach misslungenem Paralysewurf: setzt die nächste Runde aus. */
  setztAus?: boolean;
  notiz: string;
  erledigt: boolean;
  personId: string | null;
  personType: string | null;
  begleiterId: string | null;
}

/** Was der Spieler vor dem Initiativwurf wissen muss. */
export interface InitiativePool {
  pool: number;
  geistesschaerfe: number;
  geschicklichkeit: number;
  cyberwareMod: number;
  /** Darf im Tool gewürfelt werden, oder liegen echte Würfel auf dem Tisch? */
  digitalErlaubt: boolean;
  teilnehmerId: string | null;
  gemeldet: number | null;
}

/** Boosterzustand des eigenen Charakters. */
export interface BoosterStatus {
  hatBooster: boolean;
  boosterName: string;
  zusatzaktionenMax: number;
  bereitsGenutzt: number;
  darfAktivieren: boolean;
  /** Womit der Zweitwurf gewürfelt wird — OHNE Boosterbonus. */
  zweitwurfPool: number;
  ampel: number;
  ampelMax: number;
  paralyseFaellig: boolean;
  paralysePool: number;
  paralyseSchwelle: number;
  teilnehmerId: string | null;
  setztAus: boolean;
}

export interface Kampf {
  id: string;
  runde: number;
  /** Kennung des Teilnehmers, der gerade handelt. */
  amZug: string | null;
  teilnehmer: Teilnehmer[];
}

function basis(cid: string) {
  return `/api/campaigns/${cid}/kampf`;
}

export const kampfApi = {
  laden: (cid: string) => api.get<Kampf | null>(basis(cid)),
  /** Der eigene Initiative-Pool (Geistesschärfe + Geschicklichkeit + Chrom). */
  initiativePool: (cid: string) => api.get<InitiativePool>(`${basis(cid)}/initiative/pool`),
  /** Selbst gewürfelten Wert melden — landet sofort in der Liste der SL. */
  meldeInitiative: (cid: string, teilnehmerId: string, erfolge: number) =>
    api.post<Kampf>(`${basis(cid)}/teilnehmer/${teilnehmerId}/initiative`, { erfolge }),
  /** Nur SL: Initiative aller NPCs und Begleiter automatisch würfeln. */
  wuerfleNpcs: (cid: string) => api.post<Kampf>(`${basis(cid)}/initiative/npcs`),
  /** Eigener Boosterzustand — Grundlage für das Popup beim Drankommen. */
  boosterStatus: (cid: string) => api.get<BoosterStatus>(`${basis(cid)}/booster/status`),
  /** Booster zünden: zweiter Eintrag mit dem gemeldeten Zweitwurf. */
  boosterAktivieren: (cid: string, erfolge: number) =>
    api.post<Kampf>(`${basis(cid)}/booster/aktivieren`, { erfolge }),
  /** Ergebnis des Paralysewurfs melden. */
  paralyse: (cid: string, teilnehmerId: string, geschafft: boolean) =>
    api.post<Kampf>(`${basis(cid)}/teilnehmer/${teilnehmerId}/paralyse`, { geschafft }),
  /** Nur SL: Aussetzen aufheben, nachdem darüber rotiert wurde. */
  aussetzenBeendet: (cid: string, teilnehmerId: string) =>
    api.post<Kampf>(`${basis(cid)}/teilnehmer/${teilnehmerId}/aussetzen-beendet`),
  beginnen: (cid: string) => api.post<Kampf>(basis(cid)),
  beenden: (cid: string) => api.delete<void>(basis(cid)),
  hinzu: (cid: string, daten: Partial<Teilnehmer> & { name: string }) =>
    api.post<Kampf>(`${basis(cid)}/teilnehmer`, daten),
  aendern: (cid: string, id: string, daten: Partial<Teilnehmer>) =>
    api.patch<Kampf>(`${basis(cid)}/teilnehmer/${id}`, daten),
  entfernen: (cid: string, id: string) => api.delete<Kampf>(`${basis(cid)}/teilnehmer/${id}`),
  weiter: (cid: string) => api.post<Kampf>(`${basis(cid)}/weiter`),
  amZug: (cid: string, teilnehmerId: string | null) =>
    api.post<Kampf>(`${basis(cid)}/amzug`, { teilnehmerId }),
};

/**
 * Ansagereihenfolge: umgekehrt zur Handlungsreihenfolge (Zeile 59).
 *
 * Wer zuletzt handelt, sagt zuerst an — dadurch kann die schnellste Person auf
 * alles reagieren, was die anderen vorhaben. Gewürfelt wird dann in der
 * richtigen Reihenfolge.
 */
export function ansageReihenfolge(teilnehmer: Teilnehmer[]) {
  return [...teilnehmer].reverse();
}
