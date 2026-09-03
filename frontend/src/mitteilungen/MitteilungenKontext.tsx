import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  getMitteilungen,
  markiereAllesGelesen,
  markiereGelesen,
  verbindeLive,
  type Mitteilung,
} from "./api";

/**
 * Hält den Stand der SL-Mitteilungen und die Live-Leitung.
 *
 * Ein Kontext statt Zustand in einer Komponente: Das Blitz-Symbol sitzt in
 * der Werkzeugleiste, das Popup liegt über allem, und der Verlauf steckt in
 * einem Fenster — alle drei brauchen dieselben Daten.
 */

interface MitteilungenWert {
  mitteilungen: Mitteilung[];
  ungelesen: number;
  verbunden: boolean;
  /** Was gerade als Popup aufgeht (null = nichts). */
  aktuell: Mitteilung | null;
  /** Wie viele Popups nach diesem noch warten. */
  wartend: number;
  bestaetigen: () => void;
  allesGelesen: () => void;
  neuLaden: () => void;
}

const Kontext = createContext<MitteilungenWert | null>(null);

export function useMitteilungen(): MitteilungenWert {
  const wert = useContext(Kontext);
  if (!wert) {
    // Kein Fehler: Der Spieler-Login und die Kampagnenauswahl stehen
    // ausserhalb des Anbieters. Dort gibt es schlicht nichts anzuzeigen.
    return {
      mitteilungen: [],
      ungelesen: 0,
      verbunden: false,
      aktuell: null,
      wartend: 0,
      bestaetigen: () => {},
      allesGelesen: () => {},
      neuLaden: () => {},
    };
  }
  return wert;
}

export function MitteilungenAnbieter({
  campaignId,
  personId,
  istSl = false,
  children,
}: {
  campaignId: string;
  /** Eigener Charakter; null bei der Spielleitung. */
  personId: string | null;
  istSl?: boolean;
  children: ReactNode;
}) {
  const [mitteilungen, setMitteilungen] = useState<Mitteilung[]>([]);
  const [verbunden, setVerbunden] = useState(false);
  // Schlange der Popups, die noch gezeigt werden müssen. Kommen zwei
  // Ansagen kurz hintereinander, darf die zweite die erste nicht überdecken.
  const [schlange, setSchlange] = useState<Mitteilung[]>([]);

  // In Refs, damit der Live-Effekt nicht bei jeder Änderung neu verbindet.
  const personIdRef = useRef(personId);
  const istSlRef = useRef(istSl);
  personIdRef.current = personId;
  istSlRef.current = istSl;

  const neuLaden = useCallback(() => {
    getMitteilungen(campaignId)
      .then((stand) => setMitteilungen(stand.mitteilungen))
      .catch(() => {
        /* still: das Commlink soll deshalb nicht kaputtgehen */
      });
  }, [campaignId]);

  useEffect(() => {
    const trennen = verbindeLive(
      campaignId,
      (n) => {
        if (n.typ === "stand") {
          setMitteilungen(n.daten.mitteilungen);
          return;
        }
        if (n.typ === "zurueckgezogen") {
          setMitteilungen((alt) => alt.filter((m) => m.id !== n.daten.id));
          setSchlange((alt) => alt.filter((m) => m.id !== n.daten.id));
          return;
        }
        // Neue Mitteilung
        setMitteilungen((alt) => (alt.some((m) => m.id === n.daten.id) ? alt : [n.daten, ...alt]));
        // Die Spielleitung sieht ihre eigene Ansage nicht als Popup — sie hat
        // sie gerade selbst abgeschickt.
        if (!istSlRef.current) {
          setSchlange((alt) => (alt.some((m) => m.id === n.daten.id) ? alt : [...alt, n.daten]));
        }
      },
      setVerbunden,
    );
    return trennen;
  }, [campaignId]);

  const ungelesen = useMemo(() => {
    if (!personId) return 0;
    return mitteilungen.filter((m) => !m.gelesenVon.includes(personId)).length;
  }, [mitteilungen, personId]);

  const aktuell = schlange[0] ?? null;

  const bestaetigen = useCallback(() => {
    const m = schlange[0];
    if (!m) return;
    setSchlange((alt) => alt.slice(1));
    if (!personId) return;
    markiereGelesen(campaignId, m.id)
      .then(() =>
        setMitteilungen((alt) =>
          alt.map((x) => (x.id === m.id ? { ...x, gelesenVon: [...x.gelesenVon, personId] } : x)),
        ),
      )
      .catch(() => {
        /* still */
      });
  }, [schlange, campaignId, personId]);

  const allesGelesen = useCallback(() => {
    if (!personId) return;
    markiereAllesGelesen(campaignId)
      .then(() =>
        setMitteilungen((alt) =>
          alt.map((m) => (m.gelesenVon.includes(personId) ? m : { ...m, gelesenVon: [...m.gelesenVon, personId] })),
        ),
      )
      .catch(() => {
        /* still */
      });
    setSchlange([]);
  }, [campaignId, personId]);

  const wert = useMemo(
    () => ({
      mitteilungen,
      ungelesen,
      verbunden,
      aktuell,
      wartend: Math.max(0, schlange.length - 1),
      bestaetigen,
      allesGelesen,
      neuLaden,
    }),
    [mitteilungen, ungelesen, verbunden, aktuell, schlange.length, bestaetigen, allesGelesen, neuLaden],
  );

  return <Kontext.Provider value={wert}>{children}</Kontext.Provider>;
}
