import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { entitiesApi, type Person } from "../entities/api";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { bogenApi, type Erstellungsregeln } from "../traits/bogenApi";
import {
  achievementsApi,
  AUSLOESE_ARTEN,
  AUSLOESE_ARTEN_MIT_ZIEL_GEGENSTAND,
  AUSLOESE_ART_LABEL,
  type Achievement,
  type AchievementEingabe,
  type Vorschlag,
} from "./api";
import "./achievements.css";

/**
 * SL-Verwaltungsfenster (Burgermenü-Stil, Marks Vorgabe 27.09.2026): Katalog
 * aller Achievement-Definitionen, "+ Neu anlegen"-Baukasten, Liste offener
 * Auto-Trigger-Vorschläge zum Bestätigen, manuelle Vergabe an eine Person.
 * Analog zum Rassen-Baukasten-Fenster.
 */
export function AchievementVerwaltung({ campaignId }: { campaignId: string }) {
  const [katalog, setKatalog] = useState<Achievement[]>([]);
  const [vorschlaege, setVorschlaege] = useState<Vorschlag[]>([]);
  const [regeln, setRegeln] = useState<Erstellungsregeln | null>(null);
  const [gegenstaende, setGegenstaende] = useState<GegenstandMitBesitzer[]>([]);
  const [personen, setPersonen] = useState<Person[]>([]);
  const [laedt, setLaedt] = useState(true);
  const [offenesAchievement, setOffenesAchievement] = useState<Achievement | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [neuName, setNeuName] = useState("");
  const [vergebenFuer, setVergebenFuer] = useState<Achievement | null>(null);

  async function neuLaden() {
    const [k, v] = await Promise.all([achievementsApi.katalog(campaignId), achievementsApi.vorschlaege(campaignId)]);
    setKatalog(k);
    setVorschlaege(v);
    setOffenesAchievement((alt) => (alt ? k.find((x) => x.id === alt.id) ?? null : null));
  }

  useEffect(() => {
    setLaedt(true);
    Promise.all([
      neuLaden(),
      bogenApi.regeln(campaignId).catch(() => null),
      itemsApi.listAlle(campaignId).catch(() => []),
      entitiesApi.listPersonenAlsGm(campaignId).catch(() => []),
    ])
      .then(([, r, g, p]) => {
        if (r) setRegeln(r);
        setGegenstaende(g);
        setPersonen(p);
      })
      .finally(() => setLaedt(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId]);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!neuName.trim()) return;
    const neu = await achievementsApi.anlegen(campaignId, { name: neuName.trim() });
    setNeuName("");
    setAnlegenOffen(false);
    await neuLaden();
    setOffenesAchievement(neu);
  }

  async function vorschlagBestaetigen(v: Vorschlag) {
    await achievementsApi.vorschlagAnwenden(campaignId, { achievementId: v.achievementId, personId: v.personId });
    await neuLaden();
  }

  if (laedt) return <p style={{ color: "var(--text-leise)" }}>Lade Achievements…</p>;

  return (
    <div className="ac-seite">
      {vorschlaege.length > 0 && (
        <section>
          <h3 className="ac-abschnitt-titel">Offene Auto-Vorschläge ({vorschlaege.length})</h3>
          <div className="ac-vorschlag-liste">
            {vorschlaege.map((v) => (
              <div key={`${v.achievementId}:${v.personId}`} className="ac-vorschlag">
                <span className="ac-vorschlag-icon" aria-hidden="true">
                  {v.achievementIcon || "🏆"}
                </span>
                <span className="ac-vorschlag-text">
                  <span className="ac-vorschlag-name">{v.achievementName}</span>
                  <span className="ac-vorschlag-person"> — für {v.personName}</span>
                </span>
                <button type="button" onClick={() => vorschlagBestaetigen(v)}>
                  ✓ Bestätigen
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      <section>
        <div className="ac-kopf">
          <h3 className="ac-abschnitt-titel">Katalog</h3>
          <button type="button" onClick={() => setAnlegenOffen(true)}>
            + Neu anlegen
          </button>
        </div>

        {katalog.length === 0 && <p className="ac-leer">Noch keine Achievements angelegt.</p>}

        <div className="ac-raster">
          {katalog.map((a) => (
            <button key={a.id} type="button" className="ac-kachel" onClick={() => setOffenesAchievement(a)}>
              <div className="ac-kachel-kopf">
                <span className="ac-kachel-icon" aria-hidden="true">
                  {a.icon || "🏆"}
                </span>
                <span className="ac-kachel-name">{a.name}</span>
              </div>
              {a.beschreibung && <span className="ac-kachel-beschreibung">{a.beschreibung}</span>}
              <div className="ac-kachel-marken">
                <span className="ac-marke" data-art={a.art}>
                  {a.art}
                </span>
                {a.einzigartig && (
                  <span className="ac-marke" data-einzigartig="true">
                    einzigartig
                  </span>
                )}
                {a.belohnungsArt !== "KEINE" && (
                  <span className="ac-marke" data-belohnung="true">
                    {a.belohnungsArt === "EP" ? `+${a.belohnungsMenge} EP` : `+${a.belohnungsMenge} ${a.belohnungsHintergrund}`}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      </section>

      <Fenster
        offen={anlegenOffen}
        titel="Neues Achievement"
        unterzeile="Erst anlegen, dann im Baukasten ausarbeiten"
        kennung="achievement-neu"
        onSchliessen={() => {
          setAnlegenOffen(false);
          setNeuName("");
        }}
      >
        <form onSubmit={anlegen} className="ac-editor">
          <input
            type="text"
            placeholder="Name des Achievements"
            value={neuName}
            onChange={(e) => setNeuName(e.target.value)}
            required
            autoFocus
          />
          <button type="submit">Anlegen und bearbeiten</button>
        </form>
      </Fenster>

      {offenesAchievement && (
        <AchievementEditor
          campaignId={campaignId}
          achievement={offenesAchievement}
          regeln={regeln}
          gegenstaende={gegenstaende}
          onSchliessen={() => setOffenesAchievement(null)}
          onGeaendert={neuLaden}
          onVerleihen={() => setVergebenFuer(offenesAchievement)}
        />
      )}

      {vergebenFuer && (
        <ManuelleVergabe
          campaignId={campaignId}
          achievement={vergebenFuer}
          personen={personen}
          onSchliessen={() => setVergebenFuer(null)}
          onVerliehen={async () => {
            setVergebenFuer(null);
            await neuLaden();
          }}
        />
      )}
    </div>
  );
}

/** Der Baukasten für ein einzelnes Achievement. */
function AchievementEditor({
  campaignId,
  achievement,
  regeln,
  gegenstaende,
  onSchliessen,
  onGeaendert,
  onVerleihen,
}: {
  campaignId: string;
  achievement: Achievement;
  regeln: Erstellungsregeln | null;
  gegenstaende: GegenstandMitBesitzer[];
  onSchliessen: () => void;
  onGeaendert: () => Promise<void>;
  onVerleihen: () => void;
}) {
  const [name, setName] = useState(achievement.name);
  const [beschreibung, setBeschreibung] = useState(achievement.beschreibung);
  const [icon, setIcon] = useState(achievement.icon);
  const [art, setArt] = useState<"AUTO" | "MANUELL">(achievement.art);
  const [ausloeseArt, setAusloeseArt] = useState(achievement.ausloeseArt ?? "");
  const [einzigartig, setEinzigartig] = useState(achievement.einzigartig);
  const [belohnungsArt, setBelohnungsArt] = useState(achievement.belohnungsArt);
  const [belohnungsMenge, setBelohnungsMenge] = useState(achievement.belohnungsMenge);
  const [belohnungsHintergrund, setBelohnungsHintergrund] = useState(achievement.belohnungsHintergrund ?? "");
  const [zielGegenstandId, setZielGegenstandId] = useState(achievement.zielGegenstandId ?? "");
  const [laeuft, setLaeuft] = useState(false);
  const [loeschenOffen, setLoeschenOffen] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    setName(achievement.name);
    setBeschreibung(achievement.beschreibung);
    setIcon(achievement.icon);
    setArt(achievement.art);
    setAusloeseArt(achievement.ausloeseArt ?? "");
    setEinzigartig(achievement.einzigartig);
    setBelohnungsArt(achievement.belohnungsArt);
    setBelohnungsMenge(achievement.belohnungsMenge);
    setBelohnungsHintergrund(achievement.belohnungsHintergrund ?? "");
    setZielGegenstandId(achievement.zielGegenstandId ?? "");
  }, [achievement.id]);

  const brauchtZiel = AUSLOESE_ARTEN_MIT_ZIEL_GEGENSTAND.has(ausloeseArt);

  async function speichern() {
    setLaeuft(true);
    setFehler(null);
    try {
      const body: AchievementEingabe = {
        name,
        beschreibung,
        icon,
        art,
        ausloeseArt: art === "AUTO" ? ausloeseArt || null : null,
        einzigartig,
        belohnungsArt,
        belohnungsMenge,
        belohnungsHintergrund: belohnungsArt === "HINTERGRUND" ? belohnungsHintergrund || null : null,
        zielGegenstandId: brauchtZiel ? zielGegenstandId || null : null,
      };
      await achievementsApi.aendern(campaignId, achievement.id, body);
      await onGeaendert();
    } catch (e) {
      setFehler((e as Error).message || "Das Speichern hat nicht geklappt.");
    } finally {
      setLaeuft(false);
    }
  }

  async function loeschen() {
    try {
      await achievementsApi.loeschen(campaignId, achievement.id);
      setLoeschenOffen(false);
      onSchliessen();
      await onGeaendert();
    } catch (e) {
      setLoeschenOffen(false);
      setFehler((e as Error).message || "Löschen nicht möglich — vermutlich schon verliehen.");
    }
  }

  return (
    <>
      <Fenster offen breit titel={achievement.name} unterzeile="Achievement-Baukasten" kennung={`achievement:${achievement.id}`} onSchliessen={onSchliessen}>
        <div className="ac-editor">
          {fehler && <p className="ac-fehler">{fehler}</p>}

          <label className="ac-feld">
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>

          <div className="ac-reihe">
            <label className="ac-feld">
              Icon (Emoji)
              <input value={icon} onChange={(e) => setIcon(e.target.value)} placeholder="🏆" />
            </label>
            <label className="ac-feld">
              Bauart
              <select value={art} onChange={(e) => setArt(e.target.value as "AUTO" | "MANUELL")}>
                <option value="MANUELL">Manuell (SL vergibt spontan)</option>
                <option value="AUTO">Auto (aus dem Ereignisprotokoll erkannt)</option>
              </select>
            </label>
          </div>

          <label className="ac-feld">
            Beschreibung
            <textarea
              value={beschreibung}
              rows={2}
              placeholder="Was das Achievement bedeutet — kurz."
              onChange={(e) => setBeschreibung(e.target.value)}
            />
          </label>

          {art === "AUTO" && (
            <>
              <label className="ac-feld">
                Auslöser
                <select value={ausloeseArt} onChange={(e) => setAusloeseArt(e.target.value)}>
                  <option value="">— wählen —</option>
                  {AUSLOESE_ARTEN.map((a) => (
                    <option key={a} value={a}>
                      {AUSLOESE_ART_LABEL[a] ?? a}
                    </option>
                  ))}
                </select>
              </label>
              {brauchtZiel && (
                <label className="ac-feld">
                  Zielgegenstand
                  <select value={zielGegenstandId} onChange={(e) => setZielGegenstandId(e.target.value)}>
                    <option value="">— wählen —</option>
                    {gegenstaende.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </>
          )}

          <label className="ac-feld" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <input type="checkbox" checked={einzigartig} onChange={(e) => setEinzigartig(e.target.checked)} style={{ width: "auto" }} />
            einzigartig (höchstens ein Träger campaign-weit gleichzeitig)
          </label>
          <p className="ac-hinweis">
            Unmarkiert kann jede Person unabhängig ihr eigenes Exemplar erhalten (z. B. "Mörder"). Markiert
            gibt es höchstens eine Trägerin gleichzeitig (z. B. "First Kill") — bei einem Rekord-Auslöser
            wandert der Titel automatisch weiter.
          </p>

          <div className="ac-reihe">
            <label className="ac-feld">
              Belohnung
              <select value={belohnungsArt} onChange={(e) => setBelohnungsArt(e.target.value as Achievement["belohnungsArt"])}>
                <option value="KEINE">Keine (rein kosmetisch)</option>
                <option value="EP">Erfahrungspunkte</option>
                <option value="HINTERGRUND">Hintergrundpunkte</option>
              </select>
            </label>
            {belohnungsArt !== "KEINE" && (
              <label className="ac-feld">
                Menge
                <input
                  type="number"
                  min={1}
                  value={belohnungsMenge}
                  onChange={(e) => setBelohnungsMenge(Math.max(1, Number(e.target.value)))}
                />
              </label>
            )}
            {belohnungsArt === "HINTERGRUND" && (
              <label className="ac-feld">
                Welcher Hintergrund
                <select value={belohnungsHintergrund} onChange={(e) => setBelohnungsHintergrund(e.target.value)}>
                  <option value="">— wählen —</option>
                  {(regeln?.hintergruende ?? []).map((h) => (
                    <option key={h.name} value={h.name}>
                      {h.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>
          {belohnungsArt === "HINTERGRUND" && (
            <p className="ac-hinweis">
              Einziger Weg, wie ein Hintergrund nach der Charaktererstellung noch steigt — EP-Steigern
              schließt Hintergründe sonst aus.
            </p>
          )}

          <div className="ac-aktionen">
            <button type="button" className="ac-speichern" onClick={speichern} disabled={laeuft}>
              Speichern
            </button>
            <button type="button" onClick={onVerleihen}>
              🏆 Jetzt vergeben
            </button>
            <button type="button" className="ac-loeschen" onClick={() => setLoeschenOffen(true)}>
              🗑 Löschen
            </button>
          </div>
        </div>
      </Fenster>

      {loeschenOffen && (
        <Bestaetigung
          titel={`${achievement.name} löschen?`}
          text="Bereits vergebene Achievements lassen sich nicht löschen — nur Definitionen ohne Verleihung."
          jaText="Löschen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </>
  );
}

/** Spontane manuelle Vergabe an eine Person, optional mit ✨-KI-Text. */
function ManuelleVergabe({
  campaignId,
  achievement,
  personen,
  onSchliessen,
  onVerliehen,
}: {
  campaignId: string;
  achievement: Achievement;
  personen: Person[];
  onSchliessen: () => void;
  onVerliehen: () => Promise<void>;
}) {
  const [personId, setPersonId] = useState("");
  const [suche, setSuche] = useState("");
  const [text, setText] = useState("");
  const [laedtKi, setLaedtKi] = useState(false);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  const gefiltert = useMemo(() => {
    const s = suche.trim().toLowerCase();
    if (!s) return personen;
    return personen.filter((p) => p.name.toLowerCase().includes(s));
  }, [personen, suche]);

  async function kiVorschlag() {
    if (!personId) return;
    setLaedtKi(true);
    setFehler(null);
    try {
      const antwort = await achievementsApi.kiText(campaignId, { achievementId: achievement.id, personId });
      setText(antwort.text);
    } catch (e) {
      setFehler((e as Error).message || "Die KI hat nicht geantwortet.");
    } finally {
      setLaedtKi(false);
    }
  }

  async function vergeben(e: FormEvent) {
    e.preventDefault();
    if (!personId) return;
    setLaeuft(true);
    setFehler(null);
    try {
      await achievementsApi.verleihen(campaignId, achievement.id, { personId, text });
      await onVerliehen();
    } catch (e) {
      setFehler((e as Error).message || "Das Vergeben hat nicht geklappt.");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <Fenster offen titel={`${achievement.icon || "🏆"} ${achievement.name} vergeben`} kennung={`achievement-vergeben:${achievement.id}`} onSchliessen={onSchliessen}>
      <form onSubmit={vergeben} className="ac-editor">
        {fehler && <p className="ac-fehler">{fehler}</p>}

        <label className="ac-feld">
          An wen
          <input type="search" placeholder="Person suchen…" value={suche} onChange={(e) => setSuche(e.target.value)} />
        </label>
        <select value={personId} onChange={(e) => setPersonId(e.target.value)} size={Math.min(6, Math.max(3, gefiltert.length))}>
          {gefiltert.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>

        <label className="ac-feld">
          Text (KI oder frei)
          <textarea value={text} rows={4} onChange={(e) => setText(e.target.value)} />
        </label>
        <button type="button" className="ac-ki-knopf" onClick={kiVorschlag} disabled={!personId || laedtKi}>
          {laedtKi ? "✨ …" : "✨ KI-Text vorschlagen"}
        </button>

        <div className="ac-aktionen">
          <button type="submit" className="ac-speichern" disabled={!personId || laeuft}>
            🏆 Vergeben
          </button>
        </div>
      </form>
    </Fenster>
  );
}
