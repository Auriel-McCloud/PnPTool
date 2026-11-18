/**
 * Vampir-Fledermaus (Mark, 17.11.2026): „eine süße Fledermaus, die ab Stufe 3
 * auch zu einem Vampir werden kann“ — „Sie bleibt eine Fledermaus, sie kann
 * sich aber in einen Vampir verwandeln, wenn sie möchte.“
 *
 * Gleiche Schnittstelle wie `PetBewegung`/`FlugBewegung` (Zustandsautomat ohne
 * React/DOM). Was sie tut:
 *
 * - Als Fledermaus fliegt sie (kommt wie Bärbel in irgendeiner Höhe oder von
 *   oben herein) und **hängt kopfüber** unter Kanten: unter Popups, Knöpfen,
 *   Textzeilen, Kacheln oder oben am Bildschirmrand (Mark: „dass sie kopfüber
 *   rumhängt ist auch wichtig“). Dort döst sie, schläft manchmal lange und
 *   lässt ab und zu ein Häufchen fallen.
 * - Steht ein Futternapf da, landet sie daneben und frisst.
 * - Ab Schritt 3 landet sie manchmal und verwandelt sich in einer Rauchwolke
 *   mit kleinen Fledermäusen in den Vampir ihrer Stufe (3 Kind, 4 Teen, 5 ~18,
 *   6 erwachsen). Als Vampir läuft sie auf dem Boden oder auf einer Fläche,
 *   wirft beim Streicheln eine Kusshand; der erwachsene Mann setzt sich
 *   manchmal den Zylinder auf und lüftet ihn zum Gruß (Gehstock hat er immer).
 *   Danach wird sie wieder zur Fledermaus und fliegt weiter.
 * - Zutraulichkeit (Mark): wer ihr sehr vertraut, sieht sie öfter und länger
 *   als Vampir — zählt die Zutraulichkeit des Spielers, auf dessen Tablet sie ist.
 * - Bärbel will sie unbedingt fressen (flug.ts): sie flieht; ab und zu
 *   erwischt Bärbel sie, verschluckt sie, rülpst und spuckt sie zerzaust aus.
 * - Antippen = freuen, 3 s halten = packen und werfen (wie die anderen Pets).
 * - Trinkt Punkte (Mark, 18.11.2026: „wie eine Fruitbat in die Kugel beißen und
 *   sie dann austrinken“): schwebt flatternd unter einem gefüllten Punkt im
 *   Charakterbogen, beißt hinein und trinkt ihn leer (Tropfen fliegen ins Maul),
 *   gern die Reihe entlang. Nur Optik; der Punkt läuft in 10–15 Minuten wieder
 *   voll (punkte.ts). Höchstens 6 je Besuch. Der Vampir wird dafür kurz wieder
 *   zur Fledermaus.
 */

import { PACKEN_MS, type Darstellung, type Masse, type Meldung, type Quelle, type Umgebung } from "./bewegung";
import type { PetSteuerung } from "./flug";
import { FLEDERMAUS_TAKT, type FledermausStufe } from "./fledermausstufen";
import { nachbarPunkt, punktAnbeissen, punktLage, punktNachfuellen, punktTrinken, sichtbarePunkte, tropfen } from "./punkte";
import { beuteTiere } from "./treffen";

type Zustand =
  | "flattern" // zu einem Ziel
  | "fliehen" // schnell weg (Bärbel, Feuer)
  | "haengen"
  | "schlafen"
  | "stehen"
  | "fressen"
  | "verwandeln"
  | "v_stehen"
  | "v_laufen"
  | "v_freuen"
  | "v_hut"
  | "gehalten"
  | "getragen"
  | "wurf"
  | "verschluckt"
  | "taumeln"
  | "trinken" // schwebt unter einem Punkt und trinkt ihn aus
  | "raus";

/** Wo sie gerade ist: unter einer Kante hängend, auf etwas stehend, oder nirgends. */
type Ort = { art: "haengen" | "stehen"; q: Quelle | null; anteil: number } | null;

export interface FledermausOptionen {
  petId: string;
  /** Maße und Anker der Stufe (Sprite-Pixel, fledermausstufen.ts). */
  stufe: FledermausStufe;
  /** Ab Schritt 3: darf sich in den Vampir verwandeln. */
  kannVerwandeln: boolean;
  /** Erwachsener Mann: Zylinder manchmal auf (Mark, 17.11.2026). */
  zylinder: boolean;
  /** Zutraulichkeit des Spielers, auf dessen Tablet sie gerade ist. */
  zutraulich: number;
}

const FLATTER_PX_S = 230;
const FLUCHT_PX_S = 430;
const LAUF_PX_S = 40;
const WURF_BREMSE = 1.6;
const MAX_WURF_PX_S = 2600;
const BESUCH_MIN_MS = 60_000;
const BESUCH_MAX_MS = 150_000;
const takt = (a: string) => FLEDERMAUS_TAKT[a].frames * FLEDERMAUS_TAKT[a].ms;
const VERWANDELN_MS = takt("verwandeln");
/** Ab hier (Wolke am dichtesten) steht die andere Gestalt drin. */
const WECHSEL_MS = 8 * FLEDERMAUS_TAKT.verwandeln.ms;
/** Kleine Wolke beim Zylinder aufsetzen/absetzen. */
const HUTPUFF_MS = 700;
/** Zutraulichkeit, ab der sie voll vertraut (Annahme Neko). */
const VOLL_ZUTRAULICH = 40;
/** Verschluckt, aber Bärbel spuckt nie aus (Tablet weg) — dann kommt sie selbst raus. */
const NOTAUSGANG_MS = 8000;
/** Punkte trinken (18.11.2026, Annahmen Neko): Biss, Austrinken, höchstens so viele je Besuch. */
const BISS_MS = 320;
/** Austrinken je Punkt (Mark, 18.11.2026: „eher so 5–6 Sekunden, 2 Sekunden ist sehr schnell“). */
const AUSTRINKEN_MS: [number, number] = [5000, 6000];
const TRINK_MAX = 6;

export class FledermausBewegung implements PetSteuerung {
  private x: number;
  private y: number;
  private zustand: Zustand = "flattern";
  private form: "fledermaus" | "vampir" = "fledermaus";
  private ziel = { x: 0, y: 0 };
  private dort: ((jetzt: number) => void) | null = null;
  private ort: Ort = null;
  private bis = 0;
  private animStart: number;
  private flip = false;
  private kipp = 0;
  private t0: number;
  private besuchEnde: number;
  private freudeStart = -1e9;
  private puffStart: number | null = null;
  private puffZiel: "fledermaus" | "vampir" = "vampir";
  private puffDanach: ((jetzt: number) => void) | null = null;
  private hutPuff: number | null = null;
  private hut = false;
  private vampirBis = 0;
  private naechsteVerwandlung: number;
  private haeufchenGemacht = false;
  private haeufchenUm = 0;
  private napfId: string | null = null;
  private fressGemeldet = false;
  private vx = 0;
  private vy = 0;
  private griff: { start: number; vorher: Zustand; bis: number } | null = null;
  private fingerSpur: { x: number; y: number; t: number }[] = [];
  private rausGemeldet = false;
  private rausSeite: "links" | "rechts" | "oben" = "rechts";
  private verschlucktSeit = 0;
  private trink: { id: string; t0: number; dauer: number } | null = null;
  /** Von welcher Seite sie in die Kugel beißt (−1 links, 1 rechts). */
  private trinkSeite = 1;
  private getrunken = 0;
  private naechstesTrinken: number;

  private masse: () => Masse;
  private u: Umgebung;
  private melden: (m: Meldung) => void;
  private o: FledermausOptionen;

  constructor(
    masse: () => Masse,
    u: Umgebung,
    seite: "links" | "rechts",
    jetzt: number,
    melden: (m: Meldung) => void,
    o: FledermausOptionen,
  ) {
    this.masse = masse;
    this.u = u;
    this.melden = melden;
    this.o = o;
    const { bw, bh } = masse();
    const z = u.zufall;
    this.t0 = jetzt;
    this.animStart = jetzt;
    // Rein wie Bärbel: oft von oben, sonst von der Seite in irgendeiner Höhe.
    if (z() < 0.35) {
      this.x = u.breite * (0.1 + z() * 0.7);
      this.y = -bh - 10;
    } else {
      this.x = seite === "links" ? -bw - 10 : u.breite + 10;
      this.y = u.hoehe * (0.05 + z() * 0.45);
    }
    this.besuchEnde = jetzt + BESUCH_MIN_MS + z() * (BESUCH_MAX_MS - BESUCH_MIN_MS);
    this.naechsteVerwandlung = jetzt + 8_000 + z() * 20_000;
    this.naechstesTrinken = jetzt + 5_000 + z() * 12_000;
    this.flatternZu(this.zufallsZiel(), jetzt);
    beuteTiere.set(o.petId, {
      mitte: () => this.mitte(),
      bedroht: (j, bx, by) => this.bedroht(j, bx, by),
      verschlucken: (j) => this.verschlucken(j),
      ausspucken: (j, sx, sy) => this.ausspucken(j, sx, sy),
    });
  }

  setzeUmgebung(u: Umgebung) {
    this.u = u;
  }

  /** Neue Zutraulichkeit vom Server (Streicheln/Füttern). */
  setzeZutraulich(wert: number) {
    this.o = { ...this.o, zutraulich: wert };
  }

  aufraeumen() {
    this.trinkAbbrechen();
    beuteTiere.delete(this.o.petId);
  }

  get gepackt() {
    return this.zustand === "getragen";
  }

  // ── Hilfen ──────────────────────────────────────────────────────────────

  private s() {
    return this.masse().bw / this.o.stufe.breite;
  }

  /** 0..1: wie sehr sie dem Spieler hier vertraut. */
  private vertrauen() {
    return Math.max(0, Math.min(1, this.o.zutraulich / VOLL_ZUTRAULICH));
  }

  private zufallsZiel() {
    const { bw, bh } = this.masse();
    const z = this.u.zufall;
    const links = this.u.links ?? 0;
    return {
      x: links + z() * Math.max(10, this.u.breite - links - bw),
      y: this.u.hoehe * 0.03 + z() * Math.max(10, this.u.hoehe * 0.6 - bh * 0.5),
    };
  }

  /** Körpermitte (für Bärbels Jagd und Treffer). */
  private mitte() {
    const { bw, bh } = this.masse();
    const s = this.s();
    const st = this.o.stufe;
    if (this.form === "vampir" && st.kopfVampir) return { x: this.x + bw / 2, y: (this.y + st.kopfVampir[1] * s + this.y + bh) / 2 };
    if (this.zustand === "haengen" || this.zustand === "schlafen") return { x: this.x + bw / 2, y: this.y + ((st.griff + st.kopfHaengen[1]) / 2) * s };
    if (this.zustand === "stehen" || this.zustand === "fressen") return { x: this.x + bw / 2, y: this.y + ((st.kopfStehen[1] + st.hoehe) / 2) * s };
    return { x: this.x + bw / 2, y: this.y + bh / 2 };
  }

  /** Rechteck der Kante/Fläche, an der sie gerade ist (null = weg). Ohne Quelle: Decke bzw. Boden. */
  private ortRechteck() {
    if (!this.ort) return null;
    if (this.ort.q) return this.ort.q.rechteck();
    const { breite, hoehe } = this.u;
    return this.ort.art === "haengen"
      ? { left: 0, right: breite, top: -20, bottom: 0 }
      : { left: this.u.links ?? 0, right: breite, top: hoehe, bottom: hoehe + 20 };
  }

  /** Lage zum Ort: hängend unter der Unterkante, stehend auf der Oberkante. */
  private ortLage(r: { left: number; right: number; top: number; bottom: number }, anteil: number, art: "haengen" | "stehen") {
    const { bw, bh } = this.masse();
    const s = this.s();
    const mx = r.left + (r.right - r.left) * anteil;
    const x = Math.min(Math.max(mx - bw / 2, -bw * 0.2), this.u.breite - bw * 0.8);
    const y = art === "haengen" ? r.bottom - this.o.stufe.griff * s : r.top - bh + this.o.stufe.fussLuft * s;
    return { x, y };
  }

  /** Eine Kante zum Kopfüber-Hängen: Unterkanten von Flächen (Text, Knöpfe,
   *  Kacheln, Popups) im oberen Teil des Schirms, oder die Bildschirm-Oberkante. */
  private haengePlatz(): Ort {
    const { bw, bh } = this.masse();
    const z = this.u.zufall;
    const kandidaten = this.u
      .flaechen()
      .filter((f) => f.r.right - f.r.left >= bw * 0.35 && f.r.bottom > 20 && f.r.bottom < this.u.hoehe - bh * 0.9);
    if (kandidaten.length && z() < 0.8) {
      const f = kandidaten[Math.floor(z() * kandidaten.length)];
      return { art: "haengen", q: f.q, anteil: 0.2 + z() * 0.6 };
    }
    return { art: "haengen", q: null, anteil: 0.1 + z() * 0.8 };
  }

  /** Wo sie als Vampir stehen kann: Boden oder eine breite Fläche mit Kopffreiheit. */
  private stehPlatz(): Ort {
    const { bw, bh } = this.masse();
    const z = this.u.zufall;
    const kandidaten = this.u.flaechen().filter((f) => f.r.right - f.r.left >= bw * 1.4 && f.r.top > bh + 10);
    if (kandidaten.length && z() < 0.45) {
      const f = kandidaten[Math.floor(z() * kandidaten.length)];
      return { art: "stehen", q: f.q, anteil: 0.25 + z() * 0.5 };
    }
    return { art: "stehen", q: null, anteil: 0.1 + z() * 0.8 };
  }

  private setzeAnim(jetzt: number) {
    this.animStart = jetzt;
  }

  // ── Abläufe ─────────────────────────────────────────────────────────────

  private flatternZu(ziel: { x: number; y: number }, jetzt: number, dort: ((jetzt: number) => void) | null = null) {
    this.trinkAbbrechen();
    this.form = "fledermaus";
    this.ort = null;
    this.ziel = ziel;
    this.dort = dort;
    this.zustand = "flattern";
    this.setzeAnim(jetzt);
  }

  /** Zum Ort fliegen und dort hängen bzw. landen. */
  private zumOrt(ort: NonNullable<Ort>, jetzt: number, dann: (jetzt: number) => void) {
    const r = ort.q ? ort.q.rechteck() : this.ortRechteckFuer(ort);
    if (!r) {
      this.flatternZu(this.zufallsZiel(), jetzt);
      return;
    }
    const p = this.ortLage(r, ort.anteil, ort.art);
    this.flatternZu(p, jetzt, (j) => {
      const r2 = ort.q ? ort.q.rechteck() : this.ortRechteckFuer(ort);
      if (!r2) {
        this.flatternZu(this.zufallsZiel(), j);
        return;
      }
      this.ort = ort;
      dann(j);
    });
  }

  private ortRechteckFuer(ort: NonNullable<Ort>) {
    const alt = this.ort;
    this.ort = ort;
    const r = this.ortRechteck();
    this.ort = alt;
    return r;
  }

  private haengen(jetzt: number) {
    const z = this.u.zufall;
    // Manchmal schläft sie lange (bis 3 Minuten), sonst döst sie eine Weile.
    if (z() < 0.3) {
      this.zustand = "schlafen";
      this.bis = jetzt + 40_000 + z() * 140_000;
    } else {
      this.zustand = "haengen";
      this.bis = jetzt + 8_000 + z() * 17_000;
    }
    this.haeufchenUm = !this.haeufchenGemacht && z() < 0.35 ? jetzt + 2000 + z() * 6000 : 0;
    this.setzeAnim(jetzt);
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
    this.zustand = "raus";
  }

  private rausMelden() {
    if (this.rausGemeldet) return;
    this.rausGemeldet = true;
    const seite =
      this.rausSeite === "oben" ? (this.x + this.masse().bw / 2 > this.u.breite / 2 ? "rechts" : "links") : this.rausSeite;
    this.melden({ typ: "raus", seite });
  }

  /** Rauchwolke; in ihrer dichtesten Phase wechselt die Gestalt. */
  private verwandeln(jetzt: number, ziel: "fledermaus" | "vampir", danach: (jetzt: number) => void) {
    this.zustand = "verwandeln";
    this.puffStart = jetzt;
    this.puffZiel = ziel;
    this.puffDanach = danach;
    this.hutPuff = null;
  }

  private zumVampir(jetzt: number) {
    const z = this.u.zufall;
    const f = this.vertrauen();
    // Wer ihr vertraut, sieht den Vampir länger (Mark, 17.11.2026).
    this.vampirBis = jetzt + (15_000 + z() * 15_000) * (1 + 2 * f);
    this.hut = false;
    this.verwandeln(jetzt, "vampir", (j) => this.vampirStehen(j, 1500 + z() * 1500));
  }

  private zurFledermaus(jetzt: number, danach?: (jetzt: number) => void) {
    const z = this.u.zufall;
    this.verwandeln(jetzt, "fledermaus", (j) => {
      this.naechsteVerwandlung = j + 20_000 + z() * 40_000;
      // Aus der Wolke hoch in die Luft.
      if (danach) danach(j);
      else this.flatternZu({ x: this.x + (z() - 0.5) * 200, y: Math.max(10, this.y - 160 - z() * 160) }, j);
    });
  }

  private vampirStehen(jetzt: number, dauer: number) {
    this.zustand = "v_stehen";
    this.bis = jetzt + dauer;
    this.setzeAnim(jetzt);
  }

  private entscheiden(jetzt: number) {
    const z = this.u.zufall;
    if (this.form === "vampir") {
      this.entscheidenVampir(jetzt);
      return;
    }
    if (jetzt > this.besuchEnde) {
      this.rausFliegen(jetzt);
      return;
    }
    // Futter riecht sie über den ganzen Schirm.
    const napf = (this.u.spuren?.() ?? []).find((x) => x.art === "napf");
    if (napf && z() < 0.85) {
      const { bw, bh } = this.masse();
      const s = this.s();
      // Neben dem Napf landen, Maul darüber.
      const x = Math.min(Math.max(napf.x - this.o.stufe.maul[0] * s, 0), this.u.breite - bw);
      this.napfId = napf.id;
      this.flatternZu({ x, y: this.u.hoehe - bh + this.o.stufe.fussLuft * s }, jetzt, (j) => {
        this.ort = { art: "stehen", q: null, anteil: (x + bw / 2 - (this.u.links ?? 0)) / Math.max(1, this.u.breite - (this.u.links ?? 0)) };
        this.zustand = "fressen";
        this.fressGemeldet = false;
        this.bis = j + takt("fressen");
        this.setzeAnim(j);
      });
      return;
    }
    if (this.durstig(jetzt) && z() < 0.45 && this.trinkenStarten(jetzt)) return;
    const r = z();
    const f = this.vertrauen();
    const pVampir = 0.12 + 0.38 * f;
    if (this.o.kannVerwandeln && jetzt > this.naechsteVerwandlung && r < pVampir) {
      const ort = this.stehPlatz();
      if (ort) {
        this.zumOrt(ort, jetzt, (j) => this.zumVampir(j));
        return;
      }
    }
    if (r < 0.62) {
      const ort = this.haengePlatz();
      if (ort) {
        this.zumOrt(ort, jetzt, (j) => this.haengen(j));
        return;
      }
    }
    if (r < 0.7) {
      // Kurz landen und stehen (auf dem Boden oder einer Fläche).
      const ort = this.stehPlatz();
      if (ort) {
        this.zumOrt(ort, jetzt, (j) => {
          this.zustand = "stehen";
          this.bis = j + 3000 + z() * 4000;
          this.setzeAnim(j);
        });
        return;
      }
    }
    this.flatternZu(this.zufallsZiel(), jetzt);
  }

  // ── Punkte trinken (18.11.2026) ─────────────────────────────────────────

  /** Wo sie schwebt, um am Punkt zu trinken: seitlich daneben, schräg zur
   *  Kugel geneigt, das Maul beißt in ihren Rand — die Kugel selbst bleibt
   *  sichtbar (dort sieht man sie leer laufen). Maul im Flug-Streifen bei etwa
   *  52 % der Höhe (Augen ~47 %). */
  private trinkPlatz(id: string) {
    const l = punktLage(id);
    if (!l) return null;
    const s = this.s();
    const st = this.o.stufe;
    const mx = l.x + this.trinkSeite * l.r * 1.15;
    const my = l.y + l.r * 0.3;
    return { x: mx - (st.breite / 2) * s, y: my - st.hoehe * 0.52 * s };
  }

  /** Durst? Einen gefüllten Punkt suchen, unter dem Platz zum Schweben ist. */
  private durstig(jetzt: number) {
    return jetzt > this.naechstesTrinken && this.getrunken < TRINK_MAX;
  }

  private trinkenStarten(jetzt: number): boolean {
    const { bh } = this.masse();
    const z = this.u.zufall;
    const punkte = sichtbarePunkte().filter((p) => p.y > 30 && p.y + bh < this.u.hoehe - 4 && p.x > 10 && p.x < this.u.breite - 10);
    if (!punkte.length) return false;
    const p = punkte[Math.floor(z() * punkte.length)];
    return this.zumPunkt(p.id, jetzt);
  }

  private zumPunkt(id: string, jetzt: number): boolean {
    const l = punktLage(id);
    if (l) this.trinkSeite = l.x < this.x + this.masse().bw / 2 ? 1 : -1;
    const platz = this.trinkPlatz(id);
    if (!platz) return false;
    this.flatternZu(platz, jetzt, (j) => {
      if (!punktAnbeissen(id)) {
        this.entscheiden(j);
        return;
      }
      this.trink = { id, t0: j, dauer: AUSTRINKEN_MS[0] + this.u.zufall() * (AUSTRINKEN_MS[1] - AUSTRINKEN_MS[0]) };
      this.zustand = "trinken";
      this.setzeAnim(j);
    });
    return true;
  }

  /** Weggeflogen, gepackt, verschluckt: der Punkt läuft ab seinem Stand wieder voll. */
  private trinkAbbrechen() {
    if (!this.trink) return;
    punktNachfuellen(this.trink.id);
    this.trink = null;
  }

  private entscheidenVampir(jetzt: number) {
    const z = this.u.zufall;
    // Durst: kurz zurück zur Fledermaus, dann in einen Punkt beißen.
    if (this.durstig(jetzt) && !this.hut && z() < 0.25 && sichtbarePunkte().length) {
      this.zurFledermaus(jetzt, (j) => {
        if (!this.trinkenStarten(j)) this.flatternZu(this.zufallsZiel(), j);
      });
      return;
    }
    // Zeit ist um (oder sie muss weiter): Hut ab, dann zurück zur Fledermaus.
    if (jetzt > this.vampirBis || jetzt > this.besuchEnde) {
      if (this.hut) {
        this.hutAbsetzen(jetzt);
        return;
      }
      this.zurFledermaus(jetzt);
      return;
    }
    const r = z();
    if (this.o.zylinder && !this.hut && r < 0.3) {
      // Mark: „Der Mann müsste sich vielleicht noch manchmal einen Zylinder aufsetzen.“
      this.hut = true;
      this.hutPuff = jetzt;
      this.vampirStehen(jetzt, 1200 + z() * 800);
      return;
    }
    if (this.o.zylinder && this.hut && r < 0.45) {
      this.zustand = "v_hut"; // Hut lüften
      this.bis = jetzt + takt("v_hut");
      this.setzeAnim(jetzt);
      return;
    }
    if (r < 0.75) {
      const rect = this.ortRechteck();
      if (!rect) {
        this.zurFledermaus(jetzt);
        return;
      }
      const { bw } = this.masse();
      const breite = Math.max(1, rect.right - rect.left);
      const ziel = 0.08 + z() * 0.84;
      const dx = (ziel - (this.ort?.anteil ?? 0.5)) * breite;
      if (Math.abs(dx) > bw * 0.4) {
        this.ziel = { x: ziel, y: 0 };
        this.flip = dx < 0;
        this.zustand = "v_laufen";
        this.setzeAnim(jetzt);
        return;
      }
    }
    this.vampirStehen(jetzt, 2000 + z() * 3500);
  }

  private hutAbsetzen(jetzt: number) {
    this.hut = false;
    this.hutPuff = jetzt;
    this.vampirStehen(jetzt, 900);
  }

  // ── Bärbel (flug.ts) ────────────────────────────────────────────────────

  private bedroht(jetzt: number, bx: number, by: number) {
    if (["gehalten", "getragen", "wurf", "verschluckt", "raus", "verwandeln", "taumeln"].includes(this.zustand)) return;
    const flucht = () => {
      const m = this.mitte();
      const dx = m.x - bx;
      const dy = m.y - by;
      const d = Math.max(1, Math.hypot(dx, dy));
      const { bw, bh } = this.masse();
      this.flatternZu(
        {
          x: Math.min(this.u.breite - bw, Math.max(0, this.x + (dx / d) * 360)),
          y: Math.min(this.u.hoehe * 0.7, Math.max(0, this.y + (dy / d) * 220 - 60 - bh * 0.2)),
        },
        jetzt,
      );
      this.zustand = "fliehen";
    };
    if (this.form === "vampir") {
      // Schreck: puff — zurück zur Fledermaus und weg.
      this.hut = false;
      this.zurFledermaus(jetzt, () => flucht());
      return;
    }
    flucht();
  }

  private verschlucken(jetzt: number): boolean {
    if (["gehalten", "getragen", "wurf", "verschluckt", "raus", "verwandeln"].includes(this.zustand)) return false;
    this.trinkAbbrechen();
    this.form = "fledermaus";
    this.hut = false;
    this.ort = null;
    this.zustand = "verschluckt";
    this.verschlucktSeit = jetzt;
    return true;
  }

  private ausspucken(jetzt: number, sx: number, sy: number) {
    if (this.zustand !== "verschluckt") return;
    const { bw, bh } = this.masse();
    this.x = sx - bw / 2;
    this.y = sy - bh / 2;
    this.zustand = "taumeln";
    this.vx = (this.u.zufall() - 0.5) * 220;
    this.vy = -120;
    this.bis = jetzt + 2600;
    this.setzeAnim(jetzt);
  }

  erschrecken(jetzt: number) {
    // Feuer/Eis/Blitz eines anderen Pets: wie vor Bärbel fliehen.
    const m = this.mitte();
    this.bedroht(jetzt, m.x + (this.u.zufall() - 0.5) * 80, m.y + 40);
  }

  // ── Takt ────────────────────────────────────────────────────────────────

  tick(jetzt: number, dt: number) {
    const { bw, bh } = this.masse();
    const u = this.u;
    let zielKipp = 0;
    switch (this.zustand) {
      case "flattern":
      case "fliehen":
      case "raus": {
        const dx = this.ziel.x - this.x;
        const dy = this.ziel.y - this.y;
        const d = Math.hypot(dx, dy);
        const schritt = (this.zustand === "fliehen" ? FLUCHT_PX_S : FLATTER_PX_S) * dt;
        zielKipp = Math.max(-16, Math.min(16, (dx / Math.max(d, 1)) * 16));
        if (d <= schritt) {
          this.x = this.ziel.x;
          this.y = this.ziel.y;
          if (this.zustand === "raus") {
            this.rausMelden();
            return;
          }
          if (this.dort) {
            const weiter = this.dort;
            this.dort = null;
            weiter(jetzt);
          } else this.entscheiden(jetzt);
        } else {
          this.x += (dx / d) * schritt;
          this.y += (dy / d) * schritt;
        }
        break;
      }
      case "haengen":
      case "schlafen": {
        const r = this.ortRechteck();
        if (!r || !this.ort) {
          // Kante weg (Popup zu, weggescrollt): sie lässt los und fliegt.
          this.flatternZu(this.zufallsZiel(), jetzt);
          break;
        }
        const p = this.ortLage(r, this.ort.anteil, "haengen");
        this.x = p.x;
        this.y = p.y;
        if (this.haeufchenUm && jetzt > this.haeufchenUm && this.zustand === "haengen") {
          this.haeufchenUm = 0;
          this.haeufchenGemacht = true;
          const m = this.mitte();
          const hx = m.x / u.breite;
          const hy = Math.min(0.99, (this.y + bh * 0.9) / u.hoehe);
          if (hx > 0.02 && hx < 0.98 && hy > 0) this.melden({ typ: "haeufchen", x: hx, y: hy, art: "haeufchen" });
        }
        if (jetzt > this.bis) this.entscheiden(jetzt);
        break;
      }
      case "stehen":
      case "v_stehen":
      case "v_hut": {
        const r = this.ortRechteck();
        if (!r || !this.ort) {
          if (this.form === "vampir") this.zurFledermaus(jetzt);
          else this.flatternZu(this.zufallsZiel(), jetzt);
          break;
        }
        const p = this.ortLage(r, this.ort.anteil, "stehen");
        this.x = p.x;
        this.y = p.y;
        if (jetzt > this.bis) this.entscheiden(jetzt);
        break;
      }
      case "fressen": {
        const r = this.ortRechteck();
        if (r && this.ort) {
          const p = this.ortLage(r, this.ort.anteil, "stehen");
          this.y = p.y;
        }
        // Mitte des Fressens: der Napf ist leer.
        if (!this.fressGemeldet && jetzt > this.bis - takt("fressen") * 0.35) {
          this.fressGemeldet = true;
          if (this.napfId) this.melden({ typ: "fressen", id: this.napfId });
          this.napfId = null;
        }
        if (jetzt > this.bis) this.flatternZu(this.zufallsZiel(), jetzt);
        break;
      }
      case "v_laufen": {
        const r = this.ortRechteck();
        if (!r || !this.ort) {
          this.zurFledermaus(jetzt);
          break;
        }
        const breite = Math.max(1, r.right - r.left);
        const dA = this.ziel.x - this.ort.anteil;
        const schritt = (LAUF_PX_S * this.s() * 0.5 * dt) / breite;
        if (Math.abs(dA) <= schritt) {
          this.ort.anteil = this.ziel.x;
          this.entscheiden(jetzt);
        } else this.ort.anteil += Math.sign(dA) * schritt;
        const p = this.ortLage(r, this.ort.anteil, "stehen");
        this.x = p.x;
        this.y = p.y;
        break;
      }
      case "v_freuen": {
        const r = this.ortRechteck();
        if (r && this.ort) {
          const p = this.ortLage(r, this.ort.anteil, "stehen");
          this.x = p.x;
          this.y = p.y;
        }
        if (jetzt > this.bis) this.entscheiden(jetzt);
        break;
      }
      case "verwandeln": {
        const t = jetzt - this.puffStart!;
        if (t >= WECHSEL_MS && this.form !== this.puffZiel) {
          this.form = this.puffZiel;
          this.setzeAnim(jetzt);
        }
        if (this.ort) {
          const r = this.ortRechteck();
          if (r) {
            const p = this.ortLage(r, this.ort.anteil, "stehen");
            this.x = p.x;
            this.y = p.y;
          }
        }
        if (t >= VERWANDELN_MS) {
          this.puffStart = null;
          const weiter = this.puffDanach;
          this.puffDanach = null;
          weiter?.(jetzt);
        }
        break;
      }
      case "taumeln": {
        // Zerzaust aus Bärbel gespuckt: torkelt kurz, fängt sich, fliegt weg.
        this.vx *= Math.exp(-1.5 * dt);
        this.vy = this.vy * Math.exp(-1.5 * dt) + 40 * dt;
        this.x = Math.min(u.breite - bw * 0.5, Math.max(-bw * 0.5, this.x + this.vx * dt + Math.sin(jetzt / 140) * 40 * dt));
        this.y = Math.min(u.hoehe - bh, Math.max(-bh * 0.3, this.y + this.vy * dt));
        if (jetzt > this.bis) this.flatternZu(this.zufallsZiel(), jetzt);
        break;
      }
      case "trinken": {
        const t = this.trink;
        const platz = t && this.trinkPlatz(t.id);
        if (!t || !platz) {
          // Bogen zu oder weggescrollt: sie lässt los.
          this.flatternZu(this.zufallsZiel(), jetzt);
          break;
        }
        this.x = platz.x;
        this.y = platz.y;
        const k = (jetzt - t.t0 - BISS_MS) / t.dauer;
        if (k > 0) {
          punktTrinken(t.id, 1 - k);
          if (u.zufall() < dt * 7) {
            const s = this.s();
            tropfen(t.id, this.x + (this.o.stufe.breite / 2) * s, this.y + this.o.stufe.hoehe * 0.55 * s);
          }
        }
        if (k >= 1) {
          punktNachfuellen(t.id);
          this.trink = null;
          this.getrunken += 1;
          // Die Reihe entlang weitertrinken — oder satt weiterfliegen.
          const weiter = this.getrunken < TRINK_MAX && u.zufall() < 0.6 ? nachbarPunkt(t.id) : null;
          if (weiter && this.zumPunkt(weiter, jetzt)) break;
          this.naechstesTrinken = jetzt + 25_000 + u.zufall() * 35_000;
          this.freudeStart = jetzt;
          this.flatternZu({ x: this.x + (u.zufall() - 0.5) * 220, y: Math.max(10, this.y - 120 - u.zufall() * 120) }, jetzt);
        }
        break;
      }
      case "verschluckt":
        if (jetzt - this.verschlucktSeit > NOTAUSGANG_MS) {
          const m = this.mitte();
          this.ausspucken(jetzt, m.x, m.y);
        }
        break;
      case "wurf": {
        const bremse = Math.exp(-WURF_BREMSE * dt);
        this.vx *= bremse;
        this.vy = this.vy * bremse + 200 * dt;
        this.x += this.vx * dt;
        this.y += this.vy * dt;
        if (this.y + bh > u.hoehe) {
          this.y = u.hoehe - bh;
          this.vy = -Math.abs(this.vy) * 0.4;
        }
        const raus = this.x + bw < 0 ? "links" : this.x > u.breite ? "rechts" : this.y + bh < 0 ? "oben" : null;
        if (raus) {
          this.rausSeite = raus;
          this.zustand = "raus";
          this.rausMelden();
          return;
        }
        if (Math.hypot(this.vx, this.vy) < 140) this.flatternZu(this.zufallsZiel(), jetzt);
        break;
      }
      case "gehalten":
        if (jetzt - this.griff!.start >= PACKEN_MS) {
          // Gepackt: als Vampir puff zur Fledermaus — die flattert dann panisch am Finger.
          if (this.form === "vampir") this.hutPuff = jetzt;
          this.trinkAbbrechen();
          this.form = "fledermaus";
          this.hut = false;
          this.ort = null;
          this.puffStart = null;
          this.zustand = "getragen";
          this.setzeAnim(jetzt);
          const f = this.fingerSpur[this.fingerSpur.length - 1];
          if (f) this.tragen(f.x, f.y, jetzt);
        }
        break;
      default:
        break;
    }
    this.kipp += (zielKipp - this.kipp) * Math.min(1, dt * 6);
  }

  // ── Anfassen ────────────────────────────────────────────────────────────

  druckStart(jetzt: number): boolean {
    if (["wurf", "gehalten", "getragen", "verschluckt", "verwandeln"].includes(this.zustand)) return false;
    if (this.zustand === "raus" && this.rausGemeldet) return false;
    this.griff = { start: jetzt, vorher: this.zustand, bis: this.bis };
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
    this.zustand = this.griff.vorher;
    this.bis = this.griff.bis + dauer;
    this.vampirBis += dauer;
    if (this.trink) this.trink.t0 += dauer;
    if (this.haeufchenUm) this.haeufchenUm += dauer;
    this.griff = null;
    this.fingerSpur = [];
  }

  tragen(fx: number, fy: number, jetzt: number) {
    if (this.zustand !== "getragen") return;
    const { bw, bh } = this.masse();
    this.fingerSpur.push({ x: fx, y: fy, t: jetzt });
    while (this.fingerSpur.length > 2 && jetzt - this.fingerSpur[0].t > 100) this.fingerSpur.shift();
    this.x = fx - bw / 2;
    this.y = fy - bh * 0.45;
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
    this.fingerSpur = [];
    this.griff = null;
    this.zustand = "wurf";
    this.setzeAnim(jetzt);
  }

  streicheln(jetzt: number): boolean {
    if (["raus", "gehalten", "getragen", "wurf", "verschluckt", "verwandeln", "taumeln"].includes(this.zustand)) return false;
    this.freudeStart = jetzt;
    if (this.zustand === "schlafen") {
      // Aufgeweckt: noch ein bisschen hängen bleiben.
      this.zustand = "haengen";
      this.bis = jetzt + 4000 + this.u.zufall() * 4000;
    }
    if (this.form === "vampir" && ["v_stehen", "v_laufen", "v_hut", "v_freuen"].includes(this.zustand)) {
      // Kusshand (Mark, 17.11.2026).
      this.zustand = "v_freuen";
      this.bis = jetzt + takt("v_freuen") + 300;
      this.setzeAnim(jetzt);
    }
    return true;
  }

  // ── Darstellung ─────────────────────────────────────────────────────────

  darstellung(jetzt: number): Darstellung {
    const s = this.s();
    const st = this.o.stufe;
    const sek = (jetzt - this.t0) / 1000;
    let top = this.y;
    let rot = this.kipp;
    let flip = this.flip;
    let drehpunkt = "50% 50%";
    let animation = "flattern";
    let animStart = this.animStart;
    let frame: number | null = null;
    const hutSuffix = this.hut ? "_hut" : "";
    let kopf = { x: this.x + st.kopfFlug[0] * s, y: this.y + st.kopfFlug[1] * s };

    const vampirAnim = (name: string) => {
      animation = `v_${name}${hutSuffix}`;
      kopf = st.kopfVampir ? { x: this.x + st.kopfVampir[0] * s, y: this.y + st.kopfVampir[1] * s } : kopf;
    };

    switch (this.zustand) {
      case "haengen":
      case "schlafen": {
        const fr = (jetzt - this.freudeStart) / takt("freuen");
        animation = this.zustand === "schlafen" ? "schlafen" : fr >= 0 && fr < 1 ? "freuen" : "haengen";
        if (animation === "freuen") animStart = this.freudeStart;
        // Sanftes Pendeln um die Krallen.
        drehpunkt = `50% ${st.griff * s}px`;
        rot = Math.sin(sek * 2 * Math.PI * (this.zustand === "schlafen" ? 0.18 : 0.3)) * (this.zustand === "schlafen" ? 2 : 4);
        if (animation === "freuen") rot += Math.sin(fr * 4 * Math.PI) * 10;
        flip = false;
        kopf = { x: this.x + st.kopfHaengen[0] * s, y: this.y + st.kopfHaengen[1] * s };
        break;
      }
      case "stehen":
      case "fressen":
        animation = this.zustand;
        rot = 0;
        flip = false;
        kopf = { x: this.x + st.kopfStehen[0] * s, y: this.y + st.kopfStehen[1] * s };
        break;
      case "v_stehen":
        vampirAnim("idle");
        rot = 0;
        break;
      case "v_laufen":
        vampirAnim("lauf");
        rot = 0;
        break;
      case "v_freuen":
        vampirAnim("freuen");
        rot = 0;
        flip = false;
        break;
      case "v_hut":
        animation = "v_hut";
        if (st.kopfVampir) kopf = { x: this.x + st.kopfVampir[0] * s, y: this.y + st.kopfVampir[1] * s };
        rot = 0;
        flip = false;
        break;
      case "verwandeln": {
        // Bis zur Wolkenmitte die alte Gestalt, dann die neue — die Wolke deckt den Wechsel.
        if (this.form === "vampir") vampirAnim("idle");
        else {
          animation = this.ort ? "stehen" : "flattern";
          kopf = { x: this.x + st.kopfStehen[0] * s, y: this.y + st.kopfStehen[1] * s };
        }
        rot = 0;
        flip = this.form === "vampir" ? this.flip : false;
        break;
      }
      case "taumeln":
        animation = "taumeln";
        rot = Math.sin(jetzt / 90) * 25;
        break;
      case "trinken": {
        // Flatternd unter der Kugel: erst ein Ruck nach oben (Biss), dann saugen.
        animation = "flattern";
        // Kopf schräg zur Kugel geneigt, um das Maul gedreht.
        rot = -this.trinkSeite * 24;
        drehpunkt = `50% ${st.hoehe * 0.52 * s}px`;
        flip = false;
        const t = this.trink ? jetzt - this.trink.t0 : 1e9;
        if (t < BISS_MS) top -= Math.sin((t / BISS_MS) * Math.PI) * 3 * s;
        else top += Math.sin(jetzt / 110) * 1.2 * s;
        break;
      }
      case "verschluckt":
        animation = "flattern";
        frame = 0;
        break;
      case "gehalten":
        // Finger drauf, noch nicht gepackt: Gestalt bleibt, wie sie war.
        if (this.form === "vampir") vampirAnim("idle");
        else if (this.griff && (this.griff.vorher === "haengen" || this.griff.vorher === "schlafen")) {
          animation = "haengen";
          drehpunkt = `50% ${st.griff * s}px`;
          rot = Math.sin(jetzt / 30) * 3;
          kopf = { x: this.x + st.kopfHaengen[0] * s, y: this.y + st.kopfHaengen[1] * s };
        } else if (this.griff && (this.griff.vorher === "stehen" || this.griff.vorher === "fressen")) animation = "stehen";
        break;
      case "getragen":
        animation = "flattern";
        animStart = this.animStart - 1000; // panisch: schneller Takt über frame unten
        frame = Math.floor((jetzt - this.animStart) / 40) % FLEDERMAUS_TAKT.flattern.frames;
        rot = Math.sin(jetzt / 45) * 8;
        break;
      default: {
        // Fliegen: Wellenflug im Flügeltakt, kleine Freudenrolle beim Streicheln.
        animation = "flattern";
        top += Math.sin(sek * 2 * Math.PI * 1.6) * 4;
        const fr = (jetzt - this.freudeStart) / 700;
        if (fr >= 0 && fr < 1) rot += fr * 360;
        break;
      }
    }
    // Vampir: Kopf für Herzen; als Fledermaus im Flug ohne Spiegelung.
    if (this.form !== "vampir" && !["v_stehen", "v_laufen"].includes(this.zustand)) flip = false;
    const sichtbar = this.zustand !== "verschluckt";
    return {
      left: this.x,
      top,
      transform: `rotate(${rot.toFixed(1)}deg)${flip ? " scaleX(-1)" : ""}`,
      drehpunkt,
      animation,
      animStart,
      frame,
      feuer: null,
      puff: this.zustand === "verwandeln" ? this.puffStart : null,
      puffKlein:
        this.hutPuff !== null && jetzt - this.hutPuff < HUTPUFF_MS
          ? { start: this.hutPuff, x: kopf.x, y: kopf.y }
          : null,
      unsichtbar: !sichtbar,
      hockt: false,
      gepackt: this.zustand === "getragen" || this.zustand === "gehalten",
      schlaeft: this.zustand === "schlafen",
      schwitzt: false,
      kopfX: kopf.x,
      kopfY: kopf.y,
    };
  }
}
