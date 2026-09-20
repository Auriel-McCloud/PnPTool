import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { entitiesApi, type Person } from "../entities/api";
import { KACHEL_STIL, useProSeite } from "../items/kachelraster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { DotPool } from "../traits/DotPool";
import { StufenBlatt } from "../traits/StufenBlatt";
import { ART_NAMEN, ART_SYMBOLE, begleiterApi, type Begleiter, type BegleiterArt } from "./api";
import { EinflussVerwaltung } from "./EinflussVerwaltung";
import { CritterWerte, KiAttributBlatt } from "./KiAttributBlatt";
import "../items/gegenstaende.css";
import "./begleiter.css";

/**
 * Begleiter anlegen und pflegen — Sprites, Geister, Verbündete, KIs, Critter.
 *
 * Sie hängen an einer Person und teilen sich das Grundblatt mit Drohnen und
 * Fahrzeugen. Wer einem Spielercharakter zugeordnet ist, wird beim Anlegen
 * automatisch für ihn sichtbar; sonst müsste die Spielleitung bei jedem
 * Sprite daran denken, und vergässe sie es, stünde der Neuroweaver ohne da.
 *
 * KI (19.09.2026) trägt zusätzlich die sechs nicht-körperlichen
 * Person-Attribute plus Matrix-Präsenz und kann echten Entitäten
 * Einfluss-Stufen zuweisen (`EinflussVerwaltung`). CRITTER trägt zusätzlich
 * Loyalität und Ausbildung/Tricks.
 *
 * **Kachelraster + Anlegen-Popup (20.09.2026)**: dasselbe Muster wie
 * GegenstaendeUebersicht/PartyVerwaltung — Suchfeld über Name/Art/Besitzer,
 * "+ Neuer Begleiter" öffnet ein Fenster statt eines Inline-Formulars.
 */

const ARTEN: BegleiterArt[] = ["SPRITE", "GEIST", "BEGLEITER", "KI", "CRITTER"];

export function BegleiterVerwaltung({ campaignId }: { campaignId: string }) {
  const [alle, setAlle] = useState<Begleiter[]>([]);
  const [personen, setPersonen] = useState<Person[]>([]);
  const [laden, setLaden] = useState(true);
  const [offen, setOffen] = useState<Begleiter | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [suche, setSuche] = useState("");
  const rasterRef = useRef<HTMLDivElement>(null);
  const proSeite = useProSeite(rasterRef);
  const [seite, setSeite] = useState(0);

  async function neuLaden() {
    const [b, p] = await Promise.all([
      begleiterApi.liste(campaignId),
      entitiesApi.listPersonen(campaignId),
    ]);
    setAlle(b);
    setPersonen(p);
  }

  useEffect(() => {
    setLaden(true);
    neuLaden().finally(() => setLaden(false));
  }, [campaignId]);

  const personenNamen = useMemo(
    () => personen.map((p) => ({ id: p.id, label: `${p.name} (${p.personType})` })),
    [personen],
  );

  // Sucht über Name, Art und Besitzer — analog zur Gegenstände-/Party-Suche
  // ("alle Sprites von Kira" statt exaktem Namen).
  const gefiltert = useMemo(() => {
    const s = suche.trim().toLowerCase();
    if (!s) return alle;
    return alle.filter(
      (b) =>
        b.name.toLowerCase().includes(s) ||
        ART_NAMEN[b.art].toLowerCase().includes(s) ||
        (b.besitzerName ?? "").toLowerCase().includes(s),
    );
  }, [alle, suche]);

  // Nach einer neuen Suche kann die aktuelle Seite hinter dem gefilterten
  // Ende liegen — zurück auf die erste Seite, sonst wirkt die Liste leer.
  useEffect(() => {
    setSeite(0);
  }, [suche]);

  const seiten = Math.max(1, Math.ceil(gefiltert.length / proSeite));
  const aktuelleSeite = Math.min(seite, seiten - 1);
  const sichtbar = gefiltert.slice(aktuelleSeite * proSeite, (aktuelleSeite + 1) * proSeite);

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Begleiter…</p>;

  return (
    <div className="gg-seite" style={KACHEL_STIL}>
      <div className="gg-kopf">
        <input
          className="gg-suche"
          type="search"
          placeholder="Suchen — Name, Art oder Besitzer"
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
        />
        <button type="button" onClick={() => setAnlegenOffen(true)}>
          + Neuer Begleiter
        </button>
        <span className="gg-anzahl">
          {gefiltert.length} von {alle.length}
        </span>
      </div>

      <div className="gg-raster" ref={rasterRef}>
        {sichtbar.map((b) => (
          <button key={b.id} type="button" className="gg-kachel" onClick={() => setOffen(b)} title={b.name}>
            <span className="gg-kachel-bild">
              <span aria-hidden="true">{ART_SYMBOLE[b.art]}</span>
            </span>
            <span className="gg-kachel-name">{b.name}</span>
            <span className="gg-kachel-zeile">
              {ART_NAMEN[b.art]}
              {b.stufe > 0 && ` · Stufe ${b.stufe}`}
            </span>
            <span className="gg-kachel-marken">
              {b.besitzerName ? (
                <span className="gg-marke">{b.besitzerName}</span>
              ) : (
                <span className="gg-marke">ungebunden</span>
              )}
            </span>
          </button>
        ))}
      </div>

      {alle.length === 0 && <p className="gg-leer">Noch keine Begleiter in dieser Kampagne.</p>}
      {alle.length > 0 && gefiltert.length === 0 && <p className="gg-leer">Nichts gefunden.</p>}

      {seiten > 1 && (
        <div className="gg-blaettern">
          <button type="button" onClick={() => setSeite((n) => Math.max(0, n - 1))} disabled={aktuelleSeite === 0}>
            ‹
          </button>
          <span>
            {aktuelleSeite + 1} / {seiten}
          </span>
          <button
            type="button"
            onClick={() => setSeite((n) => Math.min(seiten - 1, n + 1))}
            disabled={aktuelleSeite >= seiten - 1}
          >
            ›
          </button>
        </div>
      )}

      <BegleiterAnlegenFenster
        offen={anlegenOffen}
        campaignId={campaignId}
        personen={personenNamen}
        onSchliessen={() => setAnlegenOffen(false)}
        onAngelegt={async (neu) => {
          setAnlegenOffen(false);
          await neuLaden();
          setOffen(neu);
        }}
      />

      {offen && (
        <BegleiterFenster
          campaignId={campaignId}
          begleiter={offen}
          personen={personenNamen}
          onSchliessen={() => setOffen(null)}
          onGeaendert={async () => {
            await neuLaden();
            setOffen(null);
          }}
          // Einfluss ändert sich sofort über die eigene API, ohne dass der
          // Rest des Formulars mitgespeichert werden soll — das Fenster
          // bleibt offen, damit man mehrere Ziele nacheinander zuweisen kann
          // (dasselbe Muster wie Mitglied-Hinzufügen in PartyVerwaltung).
          onEinflussGeaendert={(neu) => {
            setAlle((alt) => alt.map((b) => (b.id === neu.id ? neu : b)));
            setOffen(neu);
          }}
        />
      )}
    </div>
  );
}

/**
 * Durchsuchbare Besitzer-Auswahl (Radiobuttons statt eines langen `<select>`
 * ohne Filter) — dasselbe Muster wie `PersonenAuswahlListe` in
 * PartyVerwaltung.tsx, nur für eine Einfachauswahl statt Checkboxen, weil
 * ein Begleiter höchstens eine Person begleitet.
 */
function BesitzerAuswahl({
  personen,
  wert,
  onWaehlen,
}: {
  personen: { id: string; label: string }[];
  wert: string;
  onWaehlen: (personId: string) => void;
}) {
  const [suche, setSuche] = useState("");

  const gefiltert = useMemo(() => {
    const s = suche.trim().toLowerCase();
    if (!s) return personen;
    return personen.filter((p) => p.label.toLowerCase().includes(s));
  }, [personen, suche]);

  return (
    <div className="bg-zeile" style={{ flexDirection: "column", alignItems: "stretch", gap: 4 }}>
      <input
        type="search"
        className="bg-suchfeld"
        placeholder="Besitzer suchen…"
        value={suche}
        onChange={(e) => setSuche(e.target.value)}
      />
      <div className="bg-auswahl-liste">
        <label className="bg-auswahl-zeile">
          <input type="radio" name="bg-besitzer" checked={wert === ""} onChange={() => onWaehlen("")} />
          <span>— ungebunden —</span>
        </label>
        {gefiltert.length === 0 && suche && <p className="pt-hinweis">Nichts gefunden.</p>}
        {gefiltert.map((p) => (
          <label key={p.id} className="bg-auswahl-zeile">
            <input type="radio" name="bg-besitzer" checked={wert === p.id} onChange={() => onWaehlen(p.id)} />
            <span>{p.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

/**
 * Anlegen-Popup: Name, Art und gleich die Besitzer-Auswahl (Verbindung) in
 * einem Commlink-Fenster statt des früheren Inline-Formulars in der
 * Kopfzeile — Mark, 20.09.2026: Suche + "+"-Popup wie bei den anderen
 * Bereichen.
 */
function BegleiterAnlegenFenster({
  offen,
  campaignId,
  personen,
  onSchliessen,
  onAngelegt,
}: {
  offen: boolean;
  campaignId: string;
  personen: { id: string; label: string }[];
  onSchliessen: () => void;
  onAngelegt: (neu: Begleiter) => void;
}) {
  const [name, setName] = useState("");
  const [art, setArt] = useState<BegleiterArt>("SPRITE");
  const [besitzer, setBesitzer] = useState("");
  const [sendet, setSendet] = useState(false);

  // Frisch beginnen bei jedem Öffnen — sonst stehen noch Name/Auswahl des
  // zuletzt angelegten Begleiters da (dasselbe Muster wie PartyAnlegenFenster).
  useEffect(() => {
    if (offen) {
      setName("");
      setArt("SPRITE");
      setBesitzer("");
    }
  }, [offen]);

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSendet(true);
    try {
      const neu = await begleiterApi.anlegen(campaignId, {
        name: name.trim(),
        art,
        besitzerId: besitzer || null,
      });
      onAngelegt(neu);
    } finally {
      setSendet(false);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel="Neuer Begleiter"
      unterzeile="Name, Art und optional gleich die Verbindung zu einer Person"
      kennung="begleiter-neu"
      ton="var(--bereich-begleiter)"
      onSchliessen={onSchliessen}
    >
      <form onSubmit={anlegen} className="bg-formular">
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          autoFocus
        />

        <div className="bg-zeile">
          <span style={{ fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--neon)" }}>
            Art
          </span>
          <select value={art} onChange={(e) => setArt(e.target.value as BegleiterArt)}>
            {ARTEN.map((a) => (
              <option key={a} value={a}>
                {ART_SYMBOLE[a]} {ART_NAMEN[a]}
              </option>
            ))}
          </select>
        </div>

        <div>
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
            Verbindung (optional)
          </span>
          <BesitzerAuswahl personen={personen} wert={besitzer} onWaehlen={setBesitzer} />
        </div>

        <button type="submit" disabled={sendet || !name.trim()}>
          {sendet ? "Wird angelegt…" : "Anlegen"}
        </button>
      </form>
    </Fenster>
  );
}

function BegleiterFenster({
  campaignId,
  begleiter,
  personen,
  onSchliessen,
  onGeaendert,
  onEinflussGeaendert,
}: {
  campaignId: string;
  begleiter: Begleiter;
  personen: { id: string; label: string }[];
  onSchliessen: () => void;
  onGeaendert: () => void;
  onEinflussGeaendert: (neu: Begleiter) => void;
}) {
  const [name, setName] = useState(begleiter.name);
  const [art, setArt] = useState(begleiter.art);
  const [beziehung, setBeziehung] = useState(begleiter.beziehung);
  const [stufe, setStufe] = useState(begleiter.stufe);
  const [widerstand, setWiderstand] = useState(begleiter.widerstand);
  const [angriff, setAngriff] = useState(begleiter.angriff);
  const [agilitaet, setAgilitaet] = useState(begleiter.agilitaet);
  const [waffe, setWaffe] = useState(begleiter.waffe);
  const [waffenSchaden, setWaffenSchaden] = useState(begleiter.waffenSchaden);
  const [schadensart, setSchadensart] = useState(begleiter.schadensart);
  // Freie Fertigkeiten als Paare, damit sich Namen ändern lassen — ein
  // Objekt liesse den Schlüssel nicht umbenennen, ohne den Wert zu verlieren.
  const [fertigkeiten, setFertigkeiten] = useState<[string, number][]>(
    Object.entries(begleiter.fertigkeiten ?? {}),
  );
  const [besitzer, setBesitzer] = useState(begleiter.besitzerId ?? "");
  // KI-Attribute — Skala 1-6 wie bei Person.
  const [charisma, setCharisma] = useState(begleiter.charisma);
  const [manipulation, setManipulation] = useState(begleiter.manipulation);
  const [fassung, setFassung] = useState(begleiter.fassung);
  const [intelligenz, setIntelligenz] = useState(begleiter.intelligenz);
  const [geistesschaerfe, setGeistesschaerfe] = useState(begleiter.geistesschaerfe);
  const [entschlossenheit, setEntschlossenheit] = useState(begleiter.entschlossenheit);
  const [matrixPraesenz, setMatrixPraesenz] = useState(begleiter.matrixPraesenz);
  // CRITTER-Werte.
  const [loyalitaet, setLoyalitaet] = useState(begleiter.loyalitaet);
  const [ausbildung, setAusbildung] = useState(begleiter.ausbildung);
  // Erfahrung — reine Budget-Anzeige, keine Kostenrechnung.
  const [erfahrung, setErfahrung] = useState(begleiter.erfahrung);
  const [erfahrungAusgegeben, setErfahrungAusgegeben] = useState(begleiter.erfahrungAusgegeben);
  const [sendet, setSendet] = useState(false);
  const [loeschenOffen, setLoeschenOffen] = useState(false);

  const verteilt = widerstand + angriff + agilitaet + fertigkeiten.reduce((s, [, w]) => s + w, 0);

  async function sichern() {
    setSendet(true);
    try {
      await begleiterApi.aendern(campaignId, begleiter.id, {
        name,
        art,
        beziehung,
        stufe,
        widerstand,
        angriff,
        agilitaet,
        waffe,
        waffenSchaden,
        schadensart,
        fertigkeiten: Object.fromEntries(fertigkeiten.filter(([n]) => n.trim())),
        charisma,
        manipulation,
        fassung,
        intelligenz,
        geistesschaerfe,
        entschlossenheit,
        matrixPraesenz,
        loyalitaet,
        ausbildung,
        erfahrung,
        erfahrungAusgegeben,
      });
      if (besitzer !== (begleiter.besitzerId ?? "")) {
        await begleiterApi.besitzer(campaignId, begleiter.id, besitzer || null);
      }
      onGeaendert();
    } finally {
      setSendet(false);
    }
  }

  async function entfernen() {
    setLoeschenOffen(false);
    await begleiterApi.entfernen(campaignId, begleiter.id);
    onGeaendert();
  }

  return (
    <Fenster
      offen
      titel={`${ART_SYMBOLE[art]} ${begleiter.name}`}
      unterzeile="Blatt wie bei Drohne und Fahrzeug"
      kennung={`begleiter-bearbeiten:${begleiter.id}`}
      onSchliessen={onSchliessen}
    >
      <div className="bg-formular">
        <div className="bg-zeile">
          <input value={name} onChange={(e) => setName(e.target.value)} style={{ flex: "1 1 200px" }} />
          <select value={art} onChange={(e) => setArt(e.target.value as BegleiterArt)}>
            {ARTEN.map((a) => (
              <option key={a} value={a}>
                {ART_NAMEN[a]}
              </option>
            ))}
          </select>
        </div>

        <label className="bg-zeile" style={{ flexDirection: "column", alignItems: "stretch", gap: 3 }}>
          <span style={{ fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--neon)" }}>
            Beziehung
          </span>
          <input
            value={beziehung}
            onChange={(e) => setBeziehung(e.target.value)}
            placeholder="Wie steht er zu seinem Menschen?"
          />
        </label>

        <div>
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
          <BesitzerAuswahl personen={personen} wert={besitzer} onWaehlen={setBesitzer} />
        </div>

        {art === "KI" && (
          <KiAttributBlatt
            werte={{
              charisma,
              manipulation,
              fassung,
              intelligenz,
              geistesschaerfe,
              entschlossenheit,
              matrixPraesenz,
            }}
            onAendern={(feld, wert) => {
              if (feld === "charisma") setCharisma(wert);
              else if (feld === "manipulation") setManipulation(wert);
              else if (feld === "fassung") setFassung(wert);
              else if (feld === "intelligenz") setIntelligenz(wert);
              else if (feld === "geistesschaerfe") setGeistesschaerfe(wert);
              else if (feld === "entschlossenheit") setEntschlossenheit(wert);
              else if (feld === "matrixPraesenz") setMatrixPraesenz(wert);
            }}
          />
        )}

        {art === "CRITTER" && (
          <CritterWerte
            loyalitaet={loyalitaet}
            ausbildung={ausbildung}
            onAendern={(feld, wert) => {
              if (feld === "loyalitaet") setLoyalitaet(wert);
              else setAusbildung(wert);
            }}
          />
        )}

        <StufenBlatt
          werte={{ stufe, widerstand, angriff, agilitaet }}
          stufenHinweis="Das Budget für die Werte darunter — und zugleich die Gesundheit."
          onAendern={(feld, wert) => {
            if (feld === "stufe") setStufe(wert);
            else if (feld === "widerstand") setWiderstand(wert);
            else if (feld === "angriff") setAngriff(wert);
            else setAgilitaet(wert);
          }}
        />

        {stufe > 0 && verteilt > stufe && (
          <p style={{ color: "var(--warn)", fontSize: 13, margin: 0 }}>
            {verteilt} Punkte verteilt, die Stufe gibt {stufe} her.
          </p>
        )}

        <section>
          <h3 style={{ margin: "0 0 6px" }}>Fertigkeiten</h3>
          {fertigkeiten.map(([fName, fWert], i) => (
            <div key={i} className="bg-zeile" style={{ marginBottom: 4 }}>
              <input
                value={fName}
                onChange={(e) =>
                  setFertigkeiten((alt) => alt.map((p, j) => (j === i ? [e.target.value, p[1]] : p)))
                }
                placeholder="Name"
                style={{ flex: "1 1 160px" }}
              />
              <DotPool
                value={fWert}
                max={5}
                onChange={(w) => setFertigkeiten((alt) => alt.map((p, j) => (j === i ? [p[0], w] : p)))}
              />
              <button type="button" onClick={() => setFertigkeiten((alt) => alt.filter((_, j) => j !== i))}>
                −
              </button>
            </div>
          ))}
          <button type="button" onClick={() => setFertigkeiten((alt) => [...alt, ["", 0]])}>
            Fertigkeit hinzufügen
          </button>
        </section>

        <section>
          <h3 style={{ margin: "0 0 6px" }}>Gegenstand</h3>
          <div className="bg-zeile">
            <input
              value={waffe}
              onChange={(e) => setWaffe(e.target.value)}
              placeholder="Waffe oder Gerät"
              style={{ flex: "1 1 180px" }}
            />
            <input
              value={schadensart}
              onChange={(e) => setSchadensart(e.target.value)}
              placeholder="Schadensart"
              style={{ flex: "1 1 140px" }}
            />
          </div>
          <div className="bg-wert" style={{ marginTop: 4 }}>
            <span>Schadensbonus</span>
            <DotPool value={waffenSchaden} max={7} onChange={setWaffenSchaden} />
          </div>
        </section>

        <section>
          <h3 style={{ margin: "0 0 6px" }}>Erfahrung</h3>
          <p className="pcd-hinweis" style={{ marginBottom: 6 }}>
            Reine Übersicht — Werte bleiben frei einstellbar, es gibt keine Kostenrechnung wie bei Personen.
          </p>
          <div className="bg-zeile">
            <label style={{ display: "flex", flexDirection: "column", gap: 2, fontSize: 12 }}>
              Gesamt vergeben
              <input
                type="number"
                min={0}
                value={erfahrung}
                onChange={(e) => setErfahrung(Math.max(0, Number(e.target.value)))}
                style={{ width: 90 }}
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 2, fontSize: 12 }}>
              Davon ausgegeben
              <input
                type="number"
                min={0}
                value={erfahrungAusgegeben}
                onChange={(e) => setErfahrungAusgegeben(Math.max(0, Number(e.target.value)))}
                style={{ width: 90 }}
              />
            </label>
            <span style={{ alignSelf: "flex-end", color: "var(--text-leise)", fontSize: 13 }}>
              {Math.max(0, erfahrung - erfahrungAusgegeben)} verfügbar
            </span>
          </div>
        </section>

        {art === "KI" && (
          <EinflussVerwaltung campaignId={campaignId} begleiter={begleiter} onGeaendert={onEinflussGeaendert} />
        )}

        <div className="bg-zeile">
          <button type="button" onClick={sichern} disabled={sendet}>
            {sendet ? "Wird gespeichert…" : "Speichern"}
          </button>
          <button
            type="button"
            style={{ borderColor: "var(--signal)", color: "var(--signal)", marginLeft: "auto" }}
            onClick={() => setLoeschenOffen(true)}
          >
            Entfernen
          </button>
        </div>
      </div>

      {loeschenOffen && (
        <Bestaetigung
          titel={`${begleiter.name} entfernen?`}
          text="Der Begleiter wird endgültig gelöscht, samt Einfluss-Verknüpfungen."
          jaText="Entfernen"
          onJa={entfernen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </Fenster>
  );
}
