import { useState } from "react";
import { AUGMENT_TRAEGER_TYPEN, type GegenstandMitBesitzer } from "../items/api";
import { type DrohnenEintrag } from "../drohnen/api";
import { AugmentFenster } from "./AugmentFenster";
import { AugmentTraegerFenster, type AugmentTraeger } from "./AugmentTraegerFenster";
import "../items/gegenstaende.css";

/**
 * Werkbank-Upgraden für Spieler (29.10.2026, Mark: "natürlich war das für
 * die Spieler gedacht... damit das für sie dann auch angezeigt wird, und
 * ihre Materialien verwendet werden"). Gegenstück zu `AugmentUebersicht.tsx`
 * (SL-Ansicht, campaignweit) — hier nur die eigenen Träger (Besitzer = man
 * selbst ODER eine eigene gebundene Drohne/eigenes Fahrzeug) samt eigenen
 * Upgrades. Träger-zentriert (29.10.2026, Marks vierter Klicktest, siehe
 * `AugmentUebersicht.tsx`-Docstring) statt Upgrade-zentriert.
 * Montieren/Demontieren/Reparieren laufen über dieselben Routen wie bei der
 * SL — die Besitzprüfung sitzt serverseitig
 * (`items/routes.py::_augment_oder_404`/`_eigener_kreis`).
 */
export function AugmentUebersichtSpieler({
  campaignId,
  meine,
  meineDrohnen,
  onGeaendert,
}: {
  campaignId: string;
  /** Alle eigenen Gegenstände (Besitzer = eigene Person ODER eigene
   *  gebundene Drohne/eigenes Fahrzeug) — Träger UND Upgrades gemeinsam,
   *  damit sich montierte/freie Upgrades pro Träger clientseitig ermitteln
   *  lassen, ohne pro Klick nachzufragen. */
  meine: GegenstandMitBesitzer[];
  meineDrohnen: DrohnenEintrag[];
  onGeaendert: () => void;
}) {
  const [offenesAugment, setOffenesAugment] = useState<GegenstandMitBesitzer | null>(null);
  const [offenerTraeger, setOffenerTraeger] = useState<AugmentTraeger | null>(null);

  const defekteOhneTraeger = meine.filter((g) => g.istAugment && g.defekt && !g.montiertAnId);
  const belegteSlots = (id: string) => meine.filter((g) => g.montiertAnId === id).length;
  const gegenstandTraeger = meine.filter((g) => AUGMENT_TRAEGER_TYPEN.has(g.typ) && g.upgradeSlots > 0);
  const drohnenTraeger = meineDrohnen.filter((d) => d.upgradeSlots > 0);

  function traegerKachel(
    id: string,
    name: string,
    bildUrl: string | null,
    symbol: string,
    zeile: string,
    oeffnen: () => void,
  ) {
    return (
      <button key={id} type="button" className="gg-kachel" onClick={oeffnen}>
        <span className="gg-kachel-bild">{bildUrl ? <img src={bildUrl} alt="" /> : <span aria-hidden="true">{symbol}</span>}</span>
        <span className="gg-kachel-name">{name}</span>
        <span className="gg-kachel-zeile">{zeile}</span>
      </button>
    );
  }

  return (
    <div className="gg-seite">
      {gegenstandTraeger.length === 0 && drohnenTraeger.length === 0 && (
        <p className="gg-leer">
          Noch kein eigener Gegenstand/keine eigene Drohne mit Upgrade-Slots — dein SL trägt das Feld am
          Bearbeiten-Formular ein.
        </p>
      )}

      {defekteOhneTraeger.length > 0 && (
        <>
          <p className="lu-hinweis" style={{ color: "var(--nein)" }}>Defekt, ohne Träger ({defekteOhneTraeger.length})</p>
          <div className="gg-raster">
            {defekteOhneTraeger.map((g) => (
              <button key={g.id} type="button" className="gg-kachel" onClick={() => setOffenesAugment(g)}>
                <span className="gg-kachel-bild">{g.bildUrl ? <img src={g.bildUrl} alt="" /> : <span aria-hidden="true">🔩</span>}</span>
                <span className="gg-kachel-name">{g.name}</span>
                <span className="gg-kachel-zeile">defekt</span>
              </button>
            ))}
          </div>
        </>
      )}

      {gegenstandTraeger.length > 0 && (
        <>
          <p className="lu-hinweis">Gegenstände ({gegenstandTraeger.length})</p>
          <div className="gg-raster">
            {gegenstandTraeger.map((g) =>
              traegerKachel(g.id, g.name, g.bildUrl, "🔧", `${belegteSlots(g.id)}/${g.upgradeSlots} Slots`, () =>
                setOffenerTraeger({
                  id: g.id,
                  name: g.name,
                  kind: "Gegenstand",
                  upgradeSlots: g.upgradeSlots,
                  kampfFertigkeit: g.kampfFertigkeit,
                }),
              ),
            )}
          </div>
        </>
      )}

      {drohnenTraeger.length > 0 && (
        <>
          <p className="lu-hinweis">Drohnen &amp; Fahrzeuge ({drohnenTraeger.length})</p>
          <div className="gg-raster">
            {drohnenTraeger.map((d) =>
              traegerKachel(d.id, d.name, d.bildUrl, "⛭", `${belegteSlots(d.id)}/${d.upgradeSlots} Slots`, () =>
                setOffenerTraeger({ id: d.id, name: d.name, kind: "Person", upgradeSlots: d.upgradeSlots, kampfFertigkeit: "" }),
              ),
            )}
          </div>
        </>
      )}

      {offenesAugment && (
        <AugmentFenster campaignId={campaignId} augment={offenesAugment} onSchliessen={() => setOffenesAugment(null)} onGeaendert={onGeaendert} />
      )}

      {offenerTraeger && (
        <AugmentTraegerFenster
          campaignId={campaignId}
          traeger={offenerTraeger}
          alleGegenstaende={meine}
          onSchliessen={() => setOffenerTraeger(null)}
          onGeaendert={onGeaendert}
        />
      )}
    </div>
  );
}
