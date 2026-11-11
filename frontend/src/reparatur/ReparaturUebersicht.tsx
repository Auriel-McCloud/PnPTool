import { useEffect, useMemo, useRef, useState } from "react";
import { itemsApi, type GegenstandMitBesitzer } from "../items/api";
import { drohnenApi, type DrohnenEintrag } from "../drohnen/api";
import { ReparaturFenster, type ReparaturZiel } from "./ReparaturFenster";
import "../items/gegenstaende.css";
import { vorschau } from "../shell/vorschau";

/** Offenes Reparatur-Fenster an den frisch geladenen Listenstand hängen,
 * sonst zeigt die Kopfzeile weiter den Schnappschuss vom Öffnen. */
function zielAuffrischen(
  alt: ReparaturZiel | null,
  items: GegenstandMitBesitzer[],
  drohnen: DrohnenEintrag[],
): ReparaturZiel | null {
  if (!alt) return alt;
  if (alt.typ === "ruestung") {
    const g = items.find((x) => x.id === alt.id);
    if (!g) return alt;
    return {
      ...alt,
      name: g.name,
      ruestungKaestchenAktuell: g.ruestungKaestchenAktuell,
      ruestungKaestchenMax: g.ruestungKaestchenMax,
    };
  }
  const d = drohnen.find((x) => x.id === alt.id);
  if (!d) return alt;
  return {
    ...alt,
    name: d.name,
    typ: d.istFahrzeug ? "fahrzeug" : "drohne",
    gesundheitAktuell: d.gesundheitAktuell,
    gesundheitMax: d.gesundheitMax,
    aussenhuelleAktuell: d.aussenhuelleAktuell,
    aussenhuelleMax: d.aussenhuelleMax,
  };
}

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
  const ladung = useRef(0);

  function neuLaden(still = false) {
    // still: nach einer Reparatur nicht die ganze Seite durch "Lade…" ersetzen.
    // Das würde das offene Fenster abmontieren — die Erfolgsmeldung verschwindet,
    // und beim Wiederaufbau steht noch der alte Gesundheits-Schnappschuss.
    const gen = ++ladung.current;
    if (!still) setLaden(true);
    Promise.all([itemsApi.listAlle(campaignId), drohnenApi.liste(campaignId)])
      .then(([items, d]) => {
        if (gen !== ladung.current) return;
        setGegenstaende(items);
        setDrohnen(d);
        setOffenesZiel((alt) => zielAuffrischen(alt, items, d));
      })
      .catch(() => {
        if (gen === ladung.current) setFehler("Reparatur-Ziele konnten nicht geladen werden.");
      })
      .finally(() => {
        if (gen === ladung.current) setLaden(false);
      });
  }

  useEffect(() => {
    neuLaden(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campaignId]);

  const ruestungsziele = useMemo(
    () =>
      gegenstaende.filter(
        (g) =>
          g.typ === "Rüstung" &&
          g.ruestungKaestchenMax > 0 &&
          !g.istNatuerlich,
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
            <p className="gg-leer">Keine reparierbare Rüstung im Umlauf.</p>
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
                <span className="gg-kachel-bild">{g.bildUrl ? <img src={vorschau(g.bildUrl)} loading="lazy" decoding="async" alt="" /> : <span aria-hidden="true">🛡</span>}</span>
                <span className="gg-kachel-name">{g.name}</span>
                <span className="gg-kachel-zeile">
                  <span style={g.ruestungKaestchenAktuell < g.ruestungKaestchenMax ? { color: "var(--nein)" } : undefined}>
                    {g.ruestungKaestchenAktuell}/{g.ruestungKaestchenMax} Kästchen
                  </span>{" "}
                  — {g.ownerName ?? "ohne Besitzer"}
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
                <span className="gg-kachel-bild">{d.bildUrl ? <img src={vorschau(d.bildUrl)} loading="lazy" decoding="async" alt="" /> : <span aria-hidden="true">⛭</span>}</span>
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
          onGeaendert={() => neuLaden(true)}
        />
      )}
    </div>
  );
}
