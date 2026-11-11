import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { verbindePets, type Haeufchen, type PetAufSchirm } from "./api";
import { PACKEN_MS, PetBewegung, type Flaeche, type MenuePunkt, type Masse, type Quelle, type Rechteck, type Umgebung } from "./bewegung";
import { FlugBewegung, type PetSteuerung } from "./flug";
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
// docs/assets/critter-pet/sprites_exportieren.py bzw. baerbel_exportieren.py).
type Takt = { frames: number; ms: number };
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
  } as Record<string, Takt>,
} as const;

/** Bärbel, die fliegende Bibel (11.11.2026): alle Streifen 76×76, je Gestalt
 *  1–3 ein eigener Streifen; Fortbewegung und Schweben macht `flug.ts`. */
const BAERBEL = {
  breite: 76,
  hoehe: 76,
  /** Leerraum unter dem zugeklappten Buch (Sprite-Pixel) — zum Draufsitzen. */
  fussLuft: 14,
  animationen: {
    schweben_1: { frames: 12, ms: 140 },
    schweben_2: { frames: 12, ms: 140 },
    schweben_3: { frames: 12, ms: 140 },
    flattern_1: { frames: 16, ms: 45 },
    flattern_2: { frames: 16, ms: 45 },
    flattern_3: { frames: 16, ms: 45 },
    klappen_1: { frames: 5, ms: 60 },
    klappen_2: { frames: 5, ms: 60 },
    klappen_3: { frames: 5, ms: 60 },
    blinzeln_2: { frames: 19, ms: 110 },
    blinzeln_3: { frames: 5, ms: 70 },
  } as Record<string, Takt>,
  /** Wabernde Wolke (Mark: „intensiver, länger, ruhig ein wenig wabern“):
   *  eigene, größere Leinwand mittig über dem Buch. */
  verwandeln: { frames: 32, ms: 70, groesse: 112 },
} as const;

function sprite(art: string) {
  return art === "baerbel" ? BAERBEL : SPRITE;
}

/** Wie oft Bärbels Seite auf einer Wort-/Kastenkante liegen bleibt, die sie überquert. */
const LANDE_CHANCE = 0.7;

const SPUR_PX = {
  haeufchen: { breite: 12, hoehe: 10 },
  brand: { breite: 38, hoehe: 23 },
  seite: { breite: 14, hoehe: 11 },
} as const;
/** So viel muss man über einen Brandfleck reiben, bis er weg ist. */
const WISCH_PX = 450;

function skala() {
  return window.innerWidth < 700 ? 1.5 : 2;
}

function masse(art = "drache"): Masse {
  const s = skala();
  if (art === "baerbel") {
    return {
      bw: BAERBEL.breite * s,
      bh: BAERBEL.hoehe * s,
      fuss: BAERBEL.fussLuft * s,
      maulX: 0,
      maulY: 0,
      feuerLaenge: 0,
    };
  }
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

/** Ein Eintrag der Symbolspalte. Herausziehen setzt `data-pet-vor` — React
 * verwaltet das Attribut nicht und lässt es stehen; die Optik teilt es sich
 * mit `data-vor` (commlink.css). Das Antippen des Spielers bleibt unberührt. */
function menuePunkt(el: HTMLElement, hoehe: number): MenuePunkt {
  return {
    oben: () => {
      if (!el.isConnected) return null;
      const r = el.getBoundingClientRect();
      return r.height > 0 && r.top >= 0 && r.bottom <= hoehe ? r.top : null;
    },
    q: {
      rechteck: () => {
        if (!el.isConnected || el.dataset.petVor !== "true") return null;
        if (document.querySelector(".fn-fenster")) return null; // Popup drüber: runter
        const kante = el.closest(".cl-menue-tafel")?.getBoundingClientRect().right ?? 0;
        const r = el.getBoundingClientRect();
        if (r.right - kante < 40) return null;
        return { left: kante, right: r.right, top: r.top, bottom: r.bottom };
      },
    },
    aufklappen: () => {
      el.dataset.petVor = "true";
    },
    zuklappen: () => {
      delete el.dataset.petVor;
    },
  };
}

function umgebung(m: Masse = masse()): Umgebung {
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

  // Symbolspalte (Burgermenü) ab Tablet-Breite, nur ohne offenes Popup. Am
  // Handy ist sie eine eingefahrene Schublade (rechte Kante ≤ 0) bzw. offen
  // viel breiter — dann gilt wie bisher der Bildschirmrand.
  const tafel = fenster.length ? null : document.querySelector(".cl-menue-tafel");
  const tr = tafel?.getBoundingClientRect();
  const links = tr && tr.right > 0 && tr.width < 100 ? tr.right : 0;

  return {
    breite,
    hoehe,
    links,
    menuePunkte: () =>
      links > 0 && tafel
        ? Array.from(tafel.querySelectorAll<HTMLElement>(".cl-bereich:not(:disabled)")).map((el) => menuePunkt(el, hoehe))
        : [],
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
  // Welche Spuren schon da waren, als die Leitung aufging — alles danach ist
  // frisch entstanden (Bärbels Seite segelt dann erst los, statt gleich am
  // Element unter ihr in der Luft zu hängen).
  const bekannt = useRef<Set<string> | null>(null);
  const leitung = useRef<ReturnType<typeof verbindePets> | null>(null);

  useEffect(() => {
    const verbinden = () => {
      if (leitung.current) return;
      leitung.current = verbindePets(campaignId, (n) => {
        if (n.typ === "pets") setPets(n.daten);
        else if (n.typ === "haeufchen") {
          if (bekannt.current === null) bekannt.current = new Set(n.daten.map((h) => h.id));
          setHaeufchen(n.daten);
        }
      });
    };
    const trennen = () => {
      leitung.current?.schliessen();
      leitung.current = null;
      bekannt.current = null;
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
        // Bewusst kein <button>: die globale Button-Optik (Fläche, Rahmen,
        // Hover-Leuchten) machte aus dem Sprite ein sichtbares Kästchen.
        if ((h.art ?? "haeufchen") === "brand") {
          const px = SPUR_PX.brand;
          const stil = {
            left: h.x * window.innerWidth - (px.breite * s) / 2,
            top: h.y * window.innerHeight - (px.hoehe * s) / 2,
            width: px.breite * s,
            height: px.hoehe * s,
          };
          return <Brandfleck key={h.id} id={h.id} stil={stil} weg={weg.has(h.id)} onSauber={() => wegmachen(h.id)} />;
        }
        return (
          <HaeufchenAmElement
            key={h.id}
            h={h}
            art={h.art === "seite" ? "seite" : "haeufchen"}
            frisch={bekannt.current !== null && !bekannt.current.has(h.id)}
            weg={weg.has(h.id)}
            onWeg={() => wegmachen(h.id)}
            onGefallen={(x, y) => senden({ typ: "verschieben", id: h.id, x, y })}
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
 * Häufchen hängt am Element, auf dem es liegt (Mark, 11.11.2026: „nicht die
 * gleiche Position, sondern am HTML-Element hängen … und runterfallen, wenn
 * man die Seite wechselt“). Beim Auftauchen sucht es das Element unter sich
 * und merkt sich den Versatz; es scrollt und wandert mit. Verschwindet das
 * Element (Bereichswechsel, Popup zu, ausgeblendet), fällt es mit Schwerkraft
 * auf den Boden und meldet die neue Lage dem Server. Findet sich nach einer
 * Weile gar nichts darunter (z. B. nach dem Neuladen in einem anderen
 * Bereich), fällt es ebenfalls. Gezeichnet wird direkt am DOM, kein Render
 * pro Frame.
 */
function HaeufchenAmElement({
  h,
  art,
  frisch,
  weg,
  onWeg,
  onGefallen,
}: {
  h: Haeufchen;
  /** `seite` = Bärbels verlorene Seite: segelt flatternd zu Boden und liegt
   *  dort zerknittert (Mark, 11.11.2026: „verliert Seiten, die dann
   *  zerknittert rumliegen“). */
  art: "haeufchen" | "seite";
  /** Gerade erst entstanden (nicht vom Server mitgebracht): eine Seite segelt dann los. */
  frisch: boolean;
  weg: boolean;
  onWeg: () => void;
  onGefallen: (x: number, y: number) => void;
}) {
  const el = useRef<HTMLDivElement | null>(null);
  const gefallen = useRef(onGefallen);
  gefallen.current = onGefallen;
  const s = skala();
  const istSeite = art === "seite";
  const bw = SPUR_PX[art].breite * s;
  const bh = SPUR_PX[art].hoehe * s;
  const liegtBild = istSeite ? "url(/pets/baerbel/seite.png)" : "url(/pets/drache/haeufchen.png)";

  useLayoutEffect(() => {
    const div = el.current;
    if (!div) return;
    // Bezugspunkt: unten Mitte (dort, wo es aufliegt).
    let xAnteil = h.x;
    let x = h.x * window.innerWidth;
    let y = h.y * window.innerHeight;
    let boden = y >= window.innerHeight - 3;
    let anker: { el: Element; dx: number; dy: number } | null = null;
    let fall: { t0: number; y0: number; x0: number } | null = null;
    // Mark, 11.11.2026: „die Seiten müssen nicht immer ganz zu Boden fallen,
    // cooler wenn sie öfter mal an Wörtern usw. hängen bzw. liegen bleiben und
    // erst zu Boden fallen, wenn man die Seite wechselt“. Eine frische Seite
    // segelt los und bleibt mit LANDE_CHANCE auf jeder Wort-/Kastenkante
    // liegen, die sie überquert; dort hängt sie am Element wie ein Häufchen.
    // Verschwindet das Element, segelt sie ohne Halt zu Boden.
    let landeFlaechen: Flaeche[] = [];
    const schonGeprueft = new Set<Flaeche>();
    const losSegeln = (jetzt: number, mitLanden: boolean) => {
      fall = { t0: jetzt, y0: y, x0: x };
      div.style.backgroundImage = "url(/pets/baerbel/seite_fliegt.png)";
      div.classList.remove("pet-haeufchen-platsch");
      landeFlaechen = mitLanden ? umgebung({ bw, bh, fuss: 0, maulX: 0, maulY: 0, feuerLaenge: 0 }).flaechen() : [];
      schonGeprueft.clear();
    };
    if (istSeite && frisch && !boden) losSegeln(performance.now(), true);
    const suchenBis = performance.now() + 2500;

    const suche = () => {
      for (const e of document.elementsFromPoint(x, Math.min(y + 3, window.innerHeight - 1))) {
        if (e.closest(".pet-ebene")) continue;
        if (e === document.documentElement || e === document.body || e.id === "root") return null;
        const r = e.getBoundingClientRect();
        return { el: e, dx: x - r.left, dy: y - r.top };
      }
      return null;
    };

    const zeichnen = () => {
      div.style.left = `${x - bw / 2}px`;
      div.style.top = `${y - bh}px`;
    };

    let rahmen = 0;
    const takt = (jetzt: number) => {
      if (boden) {
        x = xAnteil * window.innerWidth;
        y = window.innerHeight;
      } else if (fall) {
        const t = Math.max(0, (jetzt - fall.t0) / 1000);
        const vorher = y;
        if (istSeite) {
          // Segeln: langsam, pendelt seitlich und kippt dabei.
          y = fall.y0 + 110 * t;
          x = fall.x0 + Math.sin(t * 2.4) * 22;
          div.style.transform = `rotate(${(Math.cos(t * 2.4) * 35).toFixed(1)}deg)`;
          // Auf einer Kante liegen bleiben?
          for (const f of landeFlaechen) {
            if (schonGeprueft.has(f) || f.r.top <= vorher || f.r.top > y) continue;
            if (x < f.r.left || x > f.r.right) continue;
            schonGeprueft.add(f);
            const r = f.q.rechteck();
            if (!r || Math.random() > LANDE_CHANCE) continue;
            y = r.top;
            fall = null;
            landeFlaechen = [];
            div.style.transform = "";
            div.style.backgroundImage = liegtBild;
            div.classList.add("pet-haeufchen-platsch");
            anker = suche();
            gefallen.current(Math.min(1, Math.max(0, x / window.innerWidth)), Math.min(1, Math.max(0, y / window.innerHeight)));
            break;
          }
          if (!fall) {
            zeichnen();
            rahmen = requestAnimationFrame(takt);
            return;
          }
        } else y = fall.y0 + 0.5 * 2600 * t * t;
        if (y >= window.innerHeight) {
          y = window.innerHeight;
          fall = null;
          boden = true;
          if (istSeite) {
            div.style.transform = "";
            div.style.backgroundImage = liegtBild;
          }
          xAnteil = Math.min(1, Math.max(0, x / window.innerWidth));
          div.classList.remove("pet-haeufchen-faellt");
          div.classList.add("pet-haeufchen-platsch");
          gefallen.current(xAnteil, 1);
        }
      } else if (anker) {
        const r = anker.el.getBoundingClientRect();
        if (!anker.el.isConnected || (r.width === 0 && r.height === 0)) {
          anker = null;
          if (istSeite) losSegeln(jetzt, false); // Seitenwechsel: ohne Halt zu Boden
          else fall = { t0: jetzt, y0: y, x0: x };
          div.classList.add("pet-haeufchen-faellt");
        } else {
          x = r.left + anker.dx;
          y = r.top + anker.dy;
        }
      } else {
        anker = suche();
        if (!anker && jetzt > suchenBis) {
          if (istSeite) losSegeln(jetzt, false);
          else fall = { t0: jetzt, y0: y, x0: x };
          div.classList.add("pet-haeufchen-faellt");
        }
      }
      zeichnen();
      rahmen = requestAnimationFrame(takt);
    };
    zeichnen();
    rahmen = requestAnimationFrame(takt);
    return () => cancelAnimationFrame(rahmen);
    // Lage kommt nur beim Auftauchen vom Server; danach führt das Häufchen selbst.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [h.id]);

  return (
    <div
      ref={el}
      role="button"
      className={`pet-haeufchen${weg ? " pet-haeufchen-weg" : ""}`}
      title={istSeite ? "Aufheben" : "Wegmachen"}
      style={{ width: bw, height: bh, backgroundImage: liegtBild }}
      onClick={onWeg}
    />
  );
}

/** Zufall mit festem Startwert — jeder Fleck sieht anders aus, aber immer gleich. */
function zufallAus(text: string) {
  let a = 0;
  for (let i = 0; i < text.length; i++) a = (Math.imul(a, 31) + text.charCodeAt(i)) | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const russCache = new Map<string, { bild: string; maske: string }>();

/**
 * Ruß auf dem Display-Glas (Mark, 11.11.2026: „so aussehen lassen, als
 * würden sie am Display sein“): durchscheinender, unregelmäßiger Rußfilm mit
 * Krümeln, Anlauffarben am Rand und einem Glanzstreif wie auf Glas. Dazu eine
 * Maske, durch die der Inhalt dahinter verschwommen und abgedunkelt wirkt
 * (backdrop-filter in pets.css) — wie Dreck auf der Scheibe.
 */
function russBild(id: string) {
  const alt = russCache.get(id);
  if (alt) return alt;
  const rnd = zufallAus(id);
  const W = 152;
  const H = 92;
  const cx = W / 2 + (rnd() - 0.5) * 8;
  const cy = H / 2 + (rnd() - 0.5) * 6;
  const zacken = Array.from({ length: 16 }, () => 0.72 + rnd() * 0.38);
  const form = (g: CanvasRenderingContext2D, sx: number, sy: number) => {
    g.beginPath();
    const punkte = zacken.map((k, i) => {
      const a = (i / zacken.length) * Math.PI * 2;
      return [cx + Math.cos(a) * sx * k, cy + Math.sin(a) * sy * k];
    });
    // Weich verbunden: Mittelpunkte als Stützstellen.
    const mitte = (i: number) => {
      const p = punkte[i % punkte.length];
      const q = punkte[(i + 1) % punkte.length];
      return [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2];
    };
    const start = mitte(0);
    g.moveTo(start[0], start[1]);
    for (let i = 1; i <= punkte.length; i++) {
      const p = punkte[i % punkte.length];
      const m = mitte(i);
      g.quadraticCurveTo(p[0], p[1], m[0], m[1]);
    }
    g.closePath();
  };
  const neu = () => {
    const c = document.createElement("canvas");
    c.width = W;
    c.height = H;
    return [c, c.getContext("2d")!] as const;
  };

  const [bc, g] = neu();
  g.filter = "blur(4px)";
  // Außen ein heller Grauschleier: Ruß auf Glas streut Licht, auf dunklem
  // Commlink sieht man ihn sonst gar nicht.
  form(g, W * 0.46, H * 0.42);
  g.fillStyle = "rgba(150,132,115,0.30)";
  g.fill();
  g.filter = "blur(3px)";
  form(g, W * 0.32, H * 0.29);
  g.fillStyle = "rgba(70,56,46,0.62)";
  g.fill();
  g.filter = "blur(2px)";
  form(g, W * 0.17 + rnd() * 6, H * 0.15 + rnd() * 4);
  g.fillStyle = "rgba(14,9,6,0.88)";
  g.fill();
  g.filter = "none";
  // Rußkrümel, nach außen dünner.
  for (let i = 0; i < 90; i++) {
    const a = rnd() * Math.PI * 2;
    const r = Math.sqrt(rnd());
    const px = cx + Math.cos(a) * r * W * 0.44;
    const py = cy + Math.sin(a) * r * H * 0.4;
    const gr = 1 + rnd() * 2.5;
    const hell = rnd() < 0.35;
    g.fillStyle = hell
      ? `rgba(175,160,145,${(0.25 + rnd() * 0.35) * (1.1 - r)})`
      : `rgba(12,8,6,${(0.3 + rnd() * 0.5) * (1.1 - r)})`;
    g.fillRect(px, py, gr, gr);
  }
  // Anlauffarben und Glanz nur dort, wo Ruß ist.
  g.globalCompositeOperation = "source-atop";
  const ring = g.createRadialGradient(cx, cy, H * 0.12, cx, cy, W * 0.5);
  ring.addColorStop(0, "rgba(0,0,0,0)");
  ring.addColorStop(0.5, "rgba(130,70,210,0.22)");
  ring.addColorStop(0.66, "rgba(40,170,210,0.2)");
  ring.addColorStop(0.82, "rgba(225,175,70,0.18)");
  ring.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = ring;
  g.fillRect(0, 0, W, H);
  const glanz = g.createLinearGradient(W * 0.1, 0, W * 0.9, H);
  glanz.addColorStop(0.32, "rgba(255,255,255,0)");
  glanz.addColorStop(0.4, "rgba(255,255,255,0.26)");
  glanz.addColorStop(0.45, "rgba(255,255,255,0)");
  glanz.addColorStop(0.52, "rgba(255,255,255,0.1)");
  glanz.addColorStop(0.55, "rgba(255,255,255,0)");
  g.fillStyle = glanz;
  g.fillRect(0, 0, W, H);

  const [mc, m] = neu();
  m.filter = "blur(5px)";
  form(m, W * 0.46, H * 0.42);
  m.fillStyle = "rgba(0,0,0,0.75)";
  m.fill();
  form(m, W * 0.3, H * 0.27);
  m.fillStyle = "rgba(0,0,0,1)";
  m.fill();

  const ergebnis = { bild: bc.toDataURL(), maske: mc.toDataURL() };
  russCache.set(id, ergebnis);
  return ergebnis;
}

/**
 * Brandfleck vom Feuerniesen (Mark, 11.11.2026): sitzt am Display, nicht an
 * der Seite — bewegt sich deshalb nie. Weg nur durch Wischen: Finger/Maus
 * drauf und hin und her reiben, er wird dabei blasser.
 */
function Brandfleck({
  id,
  stil,
  weg,
  onSauber,
}: {
  id: string;
  stil: React.CSSProperties;
  weg: boolean;
  onSauber: () => void;
}) {
  const russ = useMemo(() => russBild(id), [id]);
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
      style={{
        ...stil,
        backgroundImage: `url(${russ.bild})`,
        maskImage: `url(${russ.maske})`,
        WebkitMaskImage: `url(${russ.maske})`,
      }}
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
  const puff = useRef<HTMLDivElement | null>(null);
  const [herzen, setHerzen] = useState<Herz[]>([]);
  // Der Zustandsautomat lebt in einer Ref — kein React-Render pro Frame.
  // Laufen (Drache) oder Fliegen (Bärbel), gleiche Schnittstelle.
  const bewegung = useRef<PetSteuerung | null>(null);

  // Mark, 11.11.: „er zappelt zwar, aber ich kann ihn nicht verschieben,
  // meistens verschiebe ich den ganzen Screen“. `touch-action: none` allein
  // reicht auf dem Tablet nicht verlässlich — der Browser entscheidet beim
  // Aufsetzen auf seiner (bei einer laufenden Figur oft veralteten) Kopie der
  // Seite, ob gescrollt wird, und bricht dann unsere Pointer-Kette ab. Darum
  // die Touch-Ereignisse direkt an der Figur abfangen (nicht passiv, sonst
  // wirkt preventDefault nicht): kein Scrollen, kein Zurückziehen, kein
  // Lange-Drücken-Menü. Die Pointer-Ereignisse kommen trotzdem an.
  useEffect(() => {
    const el = figur.current;
    if (!el) return;
    const stopp = (e: TouchEvent) => {
      if (e.cancelable) e.preventDefault();
    };
    el.addEventListener("touchstart", stopp, { passive: false });
    el.addEventListener("touchmove", stopp, { passive: false });
    return () => {
      el.removeEventListener("touchstart", stopp);
      el.removeEventListener("touchmove", stopp);
    };
  }, []);

  useEffect(() => {
    const fliegt = pet.art === "baerbel";
    const sp = sprite(pet.art);
    const m = () => masse(pet.art);
    const melden = (n: Parameters<ConstructorParameters<typeof PetBewegung>[4]>[0]) => {
      if (n.typ === "raus") senden({ typ: "raus", petId: pet.id, seite: n.seite });
      else senden({ typ: "haeufchen", petId: pet.id, x: n.x, y: n.y, art: n.art });
    };
    const b: PetSteuerung = fliegt
      ? new FlugBewegung(m, umgebung(m()), pet.seite, performance.now(), melden)
      : new PetBewegung(m, umgebung(m()), pet.seite, performance.now(), melden);
    bewegung.current = b;

    let letzte = performance.now();
    let rahmen = 0;
    const tick = (jetzt: number) => {
      const dt = Math.min(0.1, (jetzt - letzte) / 1000);
      letzte = jetzt;
      b.setzeUmgebung(umgebung(m()));
      b.tick(jetzt, dt);
      const d = b.darstellung(jetzt);

      const el = figur.current;
      if (el) {
        const s = skala();
        const anim = sp.animationen[d.animation] ?? { frames: 1, ms: 1000 };
        const frame = d.frame ?? Math.floor((jetzt - d.animStart) / anim.ms) % anim.frames;
        el.style.width = `${sp.breite * s}px`;
        el.style.height = `${sp.hoehe * s}px`;
        el.style.left = `${d.left}px`;
        el.style.top = `${d.top}px`;
        el.style.backgroundImage = `url(/pets/${pet.art}/${d.animation}.png)`;
        el.style.backgroundSize = `${anim.frames * sp.breite * s}px ${sp.hoehe * s}px`;
        el.style.backgroundPosition = `${-frame * sp.breite * s}px 0`;
        el.style.transform = d.transform;
        el.dataset.hockt = d.hockt ? "ja" : "nein";
        el.dataset.gepackt = d.gepackt ? "ja" : "nein";
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
      const pu = puff.current;
      if (pu) {
        if (d.puff != null && pet.art === "baerbel") {
          const s = skala();
          const v = BAERBEL.verwandeln;
          const bild = Math.min(v.frames - 1, Math.floor((jetzt - d.puff) / v.ms));
          pu.style.display = "block";
          const rand = ((v.groesse - BAERBEL.breite) / 2) * s;
          pu.style.width = `${v.groesse * s}px`;
          pu.style.height = `${v.groesse * s}px`;
          pu.style.left = `${d.left - rand}px`;
          pu.style.top = `${d.top - rand}px`;
          pu.style.backgroundSize = `${v.frames * v.groesse * s}px ${v.groesse * s}px`;
          pu.style.backgroundPosition = `${-bild * v.groesse * s}px 0`;
        } else pu.style.display = "none";
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
    return () => {
      cancelAnimationFrame(rahmen);
      b.aufraeumen();
    };
    // Ein neuer Auftritt ist ein neuer key — die Abhängigkeiten bleiben fest.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Antippen = streicheln; 3 s draufbleiben = packen, ziehen, werfen.
  // Mark, 11.11.: „meistens zittert er nur und folgt meiner Maus nicht“ —
  // wer vor Ablauf der 3 s losgezogen hat, hat das Packen bisher abgebrochen.
  // Jetzt bricht Bewegung nichts mehr ab: solange gedrückt, wird er nach 3 s
  // gepackt und springt dann an den Finger/die Maus, wo die gerade ist.
  const druck = useRef<{ x: number; y: number; id: number; bewegt: boolean } | null>(null);

  const runter = (e: React.PointerEvent<HTMLDivElement>) => {
    const b = bewegung.current;
    if (!b) return;
    if (!b.druckStart(performance.now())) return;
    druck.current = { x: e.clientX, y: e.clientY, id: e.pointerId, bewegt: false };
    b.fingerMerken(e.clientX, e.clientY, performance.now());
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const bewegen = (e: React.PointerEvent<HTMLDivElement>) => {
    const b = bewegung.current;
    const d = druck.current;
    if (!b || !d || d.id !== e.pointerId) return;
    const jetzt = performance.now();
    if (b.gepackt) {
      b.tragen(e.clientX, e.clientY, jetzt);
    } else {
      b.fingerMerken(e.clientX, e.clientY, jetzt);
      if (Math.hypot(e.clientX - d.x, e.clientY - d.y) > 40) d.bewegt = true;
    }
  };

  const hoch = (e: React.PointerEvent<HTMLDivElement>) => {
    const b = bewegung.current;
    const d = druck.current;
    druck.current = null;
    if (!b || !d || d.id !== e.pointerId) return;
    const jetzt = performance.now();
    if (b.gepackt) {
      b.tragen(e.clientX, e.clientY, jetzt);
      b.loslassen(jetzt);
    } else {
      b.druckAbbrechen(jetzt);
      // Kurz und ruhig getippt = streicheln; vorzeitig gezogen = nichts.
      if (!d.bewegt) streicheln();
    }
  };

  const abgebrochen = () => {
    const b = bewegung.current;
    druck.current = null;
    if (!b) return;
    const jetzt = performance.now();
    if (b.gepackt) b.loslassen(jetzt);
    else b.druckAbbrechen(jetzt);
  };

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
        title={`${pet.name} (${pet.besitzerName}) — antippen: ${pet.art === "baerbel" ? "freuen" : "streicheln"}, ${PACKEN_MS / 1000} s halten: packen und werfen`}
        onPointerDown={runter}
        onPointerMove={bewegen}
        onPointerUp={hoch}
        onPointerCancel={abgebrochen}
        onContextMenu={(e) => e.preventDefault()}
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
      {pet.art === "baerbel" && (
        <div ref={puff} className="pet-feuer" style={{ display: "none", backgroundImage: "url(/pets/baerbel/verwandeln.png)" }} />
      )}
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
