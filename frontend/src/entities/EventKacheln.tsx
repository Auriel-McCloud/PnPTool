import type { Event } from "./api";
import { BildBlitz } from "../mitteilungen/BildBlitz";
import "./pc-kacheln.css"; // Selbes Raster und Kachelgerüst wie bei PCs/NPCs

/**
 * Kachel-Übersicht für Events.
 *
 * Gleiches Bedienkonzept wie PCs, NPCs und Orte. Der Zeitpunkt steht dort,
 * wo bei einem PC der Spielername steht — er ist die Einordnung, die man
 * beim Überfliegen braucht ("war das Session 3 oder 4?").
 */

interface EventKachelProps {
  campaignId: string;
  event: Event;
  verbindungen: number;
  onKlick: () => void;
}

const SICHT_TEXT: Record<string, string> = {
  GM: "SL",
  ALLE: "Alle",
  SPEZIFISCH: "Einzelne",
};

function EventKachel({ campaignId, event, verbindungen, onKlick }: EventKachelProps) {
  return (
    <div className="pc-kachel event-kachel" onClick={onKlick}>
      <div className="pc-kachel-bild-bereich">
        {event.bildUrl ? (
          <img src={event.bildUrl} alt={event.title} className="pc-kachel-bild" />
        ) : (
          <div className="pc-kachel-bild-leer">◆</div>
        )}
        <div className="pc-kachel-blitz-halter" onClick={(e) => e.stopPropagation()}>
          <BildBlitz campaignId={campaignId} bildUrl={event.bildUrl ?? ""} name={event.title} klein />
        </div>
      </div>

      <div className="pc-kachel-info">
        <div className="pc-kachel-name">{event.title}</div>
        {/* Ohne Zeitpunkt bleibt die Zeile leer statt zu fehlen — sonst
            rutschen die Werte hoch und das Raster wirkt unruhig. */}
        <div className="pc-kachel-spieler">{event.timestamp || "kein Zeitpunkt"}</div>

        <div className="pc-kachel-werte">
          <div className="pc-kachel-wert" title="Verbindungen im Beziehungsgraph">
            <span className="pc-kachel-wert-icon">⬡</span>
            <span>{verbindungen}</span>
          </div>
          <div className="pc-kachel-wert" title="Sichtbarkeit der Beschreibung">
            <span className="pc-kachel-wert-icon">{event.sichtbarkeit === "GM" ? "🔒" : "◉"}</span>
            <span>{SICHT_TEXT[event.sichtbarkeit] ?? event.sichtbarkeit}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

interface EventKachelnProps {
  campaignId: string;
  events: Event[];
  verbindungen: Map<string, number>;
  onEventKlick: (event: Event) => void;
  leertext?: string;
}

export function EventKacheln({
  campaignId,
  events,
  verbindungen,
  onEventKlick,
  leertext,
}: EventKachelnProps) {
  if (events.length === 0) {
    return <p className="pc-kacheln-leer">{leertext ?? "Noch keine Events angelegt."}</p>;
  }

  return (
    <div className="pc-kacheln-raster">
      {events.map((ev) => (
        <EventKachel
          key={ev.id}
          campaignId={campaignId}
          event={ev}
          verbindungen={verbindungen.get(ev.id) ?? 0}
          onKlick={() => onEventKlick(ev)}
        />
      ))}
    </div>
  );
}
