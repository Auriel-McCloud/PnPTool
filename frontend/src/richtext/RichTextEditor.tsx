import { EditorContent, useEditor, type JSONContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Table } from "@tiptap/extension-table";
import { TableRow } from "@tiptap/extension-table-row";
import { TableHeader } from "@tiptap/extension-table-header";
import { TableCell } from "@tiptap/extension-table-cell";
import { GmSecret } from "./GmSecretMark";
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
        background: active ? "#333" : "#f0f0f0",
        color: active ? "#fff" : "#000",
        border: "1px solid #ccc",
        borderRadius: 4,
        padding: "4px 8px",
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
}: {
  content: JSONContent;
  onChange: (doc: JSONContent) => void;
  minHeight?: number;
}) {
  const editor = useEditor({
    extensions: EXTENSIONS,
    content,
    onUpdate: ({ editor }) => onChange(editor.getJSON()),
  });

  if (!editor) return null;

  return (
    <div style={{ border: "1px solid #ccc", borderRadius: 6 }}>
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", padding: 6, borderBottom: "1px solid #eee" }}>
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
        <span style={{ borderLeft: "1px solid #ddd", margin: "0 4px" }} />
        <ToolbarButton
          title="Markierten Text vor Spielern verstecken (nur du siehst die Markierung)"
          active={editor.isActive("gmSecret")}
          onClick={() => editor.chain().focus().toggleGmSecret().run()}
        >
          🔒 SL-geheim
        </ToolbarButton>
      </div>
      <div style={{ padding: 10, minHeight }}>
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}
