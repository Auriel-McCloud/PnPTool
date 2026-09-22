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
