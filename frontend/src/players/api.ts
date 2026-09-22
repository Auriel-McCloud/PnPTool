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
}

/** Sicht der Spielleitung auf einen Zugang. */
export interface SpielerZugang {
  id: string;
  benutzername: string;
  hatPasswort: boolean;
  personId: string | null;
  personName: string | null;
}

export const playersApi = {
  anmelden: (benutzername: string, passwort: string) =>
    api.post<SpielerMe>("/api/spieler/login", { benutzername, passwort }),
  me: () => api.get<SpielerMe>("/api/spieler/me"),
  abmelden: () => api.post("/api/spieler/abmelden"),
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

  // Verwaltung durch die Spielleitung
  liste: (cid: string) => api.get<SpielerZugang[]>(`/api/campaigns/${cid}/spieler`),
  anlegen: (cid: string, benutzername: string, personId: string | null) =>
    api.post<SpielerZugang>(`/api/campaigns/${cid}/spieler`, { benutzername, personId, passwort: "" }),
  charakterZuordnen: (cid: string, spielerId: string, personId: string | null) =>
    api.post<SpielerZugang[]>(`/api/campaigns/${cid}/spieler/${spielerId}/charakter`, { personId }),
  entfernen: (cid: string, spielerId: string) => api.delete<void>(`/api/campaigns/${cid}/spieler/${spielerId}`),
};
