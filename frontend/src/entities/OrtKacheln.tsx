import type { Ort } from "./api";
import { BildBlitz } from "../mitteilungen/BildBlitz";
import "./pc-kacheln.css"; // Selbes Raster und Kachelgerüst wie bei PCs/NPCs

/**
 * Kachel-Übersicht für Orte.
 *
 * Gleiches Bedienkonzept wie PCs und NPCs: Bild, Name, Blitz zum Herzeigen,
 * Klick öffnet das Detail-Popup. Statt LP/WK stehen hier die Kennzahlen, die
 * bei einem Ort etwas aussagen: wie viele Verbindungen daran hängen und für
 * wen er sichtbar ist.
 */

interface OrtKachelProps {
  campaignId: string;
  ort: Ort;
  verbindungen: number;
  onKlick: () => void;
}

const SICHT_TEXT: Record<string, string> = {
  GM: "SL",
  ALLE: "Alle",
  SPEZIFISCH: "Einzelne",
};

function OrtKachel({ campaignId, ort, verbindungen, onKlick }: OrtKachelProps) {
  return (
    <div className="pc-kachel ort-kachel" onClick={onKlick}>
      <div className="pc-kachel-bild-bereich">
        {ort.bildUrl ? (
          <img src={ort.bildUrl} alt={ort.name} className="pc-kachel-bild" />
        ) : (
          <div className="pc-kachel-bild-leer">⌖</div>
        )}
        {/* Der Blitz sitzt am Bild, weil man einen Ort genau dann zeigen will,
            wenn man ihn gerade ansieht. Ohne Bild gibt es nichts zu zeigen —
            BildBlitz gibt dann von sich aus null zurück. */}
        <div className="pc-kachel-blitz-halter" onClick={(e) => e.stopPropagation()}>
          <BildBlitz campaignId={campaignId} bildUrl={ort.bildUrl ?? ""} name={ort.name} klein />
        </div>
      </div>

      <div className="pc-kachel-info">
        <div className="pc-kachel-name">{ort.name}</div>

        <div className="pc-kachel-werte">
          <div className="pc-kachel-wert" title="Verbindungen im Beziehungsgraph">
            <span className="pc-kachel-wert-icon">⬡</span>
            <span>{verbindungen}</span>
          </div>
          <div className="pc-kachel-wert" title="Sichtbarkeit der Beschreibung">
            <span className="pc-kachel-wert-icon">{ort.sichtbarkeit === "GM" ? "🔒" : "◉"}</span>
            <span>{SICHT_TEXT[ort.sichtbarkeit] ?? ort.sichtbarkeit}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

interface OrtKachelnProps {
  campaignId: string;
  orte: Ort[];
  /** Verbindungszahl je Ort-ID; fehlende Einträge zählen als 0. */
  verbindungen: Map<string, number>;
  onOrtKlick: (ort: Ort) => void;
  /** Steht etwas anderes an als "noch nichts angelegt"? (z.B. Filter ohne Treffer) */
  leertext?: string;
}

export function OrtKacheln({ campaignId, orte, verbindungen, onOrtKlick, leertext }: OrtKachelnProps) {
  if (orte.length === 0) {
    return <p className="pc-kacheln-leer">{leertext ?? "Noch keine Orte angelegt."}</p>;
  }

  return (
    <div className="pc-kacheln-raster">
      {orte.map((o) => (
        <OrtKachel
          key={o.id}
          campaignId={campaignId}
          ort={o}
          verbindungen={verbindungen.get(o.id) ?? 0}
          onKlick={() => onOrtKlick(o)}
        />
      ))}
    </div>
  );
}
