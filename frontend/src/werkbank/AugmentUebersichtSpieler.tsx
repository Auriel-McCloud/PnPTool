import { useState } from "react";
import { type GegenstandMitBesitzer } from "../items/api";
import { AugmentFenster } from "./AugmentFenster";
import "../items/gegenstaende.css";

/**
 * Werkbank-Augments für Spieler (29.10.2026, Mark: "natürlich war das für
 * die Spieler gedacht... damit das für sie dann auch angezeigt wird, und
 * ihre Materialien verwendet werden"). Gegenstück zu `AugmentUebersicht.tsx`
 * (SL-Ansicht, campaignweit) — hier nur die eigenen Augments (Besitzer =
 * man selbst ODER eine eigene gebundene Drohne/eigenes Fahrzeug), die
 * Vorauswahl übernimmt `SpielerAnsicht.tsx`. Montieren/Demontieren/
 * Reparieren laufen über dieselben Routen wie bei der SL — die Besitzprüfung
 * sitzt serverseitig (`items/routes.py::_augment_oder_404`/`_eigener_kreis`).
 */
export function AugmentUebersichtSpieler({
  campaignId,
  items,
  onGeaendert,
}: {
  campaignId: string;
  items: GegenstandMitBesitzer[];
  onGeaendert: () => void;
}) {
  const [offenesAugment, setOffenesAugment] = useState<GegenstandMitBesitzer | null>(null);

  const defekte = items.filter((g) => g.defekt);
  const montiert = items.filter((g) => !g.defekt && g.montiertAnId);
  const frei = items.filter((g) => !g.defekt && !g.montiertAnId);

  function kachel(g: GegenstandMitBesitzer) {
    return (
      <button key={g.id} type="button" className="gg-kachel" onClick={() => setOffenesAugment(g)}>
        <span className="gg-kachel-bild">{g.bildUrl ? <img src={g.bildUrl} alt="" /> : <span aria-hidden="true">🔩</span>}</span>
        <span className="gg-kachel-name">{g.name}</span>
        <span className="gg-kachel-zeile">
          {g.defekt ? "defekt" : g.montiertAnId ? `montiert an ${g.montiertAnName}` : "frei"}
          {g.ownerName ? ` — ${g.ownerName}` : ""}
        </span>
      </button>
    );
  }

  return (
    <div className="gg-seite">
      {items.length === 0 && (
        <p className="gg-leer">
          Noch kein Augment im Besitz — dein SL markiert einen Gegenstand mit "Ist selbst ein Augment", damit er
          hier auftaucht.
        </p>
      )}

      {defekte.length > 0 && (
        <>
          <p className="lu-hinweis" style={{ color: "var(--nein)" }}>Defekt ({defekte.length})</p>
          <div className="gg-raster">{defekte.map(kachel)}</div>
        </>
      )}
      {frei.length > 0 && (
        <>
          <p className="lu-hinweis">Frei, montierbar ({frei.length})</p>
          <div className="gg-raster">{frei.map(kachel)}</div>
        </>
      )}
      {montiert.length > 0 && (
        <>
          <p className="lu-hinweis">Montiert ({montiert.length})</p>
          <div className="gg-raster">{montiert.map(kachel)}</div>
        </>
      )}

      {offenesAugment && (
        <AugmentFenster
          campaignId={campaignId}
          augment={offenesAugment}
          onSchliessen={() => setOffenesAugment(null)}
          onGeaendert={onGeaendert}
        />
      )}
    </div>
  );
}
