import { api, ApiError } from "../api/client";

/**
 * Rassen: Katalog global, Freigabe je Kampagne.
 *
 * Die Bewertung (`bilanz`) kommt **fertig gerechnet vom Server**
 * (backend/app/rassen/balance.py) — der Editor zeigt sie nur an. Würde er sie
 * nachrechnen, liefe die Anzeige irgendwann mit dem auseinander, was beim
 * Speichern gilt.
 */
export interface Bilanz {
  punkte: number;
  vorteile: number;
  nachteile: number;
  summe: number;
  budget: number;
  nachteileSoll: number;
  /** Liegt die Rasse im Rahmen? Verhindert nichts — der Editor warnt nur. */
  stimmt: boolean;
  hinweise: string[];
}

export interface Rasse {
  id: string;
  name: string;
  beschreibung: string;
  bildUrl: string;
  /** Attributname -> Modifikator, positiv wie negativ. */
  modifikatoren: Record<string, number>;
  /** Die drei Kontingente, frei auf die Attributspalten verteilbar. */
  freiePunkte: number[];
  sortOrder: number;
  bilanz: Bilanz;
  /** Nur im Katalog gefüllt: in dieser Kampagne wählbar? */
  freigegeben: boolean;
}

export interface RasseEingabe {
  name?: string;
  beschreibung?: string;
  modifikatoren?: Record<string, number>;
  freiePunkte?: number[];
  sortOrder?: number;
}

function basis(cid: string) {
  return `/api/campaigns/${cid}/rassen`;
}

export const rassenApi = {
  /** Die in dieser Kampagne wählbaren Rassen — auch für Spieler lesbar. */
  verfuegbar: (cid: string) => api.get<Rasse[]>(basis(cid)),
  /** Alle Rassen des Regelwerks mit Freigabe-Häkchen. Nur SL. */
  katalog: (cid: string) => api.get<Rasse[]>(`${basis(cid)}/katalog`),
  anlegen: (cid: string, body: RasseEingabe & { name: string }) => api.post<Rasse>(basis(cid), body),
  aendern: (cid: string, id: string, body: RasseEingabe) => api.patch<Rasse>(`${basis(cid)}/${id}`, body),
  loeschen: (cid: string, id: string) => api.delete<void>(`${basis(cid)}/${id}`),
  /** Immer die vollständige Auswahl schicken, nicht einzelne Häkchen. */
  freigabe: (cid: string, rasseIds: string[]) => api.put<string[]>(`${basis(cid)}/freigabe`, { rasseIds }),
  bildHochladen: async (cid: string, id: string, datei: File) => {
    const formData = new FormData();
    formData.append("file", datei);
    const antwort = await fetch(`${basis(cid)}/${id}/bild`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!antwort.ok) {
      const koerper = await antwort.json().catch(() => ({ detail: antwort.statusText }));
      throw new ApiError(antwort.status, koerper.detail ?? "Upload fehlgeschlagen");
    }
    return (await antwort.json()) as Rasse;
  },
};
