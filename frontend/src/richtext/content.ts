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

// Reiner Text aus dem TipTap-Dokument — für Stellen, die keinen Editor zur
// Hand haben (der hat sein eigenes editor.getText()), aber trotzdem Text
// brauchen, z.B. den KI-Bild-Prompt-Vorschlag aus der Beschreibung eines
// Orts/Gegenstands. Nimmt direkt den `description`-Rohstring (JSON oder
// Altformat), nicht das schon geparste Dokument — spart den Umweg über
// parseRichText an jeder Aufrufstelle.
export function extrahiereReinenText(raw: string): string {
  const doc = parseRichText(raw);
  const teile: string[] = [];
  function sammeln(node: JSONContent) {
    if (node.type === "text" && node.text) teile.push(node.text);
    node.content?.forEach(sammeln);
  }
  sammeln(doc);
  return teile.join(" ").trim();
}
