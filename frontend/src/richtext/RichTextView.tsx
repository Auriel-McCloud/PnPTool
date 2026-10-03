import { EditorContent, useEditor, type JSONContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Table } from "@tiptap/extension-table";
import { TableRow } from "@tiptap/extension-table-row";
import { TableHeader } from "@tiptap/extension-table-header";
import { TableCell } from "@tiptap/extension-table-cell";
import { GmSecret } from "./GmSecretMark";
import { TextZoomKnoepfe } from "./TextZoomKnoepfe";
import "./richtext.css";

const EXTENSIONS = [StarterKit, Table.configure({ resizable: false }), TableRow, TableHeader, TableCell, GmSecret];

// Read-only Anzeige desselben Inhalts wie im RichTextEditor. GM-geheime
// Abschnitte werden hier weiterhin sichtbar und markiert dargestellt — das ist
// die SL-Sicht. Für Spieler sind sie gar nicht erst im Dokument: entfernt wird
// serverseitig in entities/visibility.py, bevor die Antwort rausgeht. Diese
// Komponente verlässt sich darauf und versteckt selbst nichts.
//
// Der Zoom-Knopf (A−/A+, Mark 03.10.2026) sitzt rechtsbündig über dem Text —
// hier gibt es sonst keine Werkzeugleiste. Wirkt global (richtext/textzoom.ts),
// trifft also auch jeden parallel offenen RichTextEditor.
export function RichTextView({ content }: { content: JSONContent }) {
  const editor = useEditor({ extensions: EXTENSIONS, content, editable: false });
  if (!editor) return null;
  return (
    <div className="rt-view rt-zoom-bereich">
      <div className="rt-view-werkzeuge">
        <TextZoomKnoepfe />
      </div>
      <EditorContent editor={editor} />
    </div>
  );
}
