import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { DotPool } from "../traits/DotPool";
import type { DrohnenPreisEintrag } from "./api";

/**
 * "+ Weitere Fertigkeiten"-Popup für den Drohnen-Umbau (26.10.2026, Mark:
 * "sollten in einem Popup aufgehen, so wie wir es immer machen und nicht in
 * einer Dropdown-Liste... und dann sollten sie ausgewählt werden können und
 * sich bei den anderen Fertigkeiten hinzufügen").
 *
 * Mehrfachauswahl-Kachelliste wie `haendler/VorlagenAuswahlPopup.tsx`: Klick
 * toggelt (Checkmarke), Popup bleibt offen, "N übernehmen" schickt die ganze
 * Auswahl auf einmal und schließt. Rein lokale Anzeige-Auswahl (kein
 * Server-Write, keine Kosten) — die übernommenen Einträge erscheinen danach
 * oben bei den normalen Fertigkeiten und sind dort ganz normal mit ¥/Material
 * kaufbar. Bereits übernommene lassen sich hier wieder abwählen ("rausholen"
 * rückgängig machen), ohne einen bereits getätigten Kauf zu verlieren.
 */
export function DrohnenWeitereFertigkeitenPopup({
  offen,
  eintraege,
  hervorgehoben,
  onUebernehmen,
  onSchliessen,
}: {
  offen: boolean;
  eintraege: DrohnenPreisEintrag[];
  hervorgehoben: Set<string>;
  onUebernehmen: (ids: Set<string>) => void;
  onSchliessen: () => void;
}) {
  const [suche, setSuche] = useState("");
  const [ausgewaehlt, setAusgewaehlt] = useState<Set<string>>(hervorgehoben);

  useEffect(() => {
    if (offen) setAusgewaehlt(new Set(hervorgehoben));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen]);

  const gefiltert = useMemo(() => {
    const q = suche.trim().toLowerCase();
    const liste = q ? eintraege.filter((e) => e.name.toLowerCase().includes(q)) : eintraege;
    return [...liste].sort((a, b) => a.name.localeCompare(b.name, "de"));
  }, [eintraege, suche]);

  function toggeln(id: string) {
    setAusgewaehlt((alt) => {
      const neu = new Set(alt);
      if (neu.has(id)) neu.delete(id);
      else neu.add(id);
      return neu;
    });
  }

  function uebernehmen() {
    onUebernehmen(ausgewaehlt);
    onSchliessen();
  }

  return (
    <Fenster
      offen={offen}
      breit
      titel="Weitere Fertigkeiten"
      unterzeile={`${eintraege.length} Stück — mehrere anklickbar, für den Sonderbau`}
      kennung="drohnen-weitere-fertigkeiten"
      onSchliessen={onSchliessen}
    >
      {eintraege.length > 6 && (
        <input
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
          placeholder="Suchen — Name"
          autoFocus
          style={{ width: "100%", marginBottom: 12 }}
        />
      )}
      {gefiltert.length === 0 && <p style={{ color: "var(--text-leise)" }}>Keine passende Fertigkeit.</p>}
      <div className="lu-raster" style={{ maxHeight: "48vh", overflowY: "auto" }}>
        {gefiltert.map((e) => {
          const gewaehlt = ausgewaehlt.has(e.traitDefId);
          return (
            <button
              key={e.traitDefId}
              type="button"
              className="lu-wert"
              onClick={() => toggeln(e.traitDefId)}
              style={gewaehlt ? { outline: "2px solid var(--neon)", outlineOffset: -2 } : undefined}
              title={gewaehlt ? "Erneut klicken zum Abwählen" : "Bei den Fertigkeiten anzeigen"}
            >
              <span className="lu-name">
                {gewaehlt && <span aria-hidden="true">✓ </span>}
                {e.name}
              </span>
              <DotPool value={e.aktuell} max={e.max} />
            </button>
          );
        })}
      </div>

      <div style={{ marginTop: 12, display: "flex", justifyContent: "flex-end" }}>
        <button type="button" className="lu-btn lu-btn-speichern" onClick={uebernehmen}>
          {ausgewaehlt.size === 0 ? "Übernehmen" : `${ausgewaehlt.size} übernehmen`}
        </button>
      </div>
    </Fenster>
  );
}
