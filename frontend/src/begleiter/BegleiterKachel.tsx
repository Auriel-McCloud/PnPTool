import { useState } from "react";
import { parseRichText } from "../richtext/content";
import { RichTextView } from "../richtext/RichTextView";
import { Fenster } from "../shell/Fenster";
import { DotPool } from "../traits/DotPool";
import { ART_NAMEN, ART_SYMBOLE, type Begleiter } from "./api";
import "./begleiter.css";

/**
 * Ein Begleiter als Kachel, die sein Blatt aufklappt.
 *
 * Das Blatt ist dasselbe wie bei Drohne und Fahrzeug (`Neotopia.xlsx`, Blatt
 * "Drohne / Fahrzeug / Sprite / Geist"): Stufe, Widerstand, Angriff,
 * Agilität, vier freie Fertigkeiten und ein Gegenstand mit Schadensbonus.
 */

/** Wofür die vier Werte im Spiel stehen — hier, weil es sonst niemand weiss. */
const WERT_ERKLAERUNG: Record<string, string> = {
  Stufe: "Zugleich die Gesundheit.",
  Widerstand: "Zieht vom erlittenen Schaden ab.",
  Angriff: "Treffen und Schaden.",
  Agilität: "Geschwindigkeit.",
};

export function BegleiterBlatt({ begleiter }: { begleiter: Begleiter }) {
  // Die Stufe steht allein oben — sie ist das Budget, aus dem die drei
  // darunter bezahlt werden, und zugleich die Gesundheit.
  const werte: [string, number, number][] = [
    ["Widerstand", begleiter.widerstand, 5],
    ["Angriff", begleiter.angriff, 5],
    ["Agilität", begleiter.agilitaet, 5],
  ];
  const fertigkeiten = Object.entries(begleiter.fertigkeiten ?? {});
  const beschreibung = parseRichText(begleiter.beschreibung);

  return (
    <>
      {begleiter.beziehung && (
        <p className="bg-beziehung">
          <span>Beziehung</span> {begleiter.beziehung}
        </p>
      )}

      {beschreibung && <RichTextView content={beschreibung} />}

      <section className="bg-stufe">
        <span className="bg-stufe-titel">Stufe</span>
        <DotPool value={begleiter.stufe} max={15} />
        <span className="bg-stufe-hinweis">Zugleich die Gesundheit.</span>
      </section>

      <section className="bg-werte">
        {werte.map(([name, wert, maximum]) => (
          <div key={name} className="bg-wert" title={WERT_ERKLAERUNG[name]}>
            <span>{name}</span>
            <DotPool value={wert} max={maximum} />
          </div>
        ))}
      </section>

      {fertigkeiten.length > 0 && (
        <section className="bg-werte">
          {fertigkeiten.map(([name, wert]) => (
            <div key={name} className="bg-wert">
              <span>{name}</span>
              <DotPool value={wert} max={5} />
            </div>
          ))}
        </section>
      )}

      {begleiter.waffe && (
        <section className="bg-waffe">
          <h3>{begleiter.waffe}</h3>
          <div className="bg-wert">
            <span>Schadensbonus{begleiter.schadensart && ` · ${begleiter.schadensart}`}</span>
            <DotPool value={begleiter.waffenSchaden} max={7} />
          </div>
        </section>
      )}
    </>
  );
}

export function BegleiterKachel({ begleiter }: { begleiter: Begleiter }) {
  const [offen, setOffen] = useState(false);

  return (
    <>
      <button type="button" className="gg-kachel" onClick={() => setOffen(true)} title={begleiter.name}>
        <span className="gg-kachel-bild">
          <span aria-hidden="true">{ART_SYMBOLE[begleiter.art]}</span>
        </span>
        <span className="gg-kachel-name">{begleiter.name}</span>
        <span className="gg-kachel-zeile">
          {ART_NAMEN[begleiter.art]}
          {begleiter.stufe > 0 && ` · Stufe ${begleiter.stufe}`}
        </span>
        <span className="gg-kachel-marken">
          {begleiter.besitzerName && <span className="gg-marke">{begleiter.besitzerName}</span>}
        </span>
      </button>

      <Fenster
        offen={offen}
        titel={`${ART_SYMBOLE[begleiter.art]} ${begleiter.name}`}
        unterzeile={[ART_NAMEN[begleiter.art], begleiter.besitzerName].filter(Boolean).join(" · ")}
        kennung={`begleiter:${begleiter.id}`}
        onSchliessen={() => setOffen(false)}
      >
        <BegleiterBlatt begleiter={begleiter} />
      </Fenster>
    </>
  );
}
