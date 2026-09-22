import { TYP_KATALOG } from "./typKatalog";
import "./gegenstaende.css";

/**
 * Große Kachel-Auswahl für den Gegenstandstyp — erster Schritt beim Anlegen.
 *
 * Ersetzt das frühere Dropdown: Mark wollte "ganz viele Kacheln mit den
 * verschiedenen Typen, und ich klicke auf die die ich gerne hätte" statt
 * eines Auswahlfelds. Der Typ ist danach fix (siehe typKatalog.ts) — die
 * große, bewusste Auswahl hier passt dazu besser als ein kleines Dropdown,
 * das man später eh nicht mehr korrigieren kann.
 */
export function TypKachelAuswahl({ onWaehlen }: { onWaehlen: (typ: string) => void }) {
  return (
    <div className="gg-typraster">
      {TYP_KATALOG.map((t) => (
        <button key={t.typ} type="button" className="gg-typ-kachel" onClick={() => onWaehlen(t.typ)}>
          <span className="gg-typ-symbol" aria-hidden="true">
            {t.symbol}
          </span>
          <span className="gg-typ-name">{t.typ}</span>
        </button>
      ))}
    </div>
  );
}
