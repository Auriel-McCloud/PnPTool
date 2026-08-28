import type { JSONContent } from "@tiptap/react";

export const EMPTY_DOC: JSONContent = { type: "doc", content: [{ type: "paragraph" }] };

function isTiptapDoc(value: unknown): value is JSONContent {
  return typeof value === "object" && value !== null && (value as JSONContent).type === "doc";
}

// Bestehende Demo-/Altdaten sind noch reine Strings (aus der Zeit vor dem
// Rich-Text-Editor). Für Kompatibilität wird ein nicht-JSON-String als ein
// einzelner Absatz interpretiert statt einen Fehler zu werfen.
export function parseRichText(raw: string): JSONContent {
  if (!raw) return EMPTY_DOC;
  try {
    const parsed = JSON.parse(raw);
    if (isTiptapDoc(parsed)) return parsed;
  } catch {
    // kein JSON -> Altformat, als Klartext behandeln
  }
  return { type: "doc", content: [{ type: "paragraph", content: [{ type: "text", text: raw }] }] };
}

export function serializeRichText(doc: JSONContent): string {
  return JSON.stringify(doc);
}
