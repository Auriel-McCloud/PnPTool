import { useEffect, useRef, useState, type ReactNode } from "react";
import "./commlink.css";

export interface Bereich {
  id: string;
  name: string;
  symbol: string;
  /**
   * Leitfarbe des Bereichs. Färbt Symbol, Übergangsbewegung und die
   * Neonröhren der Ansicht — so hat jeder Bereich einen eigenen Ton und man
   * erkennt am Licht, wo man ist.
   */
  farbe: string;
  /** Noch nicht gebaut: erscheint ausgegraut mit "bald"-Markierung. */
  bald?: boolean;
}

/** Dauer des Bereichswechsels; muss zu den Zeiten in commlink.css passen. */
const FLUG_MS = 420;
/** Dauer des herabfahrenden Balkens, ebenfalls aus commlink.css. */
const BALKEN_MS = 500;

/**
 * Die Hülle des Commlinks: Symbolspalte links, Werkzeugleiste oben.
 *
 * Bewusst inhaltsfrei — sie weiß nichts über Kampagnen, Personen oder
 * Gegenstände. Dieselbe Hülle soll später die Spieler-Ansicht tragen, nur
 * mit weniger Bereichen (siehe docs/ui-konzept.md).
 *
 * Der Bereichswechsel ist inszeniert: der angetippte Name löst sich aus dem
 * Menü, fliegt nach oben und wird zur Überschrift, während ein Balken
 * herabfährt und die neue Seite freilegt.
 */
export function CommlinkShell({
  bereiche,
  aktiv,
  onBereichWechsel,
  titel,
  werkzeuge,
  fuss,
  children,
}: {
  bereiche: Bereich[];
  aktiv: string;
  onBereichWechsel: (id: string) => void;
  titel: string;
  werkzeuge?: ReactNode;
  fuss?: ReactNode;
  children: ReactNode;
}) {
  // Kennung des einen Eintrags, der aus der Symbolspalte herausgefahren ist
  // und seinen Namen zeigt (null = keiner). Bewusst nur einer: das ganze
  // Menue auszufahren verdeckt den Inhalt und beantwortet die eigentliche
  // Frage nicht, naemlich was das gerade angetippte Zeichen bedeutet.
  const [vor, setVor] = useState<string | null>(null);
  const [schubladeOffen, setSchubladeOffen] = useState(false);
  // Kennung des laufenden Balkens (null = keiner). Als key verwendet, damit
  // die Animation bei jedem Wechsel neu startet, und danach wieder auf null
  // gesetzt — sonst bliebe das Element über dem Inhalt liegen.
  const [balken, setBalken] = useState<number | null>(null);
  const [flug, setFlug] = useState<{ text: string; farbe: string; von: DOMRect; ziel: DOMRect } | null>(null);
  const [flugLaeuft, setFlugLaeuft] = useState(false);

  const titelRef = useRef<HTMLSpanElement>(null);
  const timer = useRef<number[]>([]);

  useEffect(() => () => timer.current.forEach(clearTimeout), []);

  function waehle(b: Bereich, event: React.MouseEvent<HTMLButtonElement>) {
    // In der eingefahrenen Symbolspalte sieht man nur Zeichen, keine Namen.
    // Ein Klick fährt deshalb zuerst aus, damit man lesen kann, was man
    // wählt — gewechselt wird erst mit dem zweiten Tippen. In der Schublade
    // am Handy stehen die Namen ohnehin, dort geht es direkt.
    const istRail = window.matchMedia("(min-width: 600px)").matches;
    if (istRail && vor !== b.id) {
      setVor(b.id);
      return;
    }

    setVor(null);
    setSchubladeOffen(false);

    if (b.id === aktiv) return;

    const sanft = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const nameEl = event.currentTarget.querySelector(".cl-bereich-name");
    const zielEl = titelRef.current;

    if (sanft || !nameEl || !zielEl) {
      onBereichWechsel(b.id);
      return;
    }

    // Start- und Zielposition vor dem Umschalten messen
    setFlug({
      text: b.name,
      farbe: b.farbe,
      von: nameEl.getBoundingClientRect(),
      ziel: zielEl.getBoundingClientRect(),
    });

    // Erst im nächsten Bild die Zielkoordinaten setzen, sonst gibt es keinen
    // Übergang — der Browser sähe nur den Endzustand.
    requestAnimationFrame(() => setFlugLaeuft(true));

    timer.current.push(
      // Auf halbem Weg wechselt der Inhalt, verdeckt vom herabfahrenden Balken
      window.setTimeout(() => {
        onBereichWechsel(b.id);
        setBalken(Date.now());
      }, FLUG_MS * 0.55),
      window.setTimeout(() => {
        setFlug(null);
        setFlugLaeuft(false);
      }, FLUG_MS),
      // Balken wieder aus dem Baum nehmen, sobald er durchgelaufen ist
      window.setTimeout(() => setBalken(null), FLUG_MS * 0.55 + BALKEN_MS),
    );
  }

  const aktiverBereich = bereiche.find((b) => b.id === aktiv);

  return (
    // --bereich-farbe färbt Balken, aktives Symbol und die Neonröhren der
    // Ansicht — dadurch hat jeder Bereich seinen eigenen Ton.
    <div
      className="cl-shell"
      style={{ "--bereich-farbe": aktiverBereich?.farbe ?? "var(--neon)" } as React.CSSProperties}
    >
      <div className="cl-abdunkelung" data-offen={schubladeOffen} onClick={() => setSchubladeOffen(false)} />

      <div className="cl-menue" data-offen={schubladeOffen}>
        <nav className="cl-menue-tafel">
          <div className="cl-marke">
            <span className="cl-marke-zeichen" aria-hidden="true">
              ⌬
            </span>
            <span>
              <span className="cl-marke-name">Commlink</span>
              <span className="cl-marke-zeile">NeotopiA // v0.1</span>
            </span>
          </div>

          <div className="cl-bereiche">
            {bereiche.map((b, i) => {
              const ersterBald = b.bald && !bereiche[i - 1]?.bald;
              return (
                <div key={b.id}>
                  {ersterBald && <div className="cl-gruppe">In Arbeit</div>}
                  <button
                    type="button"
                    className="cl-bereich"
                    aria-current={b.id === aktiv ? "page" : undefined}
                    data-vor={vor === b.id ? "true" : undefined}
                    disabled={b.bald}
                    title={b.name}
                    onClick={(e) => waehle(b, e)}
                    /* --ton färbt Rahmen und Schein des vorgefahrenen Eintrags
                       in genau der Farbe, die anschließend nach oben fliegt. */
                    style={{ "--ton": b.farbe } as React.CSSProperties}
                  >
                    <span
                      className="cl-bereich-symbol"
                      aria-hidden="true"
                      style={b.bald ? undefined : { color: b.farbe }}
                    >
                      {b.symbol}
                    </span>
                    <span className="cl-bereich-name">{b.name}</span>
                    {b.bald && <span className="cl-bereich-bald">bald</span>}
                  </button>
                </div>
              );
            })}
          </div>

          {fuss && <div className="cl-menue-fuss">{fuss}</div>}
        </nav>
      </div>

      <div className="cl-haupt">
        <header className="cl-leiste">
          <button
            type="button"
            className="cl-menue-schalter"
            onClick={() => setSchubladeOffen((o) => !o)}
            aria-label="Bereiche"
          >
            ☰
          </button>
          <span className="cl-leiste-titel" ref={titelRef}>
            {titel}
          </span>
          {werkzeuge && <div className="cl-leiste-werkzeuge">{werkzeuge}</div>}
        </header>

        <main className="cl-inhalt" style={{ position: "relative" }}>
          {/* key: baut die Ansicht bei jedem Bereichswechsel neu auf */}
          <div className="cl-ansicht" key={aktiv}>
            {children}
          </div>
          {balken !== null && <div className="cl-balken" key={balken} aria-hidden="true" />}
        </main>
      </div>

      {flug && (
        <span
          className="cl-flug"
          aria-hidden="true"
          style={{
            left: flugLaeuft ? flug.ziel.left : flug.von.left,
            top: flugLaeuft ? flug.ziel.top : flug.von.top,
            opacity: flugLaeuft ? 0 : 1,
            color: flug.farbe,
            textShadow: `0 0 16px ${flug.farbe}`,
          }}
        >
          {flug.text}
        </span>
      )}

      <Stoerung />
    </div>
  );
}

/**
 * Seltenes Neonflackern (alle 5–10 Minuten, zufällig).
 *
 * Absichtlich selten: als Dauereffekt wäre es Belästigung statt Atmosphäre.
 * Wer Bewegung im System abgestellt hat, bekommt es gar nicht — Geflacker
 * ist für lichtempfindliche Menschen keine Stimmung, sondern ein Problem.
 */
function Stoerung() {
  const [aktiv, setAktiv] = useState(false);
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const planen = () => {
      const minuten = 5 + Math.random() * 5;
      timer.current = window.setTimeout(() => {
        setAktiv(true);
        window.setTimeout(() => setAktiv(false), 500);
        planen();
      }, minuten * 60_000);
    };

    planen();
    return () => window.clearTimeout(timer.current);
  }, []);

  return <div className="cl-stoerung" data-aktiv={aktiv} aria-hidden="true" />;
}
