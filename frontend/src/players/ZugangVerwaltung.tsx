import { useEffect, useState } from "react";
import { playersApi, type Sitzung } from "./api";

/**
 * Zugangsverwaltung für den Spielleiter: Beitrittscode und wer verbunden ist.
 *
 * Der Code steht bewusst groß und in Monospace da — er wird am Spieltisch
 * vorgelesen oder abfotografiert.
 */
export function ZugangVerwaltung({ campaignId }: { campaignId: string }) {
  const [code, setCode] = useState<string | null>(null);
  const [sitzungen, setSitzungen] = useState<Sitzung[]>([]);
  const [laden, setLaden] = useState(true);

  async function neuLaden() {
    const [c, s] = await Promise.all([playersApi.codeLesen(campaignId), playersApi.sitzungen(campaignId)]);
    setCode(c.code);
    setSitzungen(s);
  }

  useEffect(() => {
    setLaden(true);
    neuLaden().finally(() => setLaden(false));
  }, [campaignId]);

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Zugang…</p>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 640 }}>
      <section>
        <h3>Beitrittscode</h3>
        {code ? (
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <strong
              style={{
                fontFamily: "var(--mono)",
                fontSize: 30,
                letterSpacing: "0.25em",
                color: "var(--neon)",
                textShadow: "0 0 18px var(--neon-schwach)",
              }}
            >
              {code}
            </strong>
            <button type="button" onClick={() => playersApi.codeErzeugen(campaignId).then(neuLaden)}>
              Neu erzeugen
            </button>
            <button type="button" onClick={() => playersApi.codeEntfernen(campaignId).then(neuLaden)}>
              Beitritt schließen
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <span style={{ color: "var(--text-leise)" }}>Zurzeit kann niemand beitreten.</span>
            <button type="button" onClick={() => playersApi.codeErzeugen(campaignId).then(neuLaden)}>
              Code erzeugen
            </button>
          </div>
        )}
        <p style={{ color: "var(--text-leise)", fontSize: "0.85em", marginTop: 8 }}>
          Ein neuer Code macht den alten ungültig. Bereits verbundene Spieler bleiben verbunden — wer draußen
          bleiben soll, wird unten einzeln entfernt.
        </p>
      </section>

      <section>
        <h3>Verbunden ({sitzungen.length})</h3>
        {sitzungen.length === 0 && <p style={{ color: "var(--text-leise)" }}>Noch niemand beigetreten.</p>}
        {sitzungen.map((s) => (
          <div
            key={s.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              flexWrap: "wrap",
              borderBottom: "1px solid var(--linie)",
              padding: "8px 0",
            }}
          >
            <strong>{s.name}</strong>
            <span style={{ color: "var(--text-leise)" }}>
              {s.personName ? `spielt ${s.personName}` : "hat noch keinen Charakter"}
            </span>
            <button
              type="button"
              onClick={() => playersApi.sitzungEntfernen(campaignId, s.id).then(neuLaden)}
              style={{ marginLeft: "auto", borderColor: "var(--signal)", color: "var(--signal)" }}
            >
              Entfernen
            </button>
          </div>
        ))}
      </section>
    </div>
  );
}
