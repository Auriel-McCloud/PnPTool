/** SL-Mitteilungen: Live-Popups von der Spielleitung. */
import { api } from "../api/client";

export type MitteilungsArt = "TEXT" | "BILD";

export interface Mitteilung {
  id: string;
  art: MitteilungsArt;
  inhalt: string;
  bildUrl: string;
  anAlle: boolean;
  empfaengerIds: string[];
  gelesenVon: string[];
  erstelltAm: string;
}

export interface MitteilungenStand {
  mitteilungen: Mitteilung[];
  ungelesen: number;
}

const basis = (campaignId: string) => `/api/campaigns/${campaignId}/mitteilungen`;

export const getMitteilungen = (campaignId: string) =>
  api.get<MitteilungenStand>(basis(campaignId));

export const sendeMitteilung = (
  campaignId: string,
  body: { art?: MitteilungsArt; inhalt?: string; bildUrl?: string; anAlle: boolean; empfaengerIds?: string[] },
) => api.post<{ mitteilung: Mitteilung; zugestellt: number }>(basis(campaignId), body);

export const markiereGelesen = (campaignId: string, id: string) =>
  api.post<void>(`${basis(campaignId)}/${id}/gelesen`);

export const markiereAllesGelesen = (campaignId: string) =>
  api.post<void>(`${basis(campaignId)}/gelesen`);

export const ziehZurueck = (campaignId: string, id: string) =>
  api.delete<void>(`${basis(campaignId)}/${id}`);

/** Was über die Leitung kommt. */
export type LiveNachricht =
  | { typ: "stand"; daten: MitteilungenStand }
  | { typ: "mitteilung"; daten: Mitteilung }
  | { typ: "zurueckgezogen"; daten: { id: string } };

/**
 * Öffnet die Live-Leitung und verbindet bei Abbruch selbstständig neu.
 *
 * Wichtig fürs Tablet: Android schläfert Hintergrund-Tabs ein und trennt
 * dabei die Verbindung. Ohne Wiederverbinden bliebe das Commlink still, und
 * genau in dem Moment kommt die Initiative-Ansage.
 *
 * Der Wartezeitraum wächst bei wiederholtem Fehlschlag (1s, 2s, 4s … max 15s),
 * damit ein abgeschaltetes Backend nicht im Sekundentakt angeklopft wird.
 */
export function verbindeLive(
  campaignId: string,
  onNachricht: (n: LiveNachricht) => void,
  onStatus?: (verbunden: boolean) => void,
): () => void {
  let socket: WebSocket | null = null;
  let versuch = 0;
  let zu = false;
  let timer: number | undefined;

  const verbinde = () => {
    if (zu) return;
    const schema = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Über denselben Host/Port wie die Seite — der Vite-Proxy reicht ws weiter.
    socket = new WebSocket(`${schema}//${window.location.host}/api/campaigns/${campaignId}/mitteilungen/live`);

    socket.onopen = () => {
      versuch = 0;
      onStatus?.(true);
    };

    socket.onmessage = (ev) => {
      try {
        onNachricht(JSON.parse(ev.data) as LiveNachricht);
      } catch {
        // Kaputte Nachricht ignorieren statt die Leitung zu verlieren.
      }
    };

    socket.onclose = () => {
      onStatus?.(false);
      if (zu) return;
      versuch += 1;
      const wartezeit = Math.min(1000 * 2 ** (versuch - 1), 15000);
      timer = window.setTimeout(verbinde, wartezeit);
    };

    socket.onerror = () => socket?.close();
  };

  verbinde();

  return () => {
    zu = true;
    window.clearTimeout(timer);
    socket?.close();
  };
}
