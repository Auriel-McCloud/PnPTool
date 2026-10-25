/** Whiteboard: mehrere speicherbare Zeichnungen pro Kampagne, live mitzeichenbar. */
import { api } from "../api/client";
import type { SichtbarkeitModus } from "../entities/api";

/** Ein einzelner Strich aus react-sketch-canvas (Format wird nicht geprüft,
 * nur durchgereicht — siehe backend/app/zeichnungen/repository.py). */
export type Pfad = Record<string, unknown>;

export interface Zeichnung {
  id: string;
  name: string;
  pfade: Pfad[];
  bildUrl: string;
  spielerDuerfenZeichnen: boolean;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
  geloescht: boolean;
  erstelltAm: string;
}

const basis = (campaignId: string) => `/api/campaigns/${campaignId}/zeichnungen`;

export const zeichnungenApi = {
  liste: (campaignId: string) => api.get<Zeichnung[]>(basis(campaignId)),

  papierkorb: (campaignId: string) => api.get<Zeichnung[]>(`${basis(campaignId)}/papierkorb`),

  holen: (campaignId: string, id: string) => api.get<Zeichnung>(`${basis(campaignId)}/${id}`),

  anlegen: (campaignId: string, name: string) =>
    api.post<Zeichnung>(basis(campaignId), { name }),

  aktualisieren: (
    campaignId: string,
    id: string,
    body: Partial<Pick<Zeichnung, "name" | "bildUrl" | "spielerDuerfenZeichnen" | "sichtbarkeit" | "sichtbarFuer">>,
  ) => api.patch<Zeichnung>(`${basis(campaignId)}/${id}`, body),

  pfadeSpeichern: (campaignId: string, id: string, pfade: Pfad[]) =>
    api.patch<Zeichnung>(`${basis(campaignId)}/${id}/pfade`, { pfade }),

  geloeschtSetzen: (campaignId: string, id: string, geloescht: boolean) =>
    api.put<Zeichnung>(`${basis(campaignId)}/${id}/geloescht`, { geloescht }),

  /** Hintergrundbild hochladen (z.B. eine Karte). FormData, an api() vorbei —
   *  Content-Type NICHT setzen, der Browser braucht die multipart-Grenze. */
  async bildHochladen(campaignId: string, id: string, datei: File): Promise<Zeichnung> {
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

/** Was über die Live-Leitung eines einzelnen Boards reinkommt. */
export type ZeichnungLiveNachricht = { typ: "pfade"; daten: { pfade: Pfad[] } };

export interface ZeichnungLeitung {
  /** Striche über die Leitung schicken — der Server speichert und verteilt
   *  an alle anderen offenen Betrachter dieses Boards. Still, solange keine
   *  Verbindung steht (z.B. gerade am Wiederverbinden). */
  senden: (pfade: Pfad[]) => void;
  trennen: () => void;
}

/**
 * Öffnet die Live-Leitung für EIN Board und verbindet bei Abbruch neu.
 *
 * Gleiches Wiederverbinde-Muster wie mitteilungen/api.ts::verbindeLive
 * (wachsende Wartezeit 1s…15s) — wichtig fürs Tablet, das Hintergrund-Tabs
 * einschläfert und dabei die Verbindung kappt.
 */
export function verbindeZeichnungLive(
  campaignId: string,
  zeichnungId: string,
  onNachricht: (n: ZeichnungLiveNachricht) => void,
  onStatus?: (verbunden: boolean) => void,
): ZeichnungLeitung {
  let socket: WebSocket | null = null;
  let versuch = 0;
  let zu = false;
  let timer: number | undefined;

  const verbinde = () => {
    if (zu) return;
    const schema = window.location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(
      `${schema}//${window.location.host}/api/campaigns/${campaignId}/zeichnungen/${zeichnungId}/live`,
    );

    socket.onopen = () => {
      versuch = 0;
      onStatus?.(true);
    };

    socket.onmessage = (ev) => {
      try {
        onNachricht(JSON.parse(ev.data) as ZeichnungLiveNachricht);
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

  return {
    senden: (pfade: Pfad[]) => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ pfade }));
      }
    },
    trennen: () => {
      zu = true;
      window.clearTimeout(timer);
      socket?.close();
    },
  };
}
