import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { letzteTippPosition } from "./tippPosition";
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
  // Verschiebung von der Tipp-Stelle zur endgueltigen Fenstermitte. Erst nach
  // dem Aufbau messbar, denn vorher steht die Fenstergroesse nicht fest.
  const [herkunft, setHerkunft] = useState<{ x: number; y: number } | null>(null);
  // Die Animation startet erst, wenn gemessen wurde — sonst liefe sie im
  // ersten Bild noch mit der Vorgabe 0/0 los und der Sprung zur Tipp-Stelle
  // waere als Ruckler sichtbar. useLayoutEffect wird vor dem Zeichnen
  // ausgefuehrt, das Nachziehen bleibt deshalb unsichtbar.
  const [gemessen, setGemessen] = useState(false);

  useLayoutEffect(() => {
    if (!offen) {
      setGemessen(false);
      setHerkunft(null);
      return;
    }
    const tipp = letzteTippPosition();
    const rahmen = rahmenRef.current;
    if (tipp && rahmen) {
      const r = rahmen.getBoundingClientRect();
      setHerkunft({ x: tipp.x - (r.left + r.width / 2), y: tipp.y - (r.top + r.height / 2) });
    } else {
      setHerkunft(null);
    }
    setGemessen(true);
  }, [offen, kennung]);

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
        className={gemessen ? "fn-fenster fn-fenster-auf" : "fn-fenster"}
        ref={rahmenRef}
        role="dialog"
        aria-modal="true"
        aria-label={titel}
        tabIndex={-1}
        style={
          {
            "--fn-links": `${links}%`,
            "--fn-oben": `${oben}%`,
            // Solange ungemessen: aus dem Stand aufziehen (0/0).
            "--fn-von-x": `${herkunft?.x ?? 0}px`,
            "--fn-von-y": `${herkunft?.y ?? 0}px`,
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
