import { api } from "../api/client";

/** Welche Sprites es gibt — gleiche Liste wie `PET_ARTEN` in backend/app/pets/logic.py. */
export const PET_ARTEN = [{ wert: "drache", name: "Kleiner Drache" }] as const;
export type PetArt = (typeof PET_ARTEN)[number]["wert"];

export interface PetAufSchirm {
  id: string;
  name: string;
  art: PetArt;
  besitzerId: string;
  besitzerName: string;
  /** Von welcher Seite es hereinkommt. */
  seite: "links" | "rechts";
  /** Zählt jede Ankunft hoch — neuer Wert = neuer Auftritt. */
  ankunft: number;
}

export interface Haeufchen {
  id: string;
  petId: string;
  /** Anteile 0..1 der Bildschirmbreite/-höhe. */
  x: number;
  y: number;
  /** Häufchen (antippen) oder Brandfleck vom Feuerniesen (wegwischen). */
  art?: "haeufchen" | "brand";
}

export type PetNachricht =
  | { typ: "pets"; daten: PetAufSchirm[] }
  | { typ: "haeufchen"; daten: Haeufchen[] };

export const petsApi = {
  artLesen: (cid: string, critterId: string) =>
    api.get<{ id: string; art: PetArt | null }>(`/api/campaigns/${cid}/pets/${critterId}`),
  artSetzen: (cid: string, critterId: string, art: PetArt | null) =>
    api.put<{ id: string; art: PetArt | null }>(`/api/campaigns/${cid}/pets/${critterId}`, { art }),
};

/**
 * Live-Leitung fürs Pet. Gleiches Wiederverbinden wie bei den Mitteilungen.
 * Gibt `senden` und `schliessen` zurück.
 */
export function verbindePets(
  campaignId: string,
  onNachricht: (n: PetNachricht) => void,
): { senden: (n: object) => void; schliessen: () => void } {
  let socket: WebSocket | null = null;
  let versuch = 0;
  let zu = false;
  let timer: number | undefined;

  const verbinde = () => {
    if (zu) return;
    const schema = window.location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${schema}//${window.location.host}/api/campaigns/${campaignId}/pets/live`);
    socket.onopen = () => {
      versuch = 0;
    };
    socket.onmessage = (ev) => {
      try {
        onNachricht(JSON.parse(ev.data) as PetNachricht);
      } catch {
        /* kaputte Nachricht ignorieren */
      }
    };
    socket.onclose = () => {
      if (zu) return;
      versuch += 1;
      timer = window.setTimeout(verbinde, Math.min(1000 * 2 ** (versuch - 1), 15000));
    };
    socket.onerror = () => socket?.close();
  };
  verbinde();

  return {
    senden: (n) => {
      if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(n));
    },
    schliessen: () => {
      zu = true;
      window.clearTimeout(timer);
      socket?.close();
    },
  };
}
