import { useRef, useState } from "react";
import { BildBlitz } from "../mitteilungen/BildBlitz";

/**
 * Bild einer Entität: anzeigen, hochladen, entfernen — und per Blitz allen
 * Spielern zeigen.
 *
 * Marks Wunsch: "ich würde auch gerne von einem NPC aus ein Bild an alle
 * schicken können, also wie der NPC aussieht". Der Blitz sitzt deshalb
 * direkt am Bild statt in einem eigenen Menü.
 */
export function EntitaetsBild({
  campaignId,
  art,
  id,
  name,
  bildUrl,
  onGeaendert,
}: {
  campaignId: string;
  /** Pfadsegment der API: personen | orte | events */
  art: "personen" | "orte" | "events";
  id: string;
  name: string;
  bildUrl: string;
  onGeaendert: () => void;
}) {
  const [laedt, setLaedt] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const dateiRef = useRef<HTMLInputElement>(null);

  async function hochladen(datei: File | undefined) {
    if (!datei) return;
    setLaedt(true);
    setFehler(null);
    try {
      const daten = new FormData();
      daten.append("file", datei);
      // Content-Type nicht setzen: der Browser braucht die multipart-Grenze.
      const antwort = await fetch(`/api/campaigns/${campaignId}/${art}/${id}/bild`, {
        method: "POST",
        credentials: "include",
        body: daten,
      });
      if (!antwort.ok) {
        const f = await antwort.json().catch(() => ({ detail: antwort.statusText }));
        throw new Error(f.detail ?? "Upload fehlgeschlagen");
      }
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Upload fehlgeschlagen");
    } finally {
      setLaedt(false);
      if (dateiRef.current) dateiRef.current.value = "";
    }
  }

  async function entfernen() {
    setLaedt(true);
    try {
      await fetch(`/api/campaigns/${campaignId}/${art}/${id}`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bildUrl: "" }),
      });
      onGeaendert();
    } finally {
      setLaedt(false);
    }
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, margin: "6px 0", flexWrap: "wrap" }}>
      {bildUrl && (
        <img
          src={bildUrl}
          alt={name}
          style={{
            width: 56,
            height: 56,
            objectFit: "cover",
            borderRadius: "var(--radius)",
            border: "1px solid var(--linie)",
          }}
        />
      )}

      <input
        ref={dateiRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        style={{ display: "none" }}
        onChange={(e) => hochladen(e.target.files?.[0])}
      />

      <button
        type="button"
        onClick={() => dateiRef.current?.click()}
        disabled={laedt}
        style={{ minHeight: 0, padding: "4px 10px", fontSize: 12 }}
      >
        {laedt ? "lädt…" : bildUrl ? "Bild tauschen" : "▣ Bild"}
      </button>

      {bildUrl && (
        <>
          <BildBlitz campaignId={campaignId} bildUrl={bildUrl} name={name} klein />
          <button
            type="button"
            onClick={entfernen}
            disabled={laedt}
            style={{ minHeight: 0, padding: "4px 8px", fontSize: 12, color: "var(--signal)" }}
            title="Bild entfernen"
          >
            ✕
          </button>
        </>
      )}

      {fehler && <span style={{ color: "var(--signal)", fontSize: 12 }}>{fehler}</span>}
    </div>
  );
}
