import { useState } from "react";
import { zeigeBildAllen } from "./api";
import "./mitteilungen.css";

/**
 * Kleiner Blitz an einem Bild: schickt es allen Spielern als Popup.
 *
 * Marks Wunsch: von einem NPC oder Gegenstand aus zeigen können, wie er
 * aussieht. Bewusst **nur an alle** — Aussehen betrifft alle am Tisch;
 * gerichtete Ansagen bleiben Text.
 *
 * Sitzt an der Stelle, an der das Bild ohnehin schon steht, statt in einem
 * eigenen Menü: Man will es genau dann zeigen, wenn man es gerade ansieht.
 */
export function BildBlitz({
  campaignId,
  bildUrl,
  name,
  klein = false,
}: {
  campaignId: string;
  bildUrl: string;
  /** Wird als Bildunterschrift mitgeschickt ("Mr. Chrome"). */
  name: string;
  /** Kompakte Fassung für Kacheln und Listenzeilen. */
  klein?: boolean;
}) {
  const [zustand, setZustand] = useState<"ruhig" | "sendet" | "fertig" | "fehler">("ruhig");

  if (!bildUrl) return null;

  async function senden(e: React.MouseEvent) {
    // Sonst öffnet der Klick zugleich das Fenster, an dem der Knopf hängt.
    e.stopPropagation();
    if (zustand === "sendet") return;
    setZustand("sendet");
    try {
      await zeigeBildAllen(campaignId, bildUrl, name);
      setZustand("fertig");
      window.setTimeout(() => setZustand("ruhig"), 2000);
    } catch {
      setZustand("fehler");
      window.setTimeout(() => setZustand("ruhig"), 2500);
    }
  }

  const beschriftung: Record<typeof zustand, string> = {
    ruhig: "⚡",
    sendet: "…",
    fertig: "✓",
    fehler: "✕",
  };

  return (
    <button
      type="button"
      className="mt-bild-blitz"
      data-klein={klein ? "true" : undefined}
      data-zustand={zustand}
      onClick={senden}
      title={`Bild allen Spielern zeigen${name ? ` — ${name}` : ""}`}
      aria-label="Bild allen Spielern zeigen"
    >
      {beschriftung[zustand]}
    </button>
  );
}
