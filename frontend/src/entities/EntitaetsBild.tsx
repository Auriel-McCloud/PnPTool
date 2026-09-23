import { useRef, useState } from "react";
import { BildBlitz } from "../mitteilungen/BildBlitz";
import { KiBildPopup } from "../ki/KiBildPopup";
import { kiBildGenerieren, kiBildPrompt } from "../ki/api";
import { extrahiereReinenText } from "../richtext/content";

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
  beschreibung,
  onGeaendert,
}: {
  campaignId: string;
  /** Pfadsegment der API: personen | orte | events */
  art: "personen" | "orte" | "events";
  id: string;
  name: string;
  bildUrl: string;
  /** Roher description-Text der Entität — Grundlage für den KI-Bild-Prompt-
   * Vorschlag. Optional: ohne sie schlägt die KI nur aus dem Namen vor. */
  beschreibung?: string;
  onGeaendert: () => void;
}) {
  const [laedt, setLaedt] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [kiOffen, setKiOffen] = useState(false);
  const dateiRef = useRef<HTMLInputElement>(null);

  // Für den KI-Bild-Prompt: welcher Objekttyp das für die KI ist (Deutsch,
  // geht 1:1 in den Prompt-Vorschlag-Aufruf).
  const objektTyp = art === "personen" ? "Person" : art === "orte" ? "Ort" : "Event";

  async function hochladenAnFormData(datei: File | Blob, dateiname: string) {
    setLaedt(true);
    setFehler(null);
    try {
      const daten = new FormData();
      daten.append("file", datei, dateiname);
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
      throw e;
    } finally {
      setLaedt(false);
    }
  }

  async function hochladen(datei: File | undefined) {
    if (!datei) return;
    try {
      await hochladenAnFormData(datei, datei.name);
    } finally {
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

      <button
        type="button"
        onClick={() => setKiOffen(true)}
        disabled={laedt}
        style={{ minHeight: 0, padding: "4px 10px", fontSize: 12, color: "var(--p-violett, var(--neon))" }}
      >
        ✨ KI-Bild
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

      <KiBildPopup
        offen={kiOffen}
        objektTyp={objektTyp}
        objektName={name}
        onSchliessen={() => setKiOffen(false)}
        onPromptVorschlagen={() =>
          kiBildPrompt(campaignId, {
            objektTyp,
            objektName: name,
            bisherigeBeschreibung: beschreibung ? extrahiereReinenText(beschreibung) : "",
          })
        }
        onGenerieren={(provider, prompt) => kiBildGenerieren(campaignId, provider, prompt)}
        onUebernehmen={(blob) => hochladenAnFormData(blob, "ki-bild.png")}
      />
    </div>
  );
}
