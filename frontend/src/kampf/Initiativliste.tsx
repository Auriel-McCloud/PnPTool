import { useEffect, useRef, useState } from "react";
import { KAMPFARTEN, kampfApi, type Kampf, type Teilnehmer } from "./api";
import "./kampf.css";

/**
 * Die Initiativliste — für alle am Tisch dieselbe.
 *
 * Sortiert wird serverseitig, damit niemand eine andere Reihenfolge sieht als
 * sein Nachbar. Hier steht nur, wie sie aussieht: wer dran ist, leuchtet; der
 * eigene Charakter ist gekennzeichnet, damit man ihn im Gewühl findet.
 */

const ART = Object.fromEntries(KAMPFARTEN.map((a) => [a.wert, a]));

/**
 * Holt den Kampf und lädt ihn regelmässig nach.
 *
 * **Nachladen statt Live-Verbindung** — bewusst der erste Schritt: die
 * Oberfläche sieht genauso aus, wie sie später mit einer echten Verbindung
 * aussehen wird, nur die Bezugsquelle wird ausgetauscht (Phase 5). Für eine
 * Runde mit vier Leuten ist eine Abfrage alle drei Sekunden nichts.
 *
 * Läuft nur, solange die Seite sichtbar ist — ein Tablet in der Tasche muss
 * nicht mitzählen.
 */
export function useKampf(campaignId: string | null, takt = 3000) {
  const [kampf, setKampf] = useState<Kampf | null>(null);
  const [geladen, setGeladen] = useState(false);
  // In einem ref, damit der Takt nicht bei jedem Nachladen neu aufgesetzt wird
  const laufend = useRef(false);

  useEffect(() => {
    if (!campaignId) return;
    let abgemeldet = false;

    async function holen() {
      if (laufend.current || document.hidden) return;
      laufend.current = true;
      try {
        const neu = await kampfApi.laden(campaignId!);
        if (!abgemeldet) setKampf(neu);
      } catch {
        // Netz weg, Server neu gestartet — beim nächsten Takt wieder
      } finally {
        laufend.current = false;
        if (!abgemeldet) setGeladen(true);
      }
    }

    void holen();
    const uhr = setInterval(holen, takt);
    // Beim Zurückkommen sofort nachsehen, nicht erst nach dem nächsten Takt
    document.addEventListener("visibilitychange", holen);
    return () => {
      abgemeldet = true;
      clearInterval(uhr);
      document.removeEventListener("visibilitychange", holen);
    };
  }, [campaignId, takt]);

  return { kampf, geladen, neuLaden: setKampf };
}

export function Initiativliste({
  kampf,
  eigenePersonId,
  onAmZug,
  onBogen,
  onEntfernen,
  onErledigt,
}: {
  kampf: Kampf;
  /** Der eigene Charakter wird hervorgehoben — sonst sucht man ihn. */
  eigenePersonId?: string | null;
  /** Nur die Spielleitung: jemanden ans Ruder setzen. */
  onAmZug?: (id: string) => void;
  /** Nur die Spielleitung: den Bogen dieses Teilnehmers ansehen. */
  onBogen?: (t: Teilnehmer) => void;
  onEntfernen?: (id: string) => void;
  onErledigt?: (t: Teilnehmer) => void;
}) {
  return (
    <ol className="ka-liste">
      {kampf.teilnehmer.map((t, i) => {
        const dran = kampf.amZug === t.id;
        const meiner = Boolean(eigenePersonId) && t.personId === eigenePersonId;
        const art = ART[t.kampfart];
        return (
          <li
            key={t.id}
            className="ka-zeile"
            data-dran={dran}
            data-meiner={meiner}
            data-erledigt={t.erledigt}
          >
            <span className="ka-platz">{i + 1}</span>
            <span className="ka-init" title="Initiative">
              {t.initiative}
            </span>
            <span className="ka-art" title={art?.erklaerung}>
              {art?.symbol}
            </span>
            <span className="ka-name">
              {t.name}
              {meiner && <em className="ka-du">du</em>}
              {t.notiz && <em className="ka-notiz">{t.notiz}</em>}
            </span>

            {dran && <span className="ka-dran">am Zug</span>}

            {(onAmZug || onBogen || onEntfernen || onErledigt) && (
              <span className="ka-knoepfe">
                {onBogen && (t.personId || t.begleiterId) && (
                  <button type="button" onClick={() => onBogen(t)} title={`Bogen von ${t.name}`}>
                    ▤
                  </button>
                )}
                {onErledigt && (
                  <button
                    type="button"
                    data-aktiv={t.erledigt}
                    onClick={() => onErledigt(t)}
                    title={t.erledigt ? "Doch noch nicht gehandelt" : "Hat gehandelt"}
                  >
                    ✓
                  </button>
                )}
                {onAmZug && !dran && (
                  <button type="button" onClick={() => onAmZug(t.id)} title="Ist jetzt dran">
                    ▶
                  </button>
                )}
                {onEntfernen && (
                  <button
                    type="button"
                    className="ka-weg"
                    onClick={() => onEntfernen(t.id)}
                    title={`${t.name} aus dem Kampf nehmen`}
                  >
                    ✕
                  </button>
                )}
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
