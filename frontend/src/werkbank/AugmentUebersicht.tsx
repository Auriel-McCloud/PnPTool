import { useEffect, useState } from "react";
import { itemsApi, AUGMENT_TRAEGER_TYPEN, type GegenstandMitBesitzer } from "../items/api";
import { steckbriefKurz } from "../items/steckbrief";
import { drohnenApi, type DrohnenEintrag } from "../drohnen/api";
import { AugmentFenster } from "./AugmentFenster";
import { AugmentTraegerPanel, type AugmentTraeger } from "./AugmentTraegerPanel";
import "../items/gegenstaende.css";
import "./werkbank.css";

/**
 * Upgraden-Tab im Werkbank-Burgermenü (29.10.2026, siehe
 * docs/wiki/concepts/augments-ausruestung.md): zweigeteilte Ansicht
 * (29.10.2026, Mark: "können wir es vielleicht in der Mitte aufteilen, so
 * dass man auf einer Seite die Items und auf der anderen die
 * Upgrade-Materialien sieht?") — links der Gegenstand/die Drohne mit
 * Upgrade-Slots, rechts (`AugmentTraegerPanel`) das Fach dazu: montierte
 * Upgrades + passende freie zum Einbauen. Ein defektes, noch unmontiertes
 * Upgrade hat keinen Träger mehr zugeordnet — dafür bleibt eine eigene
 * Liste oben links, öffnet weiterhin direkt `AugmentFenster` (Reparieren).
 * **Nur SL**.
 */
export function AugmentUebersicht({ campaignId }: { campaignId: string }) {
  const [gegenstaende, setGegenstaende] = useState<GegenstandMitBesitzer[]>([]);
  const [drohnen, setDrohnen] = useState<DrohnenEintrag[]>([]);
  const [laden, setLaden] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  const [offenesAugment, setOffenesAugment] = useState<GegenstandMitBesitzer | null>(null);
  const [vorausgewaehlt, setVorausgewaehlt] = useState(false);
  const [gewaehlterTraeger, setGewaehlterTraeger] = useState<AugmentTraeger | null>(null);

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
      {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}
      {gegenstandTraeger.length === 0 && drohnenTraeger.length === 0 && (
        <p className="gg-leer">
          Noch kein Träger mit Upgrade-Slots — das Feld lässt sich bei Waffe/Rüstung/Cyberdeck/Riggerkonsole und bei
          Drohnen/Fahrzeugen im Bearbeiten-Formular setzen.
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
                    <span className="gg-kachel-zeile">defekt — {g.ownerName ?? "ohne Besitzer"}</span>
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
                    },
                    g.bildUrl,
                    "🔧",
                    `${belegteSlots(g.id)}/${g.upgradeSlots} Slots — ${g.ownerName ?? "ohne Besitzer"}`,
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
                    { id: d.id, name: d.name, kind: "Person", upgradeSlots: d.upgradeSlots, kampfFertigkeit: "" },
                    d.bildUrl,
                    "⛭",
                    `${belegteSlots(d.id)}/${d.upgradeSlots} Slots — ${d.riggerName ?? "ungebunden"}`,
                  ),
                )}
              </div>
            </>
          )}
        </div>

        <div className="wb-spalte">
          <AugmentTraegerPanel
            traeger={gewaehlterTraeger}
            alleGegenstaende={gegenstaende}
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
          onGeaendert={neuLaden}
        />
      )}
    </div>
  );
}
