import "./gridmonster.css";

/**
 * 3D-Gitterboden der GridMonster-Optik (Mark, 26.11.2026): ein Gitter in
 * Perspektive, das zum Horizont hin ins Endlose läuft. Es steht still und
 * fährt nur kurz auf den Betrachter zu, wenn sich `fahrt` ändert (jeder
 * Menüwechsel, im Takt mit dem Ankommen der neuen Ansicht) — Mark: „er
 * läuft immer nur für ein paar Sekunden, wenn man in einen anderen
 * Menüpunkt geht“. Dauerbewegung würde am Spielabend nerven.
 *
 * Der `key` baut den Boden bei jedem Wechsel neu auf, damit die
 * CSS-Animation von vorn startet. Liegt mit z-index -1 hinter allem, nimmt
 * keine Klicks an; `prefers-reduced-motion` stoppt die Fahrt (CSS).
 */
export function GridBoden({ fahrt }: { fahrt: string }) {
  return (
    <div className="gm-horizont" aria-hidden="true">
      <div className="gm-boden" key={fahrt} />
    </div>
  );
}
