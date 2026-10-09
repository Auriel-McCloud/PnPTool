/**
 * Hält die virtuelle Tastatur aus dem Inhalt.
 *
 * Android (installierte PWA, display:fullscreen) verkleinert oft nur den
 * Visual Viewport, nicht das Layout. Fenster mit height: 94svh bleiben dann
 * unter der Tastatur. Ein ständiges scrollIntoView bei jedem Viewport-Scroll
 * stiehlt dazu den Fokus — die Tastatur klappt zu, sobald man den Cursor
 * setzt oder eine Autokorrektur antippt.
 *
 * Hier nur CSS-Variablen setzen. Ins Bild holen nur, wenn die Tastatur
 * wirklich aufgeht und die Caret-Stelle tatsächlich verdeckt ist.
 */

const SCHWELLE = 80;
const DELTA = 40;

function istEingabe(el: EventTarget | null): el is HTMLElement {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  return el.isContentEditable;
}

function messen(): { hoehe: number; vvH: number; vvOben: number } | null {
  const vv = window.visualViewport;
  if (!vv) return null;
  const hoehe = Math.max(0, Math.round(window.innerHeight - vv.height - vv.offsetTop));
  return { hoehe, vvH: vv.height, vvOben: vv.offsetTop };
}

function anwenden() {
  const mass = messen();
  if (!mass) return;
  const root = document.documentElement;
  root.style.setProperty("--vv-h", `${mass.vvH}px`);
  root.style.setProperty("--vv-oben", `${mass.vvOben}px`);
  root.style.setProperty("--tastatur", `${mass.hoehe}px`);
  root.classList.toggle("tastatur-offen", mass.hoehe > SCHWELLE);
}

function caretRect(): DOMRect | null {
  const sel = window.getSelection();
  // Laufende Markierung nicht anfassen — Android blendet sonst Tastatur
  // und Auswahlgriffe aus.
  if (!sel || sel.rangeCount === 0 || !sel.isCollapsed) return null;
  const r = sel.getRangeAt(0).getBoundingClientRect();
  if (r.width === 0 && r.height === 0) return null;
  return r;
}

function insBild() {
  const el = document.activeElement;
  if (!istEingabe(el)) return;
  const vv = window.visualViewport;
  if (!vv) return;
  const rect = caretRect() ?? el.getBoundingClientRect();
  const oben = vv.offsetTop + 12;
  const unten = vv.offsetTop + vv.height - 12;
  if (rect.bottom <= unten && rect.top >= oben) return;
  el.scrollIntoView({ block: "center", inline: "nearest" });
}

let letzteHoehe = 0;

function beiResize() {
  anwenden();
  const hoehe = messen()?.hoehe ?? 0;
  if (Math.abs(hoehe - letzteHoehe) < DELTA) return;
  letzteHoehe = hoehe;
  requestAnimationFrame(insBild);
}

function beiFocusIn() {
  requestAnimationFrame(() => {
    anwenden();
    insBild();
  });
}

if (typeof window !== "undefined") {
  anwenden();
  window.visualViewport?.addEventListener("resize", beiResize);
  // offsetTop ändert sich, wenn Android den Visual Viewport schiebt —
  // Variablen nachziehen, aber nicht scrollIntoView (das klappt die IME zu).
  window.visualViewport?.addEventListener("scroll", anwenden);
  window.addEventListener("focusin", beiFocusIn);
}
