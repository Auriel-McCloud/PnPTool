import { Fenster } from "../shell/Fenster";
import "./willenskraft.css";

/**
 * Rückfrage vor dem Ausgeben von Willenskraft.
 *
 * Marks Einwand: ein Kästchen ist schnell versehentlich getroffen, und
 * **zurückholen kann es nur die Spielleitung** — ein Fehlgriff kostet also
 * echt etwas. Deshalb die Frage dazwischen.
 *
 * Ja und Nein in Blau und Rot, wie das Level Up: blau heisst weiter, rot
 * heisst lass es. Beide gross genug für den Daumen und weit genug
 * auseinander, dass man nicht das eine trifft und das andere meint.
 */
export function WillenskraftFrage({
  offen,
  uebrig,
  onJa,
  onNein,
}: {
  offen: boolean;
  /** Wieviel danach noch übrig wäre — die eigentliche Entscheidungshilfe. */
  uebrig: number;
  onJa: () => void;
  onNein: () => void;
}) {
  return (
    <Fenster
      offen={offen}
      titel="Willenskraft ausgeben?"
      unterzeile="Zurück gibt sie nur die Spielleitung"
      kennung="willenskraft-frage"
      onSchliessen={onNein}
    >
      <p className="wk-frage">
        Einen Punkt Willenskraft für einen <strong>erzwungenen Erfolg</strong> ausgeben?
      </p>
      <p className="wk-rest">
        Danach bleiben <strong>{Math.max(0, uebrig - 1)}</strong> von {uebrig} — auch für wilde Magie.
      </p>
      <div className="wk-knoepfe">
        <button type="button" className="wk-ja" onClick={onJa}>
          Ja
        </button>
        <button type="button" className="wk-nein" onClick={onNein}>
          Nein
        </button>
      </div>
    </Fenster>
  );
}
