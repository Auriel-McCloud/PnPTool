import { useState } from "react";
import { type GegenstandMitBesitzer } from "../items/api";
import { type DrohnenEintrag } from "../drohnen/api";
import { ReparaturFenster, type ReparaturZiel } from "../reparatur/ReparaturFenster";
import "../items/gegenstaende.css";

/**
 * Werkbank-Reparatur für Spieler (29.10.2026, Mark: "das war alles für die
 * Spieler gedacht!" — Korrektur, war vorher `require_campaign_gm`).
 * Gegenstück zu `reparatur/ReparaturUebersicht.tsx` (SL-Ansicht,
 * campaignweit) — hier nur die eigene Rüstung + eigene gebundene Drohnen/
 * Fahrzeuge, Vorauswahl übernimmt `SpielerAnsicht.tsx`. Kein Händler-Reiter
 * (`ReparaturFenster erlaubeHaendler={false}`) — der Weg läuft über eine
 * SL-initiierte Verhandlung, nicht über Spieler-Self-Service.
 */
export function ReparaturUebersichtSpieler({
  campaignId,
  ruestungsziele,
  drohnen,
  onGeaendert,
}: {
  campaignId: string;
  ruestungsziele: GegenstandMitBesitzer[];
  drohnen: DrohnenEintrag[];
  onGeaendert: () => void;
}) {
  const [offenesZiel, setOffenesZiel] = useState<ReparaturZiel | null>(null);

  return (
    <div className="gg-seite">
      {ruestungsziele.length === 0 && drohnen.length === 0 && (
        <p className="gg-leer">Keine eigene Rüstung oder Drohne/Fahrzeug im Besitz.</p>
      )}

      {ruestungsziele.length > 0 && (
        <>
          <p className="lu-hinweis">Rüstung ({ruestungsziele.length})</p>
          <div className="gg-raster">
            {ruestungsziele.map((g) => (
              <button
                key={g.id}
                type="button"
                className="gg-kachel"
                onClick={() =>
                  setOffenesZiel({
                    typ: "ruestung",
                    id: g.id,
                    name: g.name,
                    besitzerId: g.ownerId,
                    ruestungKaestchenAktuell: g.ruestungKaestchenAktuell,
                    ruestungKaestchenMax: g.ruestungKaestchenMax,
                  })
                }
              >
                <span className="gg-kachel-bild">
                  {g.bildUrl ? <img src={g.bildUrl} alt="" /> : <span aria-hidden="true">🛡</span>}
                </span>
                <span className="gg-kachel-name">{g.name}</span>
                <span className="gg-kachel-zeile">
                  <span style={g.ruestungKaestchenAktuell < g.ruestungKaestchenMax ? { color: "var(--nein)" } : undefined}>
                    {g.ruestungKaestchenAktuell}/{g.ruestungKaestchenMax} Kästchen
                  </span>
                </span>
              </button>
            ))}
          </div>
        </>
      )}

      {drohnen.length > 0 && (
        <>
          <p className="lu-hinweis">Drohnen &amp; Fahrzeuge ({drohnen.length})</p>
          <div className="gg-raster">
            {drohnen.map((d) => (
              <button
                key={d.id}
                type="button"
                className="gg-kachel"
                onClick={() =>
                  setOffenesZiel({
                    typ: d.istFahrzeug ? "fahrzeug" : "drohne",
                    id: d.id,
                    name: d.name,
                    gesundheitAktuell: d.gesundheitAktuell,
                    gesundheitMax: d.gesundheitMax,
                    aussenhuelleAktuell: d.aussenhuelleAktuell,
                    aussenhuelleMax: d.aussenhuelleMax,
                  })
                }
              >
                <span className="gg-kachel-bild">
                  {d.bildUrl ? <img src={d.bildUrl} alt="" /> : <span aria-hidden="true">⛭</span>}
                </span>
                <span className="gg-kachel-name">{d.name}</span>
                <span className="gg-kachel-zeile">{d.istFahrzeug ? "Fahrzeug" : "Drohne"}</span>
                <span className="gg-kachel-zeile">
                  Gesundheit {d.gesundheitAktuell}/{d.gesundheitMax}
                  {d.aussenhuelleMax != null && d.aussenhuelleMax > 0 && (
                    <>
                      {" — "}Außenhülle{" "}
                      <span style={d.aussenhuelleAktuell! < d.aussenhuelleMax ? { color: "var(--nein)" } : undefined}>
                        {d.aussenhuelleAktuell}/{d.aussenhuelleMax}
                      </span>
                    </>
                  )}
                </span>
              </button>
            ))}
          </div>
        </>
      )}

      {offenesZiel && (
        <ReparaturFenster
          campaignId={campaignId}
          ziel={offenesZiel}
          onSchliessen={() => setOffenesZiel(null)}
          onGeaendert={onGeaendert}
          erlaubeHaendler={false}
        />
      )}
    </div>
  );
}
