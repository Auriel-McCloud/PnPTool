import { useState } from "react";
import type { EntityKind, Event, Verbindung } from "./api";
import { entitiesApi } from "./api";
import { EntitaetsBild } from "./EntitaetsBild";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { VisibilitySelector, type PersonOption } from "./VisibilitySelector";
import { parseRichText, serializeRichText } from "../richtext/content";
import { BeziehungsListe, beziehungsZeilen } from "./BeziehungsListe";
import type { JSONContent } from "@tiptap/react";
import "./pc-detail.css"; // Selbes Popup-Gerüst wie bei PCs, NPCs und Orten

/**
 * Detail-Popup für ein Event.
 *
 * Gleiches Bedienkonzept wie die übrigen Entitäten. Der Beziehungs-Tab ist
 * hier der wichtigste: an einem Event hängt, wer dabei war und in welcher
 * Rolle ("Gegner", "Geisel") — genau das, wonach die NPC-Übersicht filtert.
 */

type Unteransicht = "uebersicht" | "beschreibung" | "notizen" | "beziehungen";

interface EventDetailProps {
  campaignId: string;
  event: Event;
  verbindungen: Verbindung[];
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  onSchliessen: () => void;
  onGeaendert: () => void;
}

export function EventDetail({
  campaignId,
  event,
  verbindungen,
  namen,
  pcOptions,
  onSchliessen,
  onGeaendert,
}: EventDetailProps) {
  const [unteransicht, setUnteransicht] = useState<Unteransicht>("uebersicht");
  const [titel, setTitel] = useState(event.title);
  const [zeitpunkt, setZeitpunkt] = useState(event.timestamp);
  const [beschreibungDoc, setBeschreibungDoc] = useState<JSONContent>(parseRichText(event.description));
  const [notizenDoc, setNotizenDoc] = useState<JSONContent>(parseRichText(event.notes));
  const [speichert, setSpeichert] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [loeschenOffen, setLoeschenOffen] = useState(false);

  const zeilen = beziehungsZeilen(event.id, verbindungen, namen);

  async function speichere(felder: Partial<Event>) {
    setSpeichert(true);
    setFehler(null);
    try {
      await entitiesApi.updateEvent(campaignId, event.id, felder);
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
    } finally {
      setSpeichert(false);
    }
  }

  async function loeschen() {
    setSpeichert(true);
    try {
      await entitiesApi.deleteEvent(campaignId, event.id);
      setLoeschenOffen(false);
      onGeaendert();
      onSchliessen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Löschen fehlgeschlagen");
      setLoeschenOffen(false);
    } finally {
      setSpeichert(false);
    }
  }

  return (
    <Fenster
      offen
      breit={unteransicht === "beziehungen"}
      titel={event.title}
      unterzeile={event.timestamp || "Event"}
      kennung={`event-detail:${event.id}`}
      ton="var(--bereich-events)"
      onSchliessen={onSchliessen}
    >
      <div className="pcd-inhalt">
        <nav className="pcd-nav pcd-nav-events">
          {(
            [
              ["uebersicht", "Übersicht"],
              ["beschreibung", "Beschreibung"],
              ["notizen", "Notizen"],
              ["beziehungen", `Beteiligte (${zeilen.length})`],
            ] as [Unteransicht, string][]
          ).map(([wert, text]) => (
            <button
              key={wert}
              type="button"
              className={unteransicht === wert ? "pcd-nav-aktiv" : ""}
              onClick={() => setUnteransicht(wert)}
            >
              {text}
            </button>
          ))}
        </nav>

        <div className="pcd-bereich">
          {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}

          {unteransicht === "uebersicht" && (
            <div className="pcd-uebersicht">
              <div className="pcd-bild-bereich">
                <EntitaetsBild
                  campaignId={campaignId}
                  art="events"
                  id={event.id}
                  name={event.title}
                  bildUrl={event.bildUrl ?? ""}
                  onGeaendert={onGeaendert}
                />
              </div>
              <div className="pcd-schnellzugriff">
                <div className="pcd-feld">
                  <label htmlFor={`event-titel-${event.id}`}>Titel</label>
                  <input
                    id={`event-titel-${event.id}`}
                    value={titel}
                    onChange={(e) => setTitel(e.target.value)}
                    onBlur={() => {
                      const sauber = titel.trim();
                      if (!sauber) {
                        setTitel(event.title);
                        return;
                      }
                      if (sauber !== event.title) speichere({ title: sauber });
                    }}
                  />
                </div>

                <div className="pcd-feld">
                  <label htmlFor={`event-zeit-${event.id}`}>Zeitpunkt</label>
                  <input
                    id={`event-zeit-${event.id}`}
                    value={zeitpunkt}
                    placeholder="z.B. Session 3"
                    onChange={(e) => setZeitpunkt(e.target.value)}
                    onBlur={() => {
                      // Leerer Zeitpunkt ist erlaubt — nicht jedes Event ist
                      // schon eingeordnet. In der Sortierung landet es hinten.
                      if (zeitpunkt !== event.timestamp) speichere({ timestamp: zeitpunkt });
                    }}
                  />
                </div>

                <VisibilitySelector
                  label="Sichtbarkeit der Beschreibung"
                  modus={event.sichtbarkeit}
                  sichtbarFuer={event.sichtbarFuer}
                  onChange={(m, f) => speichere({ sichtbarkeit: m, sichtbarFuer: f })}
                  pcOptions={pcOptions}
                />
                <VisibilitySelector
                  label="Sichtbarkeit der Notizen"
                  modus={event.notizenSichtbarkeit}
                  sichtbarFuer={event.notizenSichtbarFuer}
                  onChange={(m, f) => speichere({ notizenSichtbarkeit: m, notizenSichtbarFuer: f })}
                  pcOptions={pcOptions}
                />

                <div className="pcd-buttons" style={{ marginTop: 12 }}>
                  <button type="button" onClick={() => setUnteransicht("beschreibung")}>
                    📝 Beschreibung bearbeiten
                  </button>
                  <button type="button" onClick={() => setUnteransicht("beziehungen")}>
                    ⬡ Beteiligte ansehen ({zeilen.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setLoeschenOffen(true)}
                    style={{ color: "var(--signal)", borderColor: "var(--signal)" }}
                  >
                    🗑 Event löschen
                  </button>
                </div>
              </div>
            </div>
          )}

          {unteransicht === "beschreibung" && (
            <div className="pcd-editor-bereich">
              <RichTextEditor content={beschreibungDoc} onChange={setBeschreibungDoc} minHeight={200} />
              <button
                type="button"
                className="pcd-speichern"
                onClick={() => speichere({ description: serializeRichText(beschreibungDoc) })}
                disabled={speichert}
              >
                {speichert ? "Speichert…" : "Beschreibung speichern"}
              </button>
            </div>
          )}

          {unteransicht === "notizen" && (
            <div className="pcd-editor-bereich">
              <RichTextEditor content={notizenDoc} onChange={setNotizenDoc} minHeight={200} />
              <button
                type="button"
                className="pcd-speichern"
                onClick={() => speichere({ notes: serializeRichText(notizenDoc) })}
                disabled={speichert}
              >
                {speichert ? "Speichert…" : "Notizen speichern"}
              </button>
            </div>
          )}

          {unteransicht === "beziehungen" && (
            <BeziehungsListe
              campaignId={campaignId}

              zeilen={zeilen}
              onGeaendert={onGeaendert}
              farbe="var(--bereich-events, var(--neon))"
            />
          )}
        </div>
      </div>

      {loeschenOffen && (
        <Bestaetigung
          titel="Event löschen?"
          text={`„${event.title}“ wird endgültig entfernt, samt aller ${zeilen.length} Verbindungen. Das lässt sich nicht rückgängig machen.`}
          jaText="Ja, löschen"
          neinText="Abbrechen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </Fenster>
  );
}
