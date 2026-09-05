import { useEffect, useState, useMemo } from "react";
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
 * Käufe werden lokal gesammelt und erst bei "Speichern" ans Backend geschickt.
 * "Zurücksetzen" verwirft alle lokalen Änderungen.
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

// Preisberechnung (gespiegelt aus backend/app/traits/erfahrung.py)
const FAKTOR: Record<string, number> = {
  AttributKörperlich: 4,
  AttributGesellschaftlich: 4,
  AttributGeistig: 4,
  Fertigkeit: 2,
  Sphäre: 2,
  Arete: 4,
  NeuroWeavingWert: 4,
  NeuroWeaving: 2,
  Hintergrund: 3,
};

const NEU_KOSTEN: Record<string, number> = {
  Fertigkeit: 3,
  Sphäre: 3,
  Arete: 5,
  NeuroWeavingWert: 5,
  NeuroWeaving: 3,
  Hintergrund: 3,
};

function berechneKosten(kategorie: string, von: number): number | null {
  if (von <= 0) return NEU_KOSTEN[kategorie] ?? null;
  const faktor = FAKTOR[kategorie];
  return faktor != null ? von * faktor : null;
}

function berechneKostenWillenskraft(von: number): number {
  return Math.max(1, von);
}

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
  // Original-Stand vom Server
  const [original, setOriginal] = useState<Steigerungen | null>(null);
  // Lokale Änderungen: traitDefId -> Anzahl gekaufter Punkte
  const [kaeufe, setKaeufe] = useState<Record<string, number>>({});
  const [willenskraftKaeufe, setWillenskraftKaeufe] = useState(0);

  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  useEffect(() => {
    bogenApi
      .preise(campaignId, personId)
      .then((daten) => {
        setOriginal(daten);
        setKaeufe({});
        setWillenskraftKaeufe(0);
      })
      .catch(() => setFehler("Die Steigerungspreise konnten nicht geladen werden."));
  }, [campaignId, personId]);

  // Berechne den lokalen Stand basierend auf Original + Käufe
  const stand = useMemo(() => {
    if (!original) return null;

    // Berechne wie viel EP durch lokale Käufe ausgegeben wurden
    let lokalAusgegeben = 0;

    // Für jeden Kauf die Kosten berechnen
    for (const [traitDefId, anzahl] of Object.entries(kaeufe)) {
      const eintrag = original.werte.find((e) => e.traitDefId === traitDefId);
      if (!eintrag) continue;
      for (let i = 0; i < anzahl; i++) {
        const kosten = berechneKosten(eintrag.category, eintrag.aktuell + i);
        if (kosten != null) lokalAusgegeben += kosten;
      }
    }

    // Willenskraft-Käufe
    for (let i = 0; i < willenskraftKaeufe; i++) {
      lokalAusgegeben += berechneKostenWillenskraft(original.willenskraft.aktuell + i);
    }

    // Aktualisierte Werte mit lokalen Käufen
    const werte = original.werte.map((e) => {
      const gekauft = kaeufe[e.traitDefId] ?? 0;
      const neuerWert = e.aktuell + gekauft;
      const neueKosten = berechneKosten(e.category, neuerWert);
      return {
        ...e,
        aktuell: neuerWert,
        kosten: neueKosten ?? e.kosten,
      };
    });

    const willenskraftNeu = original.willenskraft.aktuell + willenskraftKaeufe;

    return {
      gesamt: original.gesamt,
      verfuegbar: original.verfuegbar - lokalAusgegeben,
      werte,
      willenskraft: {
        aktuell: willenskraftNeu,
        kosten: berechneKostenWillenskraft(willenskraftNeu),
      },
    };
  }, [original, kaeufe, willenskraftKaeufe]);

  const hatAenderungen = Object.keys(kaeufe).length > 0 || willenskraftKaeufe > 0;

  function kaufen(traitDefId: string) {
    setKaeufe((prev) => ({
      ...prev,
      [traitDefId]: (prev[traitDefId] ?? 0) + 1,
    }));
  }

  function kaufenWillenskraft() {
    setWillenskraftKaeufe((prev) => prev + 1);
  }

  function zuruecksetzen() {
    setKaeufe({});
    setWillenskraftKaeufe(0);
    setFehler(null);
  }

  async function speichern() {
    if (!hatAenderungen) return;
    setLaeuft(true);
    setFehler(null);

    try {
      // Alle Käufe sequentiell ans Backend schicken
      for (const [traitDefId, anzahl] of Object.entries(kaeufe)) {
        for (let i = 0; i < anzahl; i++) {
          await bogenApi.steigern(campaignId, personId, { traitDefId });
        }
      }
      for (let i = 0; i < willenskraftKaeufe; i++) {
        await bogenApi.steigern(campaignId, personId, { willenskraft: true });
      }

      // Neuen Stand vom Server holen
      const neuerStand = await bogenApi.preise(campaignId, personId);
      setOriginal(neuerStand);
      setKaeufe({});
      setWillenskraftKaeufe(0);
      onGeaendert?.();
    } catch (e) {
      setFehler((e as Error).message || "Das Speichern hat nicht geklappt.");
    } finally {
      setLaeuft(false);
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
        <div className="lu-aktionen">
          {hatAenderungen && (
            <>
              <button
                type="button"
                className="lu-btn lu-btn-speichern"
                onClick={speichern}
                disabled={laeuft}
              >
                {laeuft ? "Speichert…" : "✓ Speichern"}
              </button>
              <button
                type="button"
                className="lu-btn lu-btn-zurueck"
                onClick={zuruecksetzen}
                disabled={laeuft}
              >
                ✗ Zurücksetzen
              </button>
            </>
          )}
        </div>
      </header>

      <p className="lu-hinweis">
        Blau ist bezahlbar, rot noch nicht. Klicke um Punkte zu vergeben — erst "Speichern"
        macht die Änderung endgültig.
      </p>

      {fehler && <p className="lu-fehler">{fehler}</p>}

      <div className="lu-buehne">
        {kategorien.map((kategorie) => (
          <section key={kategorie}>
            <h3 className="lu-gruppe-titel">{KATEGORIE_TITEL[kategorie] ?? kategorie}</h3>
            <div className="lu-raster">
              {gruppen[kategorie].map((e) => {
                const voll = e.aktuell >= e.max;
                const leistbar = !voll && e.kosten <= stand.verfuegbar;
                const geaendert = (kaeufe[e.traitDefId] ?? 0) > 0;
                return (
                  <button
                    key={e.traitDefId}
                    type="button"
                    className={`lu-wert${leistbar ? " lu-leistbar" : ""}${voll ? " lu-voll" : ""}${geaendert ? " lu-geaendert" : ""}`}
                    onClick={() => leistbar && kaufen(e.traitDefId)}
                    disabled={!leistbar || laeuft}
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
              className={`lu-wert${stand.willenskraft.kosten <= stand.verfuegbar ? " lu-leistbar" : ""}${willenskraftKaeufe > 0 ? " lu-geaendert" : ""}`}
              onClick={() => stand.willenskraft.kosten <= stand.verfuegbar && kaufenWillenskraft()}
              disabled={stand.willenskraft.kosten > stand.verfuegbar || laeuft}
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
