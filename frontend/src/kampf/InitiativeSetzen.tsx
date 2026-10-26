import { useState } from "react";
import { createPortal } from "react-dom";
import type { Teilnehmer } from "./api";
import "./booster.css";

/**
 * Initiative direkt in der Liste ändern — per Klick auf die Zahl.
 *
 * Marks Wunsch (26.10.2026): dieselbe saubere Zahlen-Eingabe wie beim
 * Reflex-Booster-Zweitwurf und bei `mitteilungen/InitiativeMelden.tsx` —
 * leeres Feld statt vorbelegter "0", damit niemand erst eine Ziffer
 * weglöschen muss, um eine mehrstellige Zahl einzutippen. Anders als die
 * Vollbild-Warnung ist das hier **dauerhaft** verfügbar, nicht nur beim
 * Kampfbeginn — ein Tippfehler lässt sich jederzeit korrigieren.
 */
export function InitiativeSetzen({
  teilnehmer,
  onSchliessen,
  onSpeichern,
}: {
  teilnehmer: Teilnehmer;
  onSchliessen: () => void;
  onSpeichern: (wert: number) => Promise<void>;
}) {
  const [wert, setWert] = useState("");
  const [sendet, setSendet] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  async function speichern() {
    const zahl = Number(wert);
    if (!Number.isInteger(zahl) || zahl < 0) {
      setFehler("Bitte eine ganze Zahl eingeben");
      return;
    }
    setSendet(true);
    setFehler(null);
    try {
      await onSpeichern(zahl);
      onSchliessen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Konnte nicht gespeichert werden");
    } finally {
      setSendet(false);
    }
  }

  return createPortal(
    <div className="bo-huelle" role="dialog" onClick={onSchliessen}>
      <div className="bo-fenster" onClick={(e) => e.stopPropagation()}>
        <h3 className="bo-titel">Initiative von {teilnehmer.name}</h3>
        <p className="bo-hinweis" style={{ marginBottom: 10 }}>
          Aktuell {teilnehmer.initiative}
        </p>
        {fehler && <p className="bo-warnung">{fehler}</p>}
        <div className="bo-eingabe">
          <input
            type="number"
            min={0}
            inputMode="numeric"
            value={wert}
            onChange={(e) => setWert(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void speichern();
            }}
            placeholder={String(teilnehmer.initiative)}
            autoFocus
          />
        </div>
        <div className="bo-knoepfe">
          <button type="button" onClick={speichern} disabled={sendet || wert === ""}>
            {sendet ? "…" : "Eintragen"}
          </button>
          <button type="button" className="bo-nein" onClick={onSchliessen}>
            Abbrechen
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
