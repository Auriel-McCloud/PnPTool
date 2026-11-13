/**
 * KI-Begleiter als Pet (Mark, 13.11.2026): „Datenwolke oder cooles, Licht
 * pulsierendes, manchmal verschiedene Formen oder Gestalten annehmendes Wesen …
 * ein Begleiter, der wachsen kann“. Marks Wahl aus den Entwürfen: A Datenwolke
 * und B Lichtkern — „es kann gerne zwischen den 2 Gestalten wechseln und auch
 * verschiedene Farben und Gestalten annehmen“.
 *
 * Keine Sprites: die KI ist ein Schwarm aus Teilchen, der auf eine kleine
 * Leinwand gezeichnet wird. Jedes Teilchen hat drei Plätze — in der Wolke, am
 * Lichtkern (Hof oder Ring) und in der gerade angenommenen Gestalt — und
 * federt zum jeweils gültigen. So fließen Wolke, Kern und Gestalten ineinander.
 * Entwurf und Tafeln: docs/assets/critter-pet/ki_entwurf.py.
 */

/** Kantenlänge der Leinwand in KI-Pixeln. */
export const KI_G = 64;
const M = KI_G / 2;

type RGB = readonly [number, number, number];
export interface Palette {
  kern: RGB;
  hell: RGB;
  mittel: RGB;
  dunkel: RGB;
  tief: RGB;
  akzent: RGB;
}

export const PALETTEN = {
  cyan: { kern: [255, 255, 255], hell: [170, 245, 255], mittel: [60, 200, 245], dunkel: [34, 112, 205], tief: [22, 58, 128], akzent: [255, 90, 200] },
  magenta: { kern: [255, 255, 255], hell: [255, 190, 245], mittel: [245, 90, 215], dunkel: [170, 50, 170], tief: [90, 28, 110], akzent: [90, 230, 255] },
  gruen: { kern: [255, 255, 255], hell: [200, 255, 190], mittel: [80, 235, 120], dunkel: [30, 150, 80], tief: [16, 80, 50], akzent: [255, 220, 90] },
  bernstein: { kern: [255, 255, 255], hell: [255, 236, 170], mittel: [255, 180, 60], dunkel: [205, 105, 30], tief: [120, 55, 20], akzent: [120, 220, 255] },
  violett: { kern: [255, 255, 255], hell: [225, 200, 255], mittel: [160, 110, 250], dunkel: [100, 60, 200], tief: [52, 30, 120], akzent: [120, 255, 200] },
  rot: { kern: [255, 255, 255], hell: [255, 200, 180], mittel: [250, 80, 70], dunkel: [180, 36, 50], tief: [96, 20, 36], akzent: [255, 230, 120] },
} as const satisfies Record<string, Palette>;
export type KiFarbe = keyof typeof PALETTEN;
export const KI_FARBEN = Object.keys(PALETTEN) as KiFarbe[];

const AUGE = "rgb(10,18,44)";

/** Gestalten, die sie annimmt: `#` Körper, `o` Auge/Loch (glüht weiß). Dazu die
 *  Farbe, die zu der Gestalt passt. */
export const KI_GESTALTEN: Record<string, { maske: string[]; farbe: KiFarbe }> = {
  katze: {
    farbe: "cyan",
    maske: [
      "#.........#",
      "##.......##",
      "###.....###",
      "###########",
      "###########",
      "##o#####o##",
      "##o#####o##",
      "###########",
      "#####o#####",
      ".#########.",
      "..#######..",
    ],
  },
  totenkopf: {
    farbe: "gruen",
    maske: [
      "..#######..",
      ".#########.",
      "###########",
      "###########",
      "#oo#####oo#",
      "#oo#####oo#",
      "#####o#####",
      ".#########.",
      "..#######..",
      "..#.#.#.#..",
      "..#.#.#.#..",
    ],
  },
  herz: {
    farbe: "magenta",
    maske: [
      ".###...###.",
      "#####.#####",
      "###########",
      "###########",
      "###########",
      ".#########.",
      "..#######..",
      "...#####...",
      "....###....",
      ".....#.....",
    ],
  },
  schluessel: {
    farbe: "bernstein",
    maske: [
      ".###.........",
      "#####........",
      "##o##########",
      "##o##########",
      "#####...#.##.",
      ".###....#.##.",
    ],
  },
  pfeil: {
    farbe: "cyan",
    maske: [
      "......#......",
      "......##.....",
      "#########....",
      "##########...",
      "###########..",
      "##########...",
      "#########....",
      "......##.....",
      "......#......",
    ],
  },
  warnung: {
    farbe: "rot",
    maske: [
      ".....#.....",
      "....###....",
      "....###....",
      "...##o##...",
      "...##o##...",
      "..###o###..",
      "..#######..",
      ".####o####.",
      ".#########.",
      "###########",
    ],
  },
  stern: {
    farbe: "bernstein",
    maske: [
      ".....#.....",
      ".....#.....",
      "....###....",
      "###########",
      ".#########.",
      "..#######..",
      "..#######..",
      ".####.####.",
      ".##.....##.",
      "#.........#",
    ],
  },
  blitz: {
    farbe: "violett",
    maske: [
      "....####.",
      "...####..",
      "..####...",
      ".#######.",
      "....###..",
      "...###...",
      "..###....",
      ".##......",
      "#........",
    ],
  },
  smiley: {
    farbe: "gruen",
    maske: [
      "..#######..",
      ".#########.",
      "###########",
      "##oo###oo##",
      "##oo###oo##",
      "###########",
      "#o#######o#",
      "##o#####o##",
      "###ooooo###",
      ".#########.",
      "..#######..",
    ],
  },
};
export const KI_GESTALT_NAMEN = Object.keys(KI_GESTALTEN);

export type KiForm = "wolke" | "kern";

/** Maße je Gestalt-Stufe (Funke, Keim, Geist, Wesen, Entität); dazwischen wird
 *  mit jedem der 12 Wachstumsschritte überblendet. */
const TEILCHEN = [5, 14, 28, 46, 70];
const RADIUS = [3, 6, 9, 12.5, 15.5];
const KERN_R = [1, 2.2, 3.2, 4.2, 5.2];
const STRAHL = [2, 3, 4, 5, 6];
const ZIFFERN = [0, 0, 0, 3, 5];
/** Ringe um den Lichtkern: (Zuschlag auf den Kernradius, Höhe, Neigung in Grad). */
const RINGE: [number, number, number][][] = [
  [],
  [],
  [[7, 2.6, -18]],
  [[8, 3.0, -38], [8, 3.0, 38]],
  [[15, 4.6, 0], [12, 3.6, 62], [12, 3.6, -62]],
];

export interface KiMasse {
  /** Gestalt-Stufe 0–4 (Funke … Entität). */
  stufe: number;
  n: number;
  r: number;
  rc: number;
  strahl: number;
  ziffern: number;
  ringe: [number, number, number][];
  augen: boolean;
  netz: boolean;
  bahn: boolean;
  /** Vergrößerung der Gestalt-Masken. */
  gestaltMass: number;
}

export function kiMasse(schritt: number): KiMasse {
  const g = Math.min(4, Math.max(0, schritt / 3));
  const stufe = Math.floor(g);
  const k = g - stufe;
  const mix = (a: number[]) => a[stufe] + ((a[Math.min(4, stufe + 1)] ?? a[stufe]) - a[stufe]) * k;
  return {
    stufe,
    n: Math.round(mix(TEILCHEN)),
    r: mix(RADIUS),
    rc: mix(KERN_R),
    strahl: mix(STRAHL),
    ziffern: ZIFFERN[stufe],
    ringe: RINGE[stufe],
    augen: stufe >= 1,
    netz: stufe >= 2,
    bahn: stufe >= 4,
    gestaltMass: stufe >= 3 ? 2 : 1,
  };
}

function zufallsquelle(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Plätze in der Wolke für Radius 1 — immer dieselben, damit sie beim Wachsen
 *  nur dichter wird und nicht jedes Mal neu würfelt. */
const WOLKE: { x: number; y: number; d: number; gross: boolean }[] = (() => {
  const z = zufallsquelle(7);
  const kreise = [
    [0, -0.2, 0.72],
    [-0.7, 0.2, 0.48],
    [0.7, 0.2, 0.48],
  ];
  const aus: { x: number; y: number; d: number; gross: boolean }[] = [];
  while (aus.length < TEILCHEN[4] + 60) {
    const x = (z() * 2 - 1) * 1.25;
    const y = z() * 2 - 1;
    if (!kreise.some(([kx, ky, kr]) => (x - kx) ** 2 + (y - ky) ** 2 <= kr * kr)) continue;
    const d = Math.hypot(x * 0.85, y * 1.2);
    aus.push({ x, y, d, gross: z() < 0.3 && d < 0.8 });
  }
  return aus;
})();

interface Teilchen {
  x: number;
  y: number;
  vx: number;
  vy: number;
  /** Platz in der Wolke (Radius 1) und Helligkeit dort. */
  hx: number;
  hy: number;
  d: number;
  gross: boolean;
  ph: number;
  /** Platz am Lichtkern: Ring-Nummer (−1 = Hof), Winkel, Abstand im Hof. */
  ring: number;
  w: number;
  rad: number;
  /** Platz in der Gestalt (null = keine) und Helligkeit dort. */
  gx: number | null;
  gy: number;
  gd: number;
  /** Nur für eine Gestalt dazugekommen; `stirbt` = kehrt in den Kern zurück. */
  extra: boolean;
  stirbt: boolean;
}

const ZIFFER_BILD: Record<string, string[]> = {
  "0": ["###", "#.#", "#.#", "#.#", "###"],
  "1": [".#.", "##.", ".#.", ".#.", "###"],
};

export class KiWesen {
  masse: KiMasse;
  form: KiForm = "wolke";
  gestalt: string | null = null;
  /** Standby: zieht sich zusammen, Augen zu, leuchtet schwach. */
  schlaf = false;
  /** Liest gerade Daten: von unten strömen Pixel in sie hinein. */
  liest = false;
  /** Blickrichtung −1…1 (Augen wandern einen Pixel mit). */
  blickX = 0;

  private teilchen: Teilchen[] = [];
  private farbVon: Palette = PALETTEN.cyan;
  private farbNach: Palette = PALETTEN.cyan;
  private farbT0 = -1e9;
  farbe: KiFarbe = "cyan";
  private kernR = 0;
  /** 0 = Wolke, 1 = Lichtkern (läuft weich nach). */
  private kernAnteil = 0;
  private pulsBis = 0;
  private glitchBis = 0;
  private blinzelAb: number;
  private ziffern: { z: string; bis: number }[] = [];
  private strom: { x: number; y: number }[] = [];
  private zufall = zufallsquelle(99);

  constructor(schritt: number, jetzt: number) {
    this.masse = kiMasse(schritt);
    this.blinzelAb = jetzt + 2500;
    this.baue();
    for (const p of this.teilchen) {
      p.x = p.hx * this.masse.r;
      p.y = p.hy * this.masse.r;
    }
    this.kernR = this.kernZiel();
  }

  /** Neuer Wachstumsschritt: mehr Teilchen, größer — die alten bleiben, wo sie sind. */
  setzeSchritt(schritt: number, jetzt: number) {
    this.masse = kiMasse(schritt);
    if (this.masse.stufe === 0) this.form = "wolke";
    this.baue();
    if (this.gestalt) this.verteileGestalt(this.gestalt);
    this.pulsBis = jetzt + 900;
  }

  private baue() {
    const m = this.masse;
    const alt = this.teilchen.filter((p) => !p.extra);
    const neu: Teilchen[] = [];
    const ringe = m.ringe.length;
    let jeRing = 0;
    for (let i = 0; i < m.n; i++) if (ringe && i % 3 !== 0) jeRing += 1;
    jeRing = Math.max(1, Math.ceil(jeRing / Math.max(1, ringe)));
    let k = 0;
    for (let i = 0; i < m.n; i++) {
      const h = WOLKE[i];
      const a = alt[i];
      const amRing = ringe > 0 && i % 3 !== 0;
      const ring = amRing ? k % ringe : -1;
      const w = amRing ? (Math.floor(k / ringe) / jeRing) * Math.PI * 2 + ring * 0.7 : (i * 2.399963) % (Math.PI * 2);
      if (amRing) k += 1;
      neu.push({
        x: a?.x ?? 0,
        y: a?.y ?? 0,
        vx: a?.vx ?? 0,
        vy: a?.vy ?? 0,
        hx: h.x,
        hy: h.y,
        d: h.d,
        gross: h.gross,
        ph: i * 1.7,
        ring,
        w,
        rad: 2.5 + (i % 4) * 0.9,
        gx: null,
        gy: 0,
        gd: 0,
        extra: false,
        stirbt: false,
      });
    }
    this.teilchen = neu.concat(this.teilchen.filter((p) => p.extra));
    this.ziffern = Array.from({ length: m.ziffern }, () => ({ z: "0", bis: 0 }));
  }

  private kernZiel() {
    if (this.gestalt) return 0;
    const m = this.masse;
    const r = this.form === "kern" ? m.rc : m.augen ? m.r * 0.42 : 0.6;
    return this.schlaf ? r * 0.75 : r;
  }

  private stoss(kraft: number) {
    for (const p of this.teilchen) {
      const w = this.zufall() * Math.PI * 2;
      p.vx += Math.cos(w) * kraft * (0.4 + this.zufall());
      p.vy += Math.sin(w) * kraft * (0.4 + this.zufall());
    }
  }

  setzeForm(form: KiForm) {
    if (form === this.form || this.masse.stufe === 0) return;
    this.form = form;
    this.stoss(26);
  }

  setzeFarbe(name: KiFarbe, jetzt: number) {
    if (name === this.farbe) return;
    this.farbVon = this.palette(jetzt);
    this.farbNach = PALETTEN[name];
    this.farbT0 = jetzt;
    this.farbe = name;
  }

  /** Gestalt annehmen (null = zurück zu Wolke/Kern). */
  setzeGestalt(name: string | null) {
    if (name === this.gestalt) return;
    this.gestalt = name && KI_GESTALTEN[name] ? name : null;
    for (const p of this.teilchen) {
      p.gx = null;
      if (p.extra) p.stirbt = true;
    }
    if (this.gestalt) this.verteileGestalt(this.gestalt);
    this.stoss(34);
  }

  private verteileGestalt(name: string) {
    const maske = KI_GESTALTEN[name].maske;
    const mass = this.masse.gestaltMass;
    const hh = maske.length;
    const ww = Math.max(...maske.map((z) => z.length));
    const zelle = (i: number, j: number) => maske[j]?.[i] ?? ".";
    const z = zufallsquelle(3);
    const punkte: { x: number; y: number; d: number }[] = [];
    const nurUmriss = this.form === "kern";
    for (let j = 0; j < hh; j++) {
      for (let i = 0; i < ww; i++) {
        const c = zelle(i, j);
        if (c === ".") continue;
        const rand = c === "#" && [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([a, b]) => zelle(i + a, j + b) !== "#");
        for (let a = 0; a < mass; a++) {
          for (let b = 0; b < mass; b++) {
            const x = (i - ww / 2) * mass + a + 0.5;
            const y = (j - hh / 2) * mass + b + 0.5;
            if (c === "o") punkte.push({ x, y, d: -1 });
            else if (rand) punkte.push({ x, y, d: nurUmriss ? 0.2 : 0.5 });
            else if (!nurUmriss && z() < 0.5) punkte.push({ x, y, d: 0.9 });
          }
        }
      }
    }
    // Teilchen und Plätze im Kreis herum zuordnen — dann fließt die Form, statt zu springen.
    const winkel = (x: number, y: number) => Math.atan2(y, x);
    punkte.sort((p, q) => winkel(p.x, p.y) - winkel(q.x, q.y));
    const fest = this.teilchen.filter((p) => !p.stirbt);
    while (fest.length < punkte.length) {
      const p: Teilchen = {
        x: 0, y: 0, vx: 0, vy: 0, hx: 0, hy: 0, d: 0.5, gross: false, ph: fest.length * 1.7,
        ring: -1, w: 0, rad: 2.5, gx: null, gy: 0, gd: 0, extra: true, stirbt: false,
      };
      fest.push(p);
      this.teilchen.push(p);
    }
    const reihe = [...fest].sort((p, q) => winkel(p.x || p.hx, p.y || p.hy) - winkel(q.x || q.hx, q.y || q.hy));
    reihe.forEach((p, i) => {
      const ziel = punkte[Math.floor((i * punkte.length) / reihe.length)];
      p.gx = ziel.x;
      p.gy = ziel.y;
      p.gd = ziel.d;
    });
  }

  /** Kurz aufleuchten und auseinanderstieben (gestreichelt, gewachsen). */
  freude(jetzt: number) {
    this.pulsBis = jetzt + 700;
    this.stoss(22);
  }

  /** Von Feuer, Eis oder Blitz getroffen: Bildstörung. */
  stoerung(jetzt: number) {
    this.glitchBis = jetzt + 1100;
    this.stoss(60);
  }

  /** Sichtbarer Radius in KI-Pixeln (für die Greif-Fläche). */
  radius(): number {
    const m = this.masse;
    if (this.gestalt) return 7 * m.gestaltMass + 2;
    if (this.form === "kern") return m.rc + (m.ringe.length ? m.ringe[0][0] : 5) + 1;
    return Math.max(4, m.r * 1.15 + (m.bahn ? 6 : 0));
  }

  private palette(jetzt: number): Palette {
    const k = Math.min(1, (jetzt - this.farbT0) / 900);
    if (k >= 1) return this.farbNach;
    const mix = (a: RGB, b: RGB): RGB => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
    const v = this.farbVon;
    const n = this.farbNach;
    return {
      kern: mix(v.kern, n.kern),
      hell: mix(v.hell, n.hell),
      mittel: mix(v.mittel, n.mittel),
      dunkel: mix(v.dunkel, n.dunkel),
      tief: mix(v.tief, n.tief),
      akzent: mix(v.akzent, n.akzent),
    };
  }

  /** Farbe des Scheins um sie herum (CSS). */
  schein(jetzt: number): string {
    const c = this.palette(jetzt).mittel;
    return `rgba(${Math.round(c[0])},${Math.round(c[1])},${Math.round(c[2])},${this.schlaf ? 0.4 : 0.85})`;
  }

  /** Wo ein Teilchen gerade hingehört (relativ zur Mitte). */
  private platz(p: Teilchen, t: number): [number, number] {
    if (p.stirbt) return [0, 0];
    if (p.gx !== null) return [p.gx + Math.sin(t * 5 + p.ph) * 0.3, p.gy];
    const m = this.masse;
    const eng = this.schlaf ? 0.55 : 1;
    const tempo = this.schlaf ? 0.25 : 1;
    if (this.form === "kern") {
      if (p.ring >= 0 && m.ringe[p.ring]) {
        const [zu, ry, grad] = m.ringe[p.ring];
        const w = p.w + t * tempo * (p.ring % 2 ? -0.9 : 0.9);
        const x = (m.rc + zu) * Math.cos(w) * eng;
        const y = ry * Math.sin(w) * eng;
        const n = (grad * Math.PI) / 180;
        return [x * Math.cos(n) - y * Math.sin(n), x * Math.sin(n) + y * Math.cos(n)];
      }
      const w = p.w + t * tempo * 1.5;
      const r = (m.rc + p.rad) * eng;
      return [Math.cos(w) * r, Math.sin(w) * r * 0.9];
    }
    const atem = (1 + 0.06 * Math.sin(t * 2.2 * tempo)) * eng;
    return [
      p.hx * m.r * atem + Math.sin(t * 1.3 * tempo + p.ph) * 0.8,
      p.hy * m.r * atem + Math.cos(t * 1.1 * tempo + p.ph * 1.7) * 0.8,
    ];
  }

  tick(jetzt: number, dt: number) {
    const t = jetzt / 1000;
    for (const p of this.teilchen) {
      const [zx, zy] = this.platz(p, t);
      // Feder zum Platz, leicht gedämpft — sie schwingen kurz über.
      p.vx += ((zx - p.x) * 60 - p.vx * 9) * dt;
      p.vy += ((zy - p.y) * 60 - p.vy * 9) * dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
    }
    if (this.teilchen.some((p) => p.stirbt)) {
      this.teilchen = this.teilchen.filter((p) => !(p.stirbt && p.x * p.x + p.y * p.y < 3));
    }
    this.kernR += (this.kernZiel() - this.kernR) * Math.min(1, dt * 6);
    this.kernAnteil += ((this.form === "kern" && !this.gestalt ? 1 : 0) - this.kernAnteil) * Math.min(1, dt * 5);
    for (const z of this.ziffern) {
      if (jetzt >= z.bis) {
        z.z = this.zufall() < 0.5 ? "0" : "1";
        z.bis = jetzt + 300 + this.zufall() * 900;
      }
    }
    if (this.liest && this.zufall() < dt * 26) this.strom.push({ x: (this.zufall() * 2 - 1) * 9, y: M - 2 });
    for (const s of this.strom) s.y -= dt * 38;
    this.strom = this.strom.filter((s) => s.y > 2);
    if (jetzt >= this.blinzelAb + 160) this.blinzelAb = jetzt + 1800 + this.zufall() * 4200;
  }

  zeichne(ctx: CanvasRenderingContext2D, jetzt: number) {
    const m = this.masse;
    const pal = this.palette(jetzt);
    const t = jetzt / 1000;
    const glitch = jetzt < this.glitchBis;
    const band = glitch ? Math.floor(this.zufall() * KI_G) : -99;
    const css = (c: RGB) => `rgb(${Math.round(c[0])},${Math.round(c[1])},${Math.round(c[2])})`;
    const farben = {
      kern: css(pal.kern), hell: css(pal.hell), mittel: css(pal.mittel), dunkel: css(pal.dunkel), tief: css(pal.tief), akzent: css(pal.akzent),
    };
    const px = (x: number, y: number, farbe: string) => {
      let ix = Math.round(M + x - 0.5);
      const iy = Math.round(M + y - 0.5);
      if (glitch && iy >= band && iy < band + 5) ix += iy % 2 ? 3 : -3;
      if (ix < 0 || iy < 0 || ix >= KI_G || iy >= KI_G) return;
      ctx.fillStyle = farbe;
      ctx.fillRect(ix, iy, 1, 1);
    };
    const scheibe = (cx: number, cy: number, r: number, farbe: string, raster = false) => {
      if (r <= 0.3) return;
      for (let y = Math.floor(cy - r - 1); y <= cy + r + 1; y++) {
        for (let x = Math.floor(cx - r - 1); x <= cx + r + 1; x++) {
          if ((x - cx) ** 2 + (y - cy) ** 2 <= r * r && (!raster || (((x + y) % 2) + 2) % 2 === 0)) px(x, y, farbe);
        }
      }
    };
    const linie = (x0: number, y0: number, x1: number, y1: number, farbe: string) => {
      const n = Math.max(1, Math.ceil(Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0))));
      for (let i = 0; i <= n; i++) px(x0 + ((x1 - x0) * i) / n, y0 + ((y1 - y0) * i) / n, farbe);
    };
    ctx.clearRect(0, 0, KI_G, KI_G);

    const k = this.kernAnteil;
    const alsKern = k > 0.5;
    const ruhig = !this.gestalt;
    const puls = jetzt < this.pulsBis ? 1 : Math.sin(t * (this.schlaf ? 1.1 : 3.2));
    const eng = this.schlaf ? 0.55 : 1;

    // Hintere Hälften: Ringe des Lichtkerns, Umlaufbahn der Entität.
    const ringBogen = (vorn: boolean) => {
      m.ringe.forEach(([zu, ry, grad], i) => {
        const rx = (m.rc + zu) * eng;
        const n = (grad * Math.PI) / 180;
        const schritte = Math.round(rx * 8);
        for (let s = 0; s < schritte; s++) {
          const w = (s / schritte) * Math.PI * 2;
          if (Math.sin(w) > 0 !== vorn || s % 2) continue;
          const x = rx * Math.cos(w);
          const y = ry * eng * Math.sin(w);
          px(x * Math.cos(n) - y * Math.sin(n), x * Math.sin(n) + y * Math.cos(n), vorn ? farben.dunkel : farben.tief);
        }
        if (vorn && m.stufe >= 3) {
          const w = t * (i % 2 ? -1.3 : 1.3) + i * 2.1;
          if (Math.sin(w) > 0) {
            const x = rx * Math.cos(w);
            const y = ry * eng * Math.sin(w);
            const sx = x * Math.cos(n) - y * Math.sin(n);
            const sy = x * Math.sin(n) + y * Math.cos(n);
            scheibe(sx, sy, 1.2, farben.akzent);
            px(sx, sy, farben.kern);
          }
        }
      });
    };
    const bahn = (vorn: boolean) => {
      const rx = (m.r + 7) * eng;
      for (let s = 0; s < 44; s++) {
        const w = (s / 44) * Math.PI * 2;
        if (Math.sin(w) > 0 !== vorn || s % 2) continue;
        px(Math.cos(w) * rx, 2 + Math.sin(w) * 4.5 * eng, vorn ? farben.mittel : farben.tief);
      }
      const w = t * 1.2;
      if (Math.sin(w) > 0 === vorn) {
        scheibe(Math.cos(w) * rx, 2 + Math.sin(w) * 4.5 * eng, 1.2, farben.akzent);
        px(Math.cos(w) * rx, 2 + Math.sin(w) * 4.5 * eng, farben.kern);
      }
    };
    if (ruhig && alsKern) ringBogen(false);
    if (ruhig && !alsKern && m.bahn) bahn(false);

    // Datennetz der Wolke: nahe Teilchen sind verbunden.
    if (ruhig && !alsKern && m.netz && !this.schlaf) {
      const ts = this.teilchen;
      for (let i = 0; i < ts.length; i++) {
        let verbunden = 0;
        for (let j = i + 1; j < ts.length && verbunden < 2; j++) {
          const dx = ts[i].x - ts[j].x;
          const dy = ts[i].y - ts[j].y;
          if (dx * dx + dy * dy < 22) {
            linie(ts[i].x, ts[i].y, ts[j].x, ts[j].y, farben.tief);
            verbunden += 1;
          }
        }
      }
    }

    // Kern: in der Wolke ein dichter Fleck, als Lichtkern eine Kugel mit Hof und Strahlen.
    const R = this.kernR;
    if (R > 0.4) {
      if (alsKern) {
        scheibe(0, 0, R + 3.5 + puls * 1.2, farben.tief, true);
        scheibe(0, 0, R + 2 + puls * 0.6, farben.dunkel);
        scheibe(0, 0, R + 1, farben.mittel);
        scheibe(0, 0, R, farben.hell);
        scheibe(-0.4, -0.4, Math.max(0.5, R - 1.2), farben.kern);
        const lang = m.strahl * (0.75 + 0.25 * puls) * (k - 0.5) * 2 * eng;
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          for (let s = 0; s < lang; s++) {
            const a = R + 3 + s;
            if (s > lang - 2 && Math.floor(s) % 2) continue;
            px(dx * a, dy * a, s < lang / 2 ? farben.hell : farben.mittel);
          }
        }
        if (m.stufe >= 4 && !this.schlaf) {
          for (const [dx, dy] of [[1, 1], [-1, 1], [1, -1], [-1, -1]]) for (let a = 7; a < 9; a++) px(dx * a, dy * a, farben.mittel);
        }
      } else if (m.augen) {
        scheibe(0, 0, R + 1, farben.dunkel, true);
        scheibe(0, 0, R, farben.mittel);
        scheibe(0, -0.5, R - 1, farben.hell);
      } else {
        // Funke: ein heller Punkt mit kleinem Kreuz.
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) px(dx, dy, farben.hell);
        if (puls > 0.3) for (const [dx, dy] of [[2, 0], [-2, 0], [0, 2], [0, -2]]) px(dx, dy, farben.mittel);
        px(0, 0, farben.kern);
      }
    }

    // Teilchen.
    for (const p of this.teilchen) {
      const d = p.gx !== null ? p.gd : alsKern ? (p.ring >= 0 ? 0.2 : 0.55) : p.d;
      const farbe = d < 0 ? farben.kern : d < 0.38 ? farben.hell : d < 0.72 ? farben.mittel : farben.dunkel;
      px(p.x, p.y, glitch && this.zufall() < 0.15 ? farben.akzent : farbe);
      if (p.gross && p.gx === null && !alsKern && !this.schlaf) {
        px(p.x + 1, p.y, farbe);
        px(p.x, p.y + 1, farbe);
        px(p.x + 1, p.y + 1, farbe);
      }
    }

    // Daten strömen beim Lesen von unten herein.
    for (const s of this.strom) px(s.x * (s.y / M), s.y, s.y > M / 2 ? farben.mittel : farben.hell);

    // Nullen und Einsen über der Wolke.
    if (ruhig && !alsKern && !this.schlaf) {
      const anzahl = this.ziffern.length;
      this.ziffern.forEach((z, i) => {
        const w = anzahl > 1 ? -1.25 + (i * 2.5) / (anzahl - 1) : 0;
        const zx = Math.sin(w) * (m.r * 1.25 + 3) - 1;
        const zy = -Math.cos(w) * (m.r * 0.8 + 3) - 5 + Math.sin(t * 1.4 + i) * 1.2;
        ZIFFER_BILD[z.z].forEach((zeile, j) => {
          for (let c = 0; c < 3; c++) if (zeile[c] === "#") px(zx + c, zy + j, i % 2 ? farben.dunkel : farben.mittel);
        });
      });
    }

    // Augen: sitzen im Kern, blinzeln, schauen mit.
    if (m.augen && ruhig && R > 1.4) {
      const breit = !alsKern && m.stufe >= 3;
      const ab = alsKern ? (m.stufe < 3 ? 1 : 2) : m.stufe === 1 ? 1 : m.stufe < 4 ? 2 : 3;
      const zu = this.schlaf || (jetzt >= this.blinzelAb && jetzt < this.blinzelAb + 160);
      const bx = Math.round(this.blickX);
      ctx.fillStyle = AUGE;
      for (const s of [-1, 1]) {
        const ex = M + s * ab - (s > 0 ? 0 : 1) + bx;
        if (!zu) ctx.fillRect(ex, M - 1, 1, 1);
        ctx.fillRect(ex, M, 1, 1);
        if (breit) {
          const ex2 = ex + (s > 0 ? 1 : -1);
          if (!zu) ctx.fillRect(ex2, M - 1, 1, 1);
          ctx.fillRect(ex2, M, 1, 1);
        }
      }
    }

    if (ruhig && alsKern) ringBogen(true);
    if (ruhig && !alsKern && m.bahn) bahn(true);
  }
}
