import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import { WuerfelZehn } from "./WuerfelZehn";
import type { TraitDef } from "./api";
import { MAGIE_HINWEISE, SPHAEREN, SPHAEREN_STUFEN } from "./magie";
import "./probe.css";

/**
 * Wieviele Würfel? — die Rechenhilfe zur Probe.
 *
 * **Das Werkzeug würfelt nicht.** Gewürfelt wird am Tisch, mit echten Würfeln;
 * hier steht nur, wie viele man nehmen darf. Marks Vorgabe: eine Erleichterung,
 * kein Ersatz. (Ein Schalter, der das Würfeln doch erlaubt, ist als Idee
 * notiert — er zöge nach sich, dass Spielleitung und Mitspieler die Ergebnisse
 * sehen müssten, und das ist eine eigene Runde wert.)
 *
 * Zwei Fenster übereinander, wie im UI-Konzept: Fertigkeit antippen → womit?
 * → so viele Würfel.
 */

/** Reihenfolge und Beschriftung wie auf dem Blatt. */
const SPALTEN: { titel: string; kategorie: string; ton: string }[] = [
  { titel: "Körperlich", kategorie: "AttributKörperlich", ton: "#ff6b4d" },
  { titel: "Gesellschaftlich", kategorie: "AttributGesellschaftlich", ton: "#ffb648" },
  { titel: "Geistig", kategorie: "AttributGeistig", ton: "#4d8bd8" },
];

/**
 * Arete geht **nicht** mit Attributen zusammen (Zeilen 81-86). Ein
 * kontrollierter Zauber ist nur der Arete-Wert; dazunehmen lässt sich allein
 * Willenskraft, und das mit Folgen — siehe `magie.ts`.
 */
const NUR_WILLENSKRAFT = new Set(["Arete", "NeuroWeaving"]);

export interface ProbeWahl {
  name: string;
  wert: number;
  kategorie: string;
}

export function Probe({
  wahl,
  katalog,
  werte,
  willenskraft,
  onSchliessen,
}: {
  wahl: ProbeWahl | null;
  /** Nur für die Attributnamen und ihre Reihenfolge. */
  katalog: TraitDef[];
  /**
   * Aktuelle Werte, verschlüsselt nach **TraitDef-Kennung** — so liefert sie
   * das Charakterblatt. Nach Namen zu suchen ginge schief: die Karte hätte
   * dann für jeden Eintrag `undefined` und alle Attribute stünden auf 0.
   */
  werte: Map<string, number>;
  /** Obergrenze für Wilde Magie — so viele Bonuswürfel sind erlaubt. */
  willenskraft: number;
  onSchliessen: () => void;
}) {
  const [attribut, setAttribut] = useState<{ name: string; wert: number } | null>(null);
  // Bonuswürfel aus Willenskraft — nur bei Arete und NeuroWeaving.
  const [wild, setWild] = useState(0);

  if (!wahl) return null;

  const istSphaere = wahl.kategorie === "Sphäre";
  const nurWillenskraft = NUR_WILLENSKRAFT.has(wahl.kategorie);
  const pool = wahl.wert + (attribut?.wert ?? 0) + (nurWillenskraft ? wild : 0);

  function schliesseAlles() {
    setAttribut(null);
    setWild(0);
    onSchliessen();
  }

  // --- Sphären: hier wird nicht gewürfelt (Zeile 87) --------------------
  if (istSphaere) {
    return (
      <Fenster
        offen
        titel={`${wahl.name} ${wahl.wert}`}
        unterzeile="Sphäre — was damit geht"
        kennung={`sphaere:${wahl.name}`}
        onSchliessen={schliesseAlles}
      >
        <p className="pr-regel pr-hinweis">{MAGIE_HINWEISE.sphaereNichtWuerfeln}</p>
        {SPHAEREN[wahl.name] && <p className="pr-sphaerentext">{SPHAEREN[wahl.name]}</p>}
        <ol className="pr-stufen">
          {SPHAEREN_STUFEN.slice(1).map((text, i) => {
            const stufe = i + 1;
            return (
              <li key={stufe} data-erreicht={stufe <= wahl.wert} data-aktuell={stufe === wahl.wert}>
                <span className="pr-stufe-zahl">{stufe}</span>
                <span>{text}</span>
              </li>
            );
          })}
        </ol>
        {wahl.wert === 0 && <p className="pr-regel">Diese Sphäre steht dir noch nicht offen.</p>}
      </Fenster>
    );
  }

  // --- Arete und NeuroWeaving: nur Willenskraft dazu --------------------
  if (nurWillenskraft) {
    return (
      <>
        <Fenster
          offen
          titel={`${wahl.name} ${wahl.wert}`}
          unterzeile={wahl.kategorie === "Arete" ? "Kontrolliert oder wild?" : "NeuroWeaving"}
          kennung={`probe:${wahl.name}`}
          onSchliessen={schliesseAlles}
        >
          <p className="pr-regel pr-hinweis">
            {wahl.kategorie === "Arete" ? MAGIE_HINWEISE.areteKontrolliert : MAGIE_HINWEISE.neuroWeaving}
          </p>

          <div className="pr-pool">
            <span className="pr-zahl">{pool}</span>
            <WuerfelZehn groesse={54} />
          </div>
          <p className="pr-rechnung">
            {wahl.name} {wahl.wert}
            {wild > 0 && ` + ${wild} aus Willenskraft`}
          </p>

          {willenskraft > 0 ? (
            <section className="pr-wild">
              <h3>Wilde Magie</h3>
              <p className="pr-regel">{MAGIE_HINWEISE.areteWild}</p>
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
              {wild > 0 && <p className="pr-warnung">{MAGIE_HINWEISE.areteRueckstoss}</p>}
            </section>
          ) : (
            <p className="pr-regel">Ohne Willenskraft keine wilde Magie.</p>
          )}
        </Fenster>
      </>
    );
  }

  return (
    <>
      <Fenster
        offen
        titel={`${wahl.name} ${wahl.wert}`}
        unterzeile="Womit kombinierst du?"
        kennung={`probe:${wahl.name}`}
        onSchliessen={schliesseAlles}
      >
        <div className="pr-spalten">
          {SPALTEN.map((spalte) => (
            <section key={spalte.kategorie} style={{ "--cb-ton": spalte.ton } as React.CSSProperties}>
              <h3 className="pr-spalte-titel">{spalte.titel}</h3>
              {katalog
                .filter((t) => t.category === spalte.kategorie)
                .map((t) => {
                  const wert = werte.get(t.id) ?? 0;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      className="pr-attribut"
                      onClick={() => setAttribut({ name: t.name, wert })}
                    >
                      <span className="pr-attribut-name">{t.name}</span>
                      <span className="pr-attribut-summe">{wahl.wert + wert}</span>
                    </button>
                  );
                })}
            </section>
          ))}
        </div>
      </Fenster>

      {/* Zweites Fenster über dem ersten — die Zahl ist die ganze Auskunft. */}
      <Fenster
        offen={attribut !== null}
        titel={attribut ? `${wahl.name} + ${attribut.name}` : ""}
        kennung="probe-pool"
        onSchliessen={() => setAttribut(null)}
      >
        <div className="pr-pool">
          <span className="pr-zahl">{pool}</span>
          <WuerfelZehn groesse={54} />
        </div>
        <p className="pr-rechnung">
          {wahl.name} {wahl.wert}
          {attribut && attribut.wert > 0 && ` + ${attribut.name} ${attribut.wert}`}
        </p>
        <p className="pr-regel">
          <strong>1–5</strong> Misserfolg · <strong>6–10</strong> Erfolg. Zwei Zehner zählen wie vier Erfolge.
        </p>
      </Fenster>
    </>
  );
}
