import { useEffect, useState } from "react";
import type { RuestungsArt } from "../items/api";
import { Fenster } from "../shell/Fenster";
import { bogenApi, type RuestungTrefferErgebnis } from "../traits/bogenApi";

/**
 * "3× Tödlich" eingeben, Rüstung und Gesundheit rechnen automatisch mit.
 *
 * Genau der Ablauf aus dem Konzept — und mehr als Art und Stärke braucht es
 * nicht: die getragene Rüstung wirkt als **ein Pool**, es gibt keine
 * Körperzonen und damit nichts zu zielen. Welche Teile der Kästchenschaden
 * aufbraucht (dichtestes zuerst), rechnet der Server; siehe
 * backend/app/kampf/ruestung.py und docs/api/ruestung.md.
 *
 * Was zurückkommt, wird ausdrücklich angezeigt statt stillschweigend
 * verbucht: wer nur "3× Tödlich" eintippt, soll sehen, was daraus geworden
 * ist — sonst wirkt die Automatik wie ein Zufallsgenerator.
 */

const ARTEN: { wert: RuestungsArt; label: string; hinweis: string }[] = [
  { wert: "aggraviert", label: "Unheilbar", hinweis: "z.B. eine Explosion — trifft immer voll auf die Rüstung durch." },
  { wert: "schwer", label: "Tödlich", hinweis: "z.B. Schusswaffen — Rüstung wandelt es in Schlagschaden um." },
  { wert: "schlag", label: "Schlag", hinweis: "z.B. Faustschlag — Rüstung halbiert, was durchkommt." },
];

function artLabel(art: RuestungsArt) {
  return ARTEN.find((a) => a.wert === art)?.label ?? art;
}

export function RuestungsTreffer({
  campaignId,
  personId,
  offen,
  onSchliessen,
  onAngewendet,
}: {
  campaignId: string;
  personId: string;
  offen: boolean;
  onSchliessen: () => void;
  /** Nach einem angewendeten Treffer — der Aufrufer lädt daraufhin neu. */
  onAngewendet: () => void | Promise<void>;
}) {
  const [art, setArt] = useState<RuestungsArt>("schlag");
  const [staerke, setStaerke] = useState(1);
  const [laeuft, setLaeuft] = useState(false);
  const [ergebnis, setErgebnis] = useState<RuestungTrefferErgebnis | null>(null);

  // Bei jedem Öffnen frisch beginnen — sonst zeigt das Fenster noch das
  // Ergebnis des letzten Treffers, wenn ein neuer angesagt wird.
  useEffect(() => {
    if (offen) {
      setArt("schlag");
      setStaerke(1);
      setErgebnis(null);
    }
  }, [offen]);

  async function anwenden() {
    setLaeuft(true);
    try {
      setErgebnis(await bogenApi.ruestungTreffer(campaignId, personId, art, staerke));
      await onAngewendet();
    } finally {
      setLaeuft(false);
    }
  }

  const zerstoert = ergebnis?.betroffen.filter((b) => b.zerstoert) ?? [];

  return (
    <Fenster
      offen={offen}
      titel="Treffer eintragen"
      unterzeile="Rüstung rechnet automatisch mit"
      kennung="ruestungs-treffer"
      onSchliessen={onSchliessen}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 14, padding: 4 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ fontSize: "0.9em", color: "var(--text-leise)" }}>Schadensart</span>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {ARTEN.map((a) => (
              <button
                key={a.wert}
                type="button"
                data-aktiv={art === a.wert}
                onClick={() => setArt(a.wert)}
                title={a.hinweis}
                style={{
                  borderColor: art === a.wert ? "var(--neon)" : undefined,
                  color: art === a.wert ? "var(--neon)" : undefined,
                }}
              >
                {a.label}
              </button>
            ))}
          </div>
        </div>

        <label style={{ display: "flex", alignItems: "center", gap: 10, fontSize: "0.9em" }}>
          Stärke
          <input
            type="number"
            min={0}
            value={staerke}
            onChange={(e) => setStaerke(Math.max(0, Number(e.target.value)))}
            style={{ width: 70 }}
          />
        </label>

        <button type="button" onClick={anwenden} disabled={laeuft} style={{ fontWeight: 600 }}>
          Treffer anwenden
        </button>

        {ergebnis && (
          <div style={{ fontSize: "0.9em", color: "var(--text-leise)", display: "flex", flexDirection: "column", gap: 4 }}>
            <p style={{ margin: 0 }}>
              Durchgekommen:{" "}
              <strong>
                {ergebnis.hpMenge} {artLabel(ergebnis.hpArt)}
              </strong>
              {ergebnis.betroffen.length === 0 && " — ohne Rüstung voll angekommen"}
            </p>
            {ergebnis.kaestchenSchaden > 0 && (
              <p style={{ margin: 0 }}>
                Rüstung: <strong>−{ergebnis.kaestchenSchaden}</strong> Kästchen (
                {ergebnis.betroffen.map((b) => `${b.name} −${b.verlust}`).join(", ")})
              </p>
            )}
            {zerstoert.length > 0 && (
              <p style={{ margin: 0, color: "var(--nein)" }}>
                Zerstört: <strong>{zerstoert.map((b) => b.name).join(", ")}</strong> — liegt jetzt im Mitgeführten
                und schützt nicht mehr, bis es repariert ist.
              </p>
            )}
          </div>
        )}
      </div>
    </Fenster>
  );
}
