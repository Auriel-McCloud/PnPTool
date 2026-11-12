import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { Lesung } from "./api";
import "./baerbel-buch.css";

/**
 * Bärbel liest vor (Mark, 12.11.2026): „das Buch wird so groß und schlägt sich
 * auf, dass man den Text im Buch lesen kann — nicht auf der Seite in einer
 * Sprechblase.“ Schrift alt/elegant.
 *
 * Ablauf: die kleine Pixel-Bärbel schwebt zur Mitte, an ihrer Stelle wächst
 * dieses Buch zugeklappt auf volle Größe, der Deckel schwingt auf, der Vers
 * erscheint Wort für Wort wie Tinte. Antippen: Deckel zu, schrumpft zurück auf
 * die Pixel-Bärbel, die dann weiterfliegt.
 */

type Phase = "anflug" | "oeffnen" | "offen" | "schliessen" | "abflug";

export interface Rechteck {
  left: number;
  top: number;
  w: number;
  h: number;
}

const ANFLUG_MS = 900;
const KLAPPEN_MS = 1500;
const ZU_MS = 1100;
const ABFLUG_MS = 650;
const WORT_MS = 45;

/** Kurzer Vers: links Stelle + Zierde, rechts der Vers. Langer: aufgeteilt. */
const KURZ = 120;

function teilen(text: string): [string | null, string] {
  if (text.length < KURZ) return [null, text];
  const mitte = text.length / 2;
  let besteStelle = -1;
  let besterAbstand = Infinity;
  // Am liebsten nach einem Satzzeichen trennen, sonst am Wort nahe der Mitte.
  for (let i = Math.floor(text.length * 0.3); i < text.length * 0.7; i++) {
    if (/[,;:.!?]/.test(text[i]) && text[i + 1] === " ") {
      const a = Math.abs(i - mitte);
      if (a < besterAbstand) {
        besterAbstand = a;
        besteStelle = i + 1;
      }
    }
  }
  if (besteStelle < 0) {
    for (let i = 0; i < text.length; i++) {
      if (text[i] === " " && Math.abs(i - mitte) < besterAbstand) {
        besterAbstand = Math.abs(i - mitte);
        besteStelle = i;
      }
    }
  }
  if (besteStelle < 0) return [null, text];
  return [text.slice(0, besteStelle).trim(), text.slice(besteStelle).trim()];
}

/** Wörter einzeln, damit sie nacheinander wie Tinte auftauchen. */
function Tinte({ text, ab, initiale }: { text: string; ab: number; initiale: boolean }) {
  const woerter = text.split(/\s+/).filter(Boolean);
  return (
    <p className="bb-vers">
      {woerter.map((w, i) => {
        const stil = { animationDelay: `${(ab + i) * WORT_MS}ms` };
        if (i === 0 && initiale) {
          return (
            <span key={i} className="bb-wort" style={stil}>
              <span className="bb-initiale">{w[0]}</span>
              {w.slice(1)}{" "}
            </span>
          );
        }
        return (
          <span key={i} className="bb-wort" style={stil}>
            {w}{" "}
          </span>
        );
      })}
    </p>
  );
}

function Zierde({ gestalt }: { gestalt: number }) {
  if (gestalt === 2) {
    return (
      <svg className="bb-zier" viewBox="0 0 100 60" aria-hidden>
        <path d="M6 30 Q50 -4 94 30 Q50 64 6 30 Z" fill="none" stroke="currentColor" strokeWidth="3" />
        <circle cx="50" cy="30" r="13" fill="currentColor" opacity="0.85" />
        <circle cx="50" cy="30" r="5" fill="var(--bb-leder-dunkel)" />
        <circle cx="54" cy="26" r="2.4" fill="#fff" opacity="0.8" />
        {[-30, -15, 0, 15, 30].map((x) => (
          <line key={x} x1={50 + x} y1={x === 0 ? 6 : 10} x2={50 + x * 1.15} y2={x === 0 ? -2 : 3} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
        ))}
      </svg>
    );
  }
  if (gestalt === 3) {
    return (
      <svg className="bb-zier bb-zier-gesicht" viewBox="0 0 100 70" aria-hidden>
        <path d="M50 2 L54 12 L64 13 L56 19 L59 29 L50 23 L41 29 L44 19 L36 13 L46 12 Z" fill="currentColor" />
        <g className="bb-auge">
          <circle cx="32" cy="46" r="11" fill="#fff8e8" />
          <circle cx="34" cy="47" r="6.5" fill="#2a1408" />
          <circle cx="36.5" cy="44" r="2.3" fill="#fff" />
        </g>
        <g className="bb-auge">
          <circle cx="68" cy="46" r="11" fill="#fff8e8" />
          <circle cx="70" cy="47" r="6.5" fill="#2a1408" />
          <circle cx="72.5" cy="44" r="2.3" fill="#fff" />
        </g>
        <path d="M44 63 Q50 68 56 63" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg className="bb-zier" viewBox="0 0 60 80" aria-hidden>
      <path
        d="M25 4 H35 V24 H55 V34 H35 V76 H25 V34 H5 V24 H25 Z"
        fill="currentColor"
        stroke="var(--bb-gold-dunkel)"
        strokeWidth="1.5"
      />
    </svg>
  );
}

function Schnoerkel() {
  return (
    <svg className="bb-schnoerkel" viewBox="0 0 200 20" aria-hidden>
      <path
        d="M4 10 H80 M120 10 H196 M80 10 C88 2, 96 2, 100 10 C104 18, 112 18, 120 10 M100 10 m-3 0 a3 3 0 1 0 6 0 a3 3 0 1 0 -6 0"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function BaerbelBuch({
  lesung,
  gestalt,
  start,
  onFertig,
}: {
  /** null = von außen erledigt → zuklappen. */
  lesung: Lesung | null;
  /** 1 klassisch, 2 Grimoire, 3 Gesicht — wie die Pixel-Bärbel gerade aussieht. */
  gestalt: number;
  /** Wo die kleine Bärbel gerade auf dem Bildschirm ist. */
  start: () => Rechteck;
  /** Wieder klein — die Pixel-Bärbel übernimmt. */
  onFertig: () => void;
}) {
  // Text beim Aufschlagen festhalten, damit er beim Zuklappen nicht verschwindet.
  const [text] = useState(lesung);
  const [phase, setPhase] = useState<Phase>("anflug");
  const flug = useRef<HTMLDivElement | null>(null);
  const buch = useRef<HTMLDivElement | null>(null);
  const onFertigRef = useRef(onFertig);
  onFertigRef.current = onFertig;
  const timer = useRef<number[]>([]);

  const spaeter = (fn: () => void, ms: number) => {
    timer.current.push(window.setTimeout(fn, ms));
  };

  /** Transform, mit dem das zugeklappte Buch genau auf der Pixel-Bärbel liegt. */
  const klein = (): string => {
    const f = flug.current;
    const b = buch.current;
    if (!f || !b) return "scale(0.1)";
    const r = f.getBoundingClientRect();
    const s0 = start();
    const deckelB = b.offsetWidth / 2;
    const deckelH = b.offsetHeight;
    const s = Math.max(0.05, Math.min(s0.w / deckelB, s0.h / deckelH) * 1.05);
    const dx = s0.left + s0.w / 2 - (r.left + r.width / 2);
    const dy = s0.top + s0.h / 2 - (r.top + r.height / 2);
    return `translate(${dx}px, ${dy}px) scale(${s})`;
  };

  // Schrift so verkleinern, dass der Vers auf die Seiten passt — nochmal,
  // sobald die alte Schrift geladen ist (vorher misst der Ersatzfont).
  useLayoutEffect(() => {
    // Kurze Verse dürfen groß werden, lange werden kleiner — so groß, wie
    // gerade noch auf die Seiten passt.
    const einpassen = () => {
      const b = buch.current;
      if (!b) return;
      const passt = (f: number) => {
        b.style.setProperty("--bb-schrift", f.toFixed(3));
        return Array.from(b.querySelectorAll<HTMLElement>(".bb-papier")).every((p) => p.scrollHeight <= p.clientHeight + 1);
      };
      let lo = 0.55;
      let hi = 1.5;
      if (passt(hi)) return;
      for (let i = 0; i < 8; i++) {
        const mitte = (lo + hi) / 2;
        if (passt(mitte)) lo = mitte;
        else hi = mitte;
      }
      passt(lo * 0.97);
    };
    einpassen();
    let weg = false;
    Promise.all([
      document.fonts.load('20px "IM Fell English"'),
      document.fonts.load('20px "UnifrakturMaguntia"'),
    ])
      .then(() => !weg && einpassen())
      .catch(() => undefined);
    window.addEventListener("resize", einpassen);
    return () => {
      weg = true;
      window.removeEventListener("resize", einpassen);
    };
  }, []);

  // Anflug: zugeklappt von der Pixel-Bärbel auf volle Größe.
  useLayoutEffect(() => {
    if (!text) {
      onFertigRef.current();
      return;
    }
    const f = flug.current;
    if (!f) return;
    const a = f.animate(
      [
        { transform: klein(), opacity: 0.2 },
        { opacity: 1, offset: 0.15 },
        { transform: "none", opacity: 1 },
      ],
      { duration: ANFLUG_MS, easing: "cubic-bezier(.2,.75,.25,1)" },
    );
    a.onfinish = () => {
      setPhase("oeffnen");
      spaeter(() => setPhase("offen"), KLAPPEN_MS);
    };
    const t = timer.current;
    return () => {
      a.cancel();
      t.forEach((id) => window.clearTimeout(id));
    };
    // Einmal beim Aufschlagen.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const zuklappen = () => {
    if (phase !== "offen") return;
    setPhase("schliessen");
    spaeter(() => {
      setPhase("abflug");
      const f = flug.current;
      if (!f) {
        onFertigRef.current();
        return;
      }
      const a = f.animate(
        [
          { transform: "none", opacity: 1 },
          { opacity: 1, offset: 0.85 },
          { transform: klein(), opacity: 0.2 },
        ],
        { duration: ABFLUG_MS, easing: "cubic-bezier(.5,0,.75,.4)", fill: "forwards" },
      );
      a.onfinish = () => onFertigRef.current();
    }, ZU_MS);
  };

  // Woanders als gelesen markiert → von selbst zuklappen.
  useEffect(() => {
    if (!lesung && phase === "offen") zuklappen();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lesung, phase]);

  if (!text) return null;
  const [links, rechts] = teilen(text.zitat);
  const offen = phase === "oeffnen" || phase === "offen";
  const linksWoerter = links ? links.split(/\s+/).filter(Boolean).length : 0;
  // Erst schreiben, wenn der Deckel schon halb offen ist.
  const tinteAb = Math.round((KLAPPEN_MS * 0.55) / WORT_MS);

  return (
    <div className="bb-buehne" lang="de">
      <div ref={flug} className="bb-flug">
        <div className="bb-lage" data-offen={offen ? "ja" : "nein"}>
          <div
            ref={buch}
            className="bb-buch"
            data-gestalt={gestalt}
            data-phase={phase}
            role="button"
            tabIndex={0}
            title="Antippen zum Zuklappen"
            onPointerDown={(e) => {
              e.stopPropagation();
              zuklappen();
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " " || e.key === "Escape") zuklappen();
            }}
          >
            <div className="bb-hinten">
              <div className={`bb-papier bb-rechts${links === null ? " bb-mittig" : ""}`}>
                {links === null ? (
                  <Tinte text={rechts} ab={tinteAb} initiale />
                ) : (
                  <Tinte text={rechts} ab={tinteAb + linksWoerter} initiale={false} />
                )}
                <span className="bb-hinweis">antippen zum Zuklappen</span>
              </div>
            </div>
            <div className="bb-deckel">
              <div className="bb-vorne">
                <div className="bb-rahmen">
                  <span className="bb-titel">Bärbel</span>
                  <Zierde gestalt={gestalt} />
                </div>
              </div>
              <div className="bb-innen">
                <div className="bb-papier bb-links">
                  <h2 className="bb-stelle">{text.stelle}</h2>
                  <Schnoerkel />
                  {links === null ? (
                    <div className="bb-schmuck">
                      <Zierde gestalt={gestalt} />
                    </div>
                  ) : (
                    <Tinte text={links} ab={tinteAb} initiale />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
