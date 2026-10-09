import { api } from "../api/client";

export type SichtbarkeitModus = "GM" | "ALLE" | "SPEZIFISCH";
export type EntityKind = "Person" | "Ort" | "Event" | "Gegenstand" | "Fraktion";

export interface VisibilityFields {
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
}

/** "Alias aka Name" fürs SL-Auge — zeigt beides zugleich, statt den Alias
 * nur versteckt im Steckbrief zu halten (Mark, 06.10.2026: "schaut im
 * Moment nicht so aus"). Nur für Oberflächen, die sowieso den echten Namen
 * zeigen dürfen (GM-Ansichten, die eigene Figur) — niemals für das, was
 * ein Spieler über einen fremden NPC sieht; dafür gilt weiterhin
 * app/kontakte/logic.py::effektiver_alias auf dem Server. */
export function anzeigeName(name: string, alias?: string | null): string {
  const a = (alias ?? "").trim();
  return a ? `${a} aka ${name}` : name;
}

export interface Person extends VisibilityFields {
  id: string;
  name: string;
  personType: "PC" | "NPC";
  description: string;
  /** Name, unter dem ein PC diese Person in den Kontakten sieht, bis der
   * echte Name freigegeben ist — bearbeitbar im Steckbrief (Charakterblatt.tsx),
   * genau wie Ambition/Verlangen/Ziel (Mark, 06.10.2026: "könnte sich ja
   * auch ändern"). Siehe app/kontakte/logic.py::effektiver_alias. */
  alias?: string;
  /** Welche Silhouette die Körperkarte zeigt. */
  silhouette?: string;
  /** Aussehen; per Blitz an alle Spieler zeigbar. */
  bildUrl?: string;
  /** Bildergalerie: mehrere Bilder mit Primärmarkierung. */
  bilder?: { url: string; istPrimaer: boolean }[];
  notes: string;
  notizenSichtbarkeit: SichtbarkeitModus;
  notizenSichtbarFuer: string[];
  /** Extra-EP: individuelle Bonus-Punkte (zusätzlich zu kampagnenweiten EP). */
  extraEP?: number;
  /** Critter (20.09.2026): Tiere/Haustiere sind echte NPCs mit dem vollen
   * Charakterblatt statt einer eigenen Begleiter-Art — Mark: "wir machen
   * critter zu richtigen NPCs". Verbindung zu ihrem Menschen läuft über
   * `entitiesApi.critterBesitzer`, dieselbe BEGLEITET-Kante wie bei
   * Sprite/Geist/KI. */
  istCritter?: boolean;
  /** KI (20.09.2026, revidiert): dasselbe Muster wie Critter — eine Stadt-KI
   * ist eine echte Person statt einer Begleiter-Art. Ersetzt am Blatt die
   * körperlichen Attribute durch Matrix-Präsenz (`AttributMatrix`, siehe
   * `traits/bogenApi.ts::ATTRIBUT_KATEGORIEN_KI`). */
  istKI?: boolean;
  /** Shop-System (24.09.2026): Person ist ein Händler, siehe app/haendler/. */
  istHaendler?: boolean;
  /** Tutorial-Shop (10.10.2026): Händler, der NUR im Freebees-Schritt der
   * Charaktererstellung auftaucht, aus der normalen Shop-Übersicht
   * ausgeblendet bleibt (kein Verhandeln, keine Achievement-Trigger). */
  istTutorialHaendler?: boolean;
  spezialisierung?: string[];
  /** PHYSISCH = Fancy-Laden mit Verhandeln, DIGITAL = schlichter Online-Shop
   * ohne Verhandeln, mit SL-freizugebender Lieferverzögerung. */
  vertriebsart?: "PHYSISCH" | "DIGITAL";
  /** Eigenes Hintergrundbild der Shop-Seite (getrennt vom Portrait bildUrl). */
  shopHintergrundUrl?: string;
  /** Pflanzen-Vokabular (Flora & Fauna, 06.10.2026): rein kosmetisches Flag
   * für einen Critter — swapt nur ein paar Beschriftungen auf dem
   * Charakterblatt (z.B. "Alter" -> "Wachstumsstadium", Kapital/Schulden
   * ausgeblendet), keine Mechanik. Siehe traits/Charakterblatt.tsx. */
  istPflanzenCritter?: boolean;
  /** Lebenspunkte-Grundwert (10.10.2026): ersetzt für diese Person den
   * globalen Gesundheits-Grundwert (sonst 6) — z.B. eine Ratte mit
   * Grundwert 1 statt 6. -1 (oder fehlend) = globaler Standardwert gilt.
   * Siehe traits/bogen.py::gesundheit_max, editierbar in CritterFenster.tsx. */
  gesundheitGrundwert?: number;
  /** Vorgefertigte Charaktere (08.10.2026): erscheint im Ersteinstiegs-
   * Fenster der Spieler als wählbarer PC, solange noch niemand ihn spielt.
   * Explizites Opt-in der SL (vorher implizit "jeder unclaimed PC"). */
  istVorgefertigt?: boolean;
}

export interface Ort extends VisibilityFields {
  id: string;
  name: string;
  description: string;
  bildUrl?: string;
  /** Bildergalerie: mehrere Bilder mit Primärmarkierung. */
  bilder?: { url: string; istPrimaer: boolean }[];
  notes: string;
  notizenSichtbarkeit: SichtbarkeitModus;
  notizenSichtbarFuer: string[];
  /** Spotify-Playlist dieses Ortes — startet, wenn die aktive Party hier ist. */
  spotifyPlaylistUri?: string;
  spotifyPlaylistName?: string;
  spotifyPlaylistBild?: string;
  /** Shop (04.10.2026): Ort ist der Laden. */
  istShop?: boolean;
  spezialisierung?: string[];
  vertriebsart?: "PHYSISCH" | "DIGITAL";
  shopHintergrundUrl?: string;
}

export interface Event extends VisibilityFields {
  id: string;
  title: string;
  timestamp: string;
  description: string;
  bildUrl?: string;
  /** Bildergalerie: mehrere Bilder mit Primärmarkierung. */
  bilder?: { url: string; istPrimaer: boolean }[];
  notes: string;
  notizenSichtbarkeit: SichtbarkeitModus;
  notizenSichtbarFuer: string[];
  /** Spotify-Playlist dieses Events — startet, wenn die aktive Party hier ist. */
  spotifyPlaylistUri?: string;
  spotifyPlaylistName?: string;
  spotifyPlaylistBild?: string;
}

export interface KurzLangEintrag {
  /** Kurzbeschreibung — wird in der Liste angezeigt. */
  titel: string;
  /** Ausformulierte Beschreibung — nur auf Abruf sichtbar. */
  beschreibung: string;
}

export interface Fraktion extends VisibilityFields {
  id: string;
  name: string;
  description: string;
  /** Vorhaben der Fraktion — jedes mit Kurz- und Langbeschreibung. */
  ziele: KurzLangEintrag[];
  /** Miliz, Kapital, Zugang — jedes mit Kurz- und Langbeschreibung. */
  ressourcen: KurzLangEintrag[];
  bildUrl?: string;
  /** Bildergalerie: mehrere Bilder mit Primärmarkierung. */
  bilder?: { url: string; istPrimaer: boolean }[];
  notes: string;
  notizenSichtbarkeit: SichtbarkeitModus;
  notizenSichtbarFuer: string[];
}

/** Gewöhnliche, nicht kampffähige Flora (Flora & Fauna, 06.10.2026) — bewusst
 * OHNE Charakterbogen/Rasse/Attribute, anders als ein Critter. */
export interface Gewaechs extends VisibilityFields {
  id: string;
  name: string;
  description: string;
  notes: string;
  notizenSichtbarkeit: SichtbarkeitModus;
  notizenSichtbarFuer: string[];
  bildUrl?: string;
  bilder?: { url: string; istPrimaer: boolean }[];
  istEntwurf?: boolean;
  giftig?: boolean;
  essbar?: boolean;
  /** Freier Klassifikationstext, dieselbe Hausregel wie `spezialisierung`. */
  gefaehrlichkeit?: string;
  /** Freitext, z.B. "leuchtet im Dunkeln", "kybernetisch modifiziert". */
  eigenschaften?: string;
}

export interface Verbindung extends VisibilityFields {
  id: string;
  vonKind: EntityKind;
  vonId: string;
  zuKind: EntityKind;
  zuId: string;
  typ: string;
  beschreibung: string;
  seit: string;
  bis: string;
}

function base(campaignId: string) {
  return `/api/campaigns/${campaignId}`;
}

/**
 * Sortierungen, die das Backend kennt (app/entities/filterung.py).
 * Ein unbekannter Wert gibt dort 422 statt still auf den Namen zurückzufallen —
 * ein Tippfehler soll auffallen, nicht schweigen.
 */
export type Sortierung = "name" | "name-ab" | "sichtbarkeit" | "verbindungen" | "zeitpunkt";

/** Such-, Sortier- und Beziehungsfilter für eine Entitätsliste. */
export interface ListenFilter {
  suche?: string;
  sortierung?: Sortierung;
  /** Nur Personen: PC oder NPC. */
  personType?: "PC" | "NPC";
  /** Nur Einträge mit einer Verbindung zu dieser Entität. */
  verbundenMit?: string;
  /** Nur Einträge mit einer Verbindung dieser Bezeichnung. */
  verbindungsTyp?: string;
}

/** Eine Entität, mit der tatsächlich mindestens eine Verbindung besteht. */
export interface FilterZiel {
  id: string;
  kind: EntityKind;
  label: string;
  anzahl: number;
}

export interface FilterOptionen {
  typen: string[];
  ziele: FilterZiel[];
}

function query(filter?: ListenFilter): string {
  if (!filter) return "";
  const teile = new URLSearchParams();
  // Leere Werte weglassen: ein "?suche=" wäre kein Filter, würde aber die
  // Adresse ändern und damit jede Zwischenspeicherung aushebeln.
  for (const [schluessel, wert] of Object.entries(filter)) {
    if (wert !== undefined && wert !== null && String(wert).trim() !== "") {
      teile.set(schluessel, String(wert));
    }
  }
  const s = teile.toString();
  return s ? `?${s}` : "";
}

export interface CritterEintrag {
  id: string;
  name: string;
  alias: string | null;
  bildUrl: string;
  besitzerId: string | null;
  besitzerName: string | null;
}

/** Dieselbe schlanke Form wie `CritterEintrag`, für KI-Personen. */
export type KiEintrag = CritterEintrag;

/** Ein Einfluss-Eintrag einer Person (typischerweise einer KI) auf einen
 * Ort/eine Fraktion/ein Event/einen Gegenstand — echte Graphkante statt
 * Freitext, siehe `EinflussZielKind`. Verschoben von `begleiter/api.ts`
 * (20.09.2026, revidiert): KI ist jetzt eine Person statt einer
 * Begleiter-Art. */
export type EinflussZielKind = Exclude<EntityKind, "Person">;

export interface EinflussEintrag {
  zielKind: EinflussZielKind;
  zielId: string;
  zielName: string;
  stufe: number;
}

/** Ein mit einem Ort verknüpfter Critter oder ein verknüpftes Gewächs
 * (Flora & Fauna, 06.10.2026). `kind` ist das rohe Backend-Label
 * ("Person" für Critter, "Gewaechs"). */
export interface LebtInEintrag {
  id: string;
  kind: "Person" | "Gewaechs";
  name: string;
  bildUrl: string;
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
}

export const entitiesApi = {
  listPersonen: (cid: string, filter?: ListenFilter) =>
    api.get<Person[]>(`${base(cid)}/personen${query(filter)}`),
  // Ungefiltert, für die Charakter-Auswahl der SL-Vorschau — siehe api.getAsGm.
  listPersonenAlsGm: (cid: string) => api.getAsGm<Person[]>(`${base(cid)}/personen`),
  createPerson: (cid: string, body: Omit<Person, "id">) => api.post<Person>(`${base(cid)}/personen`, body),
  getPerson: (cid: string, id: string) => api.get<Person>(`${base(cid)}/personen/${id}`),
  updatePerson: (cid: string, id: string, body: Partial<Person>) =>
    api.patch<Person>(`${base(cid)}/personen/${id}`, body),
  deletePerson: (cid: string, id: string) => api.delete<void>(`${base(cid)}/personen/${id}`),
  /** Erhöht die Extra-EP eines PCs (nur positiv, irreversibel). */
  extraEpErhoehen: (cid: string, personId: string, betrag: number) =>
    api.post<Person>(`${base(cid)}/personen/${personId}/extra-ep`, { betrag }),
  /** Wandelt einen PC/NPC in-place in den jeweils anderen Typ um — der
   * ganze Baustand (Inventar, Bogen, Beziehungen) bleibt erhalten, siehe
   * app/entities/repository.py::person_zu_npc/person_zu_pc. */
  personZuNpc: (cid: string, personId: string) => api.post<Person>(`${base(cid)}/personen/${personId}/zu-npc`, {}),
  personZuPc: (cid: string, personId: string) => api.post<Person>(`${base(cid)}/personen/${personId}/zu-pc`, {}),

  /** Critter — Tiere/Haustiere als echte NPCs (`istCritter: true`), eigene
   * schlanke Liste für die Begleiter-Übersicht statt des vollen Bogens. */
  listCritter: (cid: string) => api.get<CritterEintrag[]>(`${base(cid)}/critter`),
  critterBesitzer: (cid: string, critterId: string, personId: string | null) =>
    api.post<CritterEintrag>(`${base(cid)}/critter/${critterId}/besitzer`, { personId }),

  /** KI — dasselbe Muster wie Critter, seit 20.09.2026 (revidiert) ebenfalls
   * eine echte Person (`istKI: true`) statt einer Begleiter-Art. */
  listKi: (cid: string) => api.get<KiEintrag[]>(`${base(cid)}/ki`),
  kiBesitzer: (cid: string, kiId: string, personId: string | null) =>
    api.post<KiEintrag>(`${base(cid)}/ki/${kiId}/besitzer`, { personId }),

  /** Einfluss-Kanten einer Person (typischerweise einer KI) auf Ort/
   * Fraktion/Event/Gegenstand — GM-only zum Setzen/Entfernen. */
  einflussListe: (cid: string, personId: string) =>
    api.get<EinflussEintrag[]>(`${base(cid)}/personen/${personId}/einfluss`),
  einflussSetzen: (cid: string, personId: string, zielKind: EinflussZielKind, zielId: string, stufe: number) =>
    api.post<EinflussEintrag[]>(`${base(cid)}/personen/${personId}/einfluss`, { zielKind, zielId, stufe }),
  einflussEntfernen: (cid: string, personId: string, zielKind: EinflussZielKind, zielId: string) =>
    api.delete<EinflussEintrag[]>(`${base(cid)}/personen/${personId}/einfluss/${zielKind}/${zielId}`),

  listOrte: (cid: string, filter?: ListenFilter) => api.get<Ort[]>(`${base(cid)}/orte${query(filter)}`),
  createOrt: (cid: string, body: Omit<Ort, "id">) => api.post<Ort>(`${base(cid)}/orte`, body),
  getOrt: (cid: string, id: string) => api.get<Ort>(`${base(cid)}/orte/${id}`),
  updateOrt: (cid: string, id: string, body: Partial<Ort>) => api.patch<Ort>(`${base(cid)}/orte/${id}`, body),
  deleteOrt: (cid: string, id: string) => api.delete<void>(`${base(cid)}/orte/${id}`),

  listEvents: (cid: string, filter?: ListenFilter) => api.get<Event[]>(`${base(cid)}/events${query(filter)}`),
  createEvent: (cid: string, body: Omit<Event, "id">) => api.post<Event>(`${base(cid)}/events`, body),
  getEvent: (cid: string, id: string) => api.get<Event>(`${base(cid)}/events/${id}`),
  updateEvent: (cid: string, id: string, body: Partial<Event>) =>
    api.patch<Event>(`${base(cid)}/events/${id}`, body),
  deleteEvent: (cid: string, id: string) => api.delete<void>(`${base(cid)}/events/${id}`),

  listFraktionen: (cid: string, filter?: ListenFilter) =>
    api.get<Fraktion[]>(`${base(cid)}/fraktionen${query(filter)}`),
  createFraktion: (cid: string, body: Omit<Fraktion, "id">) => api.post<Fraktion>(`${base(cid)}/fraktionen`, body),
  getFraktion: (cid: string, id: string) => api.get<Fraktion>(`${base(cid)}/fraktionen/${id}`),
  updateFraktion: (cid: string, id: string, body: Partial<Fraktion>) =>
    api.patch<Fraktion>(`${base(cid)}/fraktionen/${id}`, body),
  deleteFraktion: (cid: string, id: string) => api.delete<void>(`${base(cid)}/fraktionen/${id}`),

  /**
   * Womit sich diese Liste tatsächlich filtern lässt — aus dem echten Graphen.
   * Bewusst serverseitig ermittelt: sonst müsste die Oberfläche alle
   * Verbindungen laden, auch die, die sie gar nicht sehen darf.
   */
  filteroptionen: (cid: string, art: "personen" | "orte" | "events" | "fraktionen", personType?: "PC" | "NPC") =>
    api.get<FilterOptionen>(
      `${base(cid)}/filteroptionen?art=${art}${personType ? `&personType=${personType}` : ""}`
    ),

  listVerbindungen: (cid: string) => api.get<Verbindung[]>(`${base(cid)}/verbindungen`),
  createVerbindung: (cid: string, body: Omit<Verbindung, "id">) =>
    api.post<Verbindung>(`${base(cid)}/verbindungen`, body),
  updateVerbindung: (cid: string, id: string, body: Partial<Verbindung>) =>
    api.patch<Verbindung>(`${base(cid)}/verbindungen/${id}`, body),
  deleteVerbindung: (cid: string, id: string) => api.delete<void>(`${base(cid)}/verbindungen/${id}`),

  /** Gewächs — gewöhnliche Flora, generisches CRUD wie Ort/Event/Fraktion. */
  listGewaechse: (cid: string, filter?: ListenFilter) =>
    api.get<Gewaechs[]>(`${base(cid)}/gewaechse${query(filter)}`),
  createGewaechs: (cid: string, body: Omit<Gewaechs, "id">) => api.post<Gewaechs>(`${base(cid)}/gewaechse`, body),
  getGewaechs: (cid: string, id: string) => api.get<Gewaechs>(`${base(cid)}/gewaechse/${id}`),
  updateGewaechs: (cid: string, id: string, body: Partial<Gewaechs>) =>
    api.patch<Gewaechs>(`${base(cid)}/gewaechse/${id}`, body),
  deleteGewaechs: (cid: string, id: string) => api.delete<void>(`${base(cid)}/gewaechse/${id}`),

  /** Flora & Fauna (LEBT_IN) — many-to-many zwischen einem Ort und
   * Critter/Gewächs. Jede Mutation liefert die frische Liste zurück. */
  floraFaunaListe: (cid: string, ortId: string) =>
    api.get<LebtInEintrag[]>(`${base(cid)}/orte/${ortId}/flora-fauna`),
  floraFaunaHinzufuegen: (cid: string, ortId: string, artId: string) =>
    api.post<LebtInEintrag[]>(`${base(cid)}/orte/${ortId}/flora-fauna`, { artId }),
  floraFaunaEntfernen: (cid: string, ortId: string, artId: string) =>
    api.delete<LebtInEintrag[]>(`${base(cid)}/orte/${ortId}/flora-fauna/${artId}`),
  /** Reverse-Lookup: an welchen Orten ein Critter/Gewächs vorkommt. */
  floraFaunaOrte: (cid: string, artId: string) =>
    api.get<{ id: string; name: string }[]>(`${base(cid)}/flora-fauna/${artId}/orte`),
};
