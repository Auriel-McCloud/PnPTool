/**
 * API für die Ideenschmiede.
 *
 * Die Ideenschmiede zeigt alle Entitäten mit istEntwurf=true.
 * "In Kampagne verschieben" setzt istEntwurf auf false.
 */

import { api } from "../api/client";

export interface EntwurfItem {
  id: string;
  typ: "Person" | "Ort" | "Event" | "WikiSeite" | "Gegenstand" | "Fraktion";
  name: string;
  beschreibung: string;
  erstelltAm?: string;
}

/**
 * Holt alle Entwürfe einer Kampagne (istEntwurf=true).
 * Verwendet die spezielle /entwuerfe Route.
 */
export async function getEntwuerfe(campaignId: string): Promise<EntwurfItem[]> {
  try {
    const entwuerfe = await api.get<any[]>(`/api/campaigns/${campaignId}/entwuerfe`);
    return entwuerfe.map((e) => ({
      id: e.id,
      typ: e.typ === "person" ? "Person" : e.typ === "ort" ? "Ort" : e.typ === "event" ? "Event" : e.typ,
      name: e.name || e.title || "Unbenannt",
      beschreibung: e.description || "",
      erstelltAm: e.erstelltAm,
    }));
  } catch {
    return [];
  }
}

/**
 * Verschiebt einen Entwurf in die Kampagne (setzt istEntwurf=false).
 */
export async function inKampagneVerschieben(
  campaignId: string,
  typ: EntwurfItem["typ"],
  id: string
): Promise<void> {
  const endpunkte: Record<EntwurfItem["typ"], string> = {
    Person: `/api/campaigns/${campaignId}/personen/${id}`,
    Ort: `/api/campaigns/${campaignId}/orte/${id}`,
    Event: `/api/campaigns/${campaignId}/events/${id}`,
    WikiSeite: `/api/campaigns/${campaignId}/wiki/seiten/${id}`,
    Gegenstand: `/api/campaigns/${campaignId}/gegenstaende/${id}`,
    Fraktion: `/api/campaigns/${campaignId}/fraktionen/${id}`,
  };

  await api.patch(endpunkte[typ], { istEntwurf: false });
}

/**
 * Löscht einen Entwurf.
 */
export async function entwurfLoeschen(
  campaignId: string,
  typ: EntwurfItem["typ"],
  id: string
): Promise<void> {
  const endpunkte: Record<EntwurfItem["typ"], string> = {
    Person: `/api/campaigns/${campaignId}/personen/${id}`,
    Ort: `/api/campaigns/${campaignId}/orte/${id}`,
    Event: `/api/campaigns/${campaignId}/events/${id}`,
    WikiSeite: `/api/campaigns/${campaignId}/wiki/seiten/${id}`,
    Gegenstand: `/api/campaigns/${campaignId}/gegenstaende/${id}`,
    Fraktion: `/api/campaigns/${campaignId}/fraktionen/${id}`,
  };

  await api.delete(endpunkte[typ]);
}

/**
 * Legt einen neuen Entwurf an (istEntwurf=true).
 */
export async function entwurfAnlegen(
  campaignId: string,
  typ: EntwurfItem["typ"],
  name: string
): Promise<void> {
  switch (typ) {
    case "Person":
      await api.post(`/api/campaigns/${campaignId}/personen`, {
        name,
        personType: "NPC",
        description: "",
        notes: "",
        istEntwurf: true,
        sichtbarkeit: "GM",
        sichtbarFuer: [],
        notizenSichtbarkeit: "GM",
        notizenSichtbarFuer: [],
      });
      break;
    case "Ort":
      await api.post(`/api/campaigns/${campaignId}/orte`, {
        name,
        description: "",
        notes: "",
        istEntwurf: true,
        sichtbarkeit: "GM",
        sichtbarFuer: [],
        notizenSichtbarkeit: "GM",
        notizenSichtbarFuer: [],
      });
      break;
    case "Event":
      await api.post(`/api/campaigns/${campaignId}/events`, {
        title: name,
        timestamp: "",
        description: "",
        notes: "",
        istEntwurf: true,
        sichtbarkeit: "GM",
        sichtbarFuer: [],
        notizenSichtbarkeit: "GM",
        notizenSichtbarFuer: [],
      });
      break;
    case "WikiSeite":
      await api.post(`/api/campaigns/${campaignId}/wiki/seiten`, {
        titel: name,
        inhalt: '{"type":"doc","content":[]}',
        istEntwurf: true,
        sichtbarkeit: "GM",
        sichtbarFuer: [],
      });
      break;
    case "Gegenstand":
      await api.post(`/api/campaigns/${campaignId}/gegenstaende`, {
        name,
        description: "",
        notes: "",
        typ: "Sonstiges",
        istEntwurf: true,
      });
      break;
    case "Fraktion":
      await api.post(`/api/campaigns/${campaignId}/fraktionen`, {
        name,
        description: "",
        ziele: [],
        ressourcen: [],
        notes: "",
        istEntwurf: true,
        sichtbarkeit: "GM",
        sichtbarFuer: [],
        notizenSichtbarkeit: "GM",
        notizenSichtbarFuer: [],
      });
      break;
  }
}

export type KiTyp = "story" | "charakter" | "gegenstand";

/**
 * Lässt Gemini eine Idee generieren und als Entwurf in der Schmiede ablegen.
 * `story` wird eine Wiki-Seite (Geschichte), `charakter` ein NPC, `gegenstand`
 * eine Gegenstands-Vorlage (Typ per festem Katalog, danach nicht mehr
 * änderbar — siehe items/typKatalog.ts).
 */
export async function kiIdee(campaignId: string, typ: KiTyp, prompt: string): Promise<void> {
  await api.post(`/api/campaigns/${campaignId}/ki/idee`, { typ, prompt });
}

/** Ein einzelner Befund der Rechtschreib-/Grammatik-/Logikprüfung. */
export interface PruefBefund {
  art: "rechtschreibung" | "grammatik" | "logik";
  zitat: string;
  vorschlag: string;
  begruendung: string;
}

/** Prüft eine einzelne Wiki-Seite (Knopf direkt im Editor). */
export async function seitePruefen(campaignId: string, seitenId: string): Promise<PruefBefund[]> {
  const antwort = await api.post<{ befunde: PruefBefund[] }>(
    `/api/campaigns/${campaignId}/ki/wiki/${seitenId}/pruefen`,
  );
  return antwort.befunde;
}

/** Ergebnis eines Sweeps: welche Seiten wurden geprüft/übersprungen, mit Befunden je Seite. */
export interface SweepSeite {
  seitenId: string;
  titel: string;
  befunde: PruefBefund[];
}

export interface SweepErgebnis {
  geprueft: number;
  uebersprungen: number;
  ergebnisse: SweepSeite[];
}

/**
 * Prüft ALLE Wiki-Seiten der Kampagne, überspringt unveränderte seit der
 * letzten Prüfung. Für den "Prüf Fließtext!"-Knopf in den Einstellungen —
 * bewusst kein automatischer Hintergrundlauf, Mark will das gezielt anstoßen.
 */
export async function wikiSweep(campaignId: string): Promise<SweepErgebnis> {
  return api.post<SweepErgebnis>(`/api/campaigns/${campaignId}/ki/wiki/pruefen-alle`);
}

/** Übernimmt einen Korrekturvorschlag: ersetzt das Zitat direkt im Seitentext. */
export async function befundUebernehmen(
  campaignId: string,
  seitenId: string,
  zitat: string,
  vorschlag: string,
): Promise<{ ersetzt: boolean; inhalt: string }> {
  return api.post(`/api/campaigns/${campaignId}/ki/wiki/${seitenId}/pruefung/uebernehmen`, {
    zitat,
    vorschlag,
  });
}
