/**
 * API für objektbezogene KI-Textgenerierung — der ✨-Knopf neben „SL-geheim"
 * im RichTextEditor (Beschreibung/Notizen jeder Entität).
 *
 * Getrennt von ideenschmiede/api.ts, weil dieser Aufruf nichts anlegt oder
 * verschiebt: er liefert nur einen Textvorschlag zurück, den das Frontend
 * bei „Übernehmen" selbst ans Editor-Ende anhängt (siehe KiTextPopup.tsx).
 */
import { api } from "../api/client";

export interface KiObjektTextInput {
  objektTyp: string;
  objektName: string;
  bisherigerText: string;
  prompt: string;
}

export async function kiObjektText(campaignId: string, input: KiObjektTextInput): Promise<string> {
  const antwort = await api.post<{ text: string }>(`/api/campaigns/${campaignId}/ki/objekt-text`, input);
  return antwort.text;
}

/** Ein von der KI erkannter Verknüpfungsvorschlag (Auto-Verknüpfung). */
export interface VerknuepfungsVorschlag {
  zitat: string;
  typ: "Person" | "Ort" | "Event" | "Fraktion";
  name: string;
  /** Gesetzt, wenn der Name zu einer bestehenden Entität passt; sonst legt
   * "anwenden" einen neuen Entwurf in der Ideenschmiede an. */
  zielId: string | null;
}

/** Ein von der KI erkannter Beziehungsvorschlag zwischen zwei Entitäten
 * (echte VERBINDUNG-Kante, nicht nur ein Verweis zur Wiki-Seite). */
export interface BeziehungsVorschlag {
  typ1: "Person" | "Ort" | "Event" | "Fraktion";
  name1: string;
  zielId1: string | null;
  typ2: "Person" | "Ort" | "Event" | "Fraktion";
  name2: string;
  zielId2: string | null;
  beziehungstyp: string;
  beschreibung: string;
}

export interface VorschlaegeAntwort {
  verweise: VerknuepfungsVorschlag[];
  beziehungen: BeziehungsVorschlag[];
}

export interface AnwendenErgebnis {
  ersetzt: boolean;
  inhalt: string;
  zielId: string;
  neuAngelegt: boolean;
}

export interface BeziehungAnwendenErgebnis {
  verbindungId: string;
  zielId1: string;
  zielId2: string;
  neuAngelegt1: boolean;
  neuAngelegt2: boolean;
}

/** Auto-Verknüpfung Schritt 1: lässt die KI Erwähnungen UND Beziehungen in der Seite erkennen. */
export async function verknuepfungsVorschlaege(campaignId: string, seitenId: string): Promise<VorschlaegeAntwort> {
  return api.post<VorschlaegeAntwort>(`/api/campaigns/${campaignId}/ki/wiki/${seitenId}/verknuepfung/vorschlaege`);
}

/** Auto-Verknüpfung Schritt 2: wendet EINEN bestätigten Verweis-Vorschlag an — fügt
 * den Verweis-Chip ein (legt bei Bedarf zuerst einen Ideenschmiede-Entwurf an). */
export async function verknuepfungAnwenden(
  campaignId: string,
  seitenId: string,
  vorschlag: VerknuepfungsVorschlag,
): Promise<AnwendenErgebnis> {
  return api.post<AnwendenErgebnis>(`/api/campaigns/${campaignId}/ki/wiki/${seitenId}/verknuepfung/anwenden`, {
    zitat: vorschlag.zitat,
    typ: vorschlag.typ,
    name: vorschlag.name,
    zielId: vorschlag.zielId,
  });
}

/** Auto-Verknüpfung Schritt 2b: wendet EINEN bestätigten Beziehungs-Vorschlag
 * an — legt eine echte VERBINDUNG-Kante zwischen den zwei Entitäten an (legt
 * bei Bedarf zuerst einen Ideenschmiede-Entwurf für die fehlende Seite an). */
export async function verknuepfungBeziehungAnwenden(
  campaignId: string,
  seitenId: string,
  vorschlag: BeziehungsVorschlag,
): Promise<BeziehungAnwendenErgebnis> {
  return api.post<BeziehungAnwendenErgebnis>(`/api/campaigns/${campaignId}/ki/wiki/${seitenId}/verknuepfung/beziehung`, {
    typ1: vorschlag.typ1,
    name1: vorschlag.name1,
    zielId1: vorschlag.zielId1,
    typ2: vorschlag.typ2,
    name2: vorschlag.name2,
    zielId2: vorschlag.zielId2,
    beziehungstyp: vorschlag.beziehungstyp,
    beschreibung: vorschlag.beschreibung,
  });
}
