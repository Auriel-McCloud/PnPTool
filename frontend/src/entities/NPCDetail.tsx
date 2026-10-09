import { useEffect, useState } from "react";
import type { EntityKind, Person, Verbindung } from "./api";
import { anzeigeName } from "./api";
import { EntitaetsBild } from "./EntitaetsBild";
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
import { HaendlerEinstellungenFenster } from "../haendler/HaendlerEinstellungenFenster";
import { HaendlerBearbeiten } from "../haendler/HaendlerBearbeiten";
import { haendlerApi } from "../haendler/api";
import "./pc-detail.css"; // Selbes Styling wie PCs

/**
 * Detail-Popup für einen NPC.
 *
 * Zeigt Übersicht mit Bild und bietet Zugang zu:
 * - Charakterblatt
 * - Gegenstände
 * - Augments
 * - Beschreibung
 * - Notizen
 * - Beziehungen
 */

type Unteransicht = "uebersicht" | "blatt" | "gegenstaende" | "augments" | "beschreibung" | "notizen" | "beziehungen";

interface NPCDetailProps {
  campaignId: string;
  person: Person;
  verbindungen: Verbindung[];
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  onSchliessen: () => void;
  onGeaendert: () => void;
}

export function NPCDetail({
  campaignId,
  person,
  verbindungen,
  namen,
  pcOptions,
  onSchliessen,
  onGeaendert,
}: NPCDetailProps) {
  const [unteransicht, setUnteransicht] = useState<Unteransicht>("uebersicht");
  const [beschreibungDoc, setBeschreibungDoc] = useState<JSONContent>(parseRichText(person.description));
  const [notizenDoc, setNotizenDoc] = useState<JSONContent>(parseRichText(person.notes));

  // Händler-Flag (istHaendler) sofort nach dem Umschalten im Popup zeigen,
  // ohne auf den nächsten Reload der Liste zu warten — dasselbe Muster wie
  // BegleiterFenster::onSofortGeaendert, nötig weil EntityManager den
  // npcDetailFuer-Prop nach refreshAll() nicht automatisch erneuert.
  const [aktuellePerson, setAktuellePerson] = useState(person);
  useEffect(() => {
    setAktuellePerson(person);
  }, [person]);
  const [haendlerEinstellungenOffen, setHaendlerEinstellungenOffen] = useState(false);
  const [sortimentOffen, setSortimentOffen] = useState(false);
  const [zuPcOffen, setZuPcOffen] = useState(false);
  const [zuPcLaeuft, setZuPcLaeuft] = useState(false);
  // Shop hängt seit 04.10. am ORT, nicht an der Person (siehe
  // haendler/repository.py) — "haendlerId" für HaendlerBearbeiten/-api ist
  // also die Ort-id des Ladens, den diese Person betreibt, NICHT die
  // Person-id selbst. Ohne Auflösung hier würde HaendlerBearbeiten mit
  // person.id als Shop-id anfragen und 404en (gefunden 05.10.2026 beim Bau
  // des "Ort zu einem Laden machen"-Knopfs — nie im Browser angeklickt,
  // nur tsc -b geprüft, daher unbemerkt).
  const [ladenOrtId, setLadenOrtId] = useState<string | null>(null);
  const istHaendler = aktuellePerson.istHaendler ?? false;

  async function sortimentOeffnen() {
    const shops = await haendlerApi.alle(campaignId);
    const shop = shops.find((s) => s.haendler.some((h: { id: string }) => h.id === person.id));
    setLadenOrtId(shop?.id ?? null);
    setSortimentOffen(true);
  }

  async function zuPcMachen() {
    setZuPcLaeuft(true);
    try {
      await entitiesApi.personZuPc(campaignId, person.id);
      setZuPcOffen(false);
      onGeaendert();
      onSchliessen();
    } finally {
      setZuPcLaeuft(false);
    }
  }

  const beziehungsZahl = beziehungsZeilen(person.id, verbindungen, namen).length;

  // Autosave still — kein onGeaendert, sonst unmountet das Popup (siehe autosave.ts).
  const autosaveBeschreibung = useAutosave(async (doc: JSONContent) => {
    await entitiesApi.updatePerson(campaignId, person.id, { description: serializeRichText(doc) });
  });
  const autosaveNotizen = useAutosave(async (doc: JSONContent) => {
    await entitiesApi.updatePerson(campaignId, person.id, { notes: serializeRichText(doc) });
  });

  return (
    <>
    <Fenster
      offen
      breit={unteransicht === "blatt" || unteransicht === "gegenstaende" || unteransicht === "augments" || unteransicht === "beziehungen"}
      titel={anzeigeName(person.name, person.alias)}
      unterzeile="NPC"
      kennung={`npc-detail:${person.id}`}
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
                <EntitaetsBild
                  campaignId={campaignId}
                  art="personen"
                  id={person.id}
                  name={person.name}
                  bildUrl={person.bildUrl ?? ""}
                  beschreibung={person.description}
                  notizen={person.notes}
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
                  {istHaendler ? (
                    <>
                      <button type="button" onClick={sortimentOeffnen}>
                        🛒 Sortiment &amp; Shop bearbeiten
                      </button>
                      <button type="button" onClick={() => setHaendlerEinstellungenOffen(true)}>
                        ⚙ Händler-Einstellungen
                      </button>
                    </>
                  ) : (
                    <button type="button" onClick={() => setHaendlerEinstellungenOffen(true)}>
                      🛒 Zum Händler machen
                    </button>
                  )}
                  <button type="button" onClick={() => setZuPcOffen(true)}>
                    ⇄ Zu PC machen
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
              farbe="var(--bereich-npcs)"
              onGeaendert={onGeaendert}
            />
          )}
        </div>
      </div>

      {haendlerEinstellungenOffen && (
        <HaendlerEinstellungenFenster
          campaignId={campaignId}
          person={aktuellePerson}
          offen={haendlerEinstellungenOffen}
          onSchliessen={() => setHaendlerEinstellungenOffen(false)}
          onGeaendert={(neu) => {
            setAktuellePerson(neu);
            onGeaendert();
          }}
        />
      )}

      {sortimentOffen && ladenOrtId && (
        <HaendlerBearbeiten
          campaignId={campaignId}
          haendlerId={ladenOrtId}
          offen={sortimentOffen}
          onSchliessen={() => setSortimentOffen(false)}
          onGeaendert={onGeaendert}
        />
      )}
    </Fenster>

      {zuPcOffen && (
        <Bestaetigung
          titel={`${person.name} zum PC machen?`}
          text="Wird in-place zum PC — Inventar, Charakterbogen und Beziehungen bleiben vollständig erhalten. Händler-Status, Critter- und KI-Markierung gehen dabei verloren (ergeben an einem PC keinen Sinn). Kann jederzeit im PC-Detail wieder zu einem NPC gemacht werden."
          jaText={zuPcLaeuft ? "..." : "Zu PC machen"}
          onJa={zuPcMachen}
          onNein={() => setZuPcOffen(false)}
        />
      )}
    </>
  );
}
