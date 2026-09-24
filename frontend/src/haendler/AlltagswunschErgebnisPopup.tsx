import { createPortal } from "react-dom";
import { useMitteilungen } from "../mitteilungen/MitteilungenKontext";
import "../shell/bestaetigung.css";

/**
 * Spieler-Popup (24.09.2026): Rückmeldung, nachdem die SL einen
 * Alltagswunsch entschieden hat. Der Spieler musste dafür nicht warten —
 * das Popup kommt einfach, sobald die SL fertig ist (siehe
 * MitteilungenKontext::alltagswunschErgebnisAktuell).
 */
export function AlltagswunschErgebnisPopup() {
  const { alltagswunschErgebnisAktuell: w, alltagswunschErgebnisBestaetigen } = useMitteilungen();
  if (!w) return null;

  const angenommen = w.status === "ANGENOMMEN";

  return createPortal(
    <div className="best-huelle" onClick={alltagswunschErgebnisBestaetigen}>
      <div className="best-kasten" onClick={(e) => e.stopPropagation()}>
        <h2 className="best-titel">{angenommen ? "✅ Angenommen" : "❌ Abgelehnt"}</h2>
        <p className="best-text">
          {w.haendlerName}: „{w.wunschText}“
          <br />
          {angenommen ? (
            <>
              <strong>{w.vorschlagName}</strong> ist jetzt für {w.vorschlagPreis}¥ im Sortiment.
            </>
          ) : (
            w.ablehnungsGrund || "Leider nicht erhältlich."
          )}
        </p>
        <div className="best-knoepfe">
          <button type="button" className="best-ja" onClick={alltagswunschErgebnisBestaetigen}>
            Verstanden
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
