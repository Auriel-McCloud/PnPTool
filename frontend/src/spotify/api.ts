import { api } from "../api/client";

/**
 * Spotify — globale Anbindung (ein Konto fürs ganze Tool, siehe
 * backend/app/spotify/). Verbinden läuft über eine echte Seitennavigation
 * (OAuth-Redirect), nicht über fetch() — deshalb keine `verbinden()`-Funktion
 * hier, nur ein Link auf `/api/spotify/verbinden`.
 */

export interface SpotifyStatus {
  verbunden: boolean;
  anzeigename: string | null;
}

export interface SpotifyPlaylistTreffer {
  uri: string;
  id: string;
  name: string;
  besitzer: string;
  bildUrl: string;
  anzahlTracks: number;
}

export const spotifyApi = {
  status: () => api.get<SpotifyStatus>("/api/spotify/status"),
  trennen: () => api.post<{ ok: boolean }>("/api/spotify/trennen"),
  playlistsSuchen: (cid: string, suchtext: string) =>
    api.get<SpotifyPlaylistTreffer[]>(
      `/api/campaigns/${cid}/spotify/suche?q=${encodeURIComponent(suchtext)}`,
    ),
  /** Manueller Fallback-Knopf — startet die am Ziel hinterlegte Playlist sofort. */
  abspielen: (cid: string, zielId: string, zielKind: "Ort" | "Event") =>
    api.post<{ hinweis: string }>(`/api/campaigns/${cid}/spotify/abspielen`, { zielId, zielKind }),
};
