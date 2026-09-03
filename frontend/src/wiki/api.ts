/** API-Zugriff aufs Kampagnen-Wiki.
 *
 * Die SL-Vorschau ("Sehen wie Spieler X") hängt der Client selbst an jeden
 * GET an — hier ist dafür nichts zu tun.
 */
import { api } from "../api/client";

export type SichtbarkeitModus = "GM" | "ALLE" | "SPEZIFISCH";

export interface WikiSeite {
  id: string;
  titel: string;
  inhalt: string;
  parentId: string | null;
  symbol: string;
  sortierung: number;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
  erstelltAm: string;
  aktualisiertAm: string;
}

export interface VerzeichnisEintrag {
  stufe: number;
  text: string;
  anker: string;
}

export interface SeiteMitVerzeichnis extends WikiSeite {
  inhaltsverzeichnis: VerzeichnisEintrag[];
}

export interface BaumKnoten {
  id: string;
  titel: string;
  symbol: string;
  sortierung: number;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
  kinder: BaumKnoten[];
}

const basis = (campaignId: string) => `/api/campaigns/${campaignId}/wiki`;

export const getBaum = (campaignId: string) => api.get<BaumKnoten[]>(`${basis(campaignId)}/baum`);

export const getSeite = (campaignId: string, seitenId: string) =>
  api.get<SeiteMitVerzeichnis>(`${basis(campaignId)}/seiten/${seitenId}`);

export const seiteAnlegen = (
  campaignId: string,
  body: { titel: string; parentId?: string | null; symbol?: string },
) => api.post<WikiSeite>(`${basis(campaignId)}/seiten`, body);

export const seiteSpeichern = (
  campaignId: string,
  seitenId: string,
  body: Partial<Pick<WikiSeite, "titel" | "inhalt" | "symbol" | "sichtbarkeit" | "sichtbarFuer">>,
) => api.patch<WikiSeite>(`${basis(campaignId)}/seiten/${seitenId}`, body);

export const seiteVerschieben = (
  campaignId: string,
  seitenId: string,
  body: { parentId: string | null; sortierung?: number },
) => api.post<WikiSeite>(`${basis(campaignId)}/seiten/${seitenId}/verschieben`, body);

export const seiteLoeschen = (campaignId: string, seitenId: string) =>
  api.delete<void>(`${basis(campaignId)}/seiten/${seitenId}`);

/** "Was bisher geschah": alles bis einschliesslich dieser Seite freigeben. */
export const bisHierherFreigeben = (
  campaignId: string,
  bisSeiteId: string,
  sichtbarkeit: SichtbarkeitModus = "ALLE",
  sichtbarFuer: string[] = [],
) =>
  api.post<{ freigegeben: number; seitenIds: string[] }>(`${basis(campaignId)}/freigeben`, {
    bisSeiteId,
    sichtbarkeit,
    sichtbarFuer,
  });

export const getRueckverweise = (campaignId: string, zielId: string) =>
  api.get<{ id: string; titel: string }[]>(`${basis(campaignId)}/verweise/${zielId}`);

/** Bild hochladen. Kein JSON — deshalb an api() vorbei mit FormData.
 *  Content-Type NICHT setzen: der Browser muss die multipart-Grenze selbst
 *  bestimmen, ein manuell gesetzter Header macht den Upload kaputt. */
export async function bildHochladen(campaignId: string, datei: File): Promise<{ url: string }> {
  const daten = new FormData();
  daten.append("file", datei);
  const antwort = await fetch(`${basis(campaignId)}/bilder`, {
    method: "POST",
    credentials: "include",
    body: daten,
  });
  if (!antwort.ok) {
    const fehler = await antwort.json().catch(() => ({ detail: antwort.statusText }));
    throw new Error(fehler.detail ?? "Upload fehlgeschlagen");
  }
  return antwort.json();
}
