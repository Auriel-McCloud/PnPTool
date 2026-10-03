import { useEffect, useState } from "react";

/**
 * Lesegrößen-Zoom für Rich-Text-Boxen (Beschreibung/Notizen).
 *
 * Mark, 03.10.2026: "ein Zoom-Knopf in den Beschreibungsboxen, der die
 * Schriftgröße erhöht" — mehrstufig mit +/-, merkt sich global.
 *
 * Gilt global über eine CSS-Variable auf document.documentElement (gleiches
 * Muster wie theme/theme.ts) statt über React-Context: so bleiben mehrere
 * gleichzeitig offene Beschreibungs-Popups synchron, ohne dass ein
 * gemeinsamer Provider um die ganze App gelegt werden muss. `.ProseMirror`
 * selbst (richtext.css) liest die Variable — RichTextEditor UND
 * RichTextView treffen also automatisch beide, ein Klick irgendwo reicht.
 */
export const ZOOM_STUFEN = [100, 115, 130, 150, 175] as const;
type ZoomStufe = (typeof ZOOM_STUFEN)[number];

const SPEICHER_SCHLUESSEL = "pnptool.textzoom";
const EREIGNIS = "pnptool-textzoom";

function istStufe(wert: number): wert is ZoomStufe {
  return (ZOOM_STUFEN as readonly number[]).includes(wert);
}

export function zoomLesen(): ZoomStufe {
  try {
    const gespeichert = Number(localStorage.getItem(SPEICHER_SCHLUESSEL));
    if (istStufe(gespeichert)) return gespeichert;
  } catch {
    /* Privater Modus o.ae. — dann gilt der Standard. */
  }
  return 100;
}

export function zoomSetzen(wert: number) {
  const stufe = istStufe(wert) ? wert : 100;
  document.documentElement.style.setProperty("--rt-zoom", String(stufe / 100));
  try {
    localStorage.setItem(SPEICHER_SCHLUESSEL, String(stufe));
  } catch {
    // Privater Modus o.ae. — gilt dann nur fuer diese Sitzung.
  }
  window.dispatchEvent(new CustomEvent(EREIGNIS, { detail: stufe }));
}

/** Einmal frueh beim Start anwenden (main.tsx), analog zu themeSetzen —
 * sonst blitzt beim Laden kurz die 100%-Groesse auf, bevor der erste
 * TextZoomKnopf mountet. */
export function zoomAnwenden() {
  zoomSetzen(zoomLesen());
}

/** Hook fuer den TextZoomKnopf. Mehrere gleichzeitig gemountete Knoepfe
 * (z.B. zwei offene Popups) hoeren auf dasselbe Ereignis und bleiben so
 * synchron, ohne einen gemeinsamen Zustand hochreichen zu muessen. */
export function useTextZoom() {
  const [stufe, setStufe] = useState<ZoomStufe>(() => zoomLesen());

  useEffect(() => {
    const aktualisieren = (e: Event) => setStufe((e as CustomEvent<ZoomStufe>).detail);
    window.addEventListener(EREIGNIS, aktualisieren);
    return () => window.removeEventListener(EREIGNIS, aktualisieren);
  }, []);

  const index = ZOOM_STUFEN.indexOf(stufe);

  return {
    stufe,
    istMin: index <= 0,
    istMax: index >= ZOOM_STUFEN.length - 1,
    vergroessern: () => zoomSetzen(ZOOM_STUFEN[Math.min(index + 1, ZOOM_STUFEN.length - 1)]),
    verkleinern: () => zoomSetzen(ZOOM_STUFEN[Math.max(index - 1, 0)]),
  };
}
