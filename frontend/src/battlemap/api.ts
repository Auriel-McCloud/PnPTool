/** Battlemap: vorbereitbare Hex-Karten, live zeichnen, Tokens aus dem Kampf. */
import { api } from "../api/client";
import type { SichtbarkeitModus } from "../entities/api";

export type Pfad = Record<string, unknown>;

export interface Battlemap {
  id: string;
  name: string;
  pfade: Pfad[];
  bildUrl: string;
  spielerDuerfenZeichnen: boolean;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
  geloescht: boolean;
  erstelltAm: string;
  hexGroesse: number;
  originX: number;
  originY: number;
  spawnPcQ: number | null;
  spawnPcR: number | null;
  spawnNpcQ: number | null;
  spawnNpcR: number | null;
}

const basis = (campaignId: string) => `/api/campaigns/${campaignId}/battlemaps`;

export const battlemapApi = {
  liste: (campaignId: string) => api.get<Battlemap[]>(basis(campaignId)),
  papierkorb: (campaignId: string) => api.get<Battlemap[]>(`${basis(campaignId)}/papierkorb`),
  holen: (campaignId: string, id: string) => api.get<Battlemap>(`${basis(campaignId)}/${id}`),
  anlegen: (campaignId: string, name: string) => api.post<Battlemap>(basis(campaignId), { name }),
  aktualisieren: (campaignId: string, id: string, body: Partial<Battlemap>) =>
    api.patch<Battlemap>(`${basis(campaignId)}/${id}`, body),
  pfadeSpeichern: (campaignId: string, id: string, pfade: Pfad[]) =>
    api.patch<Battlemap>(`${basis(campaignId)}/${id}/pfade`, { pfade }),
  geloeschtSetzen: (campaignId: string, id: string, geloescht: boolean) =>
    api.put<Battlemap>(`${basis(campaignId)}/${id}/geloescht`, { geloescht }),
  async bildHochladen(campaignId: string, id: string, datei: File): Promise<Battlemap> {
    const daten = new FormData();
    daten.append("file", datei);
    const antwort = await fetch(`${basis(campaignId)}/${id}/bild`, {
      method: "POST",
      credentials: "include",
      body: daten,
    });
    if (!antwort.ok) {
      const fehler = await antwort.json().catch(() => ({ detail: antwort.statusText }));
      throw new Error(fehler.detail ?? "Upload fehlgeschlagen");
    }
    return antwort.json();
  },
};

export type BattlemapLive =
  | { typ: "pfade"; daten: { pfade: Pfad[] } }
  | { typ: "karte"; daten: Battlemap }
  | {
      typ: "tokens";
      daten: {
        amZug: string | null;
        battlemapId: string | null;
        teilnehmer: {
          id: string;
          name?: string;
          personId?: string | null;
          personType?: string | null;
          begleiterId?: string | null;
          hexQ: number | null;
          hexR: number | null;
          hexDrehung: number | null;
          zugStartQ: number | null;
          zugStartR: number | null;
          bildUrl?: string;
          istGross?: boolean;
          istDrohne?: boolean;
          istFahrzeug?: boolean;
          istCritter?: boolean;
          besitzerId?: string | null;
        }[];
      };
    };

export function verbindeBattlemapLive(
  campaignId: string,
  karteId: string,
  onNachricht: (n: BattlemapLive) => void,
  onStatus?: (verbunden: boolean) => void,
) {
  let socket: WebSocket | null = null;
  let versuch = 0;
  let zu = false;
  let timer: number | undefined;

  const verbinde = () => {
    if (zu) return;
    const schema = window.location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(
      `${schema}//${window.location.host}/api/campaigns/${campaignId}/battlemaps/${karteId}/live`,
    );
    socket.onopen = () => {
      versuch = 0;
      onStatus?.(true);
    };
    socket.onmessage = (ev) => {
      try {
        onNachricht(JSON.parse(ev.data) as BattlemapLive);
      } catch {
        /* kaputt ignorieren */
      }
    };
    socket.onclose = () => {
      onStatus?.(false);
      if (zu) return;
      versuch += 1;
      timer = window.setTimeout(verbinde, Math.min(1000 * 2 ** (versuch - 1), 15000));
    };
    socket.onerror = () => socket?.close();
  };
  verbinde();
  return {
    senden: (pfade: Pfad[]) => {
      if (socket && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ pfade }));
    },
    trennen: () => {
      zu = true;
      window.clearTimeout(timer);
      socket?.close();
    },
  };
}
