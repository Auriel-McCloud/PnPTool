import { useState } from "react";
import type { SortimentEintrag } from "./api";
import { Fenster } from "../shell/Fenster";

/**
 * Eine Ware im Shop-Raster. Der Seltenheitsrahmen kommt aus
 * `Gegenstand.seltenheit` (1–5) — siehe shop.css für die Farbschema-Regeln
 * (Marks Vorgabe 24.09.2026: grau/blau/silbern-glitzernd/orange-gezackt/
 * violett-wabernd).
 *
 * Kauf läuft immer über eine Rückfrage (Marks Standardvorgabe für
 * geldwirksame Aktionen) — kein Klick kauft direkt. Bei physischen Shops
 * steht daneben ein "Verhandeln"-Knopf (schickt ein Gegenangebot an die
 * SL statt sofort zum Listenpreis zu kaufen); digitale Shops kennen das
 * nicht (Marks Vorgabe: kein Verhandeln online).
 */
export function ShopWare({
  ware,
  seltenheit,
  kannVerhandeln,
  onKaufen,
  onVerhandelnAnfragen,
}: {
  ware: SortimentEintrag;
  /** Aus dem zugehörigen Gegenstand — die Sortiment-Antwort selbst trägt
   * keine Seltenheit, nur Name/Preis/Typ (siehe haendler/schemas.py). */
  seltenheit: number;
  kannVerhandeln: boolean;
  onKaufen: () => Promise<void>;
  onVerhandelnAnfragen?: (vorgeschlagenerPreis: number) => Promise<void>;
}) {
  const [offen, setOffen] = useState(false);
  const [verhandelModus, setVerhandelModus] = useState(false);
  const [verhandelPreis, setVerhandelPreis] = useState("");
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [verhandelGesendet, setVerhandelGesendet] = useState(false);

  const hatRabatt = ware.rabattProzent > 0;
  const effektiverPreis = hatRabatt
    ? Math.round(ware.preis * (1 - ware.rabattProzent / 100))
    : ware.preis;

  function schliessen() {
    setOffen(false);
    setVerhandelModus(false);
    setVerhandelGesendet(false);
    setVerhandelPreis("");
    setFehler(null);
  }

  async function kaufen() {
    setLaeuft(true);
    setFehler(null);
    try {
      await onKaufen();
      schliessen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Kauf fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  async function verhandelnSenden() {
    const preis = Number(verhandelPreis);
    if (!onVerhandelnAnfragen || !Number.isFinite(preis) || preis <= 0) return;
    setLaeuft(true);
    setFehler(null);
    try {
      await onVerhandelnAnfragen(preis);
      setVerhandelGesendet(true);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Anfrage konnte nicht gesendet werden");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className="shop-ware"
        data-seltenheit={seltenheit}
        onClick={() => setOffen(true)}
        title={ware.name}
      >
        {hatRabatt && <span className="shop-ware-rabatt-band">-{ware.rabattProzent}%</span>}
        <span className="shop-ware-bild">
          {ware.bildUrl ? <img src={ware.bildUrl} alt="" /> : <span aria-hidden="true">◈</span>}
        </span>
        <span className="shop-ware-name">{ware.name}</span>
        <span className="shop-ware-preis">
          {hatRabatt && <span className="shop-ware-preis-alt">{ware.preis.toLocaleString("de-AT")}¥</span>}
          <span className={hatRabatt ? "shop-ware-preis-neu" : undefined}>
            {effektiverPreis.toLocaleString("de-AT")}¥
          </span>
        </span>
      </button>

      <Fenster offen={offen} titel={ware.name} kennung={`shop-ware:${ware.gegenstandId}`} onSchliessen={schliessen}>
        {verhandelGesendet ? (
          <p className="shop-ware-erfolg">
            Angebot über {Number(verhandelPreis).toLocaleString("de-AT")}¥ an die Spielleitung geschickt — du
            bekommst Bescheid, sobald sie antwortet.
          </p>
        ) : verhandelModus ? (
          <div className="shop-ware-verhandel-form">
            {hatRabatt && ware.rabattHinweis && <p className="shop-ware-hinweis">{ware.rabattHinweis}</p>}
            <p className="shop-ware-hinweis">
              Listenpreis: <strong>{effektiverPreis.toLocaleString("de-AT")}¥</strong>. Was bietest du?
            </p>
            <input
              type="number"
              min={1}
              value={verhandelPreis}
              onChange={(e) => setVerhandelPreis(e.target.value)}
              placeholder="Dein Angebot in ¥"
              autoFocus
            />
            {fehler && <p className="shop-ware-fehler">{fehler}</p>}
            <div className="shop-ware-knoepfe">
              <button type="button" onClick={() => setVerhandelModus(false)} disabled={laeuft}>
                Zurück
              </button>
              <button type="button" onClick={verhandelnSenden} disabled={laeuft || !verhandelPreis}>
                {laeuft ? "Sendet…" : "Angebot schicken"}
              </button>
            </div>
          </div>
        ) : (
          <div className="shop-ware-kauf-form">
            {hatRabatt && ware.rabattHinweis && <p className="shop-ware-hinweis">{ware.rabattHinweis}</p>}
            <p className="shop-ware-hinweis">
              Preis: <strong>{effektiverPreis.toLocaleString("de-AT")}¥</strong>
              {hatRabatt && <> (statt {ware.preis.toLocaleString("de-AT")}¥)</>}
            </p>
            {fehler && <p className="shop-ware-fehler">{fehler}</p>}
            <div className="shop-ware-knoepfe">
              {kannVerhandeln && onVerhandelnAnfragen && (
                <button type="button" onClick={() => setVerhandelModus(true)} disabled={laeuft}>
                  Verhandeln
                </button>
              )}
              <button type="button" onClick={kaufen} disabled={laeuft} className="shop-ware-kaufen-btn">
                {laeuft ? "Kauft…" : "Kaufen"}
              </button>
            </div>
          </div>
        )}
      </Fenster>
    </>
  );
}
