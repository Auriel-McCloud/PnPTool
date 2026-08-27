import { useEffect, useState, type FormEvent } from "react";
import { entitiesApi, type Event, type Ort, type Person, type Sichtbarkeit, type Verbindung } from "./api";

const sectionStyle: React.CSSProperties = { marginBottom: "2rem" };
const listItemStyle: React.CSSProperties = { padding: "0.4rem 0", borderBottom: "1px solid #ddd" };
const formRowStyle: React.CSSProperties = { display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" };

function SichtbarkeitBadge({ value }: { value: Sichtbarkeit }) {
  return (
    <span
      style={{
        marginLeft: 8,
        fontSize: "0.75em",
        padding: "1px 6px",
        borderRadius: 4,
        background: value === "GM" ? "#333" : "#2a6",
        color: "white",
      }}
    >
      {value === "GM" ? "SL-geheim" : "Spieler sichtbar"}
    </span>
  );
}

export function EntityManager({ campaignId }: { campaignId: string }) {
  const [personen, setPersonen] = useState<Person[]>([]);
  const [orte, setOrte] = useState<Ort[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [verbindungen, setVerbindungen] = useState<Verbindung[]>([]);

  async function refreshAll() {
    const [p, o, e, v] = await Promise.all([
      entitiesApi.listPersonen(campaignId),
      entitiesApi.listOrte(campaignId),
      entitiesApi.listEvents(campaignId),
      entitiesApi.listVerbindungen(campaignId),
    ]);
    setPersonen(p);
    setOrte(o);
    setEvents(e);
    setVerbindungen(v);
  }

  useEffect(() => {
    refreshAll();
  }, [campaignId]);

  const [personForm, setPersonForm] = useState({ name: "", personType: "NPC" as "PC" | "NPC", description: "", sichtbarkeit: "GM" as Sichtbarkeit });
  async function submitPerson(e: FormEvent) {
    e.preventDefault();
    await entitiesApi.createPerson(campaignId, { ...personForm, notes: "" });
    setPersonForm({ name: "", personType: "NPC", description: "", sichtbarkeit: "GM" });
    await refreshAll();
  }

  const [ortForm, setOrtForm] = useState({ name: "", description: "", sichtbarkeit: "GM" as Sichtbarkeit });
  async function submitOrt(e: FormEvent) {
    e.preventDefault();
    await entitiesApi.createOrt(campaignId, { ...ortForm, notes: "" });
    setOrtForm({ name: "", description: "", sichtbarkeit: "GM" });
    await refreshAll();
  }

  const [eventForm, setEventForm] = useState({ title: "", timestamp: "", description: "", sichtbarkeit: "GM" as Sichtbarkeit });
  async function submitEvent(e: FormEvent) {
    e.preventDefault();
    await entitiesApi.createEvent(campaignId, { ...eventForm, notes: "" });
    setEventForm({ title: "", timestamp: "", description: "", sichtbarkeit: "GM" });
    await refreshAll();
  }

  const [verbindungForm, setVerbindungForm] = useState({
    vonId: "",
    zuId: "",
    typ: "",
    sichtbarkeit: "GM" as Sichtbarkeit,
  });
  const alleEntitaeten = [
    ...personen.map((p) => ({ id: p.id, kind: "Person" as const, label: `Person: ${p.name}` })),
    ...orte.map((o) => ({ id: o.id, kind: "Ort" as const, label: `Ort: ${o.name}` })),
    ...events.map((ev) => ({ id: ev.id, kind: "Event" as const, label: `Event: ${ev.title}` })),
  ];
  function kindOf(id: string) {
    return alleEntitaeten.find((e) => e.id === id)?.kind;
  }
  async function submitVerbindung(e: FormEvent) {
    e.preventDefault();
    const vonKind = kindOf(verbindungForm.vonId);
    const zuKind = kindOf(verbindungForm.zuId);
    if (!vonKind || !zuKind) return;
    await entitiesApi.createVerbindung(campaignId, {
      vonKind,
      vonId: verbindungForm.vonId,
      zuKind,
      zuId: verbindungForm.zuId,
      typ: verbindungForm.typ,
      beschreibung: "",
      seit: "",
      bis: "",
      sichtbarkeit: verbindungForm.sichtbarkeit,
    });
    setVerbindungForm({ vonId: "", zuId: "", typ: "", sichtbarkeit: "GM" });
    await refreshAll();
  }

  function labelFor(kind: string, id: string) {
    return alleEntitaeten.find((e) => e.kind === kind && e.id === id)?.label ?? `${kind}:${id}`;
  }

  return (
    <div>
      <section style={sectionStyle}>
        <h2>Personen</h2>
        {personen.map((p) => (
          <div key={p.id} style={listItemStyle}>
            <strong>{p.name}</strong> ({p.personType}) — {p.description}
            <SichtbarkeitBadge value={p.sichtbarkeit} />
          </div>
        ))}
        <form onSubmit={submitPerson} style={formRowStyle}>
          <input placeholder="Name" value={personForm.name} onChange={(e) => setPersonForm({ ...personForm, name: e.target.value })} required />
          <select value={personForm.personType} onChange={(e) => setPersonForm({ ...personForm, personType: e.target.value as "PC" | "NPC" })}>
            <option value="NPC">NPC</option>
            <option value="PC">PC</option>
          </select>
          <input placeholder="Beschreibung" value={personForm.description} onChange={(e) => setPersonForm({ ...personForm, description: e.target.value })} />
          <select value={personForm.sichtbarkeit} onChange={(e) => setPersonForm({ ...personForm, sichtbarkeit: e.target.value as Sichtbarkeit })}>
            <option value="GM">SL-geheim</option>
            <option value="SPIELER">Spieler sichtbar</option>
          </select>
          <button type="submit">Person anlegen</button>
        </form>
      </section>

      <section style={sectionStyle}>
        <h2>Orte</h2>
        {orte.map((o) => (
          <div key={o.id} style={listItemStyle}>
            <strong>{o.name}</strong> — {o.description}
            <SichtbarkeitBadge value={o.sichtbarkeit} />
          </div>
        ))}
        <form onSubmit={submitOrt} style={formRowStyle}>
          <input placeholder="Name" value={ortForm.name} onChange={(e) => setOrtForm({ ...ortForm, name: e.target.value })} required />
          <input placeholder="Beschreibung" value={ortForm.description} onChange={(e) => setOrtForm({ ...ortForm, description: e.target.value })} />
          <select value={ortForm.sichtbarkeit} onChange={(e) => setOrtForm({ ...ortForm, sichtbarkeit: e.target.value as Sichtbarkeit })}>
            <option value="GM">SL-geheim</option>
            <option value="SPIELER">Spieler sichtbar</option>
          </select>
          <button type="submit">Ort anlegen</button>
        </form>
      </section>

      <section style={sectionStyle}>
        <h2>Events</h2>
        {events.map((ev) => (
          <div key={ev.id} style={listItemStyle}>
            <strong>{ev.title}</strong> {ev.timestamp && `(${ev.timestamp})`} — {ev.description}
            <SichtbarkeitBadge value={ev.sichtbarkeit} />
          </div>
        ))}
        <form onSubmit={submitEvent} style={formRowStyle}>
          <input placeholder="Titel" value={eventForm.title} onChange={(e) => setEventForm({ ...eventForm, title: e.target.value })} required />
          <input placeholder="Zeitpunkt (z.B. Session 3)" value={eventForm.timestamp} onChange={(e) => setEventForm({ ...eventForm, timestamp: e.target.value })} />
          <input placeholder="Beschreibung" value={eventForm.description} onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })} />
          <select value={eventForm.sichtbarkeit} onChange={(e) => setEventForm({ ...eventForm, sichtbarkeit: e.target.value as Sichtbarkeit })}>
            <option value="GM">SL-geheim</option>
            <option value="SPIELER">Spieler sichtbar</option>
          </select>
          <button type="submit">Event anlegen</button>
        </form>
      </section>

      <section style={sectionStyle}>
        <h2>Verbindungen</h2>
        {verbindungen.map((v) => (
          <div key={v.id} style={listItemStyle}>
            {labelFor(v.vonKind, v.vonId)} <strong>— {v.typ} →</strong> {labelFor(v.zuKind, v.zuId)}
            <SichtbarkeitBadge value={v.sichtbarkeit} />
          </div>
        ))}
        <form onSubmit={submitVerbindung} style={formRowStyle}>
          <select value={verbindungForm.vonId} onChange={(e) => setVerbindungForm({ ...verbindungForm, vonId: e.target.value })} required>
            <option value="">Von...</option>
            {alleEntitaeten.map((e) => (
              <option key={e.id} value={e.id}>
                {e.label}
              </option>
            ))}
          </select>
          <input placeholder="Beziehungstyp (z.B. kennt)" value={verbindungForm.typ} onChange={(e) => setVerbindungForm({ ...verbindungForm, typ: e.target.value })} required />
          <select value={verbindungForm.zuId} onChange={(e) => setVerbindungForm({ ...verbindungForm, zuId: e.target.value })} required>
            <option value="">Zu...</option>
            {alleEntitaeten.map((e) => (
              <option key={e.id} value={e.id}>
                {e.label}
              </option>
            ))}
          </select>
          <select value={verbindungForm.sichtbarkeit} onChange={(e) => setVerbindungForm({ ...verbindungForm, sichtbarkeit: e.target.value as Sichtbarkeit })}>
            <option value="GM">SL-geheim</option>
            <option value="SPIELER">Spieler sichtbar</option>
          </select>
          <button type="submit">Verbindung anlegen</button>
        </form>
      </section>
    </div>
  );
}
