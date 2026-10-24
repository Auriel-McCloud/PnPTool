import { useState } from "react";
import { haendlerApi, type HaendlerEintrag, type SortimentEintrag } from "./api";
import { itemsApi, type Gegenstand } from "../items/api";
import { ShopKategorien } from "./ShopKategorien";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { useNachladen } from "../shell/nachladen";
import { steckbriefKurz, steckbriefZeilen } from "../items/steckbrief";
import { symbolFuerTyp } from "../items/typKatalog";
import { ersterKaufTrifft } from "../rassen/gratisKauf";
import "./shop.css";

const SELTENHEIT = ["", "Gewöhnlich", "Ungewöhnlich", "Selten", "Legendär", "Mystisch"];

function effektiverPreis(ware: SortimentEintrag): number {
  return ware.rabattProzent > 0 ? Math.round(ware.preis * (1 - ware.rabattProzent / 100)) : ware.preis;
}

function kaufPreis(ware: SortimentEintrag, gratisTyp: string, verbraucht: boolean): number {
  if (!verbraucht && ersterKaufTrifft(gratisTyp, ware.typ)) return 0;
  return effektiverPreis(ware);
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
  gratisErsterKaufTyp,
  featureGenutzt,
  onFeatureVerbraucht,
  onGekauft,
  onSchliessen,
}: {
  campaignId: string;
  personId: string;
  offen: boolean;
  kapital: number;
  ausgegeben: number;
  /** Leer = kein Gratis-Erstkauf. „alle Typen“ trifft jeden Gegenstand, einmal. */
  gratisErsterKaufTyp: string;
  featureGenutzt: boolean;
  onFeatureVerbraucht: () => void;
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

  // Still nachladen wie der normale Shop (ShopSeite.tsx) — alle 5s, solange
  // offen (24.10.2026, Marks Wunsch: die SL legt waehrend des Freebees-
  // Schritts spontan etwas Neues an, kein eigener Knopf noetig).
  async function holen() {
    const h = await haendlerApi.tutorial(campaignId);
    if (!h) return { h: null as HaendlerEintrag | null, s: [] as SortimentEintrag[], g: [] as Gegenstand[] };
    const [s, g] = await Promise.all([
      haendlerApi.sortiment(campaignId, h.id),
      itemsApi.list(campaignId, personId),
    ]);
    return { h, s, g };
  }

  function anwenden(d: { h: HaendlerEintrag | null; s: SortimentEintrag[]; g: Gegenstand[] }) {
    setHaendler(d.h);
    setSortiment(d.s);
    setGekauft(d.g);
  }

  const { ungueltig } = useNachladen(holen, anwenden, {
    aktiv: offen,
    quelle: `${campaignId}:${personId}`,
  });

  async function laden() {
    ungueltig();
    const d = await holen();
    ungueltig();
    anwenden(d);
  }

  const sichtbar = sortiment.filter((w) => kategorie === null || w.typ === kategorie);
  const gewaehlt = sichtbar.find((w) => w.gegenstandId === gewaehltId) ?? sichtbar[0] ?? null;

  async function kaufen(ware: SortimentEintrag) {
    if (!haendler) return;
    setFehler(null);
    setKommentar(null);
    setKaeuft(true);
    ungueltig();
    try {
      const antwort = await haendlerApi.kaufen(campaignId, haendler.id, ware.gegenstandId, personId);
      onGekauft(antwort.kapitalNeu, antwort.tutorialAusgegeben ?? ausgegeben);
      if (!featureGenutzt && ersterKaufTrifft(gratisErsterKaufTyp, ware.typ)) onFeatureVerbraucht();
      if (!ware.istVorlage) setGewaehltId(null);
      await laden();
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

  const preis = gewaehlt ? kaufPreis(gewaehlt, gratisErsterKaufTyp, featureGenutzt) : 0;
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
                      <span className="ts-zeile-preis">
                        {kaufPreis(ware, gratisErsterKaufTyp, featureGenutzt) === 0 &&
                        ersterKaufTrifft(gratisErsterKaufTyp, ware.typ) &&
                        !featureGenutzt
                          ? "gratis"
                          : `${effektiverPreis(ware).toLocaleString("de-AT")}¥`}
                      </span>
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
                      {preis === 0 && ersterKaufTrifft(gratisErsterKaufTyp, gewaehlt.typ) && !featureGenutzt ? (
                        <>
                          <s className="ts-preis-alt">{effektiverPreis(gewaehlt).toLocaleString("de-AT")}¥</s> gratis
                        </>
                      ) : (
                        <>
                          {gewaehlt.rabattProzent > 0 && (
                            <s className="ts-preis-alt">{gewaehlt.preis.toLocaleString("de-AT")}¥</s>
                          )}
                          {preis.toLocaleString("de-AT")}¥
                        </>
                      )}
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
        onJa={async () => {
          const stueck = rueckgabe;
          setRueckgabe(null);
          setKaeuft(true);
          setFehler(null);
          ungueltig();
          try {
            const antwort = await haendlerApi.tutorialZurueck(campaignId, haendler.id, stueck.id, personId);
            onGekauft(antwort.kapitalNeu, antwort.tutorialAusgegeben ?? ausgegeben);
            await laden();
          } catch (e) {
            setFehler(e instanceof Error ? e.message : "Zurückgeben fehlgeschlagen");
          } finally {
            setKaeuft(false);
          }
        }}
      />
    )}
    </>
  );
}
