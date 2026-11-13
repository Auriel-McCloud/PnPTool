import { treffe, type Angriff } from "./treffen";

/**
 * Feuerball (Mark, 13.11.2026: „Feuerbälle schießen, die weiter fliegen“).
 *
 * Ab dem Halbstarken schießt der Drache statt des Feuerstoßes öfter einen
 * Ball: Feuerball, Eisball (Eisdrache) oder Kugelblitz (Blitzdrache). Er
 * fliegt im Bogen weit über den Schirm und schlägt unten ein. Fliegt er über
 * den Seitenrand hinaus, kommt er auf einem anderen Tablet der Party wieder
 * herein (`herein`) — das regelt der Server.
 *
 * Gezeichnet wird direkt am DOM (ein Element je Ball), kein Render pro Frame.
 */

export type BallArt = "feuer" | "eis" | "blitz";

/** Gleiche Werte wie docs/assets/critter-pet/feuerball.py. */
const BALL = { breite: 28, hoehe: 16, frames: 6, mitteX: 20.5 } as const;
const SCHWERKRAFT = 620;
const KNALL_MS = 280;

function ebene(): HTMLElement | null {
  return document.querySelector<HTMLElement>(".pet-ebene");
}

function element(art: BallArt, s: number): HTMLDivElement {
  const el = document.createElement("div");
  el.className = `pet-ball pet-ball-${art}`;
  el.style.width = `${BALL.breite * s}px`;
  el.style.height = `${BALL.hoehe * s}px`;
  el.style.backgroundImage = `url(/pets/ball_${art}.png)`;
  el.style.setProperty("--bw", `${BALL.breite * s}px`);
  return el;
}

/** Ball so legen, dass die Kugel (nicht der Schweif) auf x/y sitzt, Schweif gegen die Flugrichtung. */
function lege(el: HTMLElement, x: number, y: number, vx: number, vy: number, s: number) {
  const w = Math.atan2(vy, vx);
  el.style.left = `${x - BALL.mitteX * s}px`;
  el.style.top = `${y - (BALL.hoehe * s) / 2}px`;
  el.style.transformOrigin = `${BALL.mitteX * s}px 50%`;
  el.style.transform = `rotate(${w.toFixed(3)}rad)`;
}

/** Einschlag: nur die Kugel platzt auf (der Schweif bleibt weg), dann verschwindet sie. */
function knall(el: HTMLElement, x: number, y: number, s: number) {
  const g = BALL.hoehe * s;
  el.classList.add("pet-ball-knall");
  el.style.transform = "";
  el.style.transformOrigin = "50% 50%";
  el.style.width = `${g}px`;
  el.style.left = `${x - g / 2}px`;
  el.style.top = `${y - g / 2}px`;
  el.style.backgroundPosition = `${-(BALL.mitteX - BALL.hoehe / 2) * s}px 0`;
  window.setTimeout(() => el.remove(), KNALL_MS);
}

/** Trifft der Einschlag ein Pet auf diesem Schirm? Rückgabe wie `treffe`. */
function einschlag(art: BallArt, x: number, y: number, s: number, taeter: string, jetzt: number) {
  const angriff: Angriff = { art, x, y, r: 26 * s };
  return treffe(angriff, taeter, jetzt);
}

export interface Schuss {
  art: BallArt;
  /** Wer geschossen hat (wird selbst nicht getroffen). */
  petId: string;
  /** Maul in Bildschirm-Pixeln. */
  x: number;
  y: number;
  richtung: 1 | -1;
  /** Bildschirm-Pixel je Sprite-Pixel, schon mit dem Wachstum des Atems. */
  skala: number;
  /** Unten eingeschlagen: Mitte des Flecks. */
  onEinschlag: (x: number, y: number, treffer: ReturnType<typeof treffe>) => void;
  /** Seitlich hinausgeflogen. */
  onHinaus: (seite: "links" | "rechts") => void;
}

/** Schuss vom Maul: flacher Bogen, weit. */
export function schiesse(sch: Schuss) {
  const wurzel = ebene();
  if (!wurzel) return;
  const s = sch.skala;
  const el = element(sch.art, s);
  wurzel.appendChild(el);
  let x = sch.x + sch.richtung * 6 * s;
  let y = sch.y;
  let vx = sch.richtung * (430 + Math.random() * 520);
  let vy = -(150 + Math.random() * 200);
  let letzte = performance.now();
  const takt = (jetzt: number) => {
    if (!el.isConnected) return;
    const dt = Math.min(0.05, (jetzt - letzte) / 1000);
    letzte = jetzt;
    vy += SCHWERKRAFT * dt;
    x += vx * dt;
    y += vy * dt;
    const breite = window.innerWidth;
    const boden = window.innerHeight - 7 * s;
    if (x < -BALL.breite * s || x > breite + BALL.breite * s) {
      el.remove();
      sch.onHinaus(x < 0 ? "links" : "rechts");
      return;
    }
    if (y >= boden) {
      knall(el, x, boden, s);
      sch.onEinschlag(x, boden, einschlag(sch.art, x, boden, s, sch.petId, jetzt));
      return;
    }
    lege(el, x, y, vx, vy, s);
    requestAnimationFrame(takt);
  };
  lege(el, x, y, vx, vy, s);
  requestAnimationFrame(takt);
}

/** Ball von einem anderen Tablet: fliegt von der Seite herein und schlägt bei
 *  (x, y) ein — genau nach `ms`, dann legt der Server dort die Flecken hin. */
export function herein(
  art: BallArt,
  seite: "links" | "rechts",
  zielX: number,
  zielY: number,
  ms: number,
  skala: number,
  onTreffer: (treffer: ReturnType<typeof treffe>) => void,
) {
  const wurzel = ebene();
  if (!wurzel) return;
  const el = element(art, skala);
  wurzel.appendChild(el);
  const t = Math.max(0.3, ms / 1000);
  const x0 = seite === "links" ? -BALL.breite * skala : window.innerWidth + BALL.breite * skala;
  const y0 = Math.max(20, zielY - window.innerHeight * 0.3);
  const vx = (zielX - x0) / t;
  const vy0 = (zielY - y0 - 0.5 * SCHWERKRAFT * t * t) / t;
  const start = performance.now();
  const takt = (jetzt: number) => {
    if (!el.isConnected) return;
    const z = (jetzt - start) / 1000;
    if (z >= t) {
      knall(el, zielX, zielY, skala);
      onTreffer(einschlag(art, zielX, zielY, skala, "", jetzt));
      return;
    }
    lege(el, x0 + vx * z, y0 + vy0 * z + 0.5 * SCHWERKRAFT * z * z, vx, vy0 + SCHWERKRAFT * z, skala);
    requestAnimationFrame(takt);
  };
  requestAnimationFrame(takt);
}
