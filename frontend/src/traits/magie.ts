/**
 * Magie- und NeuroWeaving-Regeln, soweit die Probenanzeige sie braucht.
 *
 * Quelle: `docs/reference/Neotopia.xlsx`, Blatt *Regeln*, Zeilen 44/45 und
 * 80-96. Die Texte stammen aus Marks eigenem Blatt, nicht aus fremdem
 * Material — sie dürfen deshalb hier stehen.
 */

/** Was eine Sphärenstufe erlaubt (Zeile 44/89). Der Index ist die Stufe. */
export const SPHAEREN_STUFEN = [
  "",
  "Wahrnehmbar — du siehst und spürst, was in dieser Sphäre vorgeht.",
  "Manipulation bis etwa 50 cm³.",
  "Manipulation bis etwa 4 m³.",
  "Bis zur Größe eines Hauses.",
  "„Nach meiner Größe beurteilst du mich, tust du das?“",
];

/** Kurzbeschreibung je Sphäre (Zeilen 90-92). */
export const SPHAEREN: Record<string, string> = {
  Korrespondenz: "Raummagie. „Entfernung? Was ist das?“",
  Entropie: "Wahrscheinlichkeiten. „Glück? HA!“",
  Kräfte: "Physikalische Kräfte manipulieren. Schaden durch Kräfte ist automatisch +1.",
  Leben: "Jede lebende Materie unterliegt meinem Willen.",
  Materie: "Alles, was nicht lebt, beugt sich meinem Willen.",
  Gedanken: "„Das sind nicht die Druiden, die ihr sucht.“",
  Ursprung:
    "Reine Magie. Nötig, um Verzauberungen zu schaffen und Magie in Objekten zu festigen — und für Lichtschwerter.",
  Geister:
    "Medium und Reisen in die Astralwelt. Geister können mit der Realität wechselwirken, wenn du sie lässt.",
  Zeit: "Die schwierigste aller Sphären. Drei Minuten zurück retten manchmal den Abend — 300 Jahre nicht.",
};

/**
 * Wie viele Würfel eine Probe hergibt und was sie kostet.
 *
 * **Hexkraft** (Zeilen 81-86): Ein *kontrollierter* Zauber ist nur der
 * Hexkraft-Wert. Wer mehr will, nimmt **Wilde Magie**: Bonuswürfel bis zur Höhe
 * der eigenen Willenskraft. Dafür muss vorher ein **Zielwert** an Erfolgen
 * angesagt werden — wird er unterschritten, ist die Probe gescheitert. Nach
 * einem gelungenen wilden Zauber folgt ein Willenskraftwurf gegen die Zahl
 * der Erfolge; was die Willenskraft nicht abdeckt, trifft den Magier als
 * **Schlagschaden**.
 *
 * **Sphären** (Zeile 87): werden **nie** gewürfelt. Sie beschreiben, woran
 * die Magie greift und wie groß es sein darf — keine Bonuswürfel.
 *
 * **NeuroWeaving** (Zeilen 45/95/96): dieselben Willenskraft-Regeln wie
 * Hexkraft, aber die Punkte gelten als **Bonuswürfel für die jeweilige Aktion**,
 * nicht als Begrenzung. Ein Neuroweaver darf auch Fertigkeiten einsetzen, in
 * denen er keine Punkte hat. Das Gegenstück zu Wilder Magie heißt hier
 * **Overclock** (Mark, 22.09.2026 — "Wilde Magie" für NeuroWeaving war reiner
 * Copy-Paste-Rest, passte inhaltlich nicht): das Nervensystem übers sichere
 * Limit hinaus pushen, statt unkontrolliert Magie zu wirken.
 */
export const MAGIE_HINWEISE = {
  hexkraftKontrolliert:
    "Ein kontrollierter Zauber ist nur der Hexkraft-Wert. Erfolge kannst du in Wucht oder in Dauer stecken.",
  hexkraftWild:
    "Wilde Magie: Bonuswürfel bis zur Höhe deiner Willenskraft. Sag vorher einen Zielwert an — " +
    "wird er unterschritten, ist die Probe gescheitert.",
  hexkraftRueckstoss:
    "Nach einem gelungenen wilden Zauber: Willenskraftwurf gegen die Zahl der Erfolge. Was die " +
    "Willenskraft nicht abdeckt, bekommst du als Schlagschaden. Erfolge genau auf dem Zielwert " +
    "kosten nichts.",
  sphaereNichtWuerfeln:
    "Auf Sphären wird nicht gewürfelt. Sie zeigen, woran deine Magie greift und wie groß es sein darf — " +
    "gewürfelt wird Hexkraft.",
  neuroWeaving:
    "NeuroWeaving-Punkte sind Bonuswürfel für die jeweilige Aktion, keine Begrenzung. Du darfst auch " +
    "Fertigkeiten einsetzen, in denen du keine Punkte hast.",
  overclock:
    "Overclock: Bonuswürfel bis zur Höhe deiner Willenskraft — du treibst dein Nervensystem übers " +
    "sichere Limit. Sag vorher einen Zielwert an — wird er unterschritten, ist die Probe gescheitert.",
  overclockRueckstoss:
    "Nach einem erfolgreichen Overclock: Willenskraftwurf gegen die Zahl der Erfolge. Was die " +
    "Willenskraft nicht abdeckt, bekommst du als Schlagschaden. Erfolge genau auf dem Zielwert " +
    "kosten nichts.",
};

/**
 * Kein Pool-Deckel mehr bei Overclock (Mark, 06.11.2026).
 *
 * Bis dahin galt ein harter Deckel von 12 (`NEUROWEAVING_POOL_MAX`, seit
 * 22.09.2026 — davor 10). Mark hat ihn bewusst gestrichen: der Rückschlag
 * (Willenskraftwurf gegen die Erfolge, Rest als Schlagschaden) begrenzt
 * Overclock schon von allein — wer zu weit geht, schaltet sich im
 * schlimmsten Fall selbst aus. Genau das soll möglich sein, bis hin zum
 * Spieler, der sich für sein Team aufopfert. Ein zusätzlicher harter Deckel
 * nahm diesen Momenten die Spitze, ohne einen zweiten Zweck zu erfüllen.
 * Gilt gleichermaßen für den Neuroweaver (NeuroWeaving + Overclock) und für
 * den Decker im Matrix-Hot (Matrix-Pool + Overclock, siehe unten).
 */
