/**
 * Merkt sich, wo zuletzt getippt wurde.
 *
 * Fenster sollen dort aufgehen, wo der Finger war (docs/ui-konzept.md) — sonst
 * erscheinen sie aus dem Nichts und man sucht erst, was sich gerade geaendert
 * hat. Die Alternative waere, die Koordinaten durch jeden Klick-Handler und
 * jede Komponente durchzureichen; das waere an rund zwanzig Stellen zu
 * ergaenzen und an jeder neuen wieder zu vergessen.
 *
 * Deshalb ein einzelner Mitschnitt am Dokument: er laeuft in der
 * Erfassungsphase, ist also vor jedem Klick-Handler dran und hat die Position
 * bereits liegen, wenn das Fenster gleich darauf aufgeht.
 */
let letzte: { x: number; y: number } | null = null;

if (typeof document !== "undefined") {
  document.addEventListener(
    "pointerdown",
    (e) => {
      letzte = { x: e.clientX, y: e.clientY };
    },
    { capture: true, passive: true },
  );
  // Tastaturbedienung hat keine Koordinaten. Dann soll das Fenster nicht aus
  // einer zufaelligen alten Ecke fliegen, sondern schlicht aus seiner Mitte.
  document.addEventListener("keydown", () => {
    letzte = null;
  }, { capture: true, passive: true });
}

export function letzteTippPosition() {
  return letzte;
}
