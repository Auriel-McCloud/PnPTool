import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  blendeAllesAus,
  blendeAus,
  getMitteilungen,
  markiereAllesGelesen,
  markiereGelesen,
  verbindeLive,
  type Mitteilung,
} from "./api";
import { verhandlungApi, type Verhandlung } from "../verhandlung/api";

/**
 * Hält den Stand der SL-Mitteilungen und die Live-Leitung.
 *
 * Ein Kontext statt Zustand in einer Komponente: Das Blitz-Symbol sitzt in
 * der Werkzeugleiste, das Popup liegt über allem, und der Verlauf steckt in
 * einem Fenster — alle drei brauchen dieselben Daten.
 *
 * **Trägt seit 23.09.2026 auch Verhandlungen mit** (siehe
 * app/verhandlung/routes.py): die Zustellung läuft über denselben
 * WebSocket wie SL-Mitteilungen (Backend markiert den Umschlag mit
 * `_typ: "verhandlung"`, `verteiler.verteilen` verpackt aber IMMER als
 * `{typ: "mitteilung", ...}` — deshalb hier herausgefiltert, bevor es in
 * die normale Mitteilungsliste rutscht und `MitteilungPopup` mit einer
 * fremden Objektform verwirrt).
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
  ausblenden: (id: string) => void;
  allesAusblenden: () => void;
  neuLaden: () => void;
  /** Eingehendes Verhandlungsangebot (Rüstungsreparatur beim Händler u.ä.) —
   * null = nichts wartet. Nur am eigenen Charakter, siehe Backend-Filter. */
  verhandlungAktuell: Verhandlung | null;
  verhandlungenWartend: number;
  /** Antwortet auf `verhandlungAktuell`, gibt das aktualisierte Angebot
   * zurück (mit `ergebnis` bei Annahme) — der Aufrufer zeigt damit die
   * Erfolgsmeldung, bevor er das Popup schließt. */
  verhandlungAntworten: (angenommen: boolean) => Promise<Verhandlung | null>;
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
      ausblenden: () => {},
      allesAusblenden: () => {},
      neuLaden: () => {},
      verhandlungAktuell: null,
      verhandlungenWartend: 0,
      verhandlungAntworten: async () => null,
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
  // Eigene Schlange für Verhandlungsangebote — getrennt von den Mitteilungen,
  // damit ein Angebot nicht durch ein SL-Popup verdrängt werden kann und
  // umgekehrt.
  const [verhandlungSchlange, setVerhandlungSchlange] = useState<Verhandlung[]>([]);

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

  // Aufhol-Liste beim (Wieder-)Verbinden: anders als bei Mitteilungen gibt es
  // für Verhandlungen keinen "stand"-Schnappschuss über den WebSocket (siehe
  // repository.list_offene_fuer) — deshalb ein eigener Abruf beim Laden.
  useEffect(() => {
    if (!personId) return;
    let abgebrochen = false;
    verhandlungApi
      .offene(campaignId)
      .then((offene) => {
        if (!abgebrochen) setVerhandlungSchlange(offene);
      })
      .catch(() => {
        /* still */
      });
    return () => {
      abgebrochen = true;
    };
  }, [campaignId, personId]);

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
        // Verhandlungsangebot: eigener Umschlag-Inhalt (`_typ: "verhandlung"`,
        // siehe verhandlung/routes.py::_verteilen), aber äusserlich als
        // normale "mitteilung" verpackt — derselbe Verteiler kennt keine
        // dritte Umschlagsart. Herausfiltern, bevor es in die
        // Mitteilungsliste rutscht.
        const daten = n.daten as unknown as Record<string, unknown>;
        if (daten._typ === "verhandlung") {
          const v = daten as unknown as Verhandlung;
          setVerhandlungSchlange((alt) => {
            const ohne = alt.filter((x) => x.id !== v.id);
            // Nur offene Angebote warten als Popup — eine Antwort (vom
            // eigenen zweiten Gerät oder nach Zurückziehen) räumt nur auf.
            return v.status === "OFFEN" ? [...ohne, v] : ohne;
          });
          return;
        }
        // Neue Mitteilung
        setMitteilungen((alt) => (alt.some((m) => m.id === n.daten.id) ? alt : [n.daten, ...alt]));
        // Die Spielleitung sieht ihre eigenen Mitteilungen (TEXT, BILD, WARNUNG)
        // nicht als Popup — sie hat sie gerade selbst abgeschickt. NACHRICHT-
        // Popups (Spieler-Chatnachrichten) sieht sie aber, damit sie weiss,
        // dass jemand geschrieben hat.
        const istEigene = istSlRef.current && n.daten.art !== "NACHRICHT";
        if (!istEigene) {
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
  const verhandlungAktuell = verhandlungSchlange[0] ?? null;

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

  const ausblenden = useCallback((id: string) => {
    blendeAus(campaignId, id)
      .then(() => setMitteilungen((alt) => alt.filter((m) => m.id !== id)))
      .catch(() => { /* still */ });
    setSchlange((alt) => alt.filter((m) => m.id !== id));
  }, [campaignId]);

  const allesAusblenden = useCallback(() => {
    blendeAllesAus(campaignId)
      .then(() => setMitteilungen([]))
      .catch(() => { /* still */ });
    setSchlange([]);
  }, [campaignId]);

  const verhandlungAntworten = useCallback(
    async (angenommen: boolean): Promise<Verhandlung | null> => {
      const v = verhandlungSchlange[0];
      if (!v) return null;
      const aktualisiert = await verhandlungApi.antworten(campaignId, v.id, angenommen);
      setVerhandlungSchlange((alt) => alt.filter((x) => x.id !== v.id));
      return aktualisiert;
    },
    [verhandlungSchlange, campaignId],
  );

  const wert = useMemo(
    () => ({
      mitteilungen,
      ungelesen,
      verbunden,
      aktuell,
      wartend: Math.max(0, schlange.length - 1),
      bestaetigen,
      allesGelesen,
      ausblenden,
      allesAusblenden,
      neuLaden,
      verhandlungAktuell,
      verhandlungenWartend: Math.max(0, verhandlungSchlange.length - 1),
      verhandlungAntworten,
    }),
    [
      mitteilungen,
      ungelesen,
      verbunden,
      aktuell,
      schlange.length,
      bestaetigen,
      allesGelesen,
      ausblenden,
      allesAusblenden,
      neuLaden,
      verhandlungAktuell,
      verhandlungSchlange.length,
      verhandlungAntworten,
    ],
  );

  return <Kontext.Provider value={wert}>{children}</Kontext.Provider>;
}
