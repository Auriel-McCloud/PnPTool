import { useState } from "react";
import { parseRichText } from "../richtext/content";
import { RichTextView } from "../richtext/RichTextView";
import { Fenster } from "../shell/Fenster";
import { DotPool } from "../traits/DotPool";
import { StufenBlatt } from "../traits/StufenBlatt";
import { ART_NAMEN, ART_SYMBOLE, type Begleiter } from "./api";
import { EinflussAnzeige } from "./EinflussVerwaltung";
import { KiAttributBlatt } from "./KiAttributBlatt";
import "./begleiter.css";

/**
 * Ein Begleiter als Kachel, die sein Blatt aufklappt.
 *
 * Das Grundblatt ist dasselbe wie bei Drohne und Fahrzeug (`Neotopia.xlsx`,
 * Blatt "Drohne / Fahrzeug / Sprite / Geist"): Stufe, Widerstand, Angriff,
 * Agilität, vier freie Fertigkeiten und ein Gegenstand mit Schadensbonus.
 * KI (19.09.2026) zeigt zusätzlich ihr Zusatzblatt — siehe
 * `KiAttributBlatt`/`EinflussAnzeige`. CRITTER (Tiere/Haustiere) sind seit
 * 20.09.2026 keine Begleiter-Art mehr, sondern echte NPCs — siehe
 * `entities/NPCDetail.tsx`.
 *
 * **Layout (20.09.2026, Mark: "man will das Charakterblatt sehen"):** das
 * eigentliche Blatt (Werte) steht zuerst, selten gebrauchte Verwaltung
 * (Name/Art ändern, Verbindung, Beziehung) ganz unten im Bearbeiten-Fenster
 * — siehe `BegleiterVerwaltung.tsx`.
 */

export function BegleiterBlatt({ begleiter }: { begleiter: Begleiter }) {
  const fertigkeiten = Object.entries(begleiter.fertigkeiten ?? {});
  const beschreibung = parseRichText(begleiter.beschreibung);

  return (
    <>
      {begleiter.bildUrl && (
        <img src={begleiter.bildUrl} alt={begleiter.name} className="bg-bild" />
      )}

      {begleiter.beziehung && (
        <p className="bg-beziehung">
          <span>Beziehung</span> {begleiter.beziehung}
        </p>
      )}

      {begleiter.art === "KI" && <KiAttributBlatt werte={begleiter} />}

      <StufenBlatt werte={begleiter} stufenHinweis="Zugleich die Gesundheit." />

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

      {begleiter.art === "KI" && <EinflussAnzeige begleiter={begleiter} />}

      {beschreibung && <RichTextView content={beschreibung} />}
    </>
  );
}

export function BegleiterKachel({ begleiter }: { begleiter: Begleiter }) {
  const [offen, setOffen] = useState(false);

  return (
    <>
      <button type="button" className="gg-kachel" onClick={() => setOffen(true)} title={begleiter.name}>
        <span className="gg-kachel-bild">
          {begleiter.bildUrl ? (
            <img src={begleiter.bildUrl} alt="" />
          ) : (
            <span aria-hidden="true">{ART_SYMBOLE[begleiter.art]}</span>
          )}
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
