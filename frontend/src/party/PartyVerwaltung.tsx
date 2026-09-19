import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { entitiesApi, type Event as EntitiesEvent, type Ort, type Person } from "../entities/api";
import { KACHEL_STIL, useProSeite } from "../items/kachelraster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { Fenster } from "../shell/Fenster";
import { partyApi, type Party } from "./api";
import "../items/gegenstaende.css";
import "./party.css";

/**
 * Party-Verwaltung — wer gerade zusammen unterwegs ist.
 *
 * Anders als Fraktionen (dauerhafte Organisationen mit Zielen/Ressourcen)
 * ist eine Party schlicht "wer gerade beisammen ist" — Mitglieder und
 * Aufenthaltsort können sich jederzeit ändern, die Party selbst bleibt aber
 * bestehen (kein Wegwerfobjekt, Marks Entscheidung 18.09.2026).
 *
 * **Genau eine Party pro Kampagne ist "aktiv"** — die gerade bespielte.
 * Ihr Aufenthaltsort soll später die Musik auslösen (Spotify/Yamaha-
 * MusicCast, noch nicht gebaut). Aktivieren einer Party deaktiviert
 * automatisch alle anderen serverseitig.
 */

export function PartyVerwaltung({ campaignId }: { campaignId: string }) {
  const [alle, setAlle] = useState<Party[]>([]);
  const [personen, setPersonen] = useState<Person[]>([]);
  const [orte, setOrte] = useState<Ort[]>([]);
  const [events, setEvents] = useState<EntitiesEvent[]>([]);
  const [laden, setLaden] = useState(true);
  const [offen, setOffen] = useState<Party | null>(null);
  const [anlegenOffen, setAnlegenOffen] = useState(false);
  const [suche, setSuche] = useState("");
  const rasterRef = useRef<HTMLDivElement>(null);
  const proSeite = useProSeite(rasterRef);
  const [seite, setSeite] = useState(0);

  async function neuLaden() {
    const [p, per, o, e] = await Promise.all([
      partyApi.liste(campaignId),
      entitiesApi.listPersonen(campaignId),
      entitiesApi.listOrte(campaignId),
      entitiesApi.listEvents(campaignId),
    ]);
    setAlle(p);
    setPersonen(per);
    setOrte(o);
    setEvents(e);
  }

  useEffect(() => {
    setLaden(true);
    neuLaden().finally(() => setLaden(false));
  }, [campaignId]);

  // Sucht über Name, Beschreibung, Mitgliedernamen und Aufenthaltsort — analog
  // zur Gegenstände-Suche ("alle Waffen von Kira" statt exaktem Namen), damit
  // man bei vielen Partys nicht erst jede Kachel einzeln aufklappen muss.
  const gefiltert = useMemo(() => {
    const s = suche.trim().toLowerCase();
    if (!s) return alle;
    return alle.filter((p) => {
      if (p.name.toLowerCase().includes(s)) return true;
      if (p.beschreibung.toLowerCase().includes(s)) return true;
      if (p.aufenthaltsortName?.toLowerCase().includes(s)) return true;
      return p.mitglieder.some((m) => m.name.toLowerCase().includes(s));
    });
  }, [alle, suche]);

  // Nach einer neuen Suche kann die aktuelle Seite hinter dem gefilterten
  // Ende liegen — zurück auf die erste Seite, sonst wirkt die Liste leer.
  useEffect(() => {
    setSeite(0);
  }, [suche]);

  const seiten = Math.max(1, Math.ceil(gefiltert.length / proSeite));
  const aktuelleSeite = Math.min(seite, seiten - 1);
  const sichtbar = gefiltert.slice(aktuelleSeite * proSeite, (aktuelleSeite + 1) * proSeite);

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Partys…</p>;

  return (
    <div className="gg-seite" style={KACHEL_STIL}>
      <div className="gg-kopf">
        <input
          className="gg-suche"
          type="search"
          placeholder="Suchen — Name, Mitglied oder Aufenthaltsort"
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
        />
        <button type="button" onClick={() => setAnlegenOffen(true)}>
          + Neue Party
        </button>
        <span className="gg-anzahl">
          {gefiltert.length} von {alle.length}
        </span>
      </div>

      <div className="gg-raster" ref={rasterRef}>
        {sichtbar.map((p) => (
          <button
            key={p.id}
            type="button"
            className="gg-kachel"
            data-aktiv={p.aktiv ? "true" : undefined}
            onClick={() => setOffen(p)}
            title={p.name}
          >
            <span className="gg-kachel-bild">
              <span aria-hidden="true">👥</span>
            </span>
            <span className="gg-kachel-name">{p.name}</span>
            <span className="gg-kachel-zeile">
              {p.mitglieder.length} {p.mitglieder.length === 1 ? "Mitglied" : "Mitglieder"}
              {p.aufenthaltsortName && ` · ${p.aufenthaltsortName}`}
            </span>
            <span className="gg-kachel-marken">
              {p.aktiv && <span className="gg-marke pt-marke-aktiv">Aktiv</span>}
              {!p.aufenthaltsortName && <span className="gg-marke">unterwegs</span>}
            </span>
          </button>
        ))}
      </div>

      {alle.length === 0 && <p className="gg-leer">Noch keine Partys in dieser Kampagne.</p>}
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

      <PartyAnlegenFenster
        offen={anlegenOffen}
        campaignId={campaignId}
        personen={personen}
        onSchliessen={() => setAnlegenOffen(false)}
        onAngelegt={async (neu) => {
          setAnlegenOffen(false);
          await neuLaden();
          setOffen(neu);
        }}
      />

      {offen && (
        <PartyFenster
          key={offen.id}
          campaignId={campaignId}
          party={alle.find((p) => p.id === offen.id) ?? offen}
          personen={personen}
          orte={orte}
          events={events}
          onSchliessen={() => setOffen(null)}
          // Fenster bleibt nach jeder Änderung offen — der Sinn ist ja gerade,
          // sofort zu sehen wer jetzt in der Party ist, nicht nach jedem
          // Mitglied-Hinzufügen neu zu öffnen (Marks Feedback 19.09.2026).
          onGeaendert={() => {
            neuLaden();
          }}
          onGeloescht={async () => {
            await neuLaden();
            setOffen(null);
          }}
        />
      )}
    </div>
  );
}

/**
 * Durchsuchbare Personen-Checkbox-Liste — gemeinsam genutzt beim Anlegen
 * (Mitglieder gleich mit auswählen) und beim Bearbeiten (weitere Mitglieder
 * hinzufügen). Eigenes Suchfeld pro Instanz, weil beide Stellen unabhängig
 * voneinander durchsucht werden — beim Anlegen alle Personen, beim
 * Bearbeiten nur die noch nicht zugeordneten.
 */
function PersonenAuswahlListe({
  personen,
  ausgewaehlt,
  onUmschalten,
  leerText,
}: {
  personen: Person[];
  ausgewaehlt: Set<string>;
  onUmschalten: (personId: string) => void;
  leerText: string;
}) {
  const [suche, setSuche] = useState("");

  const gefiltert = useMemo(() => {
    const s = suche.trim().toLowerCase();
    if (!s) return personen;
    return personen.filter(
      (p) => p.name.toLowerCase().includes(s) || p.personType.toLowerCase().includes(s),
    );
  }, [personen, suche]);

  if (personen.length === 0) {
    return <p className="pt-hinweis">{leerText}</p>;
  }

  return (
    <div className="pt-feld">
      <input
        type="search"
        className="pt-suchfeld"
        placeholder="Suchen — Name oder Typ…"
        value={suche}
        onChange={(e) => setSuche(e.target.value)}
      />
      <div className="pt-auswahl-liste">
        {gefiltert.length === 0 ? (
          <p className="pt-hinweis">Nichts gefunden.</p>
        ) : (
          gefiltert.map((p) => (
            <label key={p.id} className="pt-auswahl-zeile">
              <input type="checkbox" checked={ausgewaehlt.has(p.id)} onChange={() => onUmschalten(p.id)} />
              <span>{p.name}</span>
              <em className="pt-typ">{p.personType}</em>
            </label>
          ))
        )}
      </div>
    </div>
  );
}

/**
 * Anlegen-Popup: Name plus gleich die Mitgliederauswahl, damit man nicht
 * extra ins Bearbeiten-Fenster wechseln muss, um die Gruppe zu füllen
 * (Marks Wunsch — vorher gab es dafür nur ein Inline-Formular ohne
 * Mitgliederauswahl, das aus dem Commlink-Stil fiel).
 */
function PartyAnlegenFenster({
  offen,
  campaignId,
  personen,
  onSchliessen,
  onAngelegt,
}: {
  offen: boolean;
  campaignId: string;
  personen: Person[];
  onSchliessen: () => void;
  onAngelegt: (neu: Party) => void;
}) {
  const [name, setName] = useState("");
  const [ausgewaehlt, setAusgewaehlt] = useState<Set<string>>(new Set());
  const [sendet, setSendet] = useState(false);

  // Frisch beginnen bei jedem Öffnen — sonst stehen noch die Häkchen der
  // zuletzt angelegten Party da.
  useEffect(() => {
    if (offen) {
      setName("");
      setAusgewaehlt(new Set());
    }
  }, [offen]);

  function umschalten(personId: string) {
    setAusgewaehlt((alt) => {
      const neu = new Set(alt);
      if (neu.has(personId)) neu.delete(personId);
      else neu.add(personId);
      return neu;
    });
  }

  async function anlegen(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSendet(true);
    try {
      let party = await partyApi.anlegen(campaignId, { name: name.trim() });
      // Nacheinander statt Promise.all: jedes Hinzufügen liefert die neue
      // Party zurück, und die Reihenfolge in der Mitgliederliste soll der
      // Auswahlreihenfolge folgen, nicht der Antwortzeit der Requests.
      for (const personId of ausgewaehlt) {
        party = await partyApi.mitgliedHinzufuegen(campaignId, party.id, personId);
      }
      onAngelegt(party);
    } finally {
      setSendet(false);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel="Neue Party"
      unterzeile="Name und optional gleich die Mitglieder"
      kennung="party-neu"
      onSchliessen={onSchliessen}
    >
      <form onSubmit={anlegen} className="pt-formular">
        <input
          type="text"
          placeholder="Name der Party"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          autoFocus
        />

        <div className="pt-feld">
          <span className="pt-label">Mitglieder (optional)</span>
          <PersonenAuswahlListe
            personen={personen}
            ausgewaehlt={ausgewaehlt}
            onUmschalten={umschalten}
            leerText="Noch keine Personen in dieser Kampagne."
          />
        </div>

        <button type="submit" disabled={sendet}>
          {sendet ? "Wird angelegt…" : "Anlegen"}
        </button>
      </form>
    </Fenster>
  );
}

/**
 * Mitglied-Hinzufügen-Liste im Bearbeiten-Fenster: Klick fügt sofort hinzu,
 * kein Zwischenschritt über ein Dropdown. Bekommt nur noch nicht zugeordnete
 * Personen — wer schon Mitglied ist, taucht hier nicht mehr auf.
 */
function MitgliedHinzufuegenListe({
  personen,
  onHinzufuegen,
}: {
  personen: Person[];
  onHinzufuegen: (personId: string) => void;
}) {
  const [suche, setSuche] = useState("");

  const gefiltert = useMemo(() => {
    const s = suche.trim().toLowerCase();
    if (!s) return personen;
    return personen.filter(
      (p) => p.name.toLowerCase().includes(s) || p.personType.toLowerCase().includes(s),
    );
  }, [personen, suche]);

  if (personen.length === 0) {
    return <p className="pt-hinweis">Alle Personen sind bereits einer Party zugeordnet.</p>;
  }

  return (
    <div className="pt-feld">
      <input
        type="search"
        className="pt-suchfeld"
        placeholder="Person hinzufügen — suchen…"
        value={suche}
        onChange={(e) => setSuche(e.target.value)}
      />
      <div className="pt-auswahl-liste">
        {gefiltert.length === 0 ? (
          <p className="pt-hinweis">Nichts gefunden.</p>
        ) : (
          gefiltert.map((p) => (
            <button
              key={p.id}
              type="button"
              className="pt-auswahl-zeile pt-auswahl-hinzufuegen"
              onClick={() => onHinzufuegen(p.id)}
            >
              <span>{p.name}</span>
              <em className="pt-typ">{p.personType}</em>
              <span className="pt-plus" aria-hidden="true">
                +
              </span>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

/**
 * Ziel-Auswahl für "Aufenthaltsort/Ereignis" — durchsucht Orte und Events
 * gemeinsam, weil beide gleichwertige Ziele sind (Marks Wunsch 19.09.2026:
 * auch hier soll man suchen können statt eine lange Select-Liste
 * durchzuscrollen).
 */
function ZielAuswahl({
  orte,
  events,
  wert,
  onWaehlen,
}: {
  orte: Ort[];
  events: EntitiesEvent[];
  wert: string;
  onWaehlen: (neuesZiel: string) => void;
}) {
  const [suche, setSuche] = useState("");

  const eintraege = useMemo(() => {
    const alle = [
      ...orte.map((o) => ({ wert: `Ort:${o.id}`, label: o.name, symbol: "⌖" })),
      ...events.map((e) => ({ wert: `Event:${e.id}`, label: e.title, symbol: "◆" })),
    ];
    const s = suche.trim().toLowerCase();
    return s ? alle.filter((e) => e.label.toLowerCase().includes(s)) : alle;
  }, [orte, events, suche]);

  return (
    <div className="pt-feld">
      <input
        type="search"
        className="pt-suchfeld"
        placeholder="Suchen — Ort oder Ereignis…"
        value={suche}
        onChange={(e) => setSuche(e.target.value)}
      />
      <div className="pt-auswahl-liste">
        <label className="pt-auswahl-zeile">
          <input type="radio" name="pt-ziel" checked={wert === ""} onChange={() => onWaehlen("")} />
          <span>— unterwegs, kein fester Ort —</span>
        </label>
        {eintraege.length === 0 && suche && <p className="pt-hinweis">Nichts gefunden.</p>}
        {eintraege.map((e) => (
          <label key={e.wert} className="pt-auswahl-zeile">
            <input type="radio" name="pt-ziel" checked={wert === e.wert} onChange={() => onWaehlen(e.wert)} />
            <span>
              {e.symbol} {e.label}
            </span>
          </label>
        ))}
      </div>
    </div>
  );
}

function PartyFenster({
  campaignId,
  party,
  personen,
  orte,
  events,
  onSchliessen,
  onGeaendert,
  onGeloescht,
}: {
  campaignId: string;
  party: Party;
  personen: Person[];
  orte: Ort[];
  events: EntitiesEvent[];
  onSchliessen: () => void;
  onGeaendert: () => void;
  onGeloescht: () => void;
}) {
  const [name, setName] = useState(party.name);
  const [beschreibung, setBeschreibung] = useState(party.beschreibung);
  const [notizen, setNotizen] = useState(party.notizen);
  const [loeschenOffen, setLoeschenOffen] = useState(false);
  const [ziel, setZiel] = useState(
    party.aufenthaltsortId ? `${party.aufenthaltsortKind}:${party.aufenthaltsortId}` : "",
  );
  const [musikHinweis, setMusikHinweis] = useState<string | null>(null);

  // Wer noch keiner Party angehört, oder aktuell dieser hier — die Auswahl
  // soll niemanden zeigen, der bereits woanders Mitglied ist, sonst wirkt
  // der automatische Wechsel überraschend.
  const bereitsMitglied = new Set(party.mitglieder.map((m) => m.id));
  const wählbarePersonen = useMemo(
    () => personen.filter((p) => !bereitsMitglied.has(p.id)),
    [personen, party.mitglieder],
  );

  // Name, Beschreibung und Notizen speichern erst beim Verlassen des Felds
  // (onBlur) statt über einen eigenen Speichern-Knopf — dasselbe Muster wie
  // FraktionDetail/OrtDetail/EventDetail. Leerer Name würde die Party in
  // jeder Liste unauffindbar machen, dann lieber den alten behalten.
  async function nameSpeichern() {
    const sauber = name.trim();
    if (!sauber) {
      setName(party.name);
      return;
    }
    if (sauber === party.name) return;
    await partyApi.aendern(campaignId, party.id, { name: sauber });
    onGeaendert();
  }

  async function beschreibungSpeichern() {
    if (beschreibung === party.beschreibung) return;
    await partyApi.aendern(campaignId, party.id, { beschreibung });
    onGeaendert();
  }

  async function notizenSpeichern() {
    if (notizen === party.notizen) return;
    await partyApi.aendern(campaignId, party.id, { notizen });
    onGeaendert();
  }

  async function mitgliedHinzufuegen(personId: string) {
    await partyApi.mitgliedHinzufuegen(campaignId, party.id, personId);
    onGeaendert();
  }

  async function mitgliedEntfernen(personId: string) {
    await partyApi.mitgliedEntfernen(campaignId, party.id, personId);
    onGeaendert();
  }

  async function aufenthaltsortSpeichern(neuesZiel: string) {
    setZiel(neuesZiel);
    setMusikHinweis(null);
    let ergebnis: Party;
    if (!neuesZiel) {
      ergebnis = await partyApi.aufenthaltsortSetzen(campaignId, party.id, null, null);
    } else {
      const [kind, id] = neuesZiel.split(":");
      ergebnis = await partyApi.aufenthaltsortSetzen(campaignId, party.id, id, kind as "Ort" | "Event");
    }
    if (ergebnis.musikHinweis) setMusikHinweis(ergebnis.musikHinweis);
    onGeaendert();
  }

  async function aktivSchalten() {
    setMusikHinweis(null);
    if (party.aktiv) {
      await partyApi.deaktivieren(campaignId, party.id);
    } else {
      const ergebnis = await partyApi.aktivieren(campaignId, party.id);
      if (ergebnis.musikHinweis) setMusikHinweis(ergebnis.musikHinweis);
    }
    onGeaendert();
  }

  async function loeschen() {
    setLoeschenOffen(false);
    await partyApi.entfernen(campaignId, party.id);
    onGeloescht();
  }

  return (
    <Fenster
      offen
      titel={`👥 ${party.name}`}
      unterzeile={party.aktiv ? "Aktive Party" : "Nicht aktiv"}
      kennung={`party-bearbeiten:${party.id}`}
      onSchliessen={onSchliessen}
    >
      <div className="pt-formular">
        <button
          type="button"
          className="pt-aktiv-schalter"
          data-aktiv={party.aktiv ? "true" : undefined}
          onClick={aktivSchalten}
          title="Nur eine Party pro Kampagne kann aktiv sein — Aktivieren deaktiviert automatisch alle anderen"
        >
          {party.aktiv ? "★ Aktive Party" : "☆ Als aktive Party festlegen"}
        </button>
        {musikHinweis && <p className="pt-hinweis">{musikHinweis}</p>}

        <section>
          <h3 style={{ margin: "10px 0 6px" }}>Mitglieder ({party.mitglieder.length})</h3>
          {party.mitglieder.length === 0 && <p className="gg-leer">Noch niemand in dieser Party.</p>}
          {party.mitglieder.map((m) => (
            <div key={m.id} className="pt-zeile pt-mitglied">
              <span>
                {m.name} <em className="pt-typ">{m.personType}</em>
              </span>
              <button
                type="button"
                onClick={() => mitgliedEntfernen(m.id)}
                style={{ marginLeft: "auto", borderColor: "var(--signal)", color: "var(--signal)" }}
              >
                Entfernen
              </button>
            </div>
          ))}
          <MitgliedHinzufuegenListe personen={wählbarePersonen} onHinzufuegen={mitgliedHinzufuegen} />
          <p className="pt-hinweis">
            Wer hier aufgenommen wird, verlässt automatisch eine etwaige vorherige Party — eine Person ist
            immer nur in höchstens einer Party gleichzeitig.
          </p>
        </section>

        <section>
          <h3 style={{ margin: "10px 0 6px" }}>Aufenthaltsort/Ereignis</h3>
          <ZielAuswahl orte={orte} events={events} wert={ziel} onWaehlen={aufenthaltsortSpeichern} />
        </section>

        <label className="pt-zeile" style={{ flexDirection: "column", alignItems: "stretch", gap: 3 }}>
          <span className="pt-label">Beschreibung</span>
          <textarea
            value={beschreibung}
            onChange={(e) => setBeschreibung(e.target.value)}
            onBlur={beschreibungSpeichern}
            rows={2}
            style={{ resize: "vertical" }}
          />
        </label>

        <label className="pt-zeile" style={{ flexDirection: "column", alignItems: "stretch", gap: 3 }}>
          <span className="pt-label">Notizen (nur SL)</span>
          <textarea
            value={notizen}
            onChange={(e) => setNotizen(e.target.value)}
            onBlur={notizenSpeichern}
            rows={2}
            style={{ resize: "vertical" }}
          />
        </label>

        {/* Ganz unten, bewusst abgesetzt: Umbenennen ist der Notfall, nicht
            der Regelfall — man will die Party an Mitgliedern/Ort erkennen,
            nicht am Namen herumspielen (Marks Wunsch 19.09.2026). */}
        <label className="pt-zeile" style={{ flexDirection: "column", alignItems: "stretch", gap: 3, marginTop: 6 }}>
          <span className="pt-label">Name</span>
          <input value={name} onChange={(e) => setName(e.target.value)} onBlur={nameSpeichern} />
        </label>

        <div className="pt-zeile" style={{ marginTop: 10 }}>
          <button
            type="button"
            style={{ borderColor: "var(--signal)", color: "var(--signal)", marginLeft: "auto" }}
            onClick={() => setLoeschenOffen(true)}
          >
            Party auflösen
          </button>
        </div>
      </div>

      {loeschenOffen && (
        <Bestaetigung
          titel={`${party.name} auflösen?`}
          text="Mitglieder verlieren nur ihre Zugehörigkeit zu dieser Party, die Personen selbst bleiben unangetastet."
          jaText="Auflösen"
          onJa={loeschen}
          onNein={() => setLoeschenOffen(false)}
        />
      )}
    </Fenster>
  );
}
