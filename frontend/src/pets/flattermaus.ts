/**
 * Bärbels Flattermäuse (Mark, 18.11.2026): „für Bärbel die Animation, bei der
 * sie Fledermäuse ausniest — die Fledermäuse bleiben wie die Perle da, flattern
 * durch die Gegend und hängen sich kopfüber an HTML-Items, und Bärbel versucht,
 * sie mit dem Tentakel wieder einzufangen oder mit Blitzen zu vernichten, und
 * jagt sie.“
 *
 * Jede Flattermaus ist eine Spur (`art: flattermaus`) auf dem Tablet, auf dem
 * Bärbel geniest hat — sie bleibt dort, bis Bärbel sie erwischt (oder die SL
 * „Alles sauber machen“ drückt). Wie sie sich bewegt, entscheidet nur dieses
 * Tablet; der Server kennt nur den Niesort.
 *
 * Zustandsautomat ohne React/DOM wie die Pet-Steuerungen: `tick` pro Frame,
 * danach `darstellung()`. Sprite: die Baby-Fledermaus (s1) der Vampir-Fledermaus,
 * halb so groß und dunkel-violett leuchtend (pets.css `.pet-flattermaus`).
 */

import type { Masse, Quelle, Rechteck, Umgebung } from "./bewegung";

/** Rahmen der Baby-Fledermaus (frontend/public/pets/fledermaus/s1, fledermausstufen.ts). */
export const FLATTERMAUS_PX = { breite: 42, hoehe: 44, griff: 1 } as const;
/** Gegenüber dem Pet etwas über halb so groß (Annahme Neko — Mini-Fledermäuse). */
export const FLATTERMAUS_SKALA = 0.6;
export const FLATTERMAUS_TAKT = {
  flattern: { frames: 8, ms: 55 },
  haengen: { frames: 24, ms: 110 },
  taumeln: { frames: 8, ms: 60 },
} as const;

/** Annahmen Neko: Tempo, Hängedauer, Umwege beim Herumflattern. */
const FLATTER_PX_S = 190;
const FLUCHT_PX_S = 430;
const HAENGEN_MS: [number, number] = [6_000, 25_000];
const AUSSTOSS_MS = 650;
/** Gepackt, aber die Tentakel lässt los (Bärbel wurde gepackt): wieder frei. */
const LOSGELASSEN_MS = 300;
const VERKOHLT_FALL_MS = 1100;
const VERPUFFEN_MS = 450;

type Zustand = "ausstoss" | "flattern" | "haengen" | "fliehen" | "gepackt" | "getroffen" | "verpufft";

/** Hängeplatz: Unterkante einer Fläche (Quelle) oder der obere Bildschirmrand (null). */
type Ort = { q: Quelle | null; anteil: number };

export interface FlattermausBild {
  left: number;
  top: number;
  breite: number;
  hoehe: number;
  animation: keyof typeof FLATTERMAUS_TAKT;
  frame: number;
  transform: string;
  /** 0..1: vom Blitz verkohlt. */
  verkohlt: number;
  deckkraft: number;
  /** transform-origin: beim Hängen pendelt sie um die Krallen. */
  ursprung: string;
}

export class FlattermausFlug {
  private x: number;
  private y: number;
  private zustand: Zustand;
  private ort: Ort | null = null;
  private ziel = { x: 0, y: 0 };
  private umwege = 0;
  private bis = 0;
  private vx = 0;
  private vy = 0;
  private dreh = 0;
  private flip = false;
  private t0: number;
  private phase: number;
  private zustandSeit: number;
  private gepacktZuletzt = 0;
  private schnell = false;
  private u: Umgebung;
  private zufall: () => number;
  private s: () => number;
  private weg: () => void;

  /**
   * (mx, my) = Mitte in Bildschirm-Pixeln. `frisch` = gerade ausgeniest: sie
   * schießt aus dem Buch heraus, sonst flattert sie gleich los zu einem Platz.
   */
  constructor(mx: number, my: number, frisch: boolean, jetzt: number, u: Umgebung, s: () => number, weg: () => void) {
    this.u = u;
    this.zufall = u.zufall;
    this.s = s;
    this.weg = weg;
    const { bw, bh } = this.masse();
    this.x = mx - bw / 2;
    this.y = my - bh / 2;
    this.t0 = jetzt;
    this.phase = this.zufall() * Math.PI * 2;
    this.zustandSeit = jetzt;
    if (frisch) {
      // Aus dem Buch geprustet: schräg nach oben in irgendeine Richtung.
      const w = ((-160 + this.zufall() * 140) * Math.PI) / 180;
      const v = 380 + this.zufall() * 320;
      this.vx = Math.cos(w) * v;
      this.vy = Math.sin(w) * v;
      this.dreh = (this.zufall() - 0.5) * 720;
      this.zustand = "ausstoss";
    } else {
      this.zustand = "flattern";
      this.losflattern(jetzt, 0);
    }
  }

  setzeUmgebung(u: Umgebung) {
    this.u = u;
  }

  masse(): Masse {
    const k = this.s() * FLATTERMAUS_SKALA;
    return { bw: FLATTERMAUS_PX.breite * k, bh: FLATTERMAUS_PX.hoehe * k, fuss: 0, maulX: 0, maulY: 0, feuerLaenge: 0 };
  }

  // ── Was Bärbel über sie wissen muss (treffen.ts `flattermaeuse`) ─────────

  mitte() {
    const { bw, bh } = this.masse();
    // Hängend: der Körper sitzt unter den Krallen, etwa im oberen Drittel des Rahmens.
    if (this.zustand === "haengen") return { x: this.x + bw / 2, y: this.y + bh * 0.4 };
    return { x: this.x + bw / 2, y: this.y + bh / 2 };
  }

  haengt() {
    return this.zustand === "haengen";
  }

  frei() {
    return this.zustand !== "gepackt" && this.zustand !== "getroffen" && this.zustand !== "verpufft";
  }

  /** Jemand kommt (Bärbel, ein Finger) — schnell weg, weit weg von (x, y). */
  bedroht(jetzt: number, x: number, y: number) {
    if (!this.frei()) return;
    const kandidaten = Array.from({ length: 6 }, () => this.haengePlatz());
    let bester: { ort: Ort; d: number } | null = null;
    for (const ort of kandidaten) {
      const p = this.ortPunkt(ort);
      if (!p) continue;
      const d = Math.hypot(p.x - x, p.y - y);
      if (!bester || d > bester.d) bester = { ort, d };
    }
    this.ort = bester?.ort ?? null;
    this.umwege = 0;
    this.schnell = true;
    this.zustand = "fliehen";
    this.zustandSeit = jetzt;
    if (!this.ort) this.ziel = this.zufallsPunkt();
  }

  /** Tentakel greift zu. true = erwischt; ab jetzt hält die Komponente sie an der Spitze. */
  packen(jetzt: number): boolean {
    if (!this.frei()) return false;
    this.zustand = "gepackt";
    this.zustandSeit = jetzt;
    this.gepacktZuletzt = jetzt;
    return true;
  }

  /** Die Komponente meldet pro Frame, ob die Tentakel sie noch hält. */
  gehalten(jetzt: number, ja: boolean) {
    if (this.zustand !== "gepackt") return;
    if (ja) this.gepacktZuletzt = jetzt;
    else if (jetzt - this.gepacktZuletzt > LOSGELASSEN_MS) {
      // Bärbel wurde mitten im Griff gepackt: die Maus kommt frei und flieht.
      this.zustand = "flattern";
      this.bedroht(jetzt, this.x, this.y);
    }
  }

  /** Vom Blitz getroffen: verkohlt, trudelt, verpufft — dann ist die Spur weg. */
  getroffen(jetzt: number) {
    if (this.zustand === "getroffen" || this.zustand === "verpufft") return;
    this.zustand = "getroffen";
    this.zustandSeit = jetzt;
    this.vx = (this.zufall() - 0.5) * 120;
    this.vy = -160;
    this.dreh = 0;
  }

  // ── Plätze ──────────────────────────────────────────────────────────────

  private zufallsPunkt() {
    const { bw, bh } = this.masse();
    const links = this.u.links ?? 0;
    return {
      x: links + this.zufall() * Math.max(10, this.u.breite - links - bw),
      y: this.u.hoehe * 0.04 + this.zufall() * Math.max(10, this.u.hoehe * 0.7 - bh),
    };
  }

  /** Unterkante einer Fläche (Text, Knöpfe, Kacheln, Popups) oder der obere Rand. */
  private haengePlatz(): Ort {
    const { bw, bh } = this.masse();
    const z = this.zufall;
    const kandidaten = this.u
      .flaechen()
      .filter((f) => f.r.right - f.r.left >= bw * 0.6 && f.r.bottom > 16 && f.r.bottom < this.u.hoehe - bh * 1.2);
    if (kandidaten.length && z() < 0.8) {
      const f = kandidaten[Math.floor(z() * kandidaten.length)];
      return { q: f.q, anteil: 0.15 + z() * 0.7 };
    }
    return { q: null, anteil: 0.06 + z() * 0.88 };
  }

  private ortRechteck(ort: Ort): Rechteck | null {
    if (ort.q) return ort.q.rechteck();
    return { left: this.u.links ?? 0, right: this.u.breite, top: -20, bottom: 0 };
  }

  /** Wo der Rahmen beim Hängen steht: Krallen an der Unterkante. */
  private ortPunkt(ort: Ort) {
    const r = this.ortRechteck(ort);
    if (!r) return null;
    const { bw } = this.masse();
    const k = this.s() * FLATTERMAUS_SKALA;
    const mx = r.left + (r.right - r.left) * ort.anteil;
    return {
      x: Math.min(Math.max(mx - bw / 2, (this.u.links ?? 0) - bw * 0.1), this.u.breite - bw * 0.9),
      y: r.bottom - FLATTERMAUS_PX.griff * k,
    };
  }

  /** Neuer Hängeplatz, vorher 0–`maxUmwege` Schlenker durchs Bild. */
  private losflattern(jetzt: number, maxUmwege = 2) {
    this.ort = this.haengePlatz();
    this.umwege = Math.floor(this.zufall() * (maxUmwege + 1));
    this.schnell = false;
    if (this.umwege > 0) this.ziel = this.zufallsPunkt();
    this.zustand = "flattern";
    this.zustandSeit = jetzt;
  }

  // ── Takt ────────────────────────────────────────────────────────────────

  tick(jetzt: number, dt: number) {
    const { bh } = this.masse();
    switch (this.zustand) {
      case "ausstoss": {
        const bremse = Math.exp(-2.6 * dt);
        this.vx *= bremse;
        this.vy *= bremse;
        this.x += this.vx * dt;
        this.y += this.vy * dt;
        this.dreh *= Math.exp(-5 * dt);
        if (jetzt - this.zustandSeit > AUSSTOSS_MS) {
          this.dreh = 0;
          this.losflattern(jetzt);
        }
        break;
      }
      case "flattern":
      case "fliehen": {
        // Umwege: erst ein paar Schlenker, dann zum Hängeplatz.
        let ziel = this.ziel;
        if (this.umwege <= 0 && this.ort) {
          const p = this.ortPunkt(this.ort);
          if (!p) {
            this.losflattern(jetzt, 0);
            break;
          }
          ziel = p;
        }
        const dx = ziel.x - this.x;
        const dy = ziel.y - this.y;
        const d = Math.hypot(dx, dy);
        const schritt = (this.schnell ? FLUCHT_PX_S : FLATTER_PX_S) * dt;
        if (Math.abs(dx) > 4) this.flip = dx < 0;
        if (d <= schritt) {
          this.x = ziel.x;
          this.y = ziel.y;
          if (this.umwege > 0) {
            this.umwege -= 1;
            this.ziel = this.zufallsPunkt();
          } else if (this.ort) {
            this.zustand = "haengen";
            this.zustandSeit = jetzt;
            this.schnell = false;
            this.bis = jetzt + HAENGEN_MS[0] + this.zufall() * (HAENGEN_MS[1] - HAENGEN_MS[0]);
          } else this.losflattern(jetzt);
        } else {
          this.x += (dx / d) * schritt;
          this.y += (dy / d) * schritt;
        }
        break;
      }
      case "haengen": {
        const p = this.ort ? this.ortPunkt(this.ort) : null;
        if (!p) {
          // Kante weg (Popup zu, gescrollt): loslassen und weiterflattern.
          this.losflattern(jetzt, 1);
          break;
        }
        this.x = p.x;
        this.y = p.y;
        if (jetzt > this.bis) this.losflattern(jetzt);
        break;
      }
      case "getroffen": {
        const t = jetzt - this.zustandSeit;
        this.vy += 900 * dt;
        this.x += this.vx * dt;
        this.y = Math.min(this.u.hoehe - bh * 0.6, this.y + this.vy * dt);
        this.dreh += 540 * dt;
        if (t > VERKOHLT_FALL_MS) {
          this.zustand = "verpufft";
          this.zustandSeit = jetzt;
        }
        break;
      }
      case "verpufft":
        if (jetzt - this.zustandSeit > VERPUFFEN_MS) {
          this.weg();
          this.zustandSeit = Number.POSITIVE_INFINITY; // nur einmal melden
        }
        break;
      default:
        break;
    }
  }

  /** `halt` = Mitte an der Tentakelspitze, solange sie gepackt ist. */
  darstellung(jetzt: number, halt: { x: number; y: number; skala: number } | null): FlattermausBild {
    const { bw, bh } = this.masse();
    const sek = (jetzt - this.t0) / 1000;
    let left = this.x;
    let top = this.y;
    let animation: FlattermausBild["animation"] = "flattern";
    let rot = 0;
    let zoom = 1;
    let verkohlt = 0;
    let deckkraft = 1;
    let ursprung = "50% 50%";
    switch (this.zustand) {
      case "haengen":
        animation = "haengen";
        // Pendelt leicht an den Krallen.
        rot = Math.sin(sek * 2 * Math.PI * 0.45 + this.phase) * 5;
        ursprung = `50% ${FLATTERMAUS_PX.griff * (bh / FLATTERMAUS_PX.hoehe)}px`;
        break;
      case "flattern":
      case "fliehen":
        // Fledermaus-Zickzack: auf und ab und etwas seitlich, im Flügeltakt.
        top += Math.sin(sek * 2 * Math.PI * (this.schnell ? 4.2 : 2.6) + this.phase) * 5;
        left += Math.sin(sek * 2 * Math.PI * 1.1 + this.phase) * 4;
        rot = Math.sin(sek * 2 * Math.PI * 1.3 + this.phase) * 8;
        break;
      case "ausstoss":
        rot = this.dreh;
        break;
      case "gepackt":
        animation = "taumeln";
        if (halt) {
          left = halt.x - bw / 2;
          top = halt.y - bh / 2;
          zoom = halt.skala;
        }
        rot = Math.sin(jetzt / 40) * 12; // zappelt
        break;
      case "getroffen": {
        animation = "taumeln";
        rot = this.dreh;
        verkohlt = Math.min(1, (jetzt - this.zustandSeit) / 180);
        break;
      }
      case "verpufft": {
        animation = "taumeln";
        const k = Math.min(1, (jetzt - this.zustandSeit) / VERPUFFEN_MS);
        verkohlt = 1;
        deckkraft = 1 - k;
        zoom = 1 + k * 0.8;
        rot = this.dreh;
        break;
      }
    }
    const takt = FLATTERMAUS_TAKT[animation];
    // Ausgeniest und auf der Flucht schlagen die Flügel schneller.
    const ms = this.zustand === "fliehen" || this.zustand === "ausstoss" ? takt.ms * 0.6 : takt.ms;
    const frame = Math.floor((jetzt - this.t0) / ms + this.phase * 3) % takt.frames;
    const spiegel = this.flip && animation === "flattern" ? " scaleX(-1)" : "";
    return {
      left,
      top,
      breite: bw,
      hoehe: bh,
      animation,
      frame,
      transform: `rotate(${rot.toFixed(1)}deg) scale(${zoom.toFixed(3)})${spiegel}`,
      verkohlt,
      deckkraft,
      ursprung,
    };
  }
}
