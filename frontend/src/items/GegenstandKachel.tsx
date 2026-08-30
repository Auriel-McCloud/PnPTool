import { useState } from "react";
import { parseRichText } from "../richtext/content";
import { RichTextView } from "../richtext/RichTextView";
import { Fenster } from "../shell/Fenster";
import { DotPool } from "../traits/DotPool";
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

const ABLAGEN: { wert: Ablage; label: string; symbol: string; erklaerung: string }[] = [
  { wert: "AUSGERUESTET", label: "Ausgerüstet", symbol: "⚔", erklaerung: "Am Mann, sofort einsatzbereit." },
  { wert: "RUCKSACK", label: "Mitgeführt", symbol: "🎒", erklaerung: "Dabei, aber erst herauszuholen." },
  { wert: "GELAGERT", label: "Gelagert", symbol: "⌂", erklaerung: "Liegt anderswo — nicht am Körper." },
];

export function GegenstandKachel({
  item,
  onUmlegen,
}: {
  item: Gegenstand;
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
          {item.ablage === "AUSGERUESTET" && <span className="gg-marke" data-ton="neon">getragen</span>}
          {item.ablageZielName && <span className="gg-marke">{item.ablageZielName}</span>}
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

        {beschreibung && <RichTextView content={beschreibung} />}

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
              Liegt in <strong>{item.ablageZielName}</strong>. Wo genau etwas gelagert wird, legt die
              Spielleitung fest.
            </p>
          )}
          <div className="gg-ablage-knoepfe">
            {ABLAGEN.map((a) => (
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
