import { api } from "../api/client";

/**
 * Party — wer gerade zusammen unterwegs ist.
 *
 * Anders als eine Fraktion hat eine Party keine eigenen Ziele/Ressourcen —
 * sie ist schlicht "wer gerade beisammen ist" (Neotopia-Wiki, 28.08.2026:
 * "Spieler bilden nicht immer eine einzige feste Gruppe — sie können sich
 * aufteilen, wodurch mehrere gleichzeitige Partys entstehen"). Eine Person
 * ist immer nur in höchstens einer Party gleichzeitig; höchstens eine Party
 * pro Kampagne ist "aktiv" (die gerade bespielte — ihr Aufenthaltsort löst
 * später die Musik aus, Spotify/MusicCast-Anbindung noch nicht gebaut).
 */

export interface PartyMitglied {
  id: string;
  name: string;
  personType: string;
}

export interface Party {
  id: string;
  name: string;
  beschreibung: string;
  notizen: string;
  aktiv: boolean;
  mitglieder: PartyMitglied[];
  aufenthaltsortId: string | null;
  aufenthaltsortName: string | null;
  aufenthaltsortKind: string | null;
  sichtbarkeit: string;
  sichtbarFuer: string[];
  /** Nur nach aktivieren()/aufenthaltsortSetzen() gesetzt — Spotify-Rückmeldung. */
  musikHinweis?: string | null;
}

export type PartyEingabe = Partial<Pick<Party, "name" | "beschreibung" | "notizen" | "sichtbarkeit" | "sichtbarFuer">>;

function basis(campaignId: string) {
  return `/api/campaigns/${campaignId}/party`;
}

export const partyApi = {
  liste: (cid: string) => api.get<Party[]>(basis(cid)),
  einzeln: (cid: string, id: string) => api.get<Party>(`${basis(cid)}/${id}`),
  anlegen: (cid: string, daten: PartyEingabe) => api.post<Party>(basis(cid), daten),
  aendern: (cid: string, id: string, daten: PartyEingabe) => api.patch<Party>(`${basis(cid)}/${id}`, daten),
  entfernen: (cid: string, id: string) => api.delete<void>(`${basis(cid)}/${id}`),
  mitgliedHinzufuegen: (cid: string, id: string, personId: string) =>
    api.post<Party>(`${basis(cid)}/${id}/mitglieder`, { personId }),
  mitgliedEntfernen: (cid: string, id: string, personId: string) =>
    api.delete<Party>(`${basis(cid)}/${id}/mitglieder/${personId}`),
  /** `zielId: null` löst den Aufenthaltsort — die Party ist dann "unterwegs". */
  aufenthaltsortSetzen: (cid: string, id: string, zielId: string | null, zielKind: "Ort" | "Event" | null) =>
    api.put<Party>(`${basis(cid)}/${id}/aufenthaltsort`, { zielId, zielKind }),
  aktivieren: (cid: string, id: string) => api.post<Party>(`${basis(cid)}/${id}/aktivieren`, {}),
  deaktivieren: (cid: string, id: string) => api.post<Party>(`${basis(cid)}/${id}/deaktivieren`, {}),
};
