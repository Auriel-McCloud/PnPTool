import { Fenster } from "../shell/Fenster";
import type { Gegenstand } from "./api";
import "./wegwerfen.css";

/**
 * Rückfrage vor dem Wegwerfen eines Gegenstands.
 *
 * Gebaut nach dem Vorbild von `traits/WillenskraftFrage.tsx` (Marks Vorgabe):
 * zwei grosse Knöpfe, weit auseinander, damit man nicht den einen trifft und
 * den anderen meint.
 *
 * **Die Farben sind hier umgekehrt** — und das mit Absicht. Bei der
 * Willenskraft heisst blau "weiter" und rot "lass es", weil das Ausgeben die
 * gewollte Handlung ist. Hier ist das Wegwerfen der Eingriff und das Behalten
 * der harmlose Ausgang: rot markiert deshalb das Wegwerfen, blau das
 * Abbrechen. Rot bedeutet in beiden Fällen "Vorsicht", nur liegt die Vorsicht
 * einmal beim Ja und einmal beim Nein.
 *
 * Der Text sagt ausdrücklich, dass **nichts gelöscht** wird — sonst traut
 * sich niemand, ein einzigartiges Stück wegzuwerfen.
 */
export function WegwerfenFrage({
  item,
  offen,
  laeuft,
  onWegwerfen,
  onAbbrechen,
}: {
  item: Gegenstand;
  offen: boolean;
  /** Während der Server antwortet: beide Knöpfe sperren. */
  laeuft?: boolean;
  onWegwerfen: () => void;
  onAbbrechen: () => void;
}) {
  return (
    <Fenster
      offen={offen}
      titel={`${item.name} wegwerfen?`}
      kennung={`wegwerfen:${item.id}`}
      onSchliessen={onAbbrechen}
    >
      <p className="ww-hinweis">
        Der Gegenstand verschwindet aus deinem Inventar
        {item.hatMenge && item.menge > 1 ? ` — alle ${item.menge} Stück` : ""}.
      </p>
      {/* Die eigentliche Beruhigung: es ist nicht endgültig. */}
      <p className="ww-beruhigung">
        <strong>Gelöscht wird nichts.</strong> Das Stück landet bei deiner
        Spielleitung, die es dir wiedergeben kann.
      </p>
      {item.einzigartig && (
        <p className="ww-einzigartig">
          <span aria-hidden="true">✶</span> Einzigartig — es gibt es nur einmal.
        </p>
      )}
      <div className="ww-knoepfe">
        <button type="button" className="ww-weg" disabled={laeuft} onClick={onWegwerfen}>
          <span aria-hidden="true">🗑</span> Wegwerfen
        </button>
        <button type="button" className="ww-behalten" disabled={laeuft} onClick={onAbbrechen}>
          Behalten
        </button>
      </div>
    </Fenster>
  );
}
