/**
 * Bewegungslogik des Critter-Pets (Mark, 11.11.2026).
 *
 * Reiner Zustandsautomat ohne React/DOM: die Komponente ruft `tick` pro
 * Frame und liest danach `darstellung()`. Die Welt kommt über `Umgebung`
 * herein (Bildschirmgröße, Flächen zum Draufstehen, Wände zum Klettern).
 *
 * - Boden: unterer Bildschirmrand. Raus zum nächsten Tablet nur von hier.
 * - Flächen: Oberkanten von Wörtern/Textzeilen, Linien, Punkten, Kästchen,
 *   Popups — er springt drauf, läuft darauf, hüpft von einer zur nächsten.
 * - Wände: Seiten offener Popups und die Bildschirmränder — er klettert.
 *
 * Übergänge (Mark: „wir bräuchten noch eine Übergangs-Animation“): an die
 * Wand anlehnen, oben über die Kante ziehen, von der Wand abstoßen und
 * nach der Landung kurz einfedern sind eigene, interpolierte Schritte statt
 * harter Schnitte.
 *
 * Klettern ist mühsam (Mark: „soll sich anstrengender anfühlen“): einzelne
 * Klimmzüge mit Nachgreifen, alle paar Züge eine Verschnaufpause mit
 * Schwitzen und Wackeln, manchmal rutscht er ein Stück ab.
 */

export type Animation = "idle" | "lauf" | "freuen" | "sprung" | "schlafen" | "klettern" | "niesen";

export interface Masse {
  /** Box-Breite/-Höhe des Sprites in Bildschirm-Pixeln. */
  bw: number;
  bh: number;
  /** Maul im Sprite (Bildschirm-Pixel ab links oben, Blick nach rechts). */
  maulX: number;
  maulY: number;
  /** Länge des Feuerstoßes (Bildschirm-Pixel). */
  feuerLaenge: number;
  /** Leerer Rand unter den Füßen im Sprite (Bildschirm-Pixel). */
  fuss: number;
}

export interface Rechteck {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

/** Etwas, worauf er stehen oder woran er klettern kann. Liefert das aktuelle
 * Rechteck oder null, wenn es weg/verdeckt/aus dem Bild ist. */
export interface Quelle {
  rechteck(): Rechteck | null;
}

export interface Flaeche {
  q: Quelle;
  r: Rechteck;
}

export interface Umgebung {
  breite: number;
  hoehe: number;
  /** Flächen zum Draufstehen (nur bei Entscheidungen abgefragt). */
  flaechen: () => Flaeche[];
  /** Popups, an deren Seite er hochklettern kann. */
  waende: () => Flaeche[];
  zufall: () => number;
}

type Ort = { art: "boden" } | { art: "flaeche"; q: Quelle };
/** Wo die Wand vom Pet aus gesehen ist. q = null: Bildschirmrand. */
type Wand = { x: number; seite: "links" | "rechts"; q: Quelle | null };

type Zustand =
  | "laufen"
  | "idle"
  | "freuen"
  | "haeufchen"
  | "schlafen"
  | "klettern"
  | "haengen"
  | "sprung"
  | "landen"
  | "uebergang"
  | "niesen"
  | "raus";

interface Pose {
  left: number;
  top: number;
  /** Drehung in Grad; flip = horizontal gespiegelt (schaut nach links). */
  rot: number;
  flip: boolean;
}

interface Sprung {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  t0: number;
  dauer: number;
  bogen: number;
  danach: Ort;
  /** Drehung beim Absprung (von der Wand weg), läuft in den Sprung aus. */
  startRot: number;
}

interface Uebergang {
  von: Pose;
  nach: Pose;
  t0: number;
  dauer: number;
  animation: Animation;
  danach: (jetzt: number) => void;
}

type KletterPhase = "zug" | "griff" | "rast" | "rutsch";

interface Kletterei {
  phase: KletterPhase;
  t0: number;
  dauer: number;
  vonCy: number;
  nachCy: number;
  zuegeBisRast: number;
  /** Bild der Kletter-Animation am Anfang dieses Zugs. */
  frameBasis: number;
  /** Gesamtzahl Züge — ab dem dritten schwitzt er. */
  zuege: number;
}

export interface Darstellung {
  left: number;
  top: number;
  transform: string;
  animation: Animation;
  animStart: number;
  /** Feuerstoß beim Niesen: Startzeit, Maul-Ankerpunkt, Blickrichtung. */
  feuer: { start: number; x: number; y: number; flip: boolean } | null;
  /** Fester Frame statt Zeittakt (Klettern: Beine bewegen sich nur beim Zug). */
  frame: number | null;
  hockt: boolean;
  schlaeft: boolean;
  schwitzt: boolean;
  /** Kopfposition für Zzz/Herzen/Tropfen. */
  kopfX: number;
  kopfY: number;
}

export type Meldung =
  | { typ: "raus"; seite: "links" | "rechts" }
  | { typ: "haeufchen"; x: number; y: number; art: "haeufchen" | "brand" };

/** Niesen: Sprite-Takt und wann das Feuer kommt (passt zu niesen.png/feuer.png). */
const NIESEN_MS = 14 * 80;
const FEUER_AB_MS = 6 * 80;
const FEUER_MS = 8 * 70;
/** Mindestabstand zwischen zwei Niesern. */
const NIESEN_PAUSE_MS = 25_000;

const TEMPO_PX_S = 45;
/** Höchster Satz nach oben; höhere Popups werden erklettert. */
const SPRUNG_MAX_PX = 240;
/** Wie weit er seitlich auf eine andere Fläche springt. */
const SPRUNG_WEIT_PX = 450;
const KLETTER_FRAMES = 32;

const glatt = (t: number) => t * t * (3 - 2 * t);
const auslaufen = (t: number) => 1 - (1 - t) * (1 - t);

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
  niesenStart = 0;
  brandGelegt = false;
  naechstesNiesen = 0;
  rausGemeldet = false;
  nachAnkunft: ((jetzt: number) => void) | null = null;
  sprung: Sprung | null = null;
  uebergang: Uebergang | null = null;
  wand: Wand | null = null;
  kletterei: Kletterei | null = null;
  kletterZielY = 0;
  cx = 0;
  cy = 0;
  animation: Animation = "lauf";
  animStart = 0;

  private masse: () => Masse;
  private u: Umgebung;
  private melden: (m: Meldung) => void;

  constructor(masse: () => Masse, u: Umgebung, seite: "links" | "rechts", jetzt: number, melden: (m: Meldung) => void) {
    this.masse = masse;
    this.u = u;
    this.melden = melden;
    const { bw } = masse();
    this.besuchEnde = jetzt + this.zw(40_000, 120_000);
    this.naechstesNiesen = jetzt + this.zw(8_000, 20_000);
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

  /** x so, dass die Körpermitte über der Fläche bleibt. */
  private klemmeAufFlaeche(x: number, r: Rechteck) {
    const { bw } = this.masse();
    return Math.min(Math.max(x, r.left - bw / 2), r.right - bw / 2);
  }

  setzeUmgebung(u: Umgebung) {
    this.u = u;
  }

  // ── Posen ───────────────────────────────────────────────────────────────

  private stehPose(): Pose {
    const { bh, fuss } = this.masse();
    return { left: this.x, top: this.fussY - bh + fuss, rot: 0, flip: this.richtung < 0 };
  }

  private kletterPose(wand: Wand, cx: number, cy: number): Pose {
    const { bw, bh } = this.masse();
    // Kopf nach oben, Füße an der Wand.
    return wand.seite === "rechts"
      ? { left: cx - bw / 2, top: cy - bh / 2, rot: -90, flip: false }
      : { left: cx - bw / 2, top: cy - bh / 2, rot: 90, flip: true };
  }

  private starteUebergang(nach: Pose, dauer: number, animation: Animation, jetzt: number, danach: (j: number) => void) {
    this.uebergang = { von: this.aktuellePose(jetzt), nach, t0: jetzt, dauer, animation, danach };
    this.zustand = "uebergang";
  }

  // ── Handlungen ──────────────────────────────────────────────────────────

  private laufeZu(x: number, danach: ((jetzt: number) => void) | null = null) {
    this.zielX = x;
    this.richtung = x >= this.x ? 1 : -1;
    this.zustand = "laufen";
    this.nachAnkunft = danach;
  }

  private springe(x1: number, y1: number, danach: Ort, jetzt: number, startRot = 0) {
    const dx = x1 - this.x;
    const dy = this.fussY - y1; // > 0 = nach oben
    if (Math.abs(dx) > 2) this.richtung = dx > 0 ? 1 : -1;
    this.sprung = {
      x0: this.x,
      y0: this.fussY,
      x1,
      y1,
      t0: jetzt,
      dauer: 450 + Math.abs(dy) * 1.1 + Math.abs(dx) * 0.7,
      bogen: dy > 0 ? dy / 2 + 40 : 30,
      danach,
      startRot,
    };
    this.zustand = "sprung";
  }

  private fallen(jetzt: number) {
    this.ort = { art: "boden" };
    this.springe(this.x, this.u.hoehe, { art: "boden" }, jetzt);
    if (this.sprung) this.sprung.bogen = 8;
  }

  /** Zur Wand drehen (Übergang), dann Klimmzug um Klimmzug hoch. */
  private klettere(wand: Wand, zielY: number, jetzt: number) {
    const { bw, bh, fuss } = this.masse();
    this.wand = wand;
    this.kletterZielY = zielY;
    this.richtung = wand.seite === "rechts" ? 1 : -1;
    this.cx = wand.seite === "rechts" ? wand.x - bh / 2 + fuss : wand.x + bh / 2 - fuss;
    this.cy = this.fussY - bw / 2;
    this.starteUebergang(this.kletterPose(wand, this.cx, this.cy), 420, "idle", jetzt, (j) => {
      this.zustand = "klettern";
      this.kletterei = {
        phase: "griff",
        t0: j,
        dauer: 250,
        vonCy: this.cy,
        nachCy: this.cy,
        zuegeBisRast: Math.round(this.zw(4, 6)),
        frameBasis: 0,
        zuege: 0,
      };
    });
  }

  /** Oben am Popup angekommen: über die Kante ziehen und hinstellen. */
  private hochziehen(wand: Wand, r: Rechteck, jetzt: number) {
    const { bw } = this.masse();
    this.ort = { art: "flaeche", q: wand.q! };
    this.fussY = r.top;
    if (wand.seite === "rechts") {
      this.x = r.left - bw * 0.15;
      this.richtung = 1;
    } else {
      this.x = r.right - bw * 0.85;
      this.richtung = -1;
    }
    this.kletterei = null;
    this.starteUebergang(this.stehPose(), 750, "klettern", jetzt, (j) => {
      this.wand = null;
      this.zustand = "landen";
      this.bis = j + 260;
    });
  }

  /** Von der Wand abstoßen: auf eine Fläche in Reichweite oder auf den Boden. */
  private wandAbsprung(jetzt: number) {
    const { bw, bh } = this.masse();
    const wand = this.wand!;
    const startRot = wand.seite === "links" ? -90 : 90; // Kopf oben, nach dem Spiegeln
    this.x = this.cx - bw / 2;
    this.fussY = this.cy + bh / 2;
    this.richtung = wand.seite === "links" ? 1 : -1;
    this.wand = null;
    this.kletterei = null;
    this.ort = { art: "boden" };
    const ziel = this.waehleFlaeche((f) => {
      const mitte = (f.r.left + f.r.right) / 2;
      return (
        Math.abs(mitte - (this.x + bw / 2)) < SPRUNG_WEIT_PX &&
        (mitte - this.x) * this.richtung > 0 &&
        this.fussY - f.r.top <= SPRUNG_MAX_PX * 0.5
      );
    });
    if (ziel && this.u.zufall() < 0.6) {
      this.springe(this.landeX(ziel.r), ziel.r.top, { art: "flaeche", q: ziel.q }, jetzt, startRot);
    } else {
      this.springe(this.klemmeX(this.x + this.richtung * this.zw(80, 200)), this.u.hoehe, { art: "boden" }, jetzt, startRot);
    }
  }

  private landeX(r: Rechteck) {
    const { bw } = this.masse();
    const rand = Math.min(10, (r.right - r.left) / 2);
    return this.zw(r.left + rand, r.right - rand) - bw / 2;
  }

  private waehleFlaeche(passt: (f: Flaeche) => boolean): Flaeche | null {
    const kandidaten = this.u.flaechen().filter(passt);
    if (!kandidaten.length) return null;
    return kandidaten[Math.floor(this.u.zufall() * kandidaten.length)];
  }

  /** Hatschi! Nur im Stehen, nicht beim Klettern/Springen. */
  private niese(jetzt: number) {
    this.zustand = "niesen";
    this.niesenStart = jetzt;
    this.brandGelegt = false;
    this.naechstesNiesen = jetzt + NIESEN_PAUSE_MS + this.zw(0, 30_000);
  }

  /** Wo das Feuer hinkommt: 1–2 Brandflecken vorne im Feuerstoß. */
  private brandLegen() {
    const { bw, bh, fuss, maulX, maulY, feuerLaenge } = this.masse();
    const top = this.fussY - bh + fuss;
    const mx = this.richtung > 0 ? this.x + maulX : this.x + bw - maulX;
    const my = top + maulY;
    const anzahl = this.u.zufall() < 0.5 ? 1 : 2;
    for (let i = 0; i < anzahl; i++) {
      const weit = this.zw(0.55, 0.95) * feuerLaenge;
      const x = Math.min(Math.max(mx + this.richtung * weit, 10), this.u.breite - 10);
      const y = Math.min(Math.max(my + this.zw(-10, 14), 10), this.u.hoehe - 4);
      this.melden({ typ: "haeufchen", art: "brand", x: x / this.u.breite, y: y / this.u.hoehe });
    }
  }

  streicheln(jetzt: number): boolean {
    if (["raus", "sprung", "klettern", "uebergang", "niesen"].includes(this.zustand)) return false;
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
    const mitte = this.x + bw / 2;

    // Ab und zu Feuer niesen (Mark, 11.11.) — überall, wo er steht.
    if (jetzt >= this.naechstesNiesen && jetzt < this.besuchEnde && u.zufall() < 0.18) {
      return this.niese(jetzt);
    }

    if (this.ort.art === "flaeche") {
      const r = this.ort.q.rechteck();
      if (!r) return this.fallen(jetzt);
      const ende = jetzt >= this.besuchEnde;
      const breit = r.right - r.left;
      // Auch oben auf Text & Co. (Mark: „kann er oben auf den Text Häufchen machen?“).
      if (!ende && !this.haeufchenGemacht && w < 0.1) {
        this.zustand = "haeufchen";
        this.bis = jetzt + 1800;
        return;
      }
      if (!ende && !this.geschlafen && breit >= bw * 0.5 && w < 0.22) {
        this.zustand = "schlafen";
        this.geschlafen = true;
        this.bis = jetzt + this.zw(6000, 14000);
        return;
      }
      if (!ende && breit > bw * 0.4 && w < 0.45) {
        this.laufeZu(this.landeX(r));
        return;
      }
      if (!ende && w < 0.85) {
        // Zur nächsten Fläche hüpfen — nach oben nur in Sprungweite.
        const ziel = this.waehleFlaeche((f) => {
          const fm = (f.r.left + f.r.right) / 2;
          const gleich = Math.abs(f.r.top - r.top) < 3 && f.r.left < r.right && f.r.right > r.left;
          return (
            !gleich &&
            Math.abs(fm - mitte) < SPRUNG_WEIT_PX &&
            r.top - f.r.top <= SPRUNG_MAX_PX &&
            f.r.top - r.top > -SPRUNG_MAX_PX
          );
        });
        if (ziel) {
          this.springe(this.landeX(ziel.r), ziel.r.top, { art: "flaeche", q: ziel.q }, jetzt);
          return;
        }
      }
      // Runter auf den Boden, neben die Fläche.
      const rechts = u.zufall() < 0.5;
      const zx = rechts ? r.right + this.zw(10, 80) : r.left - bw - this.zw(10, 80);
      this.ort = { art: "boden" };
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
    if (!this.haeufchenGemacht && w < 0.1) {
      this.zustand = "haeufchen";
      this.bis = jetzt + 1800;
      return;
    }
    if (w < 0.45) {
      const ziel = this.waehleFlaeche((f) => u.hoehe - f.r.top <= SPRUNG_MAX_PX && u.hoehe - f.r.top > 20);
      if (ziel) {
        const zm = (ziel.r.left + ziel.r.right) / 2;
        if (Math.abs(zm - mitte) < 220) {
          this.springe(this.landeX(ziel.r), ziel.r.top, { art: "flaeche", q: ziel.q }, jetzt);
        } else {
          const absprung = this.klemmeX(zm - bw / 2 - Math.sign(zm - mitte) * 120);
          this.laufeZu(absprung, (j) => {
            const r = ziel.q.rechteck();
            if (r) this.springe(this.landeX(r), r.top, { art: "flaeche", q: ziel.q }, j);
          });
        }
        return;
      }
    }
    if (w < 0.6) {
      const waende = u.waende().filter((f) => u.hoehe - f.r.top > SPRUNG_MAX_PX * 0.6);
      if (waende.length) {
        const { q, r } = waende[Math.floor(u.zufall() * waende.length)];
        // Wand ist rechts vom Pet, wenn er links vom Popup steht.
        const vonLinks = mitte < (r.left + r.right) / 2;
        const wand: Wand = vonLinks ? { x: r.left, seite: "rechts", q } : { x: r.right, seite: "links", q };
        const start = this.klemmeX(vonLinks ? r.left - bw * 0.6 : r.right - bw * 0.4);
        this.laufeZu(start, (j) => this.klettere(wand, r.top, j));
        return;
      }
    }
    if (w < 0.7) {
      // Bildschirmrand hochklettern, oben kurz hängen, dann abspringen.
      const links = u.zufall() < 0.5;
      const wand: Wand = links ? { x: 0, seite: "links", q: null } : { x: u.breite, seite: "rechts", q: null };
      this.laufeZu(links ? 0 : this.klemmeX(u.breite), (j) => this.klettere(wand, this.zw(0.3, 0.6) * u.hoehe, j));
      return;
    }
    if (w < 0.78) {
      this.springe(this.klemmeX(this.x + this.richtung * this.zw(30, 70)), u.hoehe, { art: "boden" }, jetzt);
      return;
    }
    this.laufeZu(this.zw(0, Math.max(0, u.breite - bw)));
  }

  // ── Takt ────────────────────────────────────────────────────────────────

  private kletterTakt(jetzt: number) {
    const { bw, bh } = this.masse();
    const wand = this.wand!;
    const k = this.kletterei!;
    if (wand.q) {
      const r = wand.q.rechteck();
      if (!r) return this.wandAbsprung(jetzt);
      this.kletterZielY = r.top;
    }
    const t = Math.min(1, (jetzt - k.t0) / k.dauer);
    if (k.phase === "zug") this.cy = k.vonCy + (k.nachCy - k.vonCy) * auslaufen(t);
    if (k.phase === "rutsch") this.cy = k.vonCy + (k.nachCy - k.vonCy) * glatt(t);
    if (t < 1) return;

    // Phase vorbei → oben angekommen?
    if (wand.q && this.cy - bw / 2 <= this.kletterZielY - bh * 0.35) {
      return this.hochziehen(wand, wand.q.rechteck()!, jetzt);
    }
    if (!wand.q && this.cy <= this.kletterZielY) {
      this.zustand = "haengen";
      this.bis = jetzt + this.zw(1800, 3500);
      return;
    }
    const naechste = (phase: KletterPhase, dauer: number, nachCy = this.cy) => {
      k.phase = phase;
      k.t0 = jetzt;
      k.dauer = dauer;
      k.vonCy = this.cy;
      k.nachCy = nachCy;
    };
    if (k.phase === "zug") {
      k.zuege += 1;
      k.zuegeBisRast -= 1;
      k.frameBasis = (k.frameBasis + KLETTER_FRAMES / 2) % KLETTER_FRAMES;
      if (k.zuege > 2 && this.u.zufall() < 0.12) return naechste("rutsch", 280, this.cy + this.zw(10, 18));
      if (k.zuegeBisRast <= 0) {
        k.zuegeBisRast = Math.round(this.zw(4, 6));
        return naechste("rast", this.zw(900, 1700));
      }
      return naechste("griff", this.zw(200, 350));
    }
    // griff / rast / rutsch vorbei → nächster Klimmzug, je höher desto mühsamer.
    naechste("zug", this.zw(420, 600) + Math.min(k.zuege, 15) * 10, this.cy - this.zw(22, 32));
  }

  tick(jetzt: number, dt: number) {
    const { bw } = this.masse();
    const u = this.u;

    // Boden folgt der Fenstergröße, Fläche ihrem Element (Scrollen, Popup zu).
    if (["laufen", "idle", "freuen", "haeufchen", "schlafen", "landen", "niesen", "raus"].includes(this.zustand)) {
      if (this.ort.art === "boden") {
        this.fussY = u.hoehe;
      } else {
        const r = this.ort.q.rechteck();
        if (!r) {
          this.fallen(jetzt);
        } else {
          this.fussY = r.top;
          this.x = this.klemmeAufFlaeche(this.x, r);
          this.zielX = this.klemmeAufFlaeche(this.zielX, r);
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
            this.bis = jetzt + 400;
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
        const t = (jetzt - s.t0) / s.dauer;
        if (s.danach.art === "flaeche") {
          const r = s.danach.q.rechteck();
          if (!r) {
            s.danach = { art: "boden" };
            s.y1 = u.hoehe;
          } else {
            s.y1 = r.top;
            s.x1 = this.klemmeAufFlaeche(s.x1, r);
          }
        } else s.y1 = u.hoehe;
        if (t >= 1) {
          this.x = s.x1;
          this.fussY = s.y1;
          this.ort = s.danach;
          this.sprung = null;
          this.zustand = "landen";
          this.bis = jetzt + 220;
        } else {
          this.x = s.x0 + (s.x1 - s.x0) * t;
          this.fussY = s.y0 + (s.y1 - s.y0) * t - s.bogen * 4 * t * (1 - t);
        }
        break;
      }
      case "uebergang": {
        const ue = this.uebergang!;
        if (jetzt - ue.t0 >= ue.dauer) {
          this.uebergang = null;
          ue.danach(jetzt);
        }
        break;
      }
      case "klettern":
        this.kletterTakt(jetzt);
        break;
      case "haengen":
        if (jetzt >= this.bis) this.wandAbsprung(jetzt);
        break;
      case "landen":
        if (jetzt >= this.bis) {
          this.zustand = "idle";
          this.bis = jetzt + this.zw(500, 1400);
        }
        break;
      case "haeufchen":
        if (jetzt >= this.bis) {
          const { fuss } = this.masse();
          // Liegt hinter dem Schwanz.
          const schwanz = this.richtung > 0 ? this.x + fuss : this.x + bw - fuss;
          this.melden({ typ: "haeufchen", art: "haeufchen", x: schwanz / u.breite, y: this.fussY / u.hoehe });
          this.haeufchenGemacht = true;
          this.zustand = "idle";
          this.bis = jetzt + 1500;
        }
        break;
      case "niesen": {
        const t = jetzt - this.niesenStart;
        // Flecken entstehen, wenn das Feuer am weitesten reicht.
        if (!this.brandGelegt && t >= FEUER_AB_MS + FEUER_MS * 0.4) {
          this.brandGelegt = true;
          this.brandLegen();
        }
        if (t >= Math.max(NIESEN_MS, FEUER_AB_MS + FEUER_MS)) {
          this.zustand = "idle";
          this.bis = jetzt + this.zw(800, 1800);
        }
        break;
      }
      case "idle":
      case "freuen":
      case "schlafen":
        if (jetzt >= this.bis) this.entscheide(jetzt);
        break;
    }

    const anim = this.gewuenschteAnimation(jetzt);
    if (anim !== this.animation) {
      this.animation = anim;
      this.animStart = jetzt;
    }
  }

  private gewuenschteAnimation(jetzt: number): Animation {
    switch (this.zustand) {
      case "laufen":
      case "raus":
        return "lauf";
      case "klettern":
        return this.kletterei && this.kletterei.phase === "rast" ? "idle" : "klettern";
      case "haengen":
        return "idle";
      case "uebergang":
        return this.uebergang?.animation ?? "idle";
      case "sprung":
        return "sprung";
      case "freuen":
        return "freuen";
      case "schlafen":
        return "schlafen";
      case "niesen":
        return jetzt - this.niesenStart < NIESEN_MS ? "niesen" : "idle";
      default:
        return "idle";
    }
  }

  private aktuellePose(jetzt: number): Pose {
    const ue = this.uebergang;
    if (this.zustand === "uebergang" && ue) {
      const t = glatt(Math.min(1, (jetzt - ue.t0) / ue.dauer));
      // Beim Hochziehen erst hoch, dann drüber: Höhe läuft voraus, Seite hinterher.
      const tHoch = glatt(Math.min(1, t * 1.6));
      return {
        left: ue.von.left + (ue.nach.left - ue.von.left) * t,
        top: ue.von.top + (ue.nach.top - ue.von.top) * tHoch,
        rot: ue.von.rot + (ue.nach.rot - ue.von.rot) * t,
        flip: ue.nach.flip,
      };
    }
    if ((this.zustand === "klettern" || this.zustand === "haengen") && this.wand) {
      const p = this.kletterPose(this.wand, this.cx, this.cy);
      // Verschnaufen/Hängen: wackelt vor Anstrengung.
      const rast = this.zustand === "haengen" || this.kletterei?.phase === "rast";
      if (rast) p.rot += Math.sin(jetzt / 90) * 2.5;
      if (this.kletterei?.phase === "griff") p.rot += Math.sin(jetzt / 60) * 1.2;
      return p;
    }
    const p = this.stehPose();
    if (this.zustand === "sprung" && this.sprung) {
      const t = Math.min(1, (jetzt - this.sprung.t0) / this.sprung.dauer);
      // Nase hoch beim Steigen, runter beim Fallen; Absprung von der Wand dreht aus.
      const neigung = (p.flip ? 18 : -18) * (1 - 2 * t);
      const aus = Math.min(1, t / 0.35);
      p.rot = this.sprung.startRot * (1 - aus) + neigung * aus;
    }
    return p;
  }

  darstellung(jetzt: number): Darstellung {
    const { bw, bh } = this.masse();
    const p = this.aktuellePose(jetzt);
    const k = this.kletterei;
    let frame: number | null = null;
    if (this.zustand === "klettern" && k && k.phase !== "rast") {
      // Beine bewegen sich nur beim Klimmzug, beim Nachgreifen stehen sie.
      const fortschritt = k.phase === "zug" ? Math.min(1, (jetzt - k.t0) / k.dauer) : 0;
      frame = Math.floor(k.frameBasis + fortschritt * (KLETTER_FRAMES / 2)) % KLETTER_FRAMES;
    }
    const vertikal = Math.abs(p.rot) > 45;
    const kopfX = vertikal ? p.left + bw / 2 : p.left + (p.flip ? bw * 0.2 : bw * 0.8);
    const kopfY = vertikal ? p.top + bh / 2 - bw / 2 : p.top;
    let feuer: Darstellung["feuer"] = null;
    if (this.zustand === "niesen" && jetzt - this.niesenStart >= FEUER_AB_MS) {
      const { maulX, maulY } = this.masse();
      feuer = {
        start: this.niesenStart + FEUER_AB_MS,
        x: p.flip ? p.left + bw - maulX : p.left + maulX,
        y: p.top + maulY,
        flip: p.flip,
      };
    }
    const schwitzt =
      this.zustand === "haengen" || (this.zustand === "klettern" && !!k && (k.phase === "rast" || k.zuege >= 3));
    return {
      left: p.left,
      top: p.top,
      transform: `rotate(${p.rot.toFixed(1)}deg)${p.flip ? " scaleX(-1)" : ""}`,
      animation: this.animation,
      animStart: this.animStart,
      frame,
      feuer,
      hockt: this.zustand === "haeufchen" || this.zustand === "landen",
      schlaeft: this.zustand === "schlafen",
      schwitzt,
      kopfX,
      kopfY,
    };
  }
}
