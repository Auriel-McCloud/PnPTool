import { api } from "../api/client";

/**
 * Zusatzfertigkeiten: campaign-gebundener Katalog (kein globaler Katalog +
 * Freigabe wie bei Rassen — jeder Eintrag ist sofort in dieser Kampagne
 * wählbar), siehe backend/app/zusatzfertigkeiten/repository.py.
 */
export interface Zusatzfertigkeit {
  id: string;
  campaignId: string;
  name: string;
  kurzbeschreibung: string;
  detailbeschreibung: string;
  /** Rassengebunden (10.10.2026, Vaet-Transformation): leer = für alle
   * wählbar, gesetzt = nur diese Rasse sieht/wählt sie. */
  nurFuerRasse: string;
}

export interface ZusatzfertigkeitEingabe {
  name?: string;
  kurzbeschreibung?: string;
  detailbeschreibung?: string;
  nurFuerRasse?: string;
}

/** Eine von einer Person gewählte Zusatzfertigkeit samt Stufe. */
export interface PersonZusatzfertigkeit {
  id: string;
  name: string;
  kurzbeschreibung: string;
  detailbeschreibung: string;
  rating: number;
}

export interface PersonZusatzfertigkeitenAntwort {
  gewaehlt: PersonZusatzfertigkeit[];
  erstellungAbgeschlossen: boolean;
  /** Nur vor Erstellungsabschluss relevant. */
  freebeesUebrig: number;
  /** Nur nach Erstellungsabschluss relevant. */
  erfahrungVerfuegbar: number;
}

export interface ZusatzfertigkeitVorschlag {
  name: string;
  kurzbeschreibung: string;
  detailbeschreibung: string;
}

function katalogBasis(cid: string) {
  return `/api/campaigns/${cid}/zusatzfertigkeiten`;
}

function personBasis(cid: string, personId: string) {
  return `/api/campaigns/${cid}/personen/${personId}/zusatzfertigkeiten`;
}

export const zusatzfertigkeitenApi = {
  /** Der ganze Katalog dieser Kampagne — für SL-Tabelle UND Spieler-Popup. */
  liste: (cid: string) => api.get<Zusatzfertigkeit[]>(katalogBasis(cid)),
  anlegen: (cid: string, body: ZusatzfertigkeitEingabe & { name: string }) =>
    api.post<Zusatzfertigkeit>(katalogBasis(cid), body),
  aendern: (cid: string, id: string, body: ZusatzfertigkeitEingabe) =>
    api.patch<Zusatzfertigkeit>(`${katalogBasis(cid)}/${id}`, body),
  loeschen: (cid: string, id: string) => api.delete<void>(`${katalogBasis(cid)}/${id}`),

  /** KI-Vorschläge (nur SL) — speichert nichts, siehe ki-vorschlag.py. */
  kiVorschlaege: (cid: string, anzahl = 5) =>
    api.get<{ vorschlaege: ZusatzfertigkeitVorschlag[] }>(`${katalogBasis(cid)}/ki-vorschlaege?anzahl=${anzahl}`),
  kiVorschlagUebernehmen: (cid: string, vorschlag: ZusatzfertigkeitVorschlag) =>
    api.post<Zusatzfertigkeit>(`${katalogBasis(cid)}/ki-vorschlaege/uebernehmen`, vorschlag),

  /** Gewählte Zusatzfertigkeiten einer Person samt Kostenkontingent. */
  vonPerson: (cid: string, personId: string) =>
    api.get<PersonZusatzfertigkeitenAntwort>(personBasis(cid, personId)),
  /** Eine noch nicht gewählte Zusatzfertigkeit mit Stufe 1 anlegen — zieht
   * Freebee ODER EP ab, je nach Erstellungsphase (Backend entscheidet). */
  hinzufuegen: (cid: string, personId: string, zusatzfertigkeitId: string) =>
    api.post<PersonZusatzfertigkeitenAntwort>(personBasis(cid, personId), { zusatzfertigkeitId }),
  /** Eine bereits gewählte Zusatzfertigkeit um einen Punkt steigern (EP). */
  steigern: (cid: string, personId: string, zusatzfertigkeitId: string) =>
    api.post<PersonZusatzfertigkeitenAntwort>(`${personBasis(cid, personId)}/${zusatzfertigkeitId}/steigern`, {}),
};
