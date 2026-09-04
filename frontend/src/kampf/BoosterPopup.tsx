import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { kampfApi, type BoosterStatus, type Kampf } from "./api";
import "./booster.css";

/**
 * Reflex-Booster: Popup beim Drankommen, Ampel, Paralysewurf.
 *
 * Marks Ablauf (04.09.2026):
 *
 *   "wenn er dran kommt per Pop-up gefragt 'Reflex Booster aktivieren?' Wenn
 *   er ja sagt wird automatisch mit seinen Standard Initiative wert, also
 *   Geistes Schärfe + Geschicklichkeit ohne Bonus, gewürfelt, dadurch sollte
 *   er langsamer sein als bei seinem ersten Wurf"
 *
 * Der Zweitwurf nutzt bewusst den Pool **ohne** Boosterbonus — genau das
 * macht die Zusatzaktion zum Risiko: sie kommt meist später.
 */

/** Ampel: drei Punkte, die sich bei Nutzung füllen und beim Aussetzen leeren. */
export function Ampel({ stand, max = 3 }: { stand: number; max?: number }) {
  return (
    <span className="bo-ampel" title={`Überhitzung ${stand} von ${max}`}>
      {Array.from({ length: max }, (_, i) => (
        <span key={i} className="bo-punkt" data-an={i < stand} data-heiss={stand >= max} />
      ))}
    </span>
  );
}

export function BoosterPopup({
  campaignId,
  kampf,
  eigenePersonId,
  onGeaendert,
}: {
  campaignId: string;
  kampf: Kampf | null;
  eigenePersonId: string | null;
  onGeaendert: () => void;
}) {
  const [status, setStatus] = useState<BoosterStatus | null>(null);
  const [gefragt, setGefragt] = useState<string | null>(null);
  const [wert, setWert] = useState("");
  const [sendet, setSendet] = useState(false);
  const [modus, setModus] = useState<"frage" | "wurf" | "paralyse" | null>(null);

  // Ist der eigene Stammeintrag gerade dran?
  const eigener = kampf?.teilnehmer.find(
    (t) => t.personId === eigenePersonId && !t.zusatzzug,
  );
  const binDran = Boolean(eigener && kampf?.amZug === eigener.id);
  // Der Zusatzzug ist gerade dran — danach folgt ggf. der Paralysewurf.
  const zusatzDran = kampf?.teilnehmer.some(
    (t) => t.personId === eigenePersonId && t.zusatzzug && kampf.amZug === t.id,
  );

  useEffect(() => {
    if (!campaignId || !eigenePersonId) return;
    kampfApi
      .boosterStatus(campaignId)
      .then(setStatus)
      .catch(() => setStatus(null));
  }, [campaignId, eigenePersonId, kampf?.amZug]);

  // Beim Drankommen einmal fragen — nicht bei jedem Nachladen erneut.
  useEffect(() => {
    if (!binDran || !status?.hatBooster || !status.darfAktivieren) return;
    const kennung = `${kampf?.runde}-${eigener?.id}`;
    if (gefragt === kennung) return;
    setGefragt(kennung);
    setModus("frage");
  }, [binDran, status, kampf?.runde, eigener?.id, gefragt]);

  // Nach dem Zusatzzug: Paralysewurf, wenn die Ampel voll ist.
  useEffect(() => {
    if (zusatzDran && status?.paralyseFaellig) setModus("paralyse");
  }, [zusatzDran, status?.paralyseFaellig]);

  async function aktivieren() {
    const zahl = Number(wert);
    if (!Number.isInteger(zahl) || zahl < 0) return;
    setSendet(true);
    try {
      await kampfApi.boosterAktivieren(campaignId, zahl);
      setModus(null);
      setWert("");
      onGeaendert();
    } finally {
      setSendet(false);
    }
  }

  async function paralyseMelden(geschafft: boolean) {
    if (!status?.teilnehmerId) return;
    setSendet(true);
    try {
      await kampfApi.paralyse(campaignId, status.teilnehmerId, geschafft);
      setModus(null);
      onGeaendert();
    } finally {
      setSendet(false);
    }
  }

  if (!modus || !status?.hatBooster) return null;

  return createPortal(
    <div className="bo-huelle" role="alertdialog">
      <div className="bo-fenster">
        {modus === "frage" && (
          <>
            <h3 className="bo-titel">{status.boosterName} aktivieren?</h3>
            <p className="bo-text">
              Du handelst ein zweites Mal — aber mit deinem <strong>normalen</strong> Pool,
              ohne Boosterbonus. Meist kommst du dadurch später dran.
            </p>
            <div className="bo-zeile">
              <Ampel stand={status.ampel} max={status.ampelMax} />
              <span className="bo-hinweis">
                {status.zusatzaktionenMax < 0
                  ? "jede Runde möglich"
                  : `${status.zusatzaktionenMax - status.bereitsGenutzt} von ${status.zusatzaktionenMax} übrig`}
              </span>
            </div>
            {status.ampel >= status.ampelMax - 1 && (
              <p className="bo-warnung">
                Noch eine Nutzung und du überhitzt — dann folgt der Paralysewurf.
              </p>
            )}
            <div className="bo-knoepfe">
              <button type="button" onClick={() => setModus("wurf")}>
                Ja, aktivieren
              </button>
              <button type="button" className="bo-nein" onClick={() => setModus(null)}>
                Nein
              </button>
            </div>
          </>
        )}

        {modus === "wurf" && (
          <>
            <h3 className="bo-titel">Zweitwurf</h3>
            <div className="bo-pool">
              <span className="bo-poolzahl">{status.zweitwurfPool}</span>
              <span className="bo-poolinfo">
                Würfel
                <em>ohne Boosterbonus</em>
              </span>
            </div>
            <div className="bo-eingabe">
              <label htmlFor="bo-erfolge">Erfolge</label>
              <input
                id="bo-erfolge"
                type="number"
                min={0}
                inputMode="numeric"
                value={wert}
                onChange={(e) => setWert(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void aktivieren();
                }}
                autoFocus
              />
            </div>
            <div className="bo-knoepfe">
              <button type="button" onClick={aktivieren} disabled={sendet || wert === ""}>
                {sendet ? "…" : "Eintragen"}
              </button>
              <button type="button" className="bo-nein" onClick={() => setModus(null)}>
                Abbrechen
              </button>
            </div>
          </>
        )}

        {modus === "paralyse" && (
          <>
            <h3 className="bo-titel">Überhitzung</h3>
            <p className="bo-text">
              Dein Chrom glüht. Wirf <strong>{status.paralysePool}</strong> Würfel
              (Geistesschärfe + Willenskraft) gegen <strong>{status.paralyseSchwelle}</strong> Erfolge.
            </p>
            <p className="bo-warnung">
              Misslingt der Wurf, setzt du die nächste Runde aus.
            </p>
            <div className="bo-knoepfe">
              <button type="button" onClick={() => paralyseMelden(true)} disabled={sendet}>
                Geschafft
              </button>
              <button type="button" className="bo-nein" onClick={() => paralyseMelden(false)} disabled={sendet}>
                Nicht geschafft
              </button>
            </div>
          </>
        )}
      </div>
    </div>,
    document.body,
  );
}
