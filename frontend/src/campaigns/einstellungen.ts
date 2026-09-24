import { api } from "../api/client";

/**
 * Kampagnenweite Spieleinstellungen.
 *
 * Bewusst offen typisiert: die Sammlung soll wachsen können, ohne dass hier
 * jedes Mal ein Feld nachgetragen werden muss (siehe
 * backend/app/campaigns/repository.py, EINSTELLUNGEN_DEFAULTS).
 */
export interface Einstellungen {
  /** Zeigt Gewicht und Auslastung an — rein informativ, verhindert nichts. */
  gewichtAktiv: boolean;
  /** Attribut, aus dem sich die Traglast einer Person ergibt. */
  traglastAttribut: string;
  /** Kilogramm je Attributpunkt. */
  traglastProPunkt: number;
  /** Würfeln die Spieler im Tool statt am Tisch? */
  digitalesWuerfeln: boolean;
  /** Die SL würfelt die Initiative ihrer NPCs automatisch. */
  digitalesWuerfelnSL: boolean;
  /** Der In-World-Messenger ist eine optionale Kampagnenfunktion. */
  messengerAktiv: boolean;
  /** Kampagnenweite EP — alle PCs bekommen gemeinsam EP. */
  kampagnenEP: number;
  [weitere: string]: unknown;
}

export const einstellungenApi = {
  lesen: (cid: string) => api.get<Einstellungen>(`/api/campaigns/${cid}/einstellungen`),
  aendern: (cid: string, aenderungen: Partial<Einstellungen>) =>
    api.patch<Einstellungen>(`/api/campaigns/${cid}/einstellungen`, aenderungen),
  /** Erhöht die kampagnenweiten EP um einen Betrag (nur positiv, irreversibel). */
  epErhoehen: (cid: string, betrag: number) =>
    api.post<Einstellungen>(`/api/campaigns/${cid}/einstellungen/ep-erhoehen`, { betrag }),
};

/** Export/Import einer kompletten Kampagne als ZIP-Datei (siehe
 * backend/app/campaigns/export_import.py und docs/api/campaigns-export-import.md). */
export const kampagnenExportApi = {
  /** Löst den Download über einen unsichtbaren Anker aus — Cookie-Auth
   * läuft bei einem normalen `<a href>`-Klick automatisch mit, ein
   * `fetch()`-Umweg über Blob wäre hier unnötig komplex. */
  exportieren(cid: string, campaignName: string) {
    const a = document.createElement("a");
    a.href = `/api/campaigns/${cid}/export`;
    a.download = `${campaignName || "kampagne"}.zip`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  },
  /** Multipart-Upload der ZIP-Datei; legt serverseitig eine neue Kampagne an. */
  async importieren(datei: File): Promise<{ id: string; name: string }> {
    const form = new FormData();
    form.append("datei", datei);
    const response = await fetch("/api/campaigns/import", {
      method: "POST",
      credentials: "include",
      body: form,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(body.detail ?? "Import fehlgeschlagen");
    }
    return response.json();
  },
};

/** "2,5 / 30 kg" — kompakt und ohne unnötige Nachkommastellen. */
export function formatiereLast(last: number, kapazitaet: number): string {
  const z = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1).replace(".", ","));
  return kapazitaet > 0 ? `${z(last)} / ${z(kapazitaet)} kg` : `${z(last)} kg`;
}
