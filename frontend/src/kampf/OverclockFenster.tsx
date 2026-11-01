import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { WuerfelZehn } from "../traits/WuerfelZehn";
import { MAGIE_HINWEISE, NEUROWEAVING_POOL_MAX } from "../traits/magie";
import "../traits/probe.css";

const MATRIX_AKTION = new Set(["Brute Force", "Schleichen", "Matrix-Navigation", "Electronic Warfare"]);

/**
 * Overclock als eigene Funktion, im selben Fensterformat wie die anderen
 * NeuroWeaving-Proben: Würfelzahl, W10, Willenskraft drauflegen.
 * Das Werkzeug würfelt nicht — es sagt nur, wie viele Würfel erlaubt sind.
 */
export function OverclockFenster({
  offen,
  grundwert,
  fertigkeiten,
  willenskraft,
  onSchliessen,
  onMatrix,
}: {
  offen: boolean;
  grundwert: number;
  fertigkeiten: { name: string; wert: number }[];
  willenskraft: number;
  onSchliessen: () => void;
  /** Matrix-Aktion: weiter ins Kampf-Fenster, Pool schon mit Overclock. */
  onMatrix: (name: string, pool: number) => void;
}) {
  const [wild, setWild] = useState(0);
  const [skill, setSkill] = useState<string | null>(null);

  useEffect(() => {
    if (!offen) return;
    setWild(0);
    setSkill(null);
  }, [offen]);

  const gewaehlt = fertigkeiten.find((f) => f.name === skill) ?? null;
  const roh = gewaehlt ? grundwert + gewaehlt.wert + wild : 0;
  const gedeckelt = Boolean(gewaehlt) && roh > NEUROWEAVING_POOL_MAX;
  const pool = gedeckelt ? NEUROWEAVING_POOL_MAX : roh;

  return (
    <Fenster
      offen={offen}
      titel="Overclock"
      unterzeile="Willenskraft auf eine Aktion"
      kennung="overclock"
      onSchliessen={onSchliessen}
    >
      <div className="pr-pool">
        <span className="pr-zahl">{gewaehlt ? pool : "–"}</span>
        <WuerfelZehn groesse={54} />
      </div>
      <p className="pr-rechnung">
        {gewaehlt
          ? `NeuroWeaving ${grundwert} + ${gewaehlt.name} ${gewaehlt.wert}${
              wild > 0 ? ` + ${wild} aus Willenskraft` : ""
            }${gedeckelt ? ` — gedeckelt auf ${NEUROWEAVING_POOL_MAX}` : ""}`
          : "Wähle eine Aktion. Overclock legt Willenskraft als Bonuswürfel drauf."}
      </p>

      {willenskraft > 0 ? (
        <section className="pr-wild">
          <h3>Overclock</h3>
          <p className="pr-regel">{MAGIE_HINWEISE.overclock}</p>
          <div className="pr-wild-reihe">
            <button type="button" onClick={() => setWild((w) => Math.max(0, w - 1))} disabled={wild === 0}>
              −
            </button>
            <span className="pr-wild-zahl">
              {wild} <em>von {willenskraft}</em>
            </span>
            <button
              type="button"
              onClick={() => setWild((w) => Math.min(willenskraft, w + 1))}
              disabled={wild >= willenskraft}
            >
              +
            </button>
          </div>
          {wild > 0 && <p className="pr-warnung">{MAGIE_HINWEISE.overclockRueckstoss}</p>}
        </section>
      ) : (
        <p className="pr-regel">Ohne Willenskraft kein Overclock.</p>
      )}

      <section>
        <h3 className="pr-spalte-titel" style={{ "--cb-ton": "var(--wert-neuroweaving)" } as React.CSSProperties}>
          Aktion
        </h3>
        {fertigkeiten.map((f) => {
          const summe = Math.min(NEUROWEAVING_POOL_MAX, grundwert + f.wert + wild);
          const aktiv = skill === f.name;
          return (
            <button
              key={f.name}
              type="button"
              className="pr-attribut"
              data-gewaehlt={aktiv}
              style={{ "--cb-ton": "var(--wert-neuroweaving)" } as React.CSSProperties}
              onClick={() => setSkill(f.name)}
            >
              <span className="pr-attribut-name">{f.name}</span>
              <span className="pr-attribut-summe" style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                {summe}
                <WuerfelZehn groesse={15} />
              </span>
            </button>
          );
        })}
      </section>

      {gewaehlt && MATRIX_AKTION.has(gewaehlt.name) && (
        <button type="button" className="kk-treffer-knopf" onClick={() => onMatrix(gewaehlt.name, pool)}>
          Zum Ziel
        </button>
      )}
    </Fenster>
  );
}
