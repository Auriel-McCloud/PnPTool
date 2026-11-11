import type { Person } from "./api";
import { anzeigeName } from "./api";
import "./pc-kacheln.css";
import "./nebenfiguren.css";
import { vorschau } from "../shell/vorschau";

/**
 * Kachel-Übersicht für Nebenfiguren (10.11.2026).
 *
 * Bewusst ohne LP/WK — eine Nebenfigur hat keinen Bogen. Stattdessen Rasse,
 * Alter und die Persönlichkeit als Stichwort.
 */
export function NebenfigurKacheln({
  figuren,
  onKlick,
  leertext,
}: {
  figuren: Person[];
  onKlick: (person: Person) => void;
  leertext?: string;
}) {
  if (figuren.length === 0) {
    return <p className="pc-kacheln-leer">{leertext ?? "Noch keine Nebenfiguren angelegt."}</p>;
  }
  return (
    <div className="pc-kacheln-raster">
      {figuren.map((p) => {
        const kopf = [p.rasse, p.alter ? `${p.alter} J.` : ""].filter(Boolean).join(" · ");
        return (
          <div key={p.id} className="pc-kachel nf-kachel" onClick={() => onKlick(p)}>
            <div className="pc-kachel-bild-bereich">
              {p.bildUrl ? (
                <img src={vorschau(p.bildUrl)} loading="lazy" decoding="async" alt={p.name} className="pc-kachel-bild" />
              ) : (
                <div className="pc-kachel-bild-leer">○</div>
              )}
            </div>
            <div className="pc-kachel-info">
              <div className="pc-kachel-name">{anzeigeName(p.name, p.alias)}</div>
              {kopf && <div className="nf-kachel-zeile">{kopf}</div>}
              {p.istBlankoKontakt ? (
                <span className="nf-persoenlichkeit" title="Leerer Kontakt-Platz — der Spieler beschreibt ihn im Messenger">
                  Platzhalter
                </span>
              ) : (
                p.persoenlichkeit && <span className="nf-persoenlichkeit">{p.persoenlichkeit}</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
