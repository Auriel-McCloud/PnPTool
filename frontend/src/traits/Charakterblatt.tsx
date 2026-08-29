import { useEffect, useMemo, useState } from "react";
import { DotPool } from "./DotPool";
import { Kaestchen } from "./Kaestchen";
import { ATTRIBUT_KATEGORIEN, bogenApi, KATEGORIE_TITEL, type Bogen } from "./bogenApi";
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
  onWertGewaehlt,
}: {
  campaignId: string;
  personId: string;
  /** Antippen einer Fähigkeit — für die spätere Probenrechnung. */
  onWertGewaehlt?: (name: string, wert: number, kategorie: string) => void;
}) {
  const [bogen, setBogen] = useState<Bogen | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);

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
        <div className="cb-werte">
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
          <span className="cb-spur-titel">Gesundheit</span>
          <Kaestchen max={u.gesundheitMax} verbraucht={u.gesundheitSchaden} ton="#ff4d6b" />
        </div>
        <div className="cb-spur">
          <span className="cb-spur-titel">Willenskraft</span>
          <Kaestchen max={u.willenskraftMax} verbraucht={u.willenskraftVerbraucht} ton="#ffb648" />
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

      <div className="cb-attribute">{ATTRIBUT_KATEGORIEN.map(reihe)}</div>
      {reihe("Arete")}
      {reihe("Sphäre")}
      {reihe("NeuroWeaving")}
      {reihe("Fertigkeit")}
    </div>
  );
}
