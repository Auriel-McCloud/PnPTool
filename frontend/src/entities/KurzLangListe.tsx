import { useState } from "react";
import type { KurzLangEintrag } from "./api";
import { Fenster } from "../shell/Fenster";
import "./pc-detail.css"; // .ziel-* Stile und .pcd-* Stile

/**
 * Liste von Kurz-Lang-Einträgen (Ziele, Ressourcen) mit Editor-Popup.
 *
 * Bewusst eine eigene Komponente: Fraktions-Ziele und -Ressourcen haben
 * exakt dieselbe Bedienlogik (Liste + "Neu"-Knopf + Popup mit Kurz- und
 * Langbeschreibung). Statt das zweimal zu schreiben, kapselt diese
 * Komponente beides.
 *
 * Kontrolliert: die Liste selbst lebt im Aufrufer, der sie beim Speichern
 * an seinen eigenen API-Pfad weitergibt. Die Komponente hält nur den
 * Zustand ihres Editors (offen/geschlossen, Inhalt).
 */
interface KurzLangListeProps {
  eintraege: KurzLangEintrag[];
  /** Wird nach jedem Speichern/Entfernen mit der neuen Liste gerufen. */
  onAendern: (neue: KurzLangEintrag[]) => void;
  /** Einleitender Hinweis über der Liste. */
  hinweis: string;
  /** Text des "Neu"-Knopfs. */
  neuText: string;
  /** Text, wenn die Liste leer ist. */
  leerText: string;
  /** Einzahl für Fenstertitel: "Ziel", "Ressource". */
  einzahl: string;
  /** Kurzbeschreibung-Platzhalter. */
  titelPlatzhalter: string;
  /** Langbeschreibung-Platzhalter. */
  beschreibungPlatzhalter: string;
  /** Streuungs-Kennung für das Editor-Fenster. */
  kennung: string;
  speichert: boolean;
}

export function KurzLangListe({
  eintraege,
  onAendern,
  hinweis,
  neuText,
  leerText,
  einzahl,
  titelPlatzhalter,
  beschreibungPlatzhalter,
  kennung,
  speichert,
}: KurzLangListeProps) {
  const [editor, setEditor] = useState<{ index: number | null; titel: string; beschreibung: string } | null>(null);

  function oeffnen(index: number | null) {
    if (index === null) {
      setEditor({ index: null, titel: "", beschreibung: "" });
    } else {
      const e = eintraege[index];
      setEditor({ index, titel: e.titel, beschreibung: e.beschreibung });
    }
  }

  function speichern() {
    if (!editor) return;
    const eintrag: KurzLangEintrag = {
      titel: editor.titel.trim(),
      beschreibung: editor.beschreibung,
    };
    const neue =
      editor.index === null
        ? [...eintraege, eintrag]
        : eintraege.map((e, i) => (i === editor.index ? eintrag : e));
    setEditor(null);
    onAendern(neue);
  }

  function entfernen(index: number) {
    onAendern(eintraege.filter((_, i) => i !== index));
  }

  return (
    <div className="pcd-editor-bereich">
      <p className="pcd-hinweis">{hinweis}</p>

      <div className="ziel-liste">
        {eintraege.length === 0 && (
          <p style={{ color: "var(--text-leise)", fontStyle: "italic" }}>{leerText}</p>
        )}

        {eintraege.map((e, i) => (
          <button
            key={i}
            type="button"
            className="ziel-eintrag"
            onClick={() => oeffnen(i)}
            title="Bearbeiten"
          >
            <span className="ziel-titel">{e.titel.trim() || `Unbenannte ${einzahl.toLowerCase()}`}</span>
            <span
              className="ziel-wegwerfen"
              title="Entfernen"
              onClick={(ev) => {
                ev.stopPropagation();
                entfernen(i);
              }}
            >
              ✕
            </span>
          </button>
        ))}

        <button type="button" className="ziel-neu" onClick={() => oeffnen(null)}>
          {neuText}
        </button>
      </div>

      {editor && (
        <Fenster
          offen
          titel={editor.index === null ? `Neue ${einzahl}` : `${einzahl} bearbeiten`}
          unterzeile={editor.index === null ? "Kurzbeschreibung und, bei Bedarf, Ausführung" : undefined}
          kennung={`${kennung}:${editor.index ?? "neu"}`}
          ton="var(--bereich-fraktionen)"
          onSchliessen={() => setEditor(null)}
        >
          <div className="pcd-editor-bereich" style={{ padding: 8 }}>
            <div>
              <label className="pcd-label">Kurzbeschreibung</label>
              <input
                type="text"
                className="ziel-input"
                placeholder={titelPlatzhalter}
                value={editor.titel}
                autoFocus
                onChange={(e) => setEditor({ ...editor, titel: e.target.value })}
              />
            </div>

            <div>
              <label className="pcd-label">Beschreibung</label>
              <textarea
                className="ziel-textarea"
                placeholder={beschreibungPlatzhalter}
                value={editor.beschreibung}
                onChange={(e) => setEditor({ ...editor, beschreibung: e.target.value })}
              />
            </div>

            <div className="ziel-editor-aktionen">
              <button type="button" className="pcd-abbrechen" onClick={() => setEditor(null)}>
                Abbrechen
              </button>
              <button type="button" className="pcd-speichern" onClick={speichern} disabled={speichert}>
                {speichert ? "Speichert…" : "Speichern"}
              </button>
            </div>
          </div>
        </Fenster>
      )}
    </div>
  );
}
