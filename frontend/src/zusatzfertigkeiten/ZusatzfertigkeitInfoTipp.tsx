import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import "../regeln/infotipp.css";

/**
 * Kleines Pendant zu `regeln/InfoTipp.tsx`, aber für Zusatzfertigkeiten
 * (23.10.2026, Mark: "Tooltip-Menü fehlt beim Skill, vermutlich bei keiner
 * anderen Zusatzfertigkeit" — stimmte, das Raster in der Charaktererstellung
 * hatte für Zusatzfertigkeiten nie ein Fragezeichen, anders als bei jeder
 * normalen Fertigkeit).
 *
 * Bewusst KEIN Wrapper um `InfoTipp`: der erwartet einen GM-editierbaren
 * Erklärungstext aus dem ruleset-weiten `erklaerungen`-Store (Schlüssel wie
 * `trait:Körperkraft`). Zusatzfertigkeiten sind campaign-gebundene,
 * eigenständige Katalogeinträge mit eigener kurz-/detailbeschreibung
 * (gepflegt in `ZusatzfertigkeitenVerwaltung`) — die Quelle ist hier direkt
 * der Katalogeintrag, kein zweiter Erklärungstext zum Pflegen.
 */
export function ZusatzfertigkeitInfoTipp({
  titel,
  kurzbeschreibung,
  detailbeschreibung,
}: {
  titel: string;
  kurzbeschreibung?: string;
  detailbeschreibung?: string;
}) {
  const [offen, setOffen] = useState(false);
  const hatText = Boolean(kurzbeschreibung || detailbeschreibung);

  return (
    <>
      <button
        type="button"
        className={`it-zeichen${hatText ? "" : " it-leer"}`}
        onClick={(e) => {
          // Sonst löste die Zeile darunter zugleich ihre eigene Aktion aus
          // (Punkt antippen), wie beim normalen InfoTipp auch.
          e.stopPropagation();
          setOffen(true);
        }}
        aria-label={`Erklärung zu ${titel}`}
        title={hatText ? `Erklärung zu ${titel}` : `Zu ${titel} ist noch nichts hinterlegt`}
      >
        ?
      </button>
      <Fenster offen={offen} titel={titel} kennung={`zf-info:${titel}`} onSchliessen={() => setOffen(false)}>
        {kurzbeschreibung ? (
          <p className="it-text">{kurzbeschreibung}</p>
        ) : (
          <p className="it-text it-fehlt">Zu dieser Zusatzfertigkeit ist noch nichts hinterlegt.</p>
        )}
        {detailbeschreibung && <p className="it-text it-text-lang">{detailbeschreibung}</p>}
      </Fenster>
    </>
  );
}
