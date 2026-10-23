import { useEffect, useState } from "react";
import type { EntityKind, Person, Verbindung } from "./api";
import { anzeigeName } from "./api";
import { BildGalerie } from "./BildGalerie";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Charakterblatt } from "../traits/Charakterblatt";
import { PCInventar } from "./PCInventar";
import { AugmentsAnsicht } from "../augments/AugmentsAnsicht";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { useAutosave } from "../shell/autosave";
import { parseRichText, serializeRichText } from "../richtext/content";
import { entitiesApi } from "./api";
import { BeziehungsTab, PERSON_TYP_VORSCHLAEGE } from "./BeziehungsTab";
import { beziehungsZeilen } from "./BeziehungsListe";
import type { PersonOption } from "./VisibilitySelector";
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
 * - Beziehungen
 */

type Unteransicht = "uebersicht" | "blatt" | "gegenstaende" | "augments" | "beschreibung" | "notizen" | "beziehungen";

interface PCDetailProps {
  campaignId: string;
  person: Person;
  spielerName?: string;
  verbindungen: Verbindung[];
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  onSchliessen: () => void;
  onGeaendert: () => void;
  /** Patcht ein Feld (z.B. description) direkt in der Elternliste, ohne
   * neu zu laden — behebt, dass nach Autosave+Schließen+Wiederöffnen der
   * alte Stand aus der ungeänderten Liste kam. Siehe shell/autosave.ts. */
  onLokalAktualisiert?: (felder: Partial<Person>) => void;
}

export function PCDetail({
  campaignId,
  person,
  spielerName,
  verbindungen,
  namen,
  pcOptions,
  onSchliessen,
  onGeaendert,
  onLokalAktualisiert,
}: PCDetailProps) {
  const [unteransicht, setUnteransicht] = useState<Unteransicht>("uebersicht");
  const [beschreibungDoc, setBeschreibungDoc] = useState<JSONContent>(parseRichText(person.description));
  const [notizenDoc, setNotizenDoc] = useState<JSONContent>(parseRichText(person.notes));

  // Vorgefertigt-Checkbox + Zu-NPC-Knopf sofort nach dem Umschalten zeigen,
  // ohne auf den nächsten Reload der Liste zu warten (dasselbe Muster wie
  // NPCDetail::aktuellePerson).
  const [aktuellePerson, setAktuellePerson] = useState(person);
  useEffect(() => {
    setAktuellePerson(person);
  }, [person]);
  const [zuNpcOffen, setZuNpcOffen] = useState(false);
  const [zuNpcLaeuft, setZuNpcLaeuft] = useState(false);
  const [loeschenOffen, setLoeschenOffen] = useState(false);
  const [loeschenLaeuft, setLoeschenLaeuft] = useState(false);

  async function vorgefertigtUmschalten(wert: boolean) {
    const neu = await entitiesApi.updatePerson(campaignId, person.id, { istVorgefertigt: wert });
    setAktuellePerson(neu);
    onGeaendert();
  }

  async function zuNpcMachen() {
    setZuNpcLaeuft(true);
    try {
      await entitiesApi.personZuNpc(campaignId, person.id);
      setZuNpcOffen(false);
      onGeaendert();
      onSchliessen();
    } finally {
      setZuNpcLaeuft(false);
    }
  }

  async function loeschen() {
    setLoeschenLaeuft(true);
    try {
      await entitiesApi.deletePerson(campaignId, person.id);
      setLoeschenOffen(false);
      onGeaendert();
      onSchliessen();
    } finally {
      setLoeschenLaeuft(false);
    }
  }

  const beziehungsZahl = beziehungsZeilen(person.id, verbindungen, namen).length;

  // Autosave still — kein onGeaendert, sonst unmountet das Popup (siehe autosave.ts).
  // onLokalAktualisiert hält die Elternliste synchron, damit ein
  // Schließen+Wiederöffnen den frischen Text zeigt statt des alten Caches.
  const autosaveBeschreibung = useAutosave(async (doc: JSONContent) => {
    const description = serializeRichText(doc);
    await entitiesApi.updatePerson(campaignId, person.id, { description });
    onLokalAktualisiert?.({ description });
  });
  const autosaveNotizen = useAutosave(async (doc: JSONContent) => {
    const notes = serializeRichText(doc);
    await entitiesApi.updatePerson(campaignId, person.id, { notes });
    onLokalAktualisiert?.({ notes });
  });

  return (
    <>
    <Fenster
      offen
      breit={unteransicht === "blatt" || unteransicht === "gegenstaende" || unteransicht === "augments" || unteransicht === "beziehungen"}
      titel={anzeigeName(person.name, person.alias)}
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
            className={unteransicht === "augments" ? "pcd-nav-aktiv" : ""}
            onClick={() => setUnteransicht("augments")}
          >
            Augments
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
          <button
            type="button"
            className={unteransicht === "beziehungen" ? "pcd-nav-aktiv" : ""}
            onClick={() => setUnteransicht("beziehungen")}
          >
            Beziehungen ({beziehungsZahl})
          </button>
        </nav>

        {/* Inhalt */}
        <div className="pcd-bereich">
          {unteransicht === "uebersicht" && (
            <div className="pcd-uebersicht">
              <div className="pcd-bild-bereich">
                <BildGalerie
                  campaignId={campaignId}
                  art="personen"
                  id={person.id}
                  name={person.name}
                  beschreibung={person.description}
                  notizen={person.notes}
                  bilder={person.bilder || []}
                  bildUrl={person.bildUrl}
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
                  <label className="pcd-vorgefertigt-checkbox">
                    <input
                      type="checkbox"
                      checked={aktuellePerson.istVorgefertigt ?? false}
                      onChange={(e) => vorgefertigtUmschalten(e.target.checked)}
                    />
                    Vorgefertigter Charakter (im Ersteinstieg für Spieler wählbar)
                  </label>
                  <button type="button" onClick={() => setZuNpcOffen(true)}>
                    ⇄ Zu NPC machen
                  </button>
                  <button
                    type="button"
                    onClick={() => setLoeschenOffen(true)}
                    style={{ color: "var(--signal)", borderColor: "var(--signal)" }}
                  >
                    🗑 PC löschen
                  </button>
                </div>
              </div>
            </div>
          )}

          {unteransicht === "blatt" && (
            <Charakterblatt campaignId={campaignId} personId={person.id} bearbeitbar />
          )}

          {unteransicht === "gegenstaende" && (
            <PCInventar
              campaignId={campaignId}
              personId={person.id}
              personName={person.name}
            />
          )}

          {unteransicht === "augments" && (
            <AugmentsAnsicht
              campaignId={campaignId}
              eigenePersonId={person.id}
            />
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
                kiKontext={{ campaignId, objektTyp: "Person", objektName: person.name, feldLabel: "Beschreibung" }}
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
                kiKontext={{ campaignId, objektTyp: "Person", objektName: person.name, feldLabel: "Notizen" }}
              />
            </div>
          )}

          {unteransicht === "beziehungen" && (
            <BeziehungsTab
              campaignId={campaignId}
              eigenKind="Person"
              eigenId={person.id}
              eigenName={person.name}
              verbindungen={verbindungen}
              namen={namen}
              pcOptions={pcOptions}
              typVorschlaege={PERSON_TYP_VORSCHLAEGE}
              farbe="var(--bereich-pcs)"
              onGeaendert={onGeaendert}
            />
          )}
        </div>
      </div>
    </Fenster>

      {zuNpcOffen && (
        <Bestaetigung
          titel={`${person.name} zum NPC machen?`}
          text={
            spielerName
              ? `${spielerName} spielt diesen Charakter gerade — die Zuordnung wird gelöst, ${spielerName} sieht danach wieder den Ersteinstieg. Inventar, Charakterbogen und Beziehungen bleiben vollständig erhalten.`
              : `Wird in-place zum NPC — Inventar, Charakterbogen und Beziehungen bleiben vollständig erhalten. Kann jederzeit im NPC-Detail wieder zu einem PC gemacht werden.`
          }
          jaText={zuNpcLaeuft ? "..." : "Zu NPC machen"}
          onJa={zuNpcMachen}
          onNein={() => setZuNpcOffen(false)}
        />
      )}
      {loeschenOffen && (
        <Bestaetigung
          titel={`${person.name} löschen?`}
          text={
            spielerName
              ? `${spielerName} spielt diesen Charakter. Die Figur wird endgültig gelöscht, samt Inventar und Verbindungen. ${spielerName} sieht danach wieder den Ersteinstieg. Das lässt sich nicht rückgängig machen.`
              : `„${person.name}“ wird endgültig gelöscht, samt Inventar und ${beziehungsZahl} Verbindungen. Das lässt sich nicht rückgängig machen.`
          }
          jaText={loeschenLaeuft ? "..." : "Ja, löschen"}
          neinText="Abbrechen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </>
  );
}
