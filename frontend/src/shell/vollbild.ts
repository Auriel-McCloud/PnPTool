/**
 * Merkt sich den Wunsch nach Vollbild und stellt ihn wieder her.
 *
 * Hintergrund: sperrt man das Tablet, beendet das System das Vollbild. Beim
 * Entsperren steht man wieder mit Adressleiste da. Von selbst zurückschalten
 * darf die Seite nicht — Browser lassen `requestFullscreen` **nur als Antwort
 * auf eine Nutzeraktion** zu, sonst könnte jede Seite ungefragt den Bildschirm
 * übernehmen.
 *
 * Deshalb der Umweg: der Wunsch wird gemerkt, und beim nächsten Antippen —
 * das ist die verlangte Nutzeraktion — geht das Vollbild wieder auf. In der
 * Praxis heisst das: entsperren, einmal irgendwohin tippen, fertig.
 *
 * Scharf gestellt wird nur, wenn die Seite aus dem Verborgenen zurückkommt.
 * Wer selbst Escape drückt, will heraus und soll dann auch draussen bleiben.
 *
 * Als **installierte App** (`display: fullscreen` im Manifest) braucht es das
 * alles nicht: dort ist das Fenster selbst randlos, und Sperren ändert daran
 * nichts. Das hier ist die Krücke für den Betrieb im Browser-Tab.
 */

const SCHLUESSEL = "pnptool.vollbild";

export function vollbildGewuenscht(): boolean {
  try {
    return localStorage.getItem(SCHLUESSEL) === "ja";
  } catch {
    return false;
  }
}

export function merkeVollbildWunsch(wunsch: boolean) {
  try {
    localStorage.setItem(SCHLUESSEL, wunsch ? "ja" : "nein");
  } catch {
    // Privater Modus: dann gilt der Wunsch eben nur für diese Sitzung
  }
}

/** Läuft das gerade als installierte App statt im Browser-Tab? */
export function alsAppGestartet(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return (
    window.matchMedia("(display-mode: fullscreen)").matches ||
    window.matchMedia("(display-mode: standalone)").matches
  );
}

let scharf = false;

function nachTippenWiederherstellen() {
  if (scharf) return;
  scharf = true;
  const einmal = () => {
    document.removeEventListener("pointerdown", einmal, true);
    scharf = false;
    if (!vollbildGewuenscht() || document.fullscreenElement) return;
    // Schlägt es fehl, bleibt es eben aus — kein Grund für eine Meldung.
    void document.documentElement.requestFullscreen().catch(() => undefined);
  };
  document.addEventListener("pointerdown", einmal, true);
}

if (typeof document !== "undefined") {
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) return;
    if (alsAppGestartet()) return; // dort regelt es das Fenster selbst
    if (!vollbildGewuenscht() || document.fullscreenElement) return;
    // Ein Versuch ohne Geste ist meist vergeblich, kostet aber nichts —
    // manche Browser lassen ihn kurz nach der Rückkehr noch durch.
    void document.documentElement
      .requestFullscreen()
      .catch(() => nachTippenWiederherstellen());
  });
}
