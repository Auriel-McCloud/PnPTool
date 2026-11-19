/**
 * Traktorstrahl der kleinen KI (Mark, 19.11.2026): „etwas, das langsamer ist
 * [als der Laser] … blaue Partikel, die z. B. zum Kot fliegen, ihn aufheben,
 * dann bringt er ihn zum Rand und schmeißt ihn aus dem Bildschirm raus, wo er
 * dann verschwindet.“ Dazu ein pixeliges Herz, das beim Antippen aufsteigt.
 *
 * Reiner Zeichenbaustein ohne React wie `laser.ts`. Den Ablauf (anfliegen,
 * greifen, heben, tragen, werfen) steuert KiFigur.
 */

/** Was der Strahl tragen kann — kleine, lose Dinge. */
export const TRAKTOR_ARTEN: readonly string[] = ["haeufchen", "seite"];
/** Bis zu dieser Gestalt-Stufe (0 Funke, 1 Keim) trägt sie weg; ab Geist brennt der Laser. */
export const TRAKTOR_BIS_STUFE = 1;
/** Pause nach jedem Wurf, bevor sie das nächste Ding holt (Annahme Neko). */
export const TRAKTOR_PAUSE_MS: [number, number] = [4000, 9000];
/** Teilchen strömen so lange hinüber, bevor das Ding abhebt. */
export const GREIFEN_MS = 1400;
/** So lange schwebt es hoch unter sie. */
export const HEBEN_MS = 800;
/** Tragetempo als Anteil ihres normalen Flugtempos — langsamer als der Laser. */
export const TRAG_TEMPO = 0.7;
/** Wurf über den Rand (px/s) und Schwerkraft danach. */
export const WURF_V = 950;
export const WURF_G = 1100;

const BLAU = { kern: "rgb(225,245,255)", hell: "rgb(120,195,255)", mittel: "rgb(45,115,255)", tief: "rgb(20,50,170)" };

interface Teilchen {
  t0: number;
  leben: number;
  /** Seitliches Schlängeln: Weite, Phase. */
  weite: number;
  ph: number;
  g: number;
  hell: boolean;
}

interface Punkt {
  x: number;
  y: number;
}

export class TraktorStrahl {
  /** Strahl an = es strömen neue Teilchen nach. */
  an = false;
  private teile: Teilchen[] = [];
  private nachschub = 0;
  private an0 = 0;
  /** Letzte Enden — Teilchen fliegen auch nach dem Abschalten noch hin. */
  private von: Punkt = { x: 0, y: 0 };
  private bis: Punkt = { x: 0, y: 0 };

  get leer() {
    return !this.an && this.teile.length === 0;
  }

  einschalten(jetzt: number) {
    if (!this.an) this.an0 = jetzt;
    this.an = true;
  }

  zeichne(ctx: CanvasRenderingContext2D, jetzt: number, dt: number, von: Punkt | null, bis: Punkt | null, p: number, breite = 16) {
    if (von) this.von = von;
    if (bis) this.bis = bis;
    const a = this.von;
    const b = this.bis;
    if (this.an) {
      this.nachschub += dt * 46;
      while (this.nachschub >= 1) {
        this.nachschub -= 1;
        this.teile.push({
          t0: jetzt - Math.random() * 30,
          leben: 520 + Math.random() * 380,
          weite: (Math.random() - 0.5) * 2 * (6 + breite * 0.4),
          ph: Math.random() * Math.PI * 2,
          g: Math.random() < 0.3 ? 2 : 1,
          hell: Math.random() < 0.35,
        });
      }
    }
    this.teile = this.teile.filter((t) => jetzt - t.t0 < t.leben);

    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const lang = Math.hypot(dx, dy) || 1;
    const nx = -dy / lang;
    const ny = dx / lang;
    const raster = (v: number) => Math.round(v / p) * p;

    ctx.save();
    ctx.globalCompositeOperation = "lighter";

    if (this.an) {
      // Leiser Lichtkegel, flimmert und blendet beim Einschalten auf.
      const auf = Math.min(1, (jetzt - this.an0) / 350);
      const halbOben = 2 * p;
      const halbUnten = breite * 0.5 + 4 * p;
      const verlauf = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
      verlauf.addColorStop(0, "rgba(120,195,255,0.05)");
      verlauf.addColorStop(1, "rgba(80,160,255,0.22)");
      ctx.globalAlpha = auf * (0.75 + 0.25 * Math.sin(jetzt / 45));
      ctx.fillStyle = verlauf;
      ctx.beginPath();
      ctx.moveTo(a.x + nx * halbOben, a.y + ny * halbOben);
      ctx.lineTo(b.x + nx * halbUnten, b.y + ny * halbUnten);
      ctx.lineTo(b.x - nx * halbUnten, b.y - ny * halbUnten);
      ctx.lineTo(a.x - nx * halbOben, a.y - ny * halbOben);
      ctx.closePath();
      ctx.fill();

      // Drei Ringe wandern den Strahl hinab und werden dabei breiter.
      const winkel = Math.atan2(dy, dx);
      ctx.lineWidth = p;
      for (let i = 0; i < 3; i++) {
        const k = ((jetzt / 900 + i / 3) % 1 + 1) % 1;
        const halb = halbOben + (halbUnten - halbOben) * k;
        ctx.globalAlpha = auf * 0.4 * Math.sin(k * Math.PI);
        ctx.strokeStyle = BLAU.hell;
        ctx.beginPath();
        ctx.ellipse(a.x + dx * k, a.y + dy * k, Math.max(p, halb * 0.25), halb, winkel, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    // Blaue Teilchen schlängeln von ihr zum Ding.
    for (const t of this.teile) {
      const k = Math.max(0, (jetzt - t.t0) / t.leben);
      const e = k * k * (3 - 2 * k);
      const schlaengeln = Math.sin(k * Math.PI) * t.weite * Math.cos(t.ph + k * 7);
      const x = a.x + dx * e + nx * schlaengeln;
      const y = a.y + dy * e + ny * schlaengeln;
      ctx.globalAlpha = Math.min(1, k * 6) * (k > 0.8 ? (1 - k) * 5 : 1);
      ctx.fillStyle = t.hell ? BLAU.kern : k < 0.5 ? BLAU.hell : BLAU.mittel;
      const g = t.g * p;
      ctx.fillRect(raster(x - g / 2), raster(y - g / 2), g, g);
    }

    // Am Ende flirren ein paar Pünktchen um das Ding herum.
    if (this.an) {
      ctx.fillStyle = BLAU.hell;
      for (let i = 0; i < 6; i++) {
        const w = jetzt / 260 + (i * Math.PI) / 3;
        const r = breite * 0.55 + 3 * p + Math.sin(jetzt / 120 + i) * p;
        ctx.globalAlpha = 0.5 + 0.5 * Math.sin(jetzt / 90 + i * 2);
        ctx.fillRect(raster(b.x + Math.cos(w) * r), raster(b.y + Math.sin(w) * r * 0.6), p, p);
      }
    }
    ctx.restore();
  }
}

// ── Pixelherz beim Antippen ───────────────────────────────────────────────

const HERZ = [
  ".##.##.",
  "#######",
  "#######",
  ".#####.",
  "..###..",
  "...#...",
];
const HERZ_MS = 1300;

export interface AufsteigendesHerz {
  t0: number;
  x: number;
  y: number;
}

/** Zeichnet die Herzen, gibt die noch lebenden zurück. */
export function zeichneHerzen(ctx: CanvasRenderingContext2D, herzen: AufsteigendesHerz[], jetzt: number, p: number): AufsteigendesHerz[] {
  const lebend = herzen.filter((h) => jetzt - h.t0 < HERZ_MS);
  const q = p + 1;
  ctx.save();
  for (const h of lebend) {
    const k = (jetzt - h.t0) / HERZ_MS;
    ctx.globalAlpha = k < 0.15 ? k / 0.15 : k > 0.6 ? (1 - k) / 0.4 : 1;
    const ox = Math.round((h.x + Math.sin(k * Math.PI * 2) * 5) / q) * q - 3.5 * q;
    const oy = Math.round((h.y - 60 * (1 - (1 - k) * (1 - k))) / q) * q - 6 * q;
    // Dunkler Rand, dann Füllung, dann ein heller Glanzpunkt.
    ctx.fillStyle = "rgb(110,10,60)";
    for (let r = 0; r < HERZ.length; r++)
      for (let c = 0; c < HERZ[r].length; c++)
        if (HERZ[r][c] === "#") ctx.fillRect(ox + (c - 1) * q, oy + (r - 1) * q, q * 3, q * 3);
    ctx.fillStyle = "rgb(255,80,160)";
    for (let r = 0; r < HERZ.length; r++)
      for (let c = 0; c < HERZ[r].length; c++)
        if (HERZ[r][c] === "#") ctx.fillRect(ox + c * q, oy + r * q, q, q);
    ctx.fillStyle = "rgb(255,215,235)";
    ctx.fillRect(ox + q, oy + q, q, q);
  }
  ctx.restore();
  return lebend;
}
