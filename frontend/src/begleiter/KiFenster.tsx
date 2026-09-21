import { useEffect, useState } from "react";
import { entitiesApi, type EinflussEintrag, type Person } from "../entities/api";
import { EntitaetsBild } from "../entities/EntitaetsBild";
import { EinflussVerwaltung } from "../entities/EinflussVerwaltung";
import { parseRichText, serializeRichText } from "../richtext/content";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { Charakterblatt } from "../traits/Charakterblatt";
import "../entities/pc-detail.css";
import "./begleiter.css";

/**
 * KI-Fenster in der Begleiter-Übersicht.
 *
 * KI ist seit 20.09.2026 (revidiert) eine echte Person (`istKI=true`,
 * Mark: "mach jetzt das Gleiche für die KI") — dasselbe Muster wie
 * `CritterFenster.tsx`: volles Charakterblatt statt eines eigenen
 * Begleiter-Blatts, hier zusätzlich um Einfluss-Verwaltung (Orte/Fraktionen/
 * Events/Gegenstände) ergänzt, die es nur bei KIs sinnvoll gibt.
 *
 * Körperliche Attribute ergeben für eine körperlose KI keinen Sinn — das
 * Charakterblatt selbst blendet sie bereits aus (`bogen.person.istKI`,
 * siehe `traits/Charakterblatt.tsx`) und zeigt stattdessen Matrix-Präsenz.
 */

type Unteransicht = "blatt" | "beschreibung";

export function KiFenster({
  campaignId,
  kiId,
  besitzerId,
  personen,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  kiId: string;
  /** Aktueller Besitzer (aus der KI-Liste) — z.B. der Neuroweaver, der sie geschrieben hat. */
  besitzerId: string | null;
  /** Für die Besitzer-Auswahl. */
  personen: { id: string; label: string }[];
  onSchliessen: () => void;
  onGeaendert: () => void;
}) {
  const [person, setPerson] = useState<Person | null>(null);
  const [einfluss, setEinfluss] = useState<EinflussEintrag[]>([]);
  const [unteransicht, setUnteransicht] = useState<Unteransicht>("blatt");
  const [beschreibungDoc, setBeschreibungDoc] = useState(parseRichText(""));
  const [besitzerSuche, setBesitzerSuche] = useState("");
  const [speichert, setSpeichert] = useState(false);
  const [loeschenOffen, setLoeschenOffen] = useState(false);

  useEffect(() => {
    entitiesApi.getPerson(campaignId, kiId).then((p) => {
      setPerson(p);
      setBeschreibungDoc(parseRichText(p.description));
    });
    entitiesApi.einflussListe(campaignId, kiId).then(setEinfluss);
  }, [campaignId, kiId]);

  async function beschreibungSpeichern() {
    setSpeichert(true);
    try {
      await entitiesApi.updatePerson(campaignId, kiId, {
        description: serializeRichText(beschreibungDoc),
      });
      onGeaendert();
    } finally {
      setSpeichert(false);
    }
  }

  async function loeschen() {
    setLoeschenOffen(false);
    await entitiesApi.deletePerson(campaignId, kiId);
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
      titel={`⌬ ${person.name}`}
      unterzeile="KI — volles Charakterblatt mit Matrix-Präsenz"
      kennung={`ki-detail:${kiId}`}
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
                id={kiId}
                name={person.name}
                bildUrl={person.bildUrl ?? ""}
                onGeaendert={onGeaendert}
              />
              <Charakterblatt campaignId={campaignId} personId={kiId} bearbeitbar />
              <EinflussVerwaltung
                campaignId={campaignId}
                personId={kiId}
                einfluss={einfluss}
                onGeaendert={setEinfluss}
              />
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
                    name="ki-besitzer"
                    checked={!besitzerId}
                    onChange={async () => {
                      await entitiesApi.kiBesitzer(campaignId, kiId, null);
                      onGeaendert();
                    }}
                  />
                  <span>— ungebunden —</span>
                </label>
                {besitzerGefiltert.map((p) => (
                  <label key={p.id} className="bg-auswahl-zeile">
                    <input
                      type="radio"
                      name="ki-besitzer"
                      checked={besitzerId === p.id}
                      onChange={async () => {
                        await entitiesApi.kiBesitzer(campaignId, kiId, p.id);
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
          text="Die KI wird endgültig gelöscht, samt Charakterblatt und Einfluss-Verknüpfungen."
          jaText="Entfernen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </Fenster>
  );
}
