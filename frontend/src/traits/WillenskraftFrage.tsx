import { Fenster } from "../shell/Fenster";
import "./willenskraft.css";

/**
 * Rückfrage vor dem Ausgeben von Willenskraft.
 *
 * Marks Einwand: ein Kästchen ist schnell versehentlich getroffen, und
 * zurückholen kann es nur die Spielleitung — ein Fehlgriff kostet also echt
 * etwas. Deshalb die Frage dazwischen.
 *
 * Sie nennt auch, **wodurch** Willenskraft zurückkommt: Schlaf, oder ein
 * Handeln nach Ambition, Verlangen oder Ziel. Das ist die Auskunft, die man
 * in dem Moment braucht — "die Spielleitung gibt sie zurück" sagt nur, wen
 * man fragen muss, nicht wofür es sich lohnt.
 *
 * Ja und Nein in Blau und Rot, wie das Level Up: blau heisst weiter, rot
 * heisst lass es. Beide gross genug für den Daumen und weit genug
 * auseinander, dass man nicht das eine trifft und das andere meint.
 */
export function WillenskraftFrage({
  offen,
  uebrig,
  weg,
  onJa,
  onNein,
}: {
  offen: boolean;
  /** Wieviel danach noch übrig wäre — die eigentliche Entscheidungshilfe. */
  uebrig: number;
  /**
   * Wofür der Rest sonst noch gebraucht wird, hängt am Weg: wilde Magie gibt
   * es nur beim Magier, NeuroWeaving nur beim Technomancer. Wer weder noch
   * ist, soll nicht über Möglichkeiten lesen, die er nicht hat.
   */
  weg?: "KEINER" | "MAGIER" | "TECHNOMANCER";
  onJa: () => void;
  onNein: () => void;
}) {
  const wofuerSonst =
    weg === "MAGIER" ? " — auch für wilde Magie." : weg === "TECHNOMANCER" ? " — auch fürs NeuroWeaving." : ".";
  return (
    <Fenster
      offen={offen}
      // Die Frage steht in der Überschrift und nirgends sonst — vorher stand
      // sie dreimal fast gleich da.
      titel="Willenskraft für einen Erfolg ausgeben?"
      kennung="willenskraft-frage"
      onSchliessen={onNein}
    >
      <p className="wk-rest">
        Danach bleiben <strong>{Math.max(0, uebrig - 1)}</strong> von {uebrig}
        {wofuerSonst}
      </p>
      {/* Nicht "die Spielleitung gibt sie zurück" (Marks Einwand), sondern
          *wodurch* sie zurückkommt — das ist die Auskunft, die man in dem
          Moment braucht. */}
      <p className="wk-rueckkehr">
        Ein Punkt kommt durch <strong>Schlaf</strong> zurück — oder wenn du deiner{" "}
        <strong>Ambition</strong> oder deinem <strong>Verlangen</strong> entsprechend handelst oder
        ein <strong>Ziel</strong> erreichst.
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
