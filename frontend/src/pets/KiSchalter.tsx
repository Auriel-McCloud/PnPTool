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

  return (
    <div className="gg-wegwerfen">
      <button type="button" disabled={laeuft} onClick={umschalten}>
        {laeuft ? "…" : aktiv ? "KI deaktivieren" : "KI aktivieren"}
      </button>
      <p style={{ margin: "8px 0 0", fontSize: 12, color: "var(--text-leise)" }}>
        {aktiv ? "Die KI ist wach und schwebt über die Tablets." : "Die KI schläft — kein Pet auf den Tablets."}
      </p>
      {fehler && <p style={{ margin: "8px 0 0" }}>{fehler}</p>}
    </div>
  );
}
