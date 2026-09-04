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
