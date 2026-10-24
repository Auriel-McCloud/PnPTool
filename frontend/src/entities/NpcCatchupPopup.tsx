import { useState } from "react";
import { Fenster } from "../shell/Fenster";
import { bogenApi, type CatchupErgebnis } from "../traits/bogenApi";
import type { Person } from "./api";

/**
 * NPC-Catch-up (24.10.2026, Marks Wunsch): hebt einen NPC auf einen Anteil
 * des EP-/Vermögensniveaus eines Referenz-PCs — automatisch verteilt auf
 * Werte und eingekauft+ausgerüstet, ohne Rückfrage (Mark: "machen wir die
 * Steigerung und das Einkaufen direkt ohne Rückfrage"). Das Ergebnis wird
 * danach nur noch angezeigt, nicht mehr bestätigt.
 *
 * Lebt bewusst im NPC-Menü (EntityManager.tsx, Ansicht "npcs"), nicht bei
 * den PCs — Ziel ist immer ein NPC, der Referenz-PC ist nur die Messlatte.
 */
export function NpcCatchupPopup({
  offen,
  npcs,
  pcs,
  campaignId,
  onSchliessen,
}: {
  offen: boolean;
  npcs: Person[];
  pcs: Person[];
  campaignId: string;
  onSchliessen: () => void;
}) {
  const [npcId, setNpcId] = useState("");
  const [referenzId, setReferenzId] = useState("");
  const [prozent, setProzent] = useState(100);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [ergebnis, setErgebnis] = useState<CatchupErgebnis | null>(null);

  function zuruecksetzen() {
    setNpcId("");
    setReferenzId("");
    setProzent(100);
    setFehler(null);
    setErgebnis(null);
  }

  async function absenden(e: React.FormEvent) {
    e.preventDefault();
    if (!npcId || !referenzId) return;
    setLaeuft(true);
    setFehler(null);
    try {
      const r = await bogenApi.catchup(campaignId, npcId, referenzId, prozent);
      setErgebnis(r);
    } catch (err) {
      setFehler(err instanceof Error ? err.message : "Catch-up fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel="NPC-Catch-up"
      unterzeile="NPC auf das Niveau eines PCs heben — EP, Vermögen, Ausrüstung automatisch"
      kennung="npc-catchup"
      onSchliessen={() => {
        onSchliessen();
        zuruecksetzen();
      }}
    >
      {!ergebnis ? (
        <form onSubmit={absenden} style={{ display: "flex", flexDirection: "column", gap: 16, padding: 8 }}>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span>NPC (wird hochgezogen)</span>
            <select value={npcId} onChange={(e) => setNpcId(e.target.value)} required style={{ padding: 10 }}>
              <option value="" disabled>
                Bitte wählen …
              </option>
              {npcs.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.name}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span>Referenz-PC (Messlatte)</span>
            <select value={referenzId} onChange={(e) => setReferenzId(e.target.value)} required style={{ padding: 10 }}>
              <option value="" disabled>
                Bitte wählen …
              </option>
              {pcs.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span>
              Skalierung: <strong style={{ color: "var(--neon)" }}>{prozent}%</strong>{" "}
              {prozent > 100 ? "(stärker als der PC — Boss)" : prozent < 100 ? "(bewusst schwächer)" : "(gleichauf)"}
            </span>
            <input
              type="range"
              min={10}
              max={300}
              step={5}
              value={prozent}
              onChange={(e) => setProzent(Number(e.target.value))}
            />
          </label>
          {fehler && <p style={{ color: "var(--nein)" }}>{fehler}</p>}
          <button
            type="submit"
            disabled={laeuft || !npcId || !referenzId}
            style={{
              padding: "12px 20px",
              background: "color-mix(in srgb, var(--neon) 20%, transparent)",
              border: "1px solid var(--neon)",
              borderRadius: "var(--radius)",
              color: "var(--neon)",
              cursor: laeuft ? "default" : "pointer",
              fontWeight: 600,
              fontSize: "1rem",
            }}
          >
            {laeuft ? "Läuft …" : "Catch-up durchführen"}
          </button>
        </form>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12, padding: 8 }}>
          <p>
            <strong>{npcs.find((n) => n.id === npcId)?.name}</strong> wurde auf {ergebnis.erfahrungGesamt} EP gesamt
            und {ergebnis.budgetGeld}¥ Budget gehoben ({prozent}% von {ergebnis.referenzName}).
          </p>
          {ergebnis.steigerungen.length > 0 && (
            <div>
              <strong>Gesteigert:</strong>
              <ul>
                {ergebnis.steigerungen.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
          {ergebnis.gekauft.length > 0 && (
            <div>
              <strong>Eingekauft &amp; ausgerüstet:</strong>
              <ul>
                {ergebnis.gekauft.map((g, i) => (
                  <li key={i}>{g}</li>
                ))}
              </ul>
            </div>
          )}
          {ergebnis.steigerungen.length === 0 && ergebnis.gekauft.length === 0 && (
            <p style={{ color: "var(--text-leise)" }}>
              Keine Steigerung/Einkauf möglich (z.B. kein Tutorial-Shop oder KI-Fehler) — die EP/das Geld wurden
              trotzdem gutgeschrieben.
            </p>
          )}
          <button
            type="button"
            onClick={() => {
              onSchliessen();
              zuruecksetzen();
            }}
            style={{
              padding: "10px 18px",
              background: "transparent",
              border: "1px solid var(--text-leise)",
              borderRadius: "var(--radius)",
              color: "var(--text-leise)",
              cursor: "pointer",
            }}
          >
            Schließen
          </button>
        </div>
      )}
    </Fenster>
  );
}
