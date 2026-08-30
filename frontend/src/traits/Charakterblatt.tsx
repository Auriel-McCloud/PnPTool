import { useEffect, useMemo, useState } from "react";
import { Charaktererstellung } from "./Charaktererstellung";
import { InfoTipp } from "../regeln/InfoTipp";
import { schluessel } from "../regeln/erklaerungen";
import { LevelUp } from "./LevelUp";
import { Probe, type ProbeWahl } from "./Probe";
import { DotPool } from "./DotPool";
import { WuerfelZehn } from "./WuerfelZehn";
import { Kaestchen } from "./Kaestchen";
import { ATTRIBUT_KATEGORIEN, bogenApi, KATEGORIE_TITEL, type Bogen, type BogenUebersicht } from "./bogenApi";
import { traitsApi, type TraitDef } from "./api";
import "./charakterblatt.css";

/** Farbe je Wertegruppe — dieselbe Sprache wie die Bereichsfarben der Hülle. */
const TON: Record<string, string> = {
  AttributKörperlich: "#ff6b4d",
  AttributGesellschaftlich: "#ffb648",
  AttributGeistig: "#4d8bd8",
  Fertigkeit: "#00e5ff",
  Arete: "#c76bff",
  Sphäre: "#a865d8",
  NeuroWeavingWert: "#3ddc84",
  NeuroWeaving: "#3ddc84",
};

const WEG_TITEL: Record<string, string> = {
  KEINER: "",
  MAGIER: "Magier",
  TECHNOMANCER: "Technomancer",
};

/**
 * Das Charakterblatt — Hauptansicht des Spielers.
 *
 * **Nur lesend.** Werte ändert die Spielleitung, später der Level-Up-Modus.
 * Der Aufbau richtet sich nach dem eingeschlagenen Weg: der Katalog kommt
 * bereits gefiltert vom Server, wer kein Magier ist bekommt Sphären und Arete
 * also gar nicht erst geliefert.
 */
export function Charakterblatt({
  campaignId,
  personId,
  aenderbar = true,
  bearbeitbar = false,
  onWertGewaehlt,
}: {
  campaignId: string;
  personId: string;
  /** Schaden und Verbrauch eintragen. Werte bleiben in jedem Fall gesperrt. */
  aenderbar?: boolean;
  /**
   * Zeigt der Spielleitung einen Schalter, mit dem sie die Werte im selben
   * Blatt ändern kann. Ein zweites, anders aufgebautes Formular daneben hat
   * Mark zurecht als unübersichtlich empfunden — dasselbe Blatt, nur mit
   * anklickbaren Punkten, ist leichter zu lesen.
   */
  bearbeitbar?: boolean;
  /** Antippen einer Fähigkeit — für die spätere Probenrechnung. */
  onWertGewaehlt?: (name: string, wert: number, kategorie: string) => void;
}) {
  const [bogen, setBogen] = useState<Bogen | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  // Drei Ansichten desselben Blatts (docs/ui-konzept.md): Erstellung einmalig,
  // dann die Spielansicht, und das Ausgeben von Erfahrung bei Bedarf.
  const [ansicht, setAnsicht] = useState<"blatt" | "levelup">("blatt");
  const [bearbeiten, setBearbeiten] = useState(false);
  // Erhöhtes Maximum für einzelne Werte (eine Elder-NPC bei Schusswaffen 8).
  // Nur im Bearbeiten-Modus sichtbar — Spieler sollen davon nichts sehen.
  const [maximaZeigen, setMaximaZeigen] = useState(false);
  // Angetippter Wert: dafür geht die Rechenhilfe auf (Fertigkeit → Attribut
  // → Würfelzahl). Gewürfelt wird am Tisch, nicht hier.
  const [probe, setProbe] = useState<ProbeWahl | null>(null);

  /** Übernimmt die vom Server gerechnete Übersicht (Deckelung inbegriffen). */
  function uebernehmen(u: BogenUebersicht) {
    setBogen((alt) => (alt ? { ...alt, uebersicht: u } : alt));
  }

  /**
   * Klick auf ein Gesundheitskästchen schaltet die Schadensart weiter:
   * unbeschädigt → Schlag → schwer → aggraviert → wieder frei.
   *
   * Gerechnet wird über die Anzahl je Art, nicht über einzelne Kästchen —
   * so bleibt die Reihenfolge (schwerer Schaden links) von selbst erhalten.
   */
  async function schadenWeiterschalten(index: number) {
    if (!bogen || !aenderbar) return;
    const u = bogen.uebersicht;
    const { schadenAggraviert: agg, schadenSchwer: schwer, schadenSchlag: schlag } = u;

    let neu = { schadenAggraviert: agg, schadenSchwer: schwer, schadenSchlag: schlag };
    if (index < agg) {
      // aggraviert → wieder heil
      neu = { ...neu, schadenAggraviert: agg - 1 };
    } else if (index < agg + schwer) {
      neu = { ...neu, schadenSchwer: schwer - 1, schadenAggraviert: agg + 1 };
    } else if (index < agg + schwer + schlag) {
      neu = { ...neu, schadenSchlag: schlag - 1, schadenSchwer: schwer + 1 };
    } else {
      neu = { ...neu, schadenSchlag: schlag + 1 };
    }
    uebernehmen(await bogenApi.zustand(campaignId, personId, neu));
  }

  async function willenskraftWeiterschalten(index: number) {
    if (!bogen || !aenderbar) return;
    const u = bogen.uebersicht;
    // Verbraucht wird von rechts, frei gemacht von links — ein Klick auf ein
    // freies Feld verbraucht, einer auf ein verbrauchtes gibt zurück.
    const verbraucht = index < u.willenskraftMax - u.willenskraftVerbraucht ? u.willenskraftVerbraucht + 1 : u.willenskraftVerbraucht - 1;
    uebernehmen(
      await bogenApi.zustand(campaignId, personId, {
        willenskraftVerbraucht: Math.max(0, Math.min(verbraucht, u.willenskraftMax)),
      }),
    );
  }

  /**
   * Einen Wert setzen. Der Server rechnet die abgeleiteten Grössen neu, also
   * wird das ganze Blatt nachgeladen — Gesundheit hängt an der
   * Widerstandsfähigkeit, Willenskraft an zwei anderen Attributen.
   */
  async function wertSetzen(traitDefId: string, wert: number, maxOverride: number | null) {
    await traitsApi.setWert(campaignId, personId, traitDefId, wert, maxOverride);
    await neuLaden();
  }

  function neuLaden() {
    return bogenApi
      .laden(campaignId, personId)
      .then(setBogen)
      .catch(() => setFehler("Das Charakterblatt konnte nicht geladen werden."));
  }

  useEffect(() => {
    neuLaden();
  }, [campaignId, personId]);

  // Gesetzte Werte nachschlagbar machen; der Katalog gibt die Reihenfolge vor,
  // damit auch ungesetzte Werte mit 0 erscheinen statt zu fehlen.
  const werte = useMemo(() => {
    const m = new Map<string, number>();
    bogen?.werte.forEach((w) => m.set(w.traitDefId, w.rating));
    return m;
  }, [bogen]);

  /** Wirksames Maximum: was der Spielleiter gesetzt hat, sonst der Katalogwert. */
  function grenzeVon(t: TraitDef) {
    return bogen?.werte.find((w) => w.traitDefId === t.id)?.max ?? t.defaultMax;
  }

  const gruppen = useMemo(() => {
    const g = new Map<string, TraitDef[]>();
    bogen?.katalog.forEach((t) => {
      if (!g.has(t.category)) g.set(t.category, []);
      g.get(t.category)!.push(t);
    });
    return g;
  }, [bogen]);

  if (fehler) return <p style={{ color: "var(--signal)" }}>{fehler}</p>;
  if (!bogen) return <p style={{ color: "var(--text-leise)" }}>Lade Charakterblatt…</p>;

  const u = bogen.uebersicht;

  // Vor der Erstellung gibt es kein Blatt zu zeigen — dann führt der Ablauf
  // durch die Erstellung, und danach steht das fertige Blatt da.
  if (!u.erstellungAbgeschlossen) {
    return (
      <Charaktererstellung
        campaignId={campaignId}
        personId={personId}
        name={bogen.person.name}
        onFertig={neuLaden}
      />
    );
  }

  if (ansicht === "levelup") {
    return (
      <div className="cb-blatt">
        <header className="cb-kopf">
          <div>
            <h2 className="cb-name">{bogen.person.name}</h2>
            <div className="cb-untertitel">Level Up</div>
          </div>
          <button type="button" onClick={() => { setAnsicht("blatt"); neuLaden(); }}>
            Zurück zum Blatt
          </button>
        </header>
        <LevelUp campaignId={campaignId} personId={personId} />
      </div>
    );
  }

  function reihe(kategorie: string) {
    const eintraege = gruppen.get(kategorie);
    if (!eintraege?.length) return null;
    const ton = TON[kategorie] ?? "var(--neon)";
    return (
      <section className="cb-gruppe" key={kategorie} style={{ "--cb-ton": ton } as React.CSSProperties}>
        <h3 className="cb-gruppe-titel">{KATEGORIE_TITEL[kategorie] ?? kategorie}</h3>
        <div
          className={eintraege.length === 1 ? "cb-werte cb-werte-einzeln" : "cb-werte"}
          // Spaltenweise füllen wie auf dem Papierblatt: die ersten zehn
          // Fähigkeiten stehen dort untereinander in der ersten Spalte
          // (körperlich), die nächsten zehn in der zweiten (gesellschaftlich)
          // und so fort — passend zu den Attributspalten darüber. Zeilenweise
          // gefüllt ginge diese thematische Zuordnung verloren.
          style={{ "--cb-zeilen": Math.ceil(eintraege.length / 3) } as React.CSSProperties}
        >
          {eintraege.map((t) => {
            const wert = werte.get(t.id) ?? 0;
            return (
              // Umhüllung, weil das Erklärungszeichen selbst ein Knopf ist
              // und nicht in der Wertezeile stecken darf — ein Knopf im Knopf
              // ist ungültig und macht beide unbedienbar.
              <div key={t.id} className="cb-wert-zeile">
                {bearbeiten ? (
                  // Im Bearbeiten-Modus keine Schaltfläche: die Punkte selbst
                  // sind anklickbar, ein Knopf darum herum finge den Klick ab.
                  <div className="cb-wert cb-wert-bearbeiten">
                    <span className="cb-wert-name">{t.name}</span>
                    <DotPool
                      value={wert}
                      max={grenzeVon(t)}
                      onChange={(neu) => wertSetzen(t.id, Math.max(0, neu), null)}
                    />
                  </div>
                ) : (
                  <button
                    type="button"
                    className="cb-wert"
                    onClick={() =>
                      onWertGewaehlt
                        ? onWertGewaehlt(t.name, wert, kategorie)
                        : setProbe({ name: t.name, wert, kategorie })
                    }
                    title={`${t.name} — wie viele Würfel?`}
                  >
                    <span className="cb-wert-name">{t.name}</span>
                    <DotPool value={wert} max={t.defaultMax} onChange={undefined} />
                  </button>
                )}
                {bearbeiten && maximaZeigen && (
                  <span className="cb-maxknoepfe">
                    <button
                      type="button"
                      onClick={() => wertSetzen(t.id, wert, Math.max(1, grenzeVon(t) - 1))}
                      title={`Maximum von ${t.name} senken`}
                    >
                      −
                    </button>
                    <span className="cb-maxzahl">{grenzeVon(t)}</span>
                    <button
                      type="button"
                      onClick={() => wertSetzen(t.id, wert, grenzeVon(t) + 1)}
                      title={`Maximum von ${t.name} anheben`}
                    >
                      +
                    </button>
                  </span>
                )}
                <InfoTipp campaignId={campaignId} schluessel={schluessel.trait(t.name)} titel={t.name} />
              </div>
            );
          })}
        </div>
      </section>
    );
  }

  return (
    <div className="cb-blatt">
      <header className="cb-kopf">
        <div>
          <h2 className="cb-name">{bogen.person.name}</h2>
          <div className="cb-untertitel">
            {[u.rasse, WEG_TITEL[u.weg]].filter(Boolean).join(" · ") || "Ohne besonderen Weg"}
          </div>
        </div>
        {bearbeitbar && (
          <div className="cb-werkzeuge">
            <button
              type="button"
              data-aktiv={bearbeiten}
              onClick={() => setBearbeiten((b) => !b)}
              title="Werte im Blatt ändern"
            >
              {bearbeiten ? "Fertig" : "⚙ Bearbeiten"}
            </button>
            {bearbeiten && (
              <button
                type="button"
                data-aktiv={maximaZeigen}
                onClick={() => setMaximaZeigen((m) => !m)}
                title="Obergrenzen einzelner Werte anheben oder senken"
              >
                Maxima
              </button>
            )}
          </div>
        )}
        <button
          type="button"
          className="cb-erfahrung"
          onClick={() => setAnsicht("levelup")}
          disabled={!aenderbar}
          title={aenderbar ? "Erfahrung ausgeben" : "Erfahrungspunkte"}
        >
          <span className="cb-ep-zahl">{u.erfahrungVerfuegbar}</span>
          <span className="cb-ep-text">von {u.erfahrungGesamt} EP frei</span>
        </button>
      </header>

      <Probe
        wahl={probe}
        katalog={bogen.katalog}
        werte={werte}
        // Wilde Magie reicht bis zur Höhe der Willenskraft — die verbrauchte
        // zählt dabei nicht mit, es geht um den Gesamtwert.
        willenskraft={u.willenskraftMax}
        deckBoni={bogen.deckBoni}
        onSchliessen={() => setProbe(null)}
      />

      {/* Kopfzeile des Papierblatts. Erscheint nur, was ausgefüllt ist —
          ein Raster leerer Beschriftungen sagt niemandem etwas. */}
      {[u.konzept, u.ambition, u.verlangen, u.ziel].some(Boolean) && (
        <section className="cb-person">
          {u.konzept && <Steckbrief titel="Konzept" text={u.konzept} />}
          {u.ambition && <Steckbrief titel="Ambition" text={u.ambition} />}
          {u.verlangen && <Steckbrief titel="Verlangen" text={u.verlangen} />}
          {u.ziel && <Steckbrief titel="Ziel" text={u.ziel} />}
          {(u.kapital > 0 || u.schulden > 0) && (
            <Steckbrief
              titel="Kapital"
              text={
                `${u.kapital.toLocaleString("de-AT")}¥` +
                (u.schulden > 0 ? ` · davon ${u.schulden.toLocaleString("de-AT")}¥ Schulden` : "")
              }
            />
          )}
        </section>
      )}

      <section className="cb-zustand">
        <div className="cb-spur">
          <span className="cb-spur-titel">
            Gesundheit
            <InfoTipp campaignId={campaignId} schluessel={schluessel.bogen("gesundheit")} titel="Gesundheit" />
            {aenderbar && <span className="cb-tipp">antippen: / → X → ✳</span>}
          </span>
          <Kaestchen
            max={u.gesundheitMax}
            schaden={{
              schlag: u.schadenSchlag,
              schwer: u.schadenSchwer,
              aggraviert: u.schadenAggraviert,
            }}
            ton="#ff4d6b"
            onKlick={aenderbar ? schadenWeiterschalten : undefined}
          />
        </div>
        <div className="cb-spur">
          <span className="cb-spur-titel">
            Willenskraft
            <InfoTipp campaignId={campaignId} schluessel={schluessel.bogen("willenskraft")} titel="Willenskraft" />
          </span>
          <Kaestchen
            max={u.willenskraftMax}
            verbraucht={u.willenskraftVerbraucht}
            ton="#ffb648"
            onKlick={aenderbar ? willenskraftWeiterschalten : undefined}
          />
        </div>
        <div className="cb-spur">
          <span className="cb-spur-titel">
            I.C.E.
            <InfoTipp campaignId={campaignId} schluessel={schluessel.bogen("ice")} titel="I.C.E. (Cyber Wall)" />
            {u.offline && <span className="cb-offline">offline</span>}
          </span>
          {u.offline ? (
            <span className="cb-hinweis">Kein Commlink — nicht erreichbar, aber auch nicht angreifbar.</span>
          ) : (
            <Kaestchen max={u.iceMax} verbraucht={u.iceSchaden} ton="#35e0d0" />
          )}
        </div>
        <div className="cb-spur">
          <span className="cb-spur-titel">
            Initiative
            <InfoTipp campaignId={campaignId} schluessel={schluessel.bogen("initiative")} titel="Initiative" />
          </span>
          {/* Die Zahl ist eine Wuerfelmenge, kein Wert — ohne das Symbol
              liest sich "7" wie eine Initiative von 7. */}
          <span className="cb-initiative">
            {u.initiative}
            <WuerfelZehn groesse={18} />
          </span>
        </div>
      </section>

      {/* Gemeinsamer Teil zuerst — so sieht das Blatt für alle gleich aus.
          Was nur Magier oder Technomancer haben, kommt darunter. */}
      <div className="cb-attribute">{ATTRIBUT_KATEGORIEN.map(reihe)}</div>
      {reihe("Fertigkeit")}
      {reihe("Arete")}
      {reihe("Sphäre")}
      {reihe("NeuroWeaving")}
    </div>
  );
}

/** Ein beschriftetes Textfeld aus der Kopfzeile des Papierblatts. */
function Steckbrief({ titel, text }: { titel: string; text: string }) {
  return (
    <div className="cb-steckbrief">
      <span className="cb-steckbrief-titel">{titel}</span>
      <span className="cb-steckbrief-text">{text}</span>
    </div>
  );
}
