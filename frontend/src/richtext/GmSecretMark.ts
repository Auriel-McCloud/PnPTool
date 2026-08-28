import { Mark, mergeAttributes } from "@tiptap/core";

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    gmSecret: {
      toggleGmSecret: () => ReturnType;
    };
  }
}

// Markiert einen Textabschnitt als "vor Spielern verstecken" — wie Fett/Kursiv,
// aber mit Sichtbarkeits-Semantik statt reiner Formatierung. Wird serverseitig
// aus Spieler-Antworten entfernt (siehe backend/app/entities/visibility.py),
// die client-seitige Markierung ist nur für die SL-Ansicht beim Bearbeiten.
export const GmSecret = Mark.create({
  name: "gmSecret",

  parseHTML() {
    return [{ tag: "span[data-gm-secret]" }];
  },

  renderHTML({ HTMLAttributes }) {
    return ["span", mergeAttributes(HTMLAttributes, { "data-gm-secret": "true", class: "gm-secret" }), 0];
  },

  addCommands() {
    return {
      toggleGmSecret:
        () =>
        ({ commands }) =>
          commands.toggleMark(this.name),
    };
  },
});
