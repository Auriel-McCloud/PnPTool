import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import { WuerfelZehn } from "./WuerfelZehn";
import type { TraitDef } from "./api";
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
 * Werte, die laut Regelblatt (Zeile 27) normalerweise **ohne** Attribut
 * gewürfelt werden — Arete, Sphären, NeuroWeaving zählen zwar als Fertigkeit,
 * stehen beim Würfeln aber für sich.
 */
const OHNE_ATTRIBUT = new Set(["Arete", "Sphäre", "NeuroWeaving"]);

export interface ProbeWahl {
  name: string;
  wert: number;
  kategorie: string;
}

export function Probe({
  wahl,
  katalog,
  werte,
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
  onSchliessen: () => void;
}) {
  const [attribut, setAttribut] = useState<{ name: string; wert: number } | null>(null);

  if (!wahl) return null;

  const alleinMoeglich = OHNE_ATTRIBUT.has(wahl.kategorie);
  const pool = wahl.wert + (attribut?.wert ?? 0);

  function schliesseAlles() {
    setAttribut(null);
    onSchliessen();
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
        {alleinMoeglich && (
          <button
            type="button"
            className="pr-allein"
            onClick={() => setAttribut({ name: "ohne Attribut", wert: 0 })}
          >
            Für sich allein — {wahl.wert} Würfel
            <em>{wahl.kategorie === "Arete" ? "Arete" : wahl.kategorie} wird normalerweise ohne Attribut gewürfelt.</em>
          </button>
        )}

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
