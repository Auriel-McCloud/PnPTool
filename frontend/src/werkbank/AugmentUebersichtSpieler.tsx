import { useState } from "react";
import { AUGMENT_TRAEGER_TYPEN, type GegenstandMitBesitzer } from "../items/api";
import { steckbriefKurz } from "../items/steckbrief";
import { type DrohnenEintrag } from "../drohnen/api";
import { AugmentFenster } from "./AugmentFenster";
import { AugmentTraegerPanel, type AugmentTraeger } from "./AugmentTraegerPanel";
import "../items/gegenstaende.css";
import "./werkbank.css";

/**
 * Werkbank-Upgraden für Spieler (29.10.2026, Mark: "natürlich war das für
 * die Spieler gedacht... damit das für sie dann auch angezeigt wird, und
 * ihre Materialien verwendet werden"). Gegenstück zu `AugmentUebersicht.tsx`
 * (SL-Ansicht, campaignweit) — hier nur die eigenen Träger (Besitzer = man
 * selbst ODER eine eigene gebundene Drohne/eigenes Fahrzeug) samt eigenen
 * Upgrades. Zweigeteilte Ansicht (29.10.2026, Mark: "können wir es
 * vielleicht in der Mitte aufteilen, so dass man auf einer Seite die
 * Items und auf der anderen die Upgrade-Materialien sieht?", siehe
 * `AugmentUebersicht.tsx`-Docstring) statt Popup pro Klick.
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
  const [vorausgewaehlt, setVorausgewaehlt] = useState(false);
  const [gewaehlterTraeger, setGewaehlterTraeger] = useState<AugmentTraeger | null>(null);

  const defekteOhneTraeger = meine.filter((g) => g.istAugment && g.defekt && !g.montiertAnId);
  const belegteSlots = (id: string) => meine.filter((g) => g.montiertAnId === id).length;
  const gegenstandTraeger = meine.filter((g) => AUGMENT_TRAEGER_TYPEN.has(g.typ) && g.upgradeSlots > 0);
  const drohnenTraeger = meineDrohnen.filter((d) => d.upgradeSlots > 0);

  function traegerKachel(traeger: AugmentTraeger, bildUrl: string | null, symbol: string, zeile: string) {
    return (
      <button
        key={traeger.id}
        type="button"
        className="gg-kachel"
        data-aktiv={gewaehlterTraeger?.id === traeger.id}
        onClick={() => setGewaehlterTraeger(traeger)}
      >
        <span className="gg-kachel-bild">{bildUrl ? <img src={bildUrl} alt="" /> : <span aria-hidden="true">{symbol}</span>}</span>
        <span className="gg-kachel-name">{traeger.name}</span>
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

      <div className="wb-split">
        <div className="wb-spalte">
          {defekteOhneTraeger.length > 0 && (
            <>
              <p className="lu-hinweis" style={{ color: "var(--nein)" }}>Defekt, ohne Träger ({defekteOhneTraeger.length})</p>
              <div className="wb-kachelraster">
                {defekteOhneTraeger.map((g) => (
                  <button key={g.id} type="button" className="gg-kachel" onClick={() => setOffenesAugment(g)}>
                    <span className="gg-kachel-bild">{g.bildUrl ? <img src={g.bildUrl} alt="" /> : <span aria-hidden="true">🔩</span>}</span>
                    <span className="gg-kachel-name">{g.name}</span>
                    <span className="gg-kachel-zeile">defekt</span>
                    {steckbriefKurz(g).length > 0 && (
                      <span className="gg-kachel-steckbrief">{steckbriefKurz(g).join(" · ")}</span>
                    )}
                  </button>
                ))}
              </div>
            </>
          )}

          {gegenstandTraeger.length > 0 && (
            <>
              <p className="lu-hinweis">Gegenstände ({gegenstandTraeger.length})</p>
              <div className="wb-kachelraster">
                {gegenstandTraeger.map((g) =>
                  traegerKachel(
                    {
                      id: g.id,
                      name: g.name,
                      kind: "Gegenstand",
                      upgradeSlots: g.upgradeSlots,
                      kampfFertigkeit: g.kampfFertigkeit,
                      typ: g.typ,
                    },
                    g.bildUrl,
                    "🔧",
                    `${belegteSlots(g.id)}/${g.upgradeSlots} Slots`,
                  ),
                )}
              </div>
            </>
          )}

          {drohnenTraeger.length > 0 && (
            <>
              <p className="lu-hinweis">Drohnen &amp; Fahrzeuge ({drohnenTraeger.length})</p>
              <div className="wb-kachelraster">
                {drohnenTraeger.map((d) =>
                  traegerKachel(
                    { id: d.id, name: d.name, kind: "Person", upgradeSlots: d.upgradeSlots, kampfFertigkeit: "", typ: "" },
                    d.bildUrl,
                    "⛭",
                    `${belegteSlots(d.id)}/${d.upgradeSlots} Slots`,
                  ),
                )}
              </div>
            </>
          )}
        </div>

        <div className="wb-spalte">
          <AugmentTraegerPanel
            traeger={gewaehlterTraeger}
            alleGegenstaende={meine}
            onUpgradeKlick={(g, vorwaehlen) => {
              setVorausgewaehlt(vorwaehlen);
              setOffenesAugment(g);
            }}
          />
        </div>
      </div>

      {offenesAugment && (
        <AugmentFenster
          campaignId={campaignId}
          augment={offenesAugment}
          vorausgewaehltesZiel={vorausgewaehlt && gewaehlterTraeger ? gewaehlterTraeger : undefined}
          onSchliessen={() => setOffenesAugment(null)}
          onGeaendert={onGeaendert}
        />
      )}
    </div>
  );
}
