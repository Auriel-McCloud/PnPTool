import { api } from "../api/client";
import type { TraitDef, TraitRating } from "./api";

/** Abgeleitete Werte und Zustand — berechnet das Backend, siehe traits/bogen.py. */
export interface BogenUebersicht {
  weg: "KEINER" | "MAGIER" | "TECHNOMANCER";
  rasse: string;
  gesundheitMax: number;
  /** Summe aller Arten — für die Kurzanzeige. */
  gesundheitSchaden: number;
  schadenSchlag: number;
  schadenSchwer: number;
  schadenAggraviert: number;
  willenskraftMax: number;
  /** Wieviel davon das eingebaute Chrom dauerhaft frisst — 0 wenn keines. */
  willenskraftVerlust: number;
  willenskraftVerbraucht: number;
  iceMax: number;
  iceSchaden: number;
  /** Ohne Commlink ist man nicht angreifbar — anderer Zustand als "Wert 0". */
  offline: boolean;
  initiative: number;
  erfahrungGesamt: number;
  erfahrungAusgegeben: number;
  erfahrungVerfuegbar: number;
  /** Kopfzeile des Papierblatts. Fremde Charaktere liefern hier leer. */
  konzept: string;
  alter: string;
  ambition: string;
  verlangen: string;
  ziel: string;
  kapital: number;
  schulden: number;
  /** Solange falsch, zeigt das Blatt die Erstellung statt der Spielansicht. */
  erstellungAbgeschlossen: boolean;
}

export interface Bogen {
  person: { id: string; name: string; personType: string };
  uebersicht: BogenUebersicht;
  /**
   * Bonuswürfel aus ausgerüsteten Cyberdecks, je Matrix-Aktion. Gehört nicht
   * zu den Werten der Person, sondern zu ihrer Ausrüstung — mehrere Decks
   * addieren sich nicht, es zählt je Aktion das beste.
   */
  deckBoni: Record<string, number>;
  /** Bonuswürfel auf BESTEHENDE Werte aus ausgerüsteten Gegenständen
   * (z.B. Cyberaugen +1 auf Wahrnehmung). Schlüssel ist der Fertigkeits-/
   * Attributname; wird beim Anzeigen zum Grundwert dazuaddiert. */
  ausruestungsBoni: Record<string, number>;
  /** NEUE Fertigkeiten, die es ohne Ausrüstung nicht gibt (z.B. ein
   * Zauberstab mit "Springen 3") — eigener Abschnitt auf dem Blatt. */
  ausruestungsfertigkeiten: { name: string; bonus: number; quelle: string }[];
  /** Bereits nach dem Weg gefiltert: kein Magier, keine Sphären. */
  katalog: TraitDef[];
  werte: TraitRating[];
}

export interface ZustandUpdate {
  schadenSchlag?: number;
  schadenSchwer?: number;
  schadenAggraviert?: number;
  willenskraftVerbraucht?: number;
  iceSchaden?: number;
}

// --- Charaktererstellung ------------------------------------------------
// Spiegelt traits/erstellung.py. Die Zahlen kommen alle vom Server; hier
// steht bewusst keine einzige Regel, sonst laufen beide Seiten auseinander.

export interface Rasse {
  name: string;
  modifikatoren: Record<string, number>;
  /** Die drei Kontingente, frei auf die Attributspalten verteilbar. */
  freiePunkte: number[];
  beschreibung: string;
  startwerte: Record<string, number>;
  startmaxima: Record<string, number>;
}

export interface FertigkeitsPaket {
  id: string;
  name: string;
  beschreibung: string;
  /** Wert und Anzahl der Fertigkeiten, die genau diesen Wert bekommen. */
  verteilung: { wert: number; anzahl: number }[];
  anzahl: number;
}

export interface Erstellungsregeln {
  wege: { id: string; name: string; beschreibung: string }[];
  rassen: Rasse[];
  attributKategorien: { id: string; name: string; attribute: string[] }[];
  fertigkeitsPakete: FertigkeitsPaket[];
  hintergruende: { name: string; beschreibung: string }[];
  hintergrundMax: number;
  hintergrundPunkteGesamt: number;
  freebees: {
    gesamt: number;
    kostenJeKategorie: Record<string, number>;
    kostenWillenskraft: number;
    kostenKredit: number;
    kostenEigenkapital: number;
    kapitalJeFreebee: number;
    maxJeFertigkeit: number;
  };
  startkapital: number;
}

export interface ErstellungEingabe {
  weg: string;
  rasse: string;
  schwerpunkte: Record<string, number>;
  attributPunkte: Record<string, number>;
  fertigkeitsPaket: string;
  fertigkeitPunkte: Record<string, number>;
  hintergrundPunkte: Record<string, number>;
  freebeePunkte: Record<string, number>;
  freebeeWillenskraft: number;
  freebeeKredit: number;
  freebeeEigenkapital: number;
  konzept: string;
  alter: string;
  ambition: string;
  verlangen: string;
  ziel: string;
}

// --- Level Up -----------------------------------------------------------

export interface Steigerungspreis {
  traitDefId: string;
  name: string;
  category: string;
  aktuell: number;
  max: number;
  kosten: number;
}

export interface Steigerungen {
  verfuegbar: number;
  gesamt: number;
  werte: Steigerungspreis[];
  willenskraft: { aktuell: number; kosten: number };
}

export const bogenApi = {
  laden: (cid: string, personId: string) => api.get<Bogen>(`/api/campaigns/${cid}/personen/${personId}/bogen`),
  /** Zustand ändern — Schaden und Verbrauch, keine Werte. */
  zustand: (cid: string, personId: string, aenderung: ZustandUpdate) =>
    api.patch<BogenUebersicht>(`/api/campaigns/${cid}/personen/${personId}/zustand`, aenderung),

  regeln: (cid: string) => api.get<Erstellungsregeln>(`/api/campaigns/${cid}/erstellung/regeln`),
  erstellen: (cid: string, personId: string, eingabe: ErstellungEingabe) =>
    api.post<{ uebersicht: BogenUebersicht; freebeesVerbraucht: number }>(
      `/api/campaigns/${cid}/personen/${personId}/erstellung`,
      eingabe,
    ),

  preise: (cid: string, personId: string) =>
    api.get<Steigerungen>(`/api/campaigns/${cid}/personen/${personId}/steigern`),
  steigern: (cid: string, personId: string, was: { traitDefId?: string; willenskraft?: boolean }) =>
    api.post<Steigerungen>(`/api/campaigns/${cid}/personen/${personId}/steigern`, was),
  erfahrungVergeben: (cid: string, personId: string, punkte: number) =>
    api.post<BogenUebersicht>(`/api/campaigns/${cid}/personen/${personId}/erfahrung`, { punkte }),
};

/** Reihenfolge und Beschriftung der Wertegruppen auf dem Blatt. */
export const KATEGORIE_TITEL: Record<string, string> = {
  AttributKörperlich: "Körperlich",
  AttributGesellschaftlich: "Gesellschaftlich",
  AttributGeistig: "Geistig",
  Fertigkeit: "Fähigkeiten",
  Arete: "Arete",
  Sphäre: "Sphären",
  NeuroWeavingWert: "NeuroWeaving",
  NeuroWeaving: "NeuroWeaving-Fertigkeiten",
  Hintergrund: "Hintergründe",
};

export const ATTRIBUT_KATEGORIEN = [
  "AttributKörperlich",
  "AttributGesellschaftlich",
  "AttributGeistig",
] as const;
