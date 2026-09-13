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
        ressourcen: "",
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
