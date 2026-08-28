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
  notes: string;
  notizenSichtbarkeit: SichtbarkeitModus;
  notizenSichtbarFuer: string[];
}

export interface Ort extends VisibilityFields {
  id: string;
  name: string;
  description: string;
  notes: string;
  notizenSichtbarkeit: SichtbarkeitModus;
  notizenSichtbarFuer: string[];
}

export interface Event extends VisibilityFields {
  id: string;
  title: string;
  timestamp: string;
  description: string;
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

export const entitiesApi = {
  listPersonen: (cid: string) => api.get<Person[]>(`${base(cid)}/personen`),
  // Ungefiltert, für die Charakter-Auswahl der SL-Vorschau — siehe api.getAsGm.
  listPersonenAlsGm: (cid: string) => api.getAsGm<Person[]>(`${base(cid)}/personen`),
  createPerson: (cid: string, body: Omit<Person, "id">) => api.post<Person>(`${base(cid)}/personen`, body),

  listOrte: (cid: string) => api.get<Ort[]>(`${base(cid)}/orte`),
  createOrt: (cid: string, body: Omit<Ort, "id">) => api.post<Ort>(`${base(cid)}/orte`, body),

  listEvents: (cid: string) => api.get<Event[]>(`${base(cid)}/events`),
  createEvent: (cid: string, body: Omit<Event, "id">) => api.post<Event>(`${base(cid)}/events`, body),

  listVerbindungen: (cid: string) => api.get<Verbindung[]>(`${base(cid)}/verbindungen`),
  createVerbindung: (cid: string, body: Omit<Verbindung, "id">) =>
    api.post<Verbindung>(`${base(cid)}/verbindungen`, body),
};
