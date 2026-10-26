import { useEffect, useState } from "react";
import { DotPool } from "../traits/DotPool";
import { KATEGORIE_TITEL } from "../traits/bogenApi";
import "../traits/levelup.css";
import { drohnenApi, type DrohnenSteigerungspreise, type DrohnenPreisEintrag } from "./api";

/**
 * Nuyen statt EP: Kauf-Ansicht für Drohnen-/Fahrzeug-Attribute und
 * -Fertigkeiten, Pendant zu `traits/LevelUp.tsx`.
 *
 * Bewusst KEIN lokales Sammeln mehrerer Käufe vor dem Speichern (anders als
 * LevelUp) — ein Drohnen-Kauf ist seltener als Charakter-Leveln, und jeder
 * Kauf muss ohnehin sofort den Rigger-Kapitalstand neu ziehen, den ein
 * zweiter gleichzeitiger Kauf sonst falsch anzeigen würde. Sofort-Kauf per
 * Klick ist hier einfacher UND korrekter.
 */
const REIHENFOLGE = ["AttributDrohne", "AttributDrohneAussenhuelle", "Fertigkeit"];

export function DrohnenSteigern({
  campaignId,
  drohneId,
  onGeaendert,
}: {
  campaignId: string;
  drohneId: string;
  onGeaendert?: () => void;
}) {
  const [stand, setStand] = useState<DrohnenSteigerungspreise | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [kauftGerade, setKauftGerade] = useState<string | null>(null);

  function laden() {
    drohnenApi
      .steigerungspreise(campaignId, drohneId)
      .then(setStand)
      .catch(() => setFehler("Die Preise konnten nicht geladen werden."));
  }

  useEffect(laden, [campaignId, drohneId]);

  async function kaufen(traitDefId: string) {
    setKauftGerade(traitDefId);
    setFehler(null);
    try {
      await drohnenApi.steigern(campaignId, drohneId, traitDefId);
      laden();
      onGeaendert?.();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Der Kauf hat nicht geklappt.");
    } finally {
      setKauftGerade(null);
    }
  }

  if (fehler && !stand) return <p style={{ color: "var(--signal)" }}>{fehler}</p>;
  if (!stand) return <p style={{ color: "var(--text-leise)" }}>Lade Preise…</p>;

  if (!stand.riggerId) {
    return (
      <p style={{ color: "var(--text-leise)" }}>
        Ohne gebundenen Rigger kann hier nichts gekauft werden — zuerst unten einen Rigger zuweisen.
      </p>
    );
  }

  const gruppen = stand.werte.reduce<Record<string, DrohnenPreisEintrag[]>>((acc, e) => {
    (acc[e.category] ??= []).push(e);
    return acc;
  }, {});
  const kategorien = REIHENFOLGE.filter((k) => gruppen[k]?.length);

  return (
    <div className="lu-blatt">
      <header className="lu-kopf">
        <div className="lu-konto">
          <span className="lu-zahl">{stand.verfuegbar}¥</span>
          <span className="lu-text">
            Kapital des Riggers
            <em>bezahlt wird nicht aus einem eigenen Konto der Drohne</em>
          </span>
        </div>
      </header>

      <p className="lu-hinweis">Klicke einen Wert, um ihn sofort aus dem Rigger-Kapital zu kaufen.</p>

      {fehler && <p className="lu-fehler">{fehler}</p>}

      <div className="lu-buehne">
        {kategorien.map((kategorie) => (
          <section key={kategorie}>
            <h3 className="lu-gruppe-titel">{KATEGORIE_TITEL[kategorie] ?? kategorie}</h3>
            <div className="lu-raster">
              {gruppen[kategorie].map((e) => {
                const voll = e.aktuell >= e.max;
                const leistbar = !voll && e.kosten <= stand.verfuegbar;
                const laedt = kauftGerade === e.traitDefId;
                return (
                  <button
                    key={e.traitDefId}
                    type="button"
                    className={`lu-wert${leistbar ? " lu-leistbar" : ""}${voll ? " lu-voll" : ""}`}
                    onClick={() => leistbar && !laedt && kaufen(e.traitDefId)}
                    disabled={!leistbar || laedt || Boolean(kauftGerade)}
                    title={voll ? `${e.name} steht auf dem Maximum ${e.max}` : `${e.kosten}¥ für den nächsten Punkt`}
                  >
                    <span className="lu-name">{e.name}</span>
                    <DotPool value={e.aktuell} max={e.max} />
                    <span className="lu-preis">{voll ? "max" : laedt ? "…" : `${e.kosten}¥`}</span>
                  </button>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
