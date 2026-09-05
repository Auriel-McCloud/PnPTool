import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import type { JSONContent } from "@tiptap/react";
import {
  entitiesApi,
  type EntityKind,
  type Event,
  type ListenFilter,
  type Ort,
  type Person,
  type SichtbarkeitModus,
  type Verbindung,
} from "./api";
import { VisibilitySelector, type PersonOption } from "./VisibilitySelector";
import { SichtbarkeitBadge } from "./SichtbarkeitBadge";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { EntitaetsBild } from "./EntitaetsBild";
import { RichTextView } from "../richtext/RichTextView";
import { EMPTY_DOC, parseRichText, serializeRichText } from "../richtext/content";
import { CharacterSheetPanel } from "../traits/CharacterSheetPanel";
import { Charaktererstellung } from "../traits/Charaktererstellung";
import { Charakterblatt } from "../traits/Charakterblatt";
import { Fenster } from "../shell/Fenster";
import { getGraph } from "../graph/api";
import { PCKacheln } from "./PCKacheln";
import { PCDetail } from "./PCDetail";
import { NPCKacheln } from "./NPCKacheln";
import { NPCDetail } from "./NPCDetail";
import { OrtKacheln } from "./OrtKacheln";
import { OrtDetail } from "./OrtDetail";
import { EventKacheln } from "./EventKacheln";
import { EventDetail } from "./EventDetail";
import { Filterleiste } from "./Filterleiste";
import { playersApi, type SpielerZugang } from "../players/api";

const sectionStyle: React.CSSProperties = { marginBottom: "2.5rem" };
const listItemStyle: React.CSSProperties = { padding: "0.75rem 0", borderBottom: "1px solid var(--linie)" };
const ansichtStyle: React.CSSProperties = { flex: 1, minHeight: 0, display: "flex", flexDirection: "column" };
const listeStyle: React.CSSProperties = { flex: 1, minHeight: 0, overflowY: "auto", paddingRight: 6 };
const kopfStyle: React.CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12, flexWrap: "wrap" };
const formStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 12,
  marginTop: 12,
  padding: 16,
  background: "var(--flaeche)",
  // Neonröhre als Begrenzung (vgl. .cl-roehre in shell/commlink.css):
  // harter Kern, enger Schein nach aussen, weicher Abglanz nach innen.
  // --bereich-farbe kommt aus der Hülle, die Röhre trägt also den Ton des
  // aktuellen Bereichs. Bewusst nur auf Eingabeflächen — läge der Schein
  // auch auf jedem Listeneintrag, flimmerte die ganze Seite.
  border: "1px solid var(--bereich-farbe, var(--neon))",
  boxShadow:
    "0 0 8px -3px var(--bereich-farbe, var(--neon)), inset 0 0 16px -10px var(--bereich-farbe, var(--neon))",
  borderRadius: 8,
  maxWidth: 640,
};
const fieldRowStyle: React.CSSProperties = { display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" };
const textInputStyle: React.CSSProperties = { fontSize: "1rem", padding: "8px 10px", minWidth: 260 };

/**
 * Fokussierte Bereiche der SL-Weltansicht. "welt" bleibt als Rückwärts-
 * kompatibilität für die bisherige Gesamtansicht erhalten; die Shell nutzt
 * die fünf fokussierten Varianten.
 */
export type WeltAnsicht = "welt" | "pcs" | "npcs" | "orte" | "events" | "verbindungen";

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
        <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Beschreibung</label>
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
        <label style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>Notizen</label>
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

export function EntityManager({ campaignId, ansicht = "welt" }: { campaignId: string; ansicht?: WeltAnsicht }) {
  const [personen, setPersonen] = useState<Person[]>([]);
  const [orte, setOrte] = useState<Ort[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [verbindungen, setVerbindungen] = useState<Verbindung[]>([]);
  const [graphGegenstaende, setGraphGegenstaende] = useState<{ id: string; label: string }[]>([]);
  const [spieler, setSpieler] = useState<SpielerZugang[]>([]);
  const [ladefehler, setLadefehler] = useState<string | null>(null);
  const [laedt, setLaedt] = useState(true);

  // Such-/Sortier-/Beziehungsfilter, je Bereich getrennt. Getrennt, damit ein
  // Wechsel von NPCs zu Orten nicht die dort gesetzte Suche mitschleppt.
  const [npcFilter, setNpcFilter] = useState<ListenFilter>({});
  const [ortFilter, setOrtFilter] = useState<ListenFilter>({});
  const [eventFilter, setEventFilter] = useState<ListenFilter>({});

  // Welcher Filter für den aktuellen Bereich gilt. Personen werden im
  // Backend nach personType eingeschränkt, nicht erst hier — sonst käme die
  // Trefferzahl der Filterleiste nicht mit der Liste überein.
  const aktiverFilter: ListenFilter =
    ansicht === "npcs"
      ? { ...npcFilter, personType: "NPC" }
      : ansicht === "pcs"
        ? { personType: "PC" }
        : ansicht === "orte"
          ? ortFilter
          : ansicht === "events"
            ? eventFilter
            : {};

  // Als String vergleichen: ein neues Objekt bei jedem Render würde den
  // Effekt sonst endlos neu starten.
  const filterSchluessel = JSON.stringify(aktiverFilter);

  const refreshAll = useCallback(async () => {
    setLaedt(true);
    try {
      const filter: ListenFilter = JSON.parse(filterSchluessel);
      const personenFilter = ansicht === "pcs" || ansicht === "npcs" ? filter : {};
      const [p, o, e, v, graph, sp] = await Promise.all([
        entitiesApi.listPersonen(campaignId, personenFilter),
        entitiesApi.listOrte(campaignId, ansicht === "orte" ? filter : {}),
        entitiesApi.listEvents(campaignId, ansicht === "events" ? filter : {}),
        entitiesApi.listVerbindungen(campaignId),
        getGraph(campaignId),
        playersApi.liste(campaignId).catch(() => [] as SpielerZugang[]),
      ]);
      setPersonen(p);
      setOrte(o);
      setEvents(e);
      setVerbindungen(v);
      setSpieler(sp);
      setLadefehler(null);
      // Gegenstände sind nur dann verbindbar, wenn sie explizit "im Graph anzeigen"
      // markiert wurden (z.B. MacGuffins) — normale Inventar-Items tauchen hier
      // bewusst nicht auf, um die Verbindungen-Auswahl nicht zu überladen.
      setGraphGegenstaende(
        graph.nodes.filter((n) => n.data.kind === "Gegenstand").map((n) => ({ id: n.data.id, label: n.data.label }))
      );
    } catch (fehler) {
      // Ohne diese Meldung stünde bei einem Serverfehler nur "Noch keine
      // Einträge" da — man suchte den Fehler dann in den Daten statt in der
      // Verbindung.
      setLadefehler(fehler instanceof Error ? fehler.message : "Daten konnten nicht geladen werden");
    } finally {
      setLaedt(false);
    }
  }, [campaignId, ansicht, filterSchluessel]);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const personenById = new Map(personen.map((p) => [p.id, p.name]));
  const pcOptions: PersonOption[] = personen.filter((p) => p.personType === "PC").map((p) => ({ id: p.id, name: p.name }));
  const alleOptionen: PersonOption[] = personen.map((p) => ({ id: p.id, name: `${p.name} (${p.personType})` }));
  // Spieler-Map: personId -> Spielername (für PC-Kacheln)
  const spielerMap = new Map(
    spieler.filter((s) => s.personId).map((s) => [s.personId!, s.benutzername])
  );

  // Wie viele Verbindungen an jeder Entität hängen — für die Kacheln und die
  // Sortierung "Meiste Verbindungen". Beide Richtungen zählen: ob die
  // Spielleitung "Wirt → arbeitet in → Bar" oder umgekehrt angelegt hat, ist
  // eine Frage des Erzählens, nicht der Zugehörigkeit.
  const verbindungsZahl = useMemo(() => {
    const zahl = new Map<string, number>();
    for (const v of verbindungen) {
      zahl.set(v.vonId, (zahl.get(v.vonId) ?? 0) + 1);
      zahl.set(v.zuId, (zahl.get(v.zuId) ?? 0) + 1);
    }
    return zahl;
  }, [verbindungen]);

  // Namen der Gegenseiten für die Beziehungslisten in den Detail-Popups.
  // Nur was hier steht, wird dort angezeigt — eine für diesen Blickwinkel
  // unsichtbare Entität fehlt in der Tabelle und damit auch in der Liste.
  const namensTabelle = useMemo(() => {
    const tabelle = new Map<string, { name: string; kind: EntityKind }>();
    for (const p of personen) tabelle.set(p.id, { name: p.name, kind: "Person" });
    for (const o of orte) tabelle.set(o.id, { name: o.name, kind: "Ort" });
    for (const ev of events) tabelle.set(ev.id, { name: ev.title, kind: "Event" });
    for (const g of graphGegenstaende) tabelle.set(g.id, { name: g.label, kind: "Gegenstand" });
    return tabelle;
  }, [personen, orte, events, graphGegenstaende]);

  // --- Person ---
  const [personName, setPersonName] = useState("");
  const [personType, setPersonType] = useState<"PC" | "NPC">(ansicht === "pcs" ? "PC" : "NPC");
  const personTypeFuerAnsicht: "PC" | "NPC" =
    ansicht === "pcs" ? "PC" : ansicht === "npcs" ? "NPC" : personType;
  const personContent = useContentAndVisibility();
  const [openSheetFor, setOpenSheetFor] = useState<string | null>(null);
  // Erstellung im Fenster statt inline: sie ist ein Vorgang mit Anfang und
  // Ende, und die Personenliste dahinter soll stehenbleiben.
  const [erstellungFuer, setErstellungFuer] = useState<Person | null>(null);
  // Dasselbe dreispaltige Blatt, das der Spieler sieht — die Spielleitung
  // will beim Erzählen denselben Überblick haben, nicht die Bearbeitungsmaske.
  const [blattFuer, setBlattFuer] = useState<Person | null>(null);
  // PC-Detail-Popup für die Kachel-Ansicht
  const [pcDetailFuer, setPcDetailFuer] = useState<Person | null>(null);
  const [npcDetailFuer, setNpcDetailFuer] = useState<Person | null>(null);
  // Neuer PC anlegen (Name-Eingabe-Popup)
  const [neuerPCOffen, setNeuerPCOffen] = useState(false);
  const [neuerPCName, setNeuerPCName] = useState("");
  // Neuer NPC anlegen (Name-Eingabe-Popup)
  const [neuerNPCOffen, setNeuerNPCOffen] = useState(false);
  const [neuerNPCName, setNeuerNPCName] = useState("");
  // Orte und Events: dasselbe Muster wie bei PCs/NPCs — Kachel öffnet ein
  // Detail-Popup, ein Knopf oben legt neu an.
  const [ortDetailFuer, setOrtDetailFuer] = useState<Ort | null>(null);
  const [eventDetailFuer, setEventDetailFuer] = useState<Event | null>(null);
  const [neuerOrtOffen, setNeuerOrtOffen] = useState(false);
  const [neuerOrtName, setNeuerOrtName] = useState("");
  const [neuesEventOffen, setNeuesEventOffen] = useState(false);
  const [neuesEventTitel, setNeuesEventTitel] = useState("");
  const [neuesEventZeit, setNeuesEventZeit] = useState("");
  const [anlegeFehler, setAnlegeFehler] = useState<string | null>(null);

  // Die geöffnete Entität muss dem frisch geladenen Stand folgen, sonst zeigt
  // das Popup nach dem Speichern noch die alten Werte (und "Beziehungen (3)",
  // obwohl gerade eine gelöst wurde).
  const offenerOrt = ortDetailFuer ? (orte.find((o) => o.id === ortDetailFuer.id) ?? null) : null;
  const offenesEvent = eventDetailFuer ? (events.find((e) => e.id === eventDetailFuer.id) ?? null) : null;

  async function erstelleNeuenOrt(e: FormEvent) {
    e.preventDefault();
    if (!neuerOrtName.trim()) return;
    setAnlegeFehler(null);
    try {
      await entitiesApi.createOrt(campaignId, {
        name: neuerOrtName.trim(),
        description: "",
        notes: "",
        sichtbarkeit: "GM",
        sichtbarFuer: [],
        notizenSichtbarkeit: "GM",
        notizenSichtbarFuer: [],
      });
      setNeuerOrtName("");
      setNeuerOrtOffen(false);
      await refreshAll();
    } catch (fehler) {
      setAnlegeFehler(fehler instanceof Error ? fehler.message : "Anlegen fehlgeschlagen");
    }
  }

  async function erstelleNeuesEvent(e: FormEvent) {
    e.preventDefault();
    if (!neuesEventTitel.trim()) return;
    setAnlegeFehler(null);
    try {
      await entitiesApi.createEvent(campaignId, {
        title: neuesEventTitel.trim(),
        timestamp: neuesEventZeit.trim(),
        description: "",
        notes: "",
        sichtbarkeit: "GM",
        sichtbarFuer: [],
        notizenSichtbarkeit: "GM",
        notizenSichtbarFuer: [],
      });
      setNeuesEventTitel("");
      setNeuesEventZeit("");
      setNeuesEventOffen(false);
      await refreshAll();
    } catch (fehler) {
      setAnlegeFehler(fehler instanceof Error ? fehler.message : "Anlegen fehlgeschlagen");
    }
  }

  async function erstelleNeuenPC(e: FormEvent) {
    e.preventDefault();
    if (!neuerPCName.trim()) return;
    await entitiesApi.createPerson(campaignId, {
      name: neuerPCName.trim(),
      personType: "PC",
      description: "",
      notes: "",
      sichtbarkeit: "GM",
      sichtbarFuer: [],
      notizenSichtbarkeit: "GM",
      notizenSichtbarFuer: [],
    });
    setNeuerPCName("");
    setNeuerPCOffen(false);
    await refreshAll();
  }
  async function erstelleNeuenNPC(e: FormEvent) {
    e.preventDefault();
    if (!neuerNPCName.trim()) return;
    await entitiesApi.createPerson(campaignId, {
      name: neuerNPCName.trim(),
      personType: "NPC",
      description: "",
      notes: "",
      sichtbarkeit: "GM",
      sichtbarFuer: [],
      notizenSichtbarkeit: "GM",
      notizenSichtbarFuer: [],
    });
    setNeuerNPCName("");
    setNeuerNPCOffen(false);
    await refreshAll();
  }
  async function submitPerson(e: FormEvent) {
    e.preventDefault();
    await entitiesApi.createPerson(campaignId, {
      name: personName,
      personType: personTypeFuerAnsicht,
      ...personContent.payload(),
    });
    setPersonName("");
    setPersonType(ansicht === "pcs" ? "PC" : "NPC");
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
    ...graphGegenstaende.map((g) => ({ id: g.id, kind: "Gegenstand" as const, label: `Gegenstand: ${g.label}` })),
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

  const zeigePersonen = ansicht === "welt" || ansicht === "pcs" || ansicht === "npcs";
  const personenInAnsicht =
    ansicht === "pcs"
      ? personen.filter((p) => p.personType === "PC")
      : ansicht === "npcs"
        ? personen.filter((p) => p.personType === "NPC")
        : personen;
  const zeigeOrte = ansicht === "welt" || ansicht === "orte";
  const zeigeEvents = ansicht === "welt" || ansicht === "events";
  const zeigeVerbindungen = ansicht === "welt" || ansicht === "verbindungen";
  const personenUeberschrift =
    ansicht === "pcs" ? "Spielercharaktere" : ansicht === "npcs" ? "Nichtspielercharaktere" : "Personen";
  const personenLeertext =
    ansicht === "pcs"
      ? "Noch keine Spielercharaktere angelegt."
      : ansicht === "npcs"
        ? "Noch keine Nichtspielercharaktere angelegt."
        : "Noch keine Personen angelegt.";

  const titel = ansicht === "pcs" ? "Spielercharaktere" : ansicht === "npcs" ? "Nichtspielercharaktere" : ansicht === "orte" ? "Orte" : ansicht === "events" ? "Events" : ansicht === "verbindungen" ? "Verbindungen" : "Welt";
  const status = ansicht === "pcs" ? `${personenInAnsicht.length} PCs` : ansicht === "npcs" ? `${personenInAnsicht.length} NPCs` : ansicht === "orte" ? `${orte.length} Orte` : ansicht === "events" ? `${events.length} Events` : ansicht === "verbindungen" ? `${verbindungen.length} Verbindungen` : `${personen.length} Personen · ${orte.length} Orte · ${events.length} Events`;
  const istNurEineAnsicht = ansicht !== "welt";

  // Ist gerade gefiltert? Entscheidet, ob "nichts angelegt" oder "nichts
  // gefunden" dasteht — zwei sehr verschiedene Auskünfte.
  function gefiltert(f: ListenFilter) {
    return Boolean(f.suche?.trim() || f.verbundenMit || f.verbindungsTyp);
  }
  const istNpcGefiltert = gefiltert(npcFilter);
  const istOrtGefiltert = gefiltert(ortFilter);
  const istEventGefiltert = gefiltert(eventFilter);

  return (
    <div style={ansichtStyle}>
      {/* PC-Ansicht: eigener Kopf mit Neuer-PC-Button */}
      {ansicht === "pcs" && (
        <div style={kopfStyle}>
          <h2 style={{ marginBottom: 8 }}>{titel}</h2>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <span className="mono" style={{ color: "var(--text-leise)", fontSize: "0.82em" }}>{status}</span>
            <button
              type="button"
              onClick={() => setNeuerPCOffen(true)}
              style={{
                padding: "8px 16px",
                background: "color-mix(in srgb, var(--bereich-pcs, var(--neon)) 20%, transparent)",
                border: "1px solid var(--bereich-pcs, var(--neon))",
                borderRadius: "var(--radius)",
                color: "var(--bereich-pcs, var(--neon))",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              + Neuer PC
            </button>
          </div>
        </div>
      )}
      {/* NPC-Ansicht: eigener Kopf mit Neuer-NPC-Button */}
      {ansicht === "npcs" && (
        <div style={kopfStyle}>
          <h2 style={{ marginBottom: 8 }}>{titel}</h2>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <span className="mono" style={{ color: "var(--text-leise)", fontSize: "0.82em" }}>{status}</span>
            <button
              type="button"
              onClick={() => setNeuerNPCOffen(true)}
              style={{
                padding: "8px 16px",
                background: "color-mix(in srgb, var(--bereich-npcs, var(--neon)) 20%, transparent)",
                border: "1px solid var(--bereich-npcs, var(--neon))",
                borderRadius: "var(--radius)",
                color: "var(--bereich-npcs, var(--neon))",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              + Neuer NPC
            </button>
          </div>
        </div>
      )}
      {/* Orte-Ansicht: eigener Kopf mit Neuer-Ort-Button */}
      {ansicht === "orte" && (
        <div style={kopfStyle}>
          <h2 style={{ marginBottom: 8 }}>{titel}</h2>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <span className="mono" style={{ color: "var(--text-leise)", fontSize: "0.82em" }}>{status}</span>
            <button
              type="button"
              onClick={() => setNeuerOrtOffen(true)}
              style={{
                padding: "8px 16px",
                background: "color-mix(in srgb, var(--bereich-orte, var(--neon)) 20%, transparent)",
                border: "1px solid var(--bereich-orte, var(--neon))",
                borderRadius: "var(--radius)",
                color: "var(--bereich-orte, var(--neon))",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              + Neuer Ort
            </button>
          </div>
        </div>
      )}
      {/* Events-Ansicht: eigener Kopf mit Neues-Event-Button */}
      {ansicht === "events" && (
        <div style={kopfStyle}>
          <h2 style={{ marginBottom: 8 }}>{titel}</h2>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <span className="mono" style={{ color: "var(--text-leise)", fontSize: "0.82em" }}>{status}</span>
            <button
              type="button"
              onClick={() => setNeuesEventOffen(true)}
              style={{
                padding: "8px 16px",
                background: "color-mix(in srgb, var(--bereich-events, var(--neon)) 20%, transparent)",
                border: "1px solid var(--bereich-events, var(--neon))",
                borderRadius: "var(--radius)",
                color: "var(--bereich-events, var(--neon))",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              + Neues Event
            </button>
          </div>
        </div>
      )}
      {/* Andere Ansichten: normaler Kopf */}
      {istNurEineAnsicht && ansicht !== "pcs" && ansicht !== "npcs" && ansicht !== "orte" && ansicht !== "events" && (
        <div style={kopfStyle}>
          <h2 style={{ marginBottom: 8 }}>{titel}</h2>
          <span className="mono" style={{ color: "var(--text-leise)", fontSize: "0.82em" }}>{status}</span>
        </div>
      )}

      {/* Filterleiste: NPCs, Orte und Events. PCs bleiben ohne — es sind
          wenige, und sie tragen keine Beziehungen im selben Umfang. */}
      {ansicht === "npcs" && (
        <Filterleiste
          campaignId={campaignId}
          art="personen"
          personType="NPC"
          filter={npcFilter}
          onFilter={setNpcFilter}
          trefferzahl={personenInAnsicht.length}
          farbe="var(--bereich-npcs, var(--neon))"
        />
      )}
      {ansicht === "orte" && (
        <Filterleiste
          campaignId={campaignId}
          art="orte"
          filter={ortFilter}
          onFilter={setOrtFilter}
          trefferzahl={orte.length}
          farbe="var(--bereich-orte, var(--neon))"
        />
      )}
      {ansicht === "events" && (
        <Filterleiste
          campaignId={campaignId}
          art="events"
          filter={eventFilter}
          onFilter={setEventFilter}
          trefferzahl={events.length}
          farbe="var(--bereich-events, var(--neon))"
          mitZeitpunkt
        />
      )}

      {/* Ladefehler sichtbar machen: sonst stünde nur "noch nichts angelegt"
          da, und man suchte den Fehler in den Daten statt in der Verbindung. */}
      {ladefehler && (
        <p
          style={{
            padding: "10px 12px",
            marginBottom: 12,
            color: "var(--signal)",
            border: "1px solid var(--signal)",
            borderRadius: "var(--radius)",
            background: "color-mix(in srgb, var(--signal) 8%, transparent)",
          }}
        >
          {ladefehler}{" "}
          <button type="button" onClick={refreshAll} style={{ minHeight: 0, padding: "3px 10px", marginLeft: 8 }}>
            Erneut versuchen
          </button>
        </p>
      )}

      <div style={istNurEineAnsicht ? listeStyle : undefined}>
      {/* PCs als Kacheln */}
      {ansicht === "pcs" && (
        <section style={sectionStyle}>
          <PCKacheln
            campaignId={campaignId}
            pcs={personenInAnsicht}
            spielerMap={spielerMap}
            onPCKlick={(p) => setPcDetailFuer(p)}
            onBlitz={(p) => {
              // TODO: Blitz-Funktion implementieren
              console.log("Blitz:", p.name);
            }}
          />
        </section>
      )}

      {/* NPCs als Kacheln */}
      {ansicht === "npcs" && (
        <section style={sectionStyle}>
          <NPCKacheln
            campaignId={campaignId}
            npcs={personenInAnsicht}
            onNPCKlick={(p) => setNpcDetailFuer(p)}
            onBlitz={(p) => {
              // TODO: Blitz-Funktion implementieren
              console.log("Blitz:", p.name);
            }}
            leertext={
              laedt
                ? "Lädt…"
                : istNpcGefiltert
                  ? "Kein NPC passt zu dieser Auswahl. Filter zurücksetzen oder anders suchen."
                  : "Noch keine Nichtspielercharaktere angelegt. Oben rechts anlegen."
            }
          />
        </section>
      )}

      {zeigePersonen && ansicht !== "pcs" && ansicht !== "npcs" && (
        <section style={sectionStyle}>
          <h2>{personenUeberschrift}</h2>
          {personenInAnsicht.length === 0 && <p style={{ color: "var(--text-leise)" }}>{personenLeertext}</p>}
          {personenInAnsicht.map((p) => (
          <div key={p.id} style={listItemStyle}>
            <strong>{p.name}</strong> <span style={{ color: "var(--text-leise)" }}>({p.personType})</span>
            <EntitaetsBild
              campaignId={campaignId}
              art="personen"
              id={p.id}
              name={p.name}
              bildUrl={p.bildUrl ?? ""}
              onGeaendert={refreshAll}
            />
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
            <div style={{ marginTop: 6, display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button type="button" onClick={() => setOpenSheetFor(openSheetFor === p.id ? null : p.id)}>
                {openSheetFor === p.id ? "Gegenstände schließen" : "Gegenstände"}
              </button>
              {/* Auch für fertige Charaktere: die Spielleitung muss eine
                  verkorkste Erstellung nachbessern können. Beim Absenden
                  werden alle Werte neu gesetzt. */}
              <button type="button" onClick={() => setBlattFuer(p)}>
                Charakterblatt
              </button>
              <button type="button" onClick={() => setErstellungFuer(p)}>
                Erstellung durchlaufen
              </button>
            </div>
            {openSheetFor === p.id && (
              <CharacterSheetPanel campaignId={campaignId} person={p} pcOptions={pcOptions} alleOptionen={alleOptionen} />
            )}
          </div>
          ))}
          <form onSubmit={submitPerson} style={formStyle}>
            <div style={fieldRowStyle}>
              <input style={textInputStyle} placeholder="Name" value={personName} onChange={(e) => setPersonName(e.target.value)} required />
              {ansicht === "welt" ? (
                <select value={personType} onChange={(e) => setPersonType(e.target.value as "PC" | "NPC")}>
                  <option value="NPC">NPC</option>
                  <option value="PC">PC</option>
                </select>
              ) : (
                <span style={{ color: "var(--text-leise)", padding: "9px 0" }}>
                  Typ: {personTypeFuerAnsicht}
                </span>
              )}
            </div>
            <RichContentFields state={personContent} pcOptions={pcOptions} />
            <button type="submit">Person anlegen</button>
          </form>
        </section>
      )}

      {/* Orte als Kacheln — dasselbe Bedienkonzept wie PCs und NPCs */}
      {ansicht === "orte" && (
        <section style={sectionStyle}>
          <OrtKacheln
            campaignId={campaignId}
            orte={orte}
            verbindungen={verbindungsZahl}
            onOrtKlick={(o) => setOrtDetailFuer(o)}
            leertext={
              laedt
                ? "Lädt…"
                : istOrtGefiltert
                  ? "Kein Ort passt zu dieser Auswahl. Filter zurücksetzen oder anders suchen."
                  : "Noch keine Orte angelegt. Oben rechts anlegen."
            }
          />
        </section>
      )}

      {/* Events als Kacheln */}
      {ansicht === "events" && (
        <section style={sectionStyle}>
          <EventKacheln
            campaignId={campaignId}
            events={events}
            verbindungen={verbindungsZahl}
            onEventKlick={(ev) => setEventDetailFuer(ev)}
            leertext={
              laedt
                ? "Lädt…"
                : istEventGefiltert
                  ? "Kein Event passt zu dieser Auswahl. Filter zurücksetzen oder anders suchen."
                  : "Noch keine Events angelegt. Oben rechts anlegen."
            }
          />
        </section>
      )}

      {zeigeOrte && ansicht !== "orte" && (
        <section style={sectionStyle}>
          <h2>Orte</h2>
          {orte.length === 0 && <p style={{ color: "var(--text-leise)" }}>Noch keine Orte angelegt.</p>}
          {orte.map((o) => (
          <div key={o.id} style={listItemStyle}>
            <strong>{o.name}</strong>
            <EntitaetsBild
              campaignId={campaignId}
              art="orte"
              id={o.id}
              name={o.name}
              bildUrl={o.bildUrl ?? ""}
              onGeaendert={refreshAll}
            />
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
      )}

      {zeigeEvents && ansicht !== "events" && (
        <section style={sectionStyle}>
          <h2>Events</h2>
          {events.length === 0 && <p style={{ color: "var(--text-leise)" }}>Noch keine Events angelegt.</p>}
          {events.map((ev) => (
          <div key={ev.id} style={listItemStyle}>
            <strong>{ev.title}</strong> {ev.timestamp && <span style={{ color: "var(--text-leise)" }}>({ev.timestamp})</span>}
            <EntitaetsBild
              campaignId={campaignId}
              art="events"
              id={ev.id}
              name={ev.title}
              bildUrl={ev.bildUrl ?? ""}
              onGeaendert={refreshAll}
            />
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
      )}

      {zeigeVerbindungen && (
        <section style={sectionStyle}>
          <h2>Verbindungen</h2>
          {verbindungen.length === 0 && <p style={{ color: "var(--text-leise)" }}>Noch keine Verbindungen angelegt.</p>}
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
      )}
      </div>

      {/* Erstellung der Spielleitung: dieselbe Führung wie beim Spieler,
          nur eben für NPCs. Nach dem Absenden stehen die Werte am Charakter,
          die Liste dahinter wird neu geladen. */}
      {/* Das fertige Blatt wie beim Spieler: drei Spalten, Zustand
          eintragbar, Erfahrung ausgebbar. Die Bearbeitungsmaske daneben
          bleibt für alles, was man dort *ändert*. */}
      <Fenster
        offen={blattFuer !== null}
        breit
        titel={blattFuer?.name ?? ""}
        unterzeile="Ansehen — zum Ändern oben auf Bearbeiten"
        kennung={`bogen:${blattFuer?.id ?? ""}`}
        onSchliessen={() => setBlattFuer(null)}
      >
        {blattFuer && <Charakterblatt campaignId={campaignId} personId={blattFuer.id} bearbeitbar />}
      </Fenster>

      <Fenster
        offen={erstellungFuer !== null}
        titel={erstellungFuer ? `${erstellungFuer.name} erstellen` : ""}
        unterzeile="Werte werden dabei neu gesetzt"
        kennung="erstellung"
        onSchliessen={() => setErstellungFuer(null)}
      >
        {erstellungFuer && (
          <Charaktererstellung
            campaignId={campaignId}
            personId={erstellungFuer.id}
            name={erstellungFuer.name}
            onFertig={() => {
              setErstellungFuer(null);
              refreshAll();
            }}
          />
        )}
      </Fenster>

      {/* PC-Detail-Popup */}
      {pcDetailFuer && (
        <PCDetail
          campaignId={campaignId}
          person={pcDetailFuer}
          spielerName={spielerMap.get(pcDetailFuer.id)}
          onSchliessen={() => setPcDetailFuer(null)}
          onGeaendert={refreshAll}
        />
      )}

      {/* NPC-Detail-Popup */}
      {npcDetailFuer && (
        <NPCDetail
          campaignId={campaignId}
          person={npcDetailFuer}
          onSchliessen={() => setNpcDetailFuer(null)}
          onGeaendert={refreshAll}
        />
      )}

      {/* Ort-Detail-Popup — offenerOrt statt ortDetailFuer, damit es nach dem
          Speichern den frischen Stand zeigt und nicht die alten Werte. */}
      {offenerOrt && (
        <OrtDetail
          campaignId={campaignId}
          ort={offenerOrt}
          verbindungen={verbindungen}
          namen={namensTabelle}
          pcOptions={pcOptions}
          onSchliessen={() => setOrtDetailFuer(null)}
          onGeaendert={refreshAll}
        />
      )}

      {/* Event-Detail-Popup */}
      {offenesEvent && (
        <EventDetail
          campaignId={campaignId}
          event={offenesEvent}
          verbindungen={verbindungen}
          namen={namensTabelle}
          pcOptions={pcOptions}
          onSchliessen={() => setEventDetailFuer(null)}
          onGeaendert={refreshAll}
        />
      )}

      {/* Neuer Ort anlegen */}
      <Fenster
        offen={neuerOrtOffen}
        titel="Neuer Ort"
        unterzeile="Gib dem Ort einen Namen"
        kennung="neuer-ort"
        ton="var(--bereich-orte)"
        onSchliessen={() => {
          setNeuerOrtOffen(false);
          setNeuerOrtName("");
          setAnlegeFehler(null);
        }}
      >
        <form onSubmit={erstelleNeuenOrt} style={{ display: "flex", flexDirection: "column", gap: 16, padding: 8 }}>
          <input
            type="text"
            value={neuerOrtName}
            onChange={(e) => setNeuerOrtName(e.target.value)}
            placeholder="Name des Ortes"
            autoFocus
            style={{ fontSize: "1.1rem", padding: "12px 14px" }}
            required
          />
          {anlegeFehler && <p style={{ color: "var(--signal)", margin: 0 }}>{anlegeFehler}</p>}
          <p style={{ color: "var(--text-leise)", fontSize: "0.85rem", margin: 0 }}>
            Neue Orte sind zunächst SL-geheim. Freigeben lässt sich das im Detail-Popup.
          </p>
          <button
            type="submit"
            style={{
              padding: "12px 20px",
              background: "color-mix(in srgb, var(--ja) 20%, transparent)",
              border: "1px solid var(--ja)",
              borderRadius: "var(--radius)",
              color: "var(--ja)",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "1rem",
            }}
          >
            Ort erstellen
          </button>
        </form>
      </Fenster>

      {/* Neues Event anlegen */}
      <Fenster
        offen={neuesEventOffen}
        titel="Neues Event"
        unterzeile="Titel und, falls schon bekannt, der Zeitpunkt"
        kennung="neues-event"
        ton="var(--bereich-events)"
        onSchliessen={() => {
          setNeuesEventOffen(false);
          setNeuesEventTitel("");
          setNeuesEventZeit("");
          setAnlegeFehler(null);
        }}
      >
        <form onSubmit={erstelleNeuesEvent} style={{ display: "flex", flexDirection: "column", gap: 16, padding: 8 }}>
          <input
            type="text"
            value={neuesEventTitel}
            onChange={(e) => setNeuesEventTitel(e.target.value)}
            placeholder="Titel des Events"
            autoFocus
            style={{ fontSize: "1.1rem", padding: "12px 14px" }}
            required
          />
          <input
            type="text"
            value={neuesEventZeit}
            onChange={(e) => setNeuesEventZeit(e.target.value)}
            placeholder="Zeitpunkt (z.B. Session 3) — darf leer bleiben"
            style={{ fontSize: "1rem", padding: "10px 14px" }}
          />
          {anlegeFehler && <p style={{ color: "var(--signal)", margin: 0 }}>{anlegeFehler}</p>}
          <p style={{ color: "var(--text-leise)", fontSize: "0.85rem", margin: 0 }}>
            Neue Events sind zunächst SL-geheim. Freigeben lässt sich das im Detail-Popup.
          </p>
          <button
            type="submit"
            style={{
              padding: "12px 20px",
              background: "color-mix(in srgb, var(--ja) 20%, transparent)",
              border: "1px solid var(--ja)",
              borderRadius: "var(--radius)",
              color: "var(--ja)",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "1rem",
            }}
          >
            Event erstellen
          </button>
        </form>
      </Fenster>

      {/* Neuer PC anlegen */}
      <Fenster
        offen={neuerPCOffen}
        titel="Neuer Spielercharakter"
        unterzeile="Gib dem Charakter einen Namen"
        kennung="neuer-pc"
        onSchliessen={() => {
          setNeuerPCOffen(false);
          setNeuerPCName("");
        }}
      >
        <form onSubmit={erstelleNeuenPC} style={{ display: "flex", flexDirection: "column", gap: 16, padding: 8 }}>
          <input
            type="text"
            value={neuerPCName}
            onChange={(e) => setNeuerPCName(e.target.value)}
            placeholder="Charaktername"
            autoFocus
            style={{ fontSize: "1.1rem", padding: "12px 14px" }}
            required
          />
          <button
            type="submit"
            style={{
              padding: "12px 20px",
              background: "color-mix(in srgb, var(--ja) 20%, transparent)",
              border: "1px solid var(--ja)",
              borderRadius: "var(--radius)",
              color: "var(--ja)",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "1rem",
            }}
          >
            PC erstellen
          </button>
        </form>
      </Fenster>

      {/* Neuer NPC anlegen */}
      <Fenster
        offen={neuerNPCOffen}
        titel="Neuer Nichtspielercharakter"
        unterzeile="Gib dem NPC einen Namen"
        kennung="neuer-npc"
        onSchliessen={() => {
          setNeuerNPCOffen(false);
          setNeuerNPCName("");
        }}
      >
        <form onSubmit={erstelleNeuenNPC} style={{ display: "flex", flexDirection: "column", gap: 16, padding: 8 }}>
          <input
            type="text"
            value={neuerNPCName}
            onChange={(e) => setNeuerNPCName(e.target.value)}
            placeholder="NPC-Name"
            autoFocus
            style={{ fontSize: "1.1rem", padding: "12px 14px" }}
            required
          />
          <button
            type="submit"
            style={{
              padding: "12px 20px",
              background: "color-mix(in srgb, var(--ja) 20%, transparent)",
              border: "1px solid var(--ja)",
              borderRadius: "var(--radius)",
              color: "var(--ja)",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "1rem",
            }}
          >
            NPC erstellen
          </button>
        </form>
      </Fenster>
    </div>
  );
}
