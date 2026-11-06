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
  /** Beschwörungs-Ki-Tama (30.10.2026): Runden bis der beschworene Critter
   * automatisch den Tracker verlässt. undefined/null = kein Zeitlimit. */
  rundenVerbleibend?: number | null;
  notiz: string;
  erledigt: boolean;
  personId: string | null;
  personType: string | null;
  begleiterId: string | null;
  hexQ?: number | null;
  hexR?: number | null;
  hexDrehung?: number | null;
  zugStartQ?: number | null;
  zugStartR?: number | null;
  bildUrl?: string;
  istGross?: boolean;
  istDrohne?: boolean;
  istFahrzeug?: boolean;
  istCritter?: boolean;
  /** Rigger/Beschwörer — Spieler schiebt diese Tokens am eigenen Zug. */
  besitzerId?: string | null;
  blickrichtung?: number;
  versteckt?: boolean;
  rundumsicht?: boolean;
  /** Letzter Stand, nicht die Wahrheit. */
  veraltet?: boolean;
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
  /** Decker war schon Hot. Erst die Bleiben-Frage, dann diese. */
  matrixBleibenOffen: boolean;
}

/** Hot-Zustand des eigenen Charakters. */
export interface HotStatus {
  hatNeurolink: boolean;
  hatDeck: boolean;
  matrixHot: boolean;
  matrixBleibenFaellig: boolean;
  hotDrohneId: string | null;
  hotDrohneName: string | null;
  bleibenFaellig: boolean;
  darfWaehlen: boolean;
}

export interface Kampf {
  id: string;
  runde: number;
  /** Kennung des Teilnehmers, der gerade handelt. */
  amZug: string | null;
  teilnehmer: Teilnehmer[];
  /** Ki-Tama-Item-IDs, deren einer Ruf in diesem Kampf schon weg ist. */
  verbrauchteBeschwoerungen?: string[];
  battlemapId?: string | null;
}

export interface MatrixZeile {
  personId: string;
  name: string;
  istParty: boolean;
  ice: number | null;
  iceMax: number | null;
  iceArt?: "willenskraft" | "geraet" | null;
  klickbar: boolean;
  aus?: { id: string; name: string; runden: number }[];
}

export interface MatrixUebersicht {
  runde: number;
  teilnehmer: MatrixZeile[];
}

export interface MatrixZiel {
  id: string;
  name: string;
  art: string;
}

export interface MatrixTreffer {
  iceVorher: number;
  iceNachher: number;
  punkte: number;
  schlag: number;
  art: "schaden" | "wahl" | "schalten";
  quelle: "willenskraft" | "geraet";
  /** Drohne, kein Fahrzeug. Dann gilt die Wahl auch ohne Matrix-Hot. */
  roboter?: boolean;
  ziele: MatrixZiel[];
}

function basis(cid: string) {
  return `/api/campaigns/${cid}/kampf`;
}

/** SL-Aufruf für einen NPC. getAsGm, damit die Spieler-Vorschau das nicht umbiegt. */
function fuerPerson(pfad: string, personId?: string | null) {
  if (!personId) return pfad;
  const trenner = pfad.includes("?") ? "&" : "?";
  return `${pfad}${trenner}personId=${encodeURIComponent(personId)}`;
}

function lesen<T>(pfad: string, personId?: string | null) {
  return personId ? api.getAsGm<T>(fuerPerson(pfad, personId)) : api.get<T>(pfad);
}

export const kampfApi = {
  laden: (cid: string) => api.get<Kampf | null>(basis(cid)),
  /** Der eigene Initiative-Pool (Geistesschärfe + Geschicklichkeit + Chrom). */
  initiativePool: (cid: string) => api.get<InitiativePool>(`${basis(cid)}/initiative/pool`),
  /** Selbst gewürfelten Wert melden — landet sofort in der Liste der SL.
   *  Funktioniert auch für die eigene aktive Drohne/das eigene Fahrzeug
   *  (26.10.2026, serverseitig über BEGLEITET-Kante geprüft). */
  meldeInitiative: (cid: string, teilnehmerId: string, erfolge: number) =>
    api.post<Kampf>(`${basis(cid)}/teilnehmer/${teilnehmerId}/initiative`, { erfolge }),
  /** Eigene Initiative eintragen. Steht man noch nicht in der Liste, kommt
   *  man mit diesem Wert dazu. */
  selbstInitiative: (cid: string, erfolge: number) =>
    api.post<Kampf>(`${basis(cid)}/ich`, { erfolge }),
  /** Self-Service (26.10.2026): der Rigger nimmt seine eigene aktive Drohne/
   *  sein eigenes Fahrzeug selbst in den laufenden Kampf auf, Initiative
   *  startet bei 0 und wird direkt danach per Klick gesetzt. Nummeriert
   *  automatisch durch, wenn der Name schon vergeben ist ("Spinne 1/2"). */
  drohneBeitreten: (cid: string, drohneId: string) =>
    api.post<Kampf>(`${basis(cid)}/drohnen/${drohneId}/beitreten`),
  /** Self-Service (30.10.2026): beschwört den an ein Ki-Tama gebundenen
   *  Critter in den laufenden Kampf — `erfolge` ist die selbstberichtete
   *  Beschwörungs-Probe (Intelligenz + Beschwörungswert), MUSS vor der
   *  Initiative-Eingabe bestanden sein. Initiative startet bei 0 und wird
   *  danach wie bei Drohnen per `meldeInitiative` gesetzt. */
  beschwoeren: (cid: string, itemId: string, erfolge: number, ausgang: "ja" | "nein" | "patzer" = "ja") =>
    api.post<Kampf>(`${basis(cid)}/gegenstaende/${itemId}/beschwoeren`, { erfolge, ausgang }),
  /** Nur SL: Initiative aller NPCs und Begleiter automatisch würfeln. */
  wuerfleNpcs: (cid: string) => api.post<Kampf>(`${basis(cid)}/initiative/npcs`),
  /** Eigener Boosterzustand — Grundlage für das Popup beim Drankommen.
   *  personId nur für die SL: der NPC, der gerade dran ist. */
  boosterStatus: (cid: string, personId?: string | null) =>
    lesen<BoosterStatus>(`${basis(cid)}/booster/status`, personId),
  /** Hot: Neurolink-Pflicht, eine Drohne pro Runde, Matrix-Knopf fürs Deck. */
  hotStatus: (cid: string, personId?: string | null) => lesen<HotStatus>(`${basis(cid)}/hot`, personId),
  hotDrohne: (cid: string, drohneId: string, personId?: string | null) =>
    api.post<HotStatus>(`${basis(cid)}/hot`, personId ? { drohneId, personId } : { drohneId }),
  hotBleiben: (cid: string, bleiben: boolean, personId?: string | null) =>
    api.post<HotStatus>(`${basis(cid)}/hot`, personId ? { bleiben, personId } : { bleiben }),
  hotMatrix: (cid: string, matrix: boolean, personId?: string | null) =>
    api.post<HotStatus>(`${basis(cid)}/hot`, personId ? { matrix, personId } : { matrix }),
  hotMatrixBleiben: (cid: string, bleiben: boolean, personId?: string | null) =>
    api.post<HotStatus>(
      `${basis(cid)}/hot`,
      personId ? { matrixBleiben: bleiben, personId } : { matrixBleiben: bleiben },
    ),
  /** Booster zünden: zweiter Eintrag mit dem gemeldeten Zweitwurf. */
  boosterAktivieren: (cid: string, erfolge: number, personId?: string | null) =>
    api.post<Kampf>(`${basis(cid)}/booster/aktivieren`, personId ? { erfolge, personId } : { erfolge }),
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
  karte: (cid: string, battlemapId: string | null) =>
    api.put<Kampf>(`${basis(cid)}/karte`, { battlemapId }),
  position: (cid: string, teilnehmerId: string, q: number, r: number, drehung = 0) =>
    api.patch<Kampf>(`${basis(cid)}/teilnehmer/${teilnehmerId}/position`, { q, r, drehung }),
  blick: (cid: string, teilnehmerId: string, blickrichtung: number) =>
    api.patch<Kampf>(`${basis(cid)}/teilnehmer/${teilnehmerId}/blick`, { blickrichtung }),
  versteckt: (cid: string, teilnehmerId: string, versteckt: boolean) =>
    api.patch<Kampf>(`${basis(cid)}/teilnehmer/${teilnehmerId}/versteckt`, { versteckt }),
  amZug: (cid: string, teilnehmerId: string | null) =>
    api.post<Kampf>(`${basis(cid)}/amzug`, { teilnehmerId }),
  matrix: (cid: string) => api.get<MatrixUebersicht>(`${basis(cid)}/matrix`),
  matrixAus: (cid: string, personId: string) =>
    api.get<{ aus: { zielId: string; name: string; art: string; runden: number }[]; ice?: number; iceMax?: number; schlag?: number }>(
      `${basis(cid)}/matrix/aus/${personId}`,
    ),
  matrixNavigation: (cid: string, erfolge: number) =>
    api.post<{ gesehen: boolean }>(`${basis(cid)}/matrix/navigation`, { erfolge }),
  matrixEw: (cid: string, erfolge: number) =>
    api.post<{ bonus: number }>(`${basis(cid)}/matrix/electronic-warfare`, { erfolge }),
  matrixTreffer: (cid: string, zielPersonId: string, erfolge: number, fertigkeit: string) =>
    api.post<MatrixTreffer>(`${basis(cid)}/matrix/treffer`, { zielPersonId, erfolge, fertigkeit }),
  matrixBestaetigen: (
    cid: string,
    zielPersonId: string,
    posten: { id: string; runden: number }[],
    schlag = false,
  ) =>
    api.post<{
      schlag?: number;
      aus?: { zielId: string; name: string; art: string; runden: number }[];
      hotRueckschlag?: { riggerId: string; riggerName: string; schlag: number }[];
      dumpshock?: { riggerId: string; riggerName: string }[];
    }>(`${basis(cid)}/matrix/bestaetigen`, { zielPersonId, posten, schlag }),
  matrixAn: (cid: string, eintragId: string) =>
    api.post(`${basis(cid)}/matrix/reaktivieren/${eintragId}`),
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
