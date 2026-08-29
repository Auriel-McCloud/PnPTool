import { useEffect, useMemo, useState } from "react";
import { DotPool } from "./DotPool";
import { Kaestchen } from "./Kaestchen";
import { ATTRIBUT_KATEGORIEN, bogenApi, KATEGORIE_TITEL, type Bogen, type BogenUebersicht } from "./bogenApi";
import type { TraitDef } from "./api";
import "./charakterblatt.css";

/** Farbe je Wertegruppe — dieselbe Sprache wie die Bereichsfarben der Hülle. */
const TON: Record<string, string> = {
  AttributKörperlich: "#ff6b4d",
  AttributGesellschaftlich: "#ffb648",
  AttributGeistig: "#4d8bd8",
  Fertigkeit: "#00e5ff",
  Arete: "#c76bff",
  Sphäre: "#a865d8",
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
  onWertGewaehlt,
}: {
  campaignId: string;
  personId: string;
  /** Schaden und Verbrauch eintragen. Werte bleiben in jedem Fall gesperrt. */
  aenderbar?: boolean;
  /** Antippen einer Fähigkeit — für die spätere Probenrechnung. */
  onWertGewaehlt?: (name: string, wert: number, kategorie: string) => void;
}) {
  const [bogen, setBogen] = useState<Bogen | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);

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

  useEffect(() => {
    bogenApi
      .laden(campaignId, personId)
      .then(setBogen)
      .catch(() => setFehler("Das Charakterblatt konnte nicht geladen werden."));
  }, [campaignId, personId]);

  // Gesetzte Werte nachschlagbar machen; der Katalog gibt die Reihenfolge vor,
  // damit auch ungesetzte Werte mit 0 erscheinen statt zu fehlen.
  const werte = useMemo(() => {
    const m = new Map<string, number>();
    bogen?.werte.forEach((w) => m.set(w.traitDefId, w.rating));
    return m;
  }, [bogen]);

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

  function reihe(kategorie: string) {
    const eintraege = gruppen.get(kategorie);
    if (!eintraege?.length) return null;
    const ton = TON[kategorie] ?? "var(--neon)";
    return (
      <section className="cb-gruppe" key={kategorie} style={{ "--cb-ton": ton } as React.CSSProperties}>
        <h3 className="cb-gruppe-titel">{KATEGORIE_TITEL[kategorie] ?? kategorie}</h3>
        <div
          className="cb-werte"
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
              <button
                key={t.id}
                type="button"
                className="cb-wert"
                onClick={() => onWertGewaehlt?.(t.name, wert, kategorie)}
                disabled={!onWertGewaehlt}
                title={onWertGewaehlt ? `${t.name} würfeln` : t.name}
              >
                <span className="cb-wert-name">{t.name}</span>
                <DotPool value={wert} max={t.defaultMax} onChange={undefined} />
              </button>
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
        <div className="cb-erfahrung" title="Erfahrungspunkte">
          <span className="cb-ep-zahl">{u.erfahrungVerfuegbar}</span>
          <span className="cb-ep-text">von {u.erfahrungGesamt} EP frei</span>
        </div>
      </header>

      <section className="cb-zustand">
        <div className="cb-spur">
          <span className="cb-spur-titel">
            Gesundheit
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
          <span className="cb-spur-titel">Willenskraft</span>
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
            {u.offline && <span className="cb-offline">offline</span>}
          </span>
          {u.offline ? (
            <span className="cb-hinweis">Kein Commlink — nicht erreichbar, aber auch nicht angreifbar.</span>
          ) : (
            <Kaestchen max={u.iceMax} verbraucht={u.iceSchaden} ton="#35e0d0" />
          )}
        </div>
        <div className="cb-spur">
          <span className="cb-spur-titel">Initiative</span>
          <span className="cb-initiative">{u.initiative}</span>
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
