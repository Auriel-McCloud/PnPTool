import { useEffect, useState } from "react";
import { DotPool } from "./DotPool";
import { bogenApi, KATEGORIE_TITEL, type Steigerungen, type Steigerungspreis } from "./bogenApi";
import "./levelup.css";

/**
 * Erfahrung ausgeben.
 *
 * Zwei Farben tragen die ganze Ansicht: **blau, was du dir leisten kannst,
 * rot, was (noch) zu teuer ist.** Damit sieht man auf einen Blick, worauf es
 * hinausläuft, ohne Preise zu vergleichen — und wie sich der Rest verschiebt,
 * sobald man etwas kauft.
 *
 * Die Preise kommen von `traits/erfahrung.py` und werden hier **nicht**
 * nachgerechnet. Beim Kauf schickt die Ansicht nur mit, *was* gesteigert
 * werden soll; was es kostet, entscheidet der Server erneut.
 */

const REIHENFOLGE = [
  "AttributKörperlich",
  "AttributGesellschaftlich",
  "AttributGeistig",
  "Fertigkeit",
  "Arete",
  "Sphäre",
  "NeuroWeaving",
  // Hintergründe bewusst ausgelassen — die kann nach der Charaktererstellung
  // nur noch die SL vergeben, nicht der Spieler selbst steigern.
];

export function LevelUp({
  campaignId,
  personId,
  onGeaendert,
}: {
  campaignId: string;
  personId: string;
  /** Damit das Blatt die neuen Werte übernimmt, wenn man zurückwechselt. */
  onGeaendert?: () => void;
}) {
  const [stand, setStand] = useState<Steigerungen | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState<string | null>(null);

  useEffect(() => {
    bogenApi
      .preise(campaignId, personId)
      .then(setStand)
      .catch(() => setFehler("Die Steigerungspreise konnten nicht geladen werden."));
  }, [campaignId, personId]);

  async function kaufen(was: { traitDefId?: string; willenskraft?: boolean }, kennung: string) {
    setLaeuft(kennung);
    setFehler(null);
    try {
      setStand(await bogenApi.steigern(campaignId, personId, was));
      onGeaendert?.();
    } catch (e) {
      setFehler((e as Error).message || "Das hat nicht geklappt.");
    } finally {
      setLaeuft(null);
    }
  }

  if (fehler && !stand) return <p style={{ color: "var(--signal)" }}>{fehler}</p>;
  if (!stand) return <p style={{ color: "var(--text-leise)" }}>Lade Erfahrung…</p>;

  const gruppen = stand.werte.reduce<Record<string, Steigerungspreis[]>>((acc, e) => {
    (acc[e.category] ??= []).push(e);
    return acc;
  }, {});
  const kategorien = REIHENFOLGE.filter((k) => gruppen[k]?.length);

  const ausgegeben = stand.gesamt - stand.verfuegbar;

  return (
    <div className="lu-blatt">
      <header className="lu-kopf">
        <div className="lu-konto">
          <span className="lu-zahl">{stand.verfuegbar}</span>
          <span className="lu-text">
            Erfahrung frei
            <em>
              {ausgegeben} von {stand.gesamt} bereits ausgegeben
            </em>
          </span>
        </div>
        <p className="lu-hinweis">
          Blau ist bezahlbar, rot noch nicht. Jeder Punkt macht den nächsten teurer — der Preis
          richtet sich nach dem Wert, den du schon hast.
        </p>
      </header>

      {fehler && <p className="lu-fehler">{fehler}</p>}

      <div className="lu-buehne">
        {kategorien.map((kategorie) => (
          <section key={kategorie}>
            <h3 className="lu-gruppe-titel">{KATEGORIE_TITEL[kategorie] ?? kategorie}</h3>
            <div className="lu-raster">
              {gruppen[kategorie].map((e) => {
                const voll = e.aktuell >= e.max;
                const leistbar = !voll && e.kosten <= stand.verfuegbar;
                return (
                  <button
                    key={e.traitDefId}
                    type="button"
                    className={`lu-wert${leistbar ? " lu-leistbar" : ""}${voll ? " lu-voll" : ""}`}
                    onClick={() => leistbar && kaufen({ traitDefId: e.traitDefId }, e.traitDefId)}
                    disabled={!leistbar || laeuft !== null}
                    title={voll ? `${e.name} steht auf dem Maximum ${e.max}` : `${e.kosten} EP für den nächsten Punkt`}
                  >
                    <span className="lu-name">{e.name}</span>
                    <DotPool value={e.aktuell} max={e.max} />
                    <span className="lu-preis">{voll ? "max" : `${e.kosten}`}</span>
                  </button>
                );
              })}
            </div>
          </section>
        ))}

        <section>
          <h3 className="lu-gruppe-titel">Willenskraft</h3>
          <div className="lu-raster">
            <button
              type="button"
              className={`lu-wert${stand.willenskraft.kosten <= stand.verfuegbar ? " lu-leistbar" : ""}`}
              onClick={() => kaufen({ willenskraft: true }, "willenskraft")}
              disabled={stand.willenskraft.kosten > stand.verfuegbar || laeuft !== null}
              title={`${stand.willenskraft.kosten} EP für den nächsten Punkt`}
            >
              <span className="lu-name">
                Willenskraft
                <em className="lu-zusatz">steht auf {stand.willenskraft.aktuell}</em>
              </span>
              <span className="lu-preis">{stand.willenskraft.kosten}</span>
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
