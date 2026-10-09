import { TYP_KATALOG, symbolFuerTyp } from "../items/typKatalog";
import type { SortimentEintrag } from "./api";

/**
 * Kategorie-Kacheln vor dem eigentlichen Sortiment (10.10.2026, Marks
 * Vorgabe: "man soll zuerst auf die Kategorie klicken müssen"). Zeigt nur
 * Kategorien, die dieser Shop tatsächlich führt + eine "Alle"-Kachel.
 * Wiederverwendet den bestehenden Typ-Katalog/Symbole (items/typKatalog.ts)
 * statt eine zweite Liste zu pflegen.
 */
export function ShopKategorien({
  sortiment,
  gewaehlt,
  onWaehlen,
}: {
  sortiment: SortimentEintrag[];
  gewaehlt: string | null;
  onWaehlen: (typ: string | null) => void;
}) {
  const vorhandeneTypen = Array.from(new Set(sortiment.map((w) => w.typ))).sort();

  if (vorhandeneTypen.length <= 1) return null;

  return (
    <div className="shop-kategorien-raster">
      <button
        type="button"
        className="shop-kategorie-kachel"
        data-aktiv={gewaehlt === null}
        onClick={() => onWaehlen(null)}
      >
        <span className="shop-kategorie-symbol" aria-hidden="true">✦</span>
        <span>Alle</span>
      </button>
      {vorhandeneTypen.map((typ) => (
        <button
          key={typ}
          type="button"
          className="shop-kategorie-kachel"
          data-aktiv={gewaehlt === typ}
          onClick={() => onWaehlen(typ)}
        >
          <span className="shop-kategorie-symbol" aria-hidden="true">
            {symbolFuerTyp(typ)}
          </span>
          <span>{typ}</span>
        </button>
      ))}
    </div>
  );
}

export { TYP_KATALOG };
