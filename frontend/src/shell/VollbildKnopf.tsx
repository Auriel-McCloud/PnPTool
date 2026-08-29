import { useEffect, useState } from "react";

/**
 * Schaltet die Anzeige auf Vollbild — ohne Adressleiste und Browser-Ränder
 * fühlt sich das Commlink wie ein eigenes Gerät an.
 *
 * Der Browser lässt Vollbild nur als Reaktion auf eine Nutzeraktion zu,
 * deshalb ein Knopf und kein automatischer Aufruf. Wo die Funktion fehlt
 * (iOS-Safari am iPhone kennt sie nicht), erscheint der Knopf gar nicht
 * erst — ein Schalter, der nichts tut, ist schlimmer als keiner.
 */
export function VollbildKnopf() {
  const [aktiv, setAktiv] = useState(false);
  const [moeglich, setMoeglich] = useState(false);

  useEffect(() => {
    setMoeglich(document.fullscreenEnabled ?? false);
    // Der Zustand ändert sich auch ohne unser Zutun — etwa wenn jemand
    // Escape drückt oder das System das Vollbild beendet.
    const merken = () => setAktiv(document.fullscreenElement !== null);
    merken();
    document.addEventListener("fullscreenchange", merken);
    return () => document.removeEventListener("fullscreenchange", merken);
  }, []);

  if (!moeglich) return null;

  async function umschalten() {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else {
        await document.documentElement.requestFullscreen();
      }
    } catch {
      // Manche Browser lehnen den Wechsel ab (eingebettet, Richtlinie).
      // Kein Grund für eine Fehlermeldung — der Knopf bleibt einfach wirkungslos.
    }
  }

  return (
    <button
      type="button"
      className="cl-werkzeug"
      onClick={umschalten}
      aria-pressed={aktiv}
      title={aktiv ? "Vollbild verlassen" : "Vollbild"}
    >
      {aktiv ? "⤡" : "⤢"}
    </button>
  );
}
