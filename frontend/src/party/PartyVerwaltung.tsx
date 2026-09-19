import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { entitiesApi, type Event as EntitiesEvent, type Ort, type Person } from "../entities/api";
import { KACHEL_STIL, useProSeite } from "../items/kachelraster";
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

  const seiten = Math.max(1, Math.ceil(alle.length / proSeite));
  const aktuelleSeite = Math.min(seite, seiten - 1);
  const sichtbar = alle.slice(aktuelleSeite * proSeite, (aktuelleSeite + 1) * proSeite);

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Partys…</p>;

  return (
    <div className="gg-seite" style={KACHEL_STIL}>
      <div className="gg-kopf">
        <button type="button" onClick={() => setAnlegenOffen(true)}>
          + Neue Party
        </button>
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
          campaignId={campaignId}
          party={offen}
          personen={personen}
          orte={orte}
          events={events}
          onSchliessen={() => setOffen(null)}
          onGeaendert={async () => {
            await neuLaden();
            setOffen(null);
          }}
        />
      )}
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
          {personen.length === 0 ? (
            <p className="pt-hinweis">Noch keine Personen in dieser Kampagne.</p>
          ) : (
            <div className="pt-auswahl-liste">
              {personen.map((p) => (
                <label key={p.id} className="pt-auswahl-zeile">
                  <input type="checkbox" checked={ausgewaehlt.has(p.id)} onChange={() => umschalten(p.id)} />
                  <span>{p.name}</span>
                  <em className="pt-typ">{p.personType}</em>
                </label>
              ))}
            </div>
          )}
        </div>

        <button type="submit" disabled={sendet}>
          {sendet ? "Wird angelegt…" : "Anlegen"}
        </button>
      </form>
    </Fenster>
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
}: {
  campaignId: string;
  party: Party;
  personen: Person[];
  orte: Ort[];
  events: EntitiesEvent[];
  onSchliessen: () => void;
  onGeaendert: () => void;
}) {
  const [name, setName] = useState(party.name);
  const [beschreibung, setBeschreibung] = useState(party.beschreibung);
  const [notizen, setNotizen] = useState(party.notizen);
  const [neuesMitglied, setNeuesMitglied] = useState("");
  const [ziel, setZiel] = useState(
    party.aufenthaltsortId ? `${party.aufenthaltsortKind}:${party.aufenthaltsortId}` : "",
  );
  const [sendet, setSendet] = useState(false);

  // Wer noch keiner Party angehört, oder aktuell dieser hier — die Auswahl
  // soll niemanden zeigen, der bereits woanders Mitglied ist, sonst wirkt
  // der automatische Wechsel überraschend.
  const bereitsMitglied = new Set(party.mitglieder.map((m) => m.id));
  const wählbarePersonen = useMemo(
    () => personen.filter((p) => !bereitsMitglied.has(p.id)),
    [personen, party.mitglieder],
  );

  async function stammdatenSpeichern() {
    setSendet(true);
    try {
      await partyApi.aendern(campaignId, party.id, { name, beschreibung, notizen });
      onGeaendert();
    } finally {
      setSendet(false);
    }
  }

  async function mitgliedHinzufuegen() {
    if (!neuesMitglied) return;
    await partyApi.mitgliedHinzufuegen(campaignId, party.id, neuesMitglied);
    setNeuesMitglied("");
    onGeaendert();
  }

  async function mitgliedEntfernen(personId: string) {
    await partyApi.mitgliedEntfernen(campaignId, party.id, personId);
    onGeaendert();
  }

  async function aufenthaltsortSpeichern(neuesZiel: string) {
    setZiel(neuesZiel);
    if (!neuesZiel) {
      await partyApi.aufenthaltsortSetzen(campaignId, party.id, null, null);
    } else {
      const [kind, id] = neuesZiel.split(":");
      await partyApi.aufenthaltsortSetzen(campaignId, party.id, id, kind as "Ort" | "Event");
    }
    onGeaendert();
  }

  async function aktivSchalten() {
    if (party.aktiv) {
      await partyApi.deaktivieren(campaignId, party.id);
    } else {
      await partyApi.aktivieren(campaignId, party.id);
    }
    onGeaendert();
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

        <div className="pt-zeile">
          <input value={name} onChange={(e) => setName(e.target.value)} style={{ flex: "1 1 200px" }} />
        </div>

        <label className="pt-zeile" style={{ flexDirection: "column", alignItems: "stretch", gap: 3 }}>
          <span className="pt-label">Beschreibung</span>
          <textarea
            value={beschreibung}
            onChange={(e) => setBeschreibung(e.target.value)}
            rows={2}
            style={{ resize: "vertical" }}
          />
        </label>

        <label className="pt-zeile" style={{ flexDirection: "column", alignItems: "stretch", gap: 3 }}>
          <span className="pt-label">Notizen (nur SL)</span>
          <textarea value={notizen} onChange={(e) => setNotizen(e.target.value)} rows={2} style={{ resize: "vertical" }} />
        </label>

        <button type="button" onClick={stammdatenSpeichern} disabled={sendet}>
          {sendet ? "Wird gespeichert…" : "Speichern"}
        </button>

        <section>
          <h3 style={{ margin: "10px 0 6px" }}>Aufenthaltsort</h3>
          <select value={ziel} onChange={(e) => aufenthaltsortSpeichern(e.target.value)}>
            <option value="">— unterwegs, kein fester Ort —</option>
            <optgroup label="Orte">
              {orte.map((o) => (
                <option key={o.id} value={`Ort:${o.id}`}>
                  {o.name}
                </option>
              ))}
            </optgroup>
            <optgroup label="Events">
              {events.map((e) => (
                <option key={e.id} value={`Event:${e.id}`}>
                  {e.title}
                </option>
              ))}
            </optgroup>
          </select>
        </section>

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
          <div className="pt-zeile" style={{ marginTop: 6 }}>
            <select value={neuesMitglied} onChange={(e) => setNeuesMitglied(e.target.value)} style={{ flex: "1 1 200px" }}>
              <option value="">— Person wählen —</option>
              {wählbarePersonen.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.personType})
                </option>
              ))}
            </select>
            <button type="button" onClick={mitgliedHinzufuegen} disabled={!neuesMitglied}>
              Hinzufügen
            </button>
          </div>
          <p className="pt-hinweis">
            Wer hier aufgenommen wird, verlässt automatisch eine etwaige vorherige Party — eine Person ist
            immer nur in höchstens einer Party gleichzeitig.
          </p>
        </section>

        <div className="pt-zeile" style={{ marginTop: 10 }}>
          <button
            type="button"
            style={{ borderColor: "var(--signal)", color: "var(--signal)", marginLeft: "auto" }}
            onClick={async () => {
              await partyApi.entfernen(campaignId, party.id);
              onGeaendert();
            }}
          >
            Party auflösen
          </button>
        </div>
      </div>
    </Fenster>
  );
}
