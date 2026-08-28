import { useEffect, useState, type FormEvent } from "react";
import type { JSONContent } from "@tiptap/react";
import { entitiesApi, type Event, type Ort, type Person, type SichtbarkeitModus, type Verbindung } from "./api";
import { VisibilitySelector, type PersonOption } from "./VisibilitySelector";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { RichTextView } from "../richtext/RichTextView";
import { EMPTY_DOC, parseRichText, serializeRichText } from "../richtext/content";

const sectionStyle: React.CSSProperties = { marginBottom: "2.5rem" };
const listItemStyle: React.CSSProperties = { padding: "0.75rem 0", borderBottom: "1px solid #ddd" };
const formStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 12,
  marginTop: 12,
  padding: 16,
  background: "#fafafa",
  border: "1px solid #eee",
  borderRadius: 8,
  maxWidth: 640,
};
const fieldRowStyle: React.CSSProperties = { display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" };
const textInputStyle: React.CSSProperties = { fontSize: "1rem", padding: "8px 10px", minWidth: 260 };

function SichtbarkeitBadge({
  modus,
  sichtbarFuer,
  personenById,
  label,
}: {
  modus: SichtbarkeitModus;
  sichtbarFuer: string[];
  personenById: Map<string, string>;
  label: string;
}) {
  const text =
    modus === "GM"
      ? `${label}: SL-geheim`
      : modus === "ALLE"
        ? `${label}: alle Spieler`
        : `${label}: ${sichtbarFuer.map((id) => personenById.get(id) ?? "?").join(", ") || "niemand ausgewählt"}`;
  return (
    <span
      style={{
        marginRight: 8,
        fontSize: "0.75em",
        padding: "2px 8px",
        borderRadius: 4,
        background: modus === "GM" ? "#333" : modus === "ALLE" ? "#2a6" : "#a67c00",
        color: "white",
      }}
    >
      {text}
    </span>
  );
}

// Gebündelter State für die Felder, die Personen/Orte/Events gemeinsam haben:
// Rich-Text-Beschreibung + Notizen, je mit eigener Sichtbarkeit.
function useContentAndVisibility() {
  const [descriptionDoc, setDescriptionDoc] = useState<JSONContent>(EMPTY_DOC);
  const [notesDoc, setNotesDoc] = useState<JSONContent>(EMPTY_DOC);
  const [sichtbarkeit, setSichtbarkeit] = useState<SichtbarkeitModus>("GM");
  const [sichtbarFuer, setSichtbarFuer] = useState<string[]>([]);
  const [notizenSichtbarkeit, setNotizenSichtbarkeit] = useState<SichtbarkeitModus>("GM");
  const [notizenSichtbarFuer, setNotizenSichtbarFuer] = useState<string[]>([]);

  function reset() {
    setDescriptionDoc(EMPTY_DOC);
    setNotesDoc(EMPTY_DOC);
    setSichtbarkeit("GM");
    setSichtbarFuer([]);
    setNotizenSichtbarkeit("GM");
    setNotizenSichtbarFuer([]);
  }

  function payload() {
    return {
      description: serializeRichText(descriptionDoc),
      notes: serializeRichText(notesDoc),
      sichtbarkeit,
      sichtbarFuer,
      notizenSichtbarkeit,
      notizenSichtbarFuer,
    };
  }

  return {
    descriptionDoc,
    setDescriptionDoc,
    notesDoc,
    setNotesDoc,
    sichtbarkeit,
    setSichtbarkeit,
    sichtbarFuer,
    setSichtbarFuer,
    notizenSichtbarkeit,
    setNotizenSichtbarkeit,
    notizenSichtbarFuer,
    setNotizenSichtbarFuer,
    reset,
    payload,
  };
}

function RichContentFields({
  state,
  pcOptions,
}: {
  state: ReturnType<typeof useContentAndVisibility>;
  pcOptions: PersonOption[];
}) {
  return (
    <>
      <div>
        <label style={{ fontSize: "0.85em", color: "#555" }}>Beschreibung</label>
        <RichTextEditor content={state.descriptionDoc} onChange={state.setDescriptionDoc} />
      </div>
      <VisibilitySelector
        label="Sichtbarkeit der Beschreibung"
        modus={state.sichtbarkeit}
        sichtbarFuer={state.sichtbarFuer}
        onChange={(m, f) => {
          state.setSichtbarkeit(m);
          state.setSichtbarFuer(f);
        }}
        pcOptions={pcOptions}
      />
      <div>
        <label style={{ fontSize: "0.85em", color: "#555" }}>Notizen</label>
        <RichTextEditor content={state.notesDoc} onChange={state.setNotesDoc} minHeight={70} />
      </div>
      <VisibilitySelector
        label="Sichtbarkeit der Notizen"
        modus={state.notizenSichtbarkeit}
        sichtbarFuer={state.notizenSichtbarFuer}
        onChange={(m, f) => {
          state.setNotizenSichtbarkeit(m);
          state.setNotizenSichtbarFuer(f);
        }}
        pcOptions={pcOptions}
      />
    </>
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

  const personenById = new Map(personen.map((p) => [p.id, p.name]));
  const pcOptions: PersonOption[] = personen.filter((p) => p.personType === "PC").map((p) => ({ id: p.id, name: p.name }));

  // --- Person ---
  const [personName, setPersonName] = useState("");
  const [personType, setPersonType] = useState<"PC" | "NPC">("NPC");
  const personContent = useContentAndVisibility();
  async function submitPerson(e: FormEvent) {
    e.preventDefault();
    await entitiesApi.createPerson(campaignId, { name: personName, personType, ...personContent.payload() });
    setPersonName("");
    setPersonType("NPC");
    personContent.reset();
    await refreshAll();
  }

  // --- Ort ---
  const [ortName, setOrtName] = useState("");
  const ortContent = useContentAndVisibility();
  async function submitOrt(e: FormEvent) {
    e.preventDefault();
    await entitiesApi.createOrt(campaignId, { name: ortName, ...ortContent.payload() });
    setOrtName("");
    ortContent.reset();
    await refreshAll();
  }

  // --- Event ---
  const [eventTitle, setEventTitle] = useState("");
  const [eventTimestamp, setEventTimestamp] = useState("");
  const eventContent = useContentAndVisibility();
  async function submitEvent(e: FormEvent) {
    e.preventDefault();
    await entitiesApi.createEvent(campaignId, { title: eventTitle, timestamp: eventTimestamp, ...eventContent.payload() });
    setEventTitle("");
    setEventTimestamp("");
    eventContent.reset();
    await refreshAll();
  }

  // --- Verbindung ---
  const [verbindungForm, setVerbindungForm] = useState({
    vonId: "",
    zuId: "",
    typ: "",
    sichtbarkeit: "GM" as SichtbarkeitModus,
    sichtbarFuer: [] as string[],
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
      sichtbarFuer: verbindungForm.sichtbarFuer,
    });
    setVerbindungForm({ vonId: "", zuId: "", typ: "", sichtbarkeit: "GM", sichtbarFuer: [] });
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
            <strong>{p.name}</strong> <span style={{ color: "#888" }}>({p.personType})</span>
            <div style={{ margin: "4px 0" }}>
              <RichTextView content={parseRichText(p.description)} />
            </div>
            <SichtbarkeitBadge modus={p.sichtbarkeit} sichtbarFuer={p.sichtbarFuer} personenById={personenById} label="Beschreibung" />
            {p.notes && (
              <SichtbarkeitBadge
                modus={p.notizenSichtbarkeit}
                sichtbarFuer={p.notizenSichtbarFuer}
                personenById={personenById}
                label="Notizen"
              />
            )}
          </div>
        ))}
        <form onSubmit={submitPerson} style={formStyle}>
          <div style={fieldRowStyle}>
            <input style={textInputStyle} placeholder="Name" value={personName} onChange={(e) => setPersonName(e.target.value)} required />
            <select value={personType} onChange={(e) => setPersonType(e.target.value as "PC" | "NPC")}>
              <option value="NPC">NPC</option>
              <option value="PC">PC</option>
            </select>
          </div>
          <RichContentFields state={personContent} pcOptions={pcOptions} />
          <button type="submit">Person anlegen</button>
        </form>
      </section>

      <section style={sectionStyle}>
        <h2>Orte</h2>
        {orte.map((o) => (
          <div key={o.id} style={listItemStyle}>
            <strong>{o.name}</strong>
            <div style={{ margin: "4px 0" }}>
              <RichTextView content={parseRichText(o.description)} />
            </div>
            <SichtbarkeitBadge modus={o.sichtbarkeit} sichtbarFuer={o.sichtbarFuer} personenById={personenById} label="Beschreibung" />
            {o.notes && (
              <SichtbarkeitBadge
                modus={o.notizenSichtbarkeit}
                sichtbarFuer={o.notizenSichtbarFuer}
                personenById={personenById}
                label="Notizen"
              />
            )}
          </div>
        ))}
        <form onSubmit={submitOrt} style={formStyle}>
          <input style={textInputStyle} placeholder="Name" value={ortName} onChange={(e) => setOrtName(e.target.value)} required />
          <RichContentFields state={ortContent} pcOptions={pcOptions} />
          <button type="submit">Ort anlegen</button>
        </form>
      </section>

      <section style={sectionStyle}>
        <h2>Events</h2>
        {events.map((ev) => (
          <div key={ev.id} style={listItemStyle}>
            <strong>{ev.title}</strong> {ev.timestamp && <span style={{ color: "#888" }}>({ev.timestamp})</span>}
            <div style={{ margin: "4px 0" }}>
              <RichTextView content={parseRichText(ev.description)} />
            </div>
            <SichtbarkeitBadge modus={ev.sichtbarkeit} sichtbarFuer={ev.sichtbarFuer} personenById={personenById} label="Beschreibung" />
            {ev.notes && (
              <SichtbarkeitBadge
                modus={ev.notizenSichtbarkeit}
                sichtbarFuer={ev.notizenSichtbarFuer}
                personenById={personenById}
                label="Notizen"
              />
            )}
          </div>
        ))}
        <form onSubmit={submitEvent} style={formStyle}>
          <div style={fieldRowStyle}>
            <input style={textInputStyle} placeholder="Titel" value={eventTitle} onChange={(e) => setEventTitle(e.target.value)} required />
            <input
              style={textInputStyle}
              placeholder="Zeitpunkt (z.B. Session 3)"
              value={eventTimestamp}
              onChange={(e) => setEventTimestamp(e.target.value)}
            />
          </div>
          <RichContentFields state={eventContent} pcOptions={pcOptions} />
          <button type="submit">Event anlegen</button>
        </form>
      </section>

      <section style={sectionStyle}>
        <h2>Verbindungen</h2>
        {verbindungen.map((v) => (
          <div key={v.id} style={listItemStyle}>
            {labelFor(v.vonKind, v.vonId)} <strong>— {v.typ} →</strong> {labelFor(v.zuKind, v.zuId)}
            <div>
              <SichtbarkeitBadge modus={v.sichtbarkeit} sichtbarFuer={v.sichtbarFuer} personenById={personenById} label="Sichtbarkeit" />
            </div>
          </div>
        ))}
        <form onSubmit={submitVerbindung} style={formStyle}>
          <div style={fieldRowStyle}>
            <select value={verbindungForm.vonId} onChange={(e) => setVerbindungForm({ ...verbindungForm, vonId: e.target.value })} required>
              <option value="">Von...</option>
              {alleEntitaeten.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.label}
                </option>
              ))}
            </select>
            <input
              style={textInputStyle}
              placeholder="Beziehungstyp (z.B. kennt)"
              value={verbindungForm.typ}
              onChange={(e) => setVerbindungForm({ ...verbindungForm, typ: e.target.value })}
              required
            />
            <select value={verbindungForm.zuId} onChange={(e) => setVerbindungForm({ ...verbindungForm, zuId: e.target.value })} required>
              <option value="">Zu...</option>
              {alleEntitaeten.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.label}
                </option>
              ))}
            </select>
          </div>
          <VisibilitySelector
            label="Sichtbarkeit der Verbindung"
            modus={verbindungForm.sichtbarkeit}
            sichtbarFuer={verbindungForm.sichtbarFuer}
            onChange={(m, f) => setVerbindungForm({ ...verbindungForm, sichtbarkeit: m, sichtbarFuer: f })}
            pcOptions={pcOptions}
          />
          <button type="submit">Verbindung anlegen</button>
        </form>
      </section>
    </div>
  );
}
