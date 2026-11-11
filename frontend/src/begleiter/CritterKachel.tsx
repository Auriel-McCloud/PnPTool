import { useState } from "react";
import { anzeigeName, type CritterEintrag } from "../entities/api";
import { Fenster } from "../shell/Fenster";
import { Charakterblatt } from "../traits/Charakterblatt";
import "./begleiter.css";

/**
 * Eigener Critter als Kachel im Begleiter-Bereich der Spieleransicht
 * (Mark, 11.11.2026: zugeordneter Critter tauchte bei den Begleitern nie auf).
 *
 * Critter sind echte NPCs mit vollem Bogen (siehe `CritterFenster.tsx` für die
 * SL-Seite) — der Spieler sieht hier Bild und Charakterblatt nur zum Lesen.
 * Das Lesen erlaubt der Server über die Besitzer-Ausnahme
 * (`traits/routes.py::_darf_person_sehen` → `critter_besitzer`).
 */
export function CritterKachel({ campaignId, critter }: { campaignId: string; critter: CritterEintrag }) {
  const [offen, setOffen] = useState(false);
  const name = anzeigeName(critter.name, critter.alias);

  return (
    <>
      <button type="button" className="gg-kachel" onClick={() => setOffen(true)} title={name}>
        <span className="gg-kachel-bild">
          {critter.bildUrl ? <img src={critter.bildUrl} alt="" /> : <span aria-hidden="true">❊</span>}
        </span>
        <span className="gg-kachel-name">{name}</span>
        <span className="gg-kachel-zeile">Critter{critter.istAeon && " · Aeon"}</span>
      </button>

      <Fenster
        offen={offen}
        titel={`❊ ${name}`}
        unterzeile="Critter"
        kennung={`critter:${critter.id}`}
        ton="var(--bereich-begleiter)"
        onSchliessen={() => setOffen(false)}
      >
        {critter.bildUrl && <img src={critter.bildUrl} alt={name} className="bg-bild" />}
        {offen && <Charakterblatt campaignId={campaignId} personId={critter.id} bearbeitbar={false} />}
      </Fenster>
    </>
  );
}
