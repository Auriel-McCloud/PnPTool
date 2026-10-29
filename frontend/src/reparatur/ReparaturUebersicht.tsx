import { useEffect, useMemo, useState } from "react";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { drohnenApi, type DrohnenEintrag } from "../drohnen/api";
import { ReparaturFenster, type ReparaturZiel } from "./ReparaturFenster";
import "../items/gegenstaende.css";

/**
 * Burgermenü "Reparatur" (29.10.2026, im Chat mit Mark entschieden — siehe
 * docs/wiki/concepts/drohnen-fahrzeuge.md "Reparatur"): eigenständiger
 * Bereich statt im Bearbeiten-Popup des einzelnen Gegenstands versteckt
 * (vorher `RuestungReparatur.tsx` nur für Rüstung). Ein Ziel-Tab (Rüstung /
 * Drohnen & Fahrzeuge), Klick öffnet `ReparaturFenster` mit Material +
 * Probe (Selbst) oder Nuyen + Verhandlung (Händler, nur Rüstung).
 *
 * **Nur SL** — wie die bisherigen Reparatur-Routen (Selbst-Reparieren,
 * Händler-Angebot) schon immer GM-only waren.
 */
export function ReparaturUebersicht({ campaignId }: { campaignId: string }) {
  const [tab, setTab] = useState<"ruestung" | "drohnen">("ruestung");
  const [gegenstaende, setGegenstaende] = useState<GegenstandMitBesitzer[]>([]);
  const [drohnen, setDrohnen] = useState<DrohnenEintrag[]>([]);
  const [laden, setLaden] = useState(true);
  const [fehler, setFehler] = useState<string | null>(null);
  const [offenesZiel, setOffenesZiel] = useState<ReparaturZiel | null>(null);

  function neuLaden() {
    setLaden(true);
    Promise.all([itemsApi.listAlle(campaignId), drohnenApi.liste(campaignId)])
      .then(([items, d]) => {
        setGegenstaende(items);
        setDrohnen(d);
      })
      .catch(() => setFehler("Reparatur-Ziele konnten nicht geladen werden."))
      .finally(() => setLaden(false));
  }

  useEffect(neuLaden, [campaignId]);

  const ruestungsziele = useMemo(
    () =>
      gegenstaende.filter(
        (g) =>
          g.typ === "Rüstung" &&
          g.ruestungKaestchenMax > 0 &&
          !g.istNatuerlich &&
          g.ruestungKaestchenAktuell < g.ruestungKaestchenMax,
      ),
    [gegenstaende],
  );

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Reparatur-Ziele…</p>;

  return (
    <div className="gg-seite">
      <div className="gg-kopf">
        <button type="button" aria-pressed={tab === "ruestung"} onClick={() => setTab("ruestung")}>
          🛡 Rüstung ({ruestungsziele.length})
        </button>
        <button type="button" aria-pressed={tab === "drohnen"} onClick={() => setTab("drohnen")}>
          ⛭ Drohnen & Fahrzeuge ({drohnen.length})
        </button>
      </div>

      {fehler && <p style={{ color: "var(--signal)" }}>{fehler}</p>}

      {tab === "ruestung" && (
        <>
          {ruestungsziele.length === 0 && (
            <p className="gg-leer">Keine beschädigte, reparierbare Rüstung im Umlauf.</p>
          )}
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
                <span className="gg-kachel-bild">{g.bildUrl ? <img src={g.bildUrl} alt="" /> : <span aria-hidden="true">🛡</span>}</span>
                <span className="gg-kachel-name">{g.name}</span>
                <span className="gg-kachel-zeile">
                  {g.ruestungKaestchenAktuell}/{g.ruestungKaestchenMax} Kästchen — {g.ownerName ?? "ohne Besitzer"}
                </span>
              </button>
            ))}
          </div>
        </>
      )}

      {tab === "drohnen" && (
        <>
          {drohnen.length === 0 && <p className="gg-leer">Noch keine Drohne/kein Fahrzeug angelegt.</p>}
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
                <span className="gg-kachel-bild">{d.bildUrl ? <img src={d.bildUrl} alt="" /> : <span aria-hidden="true">⛭</span>}</span>
                <span className="gg-kachel-name">{d.name}</span>
                <span className="gg-kachel-zeile">{d.istFahrzeug ? "Fahrzeug" : "Drohne"} — {d.riggerName ?? "ungebunden"}</span>
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
          onGeaendert={neuLaden}
        />
      )}
    </div>
  );
}
