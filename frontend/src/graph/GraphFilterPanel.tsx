import { useEffect, useRef, useState } from "react";
import "./graph-filter.css";

/**
 * Dropdown über dem Graphen: welche Objekt-/Kantentypen angezeigt werden.
 *
 * Rein clientseitiger Anzeige-Filter (24.10.2026, Marks Wunsch) — ändert
 * nichts an den Daten, blendet nur im Cytoscape-Canvas aus. Die Auswahl
 * wird vom Aufrufer in localStorage gemerkt (siehe CampaignGraphView), damit
 * sie über einen Neuladen hinweg bestehen bleibt.
 */

export interface KnotenFilterOption {
  schluessel: string;
  label: string;
  anzahl: number;
}

export interface KantenFilterOption {
  typ: string;
  anzahl: number;
}

export function GraphFilterPanel({
  knotenOptionen,
  kantenOptionen,
  versteckteKnoten,
  versteckteKanten,
  onKnotenUmschalten,
  onKanteUmschalten,
  onAlleAnzeigen,
  onNormalisieren,
}: {
  knotenOptionen: KnotenFilterOption[];
  kantenOptionen: KantenFilterOption[];
  versteckteKnoten: Set<string>;
  versteckteKanten: Set<string>;
  onKnotenUmschalten: (schluessel: string) => void;
  onKanteUmschalten: (typ: string) => void;
  onAlleAnzeigen: () => void;
  onNormalisieren: () => void;
}) {
  const [offen, setOffen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  // Klick ausserhalb schliesst das Panel, wie das Fenster/die anderen
  // Dropdowns im Tool.
  useEffect(() => {
    if (!offen) return;
    function beiKlick(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOffen(false);
    }
    document.addEventListener("mousedown", beiKlick);
    return () => document.removeEventListener("mousedown", beiKlick);
  }, [offen]);

  const anzahlVersteckt = versteckteKnoten.size + versteckteKanten.size;

  return (
    <div className="gf-box" ref={boxRef}>
      <button type="button" className="gf-knopf" onClick={() => setOffen((o) => !o)}>
        ⚙ Filter{anzahlVersteckt > 0 ? ` (${anzahlVersteckt} ausgeblendet)` : ""}
      </button>
      {offen && (
        <div className="gf-panel">
          <div className="gf-kopf">
            <strong>Im Graphen anzeigen</strong>
            <button type="button" className="gf-alle" onClick={onAlleAnzeigen} disabled={anzahlVersteckt === 0}>
              Alle anzeigen
            </button>
          </div>

          {knotenOptionen.length > 0 && (
            <div className="gf-gruppe">
              <div className="gf-gruppentitel">Objekttypen</div>
              {knotenOptionen.map((o) => (
                <label key={o.schluessel} className="gf-zeile">
                  <input
                    type="checkbox"
                    checked={!versteckteKnoten.has(o.schluessel)}
                    onChange={() => onKnotenUmschalten(o.schluessel)}
                  />
                  <span>{o.label}</span>
                  <span className="gf-anzahl">{o.anzahl}</span>
                </label>
              ))}
            </div>
          )}

          {kantenOptionen.length > 0 && (
            <div className="gf-gruppe">
              <div className="gf-gruppentitel">Kantentypen</div>
              {kantenOptionen.map((o) => (
                <label key={o.typ} className="gf-zeile">
                  <input
                    type="checkbox"
                    checked={!versteckteKanten.has(o.typ)}
                    onChange={() => onKanteUmschalten(o.typ)}
                  />
                  <span>{o.typ}</span>
                  <span className="gf-anzahl">{o.anzahl}</span>
                </label>
              ))}
              <button type="button" className="gf-normalisieren" onClick={onNormalisieren}>
                ✨ Kantentypen normalisieren…
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
