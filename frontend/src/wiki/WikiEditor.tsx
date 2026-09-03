import { useEffect, useRef, useState } from "react";
import { EditorContent, useEditor, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Table } from "@tiptap/extension-table";
import { TableRow } from "@tiptap/extension-table-row";
import { TableHeader } from "@tiptap/extension-table-header";
import { TableCell } from "@tiptap/extension-table-cell";
import Image from "@tiptap/extension-image";
import { GmSecret } from "../richtext/GmSecretMark";
import { EntitaetsVerweis, type VerweisAttribute } from "../richtext/EntitaetsVerweis";
import { VerweisWaehler } from "./VerweisWaehler";
import { bildHochladen } from "./api";
import "../richtext/richtext.css";

/**
 * Der Wiki-Editor.
 *
 * Anders als der kleine RichTextEditor an den Entitäten: Überschriften
 * (daraus entsteht das Inhaltsverzeichnis), Bilder und Verknüpfungen auf
 * Kampagnenobjekte.
 *
 * Gespeichert wird als TipTap-JSON-String — dasselbe Format wie überall
 * sonst, damit die serverseitige 🔒-Redaktion unverändert greift.
 */

function Knopf({
  aktiv,
  onClick,
  title,
  children,
  disabled,
}: {
  aktiv?: boolean;
  onClick: () => void;
  title: string;
  children: React.ReactNode;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      title={title}
      disabled={disabled}
      // Ohne das verliert der Editor beim Klick den Fokus und die Auswahl —
      // ein Format ließe sich dann nie auf markierten Text anwenden.
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
      className="wk-werkzeug"
      style={{
        background: aktiv ? "var(--neon-schwach)" : "var(--flaeche)",
        color: aktiv ? "var(--neon)" : "var(--text-leise)",
        border: `1px solid ${aktiv ? "var(--neon)" : "var(--linie)"}`,
      }}
    >
      {children}
    </button>
  );
}

function Werkzeugleiste({
  editor,
  onVerweis,
  onBild,
  laedtBild,
}: {
  editor: Editor;
  onVerweis: () => void;
  onBild: () => void;
  laedtBild: boolean;
}) {
  return (
    <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 8 }}>
      {[1, 2, 3].map((stufe) => (
        <Knopf
          key={stufe}
          title={`Überschrift ${stufe} — erscheint im Inhaltsverzeichnis`}
          aktiv={editor.isActive("heading", { level: stufe })}
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: stufe as 1 | 2 | 3 }).run()
          }
        >
          H{stufe}
        </Knopf>
      ))}
      <span style={{ borderLeft: "1px solid var(--linie)", margin: "0 4px" }} />
      <Knopf title="Fett" aktiv={editor.isActive("bold")} onClick={() => editor.chain().focus().toggleBold().run()}>
        B
      </Knopf>
      <Knopf title="Kursiv" aktiv={editor.isActive("italic")} onClick={() => editor.chain().focus().toggleItalic().run()}>
        I
      </Knopf>
      <Knopf
        title="Aufzählung"
        aktiv={editor.isActive("bulletList")}
        onClick={() => editor.chain().focus().toggleBulletList().run()}
      >
        • Liste
      </Knopf>
      <Knopf
        title="Zitat"
        aktiv={editor.isActive("blockquote")}
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
      >
        ❝
      </Knopf>
      <Knopf
        title="Tabelle einfügen"
        onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}
      >
        ▦
      </Knopf>
      <span style={{ borderLeft: "1px solid var(--linie)", margin: "0 4px" }} />
      <Knopf title="Person, Ort oder Event verknüpfen" onClick={onVerweis}>
        ⧉ Verknüpfen
      </Knopf>
      <Knopf title="Bild hochladen" onClick={onBild} disabled={laedtBild}>
        {laedtBild ? "lädt…" : "▣ Bild"}
      </Knopf>
      <span style={{ borderLeft: "1px solid var(--linie)", margin: "0 4px" }} />
      <Knopf
        title="Markierten Text vor Spielern verstecken"
        aktiv={editor.isActive("gmSecret")}
        onClick={() => editor.chain().focus().toggleGmSecret().run()}
      >
        🔒 SL-geheim
      </Knopf>
    </div>
  );
}

export function WikiEditor({
  campaignId,
  seitenId,
  inhalt,
  onChange,
  nurLesen = false,
}: {
  campaignId: string;
  /** Wechselt die Seite, wird der Editor neu befüllt. */
  seitenId: string;
  inhalt: string;
  onChange: (json: string) => void;
  nurLesen?: boolean;
}) {
  const [waehlerOffen, setWaehlerOffen] = useState(false);
  const [laedtBild, setLaedtBild] = useState(false);
  const dateiRef = useRef<HTMLInputElement>(null);

  const editor = useEditor(
    {
      extensions: [
        StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
        Table.configure({ resizable: false }),
        TableRow,
        TableHeader,
        TableCell,
        Image.configure({ inline: false }),
        GmSecret,
        EntitaetsVerweis,
      ],
      content: inhalt ? JSON.parse(inhalt) : undefined,
      editable: !nurLesen,
      onUpdate: ({ editor }) => onChange(JSON.stringify(editor.getJSON())),
    },
    // Ohne seitenId in den Abhängigkeiten behielte der Editor beim
    // Seitenwechsel den alten Inhalt.
    [seitenId],
  );

  // Überschriften brauchen eine Sprungmarke, damit das Inhaltsverzeichnis
  // sie anspringen kann. Die IDs werden nach jedem Rendern nachgetragen —
  // die Ankerlogik selbst liegt im Backend, hier nur die Zuordnung.
  useEffect(() => {
    if (!editor) return;
    const nachtragen = () => {
      const wurzel = editor.view.dom;
      const vergeben = new Map<string, number>();
      wurzel.querySelectorAll("h1, h2, h3").forEach((el) => {
        const text = (el.textContent || "").trim();
        if (!text) return;
        let anker = text
          .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue")
          .replace(/Ä/g, "ae").replace(/Ö/g, "oe").replace(/Ü/g, "ue")
          .replace(/ß/g, "ss")
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "");
        if (!anker) anker = "abschnitt";
        const n = (vergeben.get(anker) ?? 0) + 1;
        vergeben.set(anker, n);
        el.id = n > 1 ? `${anker}-${n}` : anker;
      });
    };
    nachtragen();
    editor.on("update", nachtragen);
    return () => {
      editor.off("update", nachtragen);
    };
  }, [editor]);

  if (!editor) return null;

  async function bildWaehlen(datei: File | undefined) {
    if (!datei || !editor) return;
    setLaedtBild(true);
    try {
      const { url } = await bildHochladen(campaignId, datei);
      editor.chain().focus().setImage({ src: url }).run();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Bild konnte nicht hochgeladen werden");
    } finally {
      setLaedtBild(false);
      if (dateiRef.current) dateiRef.current.value = "";
    }
  }

  function verweisEinfuegen(attrs: VerweisAttribute) {
    editor?.chain().focus().verweisEinfuegen(attrs).run();
  }

  return (
    <>
      {!nurLesen && (
        <Werkzeugleiste
          editor={editor}
          onVerweis={() => setWaehlerOffen(true)}
          onBild={() => dateiRef.current?.click()}
          laedtBild={laedtBild}
        />
      )}

      <input
        ref={dateiRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        style={{ display: "none" }}
        onChange={(e) => bildWaehlen(e.target.files?.[0])}
      />

      <div className="wk-editor">
        <EditorContent editor={editor} />
      </div>

      <VerweisWaehler
        campaignId={campaignId}
        offen={waehlerOffen}
        onWaehlen={verweisEinfuegen}
        onSchliessen={() => setWaehlerOffen(false)}
      />
    </>
  );
}
