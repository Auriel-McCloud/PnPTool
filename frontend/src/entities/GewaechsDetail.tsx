import { useState } from "react";
import type { Gewaechs } from "./api";
import { entitiesApi } from "./api";
import { EntitaetsBild } from "./EntitaetsBild";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { useAutosave } from "../shell/autosave";
import { VisibilitySelector, type PersonOption } from "./VisibilitySelector";
import { parseRichText, serializeRichText } from "../richtext/content";
import type { JSONContent } from "@tiptap/react";
import "./pc-detail.css"; // Selbes Popup-Gerüst wie bei Ort/Event/Fraktion

/**
 * Detail-Popup für ein Gewächs (Flora & Fauna, 06.10.2026).
 *
 * Gleiches Bedienkonzept wie EventDetail/OrtDetail — bewusst OHNE
 * Beziehungs-Tab (ein Gewächs nimmt nicht an VERBINDUNG teil) und ohne
 * Charakterblatt (das ist Critter vorbehalten, siehe CritterFenster).
 * Stattdessen eine eigene "Eigenschaften"-Sektion für giftig/essbar/
 * Gefährlichkeit/Besonderheiten — die Klassifikation, die ein Gewächs von
 * einer reinen Orts-/Event-Beschreibung unterscheidet.
 */

type Unteransicht = "uebersicht" | "beschreibung" | "notizen";

interface GewaechsDetailProps {
  campaignId: string;
  gewaechs: Gewaechs;
  pcOptions: PersonOption[];
  onSchliessen: () => void;
  onGeaendert: () => void;
}

export function GewaechsDetail({ campaignId, gewaechs, pcOptions, onSchliessen, onGeaendert }: GewaechsDetailProps) {
  const [unteransicht, setUnteransicht] = useState<Unteransicht>("uebersicht");
  const [name, setName] = useState(gewaechs.name);
  const [gefaehrlichkeit, setGefaehrlichkeit] = useState(gewaechs.gefaehrlichkeit ?? "");
  const [eigenschaften, setEigenschaften] = useState(gewaechs.eigenschaften ?? "");
  const [beschreibungDoc, setBeschreibungDoc] = useState<JSONContent>(parseRichText(gewaechs.description));
  const [notizenDoc, setNotizenDoc] = useState<JSONContent>(parseRichText(gewaechs.notes));
  const [, setSpeichert] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [loeschenOffen, setLoeschenOffen] = useState(false);

  async function speichere(felder: Partial<Gewaechs>) {
    setSpeichert(true);
    setFehler(null);
    try {
      await entitiesApi.updateGewaechs(campaignId, gewaechs.id, felder);
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
    } finally {
      setSpeichert(false);
    }
  }

  // Still: kein onGeaendert, sonst unmountet das Popup (siehe autosave.ts).
  async function speichereStill(felder: Partial<Gewaechs>) {
    try {
      await entitiesApi.updateGewaechs(campaignId, gewaechs.id, felder);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
    }
  }

  const autosaveBeschreibung = useAutosave((doc: JSONContent) =>
    speichereStill({ description: serializeRichText(doc) }),
  );
  const autosaveNotizen = useAutosave((doc: JSONContent) => speichereStill({ notes: serializeRichText(doc) }));

  async function loeschen() {
    setSpeichert(true);
    try {
      await entitiesApi.deleteGewaechs(campaignId, gewaechs.id);
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
      titel={gewaechs.name}
      unterzeile="Gewächs"
      kennung={`gewaechs-detail:${gewaechs.id}`}
      ton="var(--bereich-orte, var(--neon))"
      onSchliessen={onSchliessen}
    >
      <div className="pcd-inhalt">
        <nav className="pcd-nav">
          {(
            [
              ["uebersicht", "Übersicht"],
              ["beschreibung", "Beschreibung"],
              ["notizen", "Notizen"],
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
                  art="gewaechse"
                  id={gewaechs.id}
                  name={gewaechs.name}
                  bildUrl={gewaechs.bildUrl ?? ""}
                  beschreibung={gewaechs.description}
                  notizen={gewaechs.notes}
                  onGeaendert={onGeaendert}
                />
              </div>
              <div className="pcd-schnellzugriff">
                <div className="pcd-feld">
                  <label htmlFor={`gewaechs-name-${gewaechs.id}`}>Name</label>
                  <input
                    id={`gewaechs-name-${gewaechs.id}`}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onBlur={() => {
                      const sauber = name.trim();
                      if (!sauber) {
                        setName(gewaechs.name);
                        return;
                      }
                      if (sauber !== gewaechs.name) speichere({ name: sauber });
                    }}
                  />
                </div>

                <div className="bg-zeile" style={{ marginTop: 8 }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em" }}>
                    <input
                      type="checkbox"
                      checked={!!gewaechs.giftig}
                      onChange={(e) => speichere({ giftig: e.target.checked })}
                    />
                    giftig
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em" }}>
                    <input
                      type="checkbox"
                      checked={!!gewaechs.essbar}
                      onChange={(e) => speichere({ essbar: e.target.checked })}
                    />
                    essbar
                  </label>
                </div>

                <div className="pcd-feld" style={{ marginTop: 8 }}>
                  <label htmlFor={`gewaechs-gefahr-${gewaechs.id}`}>Gefährlichkeit</label>
                  <input
                    id={`gewaechs-gefahr-${gewaechs.id}`}
                    value={gefaehrlichkeit}
                    placeholder="z.B. harmlos, reizend, tödlich"
                    onChange={(e) => setGefaehrlichkeit(e.target.value)}
                    onBlur={() => {
                      if (gefaehrlichkeit !== (gewaechs.gefaehrlichkeit ?? "")) speichere({ gefaehrlichkeit });
                    }}
                  />
                </div>

                <div className="pcd-feld" style={{ marginTop: 8 }}>
                  <label htmlFor={`gewaechs-eigenschaften-${gewaechs.id}`}>Besonderheiten</label>
                  <input
                    id={`gewaechs-eigenschaften-${gewaechs.id}`}
                    value={eigenschaften}
                    placeholder="z.B. leuchtet im Dunkeln, kybernetisch modifiziert"
                    onChange={(e) => setEigenschaften(e.target.value)}
                    onBlur={() => {
                      if (eigenschaften !== (gewaechs.eigenschaften ?? "")) speichere({ eigenschaften });
                    }}
                  />
                </div>

                <VisibilitySelector
                  label="Sichtbarkeit der Beschreibung"
                  modus={gewaechs.sichtbarkeit}
                  sichtbarFuer={gewaechs.sichtbarFuer}
                  onChange={(m, f) => speichere({ sichtbarkeit: m, sichtbarFuer: f })}
                  pcOptions={pcOptions}
                />
                <VisibilitySelector
                  label="Sichtbarkeit der Notizen"
                  modus={gewaechs.notizenSichtbarkeit}
                  sichtbarFuer={gewaechs.notizenSichtbarFuer}
                  onChange={(m, f) => speichere({ notizenSichtbarkeit: m, notizenSichtbarFuer: f })}
                  pcOptions={pcOptions}
                />

                <div className="pcd-buttons" style={{ marginTop: 12 }}>
                  <button type="button" onClick={() => setUnteransicht("beschreibung")}>
                    📝 Beschreibung bearbeiten
                  </button>
                  <button
                    type="button"
                    onClick={() => setLoeschenOffen(true)}
                    style={{ color: "var(--signal)", borderColor: "var(--signal)" }}
                  >
                    🗑 Gewächs löschen
                  </button>
                </div>
              </div>
            </div>
          )}

          {unteransicht === "beschreibung" && (
            <div className="pcd-editor-bereich">
              <RichTextEditor
                content={beschreibungDoc}
                onChange={(doc) => {
                  setBeschreibungDoc(doc);
                  autosaveBeschreibung(doc);
                }}
                minHeight={200}
                kiKontext={{ campaignId, objektTyp: "Gewaechs", objektName: gewaechs.name, feldLabel: "Beschreibung" }}
              />
            </div>
          )}

          {unteransicht === "notizen" && (
            <div className="pcd-editor-bereich">
              <RichTextEditor
                content={notizenDoc}
                onChange={(doc) => {
                  setNotizenDoc(doc);
                  autosaveNotizen(doc);
                }}
                minHeight={200}
                kiKontext={{ campaignId, objektTyp: "Gewaechs", objektName: gewaechs.name, feldLabel: "Notizen" }}
              />
            </div>
          )}
        </div>
      </div>

      {loeschenOffen && (
        <Bestaetigung
          titel="Gewächs löschen?"
          text={`„${gewaechs.name}“ wird endgültig entfernt, samt aller Flora-&-Fauna-Verknüpfungen. Das lässt sich nicht rückgängig machen.`}
          jaText="Ja, löschen"
          neinText="Abbrechen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </Fenster>
  );
}
