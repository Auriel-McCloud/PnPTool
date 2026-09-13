import type { Fraktion } from "./api";
import { BildBlitz } from "../mitteilungen/BildBlitz";
import "./pc-kacheln.css"; // Selbes Raster und Kachelgerüst wie bei PCs/NPCs

/**
 * Kachel-Übersicht für Fraktionen.
 *
 * Gleiches Bedienkonzept wie Orte und NPCs: Bild, Name, Blitz zum Herzeigen,
 * Klick öffnet das Detail-Popup. Zeigt Ziele und Ressourcen als Kurztext.
 */

interface FraktionKachelProps {
  campaignId: string;
  fraktion: Fraktion;
  verbindungen: number;
  onKlick: () => void;
}

const SICHT_TEXT: Record<string, string> = {
  GM: "SL",
  ALLE: "Alle",
  SPEZIFISCH: "Einzelne",
};

function FraktionKachel({ campaignId, fraktion, verbindungen, onKlick }: FraktionKachelProps) {
  return (
    <div className="pc-kachel fraktion-kachel" onClick={onKlick}>
      <div className="pc-kachel-bild-bereich">
        {fraktion.bildUrl ? (
          <img src={fraktion.bildUrl} alt={fraktion.name} className="pc-kachel-bild" />
        ) : (
          <div className="pc-kachel-bild-leer">⬡</div>
        )}
        {/* Der Blitz sitzt am Bild, weil man eine Fraktion genau dann zeigen will,
            wenn man sie gerade ansieht. Ohne Bild gibt es nichts zu zeigen —
            BildBlitz gibt dann von sich aus null zurück. */}
        <div className="pc-kachel-blitz-halter" onClick={(e) => e.stopPropagation()}>
          <BildBlitz campaignId={campaignId} bildUrl={fraktion.bildUrl ?? ""} name={fraktion.name} klein />
        </div>
      </div>

      <div className="pc-kachel-info">
        <div className="pc-kachel-name">{fraktion.name}</div>

        <div className="pc-kachel-werte">
          <div className="pc-kachel-wert" title="Verbindungen im Beziehungsgraph">
            <span className="pc-kachel-wert-icon">⬡</span>
            <span>{verbindungen}</span>
          </div>
          <div className="pc-kachel-wert" title="Sichtbarkeit der Beschreibung">
            <span className="pc-kachel-wert-icon">{fraktion.sichtbarkeit === "GM" ? "🔒" : "◉"}</span>
            <span>{SICHT_TEXT[fraktion.sichtbarkeit] ?? fraktion.sichtbarkeit}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

interface FraktionKachelnProps {
  campaignId: string;
  fraktionen: Fraktion[];
  /** Verbindungszahl je Fraktion-ID; fehlende Einträge zählen als 0. */
  verbindungen: Map<string, number>;
  onFraktionKlick: (fraktion: Fraktion) => void;
  /** Steht etwas anderes an als „noch nichts angelegt"? (z.B. Filter ohne Treffer) */
  leertext?: string;
}

export function FraktionKacheln({ campaignId, fraktionen, verbindungen, onFraktionKlick, leertext }: FraktionKachelnProps) {
  if (fraktionen.length === 0) {
    return <p className="pc-kacheln-leer">{leertext ?? "Noch keine Fraktionen angelegt."}</p>;
  }

  return (
    <div className="pc-kacheln-raster">
      {fraktionen.map((f) => (
        <FraktionKachel
          key={f.id}
          campaignId={campaignId}
          fraktion={f}
          verbindungen={verbindungen.get(f.id) ?? 0}
          onKlick={() => onFraktionKlick(f)}
        />
      ))}
    </div>
  );
}
