import { useCallback, useEffect, useRef, useState } from "react";
import { verbindePets, type Haeufchen, type PetAufSchirm } from "./api";
import { PetBewegung, type Masse, type Rechteck, type Umgebung } from "./bewegung";
import "./pets.css";

/**
 * Critter-Pet auf dem Spieler-Tablet (Mark, 11.11.2026).
 *
 * Der Server sagt, welches Pet gerade auf diesem Bildschirm ist. Was es hier
 * tut — reinlaufen, herumtapsen, Pause, Häufchen, gestreichelt werden,
 * irgendwann am Rand raus — entscheidet dieses Tablet selbst. Läuft es raus,
 * meldet das Tablet „raus“, und der Server schickt es zum nächsten
 * eingeloggten Party-Mitglied.
 *
 * Nur verbunden, solange der Tab sichtbar ist: ein Tablet im Standby soll
 * das Pet nicht festhalten.
 */

// Gleiche Werte wie frontend/public/pets/<art>/sprite.json (aus
// docs/assets/critter-pet/sprites_exportieren.py).
const SPRITE = {
  breite: 84,
  hoehe: 48,
  fussLuft: 7,
  animationen: {
    idle: { frames: 24, ms: 110 },
    lauf: { frames: 32, ms: 35 },
    freuen: { frames: 8, ms: 90 },
    sprung: { frames: 6, ms: 70 },
    schlafen: { frames: 24, ms: 150 },
  },
} as const;

const HAEUFCHEN_PX = { breite: 12, hoehe: 10 };

function skala() {
  return window.innerWidth < 700 ? 1.5 : 2;
}

function masse(): Masse {
  const s = skala();
  return { bw: SPRITE.breite * s, bh: SPRITE.hoehe * s, fuss: SPRITE.fussLuft * s };
}

/** Bildschirm und offene Popups (`Fenster`) als Kletter-/Sprungziele. */
function umgebung(): Umgebung {
  const { bw, bh } = masse();
  const rechteckVon = (el: Element): Rechteck | null => {
    if (!el.isConnected) return null;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 ? r : null;
  };
  return {
    breite: window.innerWidth,
    hoehe: window.innerHeight,
    rechteckVon,
    popups: () =>
      Array.from(document.querySelectorAll(".fn-fenster"))
        .map((el) => ({ el, r: el.getBoundingClientRect() as Rechteck }))
        // Am Handy ist ein Fenster bildschirmfüllend — da ist oben kein Platz.
        .filter(({ r }) => r.top > bh + 30 && r.right - r.left > bw * 1.3),
    zufall: Math.random,
  };
}

export function PetOverlay({ campaignId }: { campaignId: string }) {
  const [pets, setPets] = useState<PetAufSchirm[]>([]);
  const [haeufchen, setHaeufchen] = useState<Haeufchen[]>([]);
  const [weg, setWeg] = useState<Set<string>>(new Set());
  const leitung = useRef<ReturnType<typeof verbindePets> | null>(null);

  useEffect(() => {
    const verbinden = () => {
      if (leitung.current) return;
      leitung.current = verbindePets(campaignId, (n) => {
        if (n.typ === "pets") setPets(n.daten);
        else if (n.typ === "haeufchen") setHaeufchen(n.daten);
      });
    };
    const trennen = () => {
      leitung.current?.schliessen();
      leitung.current = null;
      setPets([]);
    };
    const umschalten = () => (document.visibilityState === "visible" ? verbinden() : trennen());
    umschalten();
    document.addEventListener("visibilitychange", umschalten);
    return () => {
      document.removeEventListener("visibilitychange", umschalten);
      trennen();
    };
  }, [campaignId]);

  const senden = useCallback((n: object) => leitung.current?.senden(n), []);

  const wegmachen = (id: string) => {
    // Kurz ausblenden lassen, dann beim Server abmelden.
    setWeg((alt) => new Set(alt).add(id));
    window.setTimeout(() => senden({ typ: "wegmachen", id }), 350);
  };

  const s = skala();
  return (
    <div className="pet-ebene">
      {haeufchen.map((h) => (
        // Bewusst kein <button>: die globale Button-Optik (Fläche, Rahmen,
        // Hover-Leuchten) machte aus dem Sprite ein sichtbares Kästchen.
        <div
          key={h.id}
          role="button"
          className={`pet-haeufchen${weg.has(h.id) ? " pet-haeufchen-weg" : ""}`}
          title="Wegmachen"
          style={{
            left: h.x * window.innerWidth - (HAEUFCHEN_PX.breite * s) / 2,
            top: h.y * window.innerHeight - HAEUFCHEN_PX.hoehe * s,
            width: HAEUFCHEN_PX.breite * s,
            height: HAEUFCHEN_PX.hoehe * s,
            backgroundImage: `url(/pets/drache/haeufchen.png)`,
          }}
          onClick={() => wegmachen(h.id)}
        />
      ))}
      {pets.map((p) => (
        <PetFigur key={`${p.id}:${p.ankunft}`} pet={p} senden={senden} />
      ))}
    </div>
  );
}

interface Herz {
  id: number;
  x: number;
  y: number;
}

function PetFigur({ pet, senden }: { pet: PetAufSchirm; senden: (n: object) => void }) {
  const figur = useRef<HTMLDivElement | null>(null);
  const zzz = useRef<HTMLSpanElement | null>(null);
  const [herzen, setHerzen] = useState<Herz[]>([]);
  // Der Zustandsautomat lebt in einer Ref — kein React-Render pro Frame.
  const bewegung = useRef<PetBewegung | null>(null);

  useEffect(() => {
    const b = new PetBewegung(masse, umgebung(), pet.seite, performance.now(), (m) => {
      if (m.typ === "raus") senden({ typ: "raus", petId: pet.id, seite: m.seite });
      else senden({ typ: "haeufchen", petId: pet.id, x: m.x, y: m.y });
    });
    bewegung.current = b;

    let letzte = performance.now();
    let rahmen = 0;
    const tick = (jetzt: number) => {
      const dt = Math.min(0.1, (jetzt - letzte) / 1000);
      letzte = jetzt;
      b.setzeUmgebung(umgebung());
      b.tick(jetzt, dt);
      const d = b.darstellung(jetzt);

      const el = figur.current;
      if (el) {
        const s = skala();
        const anim = SPRITE.animationen[d.animation];
        const frame = Math.floor((jetzt - d.animStart) / anim.ms) % anim.frames;
        el.style.width = `${SPRITE.breite * s}px`;
        el.style.height = `${SPRITE.hoehe * s}px`;
        el.style.left = `${d.left}px`;
        el.style.top = `${d.top}px`;
        el.style.backgroundImage = `url(/pets/${pet.art}/${d.animation}.png)`;
        el.style.backgroundSize = `${anim.frames * SPRITE.breite * s}px ${SPRITE.hoehe * s}px`;
        el.style.backgroundPosition = `${-frame * SPRITE.breite * s}px 0`;
        el.style.transform = d.transform;
        el.dataset.hockt = d.hockt ? "ja" : "nein";
      }
      const z = zzz.current;
      if (z) {
        z.style.display = d.schlaeft ? "block" : "none";
        z.style.left = `${d.kopfX}px`;
        z.style.top = `${d.kopfY - 10}px`;
      }
      rahmen = requestAnimationFrame(tick);
    };
    rahmen = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rahmen);
    // Ein neuer Auftritt ist ein neuer key — die Abhängigkeiten bleiben fest.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const streicheln = () => {
    const b = bewegung.current;
    const jetzt = performance.now();
    if (!b || !b.streicheln(jetzt)) return;
    const d = b.darstellung(jetzt);
    const id = Date.now();
    setHerzen((alt) => [...alt, { id, x: d.kopfX - 20, y: d.kopfY }, { id: id + 1, x: d.kopfX + 4, y: d.kopfY }]);
    window.setTimeout(() => setHerzen((alt) => alt.filter((h) => h.id !== id && h.id !== id + 1)), 1300);
  };

  return (
    <>
      <div
        ref={figur}
        role="button"
        className="pet-figur"
        title={`${pet.name} (${pet.besitzerName}) — streicheln`}
        onPointerDown={streicheln}
      />
      <span ref={zzz} className="pet-zzz" style={{ display: "none" }}>
        <i style={{ backgroundImage: `url(/pets/${pet.art}/z.png)` }} />
        <i style={{ backgroundImage: `url(/pets/${pet.art}/z.png)` }} />
        <i style={{ backgroundImage: `url(/pets/${pet.art}/z.png)` }} />
      </span>
      {herzen.map((h, i) => (
        <span
          key={h.id}
          className="pet-herz"
          style={{
            left: h.x,
            top: h.y,
            animationDelay: `${i % 2 === 0 ? 0 : 180}ms`,
            backgroundImage: `url(/pets/${pet.art}/herz.png)`,
          }}
        />
      ))}
    </>
  );
}
