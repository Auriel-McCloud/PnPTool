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
  /** Rassen-Features (10.10.2026, budget-neutral — siehe
   * backend/app/rassen/schemas.py). */
  bonusFreebees: number;
  gratisGegenstandId: string;
  gratisErsterKaufTyp: string;
  gratisZusatzfertigkeitId: string;
  gratisFertigkeitName: string;
  gratisFertigkeitBonus: number;
  featureHinweis: string;
  kannKredithai: boolean;
  istGross: boolean;
  rundumsicht: boolean;
  referenzAktiv: boolean;
  referenzbilder: string[];
  /** Erlaubte Wege bei der Erstellung. Leer = alle (20.11.2026). */
  erlaubteWege: string[];
}

export interface RasseEingabe {
  name?: string;
  beschreibung?: string;
  modifikatoren?: Record<string, number>;
  freiePunkte?: number[];
  sortOrder?: number;
  bonusFreebees?: number;
  gratisGegenstandId?: string;
  gratisErsterKaufTyp?: string;
  gratisZusatzfertigkeitId?: string;
  gratisFertigkeitName?: string;
  gratisFertigkeitBonus?: number;
  featureHinweis?: string;
  kannKredithai?: boolean;
  istGross?: boolean;
  rundumsicht?: boolean;
  referenzAktiv?: boolean;
  erlaubteWege?: string[];
}

/** Die vier Wege der Erstellung — Kennungen wie backend/app/traits/erstellung.py::WEGE.
 * Nur für die Häkchen an der Rasse; die Erstellung selbst liest die Namen vom Server. */
export const WEGE_AUSWAHL: { id: string; name: string }[] = [
  { id: "KEINER", name: "Weg des Chroms" },
  { id: "MAGIER", name: "Magier" },
  { id: "HAERETIKER", name: "Häretiker" },
  { id: "NEUROWEAVER", name: "NeuroWeaver" },
];

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
  referenzHochladen: async (cid: string, id: string, datei: File) => {
    const formData = new FormData();
    formData.append("file", datei);
    const antwort = await fetch(`${basis(cid)}/${id}/referenzen`, {
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
  referenzEntfernen: (cid: string, id: string, url: string) =>
    api.delete<Rasse>(`${basis(cid)}/${id}/referenzen?url=${encodeURIComponent(url)}`),
  /** Übernommenes KI-Portrait in den Pool, wenn der Schalter an ist. */
  uebernommenesPortrait: async (cid: string, personId: string, blob: Blob) => {
    const formData = new FormData();
    formData.append("personId", personId);
    formData.append("file", new File([blob], "ki-bild.png", { type: blob.type || "image/png" }));
    const antwort = await fetch(`${basis(cid)}/uebernommen`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!antwort.ok) {
      const koerper = await antwort.json().catch(() => ({ detail: antwort.statusText }));
      throw new ApiError(antwort.status, koerper.detail ?? "Pool nicht aktualisiert");
    }
    return (await antwort.json()) as { abgelegt: boolean };
  },
};
