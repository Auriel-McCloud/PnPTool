import { Fenster } from "../shell/Fenster";
import { GegenstandKachel } from "./GegenstandKachel";
import { SchlossOeffnen } from "./SchlossOeffnen";
import type { Ablage, Gegenstand } from "./api";
import { istVerschlossen } from "./api";
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
  gesamtAnzahl,
  offen,
  onSchliessen,
  onUmlegen,
  onWeitergeben,
  campaignId,
  eigenePersonId,
  inhaltVon,
  onZusammengelegt,
  schloss,
  onGeoeffnet,
}: {
  fach: Bereich | null;
  /** Bereits auf dieses Fach gefiltert (UND auf einen evtl. aktiven Suchtext). */
  items: Gegenstand[];
  /**
   * Ungefilterte Gesamtzahl in diesem Fach, nur zur Unterscheidung "wirklich
   * leer" von "nichts gefunden" (04.11.2026, Inventar-Suche). Fehlt sie,
   * gilt `items.length === 0` als "wirklich leer" — unverändertes Verhalten.
   */
  gesamtAnzahl?: number;
  offen: boolean;
  onSchliessen: () => void;
  /** Fehlt sie, ist der Inhalt nur anzusehen — so bei fremdem Besitz. */
  onUmlegen?: (item: Gegenstand, ablage: Ablage, zielId?: string | null) => Promise<void> | void;
  /** Weitergeben an ein Party-Mitglied — siehe GegenstandKachel.tsx. */
  onWeitergeben?: (item: Gegenstand, empfaengerId: string) => Promise<void> | void;
  campaignId?: string;
  eigenePersonId?: string;
  /**
   * Liefert für einen Behälter, wie viele Sachen darin liegen und wie man
   * hineinsieht — damit sich aus einem Fach das nächste öffnen lässt.
   */
  inhaltVon?: (item: Gegenstand) => { anzahl: number; oeffnen: () => void } | undefined;
  /**
   * Mehrere gleiche Stücke zu einem Stapel zusammenlegen — fehlt sie, erscheint
   * der Knopf gar nicht (so bei fremdem Besitz). Ruft nur nach, das Popup
   * selbst spricht direkt mit der API (siehe GegenstandKachel.tsx).
   */
  onZusammengelegt?: () => void;
  /** Die Kiste selbst, wenn dieses Fach eine verschlossene Kiste ist. */
  schloss?: Gegenstand;
  onGeoeffnet?: () => void;
}) {
  if (!fach) return null;

  const gewicht = items.reduce((s, g) => s + g.gewicht * (g.hatMenge ? g.menge : 1), 0);
  // Gefiltert, aber eigentlich nicht leer: eigener Hinweis statt "nichts
  // darin", sonst wirkt ein aktiver Suchtext wie Datenverlust.
  const keineTreffer = items.length === 0 && (gesamtAnzahl ?? 0) > 0;

  return (
    <Fenster
      offen={offen}
      titel={`${fach.symbol} ${fach.name}`}
      unterzeile={
        schloss && istVerschlossen(schloss)
          ? "verschlossen"
          : keineTreffer
          ? "keine Treffer"
          : items.length === 0
          ? "nichts darin"
          : `${items.length} ${items.length === 1 ? "Gegenstand" : "Gegenstände"}` +
            (gewicht > 0 ? ` · ${gewicht.toFixed(1).replace(".", ",")} kg` : "")
      }
      kennung={`fach:${fach.id}`}
      onSchliessen={onSchliessen}
    >
      {schloss && istVerschlossen(schloss) && campaignId && onGeoeffnet ? (
        <SchlossOeffnen
          item={schloss}
          campaignId={campaignId}
          offen
          ohneFenster
          onSchliessen={onSchliessen}
          onGeoeffnet={onGeoeffnet}
        />
      ) : keineTreffer ? (
        <p style={{ color: "var(--text-leise)", margin: 0 }}>Keine Treffer für den Filter.</p>
      ) : items.length === 0 ? (
        <p style={{ color: "var(--text-leise)", margin: 0 }}>Hier liegt nichts.</p>
      ) : (
        <div className="gg-fachraster">
          {items.map((g) => (
            <GegenstandKachel
              key={g.id}
              item={g}
              inhalt={inhaltVon?.(g)}
              onUmlegen={onUmlegen ? (ablage, zielId) => onUmlegen(g, ablage, zielId) : undefined}
              onWeitergeben={onWeitergeben ? (empfaengerId) => onWeitergeben(g, empfaengerId) : undefined}
              campaignId={campaignId}
              eigenePersonId={eigenePersonId}
              onZusammengelegt={onZusammengelegt}
              onGeoeffnet={onGeoeffnet}
            />
          ))}
        </div>
      )}
    </Fenster>
  );
}
