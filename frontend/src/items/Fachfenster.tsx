import { Fenster } from "../shell/Fenster";
import { GegenstandKachel } from "./GegenstandKachel";
import type { Ablage, Gegenstand } from "./api";
import type { Bereich } from "./aufbewahrung";

/**
 * Der Inhalt eines Fachs — Rucksack, Fahrzeug, Versteck — als Fenster.
 *
 * Marks Bild: was man am Körper trägt, liegt offen; alles andere muss man
 * erst aufmachen. Das Fenster *ist* diese Handlung, und dass es aufgeht,
 * vermittelt zugleich, dass man an den Rucksack nicht so schnell kommt wie
 * an das, was man in der Hand hat.
 *
 * Hier darf gescrollt werden. Im Fenster bricht das die Illusion des
 * Geräte-Displays nicht — auf der Hauptansicht schon (docs/ui-konzept.md).
 */
export function Fachfenster({
  fach,
  items,
  offen,
  onSchliessen,
  onUmlegen,
  behaelterName,
  behaelterId,
  inhaltVon,
}: {
  fach: Bereich | null;
  /** Bereits auf dieses Fach gefiltert. */
  items: Gegenstand[];
  offen: boolean;
  onSchliessen: () => void;
  /** Fehlt sie, ist der Inhalt nur anzusehen — so bei fremdem Besitz. */
  onUmlegen?: (item: Gegenstand, ablage: Ablage) => Promise<void> | void;
  behaelterName?: string;
  behaelterId?: string;
  /**
   * Liefert für einen Behälter, wie viele Sachen darin liegen und wie man
   * hineinsieht — damit sich aus einem Fach das nächste öffnen lässt.
   */
  inhaltVon?: (item: Gegenstand) => { anzahl: number; oeffnen: () => void } | undefined;
}) {
  if (!fach) return null;

  const gewicht = items.reduce((s, g) => s + g.gewicht * (g.hatMenge ? g.menge : 1), 0);

  return (
    <Fenster
      offen={offen}
      titel={`${fach.symbol} ${fach.name}`}
      unterzeile={
        items.length === 0
          ? "nichts darin"
          : `${items.length} ${items.length === 1 ? "Gegenstand" : "Gegenstände"}` +
            (gewicht > 0 ? ` · ${gewicht.toFixed(1).replace(".", ",")} kg` : "")
      }
      kennung={`fach:${fach.id}`}
      onSchliessen={onSchliessen}
    >
      {items.length === 0 ? (
        <p style={{ color: "var(--text-leise)", margin: 0 }}>Hier liegt nichts.</p>
      ) : (
        <div className="gg-fachraster">
          {items.map((g) => (
            <GegenstandKachel
              key={g.id}
              item={g}
              behaelterName={behaelterName}
              behaelterId={behaelterId}
              inhalt={inhaltVon?.(g)}
              onUmlegen={onUmlegen ? (ablage) => onUmlegen(g, ablage) : undefined}
            />
          ))}
        </div>
      )}
    </Fenster>
  );
}
