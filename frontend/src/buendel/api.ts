/** API-Zugriff für das Kampagnen-Bündel: Export (Phase 1) + Import (Phase 2).
 *
 * Siehe backend/app/campaigns/buendel_export.py / buendel_import.py für
 * Sammel-/Abgleich-/Weisslisten-Begründung und das Manifest-Format.
 */
export interface BuendelExportRequest {
  name: string;
  beschreibung: string;
  tags: string[];
  /** Alles AUSSER diesen IDs wird exportiert (invertierter Picker, Marks
   * bewusste Entscheidung — siehe BuendelAnsicht.tsx). */
  ausgeschlosseneIds: string[];
}

/** Modus für bereits in der Zielkampagne vorhandene Entitäten (per
 * stammtVonId erkannt) — gilt für den gesamten Import-Lauf, nicht pro Objekt. */
export type BuendelImportModus = "ueberspringen" | "aktualisieren";

export interface BuendelImportZaehler {
  neu: number;
  aktualisiert: number;
  uebersprungen: number;
}

export interface BuendelImportResponse extends BuendelImportZaehler {
  proTyp: Record<string, BuendelImportZaehler>;
  bundleName: string;
  herkunftCampaignName: string;
}

export interface BuendelVorschauResponse {
  bundleName: string;
  beschreibung: string;
  tags: string[];
  herkunftCampaignName: string;
  anzahlKnoten: number;
  proTyp: Record<string, { neu: number; vorhanden: number }>;
}

function basis(cid: string) {
  return `/api/campaigns/${cid}/buendel`;
}

function dateinameAusHeader(header: string | null): string | null {
  if (!header) return null;
  const treffer = /filename="?([^"]+)"?/.exec(header);
  return treffer ? treffer[1] : null;
}

async function fehlerAusAntwort(antwort: Response, fallback: string): Promise<Error> {
  const koerper = await antwort.json().catch(() => ({ detail: antwort.statusText }));
  return new Error(koerper.detail ?? fallback);
}

export const buendelApi = {
  /**
   * Löst den ZIP-Download aus. Bewusst ein echter `fetch()`-Umweg über Blob
   * statt des unsichtbaren-Anker-Tricks (wie bei
   * `campaigns/einstellungen.ts::kampagnenExportApi.exportieren`) — der
   * Export braucht hier eine Auswahl (Ausschlussliste + Metadaten) im
   * Body, ein `<a href>` kann keinen POST-Body mitschicken.
   */
  async exportieren(cid: string, body: BuendelExportRequest): Promise<void> {
    const response = await fetch(`${basis(cid)}/export`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw await fehlerAusAntwort(response, "Export fehlgeschlagen");
    const blob = await response.blob();
    const dateiname = dateinameAusHeader(response.headers.get("Content-Disposition")) ?? `${body.name || "buendel"}.zip`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = dateiname;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },

  /** Liest ein Bündel-ZIP vorab, OHNE etwas zu importieren — zeigt der SL,
   * was drin ist und was in dieser Kampagne schon existiert. Optional, der
   * eigentliche Import funktioniert auch ohne vorherigen Aufruf. */
  async vorschau(cid: string, datei: File): Promise<BuendelVorschauResponse> {
    const formData = new FormData();
    formData.append("datei", datei);
    const response = await fetch(`${basis(cid)}/import/vorschau`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!response.ok) throw await fehlerAusAntwort(response, "Vorschau fehlgeschlagen");
    return response.json();
  },

  /** Importiert ein Bündel-ZIP in DIESE (bestehende) Kampagne. */
  async importieren(
    cid: string,
    datei: File,
    modus: BuendelImportModus,
    ideenschmiede: boolean,
  ): Promise<BuendelImportResponse> {
    const formData = new FormData();
    formData.append("datei", datei);
    formData.append("modus", modus);
    formData.append("ideenschmiede", ideenschmiede ? "true" : "false");
    const response = await fetch(`${basis(cid)}/import`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!response.ok) throw await fehlerAusAntwort(response, "Import fehlgeschlagen");
    return response.json();
  },
};
