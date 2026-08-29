import { useEffect, useRef, type ReactNode } from "react";
import "./fenster.css";

/**
 * Zahl aus einer Zeichenkette — dieselbe Kennung ergibt immer dieselbe Zahl.
 * Damit steht ein Fenster stets an seinem Platz, statt bei jedem Öffnen
 * umherzuspringen; verschiedene Fenster landen trotzdem an verschiedenen
 * Stellen (Marks Wunsch: "nicht zwingend immer in der Mitte").
 */
function streuung(kennung: string): { links: number; oben: number } {
  let h = 0;
  for (let i = 0; i < kennung.length; i++) {
    h = (h * 31 + kennung.charCodeAt(i)) | 0;
  }
  const a = Math.abs(h);
  // 36–64 %: deutlich aus der Mitte gerückt, aber nie am Rand klebend
  return { links: 36 + (a % 29), oben: 38 + ((a >> 8) % 25) };
}

/**
 * Fokussiertes Fenster für die Detailansicht eines einzelnen Dings.
 *
 * Löst das Inline-Aufklappen ab (siehe docs/ui-konzept.md). Wichtig fürs
 * Leitprinzip "nie scrollen": lange Inhalte gehören hierher — im Fenster ist
 * Scrollen ausdrücklich erlaubt, auf den Übersichtsseiten nicht.
 *
 * Am Handy füllt es den Bildschirm und bekommt oben mittig einen Griff.
 */
export function Fenster({
  offen,
  titel,
  unterzeile,
  kennung,
  ton,
  onSchliessen,
  children,
}: {
  offen: boolean;
  titel: string;
  unterzeile?: ReactNode;
  /** Bestimmt die Lage; gleiche Kennung = gleiche Stelle. */
  kennung: string;
  /** Rahmenfarbe; ohne Angabe die Leitfarbe des Bereichs. */
  ton?: string;
  onSchliessen: () => void;
  children: ReactNode;
}) {
  const rahmenRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!offen) return;
    function beiTaste(e: KeyboardEvent) {
      if (e.key === "Escape") onSchliessen();
    }
    document.addEventListener("keydown", beiTaste);
    // Der Hintergrund darf nicht mitscrollen, während das Fenster offen ist
    const vorher = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    rahmenRef.current?.focus();
    return () => {
      document.removeEventListener("keydown", beiTaste);
      document.body.style.overflow = vorher;
    };
  }, [offen, onSchliessen]);

  if (!offen) return null;

  const { links, oben } = streuung(kennung);

  return (
    <div className="fn-hintergrund" onClick={onSchliessen}>
      <div
        className="fn-fenster"
        ref={rahmenRef}
        role="dialog"
        aria-modal="true"
        aria-label={titel}
        tabIndex={-1}
        style={
          {
            "--fn-links": `${links}%`,
            "--fn-oben": `${oben}%`,
            ...(ton ? { "--fn-ton": ton } : {}),
          } as React.CSSProperties
        }
        /* sonst schlösse jeder Klick im Fenster es gleich wieder */
        onClick={(e) => e.stopPropagation()}
      >
        <div className="fn-griff" aria-hidden="true" />

        <header className="fn-kopf">
          <div className="fn-kopf-text">
            <h2 className="fn-titel">{titel}</h2>
            {unterzeile && <div className="fn-unterzeile">{unterzeile}</div>}
          </div>
          <button type="button" className="fn-schliessen" onClick={onSchliessen} aria-label="Schließen">
            ✕
          </button>
        </header>

        {/* Die einzige Stelle, an der bewusst gescrollt werden darf */}
        <div className="fn-inhalt">{children}</div>
      </div>
    </div>
  );
}
