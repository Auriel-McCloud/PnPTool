import { useEffect, useState } from "react";
import { kampfApi, type InitiativePool } from "../kampf/api";
import "./mitteilungen.css";

/**
 * Initiative melden — direkt in der Warnung.
 *
 * Marks Ablauf: *"bei würfelt Initiative, bereits bei dem jeweiligen Spielern
 * seine Initiative angezeigt wird, er die Möglichkeit hat seinen manuell
 * gewürfelten wert einzugeben, damit das bei mir in der Initiative reinfolge
 * automatisch angezeigt wird"*.
 *
 * Der Spieler sieht **seinen Pool**, würfelt physisch, tippt die Erfolge —
 * fertig. Kein Wechsel in einen anderen Bereich, kein Zurufen.
 */
export function InitiativeMelden({
  campaignId,
  onFertig,
}: {
  campaignId: string;
  onFertig?: () => void;
}) {
  const [daten, setDaten] = useState<InitiativePool | null>(null);
  const [wert, setWert] = useState("");
  const [sendet, setSendet] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [fertig, setFertig] = useState(false);

  useEffect(() => {
    let weg = false;
    kampfApi
      .initiativePool(campaignId)
      .then((d) => {
        if (weg) return;
        setDaten(d);
        // Schon gemeldet? Dann den Wert zeigen statt ein leeres Feld.
        if (d.gemeldet !== null && d.gemeldet > 0) {
          setWert(String(d.gemeldet));
          setFertig(true);
        }
      })
      .catch(() => {
        // Kein eigener Charakter oder kein Kampf — dann eben ohne Eingabe.
        if (!weg) setDaten(null);
      });
    return () => {
      weg = true;
    };
  }, [campaignId]);

  async function melden() {
    if (!daten?.teilnehmerId) return;
    const zahl = Number(wert);
    if (!Number.isInteger(zahl) || zahl < 0) {
      setFehler("Bitte eine ganze Zahl eingeben");
      return;
    }
    setSendet(true);
    setFehler(null);
    try {
      await kampfApi.meldeInitiative(campaignId, daten.teilnehmerId, zahl);
      setFertig(true);
      onFertig?.();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht gemeldet werden");
    } finally {
      setSendet(false);
    }
  }

  async function digitalWuerfeln() {
    // Nur wenn die Kampagne digitales Würfeln erlaubt.
    if (!daten) return;
    setSendet(true);
    try {
      const augen = Array.from({ length: daten.pool }, () => Math.floor(Math.random() * 10) + 1);
      const zehnen = augen.filter((a) => a === 10).length;
      const uebrige = augen.filter((a) => a >= 6 && a < 10).length;
      const erfolge = zehnen >= 2 ? zehnen * 2 + uebrige : zehnen + uebrige;
      setWert(String(erfolge));
    } finally {
      setSendet(false);
    }
  }

  // Kein Kampf oder kein eigener Eintrag — dann gibt es nichts zu melden.
  if (!daten || !daten.teilnehmerId) return null;

  return (
    <div className="wn-init">
      <div className="wn-init-pool">
        <span className="wn-init-zahl">{daten.pool}</span>
        <span className="wn-init-text">
          Würfel
          <em>
            Geistesschärfe {daten.geistesschaerfe} + Geschicklichkeit {daten.geschicklichkeit}
            {daten.cyberwareMod !== 0 && ` ${daten.cyberwareMod > 0 ? "+" : ""}${daten.cyberwareMod} Chrom`}
          </em>
        </span>
      </div>

      {fertig ? (
        <p className="wn-init-fertig">
          Gemeldet: <strong>{wert}</strong> — du stehst in der Liste.
        </p>
      ) : (
        <>
          <div className="wn-init-eingabe">
            <label htmlFor="wn-erfolge">Erfolge</label>
            <input
              id="wn-erfolge"
              type="number"
              min={0}
              inputMode="numeric"
              value={wert}
              onChange={(e) => setWert(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void melden();
              }}
              placeholder="0"
              autoFocus
            />
            <button type="button" onClick={melden} disabled={sendet || wert === ""}>
              {sendet ? "…" : "Melden"}
            </button>
          </div>

          {daten.digitalErlaubt && (
            <button type="button" className="wn-init-digital" onClick={digitalWuerfeln} disabled={sendet}>
              ⚄ digital würfeln
            </button>
          )}

          <p className="wn-init-hinweis">
            Alles über 5 zählt · zwei Zehnen zählen wie vier Erfolge
          </p>
        </>
      )}

      {fehler && <p className="wn-init-fehler">{fehler}</p>}
    </div>
  );
}
