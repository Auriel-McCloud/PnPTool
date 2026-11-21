import { useState } from "react";
import type { SortimentEintrag } from "./api";
import { BildGross } from "../shell/BildGross";
import { Fenster } from "../shell/Fenster";
import { vorschau } from "../shell/vorschau";
import { MengenStepper } from "./MengenStepper";
import { istStapelbar, stueckpreis } from "./warenkorb";

/**
 * Eine Ware im Shop-Raster. Der Seltenheitsrahmen kommt aus
 * `Gegenstand.seltenheit` (1–5) — siehe shop.css für die Farbschema-Regeln
 * (Marks Vorgabe 24.09.2026: grau/blau/silbern-glitzernd/orange-gezackt/
 * violett-wabernd).
 *
 * Kein Klick kauft direkt: das Popup legt die Ware in den Warenkorb
 * (20.11.2026, Marks Vorgabe), bezahlt wird erst an der Kasse mit
 * Bestätigung (ShopWarenkorb.tsx). Stapelbare Ware (Vorlage, nicht
 * einzigartig) bekommt dabei eine Stückzahl [−] [n] [+]; ein Einzelstück
 * liegt höchstens einmal im Korb. Bei physischen Shops steht daneben ein
 * "Verhandeln"-Knopf (schickt ein Gegenangebot für EIN Stück an die SL
 * statt zum Listenpreis zu kaufen); digitale Shops kennen das nicht
 * (Marks Vorgabe: kein Verhandeln online).
 */
export function ShopWare({
  ware,
  seltenheit,
  kannVerhandeln,
  imWarenkorb,
  warenkorbAktiv,
  kapital,
  warenkorbSumme = 0,
  onInDenWarenkorb,
  onVerhandelnAnfragen,
}: {
  ware: SortimentEintrag;
  /** Aus dem zugehörigen Gegenstand — die Sortiment-Antwort selbst trägt
   * keine Seltenheit, nur Name/Preis/Typ (siehe haendler/schemas.py). */
  seltenheit: number;
  kannVerhandeln: boolean;
  /** Wie viele Stück dieser Ware schon im Warenkorb liegen (0 = keine). */
  imWarenkorb: number;
  /** false = kein Käufer bekannt (SL ohne gewählten Charakter) — dann
   * gibt es keinen Warenkorb. */
  warenkorbAktiv: boolean;
  /** Geld des Käufers; undefined/null = unbekannt, dann keine Rechnung. */
  kapital?: number | null;
  /** Was im Warenkorb schon zusammenkommt (für „Danach noch“). */
  warenkorbSumme?: number;
  onInDenWarenkorb: (anzahl: number) => void;
  onVerhandelnAnfragen?: (vorgeschlagenerPreis: number) => Promise<void>;
}) {
  const [offen, setOffen] = useState(false);
  const [anzahl, setAnzahl] = useState(1);
  const [verhandelModus, setVerhandelModus] = useState(false);
  const [verhandelPreis, setVerhandelPreis] = useState("");
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [verhandelGesendet, setVerhandelGesendet] = useState(false);
  const [bildGrossOffen, setBildGrossOffen] = useState(false);

  const hatRabatt = ware.rabattProzent > 0;
  // Ganzzahlig abgerundet wie der Server (repository.py::preis_nach_rabatt) —
  // vorher Math.round, das lag bei krummen Rabatten 1¥ neben dem echten Preis.
  const effektiverPreis = stueckpreis(ware);
  const stapelbar = istStapelbar(ware);
  const menge = stapelbar ? anzahl : 1;
  const summe = effektiverPreis * menge;
  const einzelstueckSchonImKorb = !stapelbar && imWarenkorb > 0;
  const kapitalBekannt = typeof kapital === "number";
  const korbDanach = warenkorbSumme + summe;
  const fehlt = kapitalBekannt ? korbDanach - (kapital as number) : 0;

  function schliessen() {
    setOffen(false);
    setAnzahl(1);
    setBildGrossOffen(false);
    setVerhandelModus(false);
    setVerhandelGesendet(false);
    setVerhandelPreis("");
    setFehler(null);
  }

  function inDenWarenkorb() {
    onInDenWarenkorb(menge);
    schliessen();
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
          {ware.bildUrl ? <img src={vorschau(ware.bildUrl)} loading="lazy" decoding="async" alt="" /> : <span aria-hidden="true">◈</span>}
        </span>
        {!ware.istVorlage && <span className="shop-ware-typ">Einzelstück — danach weg</span>}
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
        ) : (
          <>
            {ware.bildUrl && (
              <button
                type="button"
                className="shop-ware-detail-bild"
                onClick={() => setBildGrossOffen(true)}
                title="Bild vergrößern"
                aria-label="Bild vergrößern"
              >
                <img src={ware.bildUrl} alt="" />
              </button>
            )}
            {verhandelModus ? (
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
              {stapelbar && " pro Stück"}
              {hatRabatt && <> (statt {ware.preis.toLocaleString("de-AT")}¥)</>}
              {(!ware.istVorlage || ware.einzigartig) && " · gibt es nur einmal"}
            </p>
            {stapelbar && (
              <div className="shop-ware-anzahl">
                <MengenStepper wert={anzahl} onWert={setAnzahl} />
                <span className="shop-ware-anzahl-summe">
                  {anzahl} × {effektiverPreis.toLocaleString("de-AT")}¥ ={" "}
                  <strong>{summe.toLocaleString("de-AT")}¥</strong>
                </span>
              </div>
            )}
            {stapelbar && ware.hatMenge && ware.menge > 1 && (
              <p className="shop-ware-hinweis">
                Je Stück ×{ware.menge} — ergibt einen Stapel ×{(anzahl * ware.menge).toLocaleString("de-AT")}.
              </p>
            )}
            {imWarenkorb > 0 && (
              <p className="shop-ware-hinweis">
                {stapelbar ? `Schon im Warenkorb: ${imWarenkorb} Stück.` : "Liegt schon im Warenkorb."}
              </p>
            )}
            {kapitalBekannt && !einzelstueckSchonImKorb && (
              <p className="shop-ware-hinweis">
                Warenkorb danach: <strong>{korbDanach.toLocaleString("de-AT")}¥</strong> ·{" "}
                {fehlt > 0 ? (
                  <span className="shop-ware-fehler-inline">Dafür fehlen {fehlt.toLocaleString("de-AT")}¥</span>
                ) : (
                  <>
                    Danach noch <strong>{(-fehlt).toLocaleString("de-AT")}¥</strong>
                  </>
                )}
              </p>
            )}
            {fehler && <p className="shop-ware-fehler">{fehler}</p>}
            <div className="shop-ware-knoepfe">
              {kannVerhandeln && onVerhandelnAnfragen && (
                <button type="button" onClick={() => setVerhandelModus(true)} disabled={laeuft}>
                  Verhandeln
                </button>
              )}
              <button
                type="button"
                onClick={inDenWarenkorb}
                disabled={!warenkorbAktiv || einzelstueckSchonImKorb}
                title={warenkorbAktiv ? undefined : "Kein Käufer gewählt — ohne Charakter gibt es keinen Warenkorb"}
                className="shop-ware-kaufen-btn"
              >
                🛒 In den Warenkorb
              </button>
            </div>
          </div>
            )}
          </>
        )}
      </Fenster>
      {ware.bildUrl && (
        <BildGross
          offen={bildGrossOffen}
          bildUrl={ware.bildUrl}
          name={ware.name}
          onSchliessen={() => setBildGrossOffen(false)}
        />
      )}
    </>
  );
}
