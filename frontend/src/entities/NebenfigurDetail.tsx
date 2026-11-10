import { useEffect, useState, type FormEvent } from "react";
import type { JSONContent } from "@tiptap/react";
import type { EntityKind, Nebenfaehigkeit, Person, Verbindung } from "./api";
import { anzeigeName, entitiesApi } from "./api";
import { BildGalerie } from "./BildGalerie";
import { BeziehungsTab, PERSON_TYP_VORSCHLAEGE } from "./BeziehungsTab";
import { beziehungsZeilen } from "./BeziehungsListe";
import type { PersonOption } from "./VisibilitySelector";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { useAutosave } from "../shell/autosave";
import { parseRichText, serializeRichText } from "../richtext/content";
import { rassenApi } from "../rassen/api";
import { haendlerApi } from "../haendler/api";
import "./pc-detail.css";
import "./nebenfiguren.css";

/**
 * Detail-Popup einer Nebenfigur (10.11.2026, Marks Konzept).
 *
 * Kein Charakterbogen, kein Inventar, kein Kampf — nur Steckbrief (Name,
 * Rasse, Alter, Persönlichkeit), freie feste Fähigkeiten, Bilder,
 * Beschreibung, Notizen und Beziehungen. „Zu NPC machen“ ist eine
 * Einbahnstraße: die KI baut einen vollen Bogen, zurück geht es nicht.
 */

type Unteransicht = "uebersicht" | "beschreibung" | "notizen" | "beziehungen";

/** Bearbeitungs-Popup einer Fähigkeit: index null = neu anlegen. */
interface FaehigkeitEntwurf {
  index: number | null;
  name: string;
  wert: string;
}

export function NebenfigurDetail({
  campaignId,
  person,
  verbindungen,
  namen,
  pcOptions,
  onSchliessen,
  onGeaendert,
  onLokalAktualisiert,
}: {
  campaignId: string;
  person: Person;
  verbindungen: Verbindung[];
  namen: Map<string, { name: string; kind: EntityKind }>;
  pcOptions: PersonOption[];
  onSchliessen: () => void;
  onGeaendert: () => void;
  onLokalAktualisiert?: (felder: Partial<Person>) => void;
}) {
  const [unteransicht, setUnteransicht] = useState<Unteransicht>("uebersicht");
  const [name, setName] = useState(person.name);
  const [alter, setAlter] = useState(person.alter ?? "");
  const [persoenlichkeit, setPersoenlichkeit] = useState(person.persoenlichkeit ?? "");
  const [rasse, setRasse] = useState(person.rasse ?? "");
  const [faehigkeiten, setFaehigkeiten] = useState<Nebenfaehigkeit[]>(person.nebenfaehigkeiten ?? []);
  const [beschreibungDoc, setBeschreibungDoc] = useState<JSONContent>(parseRichText(person.description));
  const [notizenDoc, setNotizenDoc] = useState<JSONContent>(parseRichText(person.notes));
  const [rassen, setRassen] = useState<string[]>([]);
  // Händler-Gesicht (10.11.2026, Mark: „nicht jeder Händler braucht ein
  // Charakterblatt“) — Ware und Shop hängen am Ort, hier nur die Reparatur-Flagge.
  const [bietetReparatur, setBietetReparatur] = useState(person.bietetReparatur ?? false);
  const [istHaendler, setIstHaendler] = useState(person.istHaendler ?? false);
  // Laden, an dem sie verkauft — der Shop hängt am Ort (BETREIBT-Kante).
  const [laden, setLaden] = useState<{ ortId: string; ortName: string } | null>(null);
  const [ladenWahlOffen, setLadenWahlOffen] = useState(false);
  const [ladenOrte, setLadenOrte] = useState<{ id: string; name: string; istShop: boolean }[]>([]);
  const [ladenOrtId, setLadenOrtId] = useState("");
  const [abziehenOffen, setAbziehenOffen] = useState(false);

  const [entwurf, setEntwurf] = useState<FaehigkeitEntwurf | null>(null);
  const [entfernenIndex, setEntfernenIndex] = useState<number | null>(null);
  const [zuNpcOffen, setZuNpcOffen] = useState(false);
  const [zuNpcLaeuft, setZuNpcLaeuft] = useState(false);
  const [loeschenOffen, setLoeschenOffen] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    rassenApi
      .verfuegbar(campaignId)
      .then((liste) => setRassen(liste.map((r) => r.name)))
      .catch(() => setRassen([]));
  }, [campaignId]);

  useEffect(() => {
    if (!istHaendler) {
      setLaden(null);
      return;
    }
    Promise.all([haendlerApi.alle(campaignId), haendlerApi.tutorial(campaignId).catch(() => null)])
      .then(([shops, tutorial]) => {
        const alle = tutorial ? [...shops, tutorial] : shops;
        const treffer = alle.find((s) => s.haendler.some((h) => h.id === person.id));
        setLaden(treffer?.ortId ? { ortId: treffer.ortId, ortName: treffer.ortName ?? treffer.name } : null);
      })
      .catch(() => setLaden(null));
  }, [campaignId, person.id, istHaendler]);

  async function ladenWahlOeffnen() {
    setLadenOrtId(laden?.ortId ?? "");
    setLadenWahlOffen(true);
    try {
      const orte = await entitiesApi.listOrte(campaignId);
      setLadenOrte(orte.map((o) => ({ id: o.id, name: o.name, istShop: Boolean(o.istShop) })));
    } catch {
      setLadenOrte([]);
    }
  }

  async function anLadenStellen(e: FormEvent) {
    e.preventDefault();
    if (!ladenOrtId) return;
    setFehler(null);
    try {
      if (!istHaendler) await entitiesApi.updatePerson(campaignId, person.id, { istHaendler: true });
      // Setzt am Ort istShop — ein normaler Ort wird dabei zum Laden.
      await haendlerApi.standortSetzen(campaignId, person.id, ladenOrtId);
      const ort = ladenOrte.find((o) => o.id === ladenOrtId);
      setIstHaendler(true);
      setLaden({ ortId: ladenOrtId, ortName: ort?.name ?? "" });
      setLadenWahlOffen(false);
      onLokalAktualisiert?.({ istHaendler: true });
    } catch (err) {
      setFehler(err instanceof Error ? err.message : "Laden setzen fehlgeschlagen");
    }
  }

  async function vomLadenNehmen() {
    setAbziehenOffen(false);
    setFehler(null);
    try {
      await haendlerApi.standortSetzen(campaignId, person.id, null);
      await entitiesApi.updatePerson(campaignId, person.id, { istHaendler: false });
      setIstHaendler(false);
      setLaden(null);
      onLokalAktualisiert?.({ istHaendler: false });
    } catch (err) {
      setFehler(err instanceof Error ? err.message : "Vom Laden nehmen fehlgeschlagen");
    }
  }

  const beziehungsZahl = beziehungsZeilen(person.id, verbindungen, namen).length;

  async function speichern(felder: Partial<Person>) {
    setFehler(null);
    try {
      await entitiesApi.updatePerson(campaignId, person.id, felder);
      onLokalAktualisiert?.(felder);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
    }
  }

  // Autosave still — kein onGeaendert, sonst unmountet das Popup (siehe autosave.ts).
  const autosaveName = useAutosave(async (roh: string) => {
    const sauber = roh.trim();
    if (!sauber || sauber === person.name) return;
    await speichern({ name: sauber });
  });
  const autosaveAlter = useAutosave((wert: string) => speichern({ alter: wert.trim() }));
  const autosavePersoenlichkeit = useAutosave((wert: string) => speichern({ persoenlichkeit: wert.trim() }));
  const autosaveBeschreibung = useAutosave((doc: JSONContent) => speichern({ description: serializeRichText(doc) }));
  const autosaveNotizen = useAutosave((doc: JSONContent) => speichern({ notes: serializeRichText(doc) }));

  async function reparaturUmschalten() {
    const neu = !bietetReparatur;
    setBietetReparatur(neu);
    await speichern({ bietetReparatur: neu });
  }

  async function faehigkeitenSpeichern(neu: Nebenfaehigkeit[]) {
    setFaehigkeiten(neu);
    await speichern({ nebenfaehigkeiten: neu });
  }

  function entwurfUebernehmen(e: FormEvent) {
    e.preventDefault();
    if (!entwurf) return;
    const sauberName = entwurf.name.trim();
    if (!sauberName) return;
    const alterWert = entwurf.index !== null ? faehigkeiten[entwurf.index]?.wert ?? 0 : 0;
    const zahl = entwurf.wert.trim() === "" ? alterWert : Math.max(0, Math.round(Number(entwurf.wert) || 0));
    const eintrag = { name: sauberName, wert: zahl };
    const neu =
      entwurf.index === null
        ? [...faehigkeiten, eintrag]
        : faehigkeiten.map((f, i) => (i === entwurf.index ? eintrag : f));
    setEntwurf(null);
    void faehigkeitenSpeichern(neu);
  }

  async function zuNpcMachen() {
    setZuNpcLaeuft(true);
    setFehler(null);
    try {
      await entitiesApi.nebenfigurZuNpc(campaignId, person.id);
      setZuNpcOffen(false);
      onGeaendert();
      onSchliessen();
    } catch (e) {
      setZuNpcOffen(false);
      setFehler(e instanceof Error ? e.message : "Umwandeln fehlgeschlagen");
    } finally {
      setZuNpcLaeuft(false);
    }
  }

  async function loeschen() {
    await entitiesApi.deletePerson(campaignId, person.id);
    setLoeschenOffen(false);
    onGeaendert();
    onSchliessen();
  }

  // Rasse aus Altbestand, die nicht (mehr) freigegeben ist, bleibt wählbar.
  const rassenOptionen = rasse && !rassen.includes(rasse) ? [rasse, ...rassen] : rassen;

  return (
    <>
      <Fenster
        offen
        breit={unteransicht === "beziehungen"}
        titel={anzeigeName(person.name, person.alias)}
        unterzeile="Nebenfigur"
        kennung={`nebenfigur-detail:${person.id}`}
        onSchliessen={onSchliessen}
      >
        <div className="pcd-inhalt">
          <nav className="pcd-nav">
            {(
              [
                ["uebersicht", "Übersicht"],
                ["beschreibung", "Beschreibung"],
                ["notizen", "Notizen"],
                ["beziehungen", `Beziehungen (${beziehungsZahl})`],
              ] as const
            ).map(([id, text]) => (
              <button
                key={id}
                type="button"
                className={unteransicht === id ? "pcd-nav-aktiv" : ""}
                onClick={() => setUnteransicht(id)}
              >
                {text}
              </button>
            ))}
          </nav>

          <div className="pcd-bereich">
            {fehler && <p className="nf-fehler">{fehler}</p>}

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
                  <div className="pcd-feld">
                    <label htmlFor={`nf-name-${person.id}`}>Name</label>
                    <input
                      id={`nf-name-${person.id}`}
                      value={name}
                      onChange={(e) => {
                        setName(e.target.value);
                        autosaveName(e.target.value);
                      }}
                      onBlur={() => {
                        if (!name.trim()) {
                          setName(person.name);
                          return;
                        }
                        void autosaveName.jetzt();
                      }}
                    />
                  </div>
                  <div className="nf-feld-reihe">
                    <div className="pcd-feld">
                      <label htmlFor={`nf-rasse-${person.id}`}>Rasse</label>
                      <select
                        id={`nf-rasse-${person.id}`}
                        value={rasse}
                        onChange={(e) => {
                          setRasse(e.target.value);
                          void speichern({ rasse: e.target.value });
                        }}
                      >
                        <option value="">— keine —</option>
                        {rassenOptionen.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="pcd-feld">
                      <label htmlFor={`nf-alter-${person.id}`}>Alter</label>
                      <input
                        id={`nf-alter-${person.id}`}
                        value={alter}
                        onChange={(e) => {
                          setAlter(e.target.value);
                          autosaveAlter(e.target.value);
                        }}
                        onBlur={() => void autosaveAlter.jetzt()}
                      />
                    </div>
                  </div>
                  <div className="pcd-feld">
                    <label htmlFor={`nf-pers-${person.id}`}>Persönlichkeit</label>
                    <input
                      id={`nf-pers-${person.id}`}
                      value={persoenlichkeit}
                      maxLength={60}
                      placeholder="z.B. Leitwolf, Angsthase"
                      onChange={(e) => {
                        setPersoenlichkeit(e.target.value);
                        autosavePersoenlichkeit(e.target.value);
                      }}
                      onBlur={() => void autosavePersoenlichkeit.jetzt()}
                    />
                  </div>

                  <div className="nf-ueberschrift">Fähigkeiten</div>
                  {faehigkeiten.length === 0 ? (
                    <p className="nf-leer">Noch keine — z.B. Straßenwissen 4, Feilschen 3.</p>
                  ) : (
                    <div className="nf-faehigkeiten">
                      {faehigkeiten.map((f, i) => (
                        <div key={`${f.name}-${i}`} className="nf-faehigkeit">
                          <span className="nf-faehigkeit-name">{f.name}</span>
                          <span className="nf-faehigkeit-wert">{f.wert}</span>
                          <button
                            type="button"
                            title="Bearbeiten"
                            onClick={() => setEntwurf({ index: i, name: f.name, wert: "" })}
                          >
                            ✎
                          </button>
                          <button type="button" title="Entfernen" onClick={() => setEntfernenIndex(i)}>
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="nf-ueberschrift">Händler</div>
                  {istHaendler ? (
                    <p className="nf-hinweis">
                      Verkauft {laden ? <>im Laden <strong>{laden.ortName}</strong></> : "ohne festen Laden"}. Ware,
                      Spezialisierung und Tutorial-Flag pflegst du am Ort unter „Laden“.
                    </p>
                  ) : (
                    <p className="nf-hinweis">Kein Händler. Ein Händler braucht keinen Charakterbogen — nur einen Laden.</p>
                  )}
                  <div className="pcd-buttons" style={{ marginBottom: 12 }}>
                    <button type="button" onClick={() => void ladenWahlOeffnen()}>
                      {istHaendler ? "🏪 Anderen Laden wählen" : "🏪 Als Händler an einen Laden stellen"}
                    </button>
                    {istHaendler && (
                      <button type="button" onClick={() => void reparaturUmschalten()}>
                        {bietetReparatur ? "🔧 Bietet Reparatur — Flag weg" : "🔧 Als Reparatur-Händler markieren"}
                      </button>
                    )}
                    {istHaendler && (
                      <button type="button" onClick={() => setAbziehenOffen(true)}>
                        Vom Laden nehmen
                      </button>
                    )}
                  </div>

                  <div className="pcd-buttons">
                    <button type="button" onClick={() => setEntwurf({ index: null, name: "", wert: "" })}>
                      + Fähigkeit
                    </button>
                    {person.istBlankoKontakt ? (
                      <p className="nf-hinweis">
                        Leerer Kontakt-Platz — der Spieler beschreibt ihn im Messenger, dann füllt die KI ihn.
                      </p>
                    ) : (
                      <button type="button" onClick={() => setZuNpcOffen(true)} disabled={zuNpcLaeuft}>
                        {zuNpcLaeuft ? "KI baut den Bogen…" : "⇧ Zu NPC machen"}
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => setLoeschenOffen(true)}
                      style={{ color: "var(--signal)", borderColor: "var(--signal)" }}
                    >
                      🗑 Nebenfigur löschen
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
      </Fenster>

      <Fenster
        offen={entwurf !== null}
        schmal
        titel={entwurf?.index === null ? "Neue Fähigkeit" : `Fähigkeit bearbeiten`}
        unterzeile="Freier Name, fester Wert"
        kennung={`nebenfigur-faehigkeit:${person.id}`}
        onSchliessen={() => setEntwurf(null)}
      >
        {entwurf && (
          <form className="nf-formular" onSubmit={entwurfUebernehmen}>
            <input
              value={entwurf.name}
              onChange={(e) => setEntwurf({ ...entwurf, name: e.target.value })}
              placeholder="z.B. Straßenwissen"
              autoFocus
              required
            />
            <input
              type="number"
              inputMode="numeric"
              min={0}
              value={entwurf.wert}
              onChange={(e) => setEntwurf({ ...entwurf, wert: e.target.value })}
              placeholder={
                entwurf.index !== null ? `Wert (bisher ${faehigkeiten[entwurf.index]?.wert ?? 0})` : "Wert, z.B. 3"
              }
            />
            <button type="submit" className="nf-formular-knopf">
              {entwurf.index === null ? "Hinzufügen" : "Übernehmen"}
            </button>
          </form>
        )}
      </Fenster>

      <Fenster
        offen={ladenWahlOffen}
        schmal
        titel={`Laden für ${person.name}`}
        unterzeile="Ein Ort ohne Laden wird dabei zum Laden"
        kennung={`nebenfigur-laden:${person.id}`}
        onSchliessen={() => setLadenWahlOffen(false)}
      >
        <form className="nf-formular" onSubmit={anLadenStellen}>
          <select value={ladenOrtId} onChange={(e) => setLadenOrtId(e.target.value)} required>
            <option value="">— Ort wählen —</option>
            {ladenOrte.map((o) => (
              <option key={o.id} value={o.id}>
                {o.istShop ? `${o.name} (Laden)` : o.name}
              </option>
            ))}
          </select>
          <p className="nf-hinweis">Sortiment und Spezialisierung danach am Ort unter „Laden“.</p>
          <button type="submit" className="nf-formular-knopf" disabled={!ladenOrtId}>
            Dort verkaufen lassen
          </button>
        </form>
      </Fenster>

      {abziehenOffen && (
        <Bestaetigung
          titel={`${person.name} vom Laden nehmen?`}
          text={`${person.name} ist danach kein Händler mehr${laden ? ` und verkauft nicht mehr in „${laden.ortName}“` : ""}. Der Ort bleibt ein Laden, sein Sortiment bleibt.`}
          jaText="Vom Laden nehmen"
          onJa={() => void vomLadenNehmen()}
          onNein={() => setAbziehenOffen(false)}
        />
      )}

      {entfernenIndex !== null && (
        <Bestaetigung
          titel="Fähigkeit entfernen?"
          text={`„${faehigkeiten[entfernenIndex]?.name ?? ""}“ wird von ${person.name} entfernt.`}
          jaText="Entfernen"
          onJa={() => {
            const neu = faehigkeiten.filter((_, i) => i !== entfernenIndex);
            setEntfernenIndex(null);
            void faehigkeitenSpeichern(neu);
          }}
          onNein={() => setEntfernenIndex(null)}
        />
      )}
      {zuNpcOffen && (
        <Bestaetigung
          titel={`${person.name} zum NPC machen?`}
          text="Einbahnstraße: die KI baut einen vollen Charakterbogen (Rasse bleibt, die Fähigkeiten landen auf den passendsten Fertigkeiten) und kauft Startausrüstung. Name, Bilder, Beschreibung, Notizen, Beziehungen und Kontakte bleiben. Danach steht die Figur unter NPCs — zurück zur Nebenfigur geht nicht."
          jaText={zuNpcLaeuft ? "…" : "Zu NPC machen"}
          onJa={() => {
            if (!zuNpcLaeuft) void zuNpcMachen();
          }}
          onNein={() => setZuNpcOffen(false)}
        />
      )}
      {loeschenOffen && (
        <Bestaetigung
          titel={`${person.name} löschen?`}
          text={`„${person.name}“ wandert in den Papierkorb, samt ${beziehungsZahl} Verbindungen.`}
          jaText="Ja, löschen"
          onJa={() => void loeschen()}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </>
  );
}
