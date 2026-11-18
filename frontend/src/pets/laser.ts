/**
 * Reinigungslaser der KI (Mark, 18.11.2026): „ein Strahl, der an einem Punkt
 * beginnt und dann immer schneller wird, bis er wie ein Fächer aussieht, der
 * dann allen Schmutz der anderen Pets wegbrennen kann.“
 *
 * Reiner Zeichen- und Zustandsbaustein ohne React: ein Schuss (laden → Punkt →
 * Pendeln immer schneller → Fächer → aus), Funken und Rauch beim Verdampfen,
 * das rote Ausrufezeichen und die Anime-Zornader. Was getroffen wird,
 * entscheidet KiFigur mit `ueberstrichen()`.
 */

/** Was sie auf welcher Gestalt-Stufe wegbrennen kann (Mark: „am Anfang nur
 *  kleine Dinge wie Kot oder Seiten, später Schleim und danach Brandflecken“).
 *  Raureif und Krater hat Neko zugeordnet. Index = Stufe 0–4. */
export const LASER_ARTEN: readonly (readonly string[])[] = [
  [],
  [],
  ["haeufchen", "seite"],
  ["haeufchen", "seite", "schleim", "frost"],
  ["haeufchen", "seite", "schleim", "frost", "brand", "krater", "eiskrater"],
];

/** Ab so vielen Spuren schaltet sie in den Putzmodus, ab so vielen wird sie wütend. */
export const PUTZ_AB = 3;
export const WUT_AB = 10;

export interface Schmutz {
  id: string;
  art: string;
  petId: string;
  x: number;
  y: number;
}

/** Spuren, die gerade sichtbar irgendwo liegen (nicht gepackt, nicht im Verschwinden). */
export function schmutzAufSchirm(): Schmutz[] {
  return Array.from(document.querySelectorAll<HTMLElement>("[data-schmutz][data-id]:not(.pet-haeufchen-weg)"))
    .filter((el) => el.dataset.fliegt !== "ja" && !verbrannt.has(el.dataset.id!))
    .map((el) => {
      const r = el.getBoundingClientRect();
      return { id: el.dataset.id!, art: el.dataset.schmutz!, petId: el.dataset.pet ?? "", x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2 };
    })
    .filter((s) => s.x > -20 && s.x < window.innerWidth + 20 && s.y > -20 && s.y < window.innerHeight + 20);
}

/** Schon weggebrannt (zwei KIs auf einem Schirm brennen nichts doppelt). */
export const verbrannt = new Set<string>();

/** Ablauf eines Schusses in ms. */
interface Takte {
  laden: number;
  punkt: number;
  rampe: number;
  halten: number;
  aus: number;
}
const VOLL: Takte = { laden: 400, punkt: 400, rampe: 1350, halten: 700, aus: 240 };
const KURZ: Takte = { laden: 280, punkt: 280, rampe: 900, halten: 500, aus: 220 };
const KITZEL: Takte = { laden: 250, punkt: 1300, rampe: 0, halten: 0, aus: 200 };

export type SchussArt = "putzen" | "jagd" | "kitzeln";

export interface Farben {
  kern: string;
  hell: string;
  mittel: string;
}

export class LaserSchuss {
  readonly art: SchussArt;
  private t0: number;
  private takte: Takte;
  private amp: number;
  /** Grundrichtung zum Ziel, läuft dem Ziel weich nach. */
  private basis: number;
  private laenge: number;
  private phase = 0;
  private winkel: number;
  private vorher: number;
  private spur: { w: number; t: number }[] = [];
  fertig = false;

  constructor(art: SchussArt, jetzt: number, stufe: number, von: { x: number; y: number }, ziel: { x: number; y: number }) {
    this.art = art;
    this.t0 = jetzt;
    this.takte = art === "putzen" ? VOLL : art === "jagd" ? KURZ : KITZEL;
    // Geist: dünner Punktstrahl, der nur zittert · Wesen: pendelt · Entität: voller Fächer.
    this.amp = art === "kitzeln" ? 0.05 : stufe >= 4 ? 0.62 : stufe >= 3 ? 0.36 : 0.12;
    this.basis = Math.atan2(ziel.y - von.y, ziel.x - von.x);
    this.laenge = Math.hypot(ziel.x - von.x, ziel.y - von.y);
    this.winkel = this.vorher = this.basis;
  }

  private abschnitt(jetzt: number): "laden" | "punkt" | "rampe" | "halten" | "aus" | "ende" {
    let t = jetzt - this.t0;
    for (const k of ["laden", "punkt", "rampe", "halten", "aus"] as const) {
      if (t < this.takte[k]) return k;
      t -= this.takte[k];
    }
    return "ende";
  }

  /** 0…1 innerhalb der Rampe. */
  private rampe(jetzt: number) {
    const t = jetzt - this.t0 - this.takte.laden - this.takte.punkt;
    return this.takte.rampe ? Math.max(0, Math.min(1, t / this.takte.rampe)) : 1;
  }

  /** Pendel-Frequenz in Hz — wird immer schneller, bis es ein Fächer ist. */
  private frequenz(jetzt: number) {
    const k = this.rampe(jetzt);
    return 0.8 + 10 * Math.pow(k, 1.5);
  }

  /** Strahl brennt (nicht beim Laden und Ausklingen). */
  brennt(jetzt: number) {
    const a = this.abschnitt(jetzt);
    return a === "punkt" || a === "rampe" || a === "halten";
  }

  tick(jetzt: number, dt: number, von: { x: number; y: number }, ziel: { x: number; y: number } | null) {
    const a = this.abschnitt(jetzt);
    if (a === "ende") {
      this.fertig = true;
      return;
    }
    if (ziel) {
      const soll = Math.atan2(ziel.y - von.y, ziel.x - von.x);
      let d = soll - this.basis;
      while (d > Math.PI) d -= Math.PI * 2;
      while (d < -Math.PI) d += Math.PI * 2;
      this.basis += d * Math.min(1, dt * (this.art === "putzen" ? 3 : 8));
      this.laenge += (Math.hypot(ziel.x - von.x, ziel.y - von.y) - this.laenge) * Math.min(1, dt * 4);
    }
    this.vorher = this.winkel;
    if (a === "rampe" || a === "halten") {
      this.phase += Math.PI * 2 * this.frequenz(jetzt) * dt;
      const ausschlag = this.amp * Math.min(1, this.rampe(jetzt) * 1.4);
      this.winkel = this.basis + Math.sin(this.phase) * ausschlag;
    } else if (a === "punkt") {
      // Punktstrahl: zittert nur ein wenig.
      this.winkel = this.basis + Math.sin(jetzt / 37) * 0.012;
    } else this.winkel = this.basis;
    if (this.brennt(jetzt)) {
      this.spur.push({ w: this.winkel, t: jetzt });
    }
    this.spur = this.spur.filter((s) => jetzt - s.t < 130);
  }

  /** Winkelbereich und Reichweite, die der Strahl in diesem Frame überstrichen hat. */
  ueberstrichen(jetzt: number): { von: number; bis: number; reichweite: number } | null {
    if (!this.brennt(jetzt)) return null;
    const lo = Math.min(this.vorher, this.winkel);
    const hi = Math.max(this.vorher, this.winkel);
    // Im vollen Fächer brennt die ganze Breite (der Strahl ist überall zugleich).
    const voll = this.abschnitt(jetzt) === "halten" && this.art !== "kitzeln";
    const breit = voll ? this.amp : 0;
    return { von: Math.min(lo, this.basis - breit) - 0.04, bis: Math.max(hi, this.basis + breit) + 0.04, reichweite: this.laenge * 1.3 + 14 };
  }

  /** Spitze des Strahls (für Funken am Auftreffpunkt). */
  spitze(von: { x: number; y: number }) {
    const l = this.laenge * 1.08;
    return { x: von.x + Math.cos(this.winkel) * l, y: von.y + Math.sin(this.winkel) * l };
  }

  zeichne(ctx: CanvasRenderingContext2D, jetzt: number, von: { x: number; y: number }, f: Farben) {
    const a = this.abschnitt(jetzt);
    if (a === "ende") return;
    const flacker = 0.75 + Math.random() * 0.25;
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    ctx.lineCap = "round";
    if (a === "laden") {
      // Kern lädt sich auf: Lichtball wächst, Teilchen werden eingesaugt.
      const k = (jetzt - this.t0) / this.takte.laden;
      const r = 4 + k * 12;
      const g = ctx.createRadialGradient(von.x, von.y, 0, von.x, von.y, r * 1.8);
      g.addColorStop(0, f.kern);
      g.addColorStop(0.35, f.hell);
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g;
      ctx.globalAlpha = 0.5 + 0.5 * flacker;
      ctx.beginPath();
      ctx.arc(von.x, von.y, r * 1.8, 0, Math.PI * 2);
      ctx.fill();
      for (let i = 0; i < 6; i++) {
        const w = i * 1.05 + jetzt / 90;
        const d = (1 - ((k * 3 + i / 6) % 1)) * 34;
        ctx.fillStyle = f.hell;
        ctx.fillRect(von.x + Math.cos(w) * d - 1.5, von.y + Math.sin(w) * d - 1.5, 3, 3);
      }
      ctx.restore();
      return;
    }
    const aus = a === "aus" ? 1 - (jetzt - this.t0 - this.takte.laden - this.takte.punkt - this.takte.rampe - this.takte.halten) / this.takte.aus : 1;
    const l = this.laenge * 1.08;
    const dicke = this.art === "kitzeln" ? 0.6 : 1;

    // Ab einem schnellen Pendeln steht der Fächer als flimmernde Fläche.
    const f0 = this.frequenz(jetzt);
    if ((a === "rampe" || a === "halten") && f0 > 4.5 && this.art !== "kitzeln") {
      const k = Math.min(1, (f0 - 4.5) / 4);
      const breit = this.amp * Math.min(1, this.rampe(jetzt) * 1.4);
      const g = ctx.createRadialGradient(von.x, von.y, 0, von.x, von.y, l);
      g.addColorStop(0, f.hell);
      g.addColorStop(0.7, f.mittel);
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.globalAlpha = 0.4 * k * flacker * aus;
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.moveTo(von.x, von.y);
      ctx.arc(von.x, von.y, l, this.basis - breit, this.basis + breit);
      ctx.closePath();
      ctx.fill();
    }

    // Nachleuchten der letzten Strahlen — bei schnellem Pendeln wird daraus der Fächer.
    for (const s of this.spur) {
      const alt = 1 - (jetzt - s.t) / 130;
      ctx.globalAlpha = 0.35 * alt * aus;
      ctx.strokeStyle = f.mittel;
      ctx.lineWidth = 5 * dicke;
      ctx.beginPath();
      ctx.moveTo(von.x, von.y);
      ctx.lineTo(von.x + Math.cos(s.w) * l, von.y + Math.sin(s.w) * l);
      ctx.stroke();
    }
    // Der Strahl selbst: breiter Schein, heller Kern.
    const sx = von.x + Math.cos(this.winkel) * l;
    const sy = von.y + Math.sin(this.winkel) * l;
    ctx.globalAlpha = 0.45 * flacker * aus;
    ctx.strokeStyle = f.mittel;
    ctx.lineWidth = 9 * dicke;
    ctx.beginPath();
    ctx.moveTo(von.x, von.y);
    ctx.lineTo(sx, sy);
    ctx.stroke();
    ctx.globalAlpha = aus;
    ctx.strokeStyle = f.hell;
    ctx.lineWidth = 3.2 * dicke;
    ctx.stroke();
    ctx.strokeStyle = f.kern;
    ctx.lineWidth = 1.4 * dicke;
    ctx.stroke();
    // Glühender Auftreffpunkt.
    const r = (7 + Math.random() * 4) * dicke;
    const g = ctx.createRadialGradient(sx, sy, 0, sx, sy, r);
    g.addColorStop(0, f.kern);
    g.addColorStop(0.4, f.hell);
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(sx, sy, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

/** Liegt der Punkt im überstrichenen Bereich? */
export function imStrahl(
  b: { von: number; bis: number; reichweite: number },
  von: { x: number; y: number },
  p: { x: number; y: number },
  extra = 0,
): boolean {
  const d = Math.hypot(p.x - von.x, p.y - von.y);
  if (d > b.reichweite + extra) return false;
  let w = Math.atan2(p.y - von.y, p.x - von.x);
  const mitte = (b.von + b.bis) / 2;
  while (w - mitte > Math.PI) w -= Math.PI * 2;
  while (w - mitte < -Math.PI) w += Math.PI * 2;
  // Größere Ziele (Pets) werden auch am Rand gestreift.
  const rand = d > 1 ? Math.atan(extra / d) : Math.PI;
  return w >= b.von - rand && w <= b.bis + rand;
}

// ── Funken und Rauch ──────────────────────────────────────────────────────

interface Teil {
  x: number;
  y: number;
  vx: number;
  vy: number;
  t0: number;
  leben: number;
  art: "funke" | "rauch" | "blitz";
  g: number;
}

export class Verdampfen {
  private teile: Teil[] = [];

  get leer() {
    return this.teile.length === 0;
  }

  /** Spur verdampft: Lichtblitz, Funken, Rauchwölkchen. */
  puff(x: number, y: number, jetzt: number) {
    this.teile.push({ x, y, vx: 0, vy: 0, t0: jetzt, leben: 260, art: "blitz", g: 18 });
    for (let i = 0; i < 16; i++) {
      const w = Math.random() * Math.PI * 2;
      const v = 60 + Math.random() * 190;
      this.teile.push({ x, y, vx: Math.cos(w) * v, vy: Math.sin(w) * v - 90, t0: jetzt, leben: 380 + Math.random() * 420, art: "funke", g: 1.5 + Math.random() * 2 });
    }
    for (let i = 0; i < 6; i++) {
      this.teile.push({
        x: x + (Math.random() - 0.5) * 18, y: y + (Math.random() - 0.5) * 8,
        vx: (Math.random() - 0.5) * 22, vy: -18 - Math.random() * 30,
        t0: jetzt + i * 40, leben: 900 + Math.random() * 600, art: "rauch", g: 5 + Math.random() * 5,
      });
    }
  }

  /** Funken am Auftreffpunkt des Strahls (ab und zu). */
  spruehen(x: number, y: number, jetzt: number) {
    const w = -Math.PI / 2 + (Math.random() - 0.5) * 2.4;
    const v = 50 + Math.random() * 120;
    this.teile.push({ x, y, vx: Math.cos(w) * v, vy: Math.sin(w) * v, t0: jetzt, leben: 250 + Math.random() * 250, art: "funke", g: 1.2 + Math.random() * 1.4 });
  }

  zeichne(ctx: CanvasRenderingContext2D, jetzt: number, dt: number, f: Farben) {
    this.teile = this.teile.filter((t) => jetzt - t.t0 < t.leben);
    ctx.save();
    for (const t of this.teile) {
      const k = (jetzt - t.t0) / t.leben;
      if (k < 0) continue;
      if (t.art === "funke") {
        t.vy += 420 * dt;
        t.x += t.vx * dt;
        t.y += t.vy * dt;
        ctx.globalCompositeOperation = "lighter";
        ctx.globalAlpha = 1 - k;
        ctx.fillStyle = k < 0.3 ? f.kern : k < 0.6 ? f.hell : "rgb(255,150,60)";
        ctx.fillRect(t.x - t.g / 2, t.y - t.g / 2, t.g, t.g);
      } else if (t.art === "rauch") {
        t.x += t.vx * dt;
        t.y += t.vy * dt;
        ctx.globalCompositeOperation = "source-over";
        ctx.globalAlpha = 0.38 * (1 - k);
        ctx.fillStyle = "rgb(90,90,100)";
        ctx.beginPath();
        ctx.arc(t.x, t.y, t.g * (1 + k * 2.2), 0, Math.PI * 2);
        ctx.fill();
      } else {
        ctx.globalCompositeOperation = "lighter";
        const g = ctx.createRadialGradient(t.x, t.y, 0, t.x, t.y, t.g * (1 + k * 2));
        g.addColorStop(0, f.kern);
        g.addColorStop(0.5, f.hell);
        g.addColorStop(1, "rgba(0,0,0,0)");
        ctx.globalAlpha = 1 - k;
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(t.x, t.y, t.g * (1 + k * 2), 0, Math.PI * 2);
        ctx.fill();
      }
    }
    ctx.restore();
  }
}

// ── Ausrufezeichen und Zornader ───────────────────────────────────────────

const ROT = "rgb(255,42,58)";
const ROT_DUNKEL = "rgb(90,0,12)";

/** Rotes „!“ — Mitte oben bei x/y, Höhe h. */
function ausrufe(ctx: CanvasRenderingContext2D, x: number, y: number, h: number) {
  const b = Math.max(3, h * 0.28);
  ctx.fillStyle = ROT_DUNKEL;
  ctx.fillRect(x - b / 2 - 1.5, y - 1.5, b + 3, h * 0.68 + 3);
  ctx.fillRect(x - b / 2 - 1.5, y + h * 0.8 - 1.5, b + 3, b + 3);
  ctx.fillStyle = ROT;
  ctx.fillRect(x - b / 2, y, b, h * 0.68);
  ctx.fillRect(x - b / 2, y + h * 0.8, b, b);
}

/** Putzmodus: ein „!“, das über dem Kopf hüpft. */
export function zeichneAchtung(ctx: CanvasRenderingContext2D, x: number, kopf: number, jetzt: number, p: number) {
  const h = 6 * p;
  const hupf = Math.abs(Math.sin(jetzt / 160)) * 3 * p;
  ausrufe(ctx, x, kopf - h - 4 - hupf, h);
}

/** Wütend: drei blinkende „!“ und die pochende Zornader daneben. */
export function zeichneWut(ctx: CanvasRenderingContext2D, x: number, kopf: number, rechts: number, jetzt: number, p: number) {
  const h = 6 * p;
  for (let i = 0; i < 3; i++) {
    // Jedes blinkt für sich, versetzt.
    if (Math.floor(jetzt / 140 + i * 1.3) % 3 === 0) continue;
    const dx = (i - 1) * 5 * p;
    const schraeg = (i - 1) * 0.18;
    ctx.save();
    ctx.translate(x + dx, kopf - h - 4 - (i === 1 ? 2 * p : 0));
    ctx.rotate(schraeg);
    ausrufe(ctx, 0, 0, h);
    ctx.restore();
  }
  zornader(ctx, rechts, kopf + 3 * p, 4.2 * p * (1 + 0.18 * Math.max(0, Math.sin(jetzt / 85))));
}

/** 💢 — vier gebogene Stücke, die Ecken zur Mitte, die Enden nach außen. */
export function zornader(ctx: CanvasRenderingContext2D, x: number, y: number, s: number) {
  ctx.save();
  ctx.lineCap = "round";
  for (const [farbe, dicke] of [[ROT_DUNKEL, s * 0.55 + 3], [ROT, s * 0.55]] as const) {
    ctx.strokeStyle = farbe;
    ctx.lineWidth = dicke;
    for (const [sx, sy] of [[1, 1], [-1, 1], [1, -1], [-1, -1]]) {
      const cx = x + sx * s * 1.25;
      const cy = y + sy * s * 1.25;
      const w = Math.atan2(-sy, -sx);
      ctx.beginPath();
      ctx.arc(cx, cy, s * 0.95, w - 0.95, w + 0.95);
      ctx.stroke();
    }
  }
  ctx.restore();
}
