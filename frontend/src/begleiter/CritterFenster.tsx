import { useEffect, useState } from "react";
import { entitiesApi, type Person } from "../entities/api";
import { EntitaetsBild } from "../entities/EntitaetsBild";
import { parseRichText, serializeRichText } from "../richtext/content";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { Charakterblatt } from "../traits/Charakterblatt";
import "../entities/pc-detail.css";

/**
 * Critter-Fenster in der Begleiter-Übersicht.
 *
 * Critter sind seit 20.09.2026 echte NPCs (`Person`, `istCritter=true`,
 * Mark: "wir machen critter zu richtigen NPCs") — dieses Fenster ist die
 * schlanke Variante von `entities/NPCDetail.tsx` für den Begleiter-Bereich:
 * volles Charakterblatt (Attribute 1-6, Fertigkeiten 1-5, dieselbe Erstellung
 * wie jeder andere NPC), Bild, Beschreibung, Verbindung zu seinem Menschen.
 * Bewusst ohne Gegenstände/Augments/Beziehungen-Tab — kann bei Bedarf später
 * ergänzt werden, das volle `NPCDetail` bleibt im NPC-Bereich weiter nutzbar
 * für alles darüber hinaus.
 *
 * Lädt die volle `Person` selbst (die Begleiter-Übersicht kennt nur die
 * schlanken Felder aus `entitiesApi.listCritter`), damit `Charakterblatt`
 * und der Beschreibungs-Editor ihre Daten haben.
 */

type Unteransicht = "blatt" | "beschreibung";

export function CritterFenster({
  campaignId,
  critterId,
  besitzerId,
  personen,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  critterId: string;
  /** Aktueller Besitzer (aus der Critter-Liste). */
  besitzerId: string | null;
  /** Für die Besitzer-Auswahl — wer ist der Mensch dieses Critters. */
  personen: { id: string; label: string }[];
  onSchliessen: () => void;
  onGeaendert: () => void;
}) {
  const [person, setPerson] = useState<Person | null>(null);
  const [unteransicht, setUnteransicht] = useState<Unteransicht>("blatt");
  const [beschreibungDoc, setBeschreibungDoc] = useState(parseRichText(""));
  const [besitzerSuche, setBesitzerSuche] = useState("");
  const [speichert, setSpeichert] = useState(false);
  const [loeschenOffen, setLoeschenOffen] = useState(false);

  useEffect(() => {
    entitiesApi.getPerson(campaignId, critterId).then((p) => {
      setPerson(p);
      setBeschreibungDoc(parseRichText(p.description));
    });
  }, [campaignId, critterId]);

  async function beschreibungSpeichern() {
    setSpeichert(true);
    try {
      await entitiesApi.updatePerson(campaignId, critterId, {
        description: serializeRichText(beschreibungDoc),
      });
      onGeaendert();
    } finally {
      setSpeichert(false);
    }
  }

  async function loeschen() {
    setLoeschenOffen(false);
    await entitiesApi.deletePerson(campaignId, critterId);
    onGeaendert();
  }

  const besitzerGefiltert = personen.filter((p) =>
    p.label.toLowerCase().includes(besitzerSuche.trim().toLowerCase()),
  );

  if (!person) return null;

  return (
    <Fenster
      offen
      breit
      titel={`❖ ${person.name}`}
      unterzeile="Critter — volles NPC-Charakterblatt"
      kennung={`critter-detail:${critterId}`}
      onSchliessen={onSchliessen}
    >
      <div className="pcd-inhalt">
        <nav className="pcd-nav">
          <button
            type="button"
            className={unteransicht === "blatt" ? "pcd-nav-aktiv" : ""}
            onClick={() => setUnteransicht("blatt")}
          >
            Charakterblatt
          </button>
          <button
            type="button"
            className={unteransicht === "beschreibung" ? "pcd-nav-aktiv" : ""}
            onClick={() => setUnteransicht("beschreibung")}
          >
            Beschreibung
          </button>
        </nav>

        <div className="pcd-bereich">
          {unteransicht === "blatt" && (
            <>
              <EntitaetsBild
                campaignId={campaignId}
                art="personen"
                id={critterId}
                name={person.name}
                bildUrl={person.bildUrl ?? ""}
                onGeaendert={onGeaendert}
              />
              <Charakterblatt campaignId={campaignId} personId={critterId} bearbeitbar />
            </>
          )}

          {unteransicht === "beschreibung" && (
            <div className="pcd-editor-bereich">
              <RichTextEditor content={beschreibungDoc} onChange={setBeschreibungDoc} minHeight={200} />
              <button type="button" className="pcd-speichern" onClick={beschreibungSpeichern} disabled={speichert}>
                {speichert ? "Speichert…" : "Beschreibung speichern"}
              </button>
            </div>
          )}

          <section style={{ borderTop: "1px solid var(--linie)", paddingTop: 10, marginTop: 10 }}>
            <h3 style={{ margin: "0 0 6px" }}>Verwaltung</h3>
            <span
              style={{
                display: "block",
                fontSize: 11,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                color: "var(--neon)",
                marginBottom: 4,
              }}
            >
              Verbindung
            </span>
            <div className="bg-zeile" style={{ flexDirection: "column", alignItems: "stretch", gap: 4 }}>
              <input
                type="search"
                className="bg-suchfeld"
                placeholder="Besitzer suchen…"
                value={besitzerSuche}
                onChange={(e) => setBesitzerSuche(e.target.value)}
              />
              <div className="bg-auswahl-liste">
                <label className="bg-auswahl-zeile">
                  <input
                    type="radio"
                    name="critter-besitzer"
                    checked={!besitzerId}
                    onChange={async () => {
                      await entitiesApi.critterBesitzer(campaignId, critterId, null);
                      onGeaendert();
                    }}
                  />
                  <span>— ungebunden —</span>
                </label>
                {besitzerGefiltert.map((p) => (
                  <label key={p.id} className="bg-auswahl-zeile">
                    <input
                      type="radio"
                      name="critter-besitzer"
                      checked={besitzerId === p.id}
                      onChange={async () => {
                        await entitiesApi.critterBesitzer(campaignId, critterId, p.id);
                        onGeaendert();
                      }}
                    />
                    <span>{p.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="bg-zeile" style={{ marginTop: 10 }}>
              <button
                type="button"
                style={{ borderColor: "var(--signal)", color: "var(--signal)" }}
                onClick={() => setLoeschenOffen(true)}
              >
                Entfernen
              </button>
            </div>
          </section>
        </div>
      </div>

      {loeschenOffen && (
        <Bestaetigung
          titel={`${person.name} entfernen?`}
          text="Der Critter wird endgültig gelöscht, samt Charakterblatt."
          jaText="Entfernen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </Fenster>
  );
}
