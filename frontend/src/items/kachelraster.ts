import { useLayoutEffect, useRef, useState } from "react";

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
 * Geht die Höhe nur zurück, weil am Handy die Bildschirmtastatur aufklappt?
 *
 * Bug (Mark, 19.11.2026): Am Handy schloss sich das KI-Bild-Fenster eines
 * Gegenstands, sobald man in den Prompt tippte. Die Tastatur verkleinert
 * die Seite (`interactive-widget=resizes-content` in index.html), das
 * Raster misst neu, es passen weniger Kacheln auf die Seite — und die
 * Kachel des offenen Gegenstands fällt von der Seite. Mit ihr verschwinden
 * ihr Fenster und alle Fenster darüber, denn die hängen an der Kachel.
 *
 * Erkennung: gleiche Breite, weniger Höhe, und der Fokus steht in einem
 * Eingabefeld. Dann bleibt die bisherige Kachelzahl stehen; klappt die
 * Tastatur wieder zu, kehrt die alte Höhe zurück und es wird normal
 * gemessen. Drehen (Breite ändert sich) misst weiterhin sofort.
 */
export function istTastaturSchrumpfung(
  vorher: { breite: number; hoehe: number } | null,
  breite: number,
  hoehe: number,
): boolean {
  if (!vorher || Math.abs(breite - vorher.breite) >= 1 || hoehe >= vorher.hoehe) return false;
  const el = document.activeElement as HTMLElement | null;
  if (!el) return false;
  if (el.isContentEditable || el.tagName === "TEXTAREA") return true;
  if (el.tagName !== "INPUT") return false;
  const ohneTastatur = ["button", "checkbox", "radio", "range", "file", "submit", "reset", "color", "image", "hidden"];
  return !ohneTastatur.includes((el as HTMLInputElement).type);
}

/**
 * Zählt aus, wie viele Kacheln in die vorhandene Fläche passen.
 *
 * Rechnet bei jeder Größenänderung neu, damit Hoch- und Querformat am Tablet
 * gleichermaßen aufgehen.
 */
export function useProSeite(ref: React.RefObject<HTMLDivElement | null>) {
  const [proSeite, setProSeite] = useState(12);
  const gemessen = useRef<{ breite: number; hoehe: number } | null>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const messen = () => {
      const { width, height } = el.getBoundingClientRect();
      if (istTastaturSchrumpfung(gemessen.current, width, height)) return;
      gemessen.current = { breite: width, hoehe: height };
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
