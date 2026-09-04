import { api } from "../api/client";

/**
 * Kontakte und Messenger.
 *
 * Der echte NPC-Name kommt **nur** über `echterName` und nur, wenn die
 * Spielleitung ihn freigegeben hat — es gibt bewusst kein `npcName` in der
 * Spielerantwort (siehe backend/app/kontakte/security.py).
 */

export type Kontaktstufe = "GESEHEN" | "GESPROCHEN" | "KONTAKT_AUSGETAUSCHT";
export type AnfrageStatus = "KEINE" | "OFFEN" | "ANGENOMMEN" | "ABGELEHNT";

export const STUFEN: { wert: Kontaktstufe; name: string; erklaerung: string }[] = [
  { wert: "GESEHEN", name: "Gesehen", erklaerung: "Man ist sich begegnet — mehr nicht." },
  { wert: "GESPROCHEN", name: "Gesprochen", erklaerung: "Ihr habt geredet; Beschreibung wird sichtbar." },
  {
    wert: "KONTAKT_AUSGETAUSCHT",
    name: "Kontakt",
    erklaerung: "Nummern getauscht — der Chat ist offen.",
  },
];

export interface Kontakt {
  id: string;
  npcId: string;
  alias: string;
  echterName: string | null;
  persoenlicherAlias: string;
  bildUrl: string;
  beschreibung: string;
  stufe: Kontaktstufe;
  echterNameBekannt: boolean;
  kontaktAnfrageStatus: AnfrageStatus;
  persoenlicheNotizen: string;
  chatOffen: boolean;
  ungelesen: number;
}

export interface KontaktGm extends Kontakt {
  pcId: string;
  pcName: string;
  npcName: string;
}

export interface Nachricht {
  id: string;
  inhalt: string;
  erstelltAm: string;
  vonMir: boolean;
  absender: string;
  gelesen: boolean;
}

export interface Chat {
  kontaktId: string;
  npcId: string;
  alias: string;
  chatOffen: boolean;
  nachrichten: Nachricht[];
}

function basis(cid: string) {
  return `/api/campaigns/${cid}/kontakte`;
}

export const kontakteApi = {
  /** Das eigene Kontaktverzeichnis. */
  meine: (cid: string) => api.get<Kontakt[]>(basis(cid)),
  /** Nur SL: wer kennt wen. */
  uebersicht: (cid: string) => api.get<KontaktGm[]>(`${basis(cid)}/uebersicht`),
  /** Nur SL: offene Kontaktanfragen. */
  anfragen: (cid: string) => api.get<KontaktGm[]>(`${basis(cid)}/anfragen`),
  /** Nur SL: Kontaktwissen von Hand anlegen. */
  anlegen: (cid: string, pcId: string, npcId: string, stufe: Kontaktstufe = "GESEHEN") =>
    api.post<KontaktGm>(basis(cid), { pcId, npcId, stufe }),
  /** Nur SL: Stufe, Namenskenntnis oder Alias ändern. */
  aendern: (
    cid: string,
    kontaktId: string,
    daten: { stufe?: Kontaktstufe; echterNameBekannt?: boolean; alias?: string },
  ) => api.patch<KontaktGm>(`${basis(cid)}/${kontaktId}`, daten),
  loeschen: (cid: string, kontaktId: string) => api.delete<void>(`${basis(cid)}/${kontaktId}`),

  /** Eigener Alias für diesen NPC. */
  aliasSetzen: (cid: string, kontaktId: string, alias: string) =>
    api.put<Kontakt>(`${basis(cid)}/${kontaktId}/alias`, { alias }),
  /** Eigene Notizen zu diesem Kontakt. */
  notizenSetzen: (cid: string, kontaktId: string, inhalt: string) =>
    api.put<Kontakt>(`${basis(cid)}/${kontaktId}/notizen`, { inhalt }),
  /** Kontaktanfrage stellen — erst ab „gesprochen“, und nur einmal. */
  anfragen_stellen: (cid: string, kontaktId: string) =>
    api.post<Kontakt>(`${basis(cid)}/${kontaktId}/anfrage`),
  /** Nur SL: als der NPC annehmen oder ablehnen. */
  entscheiden: (cid: string, kontaktId: string, annehmen: boolean) =>
    api.post<KontaktGm>(`${basis(cid)}/${kontaktId}/anfrage/entscheiden`, { annehmen }),
  /** Nur SL: fehlendes „Gesehen“ aus dem Beziehungsgraphen anlegen. */
  erkennen: (cid: string) => api.post<KontaktGm[]>(`${basis(cid)}/erkennen`),

  chat: (cid: string, kontaktId: string) => api.get<Chat>(`${basis(cid)}/${kontaktId}/chat`),
  senden: (cid: string, kontaktId: string, inhalt: string) =>
    api.post<Nachricht>(`${basis(cid)}/${kontaktId}/chat`, { inhalt }),
};

/** TipTap-JSON zu Klartext — für die Vorschau in der Liste. */
export function alsText(inhalt: string): string {
  if (!inhalt) return "";
  try {
    const dok = JSON.parse(inhalt);
    if (dok?.type !== "doc") return inhalt;
    const zeilen: string[] = [];
    for (const absatz of dok.content ?? []) {
      const text = (absatz.content ?? []).map((t: { text?: string }) => t.text ?? "").join("");
      zeilen.push(text);
    }
    return zeilen.join("\n");
  } catch {
    return inhalt;
  }
}
