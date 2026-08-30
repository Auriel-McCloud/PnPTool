import { DotPool } from "./DotPool";
import "./stufenblatt.css";

/**
 * Das Blatt für Drohne, Fahrzeug, Sprite und Geist.
 *
 * `Neotopia.xlsx` führt alle vier auf **einem** Formular
 * ("Drohne / Fahrzeug / Sprite / Geist"), und genau so wird es hier auch nur
 * einmal gezeichnet. Vorher stand derselbe Block an vier Stellen — und als
 * Mark die Stufe eine Zeile höher haben wollte, musste ich sie viermal
 * verschieben und habe es beim ersten Mal halb vergessen.
 *
 * **Die Stufe steht allein und darüber.** Sie ist kein vierter Wert neben den
 * anderen, sondern das Budget, aus dem sie bezahlt werden — und zugleich die
 * Gesundheit.
 */

export interface StufenWerte {
  stufe: number;
  widerstand: number;
  angriff: number;
  agilitaet: number;
}

/** Wofür die drei Werte im Spiel stehen (Regelblatt Zeile 107). */
const ERKLAERUNG: Record<string, string> = {
  Widerstand: "Schadensreduktion.",
  Angriff: "Treffen und Schaden, wenn es selbst handelt.",
  Agilität: "Geschwindigkeit.",
};

export function StufenBlatt({
  werte,
  titel,
  stufenHinweis,
  onAendern,
}: {
  werte: StufenWerte;
  /** Überschrift, etwa "Fahrzeugwerte" — ohne Angabe erscheint keine. */
  titel?: string;
  /** Zusatzzeile unter der Stufe; ohne Angabe der Standardtext. */
  stufenHinweis?: string;
  /** Fehlt sie, ist das Blatt nur zum Ansehen. */
  onAendern?: (feld: keyof StufenWerte, wert: number) => void;
}) {
  const drei: [keyof StufenWerte, string, number][] = [
    ["widerstand", "Widerstand", 5],
    ["angriff", "Angriff", 5],
    ["agilitaet", "Agilität", 5],
  ];
  const verteilt = werte.widerstand + werte.angriff + werte.agilitaet;

  return (
    <section className="sb-blatt">
      {titel && <h3 className="sb-titel">{titel}</h3>}

      <div className="sb-stufe">
        <span className="sb-stufe-titel">Stufe</span>
        <DotPool
          value={werte.stufe}
          max={15}
          onChange={onAendern ? (w) => onAendern("stufe", w) : undefined}
        />
        <span className="sb-stufe-hinweis">
          {stufenHinweis ??
            "Zugleich die Gesundheit. Wird beim Kauf festgelegt und frei auf die Werte darunter verteilt."}
        </span>
      </div>

      <div className="sb-werte">
        {drei.map(([feld, beschriftung, maximum]) => (
          <div key={feld} className="sb-wert" title={ERKLAERUNG[beschriftung]}>
            <span>{beschriftung}</span>
            <DotPool
              value={werte[feld]}
              max={maximum}
              onChange={onAendern ? (w) => onAendern(feld, w) : undefined}
            />
          </div>
        ))}
      </div>

      {/* Nur beim Bearbeiten warnen: beim Ansehen ist es eine Tatsache, keine
          Aufforderung — und die Spielleitung darf bewusst darüber gehen. */}
      {onAendern && werte.stufe > 0 && verteilt > werte.stufe && (
        <p className="sb-warnung">
          {verteilt} Punkte verteilt, die Stufe gibt {werte.stufe} her.
        </p>
      )}
    </section>
  );
}
