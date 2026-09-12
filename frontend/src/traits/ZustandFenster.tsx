import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { Kaestchen, type Schadensart } from "./Kaestchen";
import "./zustandfenster.css";

/**
 * Die Vollansicht einer Zustandsleiste: alle Kästchen, Zahlenpad, Heilen.
 *
 * Warum überhaupt ein Fenster: sobald eine Leiste über zehn Kästchen geht,
 * wird sie in der Übersicht zur Leiste (siehe `Kaestchen.tsx`) — die
 * einzelnen Zellen sind dann zu schmal zum Treffen. Hier stehen sie wieder
 * groß und einzeln, und zusätzlich lässt sich Schaden **als Zahl** eintragen
 * statt fünfmal zu tippen.
 *
 * **Eigenes Zahlenpad statt Systemtastatur** (Marks Vorgabe): die
 * Bildschirmtastatur frisst am Tablet den halben Schirm und schiebt das
 * Fenster weg — dasselbe Problem, das im Messenger schon notiert ist. Ein
 * Pad im Fenster hat zudem Knöpfe in Daumengröße, was am Spieltisch mehr
 * wert ist als Tippkomfort.
 */

const ARTEN: { wert: Schadensart; label: string }[] = [
  { wert: "schlag", label: "Schlag" },
  { wert: "schwer", label: "Tödlich" },
  { wert: "aggraviert", label: "Unheilbar" },
];

/** Wie Schaden verschwindet — die Auskunft, die man beim Heilen braucht. */
const HEILHINWEIS =
  "Geheilt wird immer der leichteste Schaden zuerst: Schlagschaden geht nach einer Ruhepause " +
  "von selbst weg, tödlicher braucht Pflege oder eine Klinik, unheilbarer nur Magie oder Bioware.";

export interface ZustandWerte {
  /** Nach Art getrennt (Gesundheit) — hat Vorrang vor `verbraucht`. */
  schaden?: { schlag: number; schwer: number; aggraviert: number };
  /** Einfacher Verbrauch ohne Arten (Willenskraft, I.C.E.). */
  verbraucht?: number;
}

export function ZustandFenster({
  offen,
  titel,
  max,
  ton,
  werte,
  heilenErlaubt = true,
  heilenGesperrtHinweis,
  onSchliessen,
  onSchaden,
  onHeilen,
  onKaestchenKlick,
}: {
  offen: boolean;
  titel: string;
  max: number;
  ton: string;
  werte: ZustandWerte;
  /**
   * Willenskraft darf der Spieler ausgeben, aber nicht zurückholen (Regel
   * aus bogen.py::zustand_verboten) — dann soll der Knopf gar nicht erst
   * dastehen statt am Server abzuprallen.
   */
  heilenErlaubt?: boolean;
  heilenGesperrtHinweis?: string;
  onSchliessen: () => void;
  /** Menge und Art; bei Leisten ohne Arten ist `art` undefined. */
  onSchaden: (menge: number, art?: Schadensart) => Promise<void> | void;
  onHeilen: (menge: number) => Promise<void> | void;
  /** Einzelnes Kästchen antippen — wie bisher Schadensart weiterschalten. */
  onKaestchenKlick?: (index: number) => void;
}) {
  const nachArt = werte.schaden !== undefined;
  const [eingabe, setEingabe] = useState("");
  const [art, setArt] = useState<Schadensart>("schlag");
  const [laeuft, setLaeuft] = useState(false);

  // Bei jedem Öffnen frisch: eine stehengebliebene 6 vom letzten Mal wäre
  // im Eifer des Gefechts schnell versehentlich eingetragen.
  useEffect(() => {
    if (offen) {
      setEingabe("");
      setArt("schlag");
    }
  }, [offen]);

  const menge = Number(eingabe) || 0;
  const belegt = werte.schaden
    ? werte.schaden.schlag + werte.schaden.schwer + werte.schaden.aggraviert
    : werte.verbraucht ?? 0;

  async function fuehreAus(tun: () => Promise<void> | void) {
    setLaeuft(true);
    try {
      await tun();
      setEingabe("");
    } finally {
      setLaeuft(false);
    }
  }

  function ziffer(z: string) {
    // Zweistellig reicht: mehr Kästchen hat keine Leiste.
    setEingabe((alt) => (alt.length >= 2 ? alt : (alt + z).replace(/^0+(?=\d)/, "")));
  }

  return (
    <Fenster
      offen={offen}
      titel={titel}
      unterzeile={`${max - belegt} von ${max} frei`}
      kennung={`zustand:${titel}`}
      ton={ton}
      onSchliessen={onSchliessen}
    >
      <div className="zf-inhalt" style={{ "--zf-ton": ton } as React.CSSProperties}>
        {/* Alle Kästchen groß — hier wird gezählt und, wer mag, einzeln
            abgehakt wie auf dem Papierblatt. */}
        <div className="zf-alle">
          <Kaestchen
            max={max}
            gesamt={max}
            einzeln
            ton={ton}
            schaden={werte.schaden}
            verbraucht={werte.verbraucht}
            onKlick={onKaestchenKlick}
          />
        </div>

        {/* Der häufigste Fall am Tisch sind ein bis drei Punkte — dafür soll
            niemand ein Zahlenpad bedienen müssen. */}
        <div className="zf-schnell">
          {[1, 2, 3].map((n) => (
            <button key={n} type="button" disabled={laeuft} onClick={() => fuehreAus(() => onSchaden(n, nachArt ? art : undefined))}>
              − {n}
            </button>
          ))}
          {heilenErlaubt && (
            <button type="button" className="zf-heilknopf" disabled={laeuft} onClick={() => fuehreAus(() => onHeilen(1))}>
              + 1
            </button>
          )}
        </div>

        <div className="zf-padzeile">
          <div className="zf-pad">
            {["7", "8", "9", "4", "5", "6", "1", "2", "3"].map((z) => (
              <button key={z} type="button" onClick={() => ziffer(z)}>
                {z}
              </button>
            ))}
            <button type="button" onClick={() => ziffer("0")}>
              0
            </button>
            <button type="button" onClick={() => setEingabe((a) => a.slice(0, -1))}>
              ⌫
            </button>
            <button type="button" onClick={() => setEingabe("")}>
              C
            </button>
          </div>
          <div className="zf-anzeige" aria-live="polite">
            {eingabe || "0"}
          </div>
        </div>

        {nachArt && (
          <div className="zf-arten">
            {ARTEN.map((a) => (
              <button
                key={a.wert}
                type="button"
                data-aktiv={art === a.wert ? "true" : undefined}
                onClick={() => setArt(a.wert)}
              >
                {a.label}
              </button>
            ))}
          </div>
        )}

        <div className="zf-tun">
          <button
            type="button"
            className="zf-schaden"
            disabled={laeuft || menge <= 0}
            onClick={() => fuehreAus(() => onSchaden(menge, nachArt ? art : undefined))}
          >
            Schaden eintragen
          </button>
          {heilenErlaubt && (
            <button
              type="button"
              className="zf-heilen"
              disabled={laeuft || menge <= 0}
              onClick={() => fuehreAus(() => onHeilen(menge))}
            >
              Heilen
            </button>
          )}
        </div>

        {heilenErlaubt ? (
          nachArt && <p className="zf-hinweis">{HEILHINWEIS}</p>
        ) : (
          <p className="zf-hinweis">{heilenGesperrtHinweis}</p>
        )}
      </div>
    </Fenster>
  );
}
