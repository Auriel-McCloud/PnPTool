import { api } from "../api/client";

export type SichtbarkeitModus = "GM" | "ALLE" | "SPEZIFISCH";
export type EntityKind = "Person" | "Ort" | "Event" | "Gegenstand";

export interface VisibilityFields {
  sichtbarkeit: SichtbarkeitModus;
  sichtbarFuer: string[];
}

export interface Person extends VisibilityFields {
  id: string;
  name: string;
  personType: "PC" | "NPC";
  description: string;
  /** Welche Silhouette die Körperkarte zeigt. */
  silhouette?: string;
  /** Aussehen; per Blitz an alle Spieler zeigbar. */
  bildUrl?: string;
  notes: string;
  notizenSichtbarkeit: SichtbarkeitModus;
  notizenSichtbarFuer: string[];
}

export interface Ort extends VisibilityFields {
  id: string;
  name: string;
  description: string;
  bildUrl?: string;
  notes: string;
  notizenSichtbarkeit: SichtbarkeitModus;
  notizenSichtbarFuer: string[];
}

export interface Event extends VisibilityFields {
  id: string;
  title: string;
  timestamp: string;
  description: string;
  bildUrl?: string;
  notes: string;
  notizenSichtbarkeit: SichtbarkeitModus;
  notizenSichtbarFuer: string[];
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

  /**
   * Womit sich diese Liste tatsächlich filtern lässt — aus dem echten Graphen.
   * Bewusst serverseitig ermittelt: sonst müsste die Oberfläche alle
   * Verbindungen laden, auch die, die sie gar nicht sehen darf.
   */
  filteroptionen: (cid: string, art: "personen" | "orte" | "events", personType?: "PC" | "NPC") =>
    api.get<FilterOptionen>(
      `${base(cid)}/filteroptionen?art=${art}${personType ? `&personType=${personType}` : ""}`
    ),

  listVerbindungen: (cid: string) => api.get<Verbindung[]>(`${base(cid)}/verbindungen`),
  createVerbindung: (cid: string, body: Omit<Verbindung, "id">) =>
    api.post<Verbindung>(`${base(cid)}/verbindungen`, body),
  deleteVerbindung: (cid: string, id: string) => api.delete<void>(`${base(cid)}/verbindungen/${id}`),
};
