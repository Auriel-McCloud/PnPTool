import { api } from "../api/client";

/**
 * Achievements: Katalog (SL-Baukasten), Verleihungen (eigene für Spieler,
 * alle für SL + spontane manuelle Vergabe) und AUTO-Vorschläge (live aus
 * dem Ereignisprotokoll berechnet, siehe docs/wiki/entities/achievements.md).
 */

export type AchievementArt = "AUTO" | "MANUELL";
export type BelohnungsArt = "KEINE" | "EP" | "HINTERGRUND";

/** Fester Code-Katalog (backend/app/achievements/schemas.py::AUSLOESE_ARTEN) —
 * kein Freitext, die SL wählt aus dieser Liste. */
export const AUSLOESE_ARTEN = [
  "ERSTER_KILL",
  "MOERDER",
  "MEISTE_SCHADEN_GENOMMEN",
  "MEISTE_SCHADEN_VERTEILT",
  "ERSTER_KAUF",
  "ERSTE_VERHANDLUNG",
  "CHARAKTER_ERSTELLT",
  "GEHEIMNISTRAEGER",
  "ERSTER_BESITZ_ZIEL",
  "ERSTE_BESCHREIBUNG_ZIEL",
  "ERSTER_CRITTER",
  "ERSTE_DROHNE",
  "ENDBOSS_BESIEGT",
  "ERSTE_SITZUNG_UEBERLEBT",
] as const;

export type AusloeseArt = (typeof AUSLOESE_ARTEN)[number];

export const AUSLOESE_ARTEN_MIT_ZIEL_GEGENSTAND = new Set<string>([
  "ERSTER_BESITZ_ZIEL",
  "ERSTE_BESCHREIBUNG_ZIEL",
]);

/** Lesbare Beschriftung je auslöseArt für Dropdowns/Listen. */
export const AUSLOESE_ART_LABEL: Record<string, string> = {
  ERSTER_KILL: "Erster Kill (campaign-weit)",
  MOERDER: "Mörder (jeder kriegt seins)",
  MEISTE_SCHADEN_GENOMMEN: "Meister Schaden genommen (Rekord)",
  MEISTE_SCHADEN_VERTEILT: "Meister Schaden verteilt (Rekord)",
  ERSTER_KAUF: "Erster eigener Kauf",
  ERSTE_VERHANDLUNG: "Erste Verhandlung",
  CHARAKTER_ERSTELLT: "Charaktererstellung abgeschlossen",
  GEHEIMNISTRAEGER: "Geheimnisträger (nur für eine Person freigegeben)",
  ERSTER_BESITZ_ZIEL: "Erster Besitz eines bestimmten Gegenstands",
  ERSTE_BESCHREIBUNG_ZIEL: "Erste freigeschaltete Beschreibung eines Gegenstands",
  ERSTER_CRITTER: "Erstes Haustier (Critter)",
  ERSTE_DROHNE: "Erste Drohne",
  ENDBOSS_BESIEGT: "Endgegner besiegt",
  ERSTE_SITZUNG_UEBERLEBT: "Erste Sitzung überlebt",
};

export interface Achievement {
  id: string;
  name: string;
  beschreibung: string;
  icon: string;
  art: AchievementArt;
  ausloeseArt: string | null;
  einzigartig: boolean;
  belohnungsArt: BelohnungsArt;
  belohnungsMenge: number;
  belohnungsHintergrund: string | null;
  zielGegenstandId: string | null;
  zielGegenstandName: string | null;
}

export interface AchievementEingabe {
  name?: string;
  beschreibung?: string;
  icon?: string;
  art?: AchievementArt;
  ausloeseArt?: string | null;
  einzigartig?: boolean;
  belohnungsArt?: BelohnungsArt;
  belohnungsMenge?: number;
  belohnungsHintergrund?: string | null;
  zielGegenstandId?: string | null;
}

export interface Verleihung {
  id: string;
  personId: string;
  personName: string | null;
  achievementId: string;
  achievementName: string | null;
  achievementIcon: string;
  achievementBeschreibung: string;
  zeitpunkt: string;
  ingameZeitpunkt: string;
  sitzungId: string | null;
  slNotiz: string;
  geloescht: boolean;
  text: string;
  abgeloest: boolean;
}

export interface Vorschlag {
  achievementId: string;
  achievementName: string;
  achievementIcon: string;
  personId: string;
  personName: string;
}

function basis(cid: string) {
  return `/api/campaigns/${cid}/achievements`;
}

export const achievementsApi = {
  katalog: (cid: string) => api.get<Achievement[]>(basis(cid)),
  anlegen: (cid: string, body: AchievementEingabe & { name: string }) =>
    api.post<Achievement>(basis(cid), body),
  aendern: (cid: string, id: string, body: AchievementEingabe) =>
    api.patch<Achievement>(`${basis(cid)}/${id}`, body),
  loeschen: (cid: string, id: string) => api.delete<void>(`${basis(cid)}/${id}`),

  meine: (cid: string) => api.get<Verleihung[]>(`${basis(cid)}/meine`),
  alleVerleihungen: (cid: string) => api.get<Verleihung[]>(`${basis(cid)}/verleihungen`),
  verleihen: (cid: string, achievementId: string, body: { personId: string; text?: string; slNotiz?: string }) =>
    api.post<Verleihung>(`${basis(cid)}/${achievementId}/verleihen`, body),
  verleihungLoeschen: (cid: string, verleihungId: string) =>
    api.put<void>(`${basis(cid)}/verleihungen/${verleihungId}/geloescht`, { geloescht: true }),

  vorschlaege: (cid: string) => api.get<Vorschlag[]>(`${basis(cid)}/vorschlaege`),
  vorschlagAnwenden: (
    cid: string,
    body: { achievementId: string; personId: string; text?: string; slNotiz?: string },
  ) => api.post<Verleihung>(`${basis(cid)}/vorschlaege/anwenden`, body),

  kiText: (cid: string, body: { achievementId: string; personId: string; kontextText?: string }) =>
    api.post<{ text: string }>(`${basis(cid)}/ki-text`, body),
};
