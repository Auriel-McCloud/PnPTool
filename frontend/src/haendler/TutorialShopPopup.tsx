import { useEffect, useState } from "react";
import { haendlerApi, type HaendlerEintrag, type SortimentEintrag } from "./api";
import { itemsApi, type Gegenstand } from "../items/api";
import { ShopKategorien } from "./ShopKategorien";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { steckbriefKurz, steckbriefZeilen } from "../items/steckbrief";
import { symbolFuerTyp } from "../items/typKatalog";
import "./shop.css";

const SELTENHEIT = ["", "Gewöhnlich", "Ungewöhnlich", "Selten", "Legendär", "Mystisch"];

function effektiverPreis(ware: SortimentEintrag): number {
  return ware.rabattProzent > 0 ? Math.round(ware.preis * (1 - ware.rabattProzent / 100)) : ware.preis;
}

/**
 * Tutorial-Shop im Freebees-Schritt. Klick kauft nicht sofort — erst die
 * Werte lesen, dann Kaufen. Die Spielleitung kauft für den Charakter, dessen
 * Erstellung offen ist (NPC eingeschlossen); ohne personId lehnt der Server
 * den Kauf ab.
 */
export function TutorialShopPopup({
  campaignId,
  personId,
  offen,
  kapital,
  ausgegeben,
  onGekauft,
  onSchliessen,
}: {
  campaignId: string;
  personId: string;
  offen: boolean;
  kapital: number;
  ausgegeben: number;
  onGekauft: (kapitalNeu: number, ausgegeben: number) => void;
  onSchliessen: () => void;
}) {
  const [haendler, setHaendler] = useState<HaendlerEintrag | null>(null);
  const [sortiment, setSortiment] = useState<SortimentEintrag[]>([]);
  const [kategorie, setKategorie] = useState<string | null>(null);
  const [gewaehltId, setGewaehltId] = useState<string | null>(null);
  const [kaeuft, setKaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [kommentar, setKommentar] = useState<string | null>(null);
  const [kommentarLaedt, setKommentarLaedt] = useState(false);
  const [gekauft, setGekauft] = useState<Gegenstand[]>([]);
  const [rueckgabe, setRueckgabe] = useState<Gegenstand | null>(null);

  useEffect(() => {
    if (!offen) return;
    let aktiv = true;
    setFehler(null);
    setSortiment([]);
    haendlerApi
      .tutorial(campaignId)
      .then((h) => {
        if (!aktiv) return;
        setHaendler(h);
        if (!h) return;
        return haendlerApi.sortiment(campaignId, h.id).then((waren) => {
          if (aktiv) setSortiment(waren);
        });
      })
      .catch((e) => {
        if (!aktiv) return;
        setFehler(e instanceof Error ? e.message : "Sortiment nicht ladbar");
      });
    return () => {
      aktiv = false;
    };
  }, [offen, campaignId]);

  useEffect(() => {
    if (!offen) return;
    itemsApi.list(campaignId, personId).then(setGekauft).catch(() => setGekauft([]));
  }, [offen, campaignId, personId]);

  const sichtbar = sortiment.filter((w) => kategorie === null || w.typ === kategorie);
  const gewaehlt = sichtbar.find((w) => w.gegenstandId === gewaehltId) ?? sichtbar[0] ?? null;

  async function kaufen(ware: SortimentEintrag) {
    if (!haendler) return;
    setFehler(null);
    setKommentar(null);
    setKaeuft(true);
    try {
      const antwort = await haendlerApi.kaufen(campaignId, haendler.id, ware.gegenstandId, personId);
      onGekauft(antwort.kapitalNeu, antwort.tutorialAusgegeben ?? ausgegeben);
      itemsApi.list(campaignId, personId).then(setGekauft).catch(() => {});
      if (!ware.istVorlage) {
        setSortiment((alt) => alt.filter((w) => w.gegenstandId !== ware.gegenstandId));
        setGewaehltId(null);
      }
      setKommentarLaedt(true);
      try {
        const { kommentar: spruch } = await haendlerApi.tutorialKommentar(
          campaignId,
          haendler.id,
          ware.name,
          ware.typ,
        );
        setKommentar(spruch);
      } catch {
        // Kommentar ist rein kosmetisch — ein KI-Fehlschlag darf den Kauf
        // selbst nicht als gescheitert erscheinen lassen.
      } finally {
        setKommentarLaedt(false);
      }
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Kauf fehlgeschlagen");
    } finally {
      setKaeuft(false);
    }
  }

  const preis = gewaehlt ? effektiverPreis(gewaehlt) : 0;
  const zuTeuer = gewaehlt !== null && preis > kapital;
  const zeilen = gewaehlt ? steckbriefZeilen(gewaehlt) : [];

  return (
    <>
    <Fenster
      offen={offen}
      titel="🛒 Tutorial-Shop"
      unterzeile="Ware antippen, Werte lesen, dann kaufen. Kein Verhandeln."
      kennung="tutorial-shop"
      breit
      onSchliessen={onSchliessen}
    >
      {!haendler ? (
        <p className="shop-leer">
          Die Spielleitung hat noch keinen Tutorial-Shop eingerichtet — diesen Schritt einfach überspringen.
        </p>
      ) : (
        <div className="shop-seite ts-shop">
          <div className="ts-kopf">
            <div className="ts-verkaeufer">
              <span className="ts-verkaeufer-symbol" aria-hidden="true">
                ⌬
              </span>
              <div className="ts-verkaeufer-text">
                {kommentarLaedt && <p className="ts-kommentar-ladend">… überlegt sich einen Spruch …</p>}
                {kommentar && <p className="ts-kommentar">{kommentar}</p>}
                {!kommentar && !kommentarLaedt && <p className="ts-kommentar-platzhalter">Was darf's sein?</p>}
              </div>
            </div>
            <p className="ts-guthaben">
              Noch <strong>{kapital.toLocaleString("de-AT")}¥</strong>
            </p>
          </div>

          {fehler && <p className="shop-ware-fehler">{fehler}</p>}

          <ShopKategorien sortiment={sortiment} gewaehlt={kategorie} onWaehlen={setKategorie} />

          {sichtbar.length === 0 ? (
            fehler ? null : <p className="shop-leer">Der Tutorial-Shop führt gerade nichts.</p>
          ) : (
            <div className="ts-layout">
              <div className="ts-liste" role="listbox" aria-label="Sortiment">
                {sichtbar.map((ware) => {
                  const aktiv = gewaehlt?.gegenstandId === ware.gegenstandId;
                  const kurz = steckbriefKurz(ware);
                  return (
                    <button
                      key={ware.gegenstandId}
                      type="button"
                      role="option"
                      aria-selected={aktiv}
                      className="ts-zeile"
                      data-aktiv={aktiv}
                      data-seltenheit={ware.seltenheit || 1}
                      onClick={() => {
                        setGewaehltId(ware.gegenstandId);
                        setFehler(null);
                      }}
                    >
                      <span className="ts-zeile-bild">
                        {ware.bildUrl ? <img src={ware.bildUrl} alt="" /> : <span aria-hidden="true">{symbolFuerTyp(ware.typ)}</span>}
                      </span>
                      <span className="ts-zeile-text">
                        <span className="ts-zeile-name">{ware.name}</span>
                        <span className="ts-zeile-typ">
                          {symbolFuerTyp(ware.typ)} {ware.typ}
                          {!ware.istVorlage ? " · Einzelstück" : ""}
                          {ware.seltenheit > 1 ? ` · ${SELTENHEIT[ware.seltenheit] ?? ""}` : ""}
                        </span>
                        {kurz.length > 0 && <span className="ts-zeile-werte">{kurz.join(" · ")}</span>}
                      </span>
                      <span className="ts-zeile-preis">{effektiverPreis(ware).toLocaleString("de-AT")}¥</span>
                    </button>
                  );
                })}
              </div>

              {gewaehlt && (
                <div className="ts-detail">
                  <div className="ts-detail-kopf">
                    <span className="ts-detail-bild">
                      {gewaehlt.bildUrl ? (
                        <img src={gewaehlt.bildUrl} alt="" />
                      ) : (
                        <span aria-hidden="true">{symbolFuerTyp(gewaehlt.typ)}</span>
                      )}
                    </span>
                    <div>
                      <h3 className="ts-detail-name">{gewaehlt.name}</h3>
                      <p className="ts-detail-meta">
                        {symbolFuerTyp(gewaehlt.typ)} {gewaehlt.typ}
                        {" · "}
                        {SELTENHEIT[gewaehlt.seltenheit] || "Gewöhnlich"}
                      </p>
                    </div>
                  </div>

                  {zeilen.length > 0 ? (
                    <dl className="ts-werte">
                      {zeilen.map((z) => (
                        <div key={`${z.label}-${z.wert}`} className="ts-wert-zeile">
                          <dt>{z.label}</dt>
                          <dd>{z.wert}</dd>
                        </div>
                      ))}
                    </dl>
                  ) : (
                    <p className="ts-keine-werte">Keine besonderen Kampfwerte — Alltagsstück.</p>
                  )}

                  {gewaehlt.rabattProzent > 0 && gewaehlt.rabattHinweis && (
                    <p className="shop-ware-hinweis">{gewaehlt.rabattHinweis}</p>
                  )}

                  <p className="ts-preiszeile">
                    <span>Preis</span>
                    <strong>
                      {gewaehlt.rabattProzent > 0 && (
                        <s className="ts-preis-alt">{gewaehlt.preis.toLocaleString("de-AT")}¥</s>
                      )}
                      {preis.toLocaleString("de-AT")}¥
                    </strong>
                  </p>
                  <p className="ts-preiszeile">
                    <span>Danach noch</span>
                    <strong>{Math.max(0, kapital - preis).toLocaleString("de-AT")}¥</strong>
                  </p>
                  {zuTeuer && (
                    <p className="shop-ware-fehler">Dafür fehlen {(preis - kapital).toLocaleString("de-AT")}¥.</p>
                  )}
                  <button
                    type="button"
                    className="shop-ware-kaufen-btn"
                    onClick={() => kaufen(gewaehlt)}
                    disabled={kaeuft || zuTeuer}
                  >
                    {kaeuft ? "Kauft…" : "Kaufen"}
                  </button>
                  <div className="ts-gekauft">
                    <p className="ts-preiszeile">
                      <span>Schon ausgegeben</span>
                      <strong>{ausgegeben.toLocaleString("de-AT")}¥</strong>
                    </p>
                    {gekauft.length === 0 ? (
                      <p className="ts-keine-werte">Noch nichts gekauft.</p>
                    ) : (
                      <ul className="ts-gekauft-liste">
                        {gekauft.map((stück) => (
                          <li key={stück.id}>
                            <span>{stück.name}</span>
                            <span className="ts-gekauft-rechts">
                              <span>{(stück.preis ?? 0).toLocaleString("de-AT")}¥</span>
                              <button type="button" onClick={() => setRueckgabe(stück)}>
                                Zurück
                              </button>
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </Fenster>
    {rueckgabe && haendler && (
      <Bestaetigung
        titel="Zurückgeben?"
        text={`„${rueckgabe.name}“ zurück ins Regal, ${(rueckgabe.preis ?? 0).toLocaleString("de-AT")}¥ wieder aufs Guthaben?`}
        jaText="Zurückgeben"
        onNein={() => setRueckgabe(null)}
        onJa={() => {
          const stueck = rueckgabe;
          setRueckgabe(null);
          setKaeuft(true);
          setFehler(null);
          haendlerApi
            .tutorialZurueck(campaignId, haendler.id, stueck.id, personId)
            .then((antwort) => {
              onGekauft(antwort.kapitalNeu, antwort.tutorialAusgegeben ?? ausgegeben);
              return itemsApi.list(campaignId, personId).then(setGekauft);
            })
            .catch((e) => setFehler(e instanceof Error ? e.message : "Zurückgeben fehlgeschlagen"))
            .finally(() => setKaeuft(false));
        }}
      />
    )}
    </>
  );
}
