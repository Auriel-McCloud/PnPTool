import { createPortal } from "react-dom";
import { useMitteilungen } from "./MitteilungenKontext";
import "./mitteilungen.css";

function zeit(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? ""
    : d.toLocaleTimeString("de-AT", { hour: "2-digit", minute: "2-digit" });
}

/**
 * Das Popup einer SL-Mitteilung.
 *
 * **Ohne Absender** — die Ansage kommt aus der Spielwelt, nicht von einer
 * Person (Marks Vorgabe: "Bei SL Nachrichten gibt es keinen Absender").
 *
 * Liegt per Portal am body und über allem, auch über offenen Fenstern: Eine
 * Ansage darf nicht hinter einem Gegenstandsfenster verschwinden.
 */
export function MitteilungPopup() {
  const { aktuell, wartend, bestaetigen } = useMitteilungen();

  if (!aktuell) return null;

  return createPortal(
    <div className="mt-popup-huelle">
      <div
        className="mt-popup"
        role="alertdialog"
        aria-live="assertive"
        // Enter/Escape bestätigen: am Tablet tippt man, am Rechner drückt man.
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === "Escape") bestaetigen();
        }}
        tabIndex={-1}
        ref={(el) => el?.focus()}
      >
        <div className="mt-popup-kopf">
          <span className="mt-popup-zeichen" aria-hidden="true">
            ⚡
          </span>
          <span className="mt-popup-zeit">{zeit(aktuell.erstelltAm)}</span>
        </div>

        <div className="mt-popup-inhalt">
          {aktuell.art === "BILD" && aktuell.bildUrl ? (
            <img src={aktuell.bildUrl} alt={aktuell.inhalt || "Bild der Spielleitung"} />
          ) : (
            aktuell.inhalt
          )}
          {aktuell.art === "BILD" && aktuell.inhalt && (
            <p style={{ marginTop: 10, fontSize: 14, color: "var(--text-leise)" }}>{aktuell.inhalt}</p>
          )}
        </div>

        <div className="mt-popup-fuss">
          {wartend > 0 && (
            <span className="mt-popup-rest">
              noch {wartend} weitere
            </span>
          )}
          <button
            type="button"
            onClick={bestaetigen}
            style={{ color: "var(--warn)", borderColor: "var(--warn)" }}
          >
            Verstanden
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
