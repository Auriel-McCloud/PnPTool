import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { atemVon, istDrache, verbindePets, type Haeufchen, type Lesung, type PetAufSchirm } from "./api";
import { FLOCKE_LIEGT_MS, FLOCKEN_G, PACKEN_MS, PetBewegung, type Flaeche, type MenuePunkt, type Masse, type Quelle, type Rechteck, type SpurAufSchirm, type Umgebung } from "./bewegung";
import { FlugBewegung, type PetSteuerung } from "./flug";
import { BaerbelBuch, type Rechteck as BuchRechteck } from "./BaerbelBuch";
import { alle, makel, melde, treffe, vergiss } from "./treffen";
import "./pets.css";

/** Steuerungen der gerade sichtbaren Pets — Feuer trifft die andere Figur. */
const steuerungen = new Map<string, PetSteuerung>();

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
  /** Glückswolke des Wolkenlaufs (wolke.png). */
  wolke: { breite: 36, hoehe: 20, frames: 14, ms: 110 },
  animationen: {
    idle: { frames: 24, ms: 110 },
    lauf: { frames: 32, ms: 35 },
    freuen: { frames: 8, ms: 90 },
    klettern: { frames: 32, ms: 35 },
    niesen: { frames: 22, ms: 80 },
    sprung: { frames: 6, ms: 70 },
    schlafen: { frames: 24, ms: 150 },
    fressen: { frames: 16, ms: 90 },
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
  /** Effekt-Streifen auf eigener Leinwand; `rand` = Lage der 76er-Figur darin (links/oben). */
  effekte: {
    tentakel_1: { frames: 44, ms: 80, breite: 128, hoehe: 120, rand: 18 },
    tentakel_2: { frames: 44, ms: 80, breite: 128, hoehe: 120, rand: 18 },
    tentakel_3: { frames: 44, ms: 80, breite: 128, hoehe: 120, rand: 18 },
  } as Record<string, { frames: number; ms: number; breite: number; hoehe: number; rand: number }>,
} as const;

function sprite(art: string) {
  return art === "baerbel" ? BAERBEL : SPRITE;
}

/** Spuren, die ein Pet gerade gepackt hat (Drache schnappt eine Seite, Bärbels
 *  Tentakel holt ein Häufchen) — Mitte in Bildschirm-Pixeln. Die Spur folgt
 *  dann diesem Punkt statt ihrem Element. */
const gegriffen = new Map<string, { x: number; y: number; skala: number }>();

/** Wie oft Bärbels Seite auf einer Wort-/Kastenkante liegen bleibt, die sie überquert. */
const LANDE_CHANCE = 0.7;

const SPUR_PX = {
  haeufchen: { breite: 12, hoehe: 10 },
  brand: { breite: 38, hoehe: 23 },
  seite: { breite: 14, hoehe: 11 },
  schleim: { breite: 50, hoehe: 45 },
  frost: { breite: 38, hoehe: 23 },
} as const;
/** So viel muss man über einen Brandfleck reiben, bis er weg ist. */
const WISCH_PX = 450;

/** So viele Wolken sind höchstens gleichzeitig zu sehen (Lebensdauer / Takt + Reserve). */
const WOLKEN_MAX = 10;
/** Rußflocken beim Schütteln (je Schütteln etwa 40). */
const FLOCKEN_MAX = 56;

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
    atem: atemVon(art),
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
    // Seiten und Häufchen, die gerade irgendwo liegen (nicht fallend/segelnd).
    spuren: (): SpurAufSchirm[] =>
      Array.from(document.querySelectorAll<HTMLElement>(".pet-haeufchen[data-id]:not(.pet-haeufchen-weg)"))
        .filter((el) => el.dataset.fliegt !== "ja")
        .map((el) => {
          const r = el.getBoundingClientRect();
          return { id: el.dataset.id!, art: el.dataset.art!, x: (r.left + r.right) / 2, y: (r.top + r.bottom) / 2, unten: r.bottom };
        }),
    // Klettern nur an Popups, die oben Platz lassen (am Handy bildschirmfüllend).
    waende: () =>
      fenster
        .map((el) => ({ q: elementQuelle(el), r: el.getBoundingClientRect() as Rechteck }))
        .filter(({ r }) => r.top > m.bh + 30 && r.right - r.left > m.bw * 1.3),
    nachbarn: () => alle().map((n) => ({ art: n.art, x: n.x, y: n.y, w: n.w, h: n.h })),
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
  const [lesungen, setLesungen] = useState<Record<string, Lesung>>({});
  const weggelegt = useRef(new Set<string>());

  useEffect(() => {
    const verbinden = () => {
      if (leitung.current) return;
      leitung.current = verbindePets(campaignId, (n) => {
        if (n.typ === "pets") {
          setPets(n.daten);
          setLesungen((alt) => {
            const next = { ...alt };
            const ids = new Set(n.daten.map((p) => p.id));
            for (const id of Object.keys(next)) if (!ids.has(id)) delete next[id];
            for (const p of n.daten) {
              if (p.lesung && !weggelegt.current.has(p.id)) next[p.id] = p.lesung;
              if (!p.lesung) {
                delete next[p.id];
                weggelegt.current.delete(p.id);
              }
            }
            return next;
          });
        } else if (n.typ === "vorlesen") {
          if (!weggelegt.current.has(n.petId)) {
            setLesungen((alt) => ({
              ...alt,
              [n.petId]: { stelle: n.stelle, zitat: n.zitat },
            }));
          }
        } else if (n.typ === "haeufchen") {
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
        if (h.art === "brand" || h.art === "schleim" || h.art === "frost") {
          const px = SPUR_PX[h.art];
          const stil = {
            left: h.x * window.innerWidth - (px.breite * s) / 2,
            top: h.y * window.innerHeight - (px.hoehe * s) / 2,
            width: px.breite * s,
            height: px.hoehe * s,
          };
          return (
            <Brandfleck
              key={h.id}
              id={h.id}
              art={h.art}
              stil={stil}
              weg={weg.has(h.id)}
              onSauber={() => wegmachen(h.id)}
            />
          );
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
        <PetFigur
          key={`${p.id}:${p.ankunft}`}
          pet={p}
          senden={senden}
          wegmachen={wegmachen}
          lesung={lesungen[p.id] ?? null}
          onGelesen={(id) => {
            weggelegt.current.add(id);
            setLesungen((alt) => {
              const next = { ...alt };
              delete next[id];
              return next;
            });
          }}
        />
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
      const griff = gegriffen.get(h.id);
      if (griff) {
        // Gepackt: folgt Maul/Tentakel, wird kleiner, bis es weg ist.
        x = griff.x;
        y = griff.y + bh / 2;
        div.style.transform = `scale(${griff.skala.toFixed(2)})`;
        div.dataset.fliegt = "ja";
        zeichnen();
        rahmen = requestAnimationFrame(takt);
        return;
      }
      div.dataset.fliegt = fall ? "ja" : "";
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
      data-id={h.id}
      data-art={art}
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

const frostCache = new Map<string, { bild: string; maske: string }>();

/**
 * Raureif vom Eisdrachen (Mark, 12.11.2026): wie der Ruß ein Fleck auf dem
 * Display-Glas, aber kalt — milchig-weißer Hauch, Eisblumen, die vom Rand
 * nach innen wachsen, ein paar glitzernde Kristalle. Wegwischen wie Ruß.
 */
function frostBild(id: string) {
  const alt = frostCache.get(id);
  if (alt) return alt;
  const rnd = zufallAus(id + ":frost");
  const W = 152;
  const H = 92;
  const cx = W / 2 + (rnd() - 0.5) * 8;
  const cy = H / 2 + (rnd() - 0.5) * 6;
  const zacken = Array.from({ length: 16 }, () => 0.74 + rnd() * 0.36);
  const form = (g: CanvasRenderingContext2D, sx: number, sy: number) => {
    g.beginPath();
    const punkte = zacken.map((k, i) => {
      const a = (i / zacken.length) * Math.PI * 2;
      return [cx + Math.cos(a) * sx * k, cy + Math.sin(a) * sy * k];
    });
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
  form(g, W * 0.46, H * 0.42);
  g.fillStyle = "rgba(200,228,255,0.30)";
  g.fill();
  g.filter = "blur(2px)";
  form(g, W * 0.3, H * 0.27);
  g.fillStyle = "rgba(235,246,255,0.38)";
  g.fill();
  g.filter = "none";
  // Eisblumen: verzweigte Farnäste, vom Rand schräg zur Mitte gewachsen.
  const ast = (x: number, y: number, w: number, l: number, tiefe: number) => {
    if (tiefe > 3 || l < 3) return;
    const x2 = x + Math.cos(w) * l;
    const y2 = y + Math.sin(w) * l;
    g.strokeStyle = `rgba(240,250,255,${0.75 - tiefe * 0.15})`;
    g.lineWidth = Math.max(0.6, 1.6 - tiefe * 0.4);
    g.beginPath();
    g.moveTo(x, y);
    g.lineTo(x2, y2);
    g.stroke();
    const n = 2 + Math.floor(rnd() * 3);
    for (let i = 1; i <= n; i++) {
      const k = i / (n + 1);
      const bx = x + (x2 - x) * k;
      const by = y + (y2 - y) * k;
      ast(bx, by, w + 0.9 + (rnd() - 0.5) * 0.3, l * 0.42, tiefe + 1);
      ast(bx, by, w - 0.9 + (rnd() - 0.5) * 0.3, l * 0.42, tiefe + 1);
    }
  };
  const aeste = 5 + Math.floor(rnd() * 3);
  for (let i = 0; i < aeste; i++) {
    const a = (i / aeste) * Math.PI * 2 + rnd() * 0.6;
    const r = 0.75 + rnd() * 0.2;
    const x = cx + Math.cos(a) * W * 0.42 * r;
    const y = cy + Math.sin(a) * H * 0.38 * r;
    ast(x, y, a + Math.PI + (rnd() - 0.5) * 0.5, W * (0.16 + rnd() * 0.1), 0);
  }
  // Glitzernde Kristalle.
  for (let i = 0; i < 26; i++) {
    const a = rnd() * Math.PI * 2;
    const r = Math.sqrt(rnd());
    const px = cx + Math.cos(a) * r * W * 0.42;
    const py = cy + Math.sin(a) * r * H * 0.38;
    const gr = 1 + rnd() * 1.6;
    g.fillStyle = `rgba(255,255,255,${0.5 + rnd() * 0.5})`;
    g.fillRect(px - gr / 2, py - gr / 2, gr, gr);
    if (rnd() < 0.3) {
      g.fillStyle = "rgba(190,230,255,0.8)";
      g.fillRect(px - gr * 1.5, py - 0.4, gr * 3, 0.8);
      g.fillRect(px - 0.4, py - gr * 1.5, 0.8, gr * 3);
    }
  }
  // Kalter Glanz nur auf dem Reif.
  g.globalCompositeOperation = "source-atop";
  const glanz = g.createLinearGradient(W * 0.1, 0, W * 0.9, H);
  glanz.addColorStop(0.3, "rgba(150,210,255,0)");
  glanz.addColorStop(0.42, "rgba(170,225,255,0.3)");
  glanz.addColorStop(0.5, "rgba(150,210,255,0)");
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
  frostCache.set(id, ergebnis);
  return ergebnis;
}

const schleimCache = new Map<string, { bild: string; maske: string }>();

/**
 * Feuchter Schmierfleck vom Tentakelmonster (Mark, 11.11.2026: „hinterlässt
 * feuchte Schmierflecken am Display wie das Feuer“): durchscheinend grüner
 * Klatscher mit Spritzern, herunterlaufenden Tropfnasen und nassem Glanz.
 * Maske wie beim Ruß, damit der Inhalt dahinter leicht verzerrt wirkt.
 */
function schleimBild(id: string) {
  const alt = schleimCache.get(id);
  if (alt) return alt;
  const rnd = zufallAus(id + ":schleim");
  const W = 160;
  const H = 144;
  const cx = W / 2 + (rnd() - 0.5) * 10;
  const cy = H * 0.36;
  const zacken = Array.from({ length: 14 }, () => 0.7 + rnd() * 0.45);
  const tropfen = Array.from({ length: 3 + Math.floor(rnd() * 3) }, () => ({
    x: cx + (rnd() - 0.5) * W * 0.5,
    l: H * (0.18 + rnd() * 0.4),
    b: 4 + rnd() * 5,
  }));
  const spritzer = Array.from({ length: 12 }, () => {
    const a = rnd() * Math.PI * 2;
    const r = 0.55 + rnd() * 0.45;
    return { x: cx + Math.cos(a) * W * 0.42 * r, y: cy + Math.sin(a) * H * 0.3 * r, g: 2 + rnd() * 4 };
  });
  const form = (g: CanvasRenderingContext2D, dick: number) => {
    g.beginPath();
    const punkte = zacken.map((k, i) => {
      const a = (i / zacken.length) * Math.PI * 2;
      return [cx + Math.cos(a) * W * 0.3 * k * dick, cy + Math.sin(a) * H * 0.2 * k * dick];
    });
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
    g.fill();
    // Tropfnasen: laufen nach unten, unten ein runder Tropfen
    for (const t of tropfen) {
      g.fillRect(t.x - (t.b * dick) / 2, cy, t.b * dick, t.l);
      g.beginPath();
      g.arc(t.x, cy + t.l, t.b * dick * 0.85, 0, Math.PI * 2);
      g.fill();
    }
    for (const s of spritzer) {
      g.beginPath();
      g.arc(s.x, s.y, s.g * dick, 0, Math.PI * 2);
      g.fill();
    }
  };
  const neu = () => {
    const c = document.createElement("canvas");
    c.width = W;
    c.height = H;
    return [c, c.getContext("2d")!] as const;
  };
  const [bc, g] = neu();
  g.filter = "blur(1.5px)";
  g.fillStyle = "rgba(40,120,40,0.55)"; // dunkler Rand
  form(g, 1.06);
  g.fillStyle = "rgba(120,220,70,0.5)";
  form(g, 0.94);
  g.filter = "blur(3px)";
  g.fillStyle = "rgba(190,255,140,0.35)"; // heller Kern
  form(g, 0.55);
  g.filter = "none";
  // Bläschen und nasser Glanz
  for (let i = 0; i < 14; i++) {
    const x = cx + (rnd() - 0.5) * W * 0.45;
    const y = cy + (rnd() - 0.5) * H * 0.25;
    const r = 1 + rnd() * 2.5;
    g.strokeStyle = "rgba(230,255,210,0.6)";
    g.lineWidth = 1;
    g.beginPath();
    g.arc(x, y, r, 0, Math.PI * 2);
    g.stroke();
  }
  g.fillStyle = "rgba(255,255,255,0.75)";
  g.beginPath();
  g.ellipse(cx - W * 0.1, cy - H * 0.07, W * 0.07, H * 0.025, -0.3, 0, Math.PI * 2);
  g.fill();
  for (const t of tropfen) {
    g.fillStyle = "rgba(255,255,255,0.7)";
    g.fillRect(t.x - t.b * 0.35, cy + t.l - t.b * 0.6, 2, 2);
  }

  const [mc, m] = neu();
  m.fillStyle = "rgba(0,0,0,1)";
  form(m, 1.0);

  const ergebnis = { bild: bc.toDataURL(), maske: mc.toDataURL() };
  schleimCache.set(id, ergebnis);
  return ergebnis;
}

/**
 * Brandfleck vom Feuerniesen (Mark, 11.11.2026): sitzt am Display, nicht an
 * der Seite — bewegt sich deshalb nie. Weg nur durch Wischen: Finger/Maus
 * drauf und hin und her reiben, er wird dabei blasser.
 */
function Brandfleck({
  id,
  art,
  stil,
  weg,
  onSauber,
}: {
  id: string;
  /** `schleim`: feuchter Schmierfleck vom Tentakelmonster, `frost`: Raureif
   *  vom Eisdrachen — gleiche Wisch-Logik. */
  art: "brand" | "schleim" | "frost";
  stil: React.CSSProperties;
  weg: boolean;
  onSauber: () => void;
}) {
  const russ = useMemo(
    () => (art === "schleim" ? schleimBild(id) : art === "frost" ? frostBild(id) : russBild(id)),
    [id, art],
  );
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
      className={`pet-brand${art === "schleim" ? " pet-schleim" : art === "frost" ? " pet-frost" : ""}${weg ? " pet-haeufchen-weg" : ""}`}
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

/**
 * Zickzack eines Blitzes (Bärbel, 11.11.2026): Hauptstrahl vom Buch zum
 * Einschlag mit seitlichem Ausschlag (an den Enden schmal) und ein
 * Seitenast aus der Mitte. Liefert `points`-Strings für SVG-Polylinien.
 */
function blitzPfade(x0: number, y0: number, x1: number, y1: number, s: number): [string, string] {
  const dx = x1 - x0;
  const dy = y1 - y0;
  const l = Math.max(1, Math.hypot(dx, dy));
  const nx = -dy / l;
  const ny = dx / l;
  const n = Math.max(6, Math.round(l / 28));
  const punkte: [number, number][] = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    const aus = i === 0 || i === n ? 0 : (Math.random() - 0.5) * 2 * 16 * s * Math.sin(t * Math.PI);
    punkte.push([x0 + dx * t + nx * aus, y0 + dy * t + ny * aus]);
  }
  const k = Math.floor(n * (0.35 + Math.random() * 0.3));
  const [ax, ay] = punkte[k];
  const w = Math.atan2(dy, dx) + (Math.random() < 0.5 ? -1 : 1) * (0.5 + Math.random() * 0.5);
  const ast: [number, number][] = [[ax, ay]];
  let px = ax;
  let py = ay;
  for (let i = 0; i < 4; i++) {
    px += Math.cos(w) * 18 * s + (Math.random() - 0.5) * 10 * s;
    py += Math.sin(w) * 18 * s + (Math.random() - 0.5) * 10 * s;
    ast.push([px, py]);
  }
  const txt = (p: [number, number][]) => p.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  return [txt(punkte), txt(ast)];
}

interface Herz {
  id: number;
  x: number;
  y: number;
}

function PetFigur({
  pet,
  senden,
  wegmachen,
  lesung,
  onGelesen,
}: {
  pet: PetAufSchirm;
  senden: (n: object) => void;
  /** Spur verschwinden lassen (gefressen/eingesaugt). */
  wegmachen: (id: string) => void;
  lesung: Lesung | null;
  onGelesen: (id: string) => void;
}) {
  const wegmachenRef = useRef(wegmachen);
  wegmachenRef.current = wegmachen;
  // Was diese Figur gerade gepackt hält — beim Loslassen/Abbau wieder freigeben.
  const gehalten = useRef<string | null>(null);
  const figur = useRef<HTMLDivElement | null>(null);
  const zzz = useRef<HTMLSpanElement | null>(null);
  const tropfen = useRef<HTMLSpanElement | null>(null);
  const feuer = useRef<HTMLDivElement | null>(null);
  // Wolkenlauf: feste Anzahl Wolken-Elemente, pro Frame neu gesetzt.
  const wolkenEls = useRef<(HTMLDivElement | null)[]>([]);
  // Abgeschüttelter Ruß: ebenso ein fester Vorrat an Flocken.
  const flockenEls = useRef<(HTMLSpanElement | null)[]>([]);
  const puff = useRef<HTMLDivElement | null>(null);
  const effekt = useRef<HTMLDivElement | null>(null);
  const blitzSvg = useRef<SVGSVGElement | null>(null);
  const blitzLicht = useRef<HTMLDivElement | null>(null);
  // Großes Buch (Bärbel liest vor): Gestalt, solange es offen ist.
  const [buch, setBuch] = useState<number | null>(null);
  const buchAn = useRef(false);
  const spriteRect = useRef<BuchRechteck>({ left: 0, top: 0, w: 1, h: 1 });
  const lesungRef = useRef(lesung);
  lesungRef.current = lesung;
  const onGelesenRef = useRef(onGelesen);
  onGelesenRef.current = onGelesen;
  const [herzen, setHerzen] = useState<Herz[]>([]);
  const [klecks, setKlecks] = useState(false);
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
      else if (n.typ === "gelesen") {
        onGelesenRef.current(pet.id);
        senden({ typ: "gelesen", petId: pet.id });
      } else if (n.typ === "fressen") {
        // Bleibt im Maul/Buch stehen, bis die Spur abgeräumt ist.
        const zuletzt = gegriffen.get(n.id);
        if (zuletzt) gegriffen.set(n.id, { ...zuletzt, skala: 0.15 });
        if (gehalten.current === n.id) gehalten.current = null;
        window.setTimeout(() => gegriffen.delete(n.id), 900);
        wegmachenRef.current(n.id);
      } else senden({ typ: "haeufchen", petId: pet.id, x: n.x, y: n.y, art: n.art });
    };
    const b: PetSteuerung = fliegt
      ? new FlugBewegung(m, umgebung(m()), pet.seite, performance.now(), melden)
      : new PetBewegung(m, umgebung(m()), pet.seite, performance.now(), melden);
    bewegung.current = b;
    steuerungen.set(pet.id, b);

    let letzte = performance.now();
    let rahmen = 0;
    const tick = (jetzt: number) => {
      const dt = Math.min(0.1, (jetzt - letzte) / 1000);
      letzte = jetzt;
      if (lesungRef.current && b.lies && !b.liestGerade?.()) b.lies(jetzt);
      b.setzeUmgebung(umgebung(m()));
      b.tick(jetzt, dt);
      const d = b.darstellung(jetzt);

      const el = figur.current;
      if (el) {
        const s = skala();
        const z = d.zoom ?? 1;
        const anim = sp.animationen[d.animation] ?? { frames: 1, ms: 1000 };
        const frame = d.frame ?? Math.floor((jetzt - d.animStart) / anim.ms) % anim.frames;
        const bw = sp.breite * s * z;
        const bh = sp.hoehe * s * z;
        const left = d.left - (bw - sp.breite * s) / 2;
        const top = d.top - (bh - sp.hoehe * s) / 2;
        el.style.width = `${bw}px`;
        el.style.height = `${bh}px`;
        el.style.left = `${left}px`;
        el.style.top = `${top}px`;
        el.style.backgroundImage = `url(/pets/${pet.art}/${d.animation}.png)`;
        el.style.backgroundSize = `${anim.frames * sp.breite * s * z}px ${sp.hoehe * s * z}px`;
        el.style.backgroundPosition = `${-frame * sp.breite * s * z}px 0`;
        el.style.transform = d.transform;
        const mal = makel(pet.id, jetzt);
        el.dataset.makel = mal ?? "";
        if (istDrache(pet.art) && mal === "schleim") setKlecks(true);
        else if (istDrache(pet.art)) setKlecks(false);
        melde({ id: pet.id, art: pet.art, x: left + bw / 2, y: top + bh / 2, w: bw, h: bh });
        if (d.angriff) {
          for (const hit of treffe(d.angriff, pet.id, jetzt)) {
            // Blitz verrußt einen Drachen (Bärbels oder der des Blitzdrachen);
            // Bärbel kann nicht verrußen — sie erschrickt wie bei Feuer und Eis.
            const st = steuerungen.get(hit.id);
            if (hit.art === "blitz" && st?.verkohlen) st.verkohlen(jetzt);
            else if (hit.art !== "schleim") st?.erschrecken?.(jetzt);
          }
        }
        spriteRect.current = { left, top, w: bw, h: bh };
        const liest = !!d.liest;
        if (liest !== buchAn.current) {
          buchAn.current = liest;
          setBuch(liest ? (d.gestalt ?? 1) : null);
        }
        el.dataset.hockt = d.hockt ? "ja" : "nein";
        el.dataset.leuchtet = d.leuchten ? "ja" : "nein";
        // Effekt-Streifen, der die Figur selbst enthält (Tentakelmonster): Figur
        // unsichtbar, bleibt aber anfassbar.
        // Beim Vorlesen ebenso — das große Buch steht an ihrer Stelle.
        el.style.opacity = d.effekt?.ersetzt || d.liest ? "0" : "";
        el.style.pointerEvents = d.liest ? "none" : "";
        el.dataset.gepackt = d.gepackt ? "ja" : "nein";
      }
      // Verrußt (Bärbels Blitz), bis er sich schüttelt.
      if (figur.current) {
        const r = d.russ ?? 0;
        figur.current.style.filter =
          r > 0.01
            ? `brightness(${(1 - 0.68 * r).toFixed(3)}) sepia(${(0.55 * r).toFixed(3)}) contrast(${(1 + 0.45 * r).toFixed(3)}) saturate(${(1 - 0.65 * r).toFixed(3)})`
            : "";
      }
      const fl = d.flocken ?? [];
      if (fl.length || flockenEls.current.some((f) => f && f.style.display !== "none")) {
        const s = skala();
        flockenEls.current.forEach((fe, i) => {
          if (!fe) return;
          const f = fl[Math.max(0, fl.length - FLOCKEN_MAX) + i];
          if (!f) {
            fe.style.display = "none";
            return;
          }
          const t = (jetzt - f.t0) / 1000;
          // Wann sie unten aufkommt (Wurfparabel), danach liegt sie still.
          const tl = (-f.vy + Math.sqrt(f.vy * f.vy + 2 * FLOCKEN_G * Math.max(0, f.boden - f.y0))) / FLOCKEN_G;
          const tf = Math.min(t, tl);
          const k = 1.6; // Luftwiderstand seitlich
          const x = f.x0 + (f.vx * (1 - Math.exp(-k * tf))) / k;
          const y = Math.min(f.boden, f.y0 + f.vy * tf + 0.5 * FLOCKEN_G * tf * tf);
          const liegt = t - tl - FLOCKE_LIEGT_MS / 1000;
          const g = f.groesse * s;
          fe.style.display = "block";
          fe.style.width = `${g}px`;
          fe.style.height = `${g}px`;
          fe.style.left = `${x}px`;
          fe.style.top = `${y - g}px`;
          fe.style.opacity = liegt > 0 ? String(Math.max(0, 1 - liegt / 1.4)) : "1";
          fe.dataset.glut = f.glut && t < tl + 0.8 ? "ja" : "nein";
        });
      }
      const wl = d.wolken ?? [];
      if (wl.length || wolkenEls.current.some((w) => w && w.style.display !== "none")) {
        const s = skala();
        const wk = SPRITE.wolke;
        wolkenEls.current.forEach((we, i) => {
          if (!we) return;
          // Sind es einmal mehr als Elemente, zählen die neuesten.
          const w = wl[Math.max(0, wl.length - WOLKEN_MAX) + i];
          if (!w) {
            we.style.display = "none";
            return;
          }
          const bild = Math.min(wk.frames - 1, Math.floor((jetzt - w.t0) / wk.ms));
          we.style.display = "block";
          we.style.width = `${wk.breite * s}px`;
          we.style.height = `${wk.hoehe * s}px`;
          we.style.left = `${w.x - (wk.breite * s) / 2}px`;
          // Pfoten sinken ein wenig ein.
          we.style.top = `${w.y - wk.hoehe * s * 0.28}px`;
          we.style.backgroundSize = `${wk.frames * wk.breite * s}px ${wk.hoehe * s}px`;
          we.style.backgroundPosition = `${-bild * wk.breite * s}px 0`;
        });
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
      if (d.greift) {
        gegriffen.set(d.greift.id, { x: d.greift.x, y: d.greift.y, skala: d.greift.skala });
        gehalten.current = d.greift.id;
      } else if (gehalten.current) {
        gegriffen.delete(gehalten.current);
        gehalten.current = null;
      }
      const ef = effekt.current;
      if (ef) {
        const e = d.effekt ? BAERBEL.effekte[d.effekt.name] : undefined;
        if (d.effekt && e) {
          const s = skala();
          const bild = Math.min(e.frames - 1, Math.floor((jetzt - d.effekt.start) / e.ms));
          ef.style.display = "block";
          ef.style.backgroundImage = `url(/pets/${pet.art}/${d.effekt.name}.png)`;
          ef.style.width = `${e.breite * s}px`;
          ef.style.height = `${e.hoehe * s}px`;
          ef.style.left = `${d.left - e.rand * s}px`;
          ef.style.top = `${d.top - e.rand * s}px`;
          ef.style.backgroundSize = `${e.frames * e.breite * s}px ${e.hoehe * s}px`;
          ef.style.backgroundPosition = `${-bild * e.breite * s}px 0`;
          // Gleiche Drehung wie die Figur, um deren Mitte.
          ef.style.transformOrigin = `${(e.rand + BAERBEL.breite / 2) * s}px ${(e.rand + BAERBEL.hoehe / 2) * s}px`;
          ef.style.transform = d.transform;
        } else ef.style.display = "none";
      }
      const bs = blitzSvg.current;
      if (bs) {
        const liste = d.blitze ?? [];
        bs.style.display = liste.length ? "block" : "none";
        const gruppen = bs.querySelectorAll<SVGGElement>("g");
        gruppen.forEach((gr, i) => {
          const b = liste[i];
          if (!b) {
            gr.style.display = "none";
            gr.dataset.start = "";
            return;
          }
          gr.style.display = "";
          if (gr.dataset.start !== String(b.start)) {
            gr.dataset.start = String(b.start);
            gr.dataset.neu = "0";
            const licht = blitzLicht.current;
            if (licht) {
              licht.style.setProperty("--bx", `${b.x1}px`);
              licht.style.setProperty("--by", `${b.y1}px`);
              licht.style.display = "block";
              licht.style.animation = "none";
              void licht.offsetWidth; // Animation neu starten
              licht.style.animation = "";
            }
          }
          // Alle ~60 ms ein neuer Zickzack, dazwischen flackert er.
          if (jetzt >= Number(gr.dataset.neu || 0)) {
            gr.dataset.neu = String(jetzt + 60);
            const [haupt, ast] = blitzPfade(b.x0, b.y0, b.x1, b.y1, skala());
            gr.querySelectorAll<SVGPolylineElement>(".haupt").forEach((p) => p.setAttribute("points", haupt));
            gr.querySelectorAll<SVGPolylineElement>(".ast").forEach((p) => p.setAttribute("points", ast));
          }
          const t = jetzt - b.start;
          gr.style.opacity = t < 90 || (t > 160 && t < 330) || (t > 400 && t < 520) ? "1" : "0.25";
        });
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
      if (gehalten.current) gegriffen.delete(gehalten.current);
      steuerungen.delete(pet.id);
      vergiss(pet.id);
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
      {istDrache(pet.art) &&
        Array.from({ length: FLOCKEN_MAX }, (_, i) => (
          <span
            key={`f${i}`}
            ref={(el) => {
              flockenEls.current[i] = el;
            }}
            className="pet-russ"
            data-dunkel={i % 3 === 0 ? "ja" : "nein"}
            style={{ display: "none" }}
          />
        ))}
      {istDrache(pet.art) &&
        Array.from({ length: WOLKEN_MAX }, (_, i) => (
          <div
            key={`w${i}`}
            ref={(el) => {
              wolkenEls.current[i] = el;
            }}
            className="pet-feuer"
            style={{ display: "none", backgroundImage: "url(/pets/drache/wolke.png)" }}
          />
        ))}
      <div
        ref={figur}
        role="button"
        className="pet-figur"
        title={
          lesung
            ? `${pet.name} liest vor — antippen zum Zuklappen`
            : `${pet.name} (${pet.besitzerName}) — antippen: ${pet.art === "baerbel" ? "freuen" : "streicheln"}, ${PACKEN_MS / 1000} s halten: packen und werfen`
        }
        onPointerDown={runter}
        onPointerMove={bewegen}
        onPointerUp={hoch}
        onPointerCancel={abgebrochen}
        onContextMenu={(e) => e.preventDefault()}
      >
        {klecks && (
          <>
            <span className="pet-schleimklecks" style={{ left: "18%", top: "30%" }} />
            <span className="pet-schleimklecks" style={{ left: "48%", top: "42%", width: 36, height: 22 }} />
            <span className="pet-schleimklecks" style={{ left: "28%", top: "58%", width: 22, height: 14 }} />
          </>
        )}
      </div>
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
        <>
          <div ref={puff} className="pet-feuer" style={{ display: "none", backgroundImage: "url(/pets/baerbel/verwandeln.png)" }} />
          <div ref={effekt} className="pet-feuer" style={{ display: "none" }} />
          <div ref={blitzLicht} className="pet-blitz-licht" style={{ display: "none" }} onAnimationEnd={(e) => (e.currentTarget.style.display = "none")} />
          <svg ref={blitzSvg} className="pet-blitz" style={{ display: "none" }}>
            {[0, 1, 2].map((i) => (
              <g key={i} style={{ display: "none" }}>
                <polyline className="haupt" fill="none" stroke="rgba(150,110,255,0.45)" strokeWidth={18} strokeLinejoin="round" strokeLinecap="round" />
                <polyline className="ast" fill="none" stroke="rgba(150,110,255,0.4)" strokeWidth={8} strokeLinejoin="round" strokeLinecap="round" />
                <polyline className="haupt" fill="none" stroke="rgba(205,185,255,0.9)" strokeWidth={6} strokeLinejoin="round" strokeLinecap="round" />
                <polyline className="ast" fill="none" stroke="rgba(220,205,255,0.85)" strokeWidth={3} strokeLinejoin="round" strokeLinecap="round" />
                <polyline className="haupt" fill="none" stroke="#ffffff" strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round" />
              </g>
            ))}
          </svg>
        </>
      )}
      <span ref={tropfen} className="pet-tropfen" style={{ display: "none" }}>
        <i style={{ backgroundImage: `url(/pets/${pet.art}/tropfen.png)` }} />
        <i style={{ backgroundImage: `url(/pets/${pet.art}/tropfen.png)` }} />
      </span>
      {pet.art === "baerbel" && buch !== null && (
        <BaerbelBuch
          lesung={lesung}
          gestalt={buch}
          start={() => spriteRect.current}
          onFertig={() => {
            // Erst die Lesung vergessen, sonst schlägt sie im nächsten Frame
            // gleich wieder auf, bevor React neu gerendert hat.
            lesungRef.current = null;
            bewegung.current?.zuklappen?.(performance.now());
          }}
        />
      )}
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
