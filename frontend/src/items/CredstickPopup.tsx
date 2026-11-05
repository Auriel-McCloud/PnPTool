import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import type { Gegenstand } from "./api";
import "./wegwerfen.css";

/**
 * Credstick auf-/entladen, oder (SL) Geld direkt erzeugen (05.11.2026,
 * Tresor-Modell — siehe docs/wiki/entities/gegenstand-transfer.md).
 *
 * Ein Betrag-Eingabefeld statt Inline-Formular an der Kachel — Marks
 * Vorgabe: Ziel-/Ressourcen-Einträge laufen über gestylte Commlink-Popups,
 * nie über Inline-Formulare (siehe WeitergebenPopup.tsx fürs selbe Muster).
 */
export function CredstickPopup({
  item,
  modus,
  offen,
  onBestaetigen,
  onAbbrechen,
  laeuft = false,
  fehler = null,
}: {
  item: Gegenstand;
  /** "laden": Kapital -> Credstick. "entladen": Credstick -> Kapital.
   *  "sl-laden": SL erzeugt Geld direkt, ohne Kapitalabzug. */
  modus: "laden" | "entladen" | "sl-laden";
  offen: boolean;
  onBestaetigen: (betrag: number) => void;
  onAbbrechen: () => void;
  /** Läuft gerade eine Anfrage? Sperrt die Eingabe, bis sie durch ist. */
  laeuft?: boolean;
  fehler?: string | null;
}) {
  const [betrag, setBetrag] = useState("");

  // Frisches Feld bei jedem Öffnen — sonst steht noch der letzte Versuch drin.
  useEffect(() => {
    if (offen) setBetrag("");
  }, [offen]);

  const titel =
    modus === "laden" ? `${item.name} aufladen` : modus === "entladen" ? `${item.name} abheben` : `${item.name}: Geld erzeugen`;
  const hinweis =
    modus === "laden"
      ? "Das Geld verlässt dein Kapital und hängt danach am Credstick — wer ihn hat, hat auch das Geld."
      : modus === "entladen"
        ? "Das Geld wandert zurück auf dein eigenes Kapital."
        : "Erzeugt Geld direkt auf diesem Credstick, ohne es irgendwo abzuziehen.";
  const knopfText = modus === "laden" ? "Aufladen" : modus === "entladen" ? "Abheben" : "Erzeugen";

  const wert = Math.trunc(Number(betrag));
  const gueltig = betrag.trim() !== "" && Number.isFinite(wert) && wert > 0;

  return (
    <Fenster offen={offen} titel={titel} kennung={`credstick:${modus}:${item.id}`} onSchliessen={onAbbrechen}>
      <p className="ww-hinweis">{hinweis}</p>
      <p className="ww-beruhigung">Aktuell geladen: {item.geladenesGeld.toLocaleString("de-AT")}¥</p>
      <input
        type="number"
        min={1}
        step={1}
        value={betrag}
        onChange={(e) => setBetrag(e.target.value)}
        placeholder="Betrag in ¥"
        autoFocus
        disabled={laeuft}
        style={{
          width: "100%",
          boxSizing: "border-box",
          padding: "8px 10px",
          borderRadius: "var(--radius)",
          border: "1px solid var(--border)",
          background: "var(--card)",
          color: "var(--foreground)",
          font: "inherit",
          marginTop: 4,
        }}
      />
      {fehler && (
        <p className="ww-hinweis" style={{ color: "var(--signal)" }}>
          {fehler}
        </p>
      )}
      <div className="ww-knoepfe">
        <button type="button" className="ww-behalten" disabled={!gueltig || laeuft} onClick={() => onBestaetigen(wert)}>
          {knopfText}
        </button>
        <button type="button" onClick={onAbbrechen} disabled={laeuft}>
          Abbrechen
        </button>
      </div>
    </Fenster>
  );
}
