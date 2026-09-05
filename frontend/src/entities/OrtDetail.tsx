import { useState } from "react";
import type { EntityKind, Ort, Verbindung } from "./api";
import { entitiesApi } from "./api";
import { EntitaetsBild } from "./EntitaetsBild";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { VisibilitySelector, type PersonOption } from "./VisibilitySelector";
import { parseRichText, serializeRichText } from "../richtext/content";
import { BeziehungsListe, beziehungsZeilen } from "./BeziehungsListe";
import type { JSONContent } from "@tiptap/react";
import "./pc-detail.css"; // Selbes Popup-Gerüst wie bei PCs und NPCs

/**
 * Detail-Popup für einen Ort.
 *
 * Gleiches Bedienkonzept wie PCDetail/NPCDetail: Navigation oben, Übersicht
 * mit Bild und Schnellzugriff, dann die einzelnen Bereiche. Statt
 * Charakterblatt und Augments gibt es hier, was einen Ort ausmacht — wer und
 * was mit ihm verbunden ist.
 */

type Unteransicht = "uebersicht" | "beschreibung" | "notizen" | "beziehungen";

interface OrtDetailProps {
  campaignId: string;
  ort: Ort;
  /** Alle sichtbaren Verbindungen der Kampagne — gefiltert wird hier. */
  verbindungen: Verbindung[];
  /** ID → Name/Art für die Gegenseiten; muss sichtbarkeitsgefiltert sein. */
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  onSchliessen: () => void;
  onGeaendert: () => void;
}

export function OrtDetail({
  campaignId,
  ort,
  verbindungen,
  namen,
  pcOptions,
  onSchliessen,
  onGeaendert,
}: OrtDetailProps) {
  const [unteransicht, setUnteransicht] = useState<Unteransicht>("uebersicht");
  const [name, setName] = useState(ort.name);
  const [beschreibungDoc, setBeschreibungDoc] = useState<JSONContent>(parseRichText(ort.description));
  const [notizenDoc, setNotizenDoc] = useState<JSONContent>(parseRichText(ort.notes));
  const [speichert, setSpeichert] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [loeschenOffen, setLoeschenOffen] = useState(false);

  const zeilen = beziehungsZeilen(ort.id, verbindungen, namen);

  async function speichere(felder: Partial<Ort>) {
    setSpeichert(true);
    setFehler(null);
    try {
      await entitiesApi.updateOrt(campaignId, ort.id, felder);
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
      await entitiesApi.deleteOrt(campaignId, ort.id);
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
      titel={ort.name}
      unterzeile="Ort"
      kennung={`ort-detail:${ort.id}`}
      ton="var(--bereich-orte)"
      onSchliessen={onSchliessen}
    >
      <div className="pcd-inhalt">
        <nav className="pcd-nav pcd-nav-orte">
          {(
            [
              ["uebersicht", "Übersicht"],
              ["beschreibung", "Beschreibung"],
              ["notizen", "Notizen"],
              ["beziehungen", `Beziehungen (${zeilen.length})`],
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
                  art="orte"
                  id={ort.id}
                  name={ort.name}
                  bildUrl={ort.bildUrl ?? ""}
                  onGeaendert={onGeaendert}
                />
              </div>
              <div className="pcd-schnellzugriff">
                <div className="pcd-feld">
                  <label htmlFor={`ort-name-${ort.id}`}>Name</label>
                  <input
                    id={`ort-name-${ort.id}`}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onBlur={() => {
                      const sauber = name.trim();
                      // Leerer Name würde den Ort in jeder Liste unauffindbar
                      // machen — dann lieber den alten behalten.
                      if (!sauber) {
                        setName(ort.name);
                        return;
                      }
                      if (sauber !== ort.name) speichere({ name: sauber });
                    }}
                  />
                </div>

                <VisibilitySelector
                  label="Sichtbarkeit der Beschreibung"
                  modus={ort.sichtbarkeit}
                  sichtbarFuer={ort.sichtbarFuer}
                  onChange={(m, f) => speichere({ sichtbarkeit: m, sichtbarFuer: f })}
                  pcOptions={pcOptions}
                />
                <VisibilitySelector
                  label="Sichtbarkeit der Notizen"
                  modus={ort.notizenSichtbarkeit}
                  sichtbarFuer={ort.notizenSichtbarFuer}
                  onChange={(m, f) => speichere({ notizenSichtbarkeit: m, notizenSichtbarFuer: f })}
                  pcOptions={pcOptions}
                />

                <div className="pcd-buttons" style={{ marginTop: 12 }}>
                  <button type="button" onClick={() => setUnteransicht("beschreibung")}>
                    📝 Beschreibung bearbeiten
                  </button>
                  <button type="button" onClick={() => setUnteransicht("beziehungen")}>
                    ⬡ Beziehungen ansehen ({zeilen.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setLoeschenOffen(true)}
                    style={{ color: "var(--signal)", borderColor: "var(--signal)" }}
                  >
                    🗑 Ort löschen
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
              farbe="var(--bereich-orte, var(--neon))"
            />
          )}
        </div>
      </div>

      {loeschenOffen && (
        <Bestaetigung
          titel="Ort löschen?"
          text={`„${ort.name}“ wird endgültig entfernt, samt aller ${zeilen.length} Verbindungen. Das lässt sich nicht rückgängig machen.`}
          jaText="Ja, löschen"
          neinText="Abbrechen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </Fenster>
  );
}
