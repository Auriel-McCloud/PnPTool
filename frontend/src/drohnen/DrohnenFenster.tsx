import { useEffect, useState } from "react";
import { entitiesApi, type Person } from "../entities/api";
import { anzeigeName } from "../entities/api";
import { EntitaetsBild } from "../entities/EntitaetsBild";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { Charakterblatt } from "../traits/Charakterblatt";
import { drohnenApi } from "./api";
import { DrohnenSteigern } from "./DrohnenSteigern";
import "../entities/pc-detail.css";

/**
 * Drohnen-/Fahrzeug-Fenster — Pendant zu `begleiter/CritterFenster.tsx`.
 *
 * Volles Charakterblatt (eigene 2-Spalten-Attribute, siehe
 * `traits/bogenApi.ts::ATTRIBUT_KATEGORIEN_DROHNE`), Nuyen-Käufe statt
 * EP-LevelUp, Rigger-Bindung statt Critter-Besitzer, Aktiv-Schalter statt
 * eines reinen Anzeige-Felds.
 *
 * `istGm=false` (Spieler, nur die eigene gebundene Drohne/das eigene
 * Fahrzeug erreicht dieses Fenster überhaupt, serverseitig durchgesetzt):
 * zeigt Charakterblatt + Nuyen-Kauf + Aktiv-Schalter, blendet
 * Rigger-Zuweisung und Löschen aus — das bleibt SL-Sache.
 */
type Unteransicht = "blatt" | "kaufen";

export function DrohnenFenster({
  campaignId,
  drohneId,
  riggerId,
  riggerAktiv,
  personen,
  istGm,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  drohneId: string;
  riggerId: string | null;
  riggerAktiv: boolean;
  /** Für die Rigger-Auswahl (nur SL) — alle Menschen der Kampagne. */
  personen: { id: string; label: string }[];
  istGm: boolean;
  onSchliessen: () => void;
  onGeaendert: () => void;
}) {
  const [person, setPerson] = useState<Person | null>(null);
  const [unteransicht, setUnteransicht] = useState<Unteransicht>("blatt");
  const [riggerSuche, setRiggerSuche] = useState("");
  const [loeschenOffen, setLoeschenOffen] = useState(false);
  const [aktivLaeuft, setAktivLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  // Remount-Zähler fürs Charakterblatt, wenn ein Nuyen-Kauf den Bogen
  // ändert — dasselbe Muster wie bei CritterFenster (key wechselt).
  const [blattVersion, setBlattVersion] = useState(0);

  useEffect(() => {
    entitiesApi.getPerson(campaignId, drohneId).then(setPerson);
  }, [campaignId, drohneId]);

  async function aktivUmschalten() {
    setAktivLaeuft(true);
    setFehler(null);
    try {
      await drohnenApi.aktivSetzen(campaignId, drohneId, !riggerAktiv);
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht umgeschaltet werden.");
    } finally {
      setAktivLaeuft(false);
    }
  }

  async function loeschen() {
    setLoeschenOffen(false);
    await entitiesApi.deletePerson(campaignId, drohneId);
    onGeaendert();
  }

  const riggerGefiltert = personen.filter((p) => p.label.toLowerCase().includes(riggerSuche.trim().toLowerCase()));
  const riggerName = personen.find((p) => p.id === riggerId)?.label ?? null;

  if (!person) return null;

  const art = person.istFahrzeug ? "Fahrzeug" : "Drohne";

  return (
    <Fenster
      offen
      breit
      titel={`⛭ ${anzeigeName(person.name, person.alias)}`}
      unterzeile={`${art} — ${riggerAktiv ? "aktiv verbunden" : "nicht verbunden"}`}
      kennung={`drohne-detail:${drohneId}`}
      ton="var(--bereich-begleiter)"
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
            className={unteransicht === "kaufen" ? "pcd-nav-aktiv" : ""}
            onClick={() => setUnteransicht("kaufen")}
          >
            Nuyen ausgeben
          </button>
        </nav>

        <div className="pcd-bereich">
          {unteransicht === "blatt" && (
            <>
              <EntitaetsBild
                campaignId={campaignId}
                art="personen"
                id={drohneId}
                name={person.name}
                bildUrl={person.bildUrl ?? ""}
                beschreibung={person.description}
                notizen={person.notes}
                onGeaendert={onGeaendert}
              />
              <Charakterblatt key={`${drohneId}-${blattVersion}`} campaignId={campaignId} personId={drohneId} bearbeitbar={istGm} />
            </>
          )}

          {unteransicht === "kaufen" && (
            <DrohnenSteigern
              campaignId={campaignId}
              drohneId={drohneId}
              onGeaendert={() => setBlattVersion((v) => v + 1)}
            />
          )}

          {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}

          <section style={{ borderTop: "1px solid var(--linie)", paddingTop: 10, marginTop: 10 }}>
            <h3 style={{ margin: "0 0 6px" }}>Riggerkonsole</h3>
            <div className="bg-zeile">
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.9em" }}>
                <input
                  type="checkbox"
                  checked={riggerAktiv}
                  disabled={aktivLaeuft || !riggerId}
                  onChange={aktivUmschalten}
                />
                {riggerAktiv ? "Verbunden — nimmt am Kampf teil" : "Nicht verbunden — kein Kampfteilnehmer"}
              </label>
            </div>
            {!riggerId && <p style={{ fontSize: 12, color: "var(--text-leise)", margin: "4px 0 0" }}>Ohne Rigger nicht aktivierbar.</p>}
          </section>

          {istGm ? (
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
                Rigger
              </span>
              <div className="bg-zeile" style={{ flexDirection: "column", alignItems: "stretch", gap: 4 }}>
                <input
                  type="search"
                  className="bg-suchfeld"
                  placeholder="Rigger suchen…"
                  value={riggerSuche}
                  onChange={(e) => setRiggerSuche(e.target.value)}
                />
                <div className="bg-auswahl-liste">
                  <label className="bg-auswahl-zeile">
                    <input
                      type="radio"
                      name="drohnen-rigger"
                      checked={!riggerId}
                      onChange={async () => {
                        await drohnenApi.riggerSetzen(campaignId, drohneId, null);
                        onGeaendert();
                      }}
                    />
                    <span>— ungebunden —</span>
                  </label>
                  {riggerGefiltert.map((p) => (
                    <label key={p.id} className="bg-auswahl-zeile">
                      <input
                        type="radio"
                        name="drohnen-rigger"
                        checked={riggerId === p.id}
                        onChange={async () => {
                          await drohnenApi.riggerSetzen(campaignId, drohneId, p.id);
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
          ) : (
            riggerName && (
              <p style={{ fontSize: 12, color: "var(--text-leise)", marginTop: 10 }}>Rigger: {riggerName}</p>
            )
          )}
        </div>
      </div>

      {loeschenOffen && (
        <Bestaetigung
          titel={`${person.name} entfernen?`}
          text={`Die ${art.toLowerCase()} wird endgültig gelöscht, samt Charakterblatt.`}
          jaText="Entfernen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </Fenster>
  );
}
