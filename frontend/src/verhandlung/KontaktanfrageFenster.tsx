import type { Verhandlung } from "./api";

/**
 * Eigenes Fenster für eine Kontaktanfrage zwischen zwei Spielern.
 *
 * Kein Geldgeschäft und kein Angebot der Spielleitung — deshalb weder ¥ noch
 * „Gesamt“, sondern Name, Frage und zwei Knöpfe, die sagen, was passiert.
 * Zustellung und Antwort laufen weiter über das Verhandlungssystem
 * (`VerhandlungPopup` reicht den Zustand durch).
 */
export function KontaktanfrageFenster({
  angezeigt,
  laeuft,
  fehler,
  wartend,
  onAntwort,
  onOk,
}: {
  angezeigt: Verhandlung;
  laeuft: boolean;
  fehler: string | null;
  wartend: number;
  onAntwort: (angenommen: boolean) => void;
  onOk: () => void;
}) {
  const entschieden = angezeigt.status !== "OFFEN";
  const angenommen = angezeigt.status === "ANGENOMMEN";
  const text = angezeigt.positionen[0]?.bezeichnung ?? "Jemand möchte Kontakt mit dir austauschen";

  return (
    <div className="vh-popup-huelle">
      <div
        className={`vh-popup${entschieden ? " vh-popup-entschieden" : ""}`}
        role="alertdialog"
        aria-live="assertive"
        tabIndex={-1}
        ref={(el) => el?.focus()}
      >
        <div className="vh-popup-kopf">
          <span className="vh-popup-zeichen" aria-hidden="true">
            {entschieden ? (angenommen ? "✓" : "✕") : "◍"}
          </span>
          <span className="vh-popup-titel">
            {entschieden ? (angenommen ? "Kontakt hergestellt" : "Anfrage abgelehnt") : "Kontaktanfrage"}
          </span>
        </div>

        <div className="vh-popup-inhalt">
          {entschieden ? (
            <p className="vh-restguthaben">
              {angenommen
                ? "Ihr könnt euch jetzt im Messenger schreiben."
                : "Es wurde kein Kontakt ausgetauscht."}
            </p>
          ) : (
            <p className="vh-position-bezeichnung">{text}</p>
          )}
          {fehler && <p className="vh-fehler">{fehler}</p>}
        </div>

        <div className="vh-popup-fuss">
          {wartend > 0 && !entschieden && <span className="vh-popup-rest">noch {wartend} weitere</span>}
          {entschieden ? (
            <button type="button" className="vh-btn-ok" onClick={onOk}>
              OK
            </button>
          ) : (
            <>
              <button type="button" className="vh-btn-ablehnen" disabled={laeuft} onClick={() => onAntwort(false)}>
                Kein Interesse
              </button>
              <button type="button" className="vh-btn-annehmen" disabled={laeuft} onClick={() => onAntwort(true)}>
                {laeuft ? "Sendet…" : "Kontakt austauschen"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
