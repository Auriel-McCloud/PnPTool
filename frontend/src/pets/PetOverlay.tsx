import { useCallback, useEffect, useRef, useState } from "react";
import { verbindePets, type Haeufchen, type PetAufSchirm } from "./api";
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
  animationen: {
    idle: { frames: 24, ms: 110 },
    lauf: { frames: 24, ms: 60 },
    freuen: { frames: 8, ms: 90 },
  },
} as const;
type Animation = keyof typeof SPRITE.animationen;

const HAEUFCHEN_PX = { breite: 12, hoehe: 10 };
const TEMPO_PX_S = 45;

function zufall(min: number, max: number) {
  return min + Math.random() * (max - min);
}

function skala() {
  return window.innerWidth < 700 ? 1.5 : 2;
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

type Zustand = "laufen" | "idle" | "freuen" | "haeufchen" | "raus";

interface Herz {
  id: number;
  x: number;
}

function PetFigur({ pet, senden }: { pet: PetAufSchirm; senden: (n: object) => void }) {
  const figur = useRef<HTMLDivElement | null>(null);
  const [herzen, setHerzen] = useState<Herz[]>([]);
  // Alles, was jeden Frame wechselt, liegt in einer Ref — kein React-Render pro Frame.
  const z = useRef({
    zustand: "laufen" as Zustand,
    x: 0,
    richtung: 1,
    zielX: 0,
    bis: 0,
    besuchEnde: performance.now() + zufall(40_000, 120_000),
    haeufchenGemacht: false,
    rausGemeldet: false,
    animation: "lauf" as Animation,
    animStart: performance.now(),
  });

  const breite = () => SPRITE.breite * skala();

  useEffect(() => {
    const st = z.current;
    const w = breite();
    // Reinkommen von der Seite, die der Server sagt.
    if (pet.seite === "links") {
      st.x = -w;
      st.richtung = 1;
      st.zielX = zufall(0.1, 0.55) * window.innerWidth;
    } else {
      st.x = window.innerWidth;
      st.richtung = -1;
      st.zielX = zufall(0.4, 0.85) * window.innerWidth - w;
    }

    const setzeAnimation = (a: Animation, jetzt: number) => {
      if (st.animation !== a) {
        st.animation = a;
        st.animStart = jetzt;
      }
    };

    const naechstesZiel = () => {
      const w2 = breite();
      st.zielX = zufall(0, Math.max(0, window.innerWidth - w2));
      st.richtung = st.zielX >= st.x ? 1 : -1;
      st.zustand = "laufen";
    };

    let letzte = performance.now();
    let rahmen = 0;
    const tick = (jetzt: number) => {
      const dt = Math.min(0.1, (jetzt - letzte) / 1000);
      letzte = jetzt;
      const w2 = breite();

      if (st.zustand === "laufen" || st.zustand === "raus") {
        setzeAnimation("lauf", jetzt);
        const schritt = TEMPO_PX_S * dt * st.richtung;
        st.x += schritt;
        const angekommen = st.richtung > 0 ? st.x >= st.zielX : st.x <= st.zielX;
        if (angekommen) {
          st.x = st.zielX;
          if (st.zustand === "raus") {
            if (!st.rausGemeldet) {
              st.rausGemeldet = true;
              senden({ typ: "raus", petId: pet.id, seite: st.richtung > 0 ? "rechts" : "links" });
            }
          } else {
            st.zustand = "idle";
            st.bis = jetzt + zufall(2000, 6000);
          }
        }
      } else if (st.zustand === "idle" || st.zustand === "haeufchen" || st.zustand === "freuen") {
        setzeAnimation(st.zustand === "freuen" ? "freuen" : "idle", jetzt);
        if (jetzt >= st.bis) {
          if (st.zustand === "haeufchen") {
            // Liegt hinter dem Schwanz: links bei Blick nach rechts, sonst rechts.
            const s = skala();
            const schwanz = st.richtung > 0 ? st.x + 6 * s : st.x + w2 - 6 * s;
            senden({
              typ: "haeufchen",
              petId: pet.id,
              x: schwanz / window.innerWidth,
              y: (window.innerHeight - 2 * s) / window.innerHeight,
            });
            st.haeufchenGemacht = true;
            st.zustand = "idle";
            st.bis = jetzt + 1500;
          } else if (jetzt >= st.besuchEnde) {
            st.zustand = "raus";
            st.richtung = Math.random() < 0.5 ? -1 : 1;
            st.zielX = st.richtung > 0 ? window.innerWidth + 4 : -w2 - 4;
          } else if (st.zustand === "idle" && !st.haeufchenGemacht && Math.random() < 0.2) {
            st.zustand = "haeufchen";
            st.bis = jetzt + 1800;
          } else {
            naechstesZiel();
          }
        }
      }

      const el = figur.current;
      if (el) {
        const s = skala();
        const anim = SPRITE.animationen[st.animation];
        const frame = Math.floor((jetzt - st.animStart) / anim.ms) % anim.frames;
        el.style.width = `${SPRITE.breite * s}px`;
        el.style.height = `${SPRITE.hoehe * s}px`;
        el.style.left = `${st.x}px`;
        el.style.backgroundImage = `url(/pets/${pet.art}/${st.animation}.png)`;
        el.style.backgroundSize = `${anim.frames * SPRITE.breite * s}px ${SPRITE.hoehe * s}px`;
        el.style.backgroundPosition = `${-frame * SPRITE.breite * s}px 0`;
        el.style.transform = st.richtung < 0 ? "scaleX(-1)" : "none";
        el.dataset.hockt = st.zustand === "haeufchen" ? "ja" : "nein";
      }
      rahmen = requestAnimationFrame(tick);
    };
    rahmen = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rahmen);
    // Ein neuer Auftritt ist ein neuer key — die Abhängigkeiten bleiben fest.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const streicheln = () => {
    const st = z.current;
    if (st.zustand === "raus") return;
    st.zustand = "freuen";
    st.bis = performance.now() + 1600;
    const mitte = st.x + breite() / 2;
    const id = Date.now();
    setHerzen((alt) => [...alt, { id, x: mitte - 10 }, { id: id + 1, x: mitte + 14 }]);
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
      {herzen.map((h, i) => (
        <span
          key={h.id}
          className="pet-herz"
          style={{ left: h.x, animationDelay: `${i % 2 === 0 ? 0 : 180}ms`, backgroundImage: "url(/pets/drache/herz.png)" }}
        />
      ))}
    </>
  );
}
