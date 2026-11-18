/** Der Tummy-Acher frisst Punkte (Mark, 16.11.2026: „er könnte ja auch die
 *  Punkte der Fertigkeiten und Attribute der Spieler fressen … vielleicht
 *  wenn man ihn streichelt?“). Nur Optik: der Punkt verschwindet vom Schirm,
 *  der Wert bleibt gleich und ist weiter anklickbar. Streicheln spuckt alles
 *  wieder aus, die Punkte fliegen an ihren Platz zurück. Kein Server: wird die
 *  Seite neu geladen oder der Bogen neu aufgebaut, sind sie ohnehin wieder da. */
import type { SpurAufSchirm } from "./bewegung";

/** Markiert einen gefressenen Punkt (pets.css). React verwaltet die Klasse
 *  nicht — die Punkte von DotPool haben keine eigene — und lässt sie stehen. */
const WEG = "pet-punkt-weg";
/** Von einer Fledermaus angebissen/ausgetrunken (18.11.2026) — Füllstand per
 *  CSS-Variable `--pet-pegel`, Farbe in `--pet-farbe` (pets.css). */
const GETRUNKEN = "pet-punkt-getrunken";
/** Höchstens so viele Punkte im Bauch (Annahme Neko). */
export const PUNKTE_MAX = 12;

const nummer = new WeakMap<HTMLElement, string>();
const element = new Map<string, HTMLElement>();
const bauch = new Map<string, HTMLElement[]>();
let zaehler = 0;

function idVon(el: HTMLElement): string {
  let id = nummer.get(el);
  if (!id) {
    id = `punkt:${++zaehler}`;
    nummer.set(el, id);
    element.set(id, el);
  }
  return id;
}

export const istPunkt = (id: string) => id.startsWith("punkt:");

/** Gefüllte, sichtbare Punkte (DotPool, `data-punkt="voll"`). `unten` ist die
 *  Oberkante der Punktereihe — dort steht er, wenn er auf ihr läuft. */
export function sichtbarePunkte(): SpurAufSchirm[] {
  const aus: SpurAufSchirm[] = [];
  for (const el of document.querySelectorAll<HTMLElement>(`.dot-reihe > [data-punkt="voll"]:not(.${WEG}):not(.${GETRUNKEN})`)) {
    if (el.closest(".pet-ebene")) continue;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.bottom < 0 || r.top > window.innerHeight) continue;
    const reihe = el.parentElement!.getBoundingClientRect();
    aus.push({ id: idVon(el), art: "punkt", x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2, unten: reihe.top });
  }
  return aus;
}

export function anzahlImBauch(petId: string) {
  return (bauch.get(petId) ?? []).filter((el) => el.isConnected).length;
}

/** Fliegt ins Maul: der Punkt selbst wird verschoben und schrumpft. */
export function punktGreifen(id: string, x: number, y: number, skala: number) {
  const el = element.get(id);
  if (!el || !el.isConnected) return;
  const r = el.getBoundingClientRect();
  // Rechteck ohne eigene Verschiebung: aktuelle Verschiebung herausrechnen.
  const alt = el.dataset.petDx ? [Number(el.dataset.petDx), Number(el.dataset.petDy)] : [0, 0];
  const dx = x - (r.left + r.right) / 2 + alt[0];
  const dy = y - (r.top + r.bottom) / 2 + alt[1];
  el.dataset.petDx = String(dx);
  el.dataset.petDy = String(dy);
  el.style.transform = `translate(${dx.toFixed(1)}px, ${dy.toFixed(1)}px) scale(${skala.toFixed(2)})`;
  el.style.zIndex = "9000";
  el.style.position = "relative";
}

/** Verschluckt. */
export function punktFressen(petId: string, id: string) {
  const el = element.get(id);
  if (!el) return;
  el.classList.add(WEG);
  el.style.transform = "";
  el.style.zIndex = "";
  el.style.position = "";
  delete el.dataset.petDx;
  delete el.dataset.petDy;
  const liste = bauch.get(petId) ?? [];
  liste.push(el);
  bauch.set(petId, liste);
}

/** Abgebrochen (gepackt, bevor er schlucken konnte): zurück an den Platz. */
export function punktLoslassen(id: string) {
  const el = element.get(id);
  if (!el || !el.dataset.petDx) return;
  el.style.transform = "";
  el.style.zIndex = "";
  el.style.position = "";
  delete el.dataset.petDx;
  delete el.dataset.petDy;
}

/** Rülps — alle Punkte fliegen im Bogen aus dem Maul zurück an ihren Platz. */
export function ausspucken(petId: string, maulX: number, maulY: number): number {
  const liste = (bauch.get(petId) ?? []).filter((el) => el.isConnected);
  bauch.delete(petId);
  liste.forEach((el, i) => {
    el.classList.remove(WEG);
    const r = el.getBoundingClientRect();
    const dx = maulX - (r.left + r.right) / 2;
    const dy = maulY - (r.top + r.bottom) / 2;
    const hoch = Math.min(-60, dy * 0.5 - 80);
    el.animate(
      [
        { transform: `translate(${dx}px, ${dy}px) scale(0.3)`, opacity: 0, offset: 0 },
        { transform: `translate(${dx}px, ${dy}px) scale(0.5)`, opacity: 1, offset: 0.05 },
        { transform: `translate(${dx * 0.5}px, ${hoch}px) scale(1.3)`, offset: 0.55 },
        { transform: "translate(0, 0) scale(1)", opacity: 1, offset: 1 },
      ],
      { duration: 750, delay: i * 110, easing: "ease-in-out", fill: "backwards" },
    );
  });
  return liste.length;
}


// ── Fledermäuse trinken Punkte (Mark, 18.11.2026) ──────────────────────────
// „Die könnten die Fähigkeits- und Attributpunkte austrinken! So anstelle von
// Blut, und die füllen sich dann nur ganz langsam wieder auf, das könnte fast
// 10–15 Minuten dauern“ — „wie eine Fruitbat in die Kugel beißen und sie dann
// austrinken“. Nur Optik wie beim Tummy-Acher: der Wert bleibt gleich. Der
// Punkt läuft von oben leer, der Ring bleibt; danach füllt er sich langsam
// wieder. Neu laden füllt sofort (nichts liegt auf dem Server).

/** So lange braucht ein ausgetrunkener Punkt, bis er wieder voll ist (ms). */
const NACHFUELLEN_MS: [number, number] = [10 * 60_000, 15 * 60_000];

interface Pegel {
  pegel: number;
  /** Seit wann er nachläuft (null = wird gerade getrunken) und wie lange bis voll. */
  ab: number | null;
  dauer: number;
}
const pegel = new Map<HTMLElement, Pegel>();
let uhr = 0;

function zeigePegel(el: HTMLElement, p: number) {
  el.style.setProperty("--pet-pegel", `${(Math.max(0, Math.min(1, p)) * 100).toFixed(1)}%`);
}

function vergiss(el: HTMLElement) {
  pegel.delete(el);
  el.classList.remove(GETRUNKEN);
  el.style.removeProperty("--pet-pegel");
  el.style.removeProperty("--pet-farbe");
}

/** Alle paar Sekunden: ausgetrunkene Punkte laufen langsam wieder voll. */
function nachlaufen() {
  const jetzt = performance.now();
  for (const [el, p] of pegel) {
    // Weg (Bogen zu) oder der Wert ist jetzt kleiner: nichts mehr nachzufüllen.
    if (!el.isConnected || el.dataset.punkt !== "voll") {
      vergiss(el);
      continue;
    }
    if (p.ab === null) continue;
    p.pegel = (jetzt - p.ab) / p.dauer;
    if (p.pegel >= 1) vergiss(el);
    else zeigePegel(el, p.pegel);
  }
  if (!pegel.size && uhr) {
    window.clearInterval(uhr);
    uhr = 0;
  }
}

/** Mitte und Radius eines Punkts (null = nicht mehr da). */
export function punktLage(id: string): { x: number; y: number; r: number } | null {
  const el = element.get(id);
  if (!el || !el.isConnected) return null;
  const r = el.getBoundingClientRect();
  if (r.width <= 0) return null;
  return { x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2, r: r.width / 2 };
}

/** Reinbeißen: der Punkt zuckt kurz, ab jetzt gehört er ihr. false = geht nicht mehr. */
export function punktAnbeissen(id: string): boolean {
  const el = element.get(id);
  if (!el || !el.isConnected || el.dataset.punkt !== "voll" || el.classList.contains(WEG) || el.classList.contains(GETRUNKEN)) return false;
  el.style.setProperty("--pet-farbe", getComputedStyle(el).backgroundColor);
  el.classList.add(GETRUNKEN);
  // Die Kugel liegt beim Trinken vor ihrem Maul, nicht hinter der Fledermaus.
  el.style.position = "relative";
  el.style.zIndex = "9000";
  zeigePegel(el, 1);
  pegel.set(el, { pegel: 1, ab: null, dauer: 0 });
  el.animate(
    [{ transform: "scale(1)" }, { transform: "scale(0.78, 0.9)" }, { transform: "scale(1.08)" }, { transform: "scale(1)" }],
    { duration: 320, easing: "ease-out" },
  );
  return true;
}

/** Austrinken: `rest` 1 = voll, 0 = leer. */
export function punktTrinken(id: string, rest: number) {
  const el = element.get(id);
  const p = el && pegel.get(el);
  if (!el || !p) return;
  p.pegel = rest;
  zeigePegel(el, rest);
}

/** Fertig (oder abgebrochen): ab dem jetzigen Stand langsam wieder voll laufen. */
export function punktNachfuellen(id: string) {
  const el = element.get(id);
  const p = el && pegel.get(el);
  if (!el || !p || p.ab !== null) return;
  el.style.position = "";
  el.style.zIndex = "";
  p.dauer = NACHFUELLEN_MS[0] + Math.random() * (NACHFUELLEN_MS[1] - NACHFUELLEN_MS[0]);
  p.ab = performance.now() - p.pegel * p.dauer;
  if (!uhr) uhr = window.setInterval(nachlaufen, 3000);
}

/** Der nächste volle Punkt in derselben Reihe (die Fledermaus trinkt sich die Reihe entlang). */
export function nachbarPunkt(id: string): string | null {
  const el = element.get(id);
  const reihe = el?.parentElement;
  if (!el || !reihe) return null;
  const alle = Array.from(reihe.children) as HTMLElement[];
  const i = alle.indexOf(el);
  const frei = (k: HTMLElement) => k.dataset.punkt === "voll" && !k.classList.contains(WEG) && !k.classList.contains(GETRUNKEN);
  for (let d = 1; d < alle.length; d++) {
    for (const k of [alle[i - d], alle[i + d]]) if (k && frei(k)) return idVon(k);
  }
  return null;
}

/** Ein Tropfen fliegt vom Punkt ins Maul. */
export function tropfen(id: string, zx: number, zy: number) {
  const el = element.get(id);
  const l = punktLage(id);
  if (!el || !l) return;
  const t = document.createElement("span");
  const g = Math.max(2, l.r * 0.45);
  t.style.cssText = `position:fixed;left:${l.x - g / 2}px;top:${l.y - g / 2}px;width:${g}px;height:${g}px;border-radius:50%;` +
    `background:${el.style.getPropertyValue("--pet-farbe") || "currentColor"};pointer-events:none;z-index:9001;`;
  document.body.appendChild(t);
  const a = t.animate(
    [
      { transform: "translate(0,0) scale(1)", opacity: 1 },
      { transform: `translate(${zx - l.x}px, ${zy - l.y}px) scale(0.4)`, opacity: 0.6 },
    ],
    { duration: 260 + Math.random() * 120, easing: "ease-in" },
  );
  a.onfinish = () => t.remove();
}
