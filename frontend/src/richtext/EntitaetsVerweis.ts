import { Node, mergeAttributes } from "@tiptap/core";

/**
 * Verknüpfung auf eine Kampagnen-Entität (NPC, Ort, Event, Gegenstand).
 *
 * Ein eigener Knoten statt eines Links, weil die Verknüpfung mehr ist als
 * ein Sprungziel: Beim Speichern liest der Server sie aus dem Dokument und
 * legt daraus echte Graphkanten an (:WikiSeite)-[:VERWEIST_AUF]->(:Person).
 * Daraus entstehen die Rückverweise am NPC ("Erwähnt in: Kapitel 1").
 *
 * `atom: true` — der Chip ist unteilbar. Sonst könnte man mit dem Cursor
 * mitten hineinfahren und den Namen zerschreiben, während die Ziel-ID bleibt.
 *
 * Der Typname muss zu VERWEIS_TYP in backend/app/wiki/logic.py passen.
 */
export interface VerweisAttribute {
  zielId: string;
  zielTyp: "Person" | "Ort" | "Event" | "Gegenstand";
  label: string;
}

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    entitaetsverweis: {
      verweisEinfuegen: (attrs: VerweisAttribute) => ReturnType;
    };
  }
}

/** Farb-Token je Entitätstyp — dieselben wie Graph und Badges. */
const TYP_TOKEN: Record<string, string> = {
  Person: "--kind-person",
  Ort: "--kind-ort",
  Event: "--kind-event",
  Gegenstand: "--kind-gegenstand",
};

export const EntitaetsVerweis = Node.create({
  name: "entitaetsverweis",
  group: "inline",
  inline: true,
  atom: true,
  selectable: true,

  addAttributes() {
    return {
      zielId: { default: null },
      zielTyp: { default: "Person" },
      label: { default: "" },
    };
  },

  parseHTML() {
    return [{ tag: 'span[data-entitaetsverweis="true"]' }];
  },

  renderHTML({ HTMLAttributes, node }) {
    const typ = String(node.attrs.zielTyp ?? "Person");
    return [
      "span",
      mergeAttributes(HTMLAttributes, {
        "data-entitaetsverweis": "true",
        class: "wiki-verweis",
        "data-typ": typ,
        // Der Chip trägt die Leitfarbe seines Typs; Token statt Hexwert,
        // damit ein Themewechsel ihn mitfärbt.
        style: `--verweis-ton: var(${TYP_TOKEN[typ] ?? "--neon"})`,
      }),
      String(node.attrs.label || "Unbenannt"),
    ];
  },

  renderText({ node }) {
    return String(node.attrs.label || "");
  },

  addCommands() {
    return {
      verweisEinfuegen:
        (attrs: VerweisAttribute) =>
        ({ commands }) =>
          commands.insertContent({ type: this.name, attrs }),
    };
  },
});
