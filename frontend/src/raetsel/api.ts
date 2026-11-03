import { api } from "../api/client";

export type Seite = "N" | "O" | "S" | "W";
export type Modus = "leicht" | "mittel";

export type RaetselTafel = {
  modus: Modus;
  drehung: number;
  takt: number;
  naechster: "ebene" | "drehen";
  ringe: number[][];
  ausgaenge: number[][];
  namen: string[];
  gruppen: (number | null)[];
  offen: boolean[];
  tuer: { raum: number; seite: Seite } | null;
  freigegeben: boolean;
  kannZurueck: boolean;
};

export type RaetselAntwort = RaetselTafel | { freigegeben: false };

export function hatTafel(stand: RaetselAntwort): stand is RaetselTafel {
  return "namen" in stand;
}

const basis = (campaignId: string) => `/api/campaigns/${campaignId}/raetsel`;

export const raetselApi = {
  laden(campaignId: string, alsGm: boolean) {
    const pfad = basis(campaignId);
    return alsGm ? api.getAsGm<RaetselAntwort>(pfad) : api.get<RaetselAntwort>(pfad);
  },
  tuer: (campaignId: string, raum: number, seite: Seite) =>
    api.post<RaetselTafel>(`${basis(campaignId)}/tuer`, { raum, seite }),
  gruppe: (campaignId: string, index: number, raum: number | null) =>
    api.post<RaetselTafel>(`${basis(campaignId)}/gruppe`, { index, raum }),
  name: (campaignId: string, raum: number, name: string) =>
    api.post<RaetselTafel>(`${basis(campaignId)}/name`, { raum, name }),
  freigabe: (campaignId: string, an: boolean) =>
    api.post<RaetselTafel>(`${basis(campaignId)}/freigabe`, { an }),
  ausgang: (campaignId: string, ring: number, slot: number) =>
    api.post<RaetselTafel>(`${basis(campaignId)}/ausgang`, { ring, slot }),
  modus: (campaignId: string, modus: Modus) =>
    api.post<RaetselTafel>(`${basis(campaignId)}/modus`, { modus }),
  zurueck: (campaignId: string) => api.post<RaetselTafel>(`${basis(campaignId)}/zurueck`),
  zuruecksetzen: (campaignId: string) =>
    api.post<RaetselTafel>(`${basis(campaignId)}/zuruecksetzen`),
};

export type RaetselLeitung = { trennen: () => void };

/** Live-Stand. Klicks gehen über REST, die Leitung nur zum Zuschauen und Mitlesen. */
export function verbindeRaetselLive(
  campaignId: string,
  onStand: (stand: RaetselAntwort) => void,
  onStatus?: (verbunden: boolean) => void,
): RaetselLeitung {
  let socket: WebSocket | null = null;
  let versuch = 0;
  let zu = false;
  let timer: number | undefined;

  const verbinde = () => {
    if (zu) return;
    const schema = window.location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${schema}//${window.location.host}/api/campaigns/${campaignId}/raetsel/live`);
    socket.onopen = () => {
      versuch = 0;
      onStatus?.(true);
    };
    socket.onmessage = (ev) => {
      try {
        const nachricht = JSON.parse(ev.data) as { typ?: string; daten?: RaetselAntwort };
        if (nachricht.typ === "stand" && nachricht.daten) onStand(nachricht.daten);
      } catch {
        // Kaputte Nachricht ignorieren.
      }
    };
    socket.onclose = () => {
      onStatus?.(false);
      if (zu) return;
      versuch += 1;
      const wartezeit = Math.min(1000 * 2 ** (versuch - 1), 15000);
      timer = window.setTimeout(verbinde, wartezeit);
    };
  };

  verbinde();
  return {
    trennen: () => {
      zu = true;
      window.clearTimeout(timer);
      socket?.close();
    },
  };
}
