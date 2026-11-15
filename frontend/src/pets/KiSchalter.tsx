import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { petsApi } from "./api";

/**
 * KI am Gegenstand an-/ausschalten (Mark, 15.11.2026: „eine KI, die er
 * mitführt, kann ja auch wieder deaktiviert werden — da geht es eigentlich
 * nur um das Desktop-Pet“). Der Besitzer sieht den Knopf im Gegenstand-
 * fenster; die SL schaltet im Bearbeiten-Formular (KiKopplungWahl).
 */
export function KiSchalter({
  campaignId,
  itemId,
  aktiv: aktivVorher,
  onGeaendert,
}: {
  campaignId: string;
  itemId: string;
  aktiv: boolean;
  onGeaendert?: () => void;
}) {
  const [aktiv, setAktiv] = useState(aktivVorher);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  useEffect(() => setAktiv(aktivVorher), [aktivVorher]);

  async function umschalten() {
    setLaeuft(true);
    setFehler(null);
    try {
      const neu = await petsApi.kiAktiv(campaignId, itemId, !aktiv);
      setAktiv(neu.kiAktiv);
      onGeaendert?.();
    } catch (e) {
      setFehler(e instanceof ApiError ? e.message : "Umschalten ging nicht.");
    } finally {
      setLaeuft(false);
    }
  }

  // Im Fensterkopf links neben „Beschreibung“, gleiche Optik, ohne
  // Überschrift und Statuszeile (Mark, 15.11.2026: „fügt sich besser ins
  // Bild“). Ein Fehler steht kurz im Knopf und als Tooltip.
  return (
    <button
      type="button"
      className="gg-lesen-knopf"
      disabled={laeuft}
      onClick={umschalten}
      title={fehler ?? undefined}
    >
      {laeuft ? "…" : fehler ? "Ging nicht" : aktiv ? "KI deaktivieren" : "KI aktivieren"}
    </button>
  );
}
