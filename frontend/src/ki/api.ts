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

export interface AnwendenErgebnis {
  ersetzt: boolean;
  inhalt: string;
  zielId: string;
  neuAngelegt: boolean;
}

/** Auto-Verknüpfung Schritt 1: lässt die KI Erwähnungen in der Seite erkennen. */
export async function verknuepfungsVorschlaege(campaignId: string, seitenId: string): Promise<VerknuepfungsVorschlag[]> {
  return api.post<VerknuepfungsVorschlag[]>(`/api/campaigns/${campaignId}/ki/wiki/${seitenId}/verknuepfung/vorschlaege`);
}

/** Auto-Verknüpfung Schritt 2: wendet EINEN bestätigten Vorschlag an — fügt
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
