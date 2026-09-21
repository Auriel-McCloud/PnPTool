import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { entitiesApi, type CritterEintrag, type KiEintrag, type Person } from "../entities/api";
import { KACHEL_STIL, useProSeite } from "../items/kachelraster";
import { parseRichText, serializeRichText } from "../richtext/content";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { DotPool } from "../traits/DotPool";
import { StufenBlatt } from "../traits/StufenBlatt";
import { ART_NAMEN, ART_SYMBOLE, begleiterApi, type Begleiter, type BegleiterArt } from "./api";
import { BegleiterBild } from "./BegleiterBild";
import { CritterFenster } from "./CritterFenster";
import { KiFenster } from "./KiFenster";
import "../items/gegenstaende.css";
import "./begleiter.css";

/**
 * Begleiter anlegen und pflegen — Sprites, Geister, Verbündete.
 *
 * Sie hängen an einer Person und teilen sich das Grundblatt mit Drohnen und
 * Fahrzeugen. Wer einem Spielercharakter zugeordnet ist, wird beim Anlegen
 * automatisch für ihn sichtbar; sonst müsste die Spielleitung bei jedem
 * Sprite daran denken, und vergässe sie es, stünde der Neuroweaver ohne da.
 *
 * **KI und CRITTER sind seit 20.09.2026 KEINE Begleiter-Arten mehr** — erst
 * Mark: "wir machen critter zu richtigen NPCs", dann "mach jetzt das Gleiche
 * für die KI". Beide sind echte `Person`-Knoten (`istCritter`/`istKI`),
 * erscheinen aber trotzdem in dieser Übersicht (gemischt mit den echten
 * Begleitern) und lassen sich auch hier anlegen — mit dem vollen
 * Charakterblatt statt des Drohne/Fahrzeug-Blatts, siehe `CritterFenster`/
 * `KiFenster`. Bei KI ersetzt Matrix-Präsenz die körperlichen Attribute auf
 * dem Blatt (`traits/bogenApi.ts::ATTRIBUT_KATEGORIEN_KI`), Einfluss-Kanten
 * auf Orte/Fraktionen/Events/Gegenstände laufen über `entities/api.ts`.
 *
 * **Kachelraster + Anlegen-Popup (20.09.2026)**: dasselbe Muster wie
 * GegenstaendeUebersicht/PartyVerwaltung — Suchfeld über Name/Art/Besitzer,
 * "+ Neuer Begleiter" öffnet ein Fenster statt eines Inline-Formulars.
 *
 * **Bearbeiten-Fenster-Reihenfolge (20.09.2026, Mark: "man will das
 * Charakterblatt sehen")**: Bild und Werte stehen oben, selten gebrauchte
 * Verwaltung (Name/Art ändern, Verbindung, Beziehung) ganz unten — vorher
 * stand die Verwaltung zuerst und verdrängte das eigentliche Blatt nach
 * unten aus dem Blick.
 */

const ARTEN: BegleiterArt[] = ["SPRITE", "GEIST", "BEGLEITER"];

/** Eine Kachel in der gemeinsamen Übersicht — ein echter Begleiter, ein
 * Critter oder eine KI (beide Person mit istCritter/istKI). Gemeinsames
 * schlankes Format, damit Suche/Raster/Pagination alle drei Arten gleich
 * behandeln können. */
interface KachelEintrag {
  id: string;
  name: string;
  bildUrl: string;
  besitzerName: string | null;
  suchtext: string;
  art: "CRITTER" | "KI_PERSON" | BegleiterArt;
  stufe: number;
  quelle:
    | { kind: "begleiter"; daten: Begleiter }
    | { kind: "critter"; daten: CritterEintrag }
    | { kind: "ki"; daten: KiEintrag };
}

export function BegleiterVerwaltung({ campaignId }: { campaignId: string }) {
  const [alle, setAlle] = useState<Begleiter[]>([]);
  const [critter, setCritter] = useState<CritterEintrag[]>([]);
  const [kiListe, setKiListe] = useState<KiEintrag[]>([]);
  const [personen, setPersonen] = useState<Person[]>([]);
  const [laden, setLaden] = useState(true);
  const [offen, setOffen] = useState<Begleiter | null>(null);
  const [critterOffen, setCritterOffen] = useState<CritterEintrag | null>(null);
  const [kiOffen, setKiOffen] = useState<KiEintrag | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [suche, setSuche] = useState("");
  const rasterRef = useRef<HTMLDivElement>(null);
  const proSeite = useProSeite(rasterRef);
  const [seite, setSeite] = useState(0);

  async function neuLaden() {
    const [b, c, k, p] = await Promise.all([
      begleiterApi.liste(campaignId),
      entitiesApi.listCritter(campaignId),
      entitiesApi.listKi(campaignId),
      entitiesApi.listPersonen(campaignId),
    ]);
    setAlle(b);
    setCritter(c);
    setKiListe(k);
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

  // Alle drei Arten zu einer gemeinsamen Kachel-Liste zusammenführen — Mark,
  // 20.09.2026: Critter und KI bleiben trotz eigenem NPC-Blatt Teil der
  // Begleiter-Übersicht, nicht nur der normalen NPC-Liste.
  const kacheln = useMemo<KachelEintrag[]>(() => {
    const b: KachelEintrag[] = alle.map((x) => ({
      id: x.id,
      name: x.name,
      bildUrl: x.bildUrl,
      besitzerName: x.besitzerName,
      suchtext: `${x.name} ${ART_NAMEN[x.art]} ${x.besitzerName ?? ""}`.toLowerCase(),
      art: x.art,
      stufe: x.stufe,
      quelle: { kind: "begleiter", daten: x },
    }));
    const c: KachelEintrag[] = critter.map((x) => ({
      id: x.id,
      name: x.name,
      bildUrl: x.bildUrl,
      besitzerName: x.besitzerName,
      suchtext: `${x.name} Critter ${x.besitzerName ?? ""}`.toLowerCase(),
      art: "CRITTER",
      stufe: 0,
      quelle: { kind: "critter", daten: x },
    }));
    const k: KachelEintrag[] = kiListe.map((x) => ({
      id: x.id,
      name: x.name,
      bildUrl: x.bildUrl,
      besitzerName: x.besitzerName,
      suchtext: `${x.name} KI ${x.besitzerName ?? ""}`.toLowerCase(),
      art: "KI_PERSON",
      stufe: 0,
      quelle: { kind: "ki", daten: x },
    }));
    return [...b, ...c, ...k].sort((x, y) => x.name.localeCompare(y.name, "de"));
  }, [alle, critter, kiListe]);

  // Sucht über Name, Art und Besitzer — analog zur Gegenstände-/Party-Suche
  // ("alle Sprites von Kira" statt exaktem Namen).
  const gefiltert = useMemo(() => {
    const s = suche.trim().toLowerCase();
    if (!s) return kacheln;
    return kacheln.filter((k) => k.suchtext.includes(s));
  }, [kacheln, suche]);

  // Nach einer neuen Suche kann die aktuelle Seite hinter dem gefilterten
  // Ende liegen — zurück auf die erste Seite, sonst wirkt die Liste leer.
  useEffect(() => {
    setSeite(0);
  }, [suche]);

  const seiten = Math.max(1, Math.ceil(gefiltert.length / proSeite));
  const aktuelleSeite = Math.min(seite, seiten - 1);
  const sichtbar = gefiltert.slice(aktuelleSeite * proSeite, (aktuelleSeite + 1) * proSeite);

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Begleiter…</p>;

  function symbolVon(k: KachelEintrag) {
    if (k.art === "CRITTER") return "❖";
    if (k.art === "KI_PERSON") return "⌬";
    return ART_SYMBOLE[k.art];
  }

  function namenVon(k: KachelEintrag) {
    if (k.art === "CRITTER") return "Critter";
    if (k.art === "KI_PERSON") return "KI";
    return ART_NAMEN[k.art];
  }

  function kachelOeffnen(k: KachelEintrag) {
    if (k.quelle.kind === "begleiter") setOffen(k.quelle.daten);
    else if (k.quelle.kind === "critter") setCritterOffen(k.quelle.daten);
    else setKiOffen(k.quelle.daten);
  }

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
          {gefiltert.length} von {kacheln.length}
        </span>
      </div>

      <div className="gg-raster" ref={rasterRef}>
        {sichtbar.map((k) => (
          <button key={k.id} type="button" className="gg-kachel" onClick={() => kachelOeffnen(k)} title={k.name}>
            <span className="gg-kachel-bild">
              {k.bildUrl ? <img src={k.bildUrl} alt="" /> : <span aria-hidden="true">{symbolVon(k)}</span>}
            </span>
            <span className="gg-kachel-name">{k.name}</span>
            <span className="gg-kachel-zeile">
              {namenVon(k)}
              {k.stufe > 0 && ` · Stufe ${k.stufe}`}
            </span>
            <span className="gg-kachel-marken">
              {k.besitzerName ? (
                <span className="gg-marke">{k.besitzerName}</span>
              ) : (
                <span className="gg-marke">ungebunden</span>
              )}
            </span>
          </button>
        ))}
      </div>

      {kacheln.length === 0 && <p className="gg-leer">Noch keine Begleiter in dieser Kampagne.</p>}
      {kacheln.length > 0 && gefiltert.length === 0 && <p className="gg-leer">Nichts gefunden.</p>}

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
        onCritterAngelegt={async (neuerCritterId) => {
          setAnlegenOffen(false);
          await neuLaden();
          const gefunden = await entitiesApi.listCritter(campaignId);
          setCritter(gefunden);
          setCritterOffen(gefunden.find((c) => c.id === neuerCritterId) ?? null);
        }}
        onKiAngelegt={async (neueKiId) => {
          setAnlegenOffen(false);
          await neuLaden();
          const gefunden = await entitiesApi.listKi(campaignId);
          setKiListe(gefunden);
          setKiOffen(gefunden.find((k) => k.id === neueKiId) ?? null);
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
          // Bild ändert sich sofort über die eigene API, ohne dass der Rest
          // des Formulars mitgespeichert werden soll — das Fenster bleibt
          // offen (dasselbe Muster wie Mitglied-Hinzufügen in PartyVerwaltung).
          onSofortGeaendert={(neu) => {
            setAlle((alt) => alt.map((b) => (b.id === neu.id ? neu : b)));
            setOffen(neu);
          }}
        />
      )}

      {critterOffen && (
        <CritterFenster
          campaignId={campaignId}
          critterId={critterOffen.id}
          besitzerId={critterOffen.besitzerId}
          personen={personenNamen}
          onSchliessen={() => setCritterOffen(null)}
          onGeaendert={async () => {
            await neuLaden();
            setCritterOffen(null);
          }}
        />
      )}

      {kiOffen && (
        <KiFenster
          campaignId={campaignId}
          kiId={kiOffen.id}
          besitzerId={kiOffen.besitzerId}
          personen={personenNamen}
          onSchliessen={() => setKiOffen(null)}
          onGeaendert={async () => {
            await neuLaden();
            setKiOffen(null);
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

/** Kleine Überschrift für einen ausklappbaren/selten gebrauchten Abschnitt. */
function AbschnittTitel({ children }: { children: React.ReactNode }) {
  return (
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
      {children}
    </span>
  );
}

/**
 * Anlegen-Popup: Name, Art und gleich die Besitzer-Auswahl (Verbindung) in
 * einem Commlink-Fenster statt des früheren Inline-Formulars in der
 * Kopfzeile — Mark, 20.09.2026: Suche + "+"-Popup wie bei den anderen
 * Bereichen. Art umfasst neben den echten Begleiter-Arten auch Critter und
 * KI — beide legen im Hintergrund einen NPC statt eines Begleiters an.
 */
function BegleiterAnlegenFenster({
  offen,
  campaignId,
  personen,
  onSchliessen,
  onAngelegt,
  onCritterAngelegt,
  onKiAngelegt,
}: {
  offen: boolean;
  campaignId: string;
  personen: { id: string; label: string }[];
  onSchliessen: () => void;
  onAngelegt: (neu: Begleiter) => void;
  onCritterAngelegt: (neuerCritterId: string) => void;
  onKiAngelegt: (neueKiId: string) => void;
}) {
  const [name, setName] = useState("");
  const [art, setArt] = useState<BegleiterArt | "CRITTER" | "KI_PERSON">("SPRITE");
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
      if (art === "CRITTER" || art === "KI_PERSON") {
        // Critter/KI (20.09.2026, revidiert): echter NPC statt Begleiter-Art
        // — Mark: "wir machen critter zu richtigen NPCs" / "mach jetzt das
        // Gleiche für die KI". Volles Charakterblatt statt des
        // Drohne/Fahrzeug-Blatts.
        const neu = await entitiesApi.createPerson(campaignId, {
          name: name.trim(),
          personType: "NPC",
          description: "",
          notes: "",
          istCritter: art === "CRITTER",
          istKI: art === "KI_PERSON",
          sichtbarkeit: "GM",
          sichtbarFuer: [],
          notizenSichtbarkeit: "GM",
          notizenSichtbarFuer: [],
        });
        if (besitzer) {
          if (art === "CRITTER") await entitiesApi.critterBesitzer(campaignId, neu.id, besitzer);
          else await entitiesApi.kiBesitzer(campaignId, neu.id, besitzer);
        }
        if (art === "CRITTER") onCritterAngelegt(neu.id);
        else onKiAngelegt(neu.id);
        return;
      }
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
          <select value={art} onChange={(e) => setArt(e.target.value as BegleiterArt | "CRITTER" | "KI_PERSON")}>
            {ARTEN.map((a) => (
              <option key={a} value={a}>
                {ART_SYMBOLE[a]} {ART_NAMEN[a]}
              </option>
            ))}
            <option value="CRITTER">❖ Critter</option>
            <option value="KI_PERSON">⌬ KI</option>
          </select>
        </div>

        {(art === "CRITTER" || art === "KI_PERSON") && (
          <p className="pcd-hinweis" style={{ margin: 0 }}>
            Bekommt das volle NPC-Charakterblatt statt des Drohne/Fahrzeug-Blatts
            {art === "KI_PERSON" && " — Matrix-Präsenz statt körperlicher Attribute"}.
          </p>
        )}

        <div>
          <AbschnittTitel>Verbindung (optional)</AbschnittTitel>
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
  onSofortGeaendert,
}: {
  campaignId: string;
  begleiter: Begleiter;
  personen: { id: string; label: string }[];
  onSchliessen: () => void;
  onGeaendert: () => void;
  onSofortGeaendert: (neu: Begleiter) => void;
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
  // Erfahrung — reine Budget-Anzeige, keine Kostenrechnung.
  const [erfahrung, setErfahrung] = useState(begleiter.erfahrung);
  const [erfahrungAusgegeben, setErfahrungAusgegeben] = useState(begleiter.erfahrungAusgegeben);
  // Beschreibung als Rich-Text — dasselbe Muster wie bei Personen/Orten.
  const [beschreibungDoc, setBeschreibungDoc] = useState(parseRichText(begleiter.beschreibung));
  const [sendet, setSendet] = useState(false);
  const [speichertBeschreibung, setSpeichertBeschreibung] = useState(false);
  const [loeschenOffen, setLoeschenOffen] = useState(false);
  // Aktueller Begleiter-Stand für das Bild (das Fenster bekommt bei einem
  // reinen Bild-Upload keinen neuen `begleiter`-Prop, siehe onSofortGeaendert).
  const [aktuellerBegleiter, setAktuellerBegleiter] = useState(begleiter);

  useEffect(() => {
    setAktuellerBegleiter(begleiter);
  }, [begleiter]);

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

  async function beschreibungSpeichern() {
    setSpeichertBeschreibung(true);
    try {
      const neu = await begleiterApi.aendern(campaignId, begleiter.id, {
        beschreibung: serializeRichText(beschreibungDoc),
      });
      setAktuellerBegleiter(neu);
      onSofortGeaendert(neu);
    } finally {
      setSpeichertBeschreibung(false);
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
        <BegleiterBild
          campaignId={campaignId}
          begleiterId={begleiter.id}
          name={begleiter.name}
          bildUrl={aktuellerBegleiter.bildUrl}
          onGeaendert={async () => {
            const neu = await begleiterApi.aendern(campaignId, begleiter.id, {});
            setAktuellerBegleiter(neu);
            onSofortGeaendert(neu);
          }}
        />

        {/* Das eigentliche Blatt zuerst — Mark, 20.09.2026: "man will das
            Charakterblatt sehen". Name/Art/Verbindung/Beziehung folgen ganz
            unten, siehe Verwaltungsabschnitt. */}
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

        <div className="bg-zeile">
          <button type="button" onClick={sichern} disabled={sendet}>
            {sendet ? "Wird gespeichert…" : "Werte speichern"}
          </button>
        </div>

        {/* Beschreibung — Fließtext, deshalb unter den Werten statt dazwischen. */}
        <section>
          <h3 style={{ margin: "0 0 6px" }}>Beschreibung</h3>
          <RichTextEditor content={beschreibungDoc} onChange={setBeschreibungDoc} minHeight={100} />
          <button
            type="button"
            onClick={beschreibungSpeichern}
            disabled={speichertBeschreibung}
            style={{ marginTop: 6 }}
          >
            {speichertBeschreibung ? "Speichert…" : "Beschreibung speichern"}
          </button>
        </section>

        {/* Selten gebrauchte Verwaltung ganz unten — Mark, 20.09.2026: "man
            will das Charakterblatt sehen", nicht zuerst Name/Art/Verbindung
            ändern müssen. */}
        <section style={{ borderTop: "1px solid var(--linie)", paddingTop: 10, marginTop: 4 }}>
          <h3 style={{ margin: "0 0 6px" }}>Verwaltung</h3>

          <div className="bg-zeile">
            <label style={{ display: "flex", flexDirection: "column", gap: 3, flex: "1 1 200px" }}>
              <AbschnittTitel>Name</AbschnittTitel>
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 3 }}>
              <AbschnittTitel>Art</AbschnittTitel>
              <select value={art} onChange={(e) => setArt(e.target.value as BegleiterArt)}>
                {ARTEN.map((a) => (
                  <option key={a} value={a}>
                    {ART_NAMEN[a]}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="bg-zeile" style={{ flexDirection: "column", alignItems: "stretch", gap: 3, marginTop: 8 }}>
            <AbschnittTitel>Beziehung</AbschnittTitel>
            <input
              value={beziehung}
              onChange={(e) => setBeziehung(e.target.value)}
              placeholder="Wie steht er zu seinem Menschen?"
            />
          </label>

          <div style={{ marginTop: 8 }}>
            <AbschnittTitel>Verbindung</AbschnittTitel>
            <BesitzerAuswahl personen={personen} wert={besitzer} onWaehlen={setBesitzer} />
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

      {loeschenOffen && (
        <Bestaetigung
          titel={`${begleiter.name} entfernen?`}
          text="Der Begleiter wird endgültig gelöscht."
          jaText="Entfernen"
          onJa={entfernen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </Fenster>
  );
}
