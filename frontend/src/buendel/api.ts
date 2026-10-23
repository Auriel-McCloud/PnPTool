/** API-Zugriff für den Kampagnen-Bündel-Export (Phase 1: nur Export).
 *
 * Siehe backend/app/campaigns/buendel_export.py für Sammel-/Weisslisten-
 * Begründung und das Manifest-Format.
 */
export interface BuendelExportRequest {
  name: string;
  beschreibung: string;
  tags: string[];
  /** Alles AUSSER diesen IDs wird exportiert (invertierter Picker, Marks
   * bewusste Entscheidung — siehe BuendelAnsicht.tsx). */
  ausgeschlosseneIds: string[];
}

function basis(cid: string) {
  return `/api/campaigns/${cid}/buendel`;
}

function dateinameAusHeader(header: string | null): string | null {
  if (!header) return null;
  const treffer = /filename="?([^"]+)"?/.exec(header);
  return treffer ? treffer[1] : null;
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
    if (!response.ok) {
      const fehler = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(fehler.detail ?? "Export fehlgeschlagen");
    }
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
};
