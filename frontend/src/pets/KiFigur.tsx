import { useEffect, useRef } from "react";
import { KI_FOLGE, type PetAufSchirm } from "./api";
import { KI_FARBEN, KI_G, KI_GESTALTEN, KI_GESTALT_NAMEN, KiWesen, type KiFarbe } from "./ki";
import { makel, melde, vergiss } from "./treffen";

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
 */

type Zustand = "gleiten" | "schweben" | "gestalt" | "lesen" | "schlafen" | "raus" | "gezogen" | "wurf" | "weg";

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

export function KiFigur({ pet, senden }: { pet: PetAufSchirm; senden: (n: object) => void }) {
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
    if (!cv || !gr || !sc || !ctx) return;
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

    const entscheide = (jetzt: number) => {
      wesen.liest = false;
      lesen = null;
      if (wesen.gestalt) wesen.setzeGestalt(null);
      if (jetzt >= besuchEnde) {
        // Zum näheren Seitenrand hinaus.
        const nachRechts = x > breite() / 2;
        zustand = "raus";
        ziel = { x: nachRechts ? breite() + KI_G * p : -KI_G * p, y: klemme(y + zw(-80, 80), 60, hoehe() - 60) };
        return;
      }
      const st = stufe();
      const wahl: [number, () => void][] = [[5, () => gleite(irgendwo())]];
      if (st >= 1) {
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
      if (st >= 2) {
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
        if (zustand === "gleiten" || zustand === "raus") {
          const dx = ziel.x - x;
          const dy = ziel.y - y;
          const weit = Math.hypot(dx, dy);
          const tempo = TEMPO_PX_S * (zustand === "raus" ? 1.5 : Math.min(1, 0.25 + weit / 120));
          const k = Math.min(1, dt * 3);
          vx += ((dx / (weit || 1)) * tempo - vx) * k;
          vy += ((dy / (weit || 1)) * tempo - vy) * k;
          if (zustand === "raus" && (x < -KI_G * p * 0.5 || x > breite() + KI_G * p * 0.5)) raus(x < 0 ? "links" : "rechts");
          else if (zustand === "gleiten" && weit < 10) {
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
      // Angetippt: sie freut sich — ab dem Keim wird sie kurz ein Herz.
      sendenRef.current({ typ: "streicheln", petId: pet.id });
      wesen.schlaf = false;
      wesen.liest = false;
      lesen = null;
      danach = null;
      wesen.freude(jetzt);
      if (stufe() >= 1) {
        wesen.setzeGestalt("herz");
        if (stufe() >= 2) wesen.setzeFarbe("magenta", jetzt);
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
