import { useEffect, useState } from "react";
import { itemsApi, AUGMENT_TRAEGER_TYPEN, type GegenstandMitBesitzer } from "../items/api";
import { drohnenApi, type DrohnenEintrag } from "../drohnen/api";
import { AugmentFenster } from "./AugmentFenster";
import { AugmentTraegerFenster, type AugmentTraeger } from "./AugmentTraegerFenster";
import "../items/gegenstaende.css";

/**
 * Upgraden-Tab im Werkbank-Burgermenü (29.10.2026, siehe
 * docs/wiki/concepts/augments-ausruestung.md): Träger-zentriert statt
 * Upgrade-zentriert (29.10.2026, Marks vierter Klicktest: "ich will ja
 * einen Gegenstand upgraden, also sollte ich die leichte Pistole sehen,
 * und dort die Slots was bereits in sie verbaut ist, und wenn ich die
 * Pistole anklicke sollte ich sehen was ich in sie verbauen kann") — erst
 * der Gegenstand/die Drohne mit Upgrade-Slots, Klick öffnet
 * `AugmentTraegerFenster` (montierte Upgrades + passende freie zum
 * Einbauen). Ein defektes, noch unmontiertes Upgrade hat keinen Träger
 * mehr zugeordnet — dafür bleibt eine eigene Liste oben, öffnet weiterhin
 * direkt `AugmentFenster` (Reparieren). **Nur SL**.
 */
export function AugmentUebersicht({ campaignId }: { campaignId: string }) {
  const [gegenstaende, setGegenstaende] = useState<GegenstandMitBesitzer[]>([]);
  const [drohnen, setDrohnen] = useState<DrohnenEintrag[]>([]);
  const [laden, setLaden] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  const [offenesAugment, setOffenesAugment] = useState<GegenstandMitBesitzer | null>(null);
  const [offenerTraeger, setOffenerTraeger] = useState<AugmentTraeger | null>(null);

  function neuLaden() {
    setLaden(true);
    Promise.all([itemsApi.listAlle(campaignId), drohnenApi.liste(campaignId)])
      .then(([items, d]) => {
        setGegenstaende(items.filter((g) => !g.weggeworfen));
        setDrohnen(d);
      })
      .catch(() => setFehler("Upgrades konnten nicht geladen werden."))
      .finally(() => setLaden(false));
  }

  useEffect(neuLaden, [campaignId]);

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Upgrades…</p>;

  const defekteOhneTraeger = gegenstaende.filter((g) => g.istAugment && g.defekt && !g.montiertAnId);
  const belegteSlots = (id: string) => gegenstaende.filter((g) => g.montiertAnId === id).length;
  const gegenstandTraeger = gegenstaende.filter((g) => AUGMENT_TRAEGER_TYPEN.has(g.typ) && g.upgradeSlots > 0);
  const drohnenTraeger = drohnen.filter((d) => d.upgradeSlots > 0);

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
      {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}
      {gegenstandTraeger.length === 0 && drohnenTraeger.length === 0 && (
        <p className="gg-leer">
          Noch kein Träger mit Upgrade-Slots — das Feld lässt sich bei Waffe/Rüstung/Cyberdeck/Riggerkonsole und bei
          Drohnen/Fahrzeugen im Bearbeiten-Formular setzen.
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
                <span className="gg-kachel-zeile">defekt — {g.ownerName ?? "ohne Besitzer"}</span>
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
              traegerKachel(
                g.id,
                g.name,
                g.bildUrl,
                "🔧",
                `${belegteSlots(g.id)}/${g.upgradeSlots} Slots — ${g.ownerName ?? "ohne Besitzer"}`,
                () =>
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
              traegerKachel(
                d.id,
                d.name,
                d.bildUrl,
                "⛭",
                `${belegteSlots(d.id)}/${d.upgradeSlots} Slots — ${d.riggerName ?? "ungebunden"}`,
                () => setOffenerTraeger({ id: d.id, name: d.name, kind: "Person", upgradeSlots: d.upgradeSlots, kampfFertigkeit: "" }),
              ),
            )}
          </div>
        </>
      )}

      {offenesAugment && (
        <AugmentFenster
          campaignId={campaignId}
          augment={offenesAugment}
          onSchliessen={() => setOffenesAugment(null)}
          onGeaendert={neuLaden}
        />
      )}

      {offenerTraeger && (
        <AugmentTraegerFenster
          campaignId={campaignId}
          traeger={offenerTraeger}
          alleGegenstaende={gegenstaende}
          onSchliessen={() => setOffenerTraeger(null)}
          onGeaendert={neuLaden}
        />
      )}
    </div>
  );
}
