import { useEffect, useState } from "react";
import type { Person } from "../entities/api";
import { bogenApi, type BogenUebersicht } from "../traits/bogenApi";
import "./pc-kacheln.css";

/**
 * Kachel-Übersicht für Spielercharaktere.
 *
 * Zeigt für jeden PC: Name, Spieler (falls zugeordnet), Bild, aktuelle LP,
 * aktuelle WK, Blitz-Button zum Herzeigen. Klick öffnet das Charakterblatt.
 */

interface PCKachelProps {
  campaignId: string;
  person: Person;
  spielerName?: string;
  onKlick: () => void;
  onBlitz: () => void;
  onExtraEP?: () => void;
}

function PCKachel({ campaignId, person, spielerName, onKlick, onBlitz, onExtraEP }: PCKachelProps) {
  const [uebersicht, setUebersicht] = useState<BogenUebersicht | null>(null);

  useEffect(() => {
    bogenApi
      .laden(campaignId, person.id)
      .then((bogen) => setUebersicht(bogen.uebersicht))
      .catch(() => setUebersicht(null));
  }, [campaignId, person.id]);

  const lpAktuell = uebersicht ? uebersicht.gesundheitMax - uebersicht.gesundheitSchaden : null;
  const lpMax = uebersicht?.gesundheitMax ?? null;
  const wkAktuell = uebersicht
    ? uebersicht.willenskraftMax - uebersicht.willenskraftVerlust - uebersicht.willenskraftVerbraucht
    : null;
  const wkMax = uebersicht ? uebersicht.willenskraftMax - uebersicht.willenskraftVerlust : null;

  return (
    <div className="pc-kachel" onClick={onKlick}>
      <div className="pc-kachel-bild-bereich">
        {person.bildUrl ? (
          <img src={person.bildUrl} alt={person.name} className="pc-kachel-bild" />
        ) : (
          <div className="pc-kachel-bild-leer">◉</div>
        )}
        <button
          type="button"
          className="pc-kachel-blitz"
          onClick={(e) => {
            e.stopPropagation();
            onBlitz();
          }}
          title="Bild allen Spielern zeigen"
        >
          ⚡
        </button>
      </div>

      <div className="pc-kachel-info">
        <div className="pc-kachel-name">{person.name}</div>
        {spielerName && <div className="pc-kachel-spieler">{spielerName}</div>}

        {/* Extra-EP Anzeige mit + Button */}
        {(person.extraEP ?? 0) > 0 || onExtraEP ? (
          <div className="pc-kachel-extra-ep" style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 4, fontSize: "0.85em" }}>
            <span style={{ color: "var(--text-leise)" }}>
              Extra-EP: <strong style={{ color: "var(--neon)" }}>{person.extraEP ?? 0}</strong>
            </span>
            {onExtraEP && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onExtraEP();
                }}
                style={{
                  padding: "2px 6px",
                  background: "transparent",
                  border: "1px solid var(--neon)",
                  borderRadius: "var(--radius)",
                  color: "var(--neon)",
                  cursor: "pointer",
                  fontSize: "0.8em",
                }}
                title="Extra-EP vergeben"
              >
                1EP
              </button>
            )}
          </div>
        ) : null}

        <div className="pc-kachel-werte">
          <div className="pc-kachel-wert pc-kachel-lp" title="Lebenspunkte">
            <span className="pc-kachel-wert-icon">♥</span>
            {lpAktuell !== null && lpMax !== null ? (
              <span className={lpAktuell < lpMax * 0.3 ? "pc-kachel-kritisch" : ""}>
                {lpAktuell}/{lpMax}
              </span>
            ) : (
              <span className="pc-kachel-laden">…</span>
            )}
          </div>
          <div className="pc-kachel-wert pc-kachel-wk" title="Willenskraft">
            <span className="pc-kachel-wert-icon">◈</span>
            {wkAktuell !== null && wkMax !== null ? (
              <span className={wkAktuell === 0 ? "pc-kachel-kritisch" : ""}>
                {wkAktuell}/{wkMax}
              </span>
            ) : (
              <span className="pc-kachel-laden">…</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

interface PCKachelnProps {
  campaignId: string;
  pcs: Person[];
  spielerMap?: Map<string, string>; // personId -> Spielername
  onPCKlick: (person: Person) => void;
  onBlitz: (person: Person) => void;
  onExtraEP?: (person: Person) => void;
}

export function PCKacheln({ campaignId, pcs, spielerMap, onPCKlick, onBlitz, onExtraEP }: PCKachelnProps) {
  if (pcs.length === 0) {
    return <p className="pc-kacheln-leer">Noch keine Spielercharaktere angelegt.</p>;
  }

  return (
    <div className="pc-kacheln-raster">
      {pcs.map((p) => (
        <PCKachel
          key={p.id}
          campaignId={campaignId}
          person={p}
          spielerName={spielerMap?.get(p.id)}
          onKlick={() => onPCKlick(p)}
          onBlitz={() => onBlitz(p)}
          onExtraEP={onExtraEP ? () => onExtraEP(p) : undefined}
        />
      ))}
    </div>
  );
}
