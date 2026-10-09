import { useEffect, useState } from "react";
import { haendlerApi, type HaendlerEintrag, type SortimentEintrag } from "./api";
import { ShopKategorien } from "./ShopKategorien";
import { Fenster } from "../shell/Fenster";
import "./shop.css";

/**
 * Tutorial-Shop (10.10.2026, Marks Konzept) — eigenes, reduziertes Popup im
 * Freebees-Schritt der Charaktererstellung. Anders als `ShopSeite.tsx`:
 * - Kein Verhandeln (Mark: "im Tutorial Shop gibt es kein verhandeln")
 * - Kein eigener Bestellungen-Flow (Tutorial-Shops sind immer PHYSISCH im
 *   Sinne von "sofort übergeben" — digitale Lieferverzögerung ergibt beim
 *   allerersten Einkauf keinen Sinn)
 * - Der "Händler" ist das KI-Symbol (⌬, dasselbe wie bei der Fertigkeiten-
 *   Vergabe) statt eines Portraits — kommentiert jeden Kauf per KI-Aufruf
 *   (`haendlerApi.tutorialKommentar`), rein kosmetisch, kein Einfluss auf
 *   den Kauf selbst.
 *
 * Guthaben kommt vom Aufrufer (`kapital`) und wird nach jedem Kauf über
 * `onKapitalGeaendert` zurückgemeldet — der Freebees-Schritt zeigt daneben
 * prägnant, wieviel noch da ist (Marks Vorgabe).
 */
export function TutorialShopPopup({
  campaignId,
  offen,
  kapital,
  onKapitalGeaendert,
  onSchliessen,
}: {
  campaignId: string;
  offen: boolean;
  kapital: number;
  onKapitalGeaendert: (neu: number) => void;
  onSchliessen: () => void;
}) {
  const [haendler, setHaendler] = useState<HaendlerEintrag | null>(null);
  const [sortiment, setSortiment] = useState<SortimentEintrag[]>([]);
  const [kategorie, setKategorie] = useState<string | null>(null);
  const [kaeuft, setKaeuft] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [kommentar, setKommentar] = useState<string | null>(null);
  const [kommentarLaedt, setKommentarLaedt] = useState(false);

  useEffect(() => {
    if (!offen) return;
    haendlerApi.tutorial(campaignId).then((h) => {
      setHaendler(h);
      if (h) haendlerApi.sortiment(campaignId, h.id).then(setSortiment);
    });
  }, [offen, campaignId]);

  async function kaufen(ware: SortimentEintrag) {
    if (!haendler) return;
    setFehler(null);
    setKommentar(null);
    setKaeuft(ware.gegenstandId);
    try {
      const antwort = await haendlerApi.kaufen(campaignId, haendler.id, ware.gegenstandId);
      onKapitalGeaendert(antwort.kapitalNeu);
      // Vorlagen bleiben im Sortiment (unendlich verfügbar), Unikate
      // verschwinden — gleiches Prinzip wie im echten Shop, hier lokal
      // nachgezogen statt eines Reloads.
      if (!ware.istVorlage) {
        setSortiment((alt) => alt.filter((w) => w.gegenstandId !== ware.gegenstandId));
      }
      setKommentarLaedt(true);
      try {
        const { kommentar } = await haendlerApi.tutorialKommentar(campaignId, haendler.id, ware.name, ware.typ);
        setKommentar(kommentar);
      } catch {
        // Kommentar ist rein kosmetisch — ein KI-Fehlschlag darf den Kauf
        // selbst nicht als gescheitert erscheinen lassen.
      } finally {
        setKommentarLaedt(false);
      }
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Kauf fehlgeschlagen");
    } finally {
      setKaeuft(null);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel="🛒 Tutorial-Shop"
      unterzeile="Erste Ausrüstung einkaufen — kein Verhandeln, dafür ein Kommentar zu jedem Kauf."
      kennung="tutorial-shop"
      onSchliessen={onSchliessen}
    >
      {!haendler ? (
        <p className="shop-leer">
          Die Spielleitung hat noch keinen Tutorial-Shop eingerichtet — diesen Schritt einfach überspringen.
        </p>
      ) : (
        <div className="shop-seite">
          <div className="ts-verkaeufer">
            <span className="ts-verkaeufer-symbol" aria-hidden="true">⌬</span>
            <div className="ts-verkaeufer-text">
              {kommentarLaedt && <p className="ts-kommentar-ladend">… überlegt sich einen Spruch …</p>}
              {kommentar && <p className="ts-kommentar">{kommentar}</p>}
              {!kommentar && !kommentarLaedt && <p className="ts-kommentar-platzhalter">Was darf's sein?</p>}
            </div>
          </div>

          {fehler && <p className="shop-ware-fehler">{fehler}</p>}

          <div className="shop-waren-raster">
            <ShopKategorien sortiment={sortiment} gewaehlt={kategorie} onWaehlen={setKategorie} />
            {sortiment
              .filter((w) => kategorie === null || w.typ === kategorie)
              .map((ware) => (
                <button
                  key={ware.gegenstandId}
                  type="button"
                  className="shop-ware"
                  onClick={() => kaufen(ware)}
                  disabled={kaeuft !== null || ware.preis > kapital}
                  title={ware.name}
                >
                  <span className="shop-ware-bild">
                    {ware.bildUrl ? <img src={ware.bildUrl} alt="" /> : <span aria-hidden="true">◈</span>}
                  </span>
                  <span className="shop-ware-name">{ware.name}</span>
                  <span className="shop-ware-preis">{ware.preis.toLocaleString("de-AT")}¥</span>
                </button>
              ))}
            {sortiment.length === 0 && <p className="shop-leer">Der Tutorial-Shop führt gerade nichts.</p>}
          </div>
        </div>
      )}
    </Fenster>
  );
}
