import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Campaign } from "./useCampaign";
import "./spielstart.css";

/**
 * RPGrid-Startseite (Mark, 26.11.2026): nach dem Login eine Kachel je Spiel
 * (Regelsystem). Klick aufs Spiel: genau eine Kampagne → direkt hinein,
 * mehrere → Kampagnen-Kacheln dieses Spiels, keine → „Neue Kampagne“.
 *
 * Die SL sieht alle Spiele. Spieler sehen die Seite noch nicht — ihr Zugang
 * hängt heute an genau einer Kampagne; die Spieler-Kacheln kommen mit dem
 * Konto-Modell (docs/wiki/entities/konten-login-und-abo.md).
 */
interface Regelsystem {
  id: string;
  name: string;
  beschreibung: string;
}

// Monochrome Glyphen statt Emoji (UI-Regel für Inhalts-Symbole).
const SYMBOL: Record<string, string> = { NeotopiA: "◈", GridMonster: "✦" };
const TON: Record<string, string> = {
  NeotopiA: "var(--neon)",
  GridMonster: "var(--bereich-begleiter)",
};

export function SpielStart({
  kampagnen,
  onBetreten,
  onNeueKampagne,
  onAbmelden,
}: {
  kampagnen: Campaign[];
  onBetreten: (spiel: string, kampagnenId: string) => void;
  onNeueKampagne: (spiel: string) => void;
  onAbmelden: () => void;
}) {
  const [spiele, setSpiele] = useState<Regelsystem[] | null>(null);
  const [gewaehlt, setGewaehlt] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Regelsystem[]>("/api/regelsysteme")
      .then(setSpiele)
      .catch(() => setSpiele([]));
  }, []);

  const kampagnenVon = (spiel: string) => kampagnen.filter((k) => (k.regelsystem ?? "NeotopiA") === spiel);

  function spielWaehlen(spiel: string) {
    const eigene = kampagnenVon(spiel);
    if (eigene.length === 1) onBetreten(spiel, eigene[0].id);
    else if (eigene.length === 0) onNeueKampagne(spiel);
    else setGewaehlt(spiel);
  }

  return (
    <div className="rp-start">
      <div className="rp-start-kopf">
        <div>
          <h1 className="rp-start-titel">RPGrid</h1>
          <div className="rp-start-unter">{gewaehlt ? `${gewaehlt}: Kampagne wählen` : "Spiel wählen"}</div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {gewaehlt && (
            <button type="button" className="rp-zurueck" onClick={() => setGewaehlt(null)}>
              ← Spiele
            </button>
          )}
          <button type="button" className="rp-abmelden" onClick={onAbmelden} title="Abmelden">
            ⏻
          </button>
        </div>
      </div>

      {!spiele && <p className="rp-start-unter">Lade…</p>}

      <div className="rp-kacheln">
        {!gewaehlt &&
          spiele?.map((s) => {
            const anzahl = kampagnenVon(s.name).length;
            return (
              <button
                key={s.id}
                type="button"
                className="rp-kachel cl-roehre"
                style={{ "--rp-ton": TON[s.name] ?? "var(--neon)" } as React.CSSProperties}
                onClick={() => spielWaehlen(s.name)}
              >
                <span className="rp-kachel-symbol" aria-hidden="true">
                  {SYMBOL[s.name] ?? "◇"}
                </span>
                <span className="rp-kachel-name">{s.name}</span>
                <span className="rp-kachel-text">{s.beschreibung}</span>
                <span className="rp-kachel-zahl">
                  {anzahl === 0 ? "Noch keine Kampagne" : anzahl === 1 ? "1 Kampagne" : `${anzahl} Kampagnen`}
                </span>
              </button>
            );
          })}

        {gewaehlt && (
          <>
            {kampagnenVon(gewaehlt).map((k) => (
              <button
                key={k.id}
                type="button"
                className="rp-kachel cl-roehre"
                style={{ "--rp-ton": TON[gewaehlt] ?? "var(--neon)" } as React.CSSProperties}
                onClick={() => onBetreten(gewaehlt, k.id)}
              >
                <span className="rp-kachel-symbol" aria-hidden="true">
                  ▤
                </span>
                <span className="rp-kachel-name">{k.name}</span>
              </button>
            ))}
            <button
              type="button"
              className="rp-kachel cl-roehre"
              style={{ "--rp-ton": "var(--linie)" } as React.CSSProperties}
              onClick={() => onNeueKampagne(gewaehlt)}
            >
              <span className="rp-kachel-symbol" aria-hidden="true">
                +
              </span>
              <span className="rp-kachel-name">Neue Kampagne</span>
            </button>
          </>
        )}
      </div>
    </div>
  );
}
