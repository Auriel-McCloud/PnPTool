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
 * Eingebettet in den normalen Textfluss (nicht schwebend/fixiert) — sitzt
 * im Fertigkeiten-Popup direkt über der Sphären-/Glaubensdomänen-Sektion,
 * dort wo die Warnungen inhaltlich hingehören. Rein informativ: lässt sich
 * wegklicken, blockiert nichts (Mark: "nur anzeigen, nie blockieren").
 * Der Aufrufer entscheidet, WANN das Widget überhaupt gemountet wird (Mark:
 * nicht von Anfang an, frühestens ab der Hälfte der vergebenen Punkte) —
 * diese Komponente selbst kennt keine Schwelle.
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

/** Cyberware-Drohnenauge — für Chrom/NeuroWeaver. Hypercube-Wireframe:
 * äußerer und innerer Rahmen rotieren gegenläufig, die Speichen dazwischen
 * schieben sich rhythmisch (Tesseract-Schatten-Optik). */
function KonstruktIcon() {
  return (
    <svg viewBox="0 0 48 48" width="36" height="36" className="as-svg">
      <g className="as-hyper-links">
        <line x1="24" y1="6" x2="24" y2="15" stroke="currentColor" strokeWidth="1" opacity="0.6" />
        <line x1="42" y1="24" x2="33" y2="24" stroke="currentColor" strokeWidth="1" opacity="0.6" />
        <line x1="24" y1="42" x2="24" y2="33" stroke="currentColor" strokeWidth="1" opacity="0.6" />
        <line x1="6" y1="24" x2="15" y2="24" stroke="currentColor" strokeWidth="1" opacity="0.6" />
      </g>
      <polygon points="24,6 42,24 24,42 6,24" fill="none" stroke="currentColor" strokeWidth="1.6" className="as-hyper-aussen" />
      <polygon points="24,15 33,24 24,33 15,24" fill="none" stroke="currentColor" strokeWidth="1.6" className="as-hyper-innen" />
      <circle cx="24" cy="24" r="2.5" fill="currentColor" className="as-puls" />
    </svg>
  );
}

/** Magisches Sigill — für Magier/Häretiker. Dieselbe Hypercube-Bewegung,
 * nur mit Dreiecksformen statt Quadraten (arkaner statt technisch). */
function SigillIcon() {
  return (
    <svg viewBox="0 0 48 48" width="36" height="36" className="as-svg">
      <g className="as-hyper-links">
        <line x1="24" y1="4" x2="24" y2="13" stroke="currentColor" strokeWidth="1" opacity="0.6" />
        <line x1="41" y1="34" x2="33.5" y2="29.5" stroke="currentColor" strokeWidth="1" opacity="0.6" />
        <line x1="7" y1="34" x2="14.5" y2="29.5" stroke="currentColor" strokeWidth="1" opacity="0.6" />
      </g>
      <polygon points="24,4 41,34 7,34" fill="none" stroke="currentColor" strokeWidth="1.6" className="as-hyper-aussen" />
      <polygon points="24,13 33.5,29.5 14.5,29.5" fill="none" stroke="currentColor" strokeWidth="1.6" className="as-hyper-innen" />
      <circle cx="24" cy="26" r="2.5" fill="currentColor" className="as-puls" />
    </svg>
  );
}
