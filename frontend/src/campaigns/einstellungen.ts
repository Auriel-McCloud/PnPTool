import { api } from "../api/client";

/**
 * Kampagnenweite Spieleinstellungen.
 *
 * Bewusst offen typisiert: die Sammlung soll wachsen können, ohne dass hier
 * jedes Mal ein Feld nachgetragen werden muss (siehe
 * backend/app/campaigns/repository.py, EINSTELLUNGEN_DEFAULTS).
 */
export interface Einstellungen {
  /** Zeigt Gewicht und Auslastung an — rein informativ, verhindert nichts. */
  gewichtAktiv: boolean;
  /** Attribut, aus dem sich die Traglast einer Person ergibt. */
  traglastAttribut: string;
  /** Kilogramm je Attributpunkt. */
  traglastProPunkt: number;
  [weitere: string]: unknown;
}

export const einstellungenApi = {
  lesen: (cid: string) => api.get<Einstellungen>(`/api/campaigns/${cid}/einstellungen`),
  aendern: (cid: string, aenderungen: Partial<Einstellungen>) =>
    api.patch<Einstellungen>(`/api/campaigns/${cid}/einstellungen`, aenderungen),
};

/** "2,5 / 30 kg" — kompakt und ohne unnötige Nachkommastellen. */
export function formatiereLast(last: number, kapazitaet: number): string {
  const z = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1).replace(".", ","));
  return kapazitaet > 0 ? `${z(last)} / ${z(kapazitaet)} kg` : `${z(last)} kg`;
}
