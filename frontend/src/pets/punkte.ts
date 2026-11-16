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
  for (const el of document.querySelectorAll<HTMLElement>(`.dot-reihe > [data-punkt="voll"]:not(.${WEG})`)) {
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
