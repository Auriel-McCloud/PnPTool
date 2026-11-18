import { useState } from "react";
import type { PetSortimentEintrag } from "./api";
import { BildGross } from "../shell/BildGross";
import { Fenster } from "../shell/Fenster";
import { vorschau } from "../shell/vorschau";

/**
 * Ein Pet im Tierladen (18.11.2026) — dasselbe Kachel/Popup-Muster wie
 * `ShopWare`, aber ohne Verhandeln/Rabatt (ein Critter ist immer ein
 * Einzelstück, kein Vorlagen-Kauf) und mit der Begleiter-Warnung statt
 * "gibt es nur einmal".
 */
export function ShopPet({
  pet,
  onKaufen,
}: {
  pet: PetSortimentEintrag;
  onKaufen: () => Promise<void>;
}) {
  const [offen, setOffen] = useState(false);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [bildGrossOffen, setBildGrossOffen] = useState(false);

  function schliessen() {
    setOffen(false);
    setBildGrossOffen(false);
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

  return (
    <>
      <button type="button" className="shop-ware" onClick={() => setOffen(true)} title={pet.name}>
        <span className="shop-ware-bild">
          {pet.bildUrl ? <img src={vorschau(pet.bildUrl)} loading="lazy" decoding="async" alt="" /> : <span aria-hidden="true">✦</span>}
        </span>
        <span className="shop-ware-name">{pet.name}</span>
        <span className="shop-ware-preis">
          <span>{pet.preis.toLocaleString("de-AT")}¥</span>
        </span>
      </button>

      <Fenster offen={offen} titel={pet.name} kennung={`shop-pet:${pet.critterId}`} onSchliessen={schliessen}>
        {pet.bildUrl && (
          <button
            type="button"
            className="shop-ware-detail-bild"
            onClick={() => setBildGrossOffen(true)}
            title="Bild vergrößern"
            aria-label="Bild vergrößern"
          >
            <img src={pet.bildUrl} alt="" />
          </button>
        )}
        <div className="shop-ware-kauf-form">
          <p className="shop-ware-hinweis">
            Preis: <strong>{pet.preis.toLocaleString("de-AT")}¥</strong> · ein vollwertiger Begleiter — danach weg
          </p>
          {fehler && <p className="shop-ware-fehler">{fehler}</p>}
          <div className="shop-ware-knoepfe">
            <button type="button" onClick={kaufen} disabled={laeuft} className="shop-ware-kaufen-btn">
              {laeuft ? "Kauft…" : "Kaufen"}
            </button>
          </div>
        </div>
      </Fenster>
      {pet.bildUrl && (
        <BildGross offen={bildGrossOffen} bildUrl={pet.bildUrl} name={pet.name} onSchliessen={() => setBildGrossOffen(false)} />
      )}
    </>
  );
}
