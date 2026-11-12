import { extrahiereReinenText, parseRichText } from "../richtext/content";
import { RichTextView } from "../richtext/RichTextView";
import { Fenster } from "../shell/Fenster";
import type { Gegenstand } from "./api";
import { steckbriefZeilen, type SteckbriefZeile } from "./steckbrief";

/**
 * Readonly-Fenster für Spieler: Steckbrief (Werte) und Beschreibung.
 *
 * Die Kachel öffnet das Handlungsfenster (Umlegen, Wegwerfen, …). Die
 * Beschreibung stand dort unter dem Bild und ging auf dem Tablet unter.
 * Mark, 12.11.2026: Spieler brauchen einen eigenen Knopf, der nur liest.
 * Notizen bleiben bei der SL — die API liefert sie Spielern leer.
 */

const FAHRZEUG = new Set(["Fahrzeug", "Drohne"]);

function dauerLabel(dauer: string | undefined): string {
  if (dauer === "sofort") return "sofort";
  if (dauer === "rast") return "bis zur übernächsten Rast";
  return "bis zur Rast";
}

function extraZeilen(item: Gegenstand, montierteUpgrades: string[]): SteckbriefZeile[] {
  const zeilen: SteckbriefZeile[] = [];
  if (item.hatMenge) zeilen.push({ label: "Menge", wert: String(item.menge) });
  if (item.preis > 0) zeilen.push({ label: "Preis", wert: `${item.preis.toLocaleString("de-AT")}¥` });
  if (item.gewicht > 0) zeilen.push({ label: "Gewicht", wert: `${item.gewicht} kg` });
  if (item.koerperzone) {
    zeilen.push({
      label: "Sitzt",
      wert: item.slot ? `${item.koerperzone}, Platz ${item.slot}` : item.koerperzone,
    });
  }
  if (FAHRZEUG.has(item.typ)) {
    zeilen.push({ label: "Widerstand", wert: String(item.widerstand) });
    zeilen.push({ label: "Angriff", wert: String(item.angriff) });
    zeilen.push({ label: "Agilität", wert: String(item.agilitaet) });
  }
  if (item.typ === "Droge") {
    zeilen.push({ label: "Wirkt", wert: dauerLabel(item.wirkungDauer) });
    if ((item.heilmenge ?? 0) > 0) {
      const qualitaet = item.heilQualitaet ? ` · ${item.heilQualitaet}` : "";
      zeilen.push({ label: "Heilmenge", wert: `${item.heilmenge}${qualitaet}` });
    }
    if ((item.nebenwirkungSchadenMenge ?? 0) > 0 && item.nebenwirkungSchaden) {
      zeilen.push({
        label: "Nebenwirkung",
        wert: `${item.nebenwirkungSchaden} ${item.nebenwirkungSchadenMenge}`,
      });
    }
  }
  for (const [name, wert] of Object.entries(item.eigenschaften ?? {})) {
    if (wert) zeilen.push({ label: name, wert });
  }
  if (montierteUpgrades.length > 0) {
    zeilen.push({ label: "Verbaut", wert: montierteUpgrades.join(", ") });
  }
  return zeilen;
}

export function GegenstandLesen({
  item,
  offen,
  onSchliessen,
  montierteUpgrades = [],
}: {
  item: Gegenstand;
  offen: boolean;
  onSchliessen: () => void;
  montierteUpgrades?: string[];
}) {
  const zeilen = [...steckbriefZeilen(item), ...extraZeilen(item, montierteUpgrades)];
  const text = extrahiereReinenText(item.description ?? "");

  return (
    <Fenster
      offen={offen}
      titel={item.name}
      unterzeile={item.typ}
      kennung={`gegenstand-lesen:${item.id}`}
      onSchliessen={onSchliessen}
    >
      <section className="gg-lesen-block">
        <h3>Steckbrief</h3>
        {zeilen.length === 0 ? (
          <p className="gg-lesen-leer">Keine Werte hinterlegt.</p>
        ) : (
          <dl className="gg-eigenschaften">
            {zeilen.map((z) => (
              <div key={`${z.label}:${z.wert}`}>
                <dt>{z.label}</dt>
                <dd>{z.wert}</dd>
              </div>
            ))}
          </dl>
        )}
      </section>
      <section className="gg-lesen-block">
        <h3>Beschreibung</h3>
        {text ? (
          <RichTextView content={parseRichText(item.description)} />
        ) : (
          <p className="gg-lesen-leer">Keine Beschreibung hinterlegt.</p>
        )}
      </section>
    </Fenster>
  );
}
