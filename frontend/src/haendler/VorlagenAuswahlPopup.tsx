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
 * Wiederverwendet die Shop-Kachel (`shop-ware`, `data-seltenheit`) samt
 * Seltenheitsrahmen aus shop.css — dieselbe Optik, die Spieler beim
 * Einkaufen schon sehen, jetzt auch beim Auswählen fürs Sortiment. Zusätzlich
 * Typ + `steckbriefKurz()` (dieselbe Kurzfassung wie auf der normalen
 * Gegenstands-Kachel) direkt auf der Kachel, kein Hineinklicken nötig.
 */
export function VorlagenAuswahlPopup({
  offen,
  vorlagen,
  onWaehlen,
  onSchliessen,
}: {
  offen: boolean;
  vorlagen: GegenstandMitBesitzer[];
  onWaehlen: (gegenstand: GegenstandMitBesitzer) => void;
  onSchliessen: () => void;
}) {
  const [suche, setSuche] = useState("");

  const gefiltert = useMemo(() => {
    const q = suche.trim().toLowerCase();
    const liste = q ? vorlagen.filter((g) => g.name.toLowerCase().includes(q)) : vorlagen;
    return [...liste].sort((a, b) => a.name.localeCompare(b.name, "de"));
  }, [vorlagen, suche]);

  return (
    <Fenster
      offen={offen}
      titel="Ware wählen"
      unterzeile={`${vorlagen.length} Vorlage${vorlagen.length === 1 ? "" : "n"} verfügbar`}
      kennung="vorlagen-auswahl"
      breit
      onSchliessen={onSchliessen}
    >
      <input
        value={suche}
        onChange={(e) => setSuche(e.target.value)}
        placeholder="Suchen — Name"
        autoFocus
        style={{ width: "100%", marginBottom: 12 }}
      />
      {gefiltert.length === 0 && <p className="shop-leer">Keine passende Vorlage.</p>}
      <div className="shop-waren-raster">
        {gefiltert.map((g) => (
          <button
            key={g.id}
            type="button"
            className="shop-ware"
            data-seltenheit={g.seltenheit}
            onClick={() => onWaehlen(g)}
            title={g.name}
          >
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
        ))}
      </div>
    </Fenster>
  );
}
