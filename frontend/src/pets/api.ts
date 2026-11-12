import { api } from "../api/client";

/** Welche Sprites es gibt — gleiche Liste wie `PET_ARTEN` in backend/app/pets/logic.py.
 *  `fuer`: wo die SL sie zur Auswahl bekommt — Tiere am Critter, Bärbel (die
 *  fliegende Bibel, 11.11.2026) an einem Gegenstand. */
export const PET_ARTEN = [
  { wert: "drache", name: "Kleiner Drache", fuer: "critter" },
  // Mark, 12.11.2026 (Critter „Wolke Salamander“): derselbe Babydrache,
  // umgefärbt — blau mit silbernem Bauch spuckt Eis, silbern mit blauer Mähne Blitze.
  { wert: "eisdrache", name: "Kleiner Eisdrache", fuer: "critter" },
  { wert: "blitzdrache", name: "Kleiner Blitzdrache", fuer: "critter" },
  { wert: "baerbel", name: "Bärbel (fliegendes Buch)", fuer: "gegenstand" },
] as const;
export type PetArt = (typeof PET_ARTEN)[number]["wert"];

/** Was ein Drache beim Niesen spuckt — gleiche Figur, anderer Atem (feuer.png je Art). */
export type Atem = "feuer" | "eis" | "blitz";
const ATEM: Record<string, Atem> = { drache: "feuer", eisdrache: "eis", blitzdrache: "blitz" };

/** Alle Drachen-Varianten verhalten sich gleich (Wolkenlauf, Ruß, Schleim, Bärbels Ziel). */
export function istDrache(art: string): boolean {
  return art in ATEM;
}

export function atemVon(art: string): Atem {
  return ATEM[art] ?? "feuer";
}

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
  /** Ungelesene Bibelstelle — sie bleibt groß, bis jemand antippt. */
  lesung?: Lesung | null;
  /** Bärbel hat eine Bibelstelle, ist aber nicht beim Besitzer: bald heimfliegen
   *  (Mark, 12.11.2026: Bibelverse nur beim Besitzer). */
  heim?: boolean;
  /** Wachstum der Drachen (Mark, 12.11.2026): Ei → Baby → jung. */
  stufe?: "ei" | "baby" | "jung";
  /** Freigeschaltete Fähigkeiten (klettern, niesen, springen, wolken, menue). */
  kann?: string[];
  /** Risse im Ei, 0–4. */
  risse?: number;
}

export interface Lesung {
  stelle: string;
  /** Der Vers (gern leicht umformuliert), steht im aufgeschlagenen Buch. */
  zitat: string;
}

export interface Haeufchen {
  id: string;
  petId: string;
  /** Anteile 0..1 der Bildschirmbreite/-höhe. */
  x: number;
  y: number;
  /** Häufchen (antippen), Brandfleck vom Feuerniesen/Blitz (wegwischen),
   *  Raureif vom Eisdrachen (wegwischen),
   *  Bärbels verlorene Seite (antippen = aufheben) oder Schleim vom
   *  Tentakelmonster (wegwischen). Napf: Futternapf, bis ein Drache ihn leer frisst. */
  art?: "haeufchen" | "brand" | "seite" | "schleim" | "frost" | "napf";
}

export type PetNachricht =
  | { typ: "pets"; daten: PetAufSchirm[] }
  | { typ: "haeufchen"; daten: Haeufchen[] }
  | { typ: "vorlesen"; petId: string; stelle: string; zitat: string };

export const petsApi = {
  /** `critterId` kann auch die id eines Gegenstands sein (Bärbel). */
  artLesen: (cid: string, critterId: string) =>
    api.get<{ id: string; art: PetArt | null }>(`/api/campaigns/${cid}/pets/${critterId}`),
  artSetzen: (cid: string, critterId: string, art: PetArt | null) =>
    api.put<{ id: string; art: PetArt | null }>(`/api/campaigns/${cid}/pets/${critterId}`, { art }),
  /** Tierfutter verfüttern (12.11.2026): ein Stück weg, ein Napf auf den eigenen Bildschirm. */
  fuettern: (cid: string, itemId: string) =>
    api.post<{ text: string }>(`/api/campaigns/${cid}/pets/fuettern/${itemId}`, {}),
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
