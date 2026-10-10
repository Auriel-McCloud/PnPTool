import { symbolFuerTyp, TYP_KATALOG } from "./typKatalog";
import "./gegenstaende.css";

/**
 * Kategorie-Kacheln vor einer Gegenstandsliste — dasselbe Muster wie beim
 * Shop-Sortiment (ShopKategorien.tsx, 10.10.2026, Marks Vorgabe: "man soll
 * zuerst auf die Kategorie klicken müssen") und bei der Typauswahl beim
 * Anlegen (TypKachelAuswahl.tsx). Mark, 10.10.2026: die Gegenstandsübersicht
 * der SL warf bislang alles ungefiltert zusammen — unübersichtlich, sobald
 * viele Gegenstände existieren.
 *
 * Zeigt nur Typen, die tatsächlich vorkommen (Reihenfolge wie im
 * Typ-Katalog, damit es sich wie die Erstellung anfühlt), + eine
 * "Alle"-Kachel.
 */
export function KategorienAuswahl({
  vorhandeneTypen,
  gewaehlt,
  onWaehlen,
}: {
  vorhandeneTypen: string[];
  gewaehlt: string | null;
  onWaehlen: (typ: string | null) => void;
}) {
  if (vorhandeneTypen.length <= 1) return null;

  return (
    <div className="gg-kategorien-raster">
      <button
        type="button"
        className="gg-kategorie-kachel"
        data-aktiv={gewaehlt === null}
        onClick={() => onWaehlen(null)}
      >
        <span className="gg-kategorie-symbol" aria-hidden="true">✦</span>
        <span>Alle</span>
      </button>
      {vorhandeneTypen.map((typ) => (
        <button
          key={typ}
          type="button"
          className="gg-kategorie-kachel"
          data-aktiv={gewaehlt === typ}
          onClick={() => onWaehlen(typ)}
        >
          <span className="gg-kategorie-symbol" aria-hidden="true">
            {symbolFuerTyp(typ)}
          </span>
          <span>{typ}</span>
        </button>
      ))}
    </div>
  );
}

/** Reihenfolge wie im Typ-Katalog statt alphabetisch — vertraut aus der Erstellung. */
export function vorhandeneTypenSortiert(typen: Iterable<string>): string[] {
  const vorhanden = new Set(typen);
  return TYP_KATALOG.map((t) => t.typ).filter((typ) => vorhanden.has(typ));
}
