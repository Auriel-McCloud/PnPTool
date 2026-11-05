import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { ApiError } from "../api/client";
import { itemsApi, type Gegenstand } from "./api";
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

/**
 * Aufladen / Abheben / (SL) Geld erzeugen — dieselbe Leiste im Spieler-Fenster
 * und im SL-Objekt, damit das Laden nicht nur an einer der beiden Kacheln hängt.
 */
export function CredstickAktionen({
  item,
  campaignId,
  istSpielleitung = false,
  ohneBesitzer = false,
  onErledigt,
}: {
  item: Gegenstand;
  campaignId: string;
  istSpielleitung?: boolean;
  /** Vorlage oder herrenloses Stück: Umbuchen hat kein Kapital als Gegenkonto. */
  ohneBesitzer?: boolean;
  onErledigt?: (frisch: Gegenstand) => void;
}) {
  const [modus, setModus] = useState<"laden" | "entladen" | "sl-laden" | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);
  const [geladen, setGeladen] = useState(item.geladenesGeld ?? 0);

  useEffect(() => {
    setGeladen(item.geladenesGeld ?? 0);
  }, [item.id, item.geladenesGeld]);

  async function aktion(betrag: number) {
    if (!modus) return;
    setLaeuft(true);
    setFehler(null);
    try {
      const frisch =
        modus === "laden"
          ? await itemsApi.credstickLaden(campaignId, item.id, betrag)
          : modus === "entladen"
            ? await itemsApi.credstickEntladen(campaignId, item.id, betrag)
            : await itemsApi.credstickSlLaden(campaignId, item.id, betrag);
      setGeladen(frisch.geladenesGeld ?? 0);
      setModus(null);
      onErledigt?.(frisch);
    } catch (e) {
      setFehler(e instanceof ApiError ? e.message : e instanceof Error ? e.message : "Hat nicht geklappt.");
    } finally {
      setLaeuft(false);
    }
  }

  function oeffnen(naechster: "laden" | "entladen" | "sl-laden") {
    setFehler(null);
    setModus(naechster);
  }

  return (
    <section className="gg-ablage-wahl">
      <h3>Credstick</h3>
      <p className="gg-ablage-ort">Geladen: {geladen.toLocaleString("de-AT")}¥</p>
      {ohneBesitzer && (
        <p className="gg-ablage-ort">
          Aufladen und Abheben brauchen einen Besitzer. Geld erzeugen legt den Betrag nur auf dieses Stück — eine Vorlage kopiert ihn nicht mit.
        </p>
      )}
      <div className="gg-ablage-knoepfe" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button type="button" onClick={() => oeffnen("laden")} disabled={laeuft}>
          Aufladen
        </button>
        <button type="button" onClick={() => oeffnen("entladen")} disabled={laeuft}>
          Abheben
        </button>
        {istSpielleitung && (
          <button type="button" onClick={() => oeffnen("sl-laden")} disabled={laeuft}>
            Geld erzeugen
          </button>
        )}
      </div>
      {modus && (
        <CredstickPopup
          item={{ ...item, geladenesGeld: geladen }}
          modus={modus}
          offen
          onBestaetigen={aktion}
          onAbbrechen={() => setModus(null)}
          laeuft={laeuft}
          fehler={fehler}
        />
      )}
    </section>
  );
}
