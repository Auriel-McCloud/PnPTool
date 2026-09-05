import { useState } from "react";
import type { Person } from "./api";
import { EntitaetsBild } from "./EntitaetsBild";
import { Fenster } from "../shell/Fenster";
import { Charakterblatt } from "../traits/Charakterblatt";
import { CharacterSheetPanel } from "../traits/CharacterSheetPanel";
import { type PersonOption } from "./VisibilitySelector";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { parseRichText, serializeRichText } from "../richtext/content";
import { entitiesApi } from "./api";
import type { JSONContent } from "@tiptap/react";
import "./pc-detail.css";

/**
 * Detail-Popup für einen PC.
 *
 * Zeigt Übersicht mit Bild und bietet Zugang zu:
 * - Charakterblatt
 * - Gegenstände
 * - Beschreibung
 * - Notizen
 */

type Unteransicht = "uebersicht" | "blatt" | "gegenstaende" | "beschreibung" | "notizen";

interface PCDetailProps {
  campaignId: string;
  person: Person;
  spielerName?: string;
  pcOptions: PersonOption[];
  alleOptionen: PersonOption[];
  onSchliessen: () => void;
  onGeaendert: () => void;
}

export function PCDetail({
  campaignId,
  person,
  spielerName,
  pcOptions,
  alleOptionen,
  onSchliessen,
  onGeaendert,
}: PCDetailProps) {
  const [unteransicht, setUnteransicht] = useState<Unteransicht>("uebersicht");
  const [beschreibungDoc, setBeschreibungDoc] = useState<JSONContent>(parseRichText(person.description));
  const [notizenDoc, setNotizenDoc] = useState<JSONContent>(parseRichText(person.notes));
  const [speichert, setSpeichert] = useState(false);

  async function speichereBeschreibung() {
    setSpeichert(true);
    try {
      await entitiesApi.updatePerson(campaignId, person.id, {
        description: serializeRichText(beschreibungDoc),
      });
      onGeaendert();
    } finally {
      setSpeichert(false);
    }
  }

  async function speichereNotizen() {
    setSpeichert(true);
    try {
      await entitiesApi.updatePerson(campaignId, person.id, {
        notes: serializeRichText(notizenDoc),
      });
      onGeaendert();
    } finally {
      setSpeichert(false);
    }
  }

  return (
    <Fenster
      offen
      breit={unteransicht === "blatt"}
      titel={person.name}
      unterzeile={spielerName ? `Gespielt von ${spielerName}` : "Kein Spieler zugeordnet"}
      kennung={`pc-detail:${person.id}`}
      onSchliessen={onSchliessen}
    >
      <div className="pcd-inhalt">
        {/* Navigation */}
        <nav className="pcd-nav">
          <button
            type="button"
            className={unteransicht === "uebersicht" ? "pcd-nav-aktiv" : ""}
            onClick={() => setUnteransicht("uebersicht")}
          >
            Übersicht
          </button>
          <button
            type="button"
            className={unteransicht === "blatt" ? "pcd-nav-aktiv" : ""}
            onClick={() => setUnteransicht("blatt")}
          >
            Charakterblatt
          </button>
          <button
            type="button"
            className={unteransicht === "gegenstaende" ? "pcd-nav-aktiv" : ""}
            onClick={() => setUnteransicht("gegenstaende")}
          >
            Gegenstände
          </button>
          <button
            type="button"
            className={unteransicht === "beschreibung" ? "pcd-nav-aktiv" : ""}
            onClick={() => setUnteransicht("beschreibung")}
          >
            Beschreibung
          </button>
          <button
            type="button"
            className={unteransicht === "notizen" ? "pcd-nav-aktiv" : ""}
            onClick={() => setUnteransicht("notizen")}
          >
            Notizen
          </button>
        </nav>

        {/* Inhalt */}
        <div className="pcd-bereich">
          {unteransicht === "uebersicht" && (
            <div className="pcd-uebersicht">
              <div className="pcd-bild-bereich">
                <EntitaetsBild
                  campaignId={campaignId}
                  art="personen"
                  id={person.id}
                  name={person.name}
                  bildUrl={person.bildUrl ?? ""}
                  onGeaendert={onGeaendert}
                />
              </div>
              <div className="pcd-schnellzugriff">
                <h3>Schnellzugriff</h3>
                <div className="pcd-buttons">
                  <button type="button" onClick={() => setUnteransicht("blatt")}>
                    📋 Charakterblatt öffnen
                  </button>
                  <button type="button" onClick={() => setUnteransicht("gegenstaende")}>
                    ◈ Gegenstände verwalten
                  </button>
                  <button type="button" onClick={() => setUnteransicht("beschreibung")}>
                    📝 Beschreibung bearbeiten
                  </button>
                  <button type="button" onClick={() => setUnteransicht("notizen")}>
                    🗒️ Notizen bearbeiten
                  </button>
                </div>
              </div>
            </div>
          )}

          {unteransicht === "blatt" && (
            <Charakterblatt campaignId={campaignId} personId={person.id} bearbeitbar />
          )}

          {unteransicht === "gegenstaende" && (
            <CharacterSheetPanel
              campaignId={campaignId}
              person={person}
              pcOptions={pcOptions}
              alleOptionen={alleOptionen}
            />
          )}

          {unteransicht === "beschreibung" && (
            <div className="pcd-editor-bereich">
              <RichTextEditor
                content={beschreibungDoc}
                onChange={setBeschreibungDoc}
                minHeight={200}
              />
              <button
                type="button"
                className="pcd-speichern"
                onClick={speichereBeschreibung}
                disabled={speichert}
              >
                {speichert ? "Speichert…" : "Beschreibung speichern"}
              </button>
            </div>
          )}

          {unteransicht === "notizen" && (
            <div className="pcd-editor-bereich">
              <RichTextEditor
                content={notizenDoc}
                onChange={setNotizenDoc}
                minHeight={200}
              />
              <button
                type="button"
                className="pcd-speichern"
                onClick={speichereNotizen}
                disabled={speichert}
              >
                {speichert ? "Speichert…" : "Notizen speichern"}
              </button>
            </div>
          )}
        </div>
      </div>
    </Fenster>
  );
}
