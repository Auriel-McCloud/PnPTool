import type { Kampf } from "./api";
import "./kampf.css";

/**
 * "Du bist dran" — auch wenn man gerade woanders schaut.
 *
 * Die Initiativliste zu treffen ist im Gefecht das eine; das andere ist,
 * überhaupt zu merken, dass man an der Reihe ist. Wer gerade im Inventar
 * kramt, bekommt es sonst erst mit, wenn ihn jemand anspricht.
 *
 * Erscheint nur, wenn wirklich der eigene Charakter handelt **und** man nicht
 * ohnehin im Kampfbereich steht — dort leuchtet die Zeile ja schon. Antippen
 * bringt einen hin.
 *
 * Die Vorstufe zum Blitz-Symbol aus dem UI-Konzept: dieselbe Stelle, aber
 * bisher nur für diese eine Meldung.
 */
export function DranMeldung({
  kampf,
  eigenePersonId,
  imKampfbereich,
  onHin,
}: {
  kampf: Kampf | null;
  eigenePersonId: string | null;
  imKampfbereich: boolean;
  onHin: () => void;
}) {
  if (!kampf || !eigenePersonId || imKampfbereich) return null;
  const dran = kampf.teilnehmer.find((t) => t.id === kampf.amZug);
  if (!dran || dran.personId !== eigenePersonId) return null;

  return (
    <button type="button" className="ka-meldung" onClick={onHin}>
      <span className="ka-meldung-zeichen" aria-hidden="true">
        ⚡
      </span>
      <span>
        Du bist dran
        <em>Runde {kampf.runde} — antippen</em>
      </span>
    </button>
  );
}
