/**
 * Durchsuchbare Personen-Auswahl für Dropdowns mit potenziell vielen
 * Einträgen (07.10.2026, Mark: "bei NPCs bräuchte ich ein Suchfeld").
 *
 * Ersetzt ein einfaches <select> durch Textfeld + Treffer-Liste, meldet die
 * gewählte ID über onWaehlen — wie ein <select>, nur mit Filter statt langem
 * Scrollen. Bewusst lokal gebaut statt ein <input list>/<datalist>: damit
 * bleibt die Name->ID-Zuordnung eindeutig per Klick, auch wenn zwei
 * Einträge zufällig denselben Namen tragen (Datalist müsste über den
 * getippten Text raten).
 */
import { useEffect, useRef, useState } from "react";
import type { Person } from "../entities/api";

export function PersonSuchAuswahl({
  personen,
  wert,
  onWaehlen,
  platzhalter,
}: {
  personen: Person[];
  wert: string;
  onWaehlen: (id: string) => void;
  platzhalter: string;
}) {
  const gewaehlt = personen.find((p) => p.id === wert);
  const [suche, setSuche] = useState("");
  const [offen, setOffen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Textfeld zeigt den Namen der Auswahl, solange nicht gerade gesucht wird.
  const anzeigeText = offen ? suche : (gewaehlt?.name ?? "");

  const treffer = personen.filter((p) =>
    p.name.toLowerCase().includes(suche.trim().toLowerCase())
  );

  // Klick außerhalb schließt die Treffer-Liste — kein eigener Hook nötig,
  // das hier ist ein kleines Inline-Dropdown, kein Vollbild-Popup.
  useEffect(() => {
    if (!offen) return;
    function aufKlick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOffen(false);
        setSuche("");
      }
    }
    document.addEventListener("mousedown", aufKlick);
    return () => document.removeEventListener("mousedown", aufKlick);
  }, [offen]);

  return (
    <div className="kontakte-gm-suchauswahl" ref={wrapperRef}>
      <input
        type="text"
        className="kontakte-gm-suchauswahl-feld"
        placeholder={platzhalter}
        value={anzeigeText}
        onFocus={() => {
          setOffen(true);
          setSuche("");
        }}
        onChange={(e) => setSuche(e.target.value)}
      />
      {wert && !offen && (
        <button
          type="button"
          className="kontakte-gm-suchauswahl-loeschen"
          title="Auswahl zurücksetzen"
          onClick={() => onWaehlen("")}
        >
          ✕
        </button>
      )}
      {offen && (
        <ul className="kontakte-gm-suchauswahl-liste">
          {treffer.length === 0 && (
            <li className="kontakte-gm-suchauswahl-leer">Keine Treffer</li>
          )}
          {treffer.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                onClick={() => {
                  onWaehlen(p.id);
                  setOffen(false);
                  setSuche("");
                }}
              >
                {p.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
