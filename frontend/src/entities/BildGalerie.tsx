import { useRef, useState } from "react";
import { BildBlitz } from "../mitteilungen/BildBlitz";
import { Bestaetigung } from "../shell/Bestaetigung";
import { KiBildPopup } from "../ki/KiBildPopup";
import { kiBildGenerieren, kiBildPrompt } from "../ki/api";
import { extrahiereReinenText } from "../richtext/content";

/**
 * Bildergalerie für Entitäten: mehrere Bilder anzeigen, hochladen,
 * Primärbild wählen, einzelne entfernen.
 *
 * Backend-Feld: bilder: [{url: string, istPrimaer: boolean}]
 */
export function BildGalerie({
  campaignId,
  art,
  id,
  name,
  beschreibung,
  bilder,
  bildUrl, // Fallback für alte Daten
  onGeaendert,
}: {
  campaignId: string;
  /** Pfadsegment der API: personen | orte | events | fraktionen */
  art: "personen" | "orte" | "events" | "fraktionen";
  id: string;
  name: string;
  /** Roher description-Text der Entität — Grundlage für den KI-Bild-Prompt-
   * Vorschlag. Optional: ohne sie schlägt die KI nur aus dem Namen vor. */
  beschreibung?: string;
  bilder: { url: string; istPrimaer: boolean }[];
  /** Fallback: altes Einzelbild-Feld */
  bildUrl?: string;
  onGeaendert: () => void;
}) {
  const [laedt, setLaedt] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [loeschenOffen, setLoeschenOffen] = useState<string | null>(null); // URL des zu löschenden Bildes
  const [kiOffen, setKiOffen] = useState(false);
  const dateiRef = useRef<HTMLInputElement>(null);

  // Für den KI-Bild-Prompt: welcher Objekttyp das für die KI ist.
  const objektTyp =
    art === "personen" ? "Person" : art === "orte" ? "Ort" : art === "events" ? "Event" : "Fraktion";

  // Migration: Wenn kein bilder-Array aber ein bildUrl existiert, konvertieren
  const effektiveBilder = bilder.length > 0 
    ? bilder 
    : bildUrl 
      ? [{ url: bildUrl, istPrimaer: true }] 
      : [];

  const primaerBild = effektiveBilder.find((b) => b.istPrimaer)?.url || effektiveBilder[0]?.url || "";

  async function hochladenBytes(datei: File | Blob, dateiname: string) {
    setLaedt(true);
    setFehler(null);
    try {
      const daten = new FormData();
      daten.append("file", datei, dateiname);

      // Bild hochladen
      const uploadAntwort = await fetch(`/api/campaigns/${campaignId}/${art}/${id}/bild`, {
        method: "POST",
        credentials: "include",
        body: daten,
      });

      if (!uploadAntwort.ok) {
        const f = await uploadAntwort.json().catch(() => ({ detail: uploadAntwort.statusText }));
        throw new Error(f.detail ?? "Upload fehlgeschlagen");
      }

      // Neue URL aus der Antwort holen
      const uploadDaten = await uploadAntwort.json();
      const neueUrl = uploadDaten.bildUrl;

      // Bilder-Array aktualisieren (mit effektiveBilder für Migration)
      const neueBilder = [...effektiveBilder, { url: neueUrl, istPrimaer: effektiveBilder.length === 0 }];

      // Wenn es das erste Bild ist, auch als bildUrl setzen
      const neuesBildUrl = effektiveBilder.length === 0 ? neueUrl : undefined;

      // PATCH mit neuem bilder-Array
      await fetch(`/api/campaigns/${campaignId}/${art}/${id}`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bilder: neueBilder,
          ...(neuesBildUrl && { bildUrl: neuesBildUrl }),
        }),
      });

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
      await hochladenBytes(datei, datei.name);
    } finally {
      if (dateiRef.current) dateiRef.current.value = "";
    }
  }

  async function primaerSetzen(url: string) {
    const neueBilder = effektiveBilder.map((b) => ({
      ...b,
      istPrimaer: b.url === url,
    }));
    
    // Auch bildUrl aktualisieren (das ist das Anzeigebild in der Übersicht)
    await fetch(`/api/campaigns/${campaignId}/${art}/${id}`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        bilder: neueBilder,
        bildUrl: url, // Anzeigebild in der Übersicht
      }),
    });
    
    onGeaendert();
  }

  async function entfernen(url: string) {
    setLoeschenOffen(url);
  }

  async function entfernenBestaetigt() {
    if (!loeschenOffen) return;
    const url = loeschenOffen;
    setLoeschenOffen(null);
    
    const neueBilder = effektiveBilder.filter((b) => b.url !== url);
    
    // Wenn das Primärbild gelöscht wurde, erstes Bild zum Primär machen
    let neuesPrimaer = "";
    if (neueBilder.length > 0 && !neueBilder.some((b) => b.istPrimaer)) {
      neueBilder[0].istPrimaer = true;
      neuesPrimaer = neueBilder[0].url;
    } else if (neueBilder.length > 0) {
      neuesPrimaer = neueBilder.find((b) => b.istPrimaer)?.url || neueBilder[0].url;
    }
    
    await fetch(`/api/campaigns/${campaignId}/${art}/${id}`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        bilder: neueBilder,
        bildUrl: neuesPrimaer, // Anzeigebild aktualisieren
      }),
    });
    
    onGeaendert();
  }

  return (
    <div className="bild-galerie">
      {/* Hauptbild (Primär) */}
      {primaerBild && (
        <div className="bild-galerie-hauptbild">
          <img src={primaerBild} alt={name} />
          
          {/* Links: Anzeigebild wechseln */}
          {effektiveBilder.length > 1 && (
            <div className="bild-galerie-primaer-wechsel">
              <button
                type="button"
                onClick={() => {
                  // Zum nächsten Bild wechseln
                  const idx = effektiveBilder.findIndex(b => b.istPrimaer);
                  const naechster = effektiveBilder[(idx + 1) % effektiveBilder.length];
                  primaerSetzen(naechster.url);
                }}
                title="Anzeigebild wechseln"
              >
                ⟳
              </button>
            </div>
          )}
          
          {/* Rechts: Blitz */}
          <div className="bild-galerie-aktionen">
            <BildBlitz campaignId={campaignId} bildUrl={primaerBild} name={name} klein />
          </div>
        </div>
      )}

      {/* Thumbnails */}
      <div className="bild-galerie-thumbnails">
        {effektiveBilder.map((bild) => (
          <div
            key={bild.url}
            className={`bild-galerie-thumb ${bild.istPrimaer ? "primaer" : ""}`}
            onClick={() => primaerSetzen(bild.url)}
            title={bild.istPrimaer ? "Primärbild" : "Als Primär setzen"}
          >
            <img src={bild.url} alt="" />
            <button
              className="bild-galerie-loeschen"
              onClick={(e) => {
                e.stopPropagation();
                entfernen(bild.url);
              }}
              title="Bild entfernen"
            >
              ✕
            </button>
          </div>
        ))}

        {/* Neues Bild hinzufügen */}
        <div
          className="bild-galerie-thumb bild-galerie-neu"
          onClick={() => dateiRef.current?.click()}
        >
          <span>+</span>
        </div>

        {/* KI-Bild generieren — eigenes Kästchen statt Knopf in der Reihe,
            passt zum Kachel-Raster der Galerie. */}
        <div
          className="bild-galerie-thumb bild-galerie-neu"
          onClick={() => setKiOffen(true)}
          title="KI-Bild generieren"
        >
          <span aria-hidden="true">✨</span>
        </div>
      </div>

      <input
        ref={dateiRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        style={{ display: "none" }}
        onChange={(e) => hochladen(e.target.files?.[0])}
      />

      {laedt && <span className="bild-galerie-ladend">lädt…</span>}
      {fehler && <span className="bild-galerie-fehler">{fehler}</span>}

      {/* Bestätigungsdialog für Löschen */}
      {loeschenOffen && (
        <Bestaetigung
          titel="Bild löschen?"
          text="Das Bild wird aus der Galerie entfernt. Das lässt sich nicht rückgängig machen."
          jaText="Ja, löschen"
          neinText="Abbrechen"
          onJa={entfernenBestaetigt}
          onNein={() => setLoeschenOffen(null)}
        />
      )}

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
        onUebernehmen={(blob) => hochladenBytes(blob, "ki-bild.png")}
      />
    </div>
  );
}
