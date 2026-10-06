import { useCallback, useRef } from "react";

/**
 * Klick-Handler-Paar für ein Hintergrund-/Überlagerungs-Element, das ein
 * Popup schliesst — aber nur, wenn der Klick dort auch BEGONNEN hat, nicht
 * nur dort endet.
 *
 * Bug (Mark, 06.10.2026): Markiert man Text im Popup (z.B. eine lange
 * Beschreibung) und zieht die Maus beim Loslassen versehentlich über den
 * Rand hinaus, endet der Klick auf dem Hintergrund. Ein schlichtes
 * `onClick={onSchliessen}` auf dem Hintergrund interpretiert das als
 * "daneben geklickt" und schliesst das Popup mitten in der Textauswahl.
 *
 * Grund: Beginnen Mousedown und Mouseup auf unterschiedlichen Elementen,
 * berechnet der Browser das `click`-Ereignis am gemeinsamen Vorfahren
 * beider Punkte — bei einem Popup ist das fast immer der Hintergrund
 * selbst, auch wenn die Auswahl komplett im Popup-Inhalt begann. Eine
 * `e.target === e.currentTarget`-Prüfung allein im `onClick` hilft nicht:
 * sie ist in genau diesem Fall ohnehin schon wahr.
 *
 * Fix: der tatsächliche Beginn wird separat über `onPointerDown` gemerkt
 * (das Ereignis bubbelt ungehindert bis zum Hintergrund hoch, anders als
 * `click` bei einem Mousedown/Mouseup-Mismatch). Geschlossen wird nur,
 * wenn BEIDE — Beginn und Ende — direkt auf dem Hintergrund lagen, nicht
 * auf einem Kind-Element darunter.
 *
 * Verwendung: `<div className="x-hintergrund" {...useHintergrundSchliessen(onSchliessen)}>`
 * — der innere Popup-Inhalt braucht weiterhin sein eigenes
 * `onClick={(e) => e.stopPropagation()}`, sonst schlösse jeder Klick im
 * Popup es gleich wieder (unverändert, siehe Fenster.tsx).
 */
export function useHintergrundSchliessen(onSchliessen: () => void) {
  const begannAufHintergrund = useRef(false);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    begannAufHintergrund.current = e.target === e.currentTarget;
  }, []);

  const onClick = useCallback(
    (e: React.MouseEvent) => {
      if (begannAufHintergrund.current && e.target === e.currentTarget) {
        onSchliessen();
      }
    },
    [onSchliessen],
  );

  return { onPointerDown, onClick };
}
