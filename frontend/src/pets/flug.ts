/**
 * Flug-Logik für fliegende Pets — zuerst Bärbel, die sprechende Bibel und
 * Zauberbuch (Mark und seine Frau, 11.11.2026).
 *
 * Gleiche Schnittstelle wie `PetBewegung` (Zustandsautomat ohne React/DOM,
 * `tick` pro Frame, danach `darstellung()`), aber sie läuft nicht, sie fliegt:
 *
 * - Kommt nie unten von der Seite, sondern in irgendeiner Höhe oder von oben
 *   herein (Mark: „nie links oder rechts unten ins Bild, sondern in
 *   irgendeiner Höhe, oder gar von oben“), und fliegt auch so wieder raus.
 * - Zugeklappt schwebt sie langsam herum; aufgeklappt flattert sie wie ein
 *   Vogel schnell durchs Bild. Dazwischen klappt sie auf bzw. zu.
 * - Landet manchmal zugeklappt auf Text/Kästchen und ruht dort. Verschwindet
 *   die Fläche, klappt sie auf und flattert weg (fällt nicht wie der Drache).
 * - Verwandelt sich ab und zu in einer Zauberwolke in eine ihrer drei
 *   Gestalten (klassisch, Grimoire mit Auge, rot mit Gesicht).
 * - Blinzeln: das Gesicht oft, das violette Auge seltener und schaut sich
 *   dabei um.
 * - Statt Häufchen verliert sie beim Flattern Seiten, die zerknittert liegen
 *   bleiben (Spur-Art `seite`).
 * - Antippen = Freuen (Hüpfer, Herzen); 3 s halten = packen, sie flattert
 *   panisch am Finger; loslassen = Wurf mit Luftwiderstand, sie fängt sich
 *   wieder — oder fliegt links/rechts/oben raus zum nächsten Tablet.
 */

import { PACKEN_MS, type Darstellung, type Flaeche, type Masse, type Meldung, type Quelle, type Umgebung } from "./bewegung";

/** Was die Komponente von einer Pet-Steuerung braucht (Laufen oder Fliegen). */
export interface PetSteuerung {
  readonly gepackt: boolean;
  setzeUmgebung(u: Umgebung): void;
  tick(jetzt: number, dt: number): void;
  darstellung(jetzt: number): Darstellung;
  druckStart(jetzt: number): boolean;
  fingerMerken(fx: number, fy: number, jetzt: number): void;
  druckAbbrechen(jetzt: number): void;
  tragen(fx: number, fy: number, jetzt: number): void;
  loslassen(jetzt: number): void;
  streicheln(jetzt: number): boolean;
  aufraeumen(): void;
}

/** Sprite-Takte (gleich wie frontend/public/pets/baerbel/sprite.json). */
export const FLUG_TAKT = {
  gestalten: 3,
  klappenFrames: 5,
  klappenMs: 60,
  verwandelnFrames: 32,
  verwandelnMs: 70,
  /** Ab diesem Frame der Wolke ist sie in der neuen Gestalt. */
  verwandelnWechsel: 16,
  blinzeln: { 2: { frames: 19, ms: 110 }, 3: { frames: 5, ms: 70 } } as Record<number, { frames: number; ms: number }>,
  /** Tentakelmonster: Streifen mit Buch, eigene Leinwand (siehe PetOverlay). */
  tentakelFrames: 44,
  tentakelMs: 80,
  tentakelSchlagFrame: 33,
  /** Spitze beim Klatschen auf der Effekt-Leinwand (Sprite-Pixel, ab links oben). */
  tentakelSpitze: [98, 92] as const,
  effektRand: 18,
};

/** Blitz-Zauber (Mark, 11.11.2026: „die Blitz-Animation, die was verbrennt“). */
const LADEN_MS = 900;
const BLITZ_MS = 650;
const RUECKSTOSS_MS = 500;

type Zustand =
  | "flattern" // aufgeklappt zu einem Ziel
  | "schweben" // zugeklappt, langsam zu einem Ziel
  | "sitzen" // zugeklappt auf einer Fläche
  | "klappen" // Auf-/Zuklappen
  | "zittern" // vor der Verwandlung
  | "verwandeln"
  | "tentakel" // Monster will raus
  | "zaubern" // Blitz: laden, Blitz, Rückstoß
  | "gehalten"
  | "getragen"
  | "wurf"
  | "raus";

const FLATTER_PX_S = 230;
const SCHWEBE_PX_S = 30;
const ZITTERN_MS = 600;
const WURF_BREMSE = 1.6; // Luftwiderstand pro Sekunde
const MAX_WURF_PX_S = 2600;
const BESUCH_MIN_MS = 60_000;
const BESUCH_MAX_MS = 150_000;

export class FlugBewegung implements PetSteuerung {
  private x: number;
  private y: number;
  private zustand: Zustand = "flattern";
  private offen = true;
  private gestalt: number;
  private ziel: { x: number; y: number } = { x: 0, y: 0 };
  private bis = 0;
  private klapp: { t0: number; auf: boolean; danach: () => void } | null = null;
  private sitz: Quelle | null = null;
  private animStart: number;
  private blinzelStart: number | null = null;
  private naechstesBlinzeln: number;
  private naechsteVerwandlung: number;
  private naechsteSeite: number;
  private puffStart: number | null = null;
  private gewechselt = false;
  private effektStart = 0;
  private schleimGemeldet = false;
  private blitz: { x0: number; y0: number; x1: number; y1: number; gemeldet: boolean; rx: number; ry: number } | null = null;
  private naechstesMonster: number;
  private naechsterBlitz: number;
  private zitterStart = 0;
  private freudeStart = -1e9;
  private besuchEnde: number;
  private rausSeite: "links" | "rechts" | "oben" = "rechts";
  private rausGemeldet = false;
  private vx = 0;
  private vy = 0;
  private dreh = 0;
  private kipp = 0;
  private griff: { start: number; vorher: { zustand: Zustand; bis: number } } | null = null;
  private fingerSpur: { x: number; y: number; t: number }[] = [];
  private t0: number;

  private masse: () => Masse;
  private u: Umgebung;
  private melden: (m: Meldung) => void;

  constructor(masse: () => Masse, u: Umgebung, seite: "links" | "rechts", jetzt: number, melden: (m: Meldung) => void) {
    this.masse = masse;
    this.u = u;
    this.melden = melden;
    const { bw, bh } = masse();
    const z = u.zufall;
    this.t0 = jetzt;
    this.gestalt = 1 + Math.floor(z() * FLUG_TAKT.gestalten);
    // Rein: oft von oben, sonst von der Seite in irgendeiner Höhe — nie unten.
    if (z() < 0.35) {
      this.x = u.breite * (0.1 + z() * 0.7);
      this.y = -bh - 10;
    } else {
      this.x = seite === "links" ? -bw - 10 : u.breite + 10;
      this.y = u.hoehe * (0.05 + z() * 0.5);
    }
    this.animStart = jetzt;
    this.besuchEnde = jetzt + BESUCH_MIN_MS + z() * (BESUCH_MAX_MS - BESUCH_MIN_MS);
    this.naechstesBlinzeln = jetzt + this.blinzelPause();
    this.naechsteVerwandlung = jetzt + 15_000 + z() * 35_000;
    this.naechsteSeite = jetzt + 12_000 + z() * 25_000;
    this.naechstesMonster = jetzt + 20_000 + z() * 40_000;
    this.naechsterBlitz = jetzt + 25_000 + z() * 45_000;
    this.flatternZu(this.zufallsZiel(), jetzt);
  }

  setzeUmgebung(u: Umgebung) {
    this.u = u;
  }

  aufraeumen() {
    /* nichts an der Host-UI verändert */
  }

  get gepackt() {
    return this.zustand === "getragen";
  }

  // ── Ziele ───────────────────────────────────────────────────────────────

  private zufallsZiel() {
    const { bw, bh } = this.masse();
    const z = this.u.zufall;
    const links = this.u.links ?? 0;
    return {
      x: links + z() * Math.max(10, this.u.breite - links - bw),
      y: this.u.hoehe * 0.04 + z() * Math.max(10, this.u.hoehe * 0.62 - bh * 0.5),
    };
  }

  private blinzelPause() {
    const z = this.u.zufall;
    // Das violette Auge nur manchmal (Mark), das Gesicht öfter.
    return this.gestalt === 2 ? 7000 + z() * 10_000 : 2500 + z() * 4500;
  }

  /** Eine Fläche zum Ausruhen: oben genug Platz, breit genug für das Buch. */
  private landeplatz(): Flaeche | null {
    const { bw } = this.masse();
    const kandidaten = this.u.flaechen().filter((f) => f.r.right - f.r.left >= bw * 0.3);
    if (!kandidaten.length) return null;
    return kandidaten[Math.floor(this.u.zufall() * kandidaten.length)];
  }

  private sitzPosition(r: { left: number; right: number; top: number }) {
    const { bw, bh, fuss } = this.masse();
    const mitte = Math.min(Math.max((r.left + r.right) / 2, r.left + bw * 0.15), r.right - bw * 0.15);
    return { x: mitte - bw / 2, y: r.top - (bh - fuss) };
  }

  // ── Abläufe ─────────────────────────────────────────────────────────────

  private setzeAnim(jetzt: number) {
    this.animStart = jetzt;
  }

  private flatternZu(ziel: { x: number; y: number }, jetzt: number, sitz: Quelle | null = null) {
    if (!this.offen) {
      this.klappe(true, jetzt, () => this.flatternZu(ziel, jetzt + FLUG_TAKT.klappenFrames * FLUG_TAKT.klappenMs, sitz));
      return;
    }
    this.ziel = ziel;
    this.sitz = sitz;
    this.zustand = "flattern";
    this.setzeAnim(jetzt);
  }

  private schwebenZu(ziel: { x: number; y: number }, jetzt: number) {
    if (this.offen) {
      this.klappe(false, jetzt, () => this.schwebenZu(ziel, jetzt + FLUG_TAKT.klappenFrames * FLUG_TAKT.klappenMs));
      return;
    }
    this.ziel = ziel;
    this.zustand = "schweben";
    this.bis = jetzt + 5000 + this.u.zufall() * 7000;
    this.setzeAnim(jetzt);
  }

  private klappe(auf: boolean, jetzt: number, danach: () => void) {
    this.zustand = "klappen";
    this.klapp = { t0: jetzt, auf, danach };
    this.blinzelStart = null;
  }

  private verwandeln(jetzt: number) {
    if (this.offen) {
      this.klappe(false, jetzt, () => this.verwandeln(jetzt + FLUG_TAKT.klappenFrames * FLUG_TAKT.klappenMs));
      return;
    }
    this.zustand = "zittern";
    this.zitterStart = jetzt;
    this.blinzelStart = null;
  }

  /** Tentakelmonster will raus (Mark, 11.11.2026). Nur zugeklappt. */
  private monster(jetzt: number) {
    if (this.offen) {
      this.klappe(false, jetzt, () => this.monster(jetzt + FLUG_TAKT.klappenFrames * FLUG_TAKT.klappenMs));
      return;
    }
    this.zustand = "tentakel";
    this.effektStart = jetzt;
    this.schleimGemeldet = false;
    this.blinzelStart = null;
  }

  /** Blitz-Zauber: aufklappen, Seiten leuchten auf, Blitz schlägt irgendwo ein
   *  und hinterlässt einen Brandfleck; Rückstoß, wieder zuklappen. */
  private zaubern(jetzt: number) {
    if (!this.offen) {
      this.klappe(true, jetzt, () => this.zaubern(jetzt + FLUG_TAKT.klappenFrames * FLUG_TAKT.klappenMs));
      return;
    }
    const { bw, bh } = this.masse();
    const z = this.u.zufall;
    const x0 = this.x + bw / 2;
    const y0 = this.y + bh * 0.42;
    // Ziel: meist schräg nach unten, 220–520 px weit, im Bild.
    const w = (20 + z() * 140) * (Math.PI / 180) * (z() < 0.85 ? 1 : -1);
    const weite = 220 + z() * 300;
    const rand = 40;
    const x1 = Math.min(this.u.breite - rand, Math.max((this.u.links ?? 0) + rand, x0 + Math.cos(w) * weite));
    const y1 = Math.min(this.u.hoehe - rand, Math.max(rand, y0 + Math.sin(w) * weite));
    const d = Math.max(1, Math.hypot(x1 - x0, y1 - y0));
    this.blitz = { x0, y0, x1, y1, gemeldet: false, rx: -(x1 - x0) / d, ry: -(y1 - y0) / d };
    this.zustand = "zaubern";
    this.effektStart = jetzt;
  }

  private rausFliegen(jetzt: number) {
    const { bw, bh } = this.masse();
    const z = this.u.zufall;
    const r = z();
    this.rausSeite = r < 0.3 ? "oben" : r < 0.65 ? "links" : "rechts";
    const ziel =
      this.rausSeite === "oben"
        ? { x: this.x + (z() - 0.5) * 300, y: -bh * 1.4 }
        : { x: this.rausSeite === "links" ? -bw * 1.4 : this.u.breite + bw * 0.4, y: this.u.hoehe * (0.05 + z() * 0.45) };
    this.flatternZu(ziel, jetzt);
    if (this.zustand === "flattern") this.zustand = "raus";
    else {
      // Erst aufklappen, dann raus.
      const k = this.klapp!;
      const weiter = k.danach;
      k.danach = () => {
        weiter();
        this.zustand = "raus";
      };
    }
  }

  private entscheiden(jetzt: number) {
    const z = this.u.zufall;
    if (jetzt > this.besuchEnde) {
      this.rausFliegen(jetzt);
      return;
    }
    const r = z();
    if (this.offen) {
      if (r < 0.45) this.flatternZu(this.zufallsZiel(), jetzt);
      else if (r < 0.7) {
        const f = this.landeplatz();
        if (f) this.flatternZu(this.sitzPosition(f.r), jetzt, f.q);
        else this.schwebenZu(this.zufallsZiel(), jetzt);
      } else this.schwebenZu(this.zufallsZiel(), jetzt);
    } else {
      if (jetzt > this.naechstesMonster && r < 0.25) {
        this.naechstesMonster = jetzt + 45_000 + z() * 75_000;
        this.monster(jetzt);
      } else if (jetzt > this.naechsterBlitz && r > 0.75) {
        this.naechsterBlitz = jetzt + 50_000 + z() * 80_000;
        this.zaubern(jetzt);
      } else if (jetzt > this.naechsteVerwandlung && r < 0.3) this.verwandeln(jetzt);
      else if (r < 0.6) this.schwebenZu(this.zufallsZiel(), jetzt);
      else this.flatternZu(this.zufallsZiel(), jetzt);
    }
  }

  // ── Takt ────────────────────────────────────────────────────────────────

  tick(jetzt: number, dt: number) {
    const { bw, bh } = this.masse();
    const u = this.u;

    // Blinzeln in Ruhe (zugeklappt) — nur die Gestalten mit Augen.
    if ((this.zustand === "schweben" || this.zustand === "sitzen") && FLUG_TAKT.blinzeln[this.gestalt]) {
      const b = FLUG_TAKT.blinzeln[this.gestalt];
      if (this.blinzelStart !== null && jetzt - this.blinzelStart > b.frames * b.ms) {
        this.blinzelStart = null;
        this.naechstesBlinzeln = jetzt + this.blinzelPause();
      } else if (this.blinzelStart === null && jetzt > this.naechstesBlinzeln) {
        this.blinzelStart = jetzt;
      }
    }

    let zielKipp = 0;
    switch (this.zustand) {
      case "flattern":
      case "raus": {
        const dx = this.ziel.x - this.x;
        const dy = this.ziel.y - this.y;
        const d = Math.hypot(dx, dy);
        const schritt = FLATTER_PX_S * dt;
        zielKipp = Math.max(-14, Math.min(14, (dx / Math.max(d, 1)) * 14));
        // Seiten verlieren (statt Häufchen) — nur auf dem Bildschirm.
        if (this.zustand === "flattern" && jetzt > this.naechsteSeite) {
          this.naechsteSeite = jetzt + 25_000 + u.zufall() * 35_000;
          this.seiteVerlieren();
        }
        if (d <= schritt) {
          this.x = this.ziel.x;
          this.y = this.ziel.y;
          if (this.zustand === "raus") {
            this.rausMelden();
            return;
          }
          if (this.sitz) {
            const q = this.sitz;
            this.klappe(false, jetzt, () => {
              this.zustand = "sitzen";
              this.sitz = q;
              this.bis = jetzt + 6000 + u.zufall() * 16_000;
              this.setzeAnim(jetzt);
            });
          } else this.entscheiden(jetzt);
        } else {
          this.x += (dx / d) * schritt;
          this.y += (dy / d) * schritt;
        }
        break;
      }
      case "schweben": {
        const dx = this.ziel.x - this.x;
        const dy = this.ziel.y - this.y;
        const d = Math.hypot(dx, dy);
        const schritt = SCHWEBE_PX_S * dt;
        if (d > schritt) {
          this.x += (dx / d) * schritt;
          this.y += (dy / d) * schritt;
        }
        if (jetzt > this.bis || d <= schritt) {
          if (this.blinzelStart === null) this.entscheiden(jetzt);
        }
        break;
      }
      case "sitzen": {
        const r = this.sitz?.rechteck() ?? null;
        if (!r) {
          // Fläche weg (Popup zu, gescrollt): aufklappen und wegflattern.
          this.sitz = null;
          this.flatternZu(this.zufallsZiel(), jetzt);
          break;
        }
        const p = this.sitzPosition(r);
        this.x = p.x;
        this.y = p.y;
        if (jetzt > this.bis && this.blinzelStart === null) {
          this.sitz = null;
          this.entscheiden(jetzt);
        }
        break;
      }
      case "klappen": {
        const k = this.klapp!;
        if (jetzt - k.t0 >= FLUG_TAKT.klappenFrames * FLUG_TAKT.klappenMs) {
          this.offen = k.auf;
          this.klapp = null;
          k.danach();
        }
        break;
      }
      case "zittern":
        if (jetzt - this.zitterStart >= ZITTERN_MS) {
          this.zustand = "verwandeln";
          this.puffStart = jetzt;
          this.gewechselt = false;
        }
        break;
      case "verwandeln": {
        const t = jetzt - this.puffStart!;
        if (t >= FLUG_TAKT.verwandelnWechsel * FLUG_TAKT.verwandelnMs && !this.gewechselt) {
          let neu = this.gestalt;
          while (neu === this.gestalt) neu = 1 + Math.floor(u.zufall() * FLUG_TAKT.gestalten);
          this.gestalt = neu;
          this.gewechselt = true;
        }
        if (t >= FLUG_TAKT.verwandelnFrames * FLUG_TAKT.verwandelnMs) {
          this.puffStart = null;
          this.naechsteVerwandlung = jetzt + 40_000 + u.zufall() * 80_000;
          this.naechstesBlinzeln = jetzt + 600;
          this.schwebenZu(this.zufallsZiel(), jetzt);
        }
        break;
      }
      case "tentakel": {
        const t = jetzt - this.effektStart;
        if (!this.schleimGemeldet && t >= FLUG_TAKT.tentakelSchlagFrame * FLUG_TAKT.tentakelMs) {
          this.schleimGemeldet = true;
          this.schleimMelden(jetzt);
        }
        if (t >= FLUG_TAKT.tentakelFrames * FLUG_TAKT.tentakelMs) {
          this.naechstesBlinzeln = jetzt + 400;
          this.schwebenZu(this.zufallsZiel(), jetzt);
        }
        break;
      }
      case "zaubern": {
        const t = jetzt - this.effektStart;
        const b = this.blitz;
        if (b && !b.gemeldet && t >= LADEN_MS) {
          b.gemeldet = true;
          const x = b.x1 / u.breite;
          const y = b.y1 / u.hoehe;
          if (x > 0 && x < 1 && y > 0 && y < 1) this.melden({ typ: "haeufchen", x, y, art: "brand" });
        }
        if (b && t >= LADEN_MS + BLITZ_MS * 0.3 && t < LADEN_MS + BLITZ_MS + RUECKSTOSS_MS) {
          // Rückstoß: weg vom Einschlag, auslaufend
          const k = 1 - (t - LADEN_MS - BLITZ_MS * 0.3) / (BLITZ_MS * 0.7 + RUECKSTOSS_MS);
          this.x += b.rx * 140 * k * dt;
          this.y += b.ry * 140 * k * dt;
        }
        if (t >= LADEN_MS + BLITZ_MS + RUECKSTOSS_MS) {
          this.blitz = null;
          this.schwebenZu(this.zufallsZiel(), jetzt);
        }
        break;
      }
      case "wurf": {
        const bremse = Math.exp(-WURF_BREMSE * dt);
        this.vx *= bremse;
        this.vy = this.vy * bremse + 180 * dt; // etwas Schwere, sie fängt sich aber
        this.x += this.vx * dt;
        this.y += this.vy * dt;
        this.dreh *= Math.exp(-2 * dt);
        if (this.y + bh > u.hoehe) {
          this.y = u.hoehe - bh;
          this.vy = -Math.abs(this.vy) * 0.4;
        }
        const raus =
          this.x + bw < 0 ? "links" : this.x > u.breite ? "rechts" : this.y + bh < 0 ? "oben" : null;
        if (raus) {
          this.rausSeite = raus;
          this.zustand = "raus";
          this.rausMelden();
          return;
        }
        if (Math.hypot(this.vx, this.vy) < 140) {
          this.dreh = 0;
          this.flatternZu(this.zufallsZiel(), jetzt);
        }
        break;
      }
      case "gehalten":
        if (jetzt - this.griff!.start >= PACKEN_MS) {
          this.zustand = "getragen";
          this.offen = true; // panisch flattern
          this.blinzelStart = null;
          this.puffStart = null;
          this.klapp = null;
          this.setzeAnim(jetzt);
          const f = this.fingerSpur[this.fingerSpur.length - 1];
          if (f) this.tragen(f.x, f.y, jetzt);
        }
        break;
      default:
        break;
    }
    // Neigung weich nachziehen.
    this.kipp += (zielKipp - this.kipp) * Math.min(1, dt * 6);
  }

  private seiteVerlieren() {
    const { bw, bh } = this.masse();
    const x = (this.x + bw / 2) / this.u.breite;
    const y = (this.y + bh * 0.7) / this.u.hoehe;
    if (x > 0.02 && x < 0.98 && y > 0 && y < 0.95) this.melden({ typ: "haeufchen", x, y, art: "seite" });
  }

  /** Schleimfleck dort, wo die Tentakel aufs Display klatscht. */
  private schleimMelden(jetzt: number) {
    const { bw } = this.masse();
    const s = bw / 76;
    const top = this.y + Math.sin(((jetzt - this.t0) / 1000) * 2 * Math.PI * 0.35) * 4;
    const [sx, sy] = FLUG_TAKT.tentakelSpitze;
    const px = this.x + (sx - FLUG_TAKT.effektRand) * s;
    const py = top + (sy - FLUG_TAKT.effektRand) * s;
    const x = px / this.u.breite;
    const y = py / this.u.hoehe;
    if (x > 0.01 && x < 0.99 && y > 0.01 && y < 0.99) this.melden({ typ: "haeufchen", x, y, art: "schleim" });
  }

  private rausMelden() {
    if (this.rausGemeldet) return;
    this.rausGemeldet = true;
    const seite =
      this.rausSeite === "oben"
        ? this.x + this.masse().bw / 2 > this.u.breite / 2
          ? "rechts"
          : "links"
        : this.rausSeite;
    this.melden({ typ: "raus", seite });
  }

  // ── Anfassen ────────────────────────────────────────────────────────────

  druckStart(jetzt: number): boolean {
    if (["wurf", "gehalten", "getragen"].includes(this.zustand)) return false;
    if (this.zustand === "raus" && this.rausGemeldet) return false;
    this.griff = { start: jetzt, vorher: { zustand: this.zustand, bis: this.bis } };
    this.zustand = "gehalten";
    this.fingerSpur = [];
    return true;
  }

  fingerMerken(fx: number, fy: number, jetzt: number) {
    if (this.zustand !== "gehalten") return;
    this.fingerSpur.push({ x: fx, y: fy, t: jetzt });
    while (this.fingerSpur.length > 2 && jetzt - this.fingerSpur[0].t > 100) this.fingerSpur.shift();
  }

  druckAbbrechen(jetzt: number) {
    if (this.zustand !== "gehalten" || !this.griff) return;
    const dauer = jetzt - this.griff.start;
    const vorher = this.griff.vorher;
    this.griff = null;
    this.fingerSpur = [];
    this.zustand = vorher.zustand;
    this.bis = vorher.bis + dauer;
    if (this.klapp) this.klapp.t0 += dauer;
    if (this.puffStart !== null) this.puffStart += dauer;
    this.effektStart += dauer;
    this.zitterStart += dauer;
    if (this.blinzelStart !== null) this.blinzelStart += dauer;
  }

  tragen(fx: number, fy: number, jetzt: number) {
    if (this.zustand !== "getragen") return;
    const { bw, bh } = this.masse();
    this.fingerSpur.push({ x: fx, y: fy, t: jetzt });
    while (this.fingerSpur.length > 2 && jetzt - this.fingerSpur[0].t > 100) this.fingerSpur.shift();
    // Am Buchrücken gepackt: Finger etwas über der Mitte.
    this.x = fx - bw / 2;
    this.y = fy - bh * 0.4;
  }

  loslassen(jetzt: number) {
    if (this.zustand !== "getragen") return;
    const spur = this.fingerSpur.filter((p) => jetzt - p.t <= 120);
    if (spur.length >= 2) {
      const a = spur[0];
      const b = spur[spur.length - 1];
      const dt = Math.max(16, b.t - a.t) / 1000;
      this.vx = (b.x - a.x) / dt;
      this.vy = (b.y - a.y) / dt;
    } else {
      this.vx = 0;
      this.vy = 0;
    }
    const v = Math.hypot(this.vx, this.vy);
    if (v > MAX_WURF_PX_S) {
      this.vx *= MAX_WURF_PX_S / v;
      this.vy *= MAX_WURF_PX_S / v;
    }
    this.dreh = 0;
    this.fingerSpur = [];
    this.griff = null;
    this.sitz = null;
    this.zustand = "wurf";
    // Beim Wurf flattert schon mal eine Seite raus.
    if (v > 900) this.seiteVerlieren();
  }

  streicheln(jetzt: number): boolean {
    if (["raus", "gehalten", "getragen", "wurf"].includes(this.zustand)) return false;
    this.freudeStart = jetzt;
    return true;
  }

  // ── Darstellung ─────────────────────────────────────────────────────────

  darstellung(jetzt: number): Darstellung {
    const { bw, bh } = this.masse();
    const g = this.gestalt;
    let animation = this.offen ? `flattern_${g}` : `schweben_${g}`;
    let animStart = this.animStart;
    let frame: number | null = null;
    let top = this.y;
    let rot = this.kipp;
    const sek = (jetzt - this.t0) / 1000;

    if (this.zustand === "klappen" && this.klapp) {
      animation = `klappen_${g}`;
      const f = Math.min(FLUG_TAKT.klappenFrames - 1, Math.floor((jetzt - this.klapp.t0) / FLUG_TAKT.klappenMs));
      frame = this.klapp.auf ? f : FLUG_TAKT.klappenFrames - 1 - f;
    } else if (this.offen) {
      // Wellenflug: auf und ab im Flügeltakt.
      top += Math.sin(sek * 2 * Math.PI * 1.3) * 5;
    } else if (this.zustand !== "sitzen") {
      // Sanftes Schweben.
      top += Math.sin(sek * 2 * Math.PI * 0.35) * 4;
      rot += Math.sin(sek * 2 * Math.PI * 0.21) * 3;
    }
    if (!this.offen && this.blinzelStart !== null && this.zustand !== "klappen") {
      animation = `blinzeln_${g}`;
      animStart = this.blinzelStart;
      const b = FLUG_TAKT.blinzeln[g];
      if (b) frame = Math.min(b.frames - 1, Math.floor((jetzt - this.blinzelStart) / b.ms));
    }
    if (this.zustand === "zittern") rot += Math.sin(jetzt / 22) * 4;
    let effekt: Darstellung["effekt"] = null;
    if (this.zustand === "tentakel") effekt = { name: `tentakel_${g}`, start: this.effektStart, ersetzt: true };
    let blitz: Darstellung["blitz"] = null;
    let leuchten = false;
    if (this.zustand === "zaubern" && this.blitz) {
      const t = jetzt - this.effektStart;
      animation = `klappen_${g}`;
      frame = FLUG_TAKT.klappenFrames - 1;
      top = this.y; // still in der Luft, nur Zittern
      if (t < LADEN_MS) rot += Math.sin(jetzt / 25) * (1 + (t / LADEN_MS) * 4);
      leuchten = t < LADEN_MS + BLITZ_MS;
      if (t >= LADEN_MS && t < LADEN_MS + BLITZ_MS) {
        const b = this.blitz;
        blitz = { start: this.effektStart + LADEN_MS, x0: b.x0, y0: b.y0, x1: b.x1, y1: b.y1 };
      }
    }
    if (this.zustand === "gehalten" && this.griff) {
      const staerke = Math.min(1, (jetzt - this.griff.start) / PACKEN_MS);
      rot += Math.sin(jetzt / 30) * (2 + staerke * 9);
    }
    if (this.zustand === "getragen") rot = Math.sin(jetzt / 90) * 12;
    if (this.zustand === "wurf") {
      this.dreh += this.vx * 0.0006;
      rot = this.dreh * 40;
    }
    // Freuen: zwei kleine Hüpfer mit Wackeln.
    const fr = (jetzt - this.freudeStart) / 900;
    if (fr >= 0 && fr < 1) {
      top -= Math.abs(Math.sin(fr * 2 * Math.PI)) * 14;
      rot += Math.sin(fr * 4 * Math.PI) * 8;
    }

    return {
      left: this.x,
      top,
      transform: `rotate(${rot.toFixed(1)}deg)`,
      animation,
      animStart,
      frame,
      feuer: null,
      puff: this.zustand === "verwandeln" ? this.puffStart : null,
      effekt,
      blitz,
      leuchten,
      hockt: false,
      gepackt: this.zustand === "getragen" || this.zustand === "gehalten",
      schlaeft: false,
      schwitzt: false,
      kopfX: this.x + bw / 2,
      kopfY: top + bh * 0.12,
    };
  }
}
