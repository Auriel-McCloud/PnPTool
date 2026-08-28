import { useEffect, useRef, useState, type ReactNode } from "react";
import "./commlink.css";

export interface Bereich {
  id: string;
  name: string;
  symbol: string;
  /** Noch nicht gebaut: erscheint ausgegraut mit "bald"-Markierung. */
  bald?: boolean;
}

/**
 * Die Hülle des Commlinks: Bereichsmenü links, Werkzeugleiste oben.
 *
 * Bewusst inhaltsfrei — sie weiß nichts über Kampagnen, Personen oder
 * Gegenstände. Dieselbe Hülle soll später die Spieler-Ansicht tragen, nur
 * mit weniger Bereichen (siehe docs/ui-konzept.md).
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
  const [menueOffen, setMenueOffen] = useState(false);

  function waehle(id: string) {
    onBereichWechsel(id);
    setMenueOffen(false); // auf schmalen Geräten verdeckt das Menü den Inhalt
  }

  return (
    <div className="cl-shell">
      <div className="cl-abdunkelung" data-offen={menueOffen} onClick={() => setMenueOffen(false)} />

      <aside className="cl-menue" data-offen={menueOffen}>
        <div className="cl-marke">
          <div className="cl-marke-name">Commlink</div>
          <div className="cl-marke-zeile">NeotopiA // v0.1</div>
        </div>

        <nav className="cl-bereiche">
          {bereiche.map((b, i) => {
            // Trennlinie vor dem ersten noch nicht gebauten Bereich
            const ersterBald = b.bald && !bereiche[i - 1]?.bald;
            return (
              <div key={b.id}>
                {ersterBald && <div className="cl-gruppe">In Arbeit</div>}
                <button
                  type="button"
                  className="cl-bereich"
                  aria-current={b.id === aktiv ? "page" : undefined}
                  disabled={b.bald}
                  onClick={() => waehle(b.id)}
                >
                  <span className="cl-bereich-symbol" aria-hidden="true">
                    {b.symbol}
                  </span>
                  <span>{b.name}</span>
                  {b.bald && <span className="cl-bereich-bald">bald</span>}
                </button>
              </div>
            );
          })}
        </nav>

        {fuss && <div className="cl-menue-fuss">{fuss}</div>}
      </aside>

      <div className="cl-haupt">
        <header className="cl-leiste">
          <button
            type="button"
            className="cl-menue-schalter"
            onClick={() => setMenueOffen((o) => !o)}
            aria-label="Bereiche"
          >
            ☰
          </button>
          <span className="cl-leiste-titel">{titel}</span>
          {werkzeuge && <div className="cl-leiste-werkzeuge">{werkzeuge}</div>}
        </header>

        {/* key: erzwingt das Aufblenden bei jedem Bereichswechsel */}
        <main className="cl-inhalt cl-ansicht" key={aktiv}>
          {children}
        </main>
      </div>

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
