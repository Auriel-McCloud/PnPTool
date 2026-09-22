import { EditorContent, useEditor, type JSONContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Table } from "@tiptap/extension-table";
import { TableRow } from "@tiptap/extension-table-row";
import { TableHeader } from "@tiptap/extension-table-header";
import { TableCell } from "@tiptap/extension-table-cell";
import { useState } from "react";
import { GmSecret } from "./GmSecretMark";
import { KiTextPopup } from "../ki/KiTextPopup";
import "./richtext.css";

const EXTENSIONS = [
  StarterKit,
  Table.configure({ resizable: false }),
  TableRow,
  TableHeader,
  TableCell,
  GmSecret,
];

function ToolbarButton({
  active,
  onClick,
  title,
  children,
}: {
  active?: boolean;
  onClick: () => void;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      title={title}
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
      style={{
        fontWeight: active ? "bold" : "normal",
        background: active ? "var(--neon-schwach)" : "var(--flaeche)",
        color: active ? "var(--neon)" : "var(--text-leise)",
        border: `1px solid ${active ? "var(--neon)" : "var(--linie)"}`,
        borderRadius: 4,
        padding: "4px 8px",
        // Werkzeugleiste des Editors: viele Knöpfe nebeneinander, hier ist die
        // globale Touch-Mindesthöhe zu wuchtig.
        minHeight: 0,
        cursor: "pointer",
      }}
    >
      {children}
    </button>
  );
}

export function RichTextEditor({
  content,
  onChange,
  minHeight = 120,
  kiKontext,
}: {
  content: JSONContent;
  onChange: (doc: JSONContent) => void;
  minHeight?: number;
  /**
   * Aktiviert den ✨ KI-Knopf neben „SL-geheim" (Mark, 22.09.2026: an jeder
   * Stelle, an der man in Beschreibung/Notizen klickt). Ohne diese Prop
   * bleibt der Knopf verborgen — Aufrufer ohne campaignId/Objektbezug (z.B.
   * ein Anlege-Formular für eine noch nicht existierende Entität) brauchen
   * ihn nicht anzubieten.
   */
  kiKontext?: {
    campaignId: string;
    objektTyp: string;
    objektName: string;
    feldLabel: string;
  };
}) {
  const [kiOffen, setKiOffen] = useState(false);
  const editor = useEditor({
    extensions: EXTENSIONS,
    content,
    onUpdate: ({ editor }) => onChange(editor.getJSON()),
  });

  if (!editor) return null;

  function textAnhaengen(text: string) {
    if (!editor) return;
    // Ans Ende des Dokuments anhängen (Marks Wunsch: bisheriger Inhalt
    // bleibt erhalten). Leere Zeile trennt Absätze, wie bei der
    // Ideenschmiede-Story-Generierung (_text_zu_dokument im Backend).
    editor.chain().focus("end").run();
    const absaetze = text.split("\n\n").map((a) => a.trim()).filter(Boolean);
    for (const absatz of absaetze.length ? absaetze : [text]) {
      editor.chain().focus("end").insertContent({ type: "paragraph", content: [{ type: "text", text: absatz }] }).run();
    }
  }

  return (
    <div style={{ border: "1px solid var(--linie)", borderRadius: 6 }}>
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", padding: 6, borderBottom: "1px solid var(--linie)" }}>
        <ToolbarButton title="Fett" active={editor.isActive("bold")} onClick={() => editor.chain().focus().toggleBold().run()}>
          B
        </ToolbarButton>
        <ToolbarButton
          title="Kursiv"
          active={editor.isActive("italic")}
          onClick={() => editor.chain().focus().toggleItalic().run()}
        >
          I
        </ToolbarButton>
        <ToolbarButton
          title="Aufzählung"
          active={editor.isActive("bulletList")}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
        >
          • Liste
        </ToolbarButton>
        <ToolbarButton
          title="Tabelle einfügen"
          onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}
        >
          ▦ Tabelle
        </ToolbarButton>
        <span style={{ borderLeft: "1px solid var(--linie)", margin: "0 4px" }} />
        <ToolbarButton
          title="Markierten Text vor Spielern verstecken (nur du siehst die Markierung)"
          active={editor.isActive("gmSecret")}
          onClick={() => editor.chain().focus().toggleGmSecret().run()}
        >
          🔒 SL-geheim
        </ToolbarButton>
        {kiKontext && (
          <ToolbarButton title="Mit KI einen Textvorschlag für dieses Feld generieren" onClick={() => setKiOffen(true)}>
            <span className="rt-ki-btn">✨ KI</span>
          </ToolbarButton>
        )}
      </div>
      <div style={{ padding: 10, minHeight }}>
        <EditorContent editor={editor} />
      </div>
      {kiKontext && (
        <KiTextPopup
          offen={kiOffen}
          campaignId={kiKontext.campaignId}
          objektTyp={kiKontext.objektTyp}
          objektName={kiKontext.objektName}
          feldLabel={kiKontext.feldLabel}
          bisherigerText={editor.getText()}
          onSchliessen={() => setKiOffen(false)}
          onUebernehmen={textAnhaengen}
        />
      )}
    </div>
  );
}
