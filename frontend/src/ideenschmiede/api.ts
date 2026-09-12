/**
 * API für die Ideenschmiede.
 *
 * Die Ideenschmiede zeigt alle Entitäten mit istEntwurf=true.
 * "In Kampagne verschieben" setzt istEntwurf auf false.
 */

import { api } from "../api/client";

export interface EntwurfItem {
  id: string;
  typ: "Person" | "Ort" | "Event" | "WikiSeite" | "Gegenstand";
  name: string;
  beschreibung: string;
  erstelltAm?: string;
}

/**
 * Holt alle Entwürfe einer Kampagne (istEntwurf=true).
 * Sammelt aus verschiedenen Endpunkten und filtert.
 */
export async function getEntwuerfe(campaignId: string): Promise<EntwurfItem[]> {
  const entwuerfe: EntwurfItem[] = [];

  // Personen
  const personen = await api.get<any[]>(`/campaigns/${campaignId}/personen`);
  for (const p of personen.filter((x) => x.istEntwurf)) {
    entwuerfe.push({
      id: p.id,
      typ: "Person",
      name: p.name,
      beschreibung: p.description || "",
    });
  }

  // Orte
  const orte = await api.get<any[]>(`/campaigns/${campaignId}/orte`);
  for (const o of orte.filter((x) => x.istEntwurf)) {
    entwuerfe.push({
      id: o.id,
      typ: "Ort",
      name: o.name,
      beschreibung: o.description || "",
    });
  }

  // Events
  const events = await api.get<any[]>(`/campaigns/${campaignId}/events`);
  for (const e of events.filter((x) => x.istEntwurf)) {
    entwuerfe.push({
      id: e.id,
      typ: "Event",
      name: e.title,
      beschreibung: e.description || "",
    });
  }

  // WikiSeiten
  const seiten = await api.get<any[]>(`/campaigns/${campaignId}/wiki/seiten`);
  for (const s of seiten.filter((x) => x.istEntwurf)) {
    entwuerfe.push({
      id: s.id,
      typ: "WikiSeite",
      name: s.titel,
      beschreibung: "",
      erstelltAm: s.erstelltAm,
    });
  }

  // Gegenstände (Vorlagen ohne Besitzer)
  const vorlagen = await api.get<any[]>(`/campaigns/${campaignId}/vorlagen`);
  for (const g of vorlagen.filter((x) => x.istEntwurf)) {
    entwuerfe.push({
      id: g.id,
      typ: "Gegenstand",
      name: g.name,
      beschreibung: g.description || "",
    });
  }

  return entwuerfe;
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
    Person: `/campaigns/${campaignId}/personen/${id}`,
    Ort: `/campaigns/${campaignId}/orte/${id}`,
    Event: `/campaigns/${campaignId}/events/${id}`,
    WikiSeite: `/campaigns/${campaignId}/wiki/seiten/${id}`,
    Gegenstand: `/campaigns/${campaignId}/vorlagen/${id}`,
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
    Person: `/campaigns/${campaignId}/personen/${id}`,
    Ort: `/campaigns/${campaignId}/orte/${id}`,
    Event: `/campaigns/${campaignId}/events/${id}`,
    WikiSeite: `/campaigns/${campaignId}/wiki/seiten/${id}`,
    Gegenstand: `/campaigns/${campaignId}/vorlagen/${id}`,
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
      await api.post(`/campaigns/${campaignId}/personen`, {
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
      await api.post(`/campaigns/${campaignId}/orte`, {
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
      await api.post(`/campaigns/${campaignId}/events`, {
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
      await api.post(`/campaigns/${campaignId}/wiki/seiten`, {
        titel: name,
        inhalt: '{"type":"doc","content":[]}',
        istEntwurf: true,
        sichtbarkeit: "GM",
        sichtbarFuer: [],
      });
      break;
    case "Gegenstand":
      await api.post(`/campaigns/${campaignId}/vorlagen`, {
        name,
        description: "",
        notes: "",
        typ: "Sonstiges",
        istEntwurf: true,
      });
      break;
  }
}
