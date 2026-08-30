import { useState } from "react";
import { parseRichText } from "../richtext/content";
import { RichTextView } from "../richtext/RichTextView";
import { Fenster } from "../shell/Fenster";
import { DotPool } from "../traits/DotPool";
import { StufenBlatt } from "../traits/StufenBlatt";
import type { Ablage, Gegenstand } from "./api";

/**
 * Ein Gegenstand aus Spielersicht: Kachel, die sich zum Fenster öffnet.
 *
 * Bewusst nicht `GegenstandRow` der Spielleitung — die trägt Sichtbarkeit,
 * Besitzerwechsel, Vorlagen und Bild-Upload mit sich, von denen ein Spieler
 * nichts sehen soll und nichts darf.
 *
 * **Das Umlegen sitzt im Fenster, nicht an der Kachel.** Vorher stand unter
 * jedem Eintrag der Liste ein Knopfpaar "→ Rucksack / → Gelagert"; das war
 * die einzige Handlung, die überhaupt hervorstach, und machte die Übersicht
 * zur Knopfwand. Wo etwas liegt, entscheidet man beim Ansehen des Dings.
 */

/** Bekommen ein eigenes Blatt (Neotopia.xlsx, Blatt "Drohne/Fahrzeug"). */
const FAHRZEUGTYPEN = new Set(["Fahrzeug", "Drohne"]);

function ablagen(behaelterName?: string): { wert: Ablage; label: string; symbol: string; erklaerung: string }[] {
  return [
    { wert: "AUSGERUESTET", label: "Am Körper", symbol: "⚔", erklaerung: "Griffbereit, ohne etwas aufmachen zu müssen." },
    {
      wert: "RUCKSACK",
      // Wer einen Rucksack trägt, legt Dinge *da hinein* — und nicht in ein
      // abstraktes "mitgeführt".
      label: behaelterName ?? "Mitgeführt",
      symbol: "🎒",
      erklaerung: behaelterName ? `Verstaut im ${behaelterName}.` : "Dabei, aber erst herauszuholen.",
    },
    { wert: "GELAGERT", label: "Weggelegt", symbol: "⌷", erklaerung: "Liegt anderswo — nicht am Körper." },
  ];
}

export function GegenstandKachel({
  item,
  onUmlegen,
  behaelterName,
  behaelterId,
  inhalt,
}: {
  item: Gegenstand;
  /** Name des getragenen Behälters, falls einer da ist — für die Beschriftung. */
  behaelterName?: string;
  /**
   * Kennung des getragenen Behälters. Nötig, um den Rucksack nicht in sich
   * selbst legen zu können — der Ablageplatz "im Rucksack" ist für den
   * Rucksack selbst kein Ort.
   */
  behaelterId?: string;
  /** Nur bei Behältern und Fahrzeugen: hineinsehen, in einem weiteren Fenster. */
  inhalt?: { anzahl: number; oeffnen: () => void };
  /**
   * Die einzige Änderung, die ein Spieler an einem Gegenstand vornehmen darf.
   * Fehlt sie, ist der Gegenstand nur anzusehen — so bei fremdem Besitz.
   */
  onUmlegen?: (ablage: Ablage) => Promise<void> | void;
}) {
  const [offen, setOffen] = useState(false);
  const [laeuft, setLaeuft] = useState(false);

  const eigenschaften = Object.entries(item.eigenschaften ?? {});
  const beschreibung = parseRichText(item.description);

  async function umlegen(ablage: Ablage) {
    if (!onUmlegen) return;
    setLaeuft(true);
    try {
      await onUmlegen(ablage);
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <>
      <button type="button" className="gg-kachel" onClick={() => setOffen(true)} title={item.name}>
        <span className="gg-kachel-bild">
          {item.bildUrl ? <img src={item.bildUrl} alt="" /> : <span aria-hidden="true">◈</span>}
          {item.hatMenge && <span className="gg-kachel-menge">×{item.menge}</span>}
        </span>
        <span className="gg-kachel-name">{item.name}</span>
        <span className="gg-kachel-zeile">
          {item.typ}
          {item.gewicht > 0 && ` · ${item.gewicht} kg`}
        </span>
        <span className="gg-kachel-marken">
          {/* Kein "getragen"-Zeichen: im Abschnitt "Am Körper" wäre es an
              jeder Kachel dasselbe, und in einem Fach kann nichts getragen
              sein. Wo etwas liegt, sagt der Ort — das ist die Auskunft, die
              man beim Durchsehen eines Fachs braucht. */}
          {item.ablageZielName && <span className="gg-marke">{item.ablageZielName}</span>}
          {/* Nur am Körper von Belang: im Rucksack sieht es ohnehin niemand. */}
          {item.immerSichtbar && item.ablage === "AUSGERUESTET" && (
            <span className="gg-marke" data-ton="signal" title="Das sieht jeder">
              sichtbar
            </span>
          )}
          {item.hatMenge && item.menge === 0 && (
            <span className="gg-marke" data-ton="signal">leer</span>
          )}
        </span>
      </button>

      <Fenster
        offen={offen}
        titel={item.hatMenge ? `${item.name} ×${item.menge}` : item.name}
        unterzeile={[item.typ, item.preis > 0 ? `${item.preis.toLocaleString("de-AT")}¥` : null, item.gewicht > 0 ? `${item.gewicht} kg` : null]
          .filter(Boolean)
          .join(" · ")}
        kennung={`gegenstand:${item.id}`}
        onSchliessen={() => setOffen(false)}
      >
        {item.bildUrl && (
          <img
            src={item.bildUrl}
            alt=""
            style={{ width: "100%", maxHeight: 240, objectFit: "contain", borderRadius: "var(--radius)" }}
          />
        )}

        {item.immerSichtbar && (
          <p className="gg-sichtbar-hinweis">
            {item.ablage === "AUSGERUESTET"
              ? "Am Körper nicht zu übersehen — wer dich ansieht, sieht das hier."
              : "Trägst du es offen, sieht es jeder."}
          </p>
        )}

        {beschreibung && <RichTextView content={beschreibung} />}

        {inhalt && (
          <button type="button" className="gg-hineinsehen" onClick={inhalt.oeffnen}>
            <span aria-hidden="true">{item.typ === "Fahrzeug" ? "⛭" : "▣"}</span>
            Hineinsehen
            <span className="gg-fach-zahl">{inhalt.anzahl}</span>
          </button>
        )}

        {/* Blatt für Drohne und Fahrzeug (Neotopia.xlsx). Erscheint bei
            diesen Typen **immer** — auch ungepflegt: dass noch nichts
            eingetragen ist, ist selbst eine Auskunft. Vorher blieb ein
            Fahrzeug ohne Werte völlig stumm, und man rätselte, ob es kein
            Blatt hat oder ob die Anzeige fehlt. */}
        {(FAHRZEUGTYPEN.has(item.typ) ||
          item.stufe > 0 ||
          item.widerstand > 0 ||
          item.angriff > 0 ||
          item.agilitaet > 0) && (
          <>
            <StufenBlatt
              titel={item.typ === "Drohne" ? "Drohnenwerte" : "Fahrzeugwerte"}
              werte={item}
              stufenHinweis={
                item.stufe === 0
                  ? "Noch keine Stufe festgelegt — das trägt die Spielleitung ein."
                  : undefined
              }
            />
            {Object.keys(item.fahrzeugFertigkeiten ?? {}).length > 0 && (
              <div className="gg-fahrzeugwerte">
                {Object.entries(item.fahrzeugFertigkeiten).map(([name, wert]) => (
                  <div key={name} className="gg-fahrzeugwert">
                    <span>{name}</span>
                    <DotPool value={wert} max={5} />
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {item.kraft > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ color: "var(--text-leise)", fontSize: 13 }}>
              {item.typ === "Rüstung" ? "Rüstungsbonus" : "Schaden"}
            </span>
            <DotPool value={item.kraft} max={7} />
          </div>
        )}

        {eigenschaften.length > 0 && (
          <dl className="gg-eigenschaften">
            {eigenschaften.map(([schluessel, wert]) => (
              <div key={schluessel}>
                <dt>{schluessel}</dt>
                <dd>{wert}</dd>
              </div>
            ))}
          </dl>
        )}

        {/* Hierher gehört das Umlegen: man sieht sich das Ding an und
            entscheidet dabei, wo es hin soll. */}
        {onUmlegen && (
        <section className="gg-ablage-wahl">
          <h3>Wo ist es?</h3>
          {item.ablage === "GELAGERT" && item.ablageZielName && (
            <p className="gg-ablage-ort">
              Liegt in <strong>{item.ablageZielName}</strong>. Den genauen Platz bestimmt die Spielleitung —
              du kannst es hier nur an dich nehmen.
            </p>
          )}
          <div className="gg-ablage-knoepfe">
            {ablagen(behaelterName)
              // Nichts kann in sich selbst liegen.
              .filter((a) => !(a.wert === "RUCKSACK" && item.id === behaelterId))
              .map((a) => (
                <button
                  key={a.wert}
                  type="button"
                  data-aktiv={item.ablage === a.wert}
                  disabled={laeuft || item.ablage === a.wert}
                  onClick={() => umlegen(a.wert)}
                  title={a.erklaerung}
                >
                  <span aria-hidden="true">{a.symbol}</span> {a.label}
                </button>
              ))}
          </div>
        </section>
        )}
      </Fenster>
    </>
  );
}
