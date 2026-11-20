import { useState } from "react";
import { Bestaetigung } from "../shell/Bestaetigung";
import { MengenStepper } from "./MengenStepper";
import { istStapelbar, type WarenkorbPosten } from "./warenkorb";

const yen = (n: number) => `${n.toLocaleString("de-AT")}¥`;

/**
 * Warenkorb-Leiste im normalen Shop (20.11.2026). Zeilen ändern/entfernen
 * kostet nichts — bezahlt wird erst mit „Bezahlen“ + Bestätigung (Marks
 * Standard für geldwirksame Aktionen). Kapital/„Danach noch“/„Dafür fehlen“
 * sind nur UX, der Server prüft den ganzen Korb selbst noch einmal
 * (haendler/kauf.py) und kauft bei einem Fehler gar nichts.
 */
export function ShopWarenkorb({
  posten,
  kapital,
  digital,
  laeuft,
  fehler,
  hinweis,
  onAnzahl,
  onEntfernen,
  onLeeren,
  onBezahlen,
}: {
  posten: WarenkorbPosten[];
  /** null = unbekannt (Laden fehlgeschlagen) — dann entscheidet der Server. */
  kapital: number | null;
  digital: boolean;
  laeuft: boolean;
  fehler: string | null;
  /** Z.B. „… ist nicht mehr im Sortiment und wurde aus dem Warenkorb genommen“. */
  hinweis: string | null;
  onAnzahl: (gegenstandId: string, anzahl: number) => void;
  onEntfernen: (gegenstandId: string) => void;
  onLeeren: () => void;
  onBezahlen: () => Promise<void>;
}) {
  const [aufgeklappt, setAufgeklappt] = useState(true);
  const [fragen, setFragen] = useState(false);

  const stueck = posten.reduce((s, p) => s + p.zeile.anzahl, 0);
  const summe = posten.reduce((s, p) => s + p.summe, 0);
  const zuTeuer = kapital !== null && summe > kapital;
  const leer = posten.length === 0;

  const zusammenfassung = posten
    .map((p) => `${p.zeile.anzahl}× ${p.ware.name}`)
    .join(", ");

  return (
    <section className="shop-warenkorb" aria-label="Warenkorb" data-leer={leer}>
      <button
        type="button"
        className="shop-warenkorb-kopf"
        onClick={() => setAufgeklappt((a) => !a)}
        aria-expanded={aufgeklappt}
      >
        <span>
          🛒 Warenkorb ({stueck})
        </span>
        {!leer && <strong>{yen(summe)}</strong>}
        <span aria-hidden="true">{aufgeklappt ? "▾" : "▸"}</span>
      </button>

      {hinweis && <p className="shop-ware-hinweis shop-warenkorb-hinweis">{hinweis}</p>}

      {aufgeklappt && (
        <>
          {leer ? (
            <p className="shop-ware-hinweis shop-warenkorb-leer">
              Noch leer — Ware antippen und „In den Warenkorb“. Bezahlt wird erst hier.
            </p>
          ) : (
            <ul className="shop-warenkorb-liste">
              {posten.map((p) => (
                <li key={p.zeile.gegenstandId} className="shop-warenkorb-zeile">
                  <span className="shop-warenkorb-name">
                    {p.ware.name}
                    {!istStapelbar(p.ware) && <span className="shop-warenkorb-marke">Einzelstück</span>}
                  </span>
                  {istStapelbar(p.ware) ? (
                    <MengenStepper
                      wert={p.zeile.anzahl}
                      onWert={(n) => onAnzahl(p.zeile.gegenstandId, n)}
                      deaktiviert={laeuft}
                      bezeichnung={`Anzahl ${p.ware.name}`}
                    />
                  ) : (
                    <span className="shop-warenkorb-fest">1 ×</span>
                  )}
                  <span className="shop-warenkorb-stueckpreis">{yen(p.stueckpreis)}/Stk.</span>
                  <span className="shop-warenkorb-zeilensumme">
                    {yen(p.summe)}
                    {p.gratisStuecke > 0 && <span className="shop-warenkorb-gratis">1 Stück gratis (Rassen-Feature)</span>}
                  </span>
                  <button
                    type="button"
                    className="shop-warenkorb-weg"
                    onClick={() => onEntfernen(p.zeile.gegenstandId)}
                    disabled={laeuft}
                    aria-label={`${p.ware.name} aus dem Warenkorb nehmen`}
                    title="Aus dem Warenkorb nehmen"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}

          {!leer && (
            <div className="shop-warenkorb-fuss">
              <p className="ts-preiszeile">
                <span>Summe</span>
                <strong>{yen(summe)}</strong>
              </p>
              {kapital !== null && (
                <p className="ts-preiszeile">
                  <span>Danach noch</span>
                  <strong>{yen(Math.max(0, kapital - summe))}</strong>
                </p>
              )}
              {zuTeuer && kapital !== null && (
                <p className="shop-ware-fehler">Dafür fehlen {yen(summe - kapital)}.</p>
              )}
              {fehler && <p className="shop-ware-fehler">{fehler}</p>}
              <div className="shop-ware-knoepfe">
                <button type="button" onClick={onLeeren} disabled={laeuft}>
                  Leeren
                </button>
                <button
                  type="button"
                  className="shop-ware-kaufen-btn"
                  onClick={() => setFragen(true)}
                  disabled={laeuft || zuTeuer}
                >
                  {laeuft ? "Bezahlt…" : `Bezahlen (${yen(summe)})`}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {fragen && (
        <Bestaetigung
          titel={digital ? "Bestellung bezahlen?" : "Warenkorb bezahlen?"}
          text={
            `${zusammenfassung} für insgesamt ${yen(summe)}` +
            (kapital !== null ? ` — danach noch ${yen(Math.max(0, kapital - summe))}.` : ".") +
            (digital ? " Die Lieferung gibt deine Spielleitung später frei." : "")
          }
          jaText="Bezahlen"
          onJa={() => {
            setFragen(false);
            void onBezahlen();
          }}
          onNein={() => setFragen(false)}
        />
      )}
    </section>
  );
}
