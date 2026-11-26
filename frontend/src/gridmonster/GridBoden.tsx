import { useEffect, useRef, useState } from "react";
import { DING_ARTEN, DINGE, DingBild, dingBreite, type DingArt } from "./GridDinge";
import "./gridmonster.css";

/**
 * 3D-Gitterboden der GridMonster-Optik (Mark, 26.11.2026): ein Gitter in
 * Perspektive, das zum Horizont hin ins Endlose läuft. Es steht still und
 * fährt nur kurz auf den Betrachter zu, wenn sich `fahrt` ändert (jeder
 * Menüwechsel, im Takt mit dem Ankommen der neuen Ansicht) — Mark: „er
 * läuft immer nur für ein paar Sekunden, wenn man in einen anderen
 * Menüpunkt geht“. Dauerbewegung würde am Spielabend nerven.
 *
 * Fundstücke (Mark, 26.11.2026): ab und zu steht zufällig ein Elektronik-
 * Ding aufrecht in einem Gitterfeld — nach dem Ankommen mit einer Chance,
 * oder irgendwann, während man in einem Menü bleibt. Nicht an einen
 * Menüpunkt gebunden. Beim nächsten Wechsel fährt es mit dem Boden davon.
 *
 * Aufbau: .gm-boden ist die gekippte Ebene (preserve-3d, darum OHNE Maske —
 * eine Maske würde die Kinder flach in die Ebene drücken). Das Gitter ist
 * ein eigenes Kind mit Maske und Fahrt-Animation (per `key` bei jedem
 * Wechsel neu gestartet). Ein Fundstück ist ein Punkt auf der Ebene
 * (.gm-fund, fährt beim Wechsel mit) mit flachem Bodenschatten und dem per
 * rotateX zurückgekippten, aufrecht stehenden Bild. Liegt mit z-index -1 hinter allem, nimmt
 * keine Klicks an; `prefers-reduced-motion` stoppt die Bewegung (CSS).
 */

/** Zellgröße des Gitters in px — muss zu background-size in gridmonster.css passen. */
const ZELLE = 64;
/** Dauer anfahren + ausrollen (gm-anfahren/gm-ausrollen). */
const ANKUNFT_MS = 340 + 1200;
/** Dauer, bis ein wegfahrendes Ding aus dem Bild ist (= gm-anfahren). */
const WEG_MS = 340;
/** Chance auf ein Fundstück nach dem Ankommen in einem Menü. */
const CHANCE_NACH_ANKUNFT = 0.3;
/** In der Ruhe: alle 45–120 s eine Chance auf ein (weiteres) Fundstück. */
const RUHE_MIN_MS = 45_000;
const RUHE_MAX_MS = 120_000;
const CHANCE_IN_RUHE = 0.5;
/** Nie mehr als so viele gleichzeitig — es soll selten und besonders bleiben. */
const HOECHSTENS = 2;
/**
 * Reihen (Abstand vom Horizont in Zellen) und wie weit seitlich je Reihe —
 * weiter vorn wirkt die Perspektive stärker, dort nur nahe der Mitte.
 */
const REIHEN: { reihe: number; seitlich: number }[] = [
  { reihe: 1, seitlich: 5 },
  { reihe: 2, seitlich: 3 },
];

interface Ding {
  id: number;
  art: DingArt;
  spalte: number;
  reihe: number;
  geht: boolean;
}

let naechsteId = 1;

function neuesDing(vorhanden: Ding[]): Ding | null {
  for (let versuch = 0; versuch < 8; versuch++) {
    const r = REIHEN[Math.floor(Math.random() * REIHEN.length)];
    const spalte = Math.floor(Math.random() * (2 * r.seitlich + 1)) - r.seitlich;
    if (vorhanden.some((d) => !d.geht && d.reihe === r.reihe && d.spalte === spalte)) continue;
    const art = DING_ARTEN[Math.floor(Math.random() * DING_ARTEN.length)];
    return { id: naechsteId++, art, spalte, reihe: r.reihe, geht: false };
  }
  return null;
}

function hinzufuegen(alt: Ding[]): Ding[] {
  if (alt.filter((d) => !d.geht).length >= HOECHSTENS) return alt;
  const neu = neuesDing(alt);
  return neu ? [...alt, neu] : alt;
}

export function GridBoden({ fahrt }: { fahrt: string }) {
  const [dinge, setDinge] = useState<Ding[]>([]);
  const ruheTimer = useRef<number | undefined>(undefined);

  // Jede Fahrt: vorhandene Dinge fahren mit davon, nach dem Ankommen evtl. ein neues.
  useEffect(() => {
    setDinge((alt) => alt.map((d) => ({ ...d, geht: true })));
    const weg = window.setTimeout(() => setDinge((alt) => alt.filter((d) => !d.geht)), WEG_MS + 60);
    const neu = window.setTimeout(() => {
      if (Math.random() < CHANCE_NACH_ANKUNFT) setDinge(hinzufuegen);
    }, ANKUNFT_MS);
    return () => {
      window.clearTimeout(weg);
      window.clearTimeout(neu);
    };
  }, [fahrt]);

  // In der Ruhe taucht ab und zu etwas auf, ganz unabhängig vom Menü.
  useEffect(() => {
    const planen = () => {
      const ms = RUHE_MIN_MS + Math.random() * (RUHE_MAX_MS - RUHE_MIN_MS);
      ruheTimer.current = window.setTimeout(() => {
        if (Math.random() < CHANCE_IN_RUHE) setDinge(hinzufuegen);
        planen();
      }, ms);
    };
    planen();
    return () => window.clearTimeout(ruheTimer.current);
  }, []);

  return (
    <div className="gm-horizont" aria-hidden="true">
      <div className="gm-boden">
        <div className="gm-gitter" key={fahrt} />
        {dinge.map((d) => (
          <div
            key={d.id}
            className="gm-fund"
            data-geht={d.geht ? "true" : undefined}
            style={
              {
                // Zellmitte seitlich, Fußpunkt kurz vor der vorderen Zelllinie
                left: `calc(50% + ${d.spalte * ZELLE}px)`,
                top: `${d.reihe * ZELLE + ZELLE * 0.8}px`,
                "--b": `${dingBreite(d.art)}px`,
                "--h": `${DINGE[d.art].hoehe}px`,
              } as React.CSSProperties
            }
          >
            <div className="gm-ding-schatten" />
            <div className="gm-ding" title={DINGE[d.art].name}>
              <DingBild art={d.art} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
