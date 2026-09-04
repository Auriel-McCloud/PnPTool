import { createPortal } from "react-dom";
import { InitiativeMelden } from "./InitiativeMelden";
import { useMitteilungen } from "./MitteilungenKontext";
import "./mitteilungen.css";

/**
 * Vollbild-Warnung: der ganze Schirm pulsiert, die Ansage steht in der Mitte.
 *
 * Marks Bild für die Initiative. Bewusst lauter als das normale Popup — und
 * deshalb eine eigene Art, damit es die Wirkung nicht durch Gewöhnung
 * verliert.
 *
 * Der Farbton ist wählbar (rot/blau/violett), weil am Tisch noch erprobt
 * wird, welcher wirkt.
 *
 * Wie die Verwundungsanzeige: liegt über allem, nimmt keine Eingaben an, und
 * respektiert `prefers-reduced-motion` (global in index.css) — für
 * lichtempfindliche Menschen ist Pulsieren keine Stimmung, sondern ein
 * Problem. Die Ansage bleibt dann trotzdem lesbar stehen.
 */
export function Warnung({ campaignId }: { campaignId?: string | null }) {
  const { aktuell, wartend, bestaetigen } = useMitteilungen();

  if (!aktuell || aktuell.art !== "WARNUNG") return null;

  const farbe = aktuell.farbe || "rot";

  return createPortal(
    <div className="wn-huelle" role="alertdialog" aria-live="assertive" data-farbe={farbe}>
      {/* Der pulsierende Schleier. Nimmt keine Klicks an, damit er den
          Bestätigen-Knopf nicht abfängt. */}
      <div className="wn-puls" aria-hidden="true" />

      <div className="wn-mitte">
        <div className="wn-zeichen" aria-hidden="true">
          ⚠
        </div>
        <p className="wn-text">{aktuell.inhalt}</p>

        {/* Bei "Würfelt für Initiative!" gleich das Eingabefeld — Marks
            Wunsch: melden ohne den Bereich zu wechseln. */}
        {aktuell.initiative && campaignId && (
          <InitiativeMelden campaignId={campaignId} />
        )}
        <div className="wn-fuss">
          {wartend > 0 && <span className="wn-rest">noch {wartend} weitere</span>}
          <button
            type="button"
            className="wn-knopf"
            onClick={bestaetigen}
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === "Escape") bestaetigen();
            }}
          >
            Verstanden
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
