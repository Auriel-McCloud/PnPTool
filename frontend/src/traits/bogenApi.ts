import { api } from "../api/client";
import type { TraitDef, TraitRating } from "./api";

/** Abgeleitete Werte und Zustand — berechnet das Backend, siehe traits/bogen.py. */
export interface BogenUebersicht {
  weg: "KEINER" | "MAGIER" | "TECHNOMANCER";
  rasse: string;
  gesundheitMax: number;
  gesundheitSchaden: number;
  willenskraftMax: number;
  willenskraftVerbraucht: number;
  iceMax: number;
  iceSchaden: number;
  /** Ohne Commlink ist man nicht angreifbar — anderer Zustand als "Wert 0". */
  offline: boolean;
  initiative: number;
  erfahrungGesamt: number;
  erfahrungVerfuegbar: number;
}

export interface Bogen {
  person: { id: string; name: string; personType: string };
  uebersicht: BogenUebersicht;
  /** Bereits nach dem Weg gefiltert: kein Magier, keine Sphären. */
  katalog: TraitDef[];
  werte: TraitRating[];
}

export const bogenApi = {
  laden: (cid: string, personId: string) => api.get<Bogen>(`/api/campaigns/${cid}/personen/${personId}/bogen`),
};

/** Reihenfolge und Beschriftung der Wertegruppen auf dem Blatt. */
export const KATEGORIE_TITEL: Record<string, string> = {
  AttributKörperlich: "Körperlich",
  AttributGesellschaftlich: "Gesellschaftlich",
  AttributGeistig: "Geistig",
  Fertigkeit: "Fähigkeiten",
  Arete: "Arete",
  Sphäre: "Sphären",
  NeuroWeaving: "NeuroWeaving",
};

export const ATTRIBUT_KATEGORIEN = [
  "AttributKörperlich",
  "AttributGesellschaftlich",
  "AttributGeistig",
] as const;
