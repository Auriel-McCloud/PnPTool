import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { drohnenApi, type MakerProbePool, type MakerProbenErgebnis } from "./api";
import "../traits/levelup.css";
import "../items/wegwerfen.css";

/**
 * Maker-Probe vorm Material-Umbau (26.10.2026, Mark: "es sollte nicht
 * einfach nur möglich sein ein Maschinenteil zu verwenden, sondern der
 * Spieler muss dann eine Probe auf Maker machen").
 *
 * Reiner Selbstbericht wie bei Paralysewurf/Booster-Aktivierung: der
 * Spieler würfelt am Tisch (Pool = Maker + frei gewähltes Attribut, siehe
 * `drohnenApi.makerProbePool`), das Popup zeigt nur den Pool und die
 * benötigten Erfolge und fragt danach "geschafft?" mit drei Antworten.
 * Backend entscheidet die Konsequenz (`drohne_steigern`, Material-Pfad):
 * "ja" verbraucht Material + Wert +1, "patzer" verbraucht NUR Material,
 * "nein" lässt beides unangetastet.
 */
export function MakerProbePopup({
  offen,
  campaignId,
  drohneId,
  traitDefId,
  materialId,
  materialName,
  onAbgeschlossen,
  onSchliessen,
}: {
  offen: boolean;
  campaignId: string;
  drohneId: string;
  traitDefId: string | null;
  materialId: string | null;
  materialName: string;
  onAbgeschlossen: () => void;
  onSchliessen: () => void;
}) {
  const [pool, setPool] = useState<MakerProbePool | null>(null);
  const [gewaehltesAttribut, setGewaehltesAttribut] = useState<string | null>(null);
  const [ladend, setLadend] = useState(true);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [ergebnisText, setErgebnisText] = useState<string | null>(null);

  useEffect(() => {
    if (!offen || !traitDefId) return;
    setLadend(true);
    setFehler(null);
    setErgebnisText(null);
    setGewaehltesAttribut(null);
    drohnenApi
      .makerProbePool(campaignId, drohneId, traitDefId)
      .then(setPool)
      .catch(() => setFehler("Pool konnte nicht geladen werden"))
      .finally(() => setLadend(false));
  }, [offen, campaignId, drohneId, traitDefId]);

  const attributWert = gewaehltesAttribut ? (pool?.attribute.find((a) => a.name === gewaehltesAttribut)?.wert ?? 0) : null;
  const poolGroesse = pool && attributWert != null ? pool.maker + attributWert : null;

  async function melden(ergebnis: MakerProbenErgebnis) {
    if (!traitDefId) return;
    setLaeuft(true);
    setFehler(null);
    try {
      const res = await drohnenApi.steigern(campaignId, drohneId, traitDefId, materialId, ergebnis);
      if (ergebnis === "ja") setErgebnisText(`Geschafft! ${pool?.name} steigt, ${materialName} ist verbraucht.`);
      else if (ergebnis === "patzer") setErgebnisText(`Patzer — ${materialName} ist verbraucht, kein Fortschritt.`);
      else setErgebnisText(`Nicht geschafft — ${materialName} bleibt, kein Fortschritt. Später erneut versuchen.`);
      void res;
      onAbgeschlossen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht gespeichert werden");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel={pool ? `Maker-Probe: ${pool.name}` : "Maker-Probe"}
      kennung={`maker-probe:${traitDefId ?? ""}`}
      onSchliessen={onSchliessen}
    >
      {ladend && <p style={{ color: "var(--text-leise)" }}>Lade Pool…</p>}

      {!ladend && pool && !ergebnisText && (
        <>
          <p className="lu-hinweis">
            Maker (Hardware): <strong>{pool.maker}</strong> — wähle dazu ein Attribut, mit dem du würfelst.
          </p>
          <div className="lu-zahlart" style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 10 }}>
            {pool.attribute.map((a) => (
              <button
                key={a.name}
                type="button"
                className="lu-zahlart-knopf"
                data-aktiv={gewaehltesAttribut === a.name}
                onClick={() => setGewaehltesAttribut(a.name)}
              >
                {a.name} {a.wert}
              </button>
            ))}
          </div>

          {poolGroesse != null && (
            <p className="lu-hinweis">
              Pool: <strong>{pool.maker} + {attributWert}</strong> = <strong>{poolGroesse}</strong> Würfel. Du
              brauchst <strong>{pool.benoetigteErfolge}</strong> Erfolge.
            </p>
          )}

          {fehler && <p className="lu-fehler">{fehler}</p>}

          <p className="lu-hinweis" style={{ marginTop: 10 }}>Am Tisch gewürfelt — geschafft?</p>
          <div className="ww-knoepfe">
            <button type="button" className="ww-behalten" disabled={laeuft || !gewaehltesAttribut} onClick={() => melden("ja")}>
              ✓ Ja
            </button>
            <button type="button" disabled={laeuft || !gewaehltesAttribut} onClick={() => melden("nein")}>
              ✗ Nein
            </button>
            <button
              type="button"
              style={{ color: "var(--nein)", borderColor: "var(--nein)" }}
              disabled={laeuft || !gewaehltesAttribut}
              onClick={() => melden("patzer")}
            >
              ⚡ Patzer
            </button>
          </div>
        </>
      )}

      {ergebnisText && (
        <>
          <p className="ww-beruhigung">{ergebnisText}</p>
          <div className="ww-knoepfe">
            <button type="button" className="ww-behalten" onClick={onSchliessen}>
              Schließen
            </button>
          </div>
        </>
      )}
    </Fenster>
  );
}
