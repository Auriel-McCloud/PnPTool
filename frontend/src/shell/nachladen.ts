import { useEffect, useRef } from "react";

type Optionen = {
  /** Abstand zwischen zwei stillen Abfragen. Am Tisch reichen 5 Sekunden. */
  takt?: number;
  /** Takt aus — z.B. solange ein Bearbeiten-Fenster offen ist. */
  pausiert?: boolean;
  /** false: gar nicht laufen (noch keine Kampagne). */
  aktiv?: boolean;
  /** Wechselt die Quelle (Kampagne, Person) — dann sofort neu holen. */
  quelle?: string;
};

/**
 * Still nachladen, solange der Tab sichtbar ist.
 *
 * Gleiche Bauart wie `useKampf`: kein Popup, kein Remount, nur Daten.
 * Eine eigene Aktion ruft `ungueltig` unmittelbar vor dem Setzen des
 * frischen Stands — eine ältere Antwort, die danach ankommt, wird
 * verworfen und überschreibt ihn nicht.
 *
 * Im Hintergrund (Handy in der Tasche) wird nicht gefragt. Beim
 * Zurückkommen sofort, nicht erst nach dem nächsten Takt.
 */
export function useNachladen<T>(
  laden: () => Promise<T>,
  anwenden: (daten: T) => void,
  { takt = 5000, pausiert = false, aktiv = true, quelle = "" }: Optionen = {},
): { ungueltig: () => void } {
  const gen = useRef(0);
  const ladenRef = useRef(laden);
  const anwendenRef = useRef(anwenden);
  ladenRef.current = laden;
  anwendenRef.current = anwenden;

  function ungueltig() {
    gen.current += 1;
  }

  useEffect(() => {
    if (!aktiv || pausiert) return;
    let abgemeldet = false;

    async function holen() {
      if (document.hidden || abgemeldet) return;
      const meine = ++gen.current;
      try {
        const daten = await ladenRef.current();
        if (abgemeldet || meine !== gen.current) return;
        anwendenRef.current(daten);
      } catch {
        // Netz weg — nächster Takt
      }
    }

    void holen();
    const uhr = window.setInterval(() => {
      if (!document.hidden) void holen();
    }, takt);
    const beiSicht = () => {
      if (!document.hidden) void holen();
    };
    document.addEventListener("visibilitychange", beiSicht);
    return () => {
      abgemeldet = true;
      gen.current += 1;
      window.clearInterval(uhr);
      document.removeEventListener("visibilitychange", beiSicht);
    };
  }, [aktiv, pausiert, takt, quelle]);

  return { ungueltig };
}
