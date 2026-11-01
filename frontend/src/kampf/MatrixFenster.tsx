import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { WuerfelZehn } from "../traits/WuerfelZehn";
import { kampfApi, type MatrixTreffer, type MatrixZeile } from "./api";
import "./matrix.css";

const EINSTIEG = new Set(["Brute Force", "Schleichen"]);

export function MatrixFenster({
  offen,
  campaignId,
  fertigkeit,
  pool,
  onSchliessen,
}: {
  offen: boolean;
  campaignId: string;
  fertigkeit: string;
  pool: number;
  onSchliessen: () => void;
}) {
  const [liste, setListe] = useState<MatrixZeile[]>([]);
  const [ziel, setZiel] = useState<MatrixZeile | null>(null);
  const [erfolge, setErfolge] = useState("");
  const [hinweis, setHinweis] = useState("");
  const [treffer, setTreffer] = useState<MatrixTreffer | null>(null);
  const [wahl, setWahl] = useState<Record<string, number>>({});
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!offen) return;
    setZiel(null);
    setErfolge("");
    setHinweis("");
    setTreffer(null);
    setWahl({});
    kampfApi.matrix(campaignId).then((u) => setListe(u.teilnehmer)).catch(() => setHinweis("Kein laufender Kampf."));
  }, [offen, campaignId]);

  const punkte = treffer?.punkte ?? 0;
  const verbraucht = Object.values(wahl).reduce((s, n) => s + n, 0);
  const frei = punkte - verbraucht;

  async function senden(navErfolg?: boolean) {
    const n = navErfolg === undefined ? Number(erfolge) : navErfolg ? 1 : 0;
    if (navErfolg === undefined && (erfolge === "" || Number.isNaN(n) || n < 0)) return;
    setBusy(true);
    setHinweis("");
    try {
      if (fertigkeit === "Matrix-Navigation") {
        const r = await kampfApi.matrixNavigation(campaignId, n);
        setHinweis(r.gesehen ? "Gegnerisches ICE ist für diesen Kampf sichtbar." : "Kein Erfolg, nichts gesehen.");
        const u = await kampfApi.matrix(campaignId);
        setListe(u.teilnehmer);
      } else if (fertigkeit === "Electronic Warfare") {
        const r = await kampfApi.matrixEw(campaignId, n);
        setHinweis(r.bonus ? `Party-ICE +${r.bonus} für 3 Runden.` : "1 Erfolg gibt keinen Bonus.");
      } else if (ziel) {
        const r = await kampfApi.matrixTreffer(campaignId, ziel.personId, n, fertigkeit);
        setTreffer(r);
        setWahl({});
        if (r.punkte < 1) {
          setHinweis(`ICE ${r.iceVorher} → ${r.iceNachher}. Nichts zum Schalten.`);
        }
      }
    } catch (e) {
      setHinweis(e instanceof Error ? e.message : "Das hat nicht geklappt.");
    } finally {
      setBusy(false);
    }
  }

  function schalter(id: string, runden: number) {
    setWahl((alt) => {
      const neu = { ...alt };
      if (neu[id] === runden) delete neu[id];
      else neu[id] = runden;
      const summe = Object.values(neu).reduce((s, n) => s + n, 0);
      if (summe > punkte) return alt;
      return neu;
    });
  }

  async function bestaetigen() {
    if (!ziel || !treffer) return;
    setBusy(true);
    try {
      await kampfApi.matrixBestaetigen(
        campaignId,
        ziel.personId,
        Object.entries(wahl).map(([id, runden]) => ({ id, runden })),
      );
      onSchliessen();
    } catch (e) {
      setHinweis(e instanceof Error ? e.message : "Nicht übernommen.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Fenster offen={offen} titel={fertigkeit} kennung={`matrix-${fertigkeit}`} onSchliessen={onSchliessen}>
      <div className="mx">
        <div className="mx-pool-kachel">
          <span className="mx-pool-titel">Würfelpool</span>
          <span className="mx-pool-ziffer">
            {pool}
            <WuerfelZehn groesse={15} />
          </span>
        </div>
        {hinweis && <p className="mx-hinweis">{hinweis}</p>}

        {EINSTIEG.has(fertigkeit) && !treffer && (
          <ul className="mx-liste">
            {liste.map((z) => (
              <li key={z.personId}>
                <button
                  type="button"
                  disabled={!z.klickbar}
                  data-aktiv={ziel?.personId === z.personId}
                  onClick={() => setZiel(z)}
                >
                  <span>{z.name}</span>
                  <em>{z.ice === null ? "ICE verdeckt" : `ICE ${z.ice}`}</em>
                </button>
                {(z.aus ?? []).map((a) => (
                  <button
                    key={a.id}
                    type="button"
                    className="mx-aus"
                    onClick={() => kampfApi.matrixAn(campaignId, a.id).then(() => kampfApi.matrix(campaignId).then((u) => setListe(u.teilnehmer)))}
                  >
                    <span>{a.name}</span>
                    <em>{a.runden}</em>
                  </button>
                ))}
              </li>
            ))}
          </ul>
        )}

        {fertigkeit === "Matrix-Navigation" && !treffer && (
          <div className="mx-nav">
            <p>Schwierigkeitsgrad wird von der SL festgelegt.</p>
            <div className="mx-aktionen">
              <button type="button" className="mx-ok" disabled={busy} onClick={() => senden(true)}>Erfolg</button>
              <button type="button" disabled={busy} onClick={() => senden(false)}>Fehlschlag</button>
            </div>
          </div>
        )}

        {fertigkeit !== "Matrix-Navigation" && (fertigkeit === "Electronic Warfare" || ziel) && !treffer && (
          <label className="mx-eingabe">
            Erfolge
            <input
              type="number"
              inputMode="numeric"
              value={erfolge}
              placeholder="0"
              onChange={(e) => setErfolge(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && senden()}
            />
          </label>
        )}

        {!treffer && fertigkeit !== "Matrix-Navigation" && (fertigkeit !== "Brute Force" && fertigkeit !== "Schleichen" || ziel) && (
          <button type="button" className="mx-ok" disabled={busy || erfolge === ""} onClick={() => senden()}>
            Eintragen
          </button>
        )}

        {treffer && treffer.punkte > 0 && (
          <>
            <div className="mx-punkte-block">
              <span className="mx-punkte-titel">Punkte</span>
              <span className="mx-punkte">{frei}</span>
            </div>
            <p className="mx-hinweis">ICE {treffer.iceVorher} → {treffer.iceNachher}.</p>
            <ul className="mx-liste">
              {treffer.ziele.map((z) => (
                <li key={z.id} className="mx-ziel">
                  <span>{z.name}</span>
                  <span className="mx-schalter">
                    {[1, 2, 3].map((n) => (
                      <button
                        key={n}
                        type="button"
                        data-aktiv={wahl[z.id] === n}
                        onClick={() => schalter(z.id, n)}
                      >
                        {n}
                      </button>
                    ))}
                  </span>
                </li>
              ))}
            </ul>
            <div className="mx-aktionen">
              <button type="button" onClick={() => setWahl({})}>Zurücksetzen</button>
              <button type="button" className="mx-ok" disabled={busy} onClick={bestaetigen}>Bestätigen</button>
            </div>
          </>
        )}
      </div>
    </Fenster>
  );
}
