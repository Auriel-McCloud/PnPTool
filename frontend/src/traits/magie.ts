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
 * **Arete** (Zeilen 81-86): Ein *kontrollierter* Zauber ist nur der
 * Arete-Wert. Wer mehr will, nimmt **Wilde Magie**: Bonuswürfel bis zur Höhe
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
 * Arete, aber die Punkte gelten als **Bonuswürfel für die jeweilige Aktion**,
 * nicht als Begrenzung. Ein Technomancer darf auch Fertigkeiten einsetzen, in
 * denen er keine Punkte hat.
 */
export const MAGIE_HINWEISE = {
  areteKontrolliert:
    "Ein kontrollierter Zauber ist nur der Arete-Wert. Erfolge kannst du in Wucht oder in Dauer stecken.",
  areteWild:
    "Wilde Magie: Bonuswürfel bis zur Höhe deiner Willenskraft. Sag vorher einen Zielwert an — " +
    "wird er unterschritten, ist die Probe gescheitert.",
  areteRueckstoss:
    "Nach einem gelungenen wilden Zauber: Willenskraftwurf gegen die Zahl der Erfolge. Was die " +
    "Willenskraft nicht abdeckt, bekommst du als Schlagschaden. Erfolge genau auf dem Zielwert " +
    "kosten nichts.",
  sphaereNichtWuerfeln:
    "Auf Sphären wird nicht gewürfelt. Sie zeigen, woran deine Magie greift und wie groß es sein darf — " +
    "gewürfelt wird Arete.",
  neuroWeaving:
    "NeuroWeaving-Punkte sind Bonuswürfel für die jeweilige Aktion, keine Begrenzung. Du darfst auch " +
    "Fertigkeiten einsetzen, in denen du keine Punkte hast.",
};
