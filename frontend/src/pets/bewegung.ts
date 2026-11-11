/**
 * Bewegungslogik des Critter-Pets (Mark, 11.11.2026: „nicht nur unten am
 * Rand rumlaufen, sondern auch wo rauf klettern oder springen“).
 *
 * Reiner Zustandsautomat ohne React: die Komponente ruft `tick` pro Frame
 * und liest danach `darstellung()`. Die Welt kommt über `Umgebung` herein
 * (Bildschirmgröße, offene Popups) — so bleibt die Logik vom DOM getrennt.
 *
 * Orte: Boden (unterer Bildschirmrand), Plattform (Oberkante eines offenen
 * Popups), Wand (Seite eines Popups oder Bildschirmrand, beim Klettern).
 * Raus läuft er nur über den Boden — so wandert er zum nächsten Tablet.
 */

export type Animation = "idle" | "lauf" | "freuen" | "sprung" | "schlafen";

export interface Masse {
  /** Box-Breite/-Höhe des Sprites in Bildschirm-Pixeln. */
  bw: number;
  bh: number;
  /** Leerer Rand unter den Füßen im Sprite (Bildschirm-Pixel). */
  fuss: number;
}

export interface Rechteck {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

export interface Umgebung {
  breite: number;
  hoehe: number;
  /** Popups, auf die er klettern/springen kann. */
  popups: () => { el: Element; r: Rechteck }[];
  /** Aktuelles Rechteck eines Popups, null wenn es zu ist. */
  rechteckVon: (el: Element) => Rechteck | null;
  zufall: () => number;
}

type Ort = { art: "boden" } | { art: "plattform"; el: Element };
/** Wo die Wand vom Pet aus gesehen ist. */
type Wand = { x: number; seite: "links" | "rechts"; el: Element | null };

type Zustand =
  | "laufen"
  | "idle"
  | "freuen"
  | "haeufchen"
  | "schlafen"
  | "klettern"
  | "haengen"
  | "sprung"
  | "raus";

interface Sprung {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  t0: number;
  dauer: number;
  bogen: number;
  danach: Ort;
}

export interface Darstellung {
  left: number;
  top: number;
  transform: string;
  animation: Animation;
  animStart: number;
  hockt: boolean;
  schlaeft: boolean;
  /** Kopfposition für Zzz/Herzen. */
  kopfX: number;
  kopfY: number;
}

export type Meldung =
  | { typ: "raus"; seite: "links" | "rechts" }
  | { typ: "haeufchen"; x: number; y: number };

const TEMPO_PX_S = 45;
const KLETTER_PX_S = 45;
/** Höchster Satz nach oben; höhere Popups werden erklettert. */
const SPRUNG_MAX_PX = 240;

export class PetBewegung {
  zustand: Zustand = "laufen";
  ort: Ort = { art: "boden" };
  x = 0;
  fussY = 0;
  richtung = 1;
  zielX = 0;
  bis = 0;
  besuchEnde: number;
  haeufchenGemacht = false;
  geschlafen = false;
  rausGemeldet = false;
  nachAnkunft: ((jetzt: number) => void) | null = null;
  sprung: Sprung | null = null;
  wand: Wand | null = null;
  kletterZielY = 0;
  cx = 0;
  cy = 0;
  animation: Animation = "lauf";
  animStart = 0;

  private masse: () => Masse;
  private u: Umgebung;
  private melden: (m: Meldung) => void;

  constructor(
    masse: () => Masse,
    u: Umgebung,
    seite: "links" | "rechts",
    jetzt: number,
    melden: (m: Meldung) => void,
  ) {
    this.masse = masse;
    this.u = u;
    this.melden = melden;
    const { bw } = masse();
    this.besuchEnde = jetzt + this.zw(40_000, 120_000);
    this.fussY = u.hoehe;
    // Reinkommen von der Seite, die der Server sagt.
    if (seite === "links") {
      this.x = -bw;
      this.laufeZu(this.zw(0.1, 0.5) * u.breite);
    } else {
      this.x = u.breite;
      this.laufeZu(this.zw(0.4, 0.85) * u.breite - bw);
    }
    this.animStart = jetzt;
  }

  private zw(min: number, max: number) {
    return min + this.u.zufall() * (max - min);
  }

  private klemmeX(x: number) {
    return Math.min(Math.max(x, 0), Math.max(0, this.u.breite - this.masse().bw));
  }

  setzeUmgebung(u: Umgebung) {
    this.u = u;
  }

  // ── Handlungen ──────────────────────────────────────────────────────────

  private laufeZu(x: number, danach: ((jetzt: number) => void) | null = null) {
    this.zielX = x;
    this.richtung = x >= this.x ? 1 : -1;
    this.zustand = "laufen";
    this.nachAnkunft = danach;
  }

  private springe(x1: number, y1: number, danach: Ort, jetzt: number) {
    const dx = x1 - this.x;
    const dy = this.fussY - y1; // > 0 = nach oben
    if (Math.abs(dx) > 2) this.richtung = dx > 0 ? 1 : -1;
    this.sprung = {
      x0: this.x,
      y0: this.fussY,
      x1,
      y1,
      t0: jetzt,
      dauer: 450 + Math.abs(dy) * 1.2 + Math.abs(dx) * 0.8,
      bogen: dy > 0 ? dy / 2 + 40 : 30,
      danach,
    };
    this.zustand = "sprung";
  }

  private fallen(jetzt: number) {
    this.springe(this.x, this.u.hoehe, { art: "boden" }, jetzt);
    if (this.sprung) this.sprung.bogen = 8;
  }

  private klettere(wand: Wand, zielY: number) {
    const { bw, bh, fuss } = this.masse();
    this.wand = wand;
    this.kletterZielY = zielY;
    this.cx = wand.seite === "rechts" ? wand.x - bh / 2 + fuss : wand.x + bh / 2 - fuss;
    this.cy = this.fussY - bw / 2;
    this.zustand = "klettern";
  }

  /** Oben am Popup angekommen: auf die Oberkante steigen. */
  private aufsteigen(wand: Wand, r: Rechteck, jetzt: number) {
    const { bw } = this.masse();
    this.ort = { art: "plattform", el: wand.el! };
    this.fussY = r.top;
    if (wand.seite === "rechts") {
      this.x = r.left - bw * 0.2;
      this.richtung = 1;
    } else {
      this.x = r.right - bw * 0.8;
      this.richtung = -1;
    }
    this.wand = null;
    this.zustand = "idle";
    this.bis = jetzt + this.zw(800, 2000);
  }

  /** Von der Wand abstoßen und auf den Boden springen. */
  private wandAbsprung(jetzt: number) {
    const { bw, bh } = this.masse();
    const wand = this.wand!;
    this.x = this.cx - bw / 2;
    this.fussY = this.cy + bh / 2;
    this.richtung = wand.seite === "links" ? 1 : -1;
    this.wand = null;
    this.ort = { art: "boden" };
    this.springe(this.klemmeX(this.x + this.richtung * this.zw(80, 200)), this.u.hoehe, { art: "boden" }, jetzt);
  }

  streicheln(jetzt: number): boolean {
    if (this.zustand === "raus" || this.zustand === "sprung" || this.zustand === "klettern") return false;
    if (this.zustand === "haengen") return true; // Herzchen ja, loslassen nein
    this.zustand = "freuen";
    this.bis = jetzt + 1600;
    return true;
  }

  // ── Entscheidungen ──────────────────────────────────────────────────────

  private entscheide(jetzt: number) {
    const { bw } = this.masse();
    const u = this.u;
    const w = u.zufall();

    if (this.ort.art === "plattform") {
      const r = u.rechteckVon(this.ort.el);
      if (!r) return this.fallen(jetzt);
      const ende = jetzt >= this.besuchEnde;
      if (!ende && !this.geschlafen && w < 0.3) {
        this.zustand = "schlafen";
        this.geschlafen = true;
        this.bis = jetzt + this.zw(6000, 14000);
        return;
      }
      if (!ende && w < 0.65) {
        this.laufeZu(this.zw(r.left - bw * 0.2, r.right - bw * 0.8));
        return;
      }
      // Runter auf den Boden, neben das Popup.
      const rechts = u.zufall() < 0.5;
      const zx = rechts ? r.right + this.zw(10, 80) : r.left - bw - this.zw(10, 80);
      this.springe(this.klemmeX(zx), u.hoehe, { art: "boden" }, jetzt);
      return;
    }

    // Boden
    if (jetzt >= this.besuchEnde) {
      this.zustand = "raus";
      this.richtung = u.zufall() < 0.5 ? -1 : 1;
      this.zielX = this.richtung > 0 ? u.breite + 4 : -bw - 4;
      return;
    }
    if (!this.haeufchenGemacht && w < 0.12) {
      this.zustand = "haeufchen";
      this.bis = jetzt + 1800;
      return;
    }
    const popups = u.popups();
    if (popups.length && w < 0.5) {
      const { el, r } = popups[Math.floor(u.zufall() * popups.length)];
      const hoch = u.hoehe - r.top;
      const vonLinks = this.x + bw / 2 < (r.left + r.right) / 2;
      const springen = hoch <= SPRUNG_MAX_PX * 0.6 || (hoch <= SPRUNG_MAX_PX && u.zufall() < 0.5);
      if (springen) {
        const absprung = this.klemmeX(vonLinks ? r.left - bw - 30 : r.right + 30);
        const landung = vonLinks ? r.left - bw * 0.1 : r.right - bw * 0.9;
        this.laufeZu(absprung, (j) => this.springe(landung, r.top, { art: "plattform", el }, j));
      } else {
        // An der Seite hochklettern: Wand ist rechts vom Pet, wenn er links davon steht.
        const wand: Wand = vonLinks ? { x: r.left, seite: "rechts", el } : { x: r.right, seite: "links", el };
        const start = this.klemmeX(vonLinks ? r.left - bw * 0.6 : r.right - bw * 0.4);
        this.laufeZu(start, () => this.klettere(wand, r.top));
      }
      return;
    }
    if (w < 0.62) {
      // Bildschirmrand hochklettern, oben kurz hängen, dann abspringen.
      const links = u.zufall() < 0.5;
      const wand: Wand = links ? { x: 0, seite: "links", el: null } : { x: u.breite, seite: "rechts", el: null };
      this.laufeZu(links ? 0 : this.klemmeX(u.breite), () => this.klettere(wand, this.zw(0.3, 0.6) * u.hoehe));
      return;
    }
    if (w < 0.74) {
      // Kleiner Hüpfer.
      this.springe(this.klemmeX(this.x + this.richtung * this.zw(30, 70)), u.hoehe, { art: "boden" }, jetzt);
      return;
    }
    this.laufeZu(this.zw(0, Math.max(0, u.breite - bw)));
  }

  // ── Takt ────────────────────────────────────────────────────────────────

  tick(jetzt: number, dt: number) {
    const { bw, bh } = this.masse();
    const u = this.u;

    // Boden folgt der Fenstergröße, Plattform dem Popup.
    if (this.zustand !== "sprung" && this.zustand !== "klettern" && this.zustand !== "haengen") {
      if (this.ort.art === "boden") {
        this.fussY = u.hoehe;
      } else {
        const r = u.rechteckVon(this.ort.el);
        if (!r) {
          this.ort = { art: "boden" };
          this.fallen(jetzt);
        } else {
          this.fussY = r.top;
          const min = r.left - bw * 0.25;
          const max = r.right - bw * 0.75;
          this.x = Math.min(Math.max(this.x, min), max);
          this.zielX = Math.min(Math.max(this.zielX, min), max);
        }
      }
    }

    switch (this.zustand) {
      case "laufen":
      case "raus": {
        this.x += TEMPO_PX_S * dt * this.richtung;
        const angekommen = this.richtung > 0 ? this.x >= this.zielX : this.x <= this.zielX;
        if (angekommen) {
          this.x = this.zielX;
          if (this.zustand === "raus") {
            if (!this.rausGemeldet) {
              this.rausGemeldet = true;
              this.melden({ typ: "raus", seite: this.richtung > 0 ? "rechts" : "links" });
            }
          } else if (this.nachAnkunft) {
            const weiter = this.nachAnkunft;
            this.nachAnkunft = null;
            this.zustand = "idle";
            weiter(jetzt);
          } else {
            this.zustand = "idle";
            this.bis = jetzt + this.zw(2000, 6000);
          }
        }
        break;
      }
      case "sprung": {
        const s = this.sprung!;
        let t = (jetzt - s.t0) / s.dauer;
        if (s.danach.art === "plattform") {
          const r = u.rechteckVon(s.danach.el);
          if (!r) {
            s.danach = { art: "boden" };
            s.y1 = u.hoehe;
          } else s.y1 = r.top;
        } else s.y1 = u.hoehe;
        if (t >= 1) {
          t = 1;
          this.x = s.x1;
          this.fussY = s.y1;
          this.ort = s.danach;
          this.sprung = null;
          this.zustand = "idle";
          this.bis = jetzt + this.zw(600, 1500);
        } else {
          this.x = s.x0 + (s.x1 - s.x0) * t;
          this.fussY = s.y0 + (s.y1 - s.y0) * t - s.bogen * 4 * t * (1 - t);
        }
        break;
      }
      case "klettern": {
        const wand = this.wand!;
        if (wand.el) {
          const r = u.rechteckVon(wand.el);
          if (!r) {
            this.wandAbsprung(jetzt);
            break;
          }
          this.kletterZielY = r.top;
        }
        this.cy -= KLETTER_PX_S * dt;
        if (wand.el) {
          // Kopf über der Kante → hinaufsteigen.
          if (this.cy - bw / 2 <= this.kletterZielY - bh * 0.4) {
            this.aufsteigen(wand, u.rechteckVon(wand.el)!, jetzt);
          }
        } else if (this.cy <= this.kletterZielY) {
          this.zustand = "haengen";
          this.bis = jetzt + this.zw(1500, 3500);
        }
        break;
      }
      case "haengen":
        if (jetzt >= this.bis) this.wandAbsprung(jetzt);
        break;
      case "haeufchen":
        if (jetzt >= this.bis) {
          const { fuss } = this.masse();
          // Liegt hinter dem Schwanz.
          const schwanz = this.richtung > 0 ? this.x + fuss : this.x + bw - fuss;
          this.melden({ typ: "haeufchen", x: schwanz / u.breite, y: 1 });
          this.haeufchenGemacht = true;
          this.zustand = "idle";
          this.bis = jetzt + 1500;
        }
        break;
      case "idle":
      case "freuen":
      case "schlafen":
        if (jetzt >= this.bis) this.entscheide(jetzt);
        break;
    }

    const anim: Animation =
      this.zustand === "laufen" || this.zustand === "raus" || this.zustand === "klettern"
        ? "lauf"
        : this.zustand === "sprung"
          ? "sprung"
          : this.zustand === "freuen"
            ? "freuen"
            : this.zustand === "schlafen"
              ? "schlafen"
              : "idle";
    if (anim !== this.animation) {
      this.animation = anim;
      this.animStart = jetzt;
    }
  }

  darstellung(jetzt: number): Darstellung {
    const { bw, bh, fuss } = this.masse();
    const basis = {
      animation: this.animation,
      animStart: this.animStart,
      hockt: this.zustand === "haeufchen",
      schlaeft: this.zustand === "schlafen",
    };
    if ((this.zustand === "klettern" || this.zustand === "haengen") && this.wand) {
      // Kopf nach oben, Füße an der Wand.
      const rechts = this.wand.seite === "rechts";
      return {
        ...basis,
        left: this.cx - bw / 2,
        top: this.cy - bh / 2,
        transform: rechts ? "rotate(-90deg)" : "rotate(90deg) scaleX(-1)",
        kopfX: this.cx,
        kopfY: this.cy - bw / 2,
      };
    }
    let transform = this.richtung < 0 ? "scaleX(-1)" : "";
    if (this.zustand === "sprung" && this.sprung) {
      const t = Math.min(1, (jetzt - this.sprung.t0) / this.sprung.dauer);
      // Nase hoch beim Steigen, runter beim Fallen.
      transform += ` rotate(${(-18 * (1 - 2 * t)).toFixed(1)}deg)`;
    }
    const kopfRechts = this.richtung > 0;
    return {
      ...basis,
      left: this.x,
      top: this.fussY - bh + fuss,
      transform: transform || "none",
      kopfX: this.x + (kopfRechts ? bw * 0.8 : bw * 0.2),
      kopfY: this.fussY - bh + fuss,
    };
  }
}
