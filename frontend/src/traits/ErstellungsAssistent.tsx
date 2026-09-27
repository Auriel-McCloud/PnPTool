import { useEffect, useMemo, useRef, useState } from "react";
import { berate, type BeraterHinweis } from "./berater";
import "./assistent.css";

/**
 * Karl-Klammer-artiger Erstellungsassistent (27.09.2026, Marks Idee).
 *
 * Zwei Flavors passend zum Weg: ein Cyberware-Konstrukt für Chrom/
 * NeuroWeaver, ein magisches Sigill für Magier/Häretiker — dieselbe Wahl
 * wie magieBegriffe.ts, nur visuell statt textlich. Reagiert live auf
 * berater.ts (kein KI-Aufruf, siehe dortiger Docstring).
 *
 * Rein informativ: erscheint unten rechts, lässt sich wegklicken, blockiert
 * nichts (Mark: "nur anzeigen, nie blockieren").
 */
export function ErstellungsAssistent({
  werte,
  weg,
  attributKategorien,
}: {
  werte: Record<string, number>;
  weg: string;
  attributKategorien?: { id: string; attribute: string[] }[];
}) {
  const hinweise = useMemo(() => berate(werte, weg, attributKategorien), [werte, weg, attributKategorien]);
  const magisch = weg === "MAGIER" || weg === "HAERETIKER";
  const [ausgeblendet, setAusgeblendet] = useState<Set<string>>(new Set());
  const [aktivIndex, setAktivIndex] = useState(0);

  const sichtbar = hinweise.filter((h) => !ausgeblendet.has(h.code));

  // Neue Warnung aufgetaucht → wieder von vorn zeigen, nicht mitten in einer
  // Liste hängenbleiben, die es nicht mehr gibt.
  const anzahlRef = useRef(sichtbar.length);
  useEffect(() => {
    if (sichtbar.length !== anzahlRef.current) {
      setAktivIndex(0);
      anzahlRef.current = sichtbar.length;
    }
  }, [sichtbar.length]);

  if (sichtbar.length === 0) return null;

  const aktuell: BeraterHinweis = sichtbar[Math.min(aktivIndex, sichtbar.length - 1)];

  function weiter() {
    setAktivIndex((i) => (i + 1) % sichtbar.length);
  }

  function wegklicken() {
    setAusgeblendet((alt) => new Set(alt).add(aktuell.code));
  }

  return (
    <div className={`as-box${magisch ? " as-box-magisch" : " as-box-chrom"}`} role="status">
      <div className="as-figur" aria-hidden="true">
        {magisch ? <SigillIcon /> : <KonstruktIcon />}
      </div>
      <div className="as-blase">
        <p className="as-text">{aktuell.text}</p>
        <div className="as-fuss">
          {sichtbar.length > 1 && (
            <button type="button" className="as-weiter" onClick={weiter}>
              Noch was? ({aktivIndex + 1}/{sichtbar.length})
            </button>
          )}
          <button type="button" className="as-schliessen" onClick={wegklicken} title="Diesen Hinweis nicht mehr zeigen">
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}

/** Cyberware-Drohnenauge — für Chrom/NeuroWeaver. */
function KonstruktIcon() {
  return (
    <svg viewBox="0 0 48 48" width="40" height="40" className="as-svg">
      <circle cx="24" cy="24" r="20" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="24" cy="24" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="24" cy="24" r="3" fill="currentColor" className="as-puls" />
      <line x1="24" y1="4" x2="24" y2="10" stroke="currentColor" strokeWidth="2" />
      <line x1="24" y1="38" x2="24" y2="44" stroke="currentColor" strokeWidth="2" />
      <line x1="4" y1="24" x2="10" y2="24" stroke="currentColor" strokeWidth="2" />
      <line x1="38" y1="24" x2="44" y2="24" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

/** Magisches Sigill — für Magier/Häretiker. */
function SigillIcon() {
  return (
    <svg viewBox="0 0 48 48" width="40" height="40" className="as-svg">
      <polygon points="24,4 42,36 6,36" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="24" cy="26" r="14" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="24" cy="26" r="3" fill="currentColor" className="as-puls" />
    </svg>
  );
}
