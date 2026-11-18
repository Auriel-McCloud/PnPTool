import { useEffect, useRef } from "react";
import { KI_FOLGE, type PetAufSchirm } from "./api";
import { KI_FARBEN, KI_G, KI_GESTALTEN, KI_GESTALT_NAMEN, KiWesen, type KiFarbe } from "./ki";
import {
  imStrahl, LASER_ARTEN, LaserSchuss, PUTZ_AB, schmutzAufSchirm, verbrannt, Verdampfen, WUT_AB, zeichneAchtung, zeichneWut,
  type SchussArt, type Schmutz,
} from "./laser";
import { anzahlImBauch } from "./punkte";
import { alle, kitzelbar, makel, melde, treffe, vergiss } from "./treffen";

/**
 * Die KI eines Spielers als Pet (Mark, 13.11.2026) — schwebt über den Schirm,
 * pulsiert, wechselt zwischen Datenwolke und Lichtkern, nimmt Farben und
 * Gestalten an und zieht irgendwann zum nächsten Tablet weiter.
 *
 * Was sie kann, wächst mit ihr (Stufe aus dem Pet-Dict, 13 Schritte):
 *   Funke   schwebt und pulsiert
 *   Keim    wechselt Wolke ↔ Lichtkern, blinzelt, wird beim Antippen ein Herz, schläft
 *   Geist   nimmt Farben und Gestalten an
 *   Wesen   liest Daten: schwebt über eine Zeile und fährt mit einem Lichtstrich darüber
 *   Entität Umlaufbahn und drei Ringe, Gestalten öfter
 *
 * Antippen = sie freut sich. Ziehen = sie kommt mit; mit Schwung über den
 * Seitenrand geworfen, fliegt sie zum nächsten Tablet. Gezeichnet wird auf
 * eine Leinwand direkt am DOM, kein Render pro Frame.
 *
 * Reinigungslaser (Mark, 18.11.2026), ab Geist: liegen 3 Spuren auf dem
 * Schirm, schaltet sie in den Putzmodus (rotes „!“), fliegt hin und brennt
 * alles weg, was ihre Stufe kann — Strahl auf einen Punkt, der immer
 * schneller pendelt, bis er ein Fächer ist. Pets im Fächer verrußen. Ab 10
 * Spuren ist sie wütend (drei „!“, Zornader, rot): erst sauber machen, dann
 * den Schuldigen jagen, auch über die Tablets hinweg, bis sie einen erwischt.
 * Die Entität kitzelt außerdem den Tummy-Acher, bis er die Punkte ausrülpst.
 */

type Zustand = "gleiten" | "schweben" | "gestalt" | "lesen" | "schlafen" | "raus" | "gezogen" | "wurf" | "weg" | "saugen" | "laser";

/** KI-Futter (Mark, 15.11.2026): so lange saugt sie ein Datenpaket ein. */
const SAUGEN_MS = 1500;

/** Wie lange sie bleibt, bevor sie weiterzieht (Annahme Neko, wie Bärbel). */
const BESUCH_MS: [number, number] = [60_000, 150_000];
const TEMPO_PX_S = 95;

function zw(a: number, b: number) {
  return a + Math.random() * (b - a);
}

function kiPixel() {
  return window.innerWidth < 700 ? 2 : 3;
}

/** Eine sichtbare Zeile oder ein Kästchen, das sie „lesen“ kann — im obersten Popup, sonst auf der Seite. */
function leseZiel(): Element | null {
  const fenster = Array.from(document.querySelectorAll(".fn-fenster"));
  const wurzel: Element = fenster.length ? fenster[fenster.length - 1] : document.body;
  const kandidaten = Array.from(wurzel.querySelectorAll("h1, h2, h3, h4, label, button, p, td, th, li, input, .cl-roehre"))
    .slice(0, 400)
    .filter((el) => {
      if (el.closest(".pet-ebene")) return false;
      const r = el.getBoundingClientRect();
      return (
        r.width >= 50 && r.width <= 520 && r.height >= 12 && r.height <= 70 &&
        r.top > 90 && r.bottom < window.innerHeight - 20 && r.left >= 0 && r.right <= window.innerWidth
      );
    });
  return kandidaten.length ? kandidaten[Math.floor(Math.random() * kandidaten.length)] : null;
}

export function KiFigur({
  pet,
  senden,
  wegmachen,
  onTreffer,
}: {
  pet: PetAufSchirm;
  senden: (n: object) => void;
  /** Datenpaket eingesaugt: Spur weg, `petId` = sie hat es gefressen (heilt, wächst). */
  wegmachen: (id: string, petId?: string) => void;
  /** Laser hat Pets gestreift — sie verrußen wie nach Bärbels Blitz. */
  onTreffer: (t: ReturnType<typeof treffe>) => void;
}) {
  const wegmachenRef = useRef(wegmachen);
  wegmachenRef.current = wegmachen;
  const trefferRef = useRef(onTreffer);
  trefferRef.current = onTreffer;
  // Kommt vom Server und kann sich während des Besuchs ändern.
  const jagdDaRef = useRef(false);
  jagdDaRef.current = !!pet.jagdDa;
  const laserLw = useRef<HTMLCanvasElement | null>(null);
  const leinwand = useRef<HTMLCanvasElement | null>(null);
  const griff = useRef<HTMLDivElement | null>(null);
  const scan = useRef<HTMLDivElement | null>(null);
  const wesenRef = useRef<KiWesen | null>(null);
  const sendenRef = useRef(senden);
  sendenRef.current = senden;
  const schritt = Math.max(0, (KI_FOLGE as readonly string[]).indexOf(pet.stufe ?? "funke"));

  // Gewachsen: dieselbe Figur wird größer, kein neuer Auftritt.
  useEffect(() => {
    wesenRef.current?.setzeSchritt(schritt, performance.now());
  }, [schritt]);

  useEffect(() => {
    const cv = leinwand.current;
    const gr = griff.current;
    const sc = scan.current;
    const ctx = cv?.getContext("2d");
    const lw = laserLw.current;
    const lctx = lw?.getContext("2d");
    if (!cv || !gr || !sc || !ctx || !lw || !lctx) return;
    const p = kiPixel();
    const jetzt0 = performance.now();
    const wesen = new KiWesen(schritt, jetzt0);
    wesenRef.current = wesen;
    const stufe = () => wesen.masse.stufe;

    const breite = () => window.innerWidth;
    const hoehe = () => window.innerHeight;
    const rand = () => wesen.radius() * p + 8;
    let x = pet.seite === "links" ? -KI_G * p * 0.5 : breite() + KI_G * p * 0.5;
    let y = hoehe() * zw(0.25, 0.65);
    let vx = 0;
    let vy = 0;
    let zustand: Zustand = "gleiten";
    let ziel = { x: breite() * (pet.seite === "links" ? zw(0.2, 0.45) : zw(0.55, 0.8)), y: hoehe() * zw(0.25, 0.6) };
    let bis = 0;
    let besuchEnde = jetzt0 + zw(BESUCH_MS[0], BESUCH_MS[1]);
    let geschlafen = false;
    let lesen: Element | null = null;
    let danach: (() => void) | null = null;
    let rausGemeldet = false;
    let letzterMakel = 0;
    let finger: { x: number; y: number; t: number }[] = [];
    let druck: { id: number; x: number; y: number; bewegt: boolean; vorher: Zustand } | null = null;
    // Datenpaket, das sie gerade einsaugt (Element, Spur-id, Start und Lage).
    let saugen: { el: HTMLElement; id: string; t0: number; x0: number; y0: number } | null = null;
    const saugenAbbrechen = () => {
      if (!saugen) return;
      saugen.el.style.transform = "";
      saugen.el.style.opacity = "";
      saugen.el.dataset.saugt = "";
      saugen = null;
    };

    const klemme = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
    const irgendwo = () => ({
      x: zw(rand(), Math.max(rand() + 1, breite() - rand())),
      y: zw(Math.max(70, rand()), Math.max(rand() + 71, hoehe() - rand())),
    });
    const gleite = (z: { x: number; y: number }, dann: (() => void) | null = null) => {
      ziel = z;
      danach = dann;
      zustand = "gleiten";
    };
    const schwebe = (jetzt: number, ms: number) => {
      zustand = "schweben";
      bis = jetzt + ms;
    };
    const raus = (seite: "links" | "rechts") => {
      if (rausGemeldet) return;
      rausGemeldet = true;
      zustand = "weg";
      sendenRef.current({ typ: "raus", petId: pet.id, seite });
    };
    const andereFarbe = (): KiFarbe => {
      const rest = KI_FARBEN.filter((f) => f !== wesen.farbe);
      return rest[Math.floor(Math.random() * rest.length)];
    };
    const rausFliegen = () => {
      // Zum näheren Seitenrand hinaus.
      const nachRechts = x > breite() / 2;
      zustand = "raus";
      ziel = { x: nachRechts ? breite() + KI_G * p : -KI_G * p, y: klemme(y + zw(-80, 80), 60, hoehe() - 60) };
    };

    // ── Reinigungslaser (Mark, 18.11.2026) ──────────────────────────────
    let putz = false;
    let putzSchuesse = 0;
    let jagdZiele: string[] = [...(pet.jagd ?? [])];
    let wut = jagdZiele.length > 0;
    let farbeVorher: KiFarbe | null = null;
    // Wer wie viele Spuren auf diesem Schirm hinterlassen hat (Schuldige).
    const schuldig = new Map<string, number>();
    const gezaehlt = new Set<string>();
    let schuss: LaserSchuss | null = null;
    let schussZiel: () => { x: number; y: number } | null = () => null;
    let schussFertig: (() => void) | null = null;
    let gestreift = new Set<string>();
    let erwischt = false;
    let verfolgt: { id: string; art: SchussArt } | null = null;
    let jagdLos = jetzt0 + zw(3000, 6000);
    let naechsterBlick = jetzt0 + 1500;
    let naechstesKitzeln = jetzt0 + zw(5000, 15000);
    let leinwandBenutzt = false;
    const dampf = new Verdampfen();

    const kannBrennen = (art: string) => LASER_ARTEN[stufe()]?.includes(art) ?? false;
    const zaehle = (liste: Schmutz[]) => {
      for (const s of liste) {
        if (gezaehlt.has(s.id)) continue;
        gezaehlt.add(s.id);
        if (s.petId && s.petId !== pet.id) schuldig.set(s.petId, (schuldig.get(s.petId) ?? 0) + 1);
      }
    };
    const wuetend = (jetzt: number) => {
      wut = true;
      if (wesen.farbe !== "rot") {
        farbeVorher = farbeVorher ?? wesen.farbe;
        wesen.setzeFarbe("rot", jetzt);
      }
    };
    const beruhigen = (jetzt: number) => {
      wut = false;
      jagdZiele = [];
      if (farbeVorher) wesen.setzeFarbe(farbeVorher, jetzt);
      farbeVorher = null;
      wesen.freude(jetzt);
    };
    if (wut) {
      farbeVorher = "cyan";
      wesen.setzeFarbe("rot", jetzt0);
    }
    const stillhalten = () => {
      wesen.schlaf = false;
      wesen.liest = false;
      lesen = null;
      if (wesen.gestalt) wesen.setzeGestalt(null);
    };
    const schiessen = (art: SchussArt, jetzt: number, zielVon: () => { x: number; y: number } | null, dann: () => void) => {
      const z = zielVon();
      if (!z) return dann();
      stillhalten();
      schuss = new LaserSchuss(art, jetzt, stufe(), { x, y }, z);
      schussZiel = zielVon;
      schussFertig = dann;
      gestreift = new Set();
      zustand = "laser";
    };
    const putzEnde = (jetzt: number) => {
      putz = false;
      if (wut) {
        const ziele = [...schuldig.entries()].sort((a, b) => b[1] - a[1]).map(([id]) => id);
        if (ziele.length) {
          // Erst sauber machen, dann jagen (Mark): wer am meisten Dreck gemacht hat, zuerst.
          jagdZiele = ziele;
          sendenRef.current({ typ: "jagd", petId: pet.id, ziele });
          jagdLos = jetzt + zw(2500, 4000);
          schwebe(jetzt, 700);
          return;
        }
        beruhigen(jetzt);
      } else wesen.freude(jetzt);
      schwebe(jetzt, zw(1200, 2200));
    };
    const naechsterSchuss = (jetzt: number) => {
      const liste = schmutzAufSchirm();
      zaehle(liste);
      if (liste.length >= WUT_AB) wuetend(jetzt);
      const brennbar = liste.filter((s) => kannBrennen(s.art));
      if (!brennbar.length || putzSchuesse >= 40) return putzEnde(jetzt);
      putzSchuesse += 1;
      brennbar.sort((a, b) => Math.hypot(a.x - x, a.y - y) - Math.hypot(b.x - x, b.y - y));
      const z = brennbar[0];
      const abstand = 80 + wesen.radius() * p;
      let py = z.y - abstand;
      if (py < Math.max(70, rand())) py = Math.min(hoehe() - rand(), z.y + abstand);
      const px = klemme(z.x + zw(-0.35, 0.35) * abstand, rand(), breite() - rand());
      let letzt = { x: z.x, y: z.y };
      const punkt = () => {
        const el = document.querySelector<HTMLElement>(`[data-schmutz][data-id="${CSS.escape(z.id)}"]`);
        if (el && !el.classList.contains("pet-haeufchen-weg")) {
          const r = el.getBoundingClientRect();
          letzt = { x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2 };
        }
        return letzt;
      };
      gleite({ x: px, y: py }, () => schiessen("putzen", performance.now(), punkt, () => naechsterSchuss(performance.now())));
    };
    /** Genug Dreck da? Dann Putzmodus. */
    const putzPruefen = (jetzt: number) => {
      if (stufe() < 2 || putz) return false;
      const liste = schmutzAufSchirm();
      if (liste.length < PUTZ_AB || !liste.some((s) => kannBrennen(s.art))) return false;
      putz = true;
      putzSchuesse = 0;
      schuldig.clear();
      gezaehlt.clear();
      stillhalten();
      naechsterSchuss(jetzt);
      return true;
    };
    const koerper = (id: string) => alle().find((k) => k.id === id) ?? null;
    const jagen = (id: string, art: SchussArt) => {
      stillhalten();
      verfolgt = { id, art };
      danach = null;
      zustand = "gleiten";
    };
    const findeSchuldigen = () => {
      for (const id of jagdZiele) if (koerper(id)) return id;
      return null;
    };
    /** Wütend ohne Dreck: Schuldigen hier jagen, sonst suchen, sonst los zum Tablet, wo er ist. */
    const jagdSchritt = (jetzt: number) => {
      const id = findeSchuldigen();
      if (id) {
        jagen(id, "jagd");
        return true;
      }
      if (!jagdDaRef.current) return false;
      if (jetzt >= jagdLos) rausFliegen();
      else gleite(irgendwo());
      return true;
    };
    const verfolgungSchuss = (jetzt: number) => {
      const v = verfolgt;
      if (!v) return;
      verfolgt = null;
      erwischt = false;
      const zielVon = () => {
        const k = koerper(v.id);
        return k ? { x: k.x, y: k.y } : null;
      };
      schiessen(v.art, jetzt, zielVon, () => {
        const j = performance.now();
        if (v.art === "kitzeln") {
          // Er rülpst, die gefressenen Punkte fliegen zurück an ihren Platz.
          kitzelbar.get(v.id)?.();
          wesen.freude(j);
          schwebe(j, 1200);
          return;
        }
        if (erwischt) {
          // Erwischt: Wut weg, sie ist zufrieden.
          sendenRef.current({ typ: "jagd", petId: pet.id, ziele: [] });
          beruhigen(j);
          if (stufe() >= 2) {
            wesen.setzeGestalt("smiley");
            zustand = "gestalt";
            bis = j + 2200;
          } else schwebe(j, 1500);
          return;
        }
        schwebe(j, 400);
      });
    };

    const entscheide = (jetzt: number) => {
      wesen.liest = false;
      lesen = null;
      if (wesen.gestalt) wesen.setzeGestalt(null);
      if (putz) return naechsterSchuss(jetzt);
      if (jetzt >= besuchEnde) return rausFliegen();
      // Futter geht vor (15.11.2026): liegt ein Datenpaket da, holt sie es sich.
      const paket = Array.from(document.querySelectorAll<HTMLElement>(".pet-datenpaket")).find(
        (el) => !el.classList.contains("pet-haeufchen-weg") && el.dataset.saugt !== "ja",
      );
      if (paket?.dataset.id) {
        const r = paket.getBoundingClientRect();
        const id = paket.dataset.id;
        gleite({ x: r.left + r.width / 2, y: Math.max(rand(), r.top + r.height / 2 - wesen.radius() * p * 0.5) }, () => {
          if (!paket.isConnected) return schwebe(performance.now(), 600);
          const rr = paket.getBoundingClientRect();
          paket.dataset.saugt = "ja";
          saugen = { el: paket, id, t0: performance.now(), x0: rr.left + rr.width / 2, y0: rr.top + rr.height / 2 };
          wesen.liest = true;
          zustand = "saugen";
          bis = performance.now() + SAUGEN_MS;
        });
        return;
      }
      if (putzPruefen(jetzt)) return;
      if (jagdZiele.length && jagdSchritt(jetzt)) return;
      const st = stufe();
      // Entität: hat ein Tummy-Acher Punkte im Bauch, kitzelt sie ihn mit dem Strahl.
      if (st >= 4 && !wut && jetzt >= naechstesKitzeln) {
        const tummy = alle().find((k) => kitzelbar.has(k.id) && anzahlImBauch(k.id) > 0);
        if (tummy) {
          naechstesKitzeln = jetzt + zw(8000, 14000);
          return jagen(tummy.id, "kitzeln");
        }
      }
      const wahl: [number, () => void][] = [[5, () => gleite(irgendwo())]];
      if (st >= 1 && !wut) {
        wahl.push([2, () => {
          wesen.setzeForm(wesen.form === "wolke" ? "kern" : "wolke");
          schwebe(jetzt, zw(2500, 5000));
        }]);
        if (!geschlafen) {
          wahl.push([0.6, () => {
            geschlafen = true;
            wesen.schlaf = true;
            zustand = "schlafen";
            bis = jetzt + zw(15_000, 40_000);
            besuchEnde = Math.max(besuchEnde, bis + 15_000);
          }]);
        }
      }
      if (st >= 2 && !wut) {
        wahl.push([st >= 4 ? 3 : 2, () => {
          const name = KI_GESTALT_NAMEN[Math.floor(Math.random() * KI_GESTALT_NAMEN.length)];
          wesen.setzeGestalt(name);
          wesen.setzeFarbe(KI_GESTALTEN[name].farbe, jetzt);
          zustand = "gestalt";
          bis = jetzt + zw(4000, 7000);
        }]);
        wahl.push([1, () => {
          wesen.setzeFarbe(andereFarbe(), jetzt);
          schwebe(jetzt, zw(1500, 3000));
        }]);
      }
      if (st >= 3) {
        wahl.push([2, () => {
          const el = leseZiel();
          if (!el) return gleite(irgendwo());
          const r = el.getBoundingClientRect();
          gleite({ x: klemme((r.left + r.right) / 2, rand(), breite() - rand()), y: Math.max(rand(), r.top - wesen.radius() * p - 6) }, () => {
            if (!el.isConnected) return schwebe(performance.now(), 600);
            lesen = el;
            wesen.liest = true;
            zustand = "lesen";
            bis = performance.now() + zw(2600, 4200);
          });
        }]);
      }
      let w = Math.random() * wahl.reduce((s, [g]) => s + g, 0);
      for (const [g, tun] of wahl) {
        w -= g;
        if (w <= 0) return tun();
      }
      wahl[0][1]();
    };

    let letzte = jetzt0;
    let rahmen = 0;
    let scheinAb = 0;
    const takt = (jetzt: number) => {
      const dt = Math.min(0.05, (jetzt - letzte) / 1000);
      letzte = jetzt;
      if (zustand !== "weg") {
        if (zustand === "gleiten" && verfolgt) {
          // Hinter dem Schuldigen (oder dem Tummy-Acher) her; nah genug = Strahl.
          const k = koerper(verfolgt.id);
          if (!k) {
            verfolgt = null;
            schwebe(jetzt, 800);
          } else {
            const hoch = k.y - 100 >= Math.max(70, rand());
            ziel = { x: klemme(k.x + (x < k.x ? -40 : 40), rand(), breite() - rand()), y: hoch ? k.y - 100 : Math.min(hoehe() - rand(), k.y + 100) };
            if (Math.hypot(k.x - x, k.y - y) < 175) verfolgungSchuss(jetzt);
          }
        }
        if (zustand === "gleiten" || zustand === "raus") {
          const dx = ziel.x - x;
          const dy = ziel.y - y;
          const weit = Math.hypot(dx, dy);
          const eilig = putz || wut || verfolgt ? 1.8 : 1;
          const tempo = TEMPO_PX_S * (zustand === "raus" ? 1.5 : eilig * Math.min(1, 0.25 + weit / 120));
          const k = Math.min(1, dt * 3);
          vx += ((dx / (weit || 1)) * tempo - vx) * k;
          vy += ((dy / (weit || 1)) * tempo - vy) * k;
          if (zustand === "raus" && (x < -KI_G * p * 0.5 || x > breite() + KI_G * p * 0.5)) raus(x < 0 ? "links" : "rechts");
          else if (zustand === "gleiten" && weit < 10 && !verfolgt) {
            const tun = danach;
            danach = null;
            if (tun) tun();
            else schwebe(jetzt, zw(1500, 5000));
          }
        } else if (zustand === "wurf") {
          const brems = Math.max(0, 1 - 1.6 * dt);
          vx *= brems;
          vy *= brems;
          // Oben und unten prallt sie ab; seitlich fliegt sie zum nächsten Tablet.
          if ((y < rand() && vy < 0) || (y > hoehe() - rand() && vy > 0)) vy = -vy * 0.6;
          if (x < -KI_G * p * 0.4 || x > breite() + KI_G * p * 0.4) raus(x < 0 ? "links" : "rechts");
          else if (Math.hypot(vx, vy) < 45) {
            if ((x < rand() && vx <= 0) || (x > breite() - rand() && vx >= 0)) gleite(irgendwo());
            else schwebe(jetzt, zw(800, 2000));
          }
        } else if (zustand === "saugen") {
          vx *= Math.max(0, 1 - 6 * dt);
          vy *= Math.max(0, 1 - 6 * dt);
          const sg = saugen;
          if (!sg || !sg.el.isConnected) {
            saugen = null;
            wesen.liest = false;
            schwebe(jetzt, 600);
          } else {
            // Das Paket wird in sie hineingezogen und schrumpft dabei.
            const k = Math.min(1, (jetzt - sg.t0) / SAUGEN_MS);
            const e = k * k;
            sg.el.style.transform = `translate(${(x - sg.x0) * e}px, ${(y - sg.y0) * e}px) scale(${1 - 0.9 * e})`;
            sg.el.style.opacity = String(1 - 0.7 * e);
            if (k >= 1) {
              saugen = null;
              wesen.liest = false;
              wegmachenRef.current(sg.id, pet.id);
              wesen.freude(jetzt);
              schwebe(jetzt, 1400);
            }
          }
        } else if (zustand === "laser") {
          vx *= Math.max(0, 1 - 6 * dt);
          vy *= Math.max(0, 1 - 6 * dt);
          const s = schuss;
          if (!s) schwebe(jetzt, 400);
          else {
            const von = { x, y };
            s.tick(jetzt, dt, von, schussZiel());
            const b = s.ueberstrichen(jetzt);
            if (b) {
              // Alles im Strahl verdampft — soweit ihre Stufe die Spur-Art schon kann.
              for (const sp of schmutzAufSchirm()) {
                if (!kannBrennen(sp.art) || !imStrahl(b, von, sp)) continue;
                verbrannt.add(sp.id);
                zaehle([sp]);
                wegmachenRef.current(sp.id);
                dampf.puff(sp.x, sp.y, jetzt);
              }
              // Pets im Fächer verrußen (Mark: „das mit dem Verrußen passt“).
              if (s.art !== "kitzeln") {
                for (const k of alle()) {
                  if (k.id === pet.id || gestreift.has(k.id) || !imStrahl(b, von, k, Math.max(k.w, k.h) * 0.4)) continue;
                  gestreift.add(k.id);
                  if (jagdZiele.includes(k.id)) erwischt = true;
                  trefferRef.current(treffe({ art: "blitz", x: k.x, y: k.y, r: 4 }, pet.id, jetzt));
                }
              }
              if (Math.random() < dt * 40) {
                const sp = s.spitze(von);
                dampf.spruehen(sp.x, sp.y, jetzt);
              }
            }
            if (s.fertig) {
              const dann = schussFertig;
              schuss = null;
              schussFertig = null;
              schwebe(jetzt, 300);
              dann?.();
            }
          }
        } else if (zustand === "gezogen") {
          const f = finger[finger.length - 1];
          if (f) {
            // Sie folgt dem Finger wie an einem Gummiband.
            vx = (f.x - x) * 9;
            vy = (f.y - y) * 9;
          }
        } else {
          vx *= Math.max(0, 1 - 4 * dt);
          vy *= Math.max(0, 1 - 4 * dt);
          if (zustand === "lesen" && lesen && !lesen.isConnected) bis = 0;
          if (jetzt >= bis) {
            if (zustand === "schlafen") {
              wesen.schlaf = false;
              wesen.freude(jetzt);
              schwebe(jetzt, 1200);
            } else entscheide(jetzt);
          }
        }
        x += vx * dt;
        y += vy * dt;
      }
      wesen.blickX = Math.abs(vx) > 25 ? Math.sign(vx) : 0;

      // Von einem Drachen angeniest oder von Bärbels Blitz getroffen: Bildstörung.
      if (makel(pet.id, jetzt) && jetzt - letzterMakel > 2500) {
        letzterMakel = jetzt;
        if (zustand === "schlafen") {
          wesen.schlaf = false;
          schwebe(jetzt, 1500);
        }
        wesen.stoerung(jetzt);
      }

      // Ab und zu umschauen: genug Dreck da, oder ist der Schuldige aufgetaucht?
      if (jetzt >= naechsterBlick) {
        naechsterBlick = jetzt + 1200;
        const frei = zustand === "schweben" || zustand === "gestalt" || zustand === "lesen" || zustand === "schlafen" ||
          (zustand === "gleiten" && !danach && !verfolgt);
        if (frei && !putz && !putzPruefen(jetzt) && jagdZiele.length) {
          const id = findeSchuldigen();
          if (id) jagen(id, "jagd");
          // Er ist auf einem anderen Tablet: nach kurzem Umschauen hinterher.
          else if (jagdDaRef.current && jetzt >= jagdLos) rausFliegen();
        }
      }

      wesen.tick(jetzt, dt);
      wesen.zeichne(ctx, jetzt);
      const wippen = zustand === "schlafen" ? Math.sin(jetzt / 900) * 2 : Math.sin(jetzt / 420) * 4;
      const g = KI_G * p;
      cv.style.transform = `translate(${Math.round(x - g / 2)}px, ${Math.round(y - g / 2 + wippen)}px)`;
      const r = Math.max(22, wesen.radius() * p);
      gr.style.width = gr.style.height = `${r * 2}px`;
      gr.style.transform = `translate(${Math.round(x - r)}px, ${Math.round(y - r + wippen)}px)`;
      gr.style.display = zustand === "weg" ? "none" : "";
      cv.style.display = zustand === "weg" ? "none" : "";
      if (jetzt >= scheinAb) {
        scheinAb = jetzt + 120;
        const farbe = wesen.schein(jetzt);
        cv.style.setProperty("--ki-schein", farbe);
        sc.style.setProperty("--ki-schein", farbe);
      }
      if (zustand === "lesen" && lesen) {
        const lr = lesen.getBoundingClientRect();
        sc.style.display = "block";
        sc.style.left = `${lr.left - 2}px`;
        sc.style.top = `${lr.top - 1}px`;
        sc.style.width = `${lr.width + 4}px`;
        sc.style.height = `${lr.height + 2}px`;
      } else sc.style.display = "none";
      if (zustand !== "weg") melde({ id: pet.id, art: pet.art, x, y, w: r * 2, h: r * 2 });

      // Laser, Funken, Rauch, „!“ und Zornader auf der großen Leinwand.
      const braucht = !!schuss || !dampf.leer || putz || wut;
      if (braucht || leinwandBenutzt) {
        if (lw.width !== breite() || lw.height !== hoehe()) {
          lw.width = breite();
          lw.height = hoehe();
        }
        lctx.clearRect(0, 0, lw.width, lw.height);
        const f = wesen.laserFarben(jetzt);
        const mitte = { x, y: y + wippen };
        if (schuss && zustand !== "weg") schuss.zeichne(lctx, jetzt, mitte, f);
        dampf.zeichne(lctx, jetzt, dt, f);
        if (zustand !== "weg" && zustand !== "gezogen") {
          const kopf = mitte.y - wesen.radius() * p - 4;
          // Zeichen wachsen mit ihr mit (beim kleinen Geist wäre die Ader sonst größer als sie).
          const zp = p * (0.65 + 0.09 * stufe());
          if (wut) zeichneWut(lctx, mitte.x, kopf, mitte.x + wesen.radius() * p * 0.85 + 6, jetzt, zp);
          else if (putz) zeichneAchtung(lctx, mitte.x, kopf, jetzt, zp);
        }
        leinwandBenutzt = braucht;
      }
      rahmen = requestAnimationFrame(takt);
    };
    rahmen = requestAnimationFrame(takt);

    const runter = (e: PointerEvent) => {
      if (zustand === "weg" || zustand === "raus") return;
      e.preventDefault();
      e.stopPropagation();
      gr.setPointerCapture(e.pointerId);
      druck = { id: e.pointerId, x: e.clientX, y: e.clientY, bewegt: false, vorher: zustand };
      finger = [{ x: e.clientX, y: e.clientY, t: performance.now() }];
    };
    const bewegen = (e: PointerEvent) => {
      if (!druck || druck.id !== e.pointerId) return;
      const t = performance.now();
      finger.push({ x: e.clientX, y: e.clientY, t });
      while (finger.length > 2 && t - finger[0].t > 120) finger.shift();
      if (!druck.bewegt && Math.hypot(e.clientX - druck.x, e.clientY - druck.y) > 10) {
        druck.bewegt = true;
        saugenAbbrechen();
        schuss = null;
        schussFertig = null;
        verfolgt = null;
        // Mitgenommen: was sie gerade tat, ist vorbei.
        wesen.schlaf = false;
        wesen.liest = false;
        lesen = null;
        danach = null;
        if (wesen.gestalt) wesen.setzeGestalt(null);
        zustand = "gezogen";
      }
    };
    const los = (e: PointerEvent) => {
      if (!druck || druck.id !== e.pointerId) return;
      const d = druck;
      druck = null;
      const jetzt = performance.now();
      if (d.bewegt) {
        const a = finger[0];
        const b = finger[finger.length - 1];
        const dauer = Math.max(0.016, (b.t - a.t) / 1000);
        vx = klemme((b.x - a.x) / dauer, -1800, 1800);
        vy = klemme((b.y - a.y) / dauer, -1800, 1800);
        zustand = "wurf";
        return;
      }
      saugenAbbrechen();
      schuss = null;
      schussFertig = null;
      verfolgt = null;
      // Angetippt: sie freut sich — ab dem Keim wird sie kurz ein Herz.
      // Wütend bleibt sie rot (das Herz nimmt ihr die Wut nicht).
      sendenRef.current({ typ: "streicheln", petId: pet.id });
      wesen.schlaf = false;
      wesen.liest = false;
      lesen = null;
      danach = null;
      wesen.freude(jetzt);
      if (stufe() >= 1) {
        wesen.setzeGestalt("herz");
        if (stufe() >= 2 && !wut) wesen.setzeFarbe("magenta", jetzt);
        zustand = "gestalt";
        bis = jetzt + 1900;
      } else schwebe(jetzt, 900);
    };
    const stopp = (e: TouchEvent) => {
      if (e.cancelable) e.preventDefault();
    };
    gr.addEventListener("pointerdown", runter);
    gr.addEventListener("pointermove", bewegen);
    gr.addEventListener("pointerup", los);
    gr.addEventListener("pointercancel", los);
    gr.addEventListener("touchstart", stopp, { passive: false });
    gr.addEventListener("touchmove", stopp, { passive: false });
    return () => {
      cancelAnimationFrame(rahmen);
      saugenAbbrechen();
      vergiss(pet.id);
      wesenRef.current = null;
      gr.removeEventListener("pointerdown", runter);
      gr.removeEventListener("pointermove", bewegen);
      gr.removeEventListener("pointerup", los);
      gr.removeEventListener("pointercancel", los);
      gr.removeEventListener("touchstart", stopp);
      gr.removeEventListener("touchmove", stopp);
    };
    // Ein neuer Auftritt ist ein neuer key — die Abhängigkeiten bleiben fest.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const g = KI_G * kiPixel();
  return (
    <>
      <canvas ref={laserLw} className="pet-ki-laser" />
      <div ref={scan} className="pet-ki-scan" style={{ display: "none" }} />
      <canvas ref={leinwand} className="pet-ki" width={KI_G} height={KI_G} style={{ left: 0, top: 0, width: g, height: g }} />
      <div
        ref={griff}
        role="button"
        className="pet-ki-griff"
        style={{ left: 0, top: 0 }}
        title={`${pet.name} (${pet.besitzerName}) — antippen: sie freut sich, ziehen: mitnehmen und werfen`}
        onContextMenu={(e) => e.preventDefault()}
      />
    </>
  );
}
