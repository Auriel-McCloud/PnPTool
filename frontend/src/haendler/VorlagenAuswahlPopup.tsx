import { useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import type { GegenstandMitBesitzer } from "../items/api";
import { steckbriefKurz } from "../items/steckbrief";
import { symbolFuerTyp } from "../items/typKatalog";
import "./shop.css";

/**
 * Ware-Auswahl für den Sortiment-Editor (11.10.2026, Mark: das reine
 * Namens-Dropdown zeigte "außer dem Namen keine Infos ... ich weiß nicht
 * welche Seltenheit sie haben und den Steckbrief sehe ich auch nicht").
 *
 * Mehrfachauswahl (11.10.2026, Mark direkt im Anschluss: Popup schloss nach
 * jedem Klick — "ich klicke auf eine Sache und das Fenster geht wieder zu").
 * Klick toggelt die Auswahl (Haken-Marke + Neon-Outline), ein gemeinsamer
 * Preis gilt optional für den ganzen Schwung, "N Waren hinzufügen" erst am
 * Ende schickt alles auf einmal ab und schließt.
 *
 * Wiederverwendet die Shop-Kachel (`shop-ware`, `data-seltenheit`) samt
 * Seltenheitsrahmen aus shop.css — dieselbe Optik, die Spieler beim
 * Einkaufen schon sehen, jetzt auch beim Auswählen fürs Sortiment. Zusätzlich
 * Typ + `steckbriefKurz()` (dieselbe Kurzfassung wie auf der normalen
 * Gegenstands-Kachel) direkt auf der Kachel, kein Hineinklicken nötig.
 */
export function VorlagenAuswahlPopup({
  offen,
  vorlagen,
  onHinzufuegen,
  onSchliessen,
  titel = "Ware wählen",
  leertext = "Keine passende Vorlage.",
  kennung = "vorlagen-auswahl",
}: {
  offen: boolean;
  vorlagen: GegenstandMitBesitzer[];
  /** preis fehlt (undefined) = Grundpreis je Gegenstand; gesetzt = derselbe
   * Preis für alle gerade ausgewählten Stücke. */
  onHinzufuegen: (gegenstandIds: string[], preis?: number) => Promise<void>;
  onSchliessen: () => void;
  titel?: string;
  leertext?: string;
  kennung?: string;
}) {
  const [suche, setSuche] = useState("");
  const [ausgewaehlt, setAusgewaehlt] = useState<Set<string>>(new Set());
  const [preis, setPreis] = useState("");
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  const gefiltert = useMemo(() => {
    const q = suche.trim().toLowerCase();
    const liste = q ? vorlagen.filter((g) => g.name.toLowerCase().includes(q)) : vorlagen;
    return [...liste].sort((a, b) => a.name.localeCompare(b.name, "de"));
  }, [vorlagen, suche]);

  function toggeln(id: string) {
    setAusgewaehlt((alt) => {
      const neu = new Set(alt);
      if (neu.has(id)) neu.delete(id);
      else neu.add(id);
      return neu;
    });
  }

  function zuruecksetzenUndSchliessen() {
    setSuche("");
    setAusgewaehlt(new Set());
    setPreis("");
    setFehler(null);
    onSchliessen();
  }

  async function hinzufuegen() {
    if (ausgewaehlt.size === 0) return;
    setLaeuft(true);
    setFehler(null);
    try {
      await onHinzufuegen([...ausgewaehlt], preis.trim() ? Number(preis) : undefined);
      zuruecksetzenUndSchliessen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Hinzufügen fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel={titel}
      unterzeile={`${vorlagen.length} Stück verfügbar — mehrere anklickbar`}
      kennung={kennung}
      breit
      onSchliessen={zuruecksetzenUndSchliessen}
    >
      <input
        value={suche}
        onChange={(e) => setSuche(e.target.value)}
        placeholder="Suchen — Name"
        autoFocus
        style={{ width: "100%", marginBottom: 12 }}
      />
      {gefiltert.length === 0 && <p className="shop-leer">{leertext}</p>}
      <div className="shop-waren-raster" style={{ maxHeight: "48vh", overflowY: "auto" }}>
        {gefiltert.map((g) => {
          const gewaehlt = ausgewaehlt.has(g.id);
          return (
            <button
              key={g.id}
              type="button"
              className="shop-ware"
              data-seltenheit={g.seltenheit}
              data-gewaehlt={gewaehlt}
              onClick={() => toggeln(g.id)}
              title={g.name}
            >
              {gewaehlt && (
                <span className="shop-ware-gewaehlt-marke" aria-hidden="true">
                  ✓
                </span>
              )}
              <span className="shop-ware-bild">
                {g.bildUrl ? <img src={g.bildUrl} alt="" /> : <span aria-hidden="true">{symbolFuerTyp(g.typ)}</span>}
              </span>
              <span className="shop-ware-name">{g.name}</span>
              <span className="shop-ware-typ">
                {symbolFuerTyp(g.typ)} {g.typ}
              </span>
              {steckbriefKurz(g).length > 0 && (
                <span className="shop-ware-steckbrief">{steckbriefKurz(g).join(" · ")}</span>
              )}
              <span className="shop-ware-preis">
                <span>{g.preis.toLocaleString("de-AT")}¥</span>
              </span>
            </button>
          );
        })}
      </div>

      <div className="shop-editor-hinzufuegen" style={{ marginTop: 12 }}>
        <input
          type="number"
          min={0}
          value={preis}
          onChange={(e) => setPreis(e.target.value)}
          placeholder="Preis für alle (leer = Grundpreis je Stück)"
          disabled={laeuft}
        />
        <button type="button" onClick={hinzufuegen} disabled={laeuft || ausgewaehlt.size === 0}>
          {laeuft
            ? "Fügt hinzu…"
            : ausgewaehlt.size === 0
              ? "Hinzufügen"
              : `${ausgewaehlt.size} ${ausgewaehlt.size === 1 ? "Ware" : "Waren"} hinzufügen`}
        </button>
      </div>
      {fehler && <p className="shop-ware-fehler">{fehler}</p>}
    </Fenster>
  );
}
