import { useCallback, useEffect, useRef, useState } from "react";
import { verbindePets, type Haeufchen, type PetAufSchirm } from "./api";
import { PetBewegung, type Flaeche, type Masse, type Quelle, type Rechteck, type Umgebung } from "./bewegung";
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
  maul: [73, 26],
  feuer: { breite: 56, hoehe: 28, frames: 16, ms: 70 },
  animationen: {
    idle: { frames: 24, ms: 110 },
    lauf: { frames: 32, ms: 35 },
    freuen: { frames: 8, ms: 90 },
    klettern: { frames: 32, ms: 35 },
    niesen: { frames: 22, ms: 80 },
    sprung: { frames: 6, ms: 70 },
    schlafen: { frames: 24, ms: 150 },
  },
} as const;

const SPUR_PX = {
  haeufchen: { breite: 12, hoehe: 10 },
  brand: { breite: 32, hoehe: 18 },
} as const;
/** So viel muss man über einen Brandfleck reiben, bis er weg ist. */
const WISCH_PX = 450;

function skala() {
  return window.innerWidth < 700 ? 1.5 : 2;
}

function masse(): Masse {
  const s = skala();
  return {
    bw: SPRITE.breite * s,
    bh: SPRITE.hoehe * s,
    fuss: SPRITE.fussLuft * s,
    maulX: SPRITE.maul[0] * s,
    maulY: SPRITE.maul[1] * s,
    feuerLaenge: SPRITE.feuer.breite * s,
  };
}

/**
 * Worauf er stehen kann (Mark, 11.11.2026: „auf Wörtern, Linien, Punkten,
 * Kästchen usw. rumlaufen“). Textzeilen über Range-Rechtecke, dazu Knöpfe,
 * Felder, Bilder, Linien, Punkte-Reihen, Kacheln/Karten und Popups.
 */
const KASTEN = [
  "button",
  "input",
  "select",
  "textarea",
  "img",
  "hr",
  "h1",
  "h2",
  "h3",
  "h4",
  "table",
  ".fn-fenster",
  ".cl-roehre",
  ".dot-reihe",
  ".kk-punkt",
  ".bo-punkt",
  "[class*='kachel']",
  "[class*='karte']",
].join(",");
const MAX_TEXTKNOTEN = 400;
const MAX_KAESTEN = 300;

/** Liegt an dieser Stelle wirklich das erwartete Element oben (nicht verdeckt,
 * nicht weggescrollt in einem Container)? Das Pet selbst zählt nicht. */
function obenAuf(x: number, y: number, ziel: Element): boolean {
  for (const el of document.elementsFromPoint(x, y)) {
    if (el.closest(".pet-ebene")) continue;
    return el === ziel || ziel.contains(el) || el.contains(ziel);
  }
  return false;
}

function brauchbar(r: Rechteck, m: Masse, hoehe: number, breite: number): boolean {
  return (
    r.right - r.left >= 14 &&
    r.top >= m.bh - m.fuss + 4 && // Platz für den Kopf
    r.top <= hoehe - 30 && // sonst ist es praktisch der Boden
    r.right > 0 &&
    r.left < breite
  );
}

function umgebung(): Umgebung {
  const m = masse();
  const breite = window.innerWidth;
  const hoehe = window.innerHeight;

  // Mit offenem Popup nur noch innerhalb des obersten Popups — der Rest liegt
  // abgedunkelt dahinter.
  const fenster = Array.from(document.querySelectorAll(".fn-fenster"));
  const wurzel: Element = fenster.length ? fenster[fenster.length - 1] : document.body;

  const elementQuelle = (el: Element): Quelle => ({
    rechteck: () => {
      if (!el.isConnected) return null;
      const r = el.getBoundingClientRect();
      if (!brauchbar(r, m, hoehe, breite)) return null;
      return obenAuf((Math.max(r.left, 0) + Math.min(r.right, breite)) / 2, r.top + 2, el) ? r : null;
    },
  });

  const flaechen = (): Flaeche[] => {
    const aus: Flaeche[] = [];
    const kaesten = [wurzel, ...Array.from(wurzel.querySelectorAll(KASTEN)).slice(0, MAX_KAESTEN)];
    for (const el of kaesten) {
      if (el === document.body) continue;
      const q = elementQuelle(el);
      const r = q.rechteck();
      if (r) aus.push({ q, r });
    }
    const walker = document.createTreeWalker(wurzel, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) =>
        n.nodeValue?.trim() && !n.parentElement?.closest(".pet-ebene, script, style")
          ? NodeFilter.FILTER_ACCEPT
          : NodeFilter.FILTER_REJECT,
    });
    let knoten: Node | null;
    let gezaehlt = 0;
    while ((knoten = walker.nextNode()) && gezaehlt < MAX_TEXTKNOTEN) {
      gezaehlt += 1;
      const text = knoten;
      const eltern = text.parentElement;
      if (!eltern) continue;
      const range = document.createRange();
      range.selectNodeContents(text);
      const zeilen = range.getClientRects();
      for (let i = 0; i < zeilen.length; i++) {
        const q: Quelle = {
          rechteck: () => {
            if (!text.isConnected) return null;
            const r = range.getClientRects()[i];
            if (!r || !brauchbar(r, m, hoehe, breite)) return null;
            return obenAuf((r.left + r.right) / 2, r.top + Math.min(4, r.height / 2), eltern) ? r : null;
          },
        };
        const r = q.rechteck();
        if (r) aus.push({ q, r });
      }
    }
    return aus;
  };

  return {
    breite,
    hoehe,
    flaechen,
    // Klettern nur an Popups, die oben Platz lassen (am Handy bildschirmfüllend).
    waende: () =>
      fenster
        .map((el) => ({ q: elementQuelle(el), r: el.getBoundingClientRect() as Rechteck }))
        .filter(({ r }) => r.top > m.bh + 30 && r.right - r.left > m.bw * 1.3),
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
      {haeufchen.map((h) => {
        const art = h.art ?? "haeufchen";
        const px = SPUR_PX[art];
        const stil = {
          left: h.x * window.innerWidth - (px.breite * s) / 2,
          top: h.y * window.innerHeight - (art === "brand" ? (px.hoehe * s) / 2 : px.hoehe * s),
          width: px.breite * s,
          height: px.hoehe * s,
          backgroundImage: `url(/pets/drache/${art}.png)`,
        };
        // Bewusst kein <button>: die globale Button-Optik (Fläche, Rahmen,
        // Hover-Leuchten) machte aus dem Sprite ein sichtbares Kästchen.
        return art === "brand" ? (
          <Brandfleck key={h.id} stil={stil} weg={weg.has(h.id)} onSauber={() => wegmachen(h.id)} />
        ) : (
          <div
            key={h.id}
            role="button"
            className={`pet-haeufchen${weg.has(h.id) ? " pet-haeufchen-weg" : ""}`}
            title="Wegmachen"
            style={stil}
            onClick={() => wegmachen(h.id)}
          />
        );
      })}
      {pets.map((p) => (
        <PetFigur key={`${p.id}:${p.ankunft}`} pet={p} senden={senden} />
      ))}
    </div>
  );
}

/**
 * Brandfleck vom Feuerniesen (Mark, 11.11.2026): weg nur durch Wischen —
 * Finger/Maus drauf und hin und her reiben, er wird dabei blasser.
 */
function Brandfleck({ stil, weg, onSauber }: { stil: React.CSSProperties; weg: boolean; onSauber: () => void }) {
  const rest = useRef(1);
  const letzter = useRef<{ x: number; y: number } | null>(null);
  const el = useRef<HTMLDivElement | null>(null);
  const fertig = useRef(false);

  const reiben = (e: React.PointerEvent<HTMLDivElement>) => {
    if (fertig.current || !letzter.current) return;
    const d = Math.hypot(e.clientX - letzter.current.x, e.clientY - letzter.current.y);
    letzter.current = { x: e.clientX, y: e.clientY };
    rest.current = Math.max(0, rest.current - d / WISCH_PX);
    if (el.current) el.current.style.opacity = String(0.25 + rest.current * 0.75);
    if (rest.current <= 0) {
      fertig.current = true;
      onSauber();
    }
  };

  return (
    <div
      ref={el}
      role="button"
      className={`pet-brand${weg ? " pet-haeufchen-weg" : ""}`}
      title="Sauberwischen"
      style={stil}
      onPointerDown={(e) => {
        letzter.current = { x: e.clientX, y: e.clientY };
        e.currentTarget.setPointerCapture(e.pointerId);
      }}
      onPointerMove={reiben}
      onPointerUp={() => (letzter.current = null)}
      onPointerCancel={() => (letzter.current = null)}
    />
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
  const tropfen = useRef<HTMLSpanElement | null>(null);
  const feuer = useRef<HTMLDivElement | null>(null);
  const [herzen, setHerzen] = useState<Herz[]>([]);
  // Der Zustandsautomat lebt in einer Ref — kein React-Render pro Frame.
  const bewegung = useRef<PetBewegung | null>(null);

  useEffect(() => {
    const b = new PetBewegung(masse, umgebung(), pet.seite, performance.now(), (m) => {
      if (m.typ === "raus") senden({ typ: "raus", petId: pet.id, seite: m.seite });
      else senden({ typ: "haeufchen", petId: pet.id, x: m.x, y: m.y, art: m.art });
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
        const frame = d.frame ?? Math.floor((jetzt - d.animStart) / anim.ms) % anim.frames;
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
      const fe = feuer.current;
      if (fe) {
        if (d.feuer) {
          const s = skala();
          const f = SPRITE.feuer;
          const bild = Math.min(f.frames - 1, Math.floor((jetzt - d.feuer.start) / f.ms));
          fe.style.display = "block";
          fe.style.width = `${f.breite * s}px`;
          fe.style.height = `${f.hoehe * s}px`;
          fe.style.left = `${d.feuer.flip ? d.feuer.x - f.breite * s : d.feuer.x}px`;
          fe.style.top = `${d.feuer.y - (f.hoehe * s) / 2}px`;
          fe.style.backgroundSize = `${f.frames * f.breite * s}px ${f.hoehe * s}px`;
          fe.style.backgroundPosition = `${-bild * f.breite * s}px 0`;
          fe.style.transform = d.feuer.flip ? "scaleX(-1)" : "none";
        } else fe.style.display = "none";
      }
      const tr = tropfen.current;
      if (tr) {
        tr.style.display = d.schwitzt ? "block" : "none";
        tr.style.left = `${d.kopfX}px`;
        tr.style.top = `${d.kopfY + 6}px`;
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
      <div
        ref={feuer}
        className="pet-feuer"
        style={{ display: "none", backgroundImage: `url(/pets/${pet.art}/feuer.png)` }}
      />
      <span ref={tropfen} className="pet-tropfen" style={{ display: "none" }}>
        <i style={{ backgroundImage: `url(/pets/${pet.art}/tropfen.png)` }} />
        <i style={{ backgroundImage: `url(/pets/${pet.art}/tropfen.png)` }} />
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
