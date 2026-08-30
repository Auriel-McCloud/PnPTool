import { useLayoutEffect, useState } from "react";

/**
 * Ausmessung des Kachelrasters — von der Spielleitung *und* der Spielersicht
 * genutzt, damit beide dieselben Kacheln in derselben Größe zeigen.
 *
 * Kern des Leitprinzips "nie scrollen" (docs/ui-konzept.md): statt die Liste
 * überlaufen zu lassen, wird die tatsächlich vorhandene Fläche gemessen und
 * der Rest geblättert.
 */

/** Muss zu den Werten in gegenstaende.css passen. */
export const KACHEL_BREITE = 148;
export const KACHEL_HOEHE = 168;
export const ABSTAND = 10;

/** Die Maße als CSS-Variablen, wie sie das Raster erwartet. */
export const KACHEL_STIL = {
  "--gg-kachel-breite": `${KACHEL_BREITE}px`,
  "--gg-kachel-hoehe": `${KACHEL_HOEHE}px`,
  "--gg-abstand": `${ABSTAND}px`,
} as React.CSSProperties;

/**
 * Zählt aus, wie viele Kacheln in die vorhandene Fläche passen.
 *
 * Rechnet bei jeder Größenänderung neu, damit Hoch- und Querformat am Tablet
 * gleichermaßen aufgehen.
 */
export function useProSeite(ref: React.RefObject<HTMLDivElement | null>) {
  const [proSeite, setProSeite] = useState(12);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const messen = () => {
      const { width, height } = el.getBoundingClientRect();
      const spalten = Math.max(1, Math.floor((width + ABSTAND) / (KACHEL_BREITE + ABSTAND)));
      const zeilen = Math.max(1, Math.floor((height + ABSTAND) / (KACHEL_HOEHE + ABSTAND)));
      setProSeite(spalten * zeilen);
    };
    messen();
    const beobachter = new ResizeObserver(messen);
    beobachter.observe(el);
    return () => beobachter.disconnect();
  }, [ref]);

  return proSeite;
}
