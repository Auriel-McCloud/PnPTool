import { useCallback, useEffect, useRef } from "react";

/** Wie lange nach der letzten Eingabe gespeichert wird — identisch zum
 * Wiki-Vorbild (wiki/WikiAnsicht.tsx::AUTOSAVE_MS). */
const AUTOSAVE_MS = 1200;

/**
 * Automatisches Speichern nach Eingabepause, für Beschreibungs-/Notizen-
 * Editoren außerhalb des Wikis (Ort/Fraktion/Event/NPC/PC/Gegenstand/
 * Begleiter-Detail-Popups).
 *
 * Gleiches Muster wie im Wiki (WikiAnsicht.tsx::merken/jetztSpeichern):
 * 1200ms nach der letzten Änderung wird automatisch gespeichert, zusätzlich
 * beim Verlassen der Komponente sofort (Tab-Wechsel im Popup, Schließen).
 * Löst Marks Problem, dass ein Tablet-Standby/Reload zwischen letzter
 * Eingabe und Klick auf "Speichern" den Text verwirft.
 *
 * Bewusst ohne Statusanzeige (Mark, 27.09.2026: "einfach still im
 * Hintergrund speichern") — Aufrufer mit einem eigenen "speichert…"-Zustand
 * für andere Formularteile (z.B. das große Gegenstand-Bearbeiten-Fenster)
 * bleiben davon unberührt, da diese Funktion nur ihr eigenes `speichern`
 * ruft, nie einen fremden Ladezustand setzt.
 *
 * Der `speichern`-Callback darf NICHT die Elternliste neu laden
 * (`onGeaendert` / `refreshAll`) und das Fenster nicht schließen: der Reload
 * unmountet das Popup, die Öffnen-Animation läuft nochmal, der Tab springt
 * auf die Übersicht. Genau das ist Marks "zwei Wörter, Popup zu, wieder
 * auf, nicht mehr im Beschreibungstab" (30.09.2026). Nur das PATCH selbst.
 *
 * Rückgabe: `planen(wert)` — bei jeder Änderung aufrufen (z.B. im
 * `onChange` des Editors), nicht in einem `useEffect` auf den State selbst,
 * damit ein reines Neuladen/Öffnen keinen Speichervorgang auslöst.
 */
export function useAutosave<T>(speichern: (wert: T) => void | Promise<void>): (wert: T) => void {
  const timer = useRef<number | undefined>(undefined);
  // Letzter noch nicht geschriebener Stand. Als Ref statt State, damit der
  // Unmount-Cleanup unten den aktuellen Wert sieht, ohne dass jede Änderung
  // den Effekt neu aufsetzt.
  const ausstehend = useRef<{ wert: T } | null>(null);
  const speichernRef = useRef(speichern);
  speichernRef.current = speichern;

  const jetzt = useCallback(() => {
    window.clearTimeout(timer.current);
    const auftrag = ausstehend.current;
    if (!auftrag) return;
    ausstehend.current = null;
    speichernRef.current(auftrag.wert);
  }, []);

  const planen = useCallback(
    (wert: T) => {
      ausstehend.current = { wert };
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(jetzt, AUTOSAVE_MS);
    },
    [jetzt],
  );

  // Ausstehendes wegschreiben, bevor die Komponente verschwindet — sonst
  // geht genau der letzte Tippstoß verloren, den Autosave eigentlich retten soll.
  useEffect(() => {
    return () => {
      window.clearTimeout(timer.current);
      if (ausstehend.current) speichernRef.current(ausstehend.current.wert);
    };
  }, []);

  return planen;
}
