import { api } from "../api/client";
import type { Nachricht } from "./api";

/**
 * Gruppenchats (Phase 2 des Messengers).
 *
 * Nur die Spielleitung legt Gruppen an; Mitglieder sind Spielercharaktere und
 * NPCs gemischt. Die Namen kommen fertig pro Betrachter vom Server: Spieler
 * sehen NPCs unter dem eigenen Alias („Unbekannter Ork“), die SL die echten
 * Namen (siehe backend/app/gruppenchat/security.py).
 */

export interface Teilnehmer {
  id: string;
  name: string;
  bildUrl: string;
  istNpc: boolean;
  /** Der Betrachter selbst (nur Spieleransicht). */
  ich: boolean;
}

export interface Gruppe {
  id: string;
  name: string;
  /** Geschlossen = für Spieler unsichtbar, nichts gelöscht. */
  offen: boolean;
  ungelesen: number;
  teilnehmer: Teilnehmer[];
}

export interface GruppenNachricht extends Nachricht {
  bildUrl: string;
}

export interface GruppenChat {
  gruppe: Gruppe;
  nachrichten: GruppenNachricht[];
  /** Nur SL: die NPC-Mitglieder, als die sie schreiben kann. */
  sprecher: Teilnehmer[];
}

function basis(cid: string) {
  return `/api/campaigns/${cid}/gruppenchats`;
}

export const gruppenApi = {
  /** Spieler: die eigenen offenen Gruppen. SL: alle. */
  liste: (cid: string) => api.get<Gruppe[]>(basis(cid)),
  chat: (cid: string, gruppeId: string) => api.get<GruppenChat>(`${basis(cid)}/${gruppeId}/chat`),
  /** Spieler schreiben als eigener Charakter; die SL gibt `alsPersonId` (ein NPC der Gruppe) an. */
  senden: (cid: string, gruppeId: string, inhalt: string, alsPersonId?: string) =>
    api.post<GruppenNachricht>(`${basis(cid)}/${gruppeId}/chat`, { inhalt, alsPersonId: alsPersonId ?? null }),

  // --- nur SL
  anlegen: (cid: string, name: string, personIds: string[]) =>
    api.post<Gruppe>(basis(cid), { name, personIds }),
  aendern: (cid: string, gruppeId: string, daten: { name?: string; offen?: boolean }) =>
    api.patch<Gruppe>(`${basis(cid)}/${gruppeId}`, daten),
  loeschen: (cid: string, gruppeId: string) => api.delete<void>(`${basis(cid)}/${gruppeId}`),
  teilnehmerHinzu: (cid: string, gruppeId: string, personId: string) =>
    api.post<Gruppe>(`${basis(cid)}/${gruppeId}/teilnehmer`, { personId }),
  teilnehmerEntfernen: (cid: string, gruppeId: string, personId: string) =>
    api.delete<Gruppe>(`${basis(cid)}/${gruppeId}/teilnehmer/${personId}`),
};
