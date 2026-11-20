import { api } from "../api/client";

export interface SpielerMe {
  spielerId: string;
  benutzername: string;
  campaignId: string;
  campaignName: string;
  /** Ohne zugeordneten Charakter kann der Spieler nur wenig sehen. */
  personId: string | null;
  personName: string | null;
  hatPasswort: boolean;
  /** Portrait des eigenen Charakters — siehe playersApi.meinBildHochladen. */
  personBildUrl?: string | null;
  /** Galerie: alle hochgeladenen Bilder, eines davon ist das Anzeigebild. */
  personBilder?: PortraitBild[];
}

/** Ein Bild in der Charakterportrait-Galerie. */
export interface PortraitBild {
  url: string;
  istPrimaer: boolean;
}

/** Sicht der Spielleitung auf einen Zugang. */
export interface SpielerZugang {
  id: string;
  benutzername: string;
  hatPasswort: boolean;
  personId: string | null;
  personName: string | null;
}

/** Ein vorgebauter PC zur Auswahl im Ersteinstiegs-Fenster — schlanke Form,
 * kein voller Bogen. Spaltensummen für den Steckbrief vor der Übernahme. */
export interface SpaltenSumme {
  koerperlich: number;
  gesellschaftlich: number;
  geistig: number;
}

export interface VorgefertigterCharakter {
  id: string;
  name: string;
  bildUrl?: string;
  konzept?: string;
  rasse?: string;
  weg?: string;
  /** Nur Anzeige. Häretiker bleiben mechanisch Magier. */
  magieFlavor?: "MAGIER" | "HAERETIKER";
  ambition?: string;
  verlangen?: string;
  ziel?: string;
  attribute?: SpaltenSumme;
  fertigkeiten?: SpaltenSumme;
  sphaeren?: number;
  neuroweaving?: number;
  vorgefertigtSignifikanz?: "normal" | "hervorheben" | "wichtig";
}

export const playersApi = {
  anmelden: (benutzername: string, passwort: string) =>
    api.post<SpielerMe>("/api/spieler/login", { benutzername, passwort }),
  me: () => api.get<SpielerMe>("/api/spieler/me"),
  abmelden: () => api.post("/api/spieler/abmelden"),
  /** Vorgebaute PCs, die noch niemandem zugeordnet sind (Ersteinstieg). */
  vorgefertigteListe: () => api.get<VorgefertigterCharakter[]>("/api/spieler/vorgefertigte"),
  /** Wählt einen vorgebauten, noch freien PC dauerhaft — atomar serverseitig geprüft. */
  charakterWaehlen: (personId: string) =>
    api.post<SpielerMe>("/api/spieler/charakter-waehlen", { personId }),
  /** Legt einen frischen PC an und startet damit die eigene Charaktererstellung. */
  charakterNeu: () => api.post<SpielerMe>("/api/spieler/charakter-neu"),
  /** Leeres Passwort entfernt den Schutz wieder. */
  passwortSetzen: (passwort: string) => api.post<SpielerMe>("/api/spieler/passwort", { passwort }),
  /** Charakterportrait für den eigenen zugeordneten Charakter setzen. */
  meinBildHochladen: async (datei: File): Promise<SpielerMe> => {
    const daten = new FormData();
    daten.append("file", datei);
    // Content-Type nicht setzen: der Browser braucht die multipart-Grenze
    // (gleiches Muster wie EntitaetsBild.tsx).
    const antwort = await fetch("/api/spieler/mein-bild", {
      method: "POST",
      credentials: "include",
      body: daten,
    });
    if (!antwort.ok) {
      const f = await antwort.json().catch(() => ({ detail: antwort.statusText }));
      throw new Error(f.detail ?? "Upload fehlgeschlagen");
    }
    return antwort.json();
  },
  /** Entfernt ein Bild aus der eigenen Galerie — ohne URL das aktuelle Anzeigebild. */
  meinBildEntfernen: (url?: string) =>
    api.delete<SpielerMe>(`/api/spieler/mein-bild${url ? `?url=${encodeURIComponent(url)}` : ""}`),
  /** Wählt ein schon hochgeladenes Galerie-Bild als Anzeigebild. */
  meinBildAnzeigeWaehlen: (url: string) => api.post<SpielerMe>("/api/spieler/mein-bild-anzeige", { url }),
  /** Schritt 1 des KI-Bild-Popups: Prompt-Vorschlag fürs eigene Portrait. */
  meinBildKiPrompt: async (): Promise<string> => {
    const antwort = await api.post<{ prompt: string }>("/api/spieler/mein-bild-ki-prompt");
    return antwort.prompt;
  },
  /** Schritt 2: generiert eine Bildvorschau — speichert NICHTS, siehe
   * KiBildPopup.tsx. Übernehmen läuft über meinBildHochladen oben.
   *
   * Läuft als Hintergrund-Job + Polling (20.11.2026, Marks Bugreport
   * "Failed to fetch"), derselbe Grund und dasselbe Muster wie
   * ki/api.ts::kiBildGenerieren. */
  meinBildKiGenerieren: async (provider: "lokal" | "cloud", prompt: string): Promise<{ blob: Blob; referenz: string | null }> => {
    const gestartet = await api.post<{ jobId: string }>("/api/spieler/mein-bild-ki", { provider, prompt });

    let fehlgeschlageneVersuche = 0;
    for (;;) {
      await new Promise((r) => setTimeout(r, 1500));
      let stand: {
        fertig: boolean;
        bildBase64?: string | null;
        contentType?: string | null;
        referenz?: string | null;
        fehler?: string | null;
      };
      try {
        stand = await api.get(`/api/spieler/mein-bild-ki-status/${gestartet.jobId}`);
      } catch (e) {
        fehlgeschlageneVersuche += 1;
        if (fehlgeschlageneVersuche > 10) throw e;
        continue;
      }
      fehlgeschlageneVersuche = 0;
      if (!stand.fertig) continue;
      if (!stand.bildBase64 || !stand.contentType) {
        throw new Error("Bildgenerierung lieferte kein Ergebnis");
      }
      const bin = atob(stand.bildBase64);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return { blob: new Blob([bytes], { type: stand.contentType }), referenz: stand.referenz ?? null };
    }
  },
  meinBildInPool: async (blob: Blob) => {
    const formData = new FormData();
    formData.append("file", new File([blob], "portrait-ki.png", { type: blob.type || "image/png" }));
    const antwort = await fetch("/api/spieler/mein-bild-rassenpool", {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!antwort.ok) {
      const f = await antwort.json().catch(() => ({ detail: antwort.statusText }));
      throw new Error(f.detail ?? "Rassen-Pool nicht aktualisiert");
    }
  },

  // Verwaltung durch die Spielleitung
  liste: (cid: string) => api.get<SpielerZugang[]>(`/api/campaigns/${cid}/spieler`),
  anlegen: (cid: string, benutzername: string, personId: string | null) =>
    api.post<SpielerZugang>(`/api/campaigns/${cid}/spieler`, { benutzername, personId, passwort: "" }),
  charakterZuordnen: (cid: string, spielerId: string, personId: string | null) =>
    api.post<SpielerZugang[]>(`/api/campaigns/${cid}/spieler/${spielerId}/charakter`, { personId }),
  entfernen: (cid: string, spielerId: string) => api.delete<void>(`/api/campaigns/${cid}/spieler/${spielerId}`),
};
