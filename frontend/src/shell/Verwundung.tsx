import { useEffect, useRef, useState } from "react";
import { bogenApi, type BogenUebersicht } from "../traits/bogenApi";
import "./verwundung.css";

/**
 * Der Zustand des eigenen Charakters, regelmässig nachgeholt.
 *
 * Gleiche Bauart wie `useKampf`: nachladen statt Live-Verbindung, und nur
 * solange die Seite sichtbar ist. Nötig, weil auch die Spielleitung Schaden
 * einträgt — ohne Nachfragen bliebe der Bildschirm dann heil, während die
 * Figur längst blutet.
 */
export function useZustand(campaignId: string | null, personId: string | null, takt = 5000) {
  const [zustand, setZustand] = useState<BogenUebersicht | null>(null);
  const laufend = useRef(false);

  useEffect(() => {
    if (!campaignId || !personId) return;
    let abgemeldet = false;

    async function holen() {
      if (laufend.current || document.hidden) return;
      laufend.current = true;
      try {
        const bogen = await bogenApi.laden(campaignId!, personId!);
        if (!abgemeldet) setZustand(bogen.uebersicht);
      } catch {
        // Netz weg — beim nächsten Takt wieder
      } finally {
        laufend.current = false;
      }
    }

    void holen();
    const uhr = setInterval(holen, takt);
    document.addEventListener("visibilitychange", holen);
    return () => {
      abgemeldet = true;
      clearInterval(uhr);
      document.removeEventListener("visibilitychange", holen);
    };
  }, [campaignId, personId, takt]);

  return zustand;
}

/**
 * Das Gerät blutet mit.
 *
 * Von unten steigt ein dunkles Rot auf, je mehr Gesundheit fehlt — nicht
 * gleichmässig über den Schirm, sondern als Schein vom unteren Rand her.
 * Bleiben nur noch zwei Kästchen, fängt es an zu pulsen. Marks Bild.
 *
 * Liegt über allem und nimmt keine Eingaben an (`pointer-events: none`);
 * wer die Bewegung nicht will, bekommt sie über `prefers-reduced-motion`
 * ohnehin nicht — das gilt global in `index.css`.
 */
export function Verwundung({ zustand }: { zustand: BogenUebersicht | null }) {
  if (!zustand || zustand.gesundheitMax <= 0) return null;

  const uebrig = Math.max(0, zustand.gesundheitMax - zustand.gesundheitSchaden);
  const anteil = 1 - uebrig / zustand.gesundheitMax;
  if (anteil <= 0) return null;

  // Zwei Kästchen sind der Punkt, an dem es ernst wird — ab da pulst es.
  const kritisch = uebrig > 0 && uebrig <= 2;

  return (
    <div
      className="vw-schleier"
      data-kritisch={kritisch}
      aria-hidden="true"
      style={{ "--vw-anteil": anteil.toFixed(3) } as React.CSSProperties}
    />
  );
}
