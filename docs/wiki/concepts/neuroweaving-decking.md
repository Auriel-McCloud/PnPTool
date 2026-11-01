---
title: NeuroWeaving und Decking
created: 2026-09-18
updated: 2026-11-01
type: konzept
tags: [neuroweaving, versionsgeschichte, widerspruch, geplant]
sources: [../../reference/Neotopia_Regeln.md, ../../regeln-neotopia.md, ../../../backend/app/traits/seed.py]
status: aktuell
---

# NeuroWeaving und Decking

## Definition

Der Gegenweg zu Hexkraft (siehe [[magie-hexkraft]] — „Hexkraft != NeuroWeaving",
schließt sich aus). Gleiche Grundregeln wie Hexkraft/Arete beim
Willenskrafteinsatz und dessen Folgen, **aber**:

- **NeuroWeaving-Fertigkeiten geben Bonuswürfel** (anders als Sphären, die nur
  begrenzen). **Sechs Fertigkeiten** (seit 22.09.2026, siehe „Entwicklung"):
  Brute Force, Schleichen, Daten Verarbeiten, Kompilieren, Electronic Warfare,
  Matrix-Navigation.
- Ein Neuroweaver darf NeuroWeaving-Fertigkeiten auch nutzen, in denen er
  keine Punkte hat.
- **Das Gegenstück zu Wilder Magie heißt hier „Overclock"** (Mark,
  22.09.2026) — dieselbe Mechanik (Bonuswürfel bis zur Willenskraft, Zielwert
  vorher ansagen, Rückstoß bei Erfolg), aber „Wilde Magie" als Bezeichnung war
  reiner Copy-Paste-Rest und passte inhaltlich nicht: das Nervensystem wird
  übers sichere Limit gepusht, nicht unkontrolliert Magie wirkt.
- **Der NeuroWeaving-Grundwert selbst geht nur bis 6, nicht bis 10 wie
  Hexkraft** (Mark, 22.09.2026). Grund: Hexkraft wird bei einem kontrollierten
  Zauber allein gewürfelt und geht deshalb bis 10 — NeuroWeaving wird aber
  **immer** mit genau einer der sechs Fertigkeiten kombiniert (Wert + Fertigkeit,
  Pool-Deckel 12, siehe `frontend/src/traits/magie.ts::NEUROWEAVING_POOL_MAX`).
  Bei Max 10 hätte der Grundwert allein schon den ganzen Pool füllen können —
  die Fertigkeit wäre kosmetisch gewesen. Max 6 (wie eine normale Fertigkeit)
  erzwingt, dass beide Werte tatsächlich kombiniert werden müssen, um auf den
  Pool-Deckel zu kommen.
- **Wilde Magie hat KEINEN Pool-Deckel, NeuroWeaving schon** — kein
  Widerspruch, sondern zwei verschiedene Ausgangslagen (Mark, 22.09.2026
  nachgefragt): Hexkraft trägt die Last allein (ein Wert bis 10 + beliebig
  viele wilde Würfel obendrauf), NeuroWeaving kombiniert zwei Werte (Grundwert
  + Fertigkeit), die ohne Deckel linear bis 12 (6+6) explodieren würden. Wilde
  Magie hat dafür ihre eigene Bremse: das Rückstoß-Risiko (Schaden, wenn die
  Erfolge die Willenskraft übersteigen) — NeuroWeaving/Overclock kennt dasselbe
  Risiko, aber eben zusätzlich den Pool-Deckel.

**Cyberwall/I.C.E.** wird für Decker (Hacker) mit Geräten benötigt. Decking
nutzt i. d. R. Intelligenz + Matrix zum Hacken; Cyberdeck-Fertigkeiten
(B/S/D/K/EW/N — sechs Werte, seit 22.09.2026) geben Bonuswürfel je Aktion.
**KI nutzt dieselben sechs Fertigkeiten wie ein Neuroweaver** — kein eigenes
Gerät nötig, dieselbe Matrix-Präsenz wie beim NeuroWeaving.

## Die sechs Fertigkeiten im Detail

| Fertigkeit | Was sie tut |
|---|---|
| Brute Force | Aggressiver Frontalangriff auf Sicherheitssysteme — laut, riskant, effektiv gegen stark gepanzerte Hosts |
| Schleichen | Unbemerktes Eindringen, kaum Spuren, umgeht ICE |
| Daten Verarbeiten | Große Datenmengen in Echtzeit durchsuchen/filtern/auswerten |
| Kompilieren | Spontan eigene Programme/Effekte erschaffen |
| **Electronic Warfare** | „Rauschen" — sinnbildlich eine Rauchgranate im Netz. **Rein tarnend**, senkt NICHT gegnerische Verteidigung, sondern erschwert Ortung/Erkennung der eigenen Gruppe. Eine Probe bestimmt Radius UND Dauer zugleich; Dauer ist kontextabhängig (Szene bis Sekunden), im Kampf immer nur ein einmaliger Soforteffekt. Auffälliger als Schleichen. |
| **Matrix-Navigation** | Dinge im Netz aufspüren, auch Verstecktes. Erfolgsstufen bestimmen die Tiefe des Fundes — genug Erfolge finden sogar Backdoors in Host-Architekturen. Bewusst getrennt von Schleichen: Navigation findet den Weg, Schleichen hält unentdeckt, keine Überschneidung. |

## Matrix-Verteidigung (I.C.E.)

**Wer kein Neuroweaver ist, bezieht I.C.E. vom Commlink.** Ohne Commlink ist
der Wert 0 — dann ist man aber auch offline und nicht angreifbar. Bei mehreren
Geräten gilt der **beste** Wert, nicht die Summe. **Cyberdecks addieren ihren
Bonus obendrauf** (Cywall+1 bis +4) — hier wird summiert, weil Zusatzausrüstung,
kein Zugangsgerät; ein Deck allein nützt aber nichts ohne Commlink.

**Neuroweaver: Fassung + Geistesschärfe** — siehe „Entwicklung", weicht bewusst
vom Excel ab.

## Entwicklung

- **29.08.2026 (Tag 1 des Projekts!) — Neuroweaver-Verteidigung geändert.**
  Excel Zeile 99 sagt „Willenskraft". Mark hat das noch am ersten Projekttag
  auf Fassung+Geistesschärfe umgestellt: die Willenskraft wird beim NeuroWeaving
  selbst verbraucht — dieselbe Größe als Verteidigung hätte den Neuroweaver
  nach jeder eigenen Aktion verwundbarer gemacht. **Das Excel ist an dieser
  Stelle nie nachgezogen worden** und bleibt es auch bewusst (siehe
  [[../../reference/INDEX.md]] — Excel ist reine Rohdaten-Quelle).
- **10.09.2026 — Technomancer → Neuroweaver umbenannt.** Reine Namensänderung,
  gleicher Anlass wie Arete→Hexkraft.
- **22.09.2026 — Erweiterung auf 6 Skills umgesetzt** (`CLAUDE.md` Punkt 9).
  Vorschlag vom 20.09.2026 (Electronic Warfare + Matrix-Navigation) mit Mark
  durchgesprochen und in den Katalog übernommen: `backend/app/traits/seed.py`
  (Katalogeinträge + Beschreibungen), Cyberdeck-Werte in `items/schemas.py`/
  `repository.py`/`routes.py` (`deckElectronicWarfare`/`deckMatrixNavigation`,
  analog zu B/S/D/K). Frontend braucht keine Änderung — Probe/Kampfkarte/
  LevelUp iterieren generisch über Katalog/`deckBoni`, keine hartkodierten
  Skill-Namen. Gilt für NeuroWeaver, Decker UND KI. **Cyberdecks als echte
  Gegenstände im System (statt nur Referenztabelle im Wiki) bleibt bewusst
  offen** — Mark macht das separat, nicht Teil dieser Erweiterung.
- **22.09.2026 — NeuroWeaving-Grundwert-Maximum 10 → 6.** Mark beim Erstellen
  eines Neuroweavers gefunden: der Katalog erlaubte den Grundwert bis 10,
  genauso wie Hexkraft — aber anders als Hexkraft (allein gewürfelt) wird
  NeuroWeaving immer mit einer Fertigkeit kombiniert (Pool-Deckel). Bei
  Max 10 hätte der Grundwert allein den Pool ausschöpfen können. Auf 6
  gesenkt, damit echtes Kombinieren beider Werte nötig bleibt.
- **22.09.2026 — NeuroWeaving-Pool-Deckel 10 → 12.** Seit der Erweiterung auf
  6 Skills ist überall im Regelwerk 6 das neue Maximum — 10 als Pool-Deckel
  wirkte dagegen unpassend niedrig. 12 ist außerdem schon das etablierte
  "rundes Maximum" im Tool (natürliches Gesundheitsmaximum, siehe
  `GESUNDHEIT_GRUNDWERT`). `magie.ts::NEUROWEAVING_POOL_MAX`, dazu zwei
  hartkodierte 10er in `Kampfkarte.tsx` durch die Konstante ersetzt (waren
  bisher nicht synchron mit dem Deckel in `Probe.tsx`).
- **22.09.2026 — Freebees/Erfahrung konnten den NeuroWeaving-Grundwert nicht
  steigern.** `NeuroWeavingWert` fehlte in der festen Anzeige-Reihenfolge im
  Freebee-Schritt der Erstellung (`Charaktererstellung.tsx`) und im LevelUp
  (`LevelUp.tsx`) — beide zeigten nur die sechs Fertigkeiten darunter, nie
  den Wert selbst. Der Fertigkeiten-Schritt hatte es schon richtig, daher
  fiel es dort nicht auf. Ergänzt in beiden Dateien.
- **22.09.2026 — NeuroWeaving-Grundwert fehlte auch im Charakterblatt
  selbst.** Derselbe Fehler wie oben, dritte Stelle: `Charakterblatt.tsx`
  zeigte `reihe("NeuroWeaving")` (die sechs Fertigkeiten), aber nie
  `reihe("NeuroWeavingWert")` (den Grundwert). Ergänzt.
- **22.09.2026 — Probenauswahl beim NeuroWeaving verlangte einen Pflichtklick
  ohne echte Wahl.** Klickt man auf eine der sechs Fertigkeiten, gibt es nur
  einen möglichen Partner (den NeuroWeaving-Grundwert — anders als bei
  normalen Attributen mit drei Spalten zur Auswahl). `Probe.tsx` wird jetzt
  automatisch vorbelegt, wenn genau ein Kandidat existiert (Mark: „ich habe
  ja garkeine Wahl"). Der umgekehrte Fall — Klick auf den Grundwert, sechs
  mögliche Fertigkeiten — bleibt bewusst eine echte Auswahl.
- **22.09.2026 — „Wilde Magie" bei NeuroWeaving in „Overclock" umbenannt.**
  War ein Copy-Paste-Rest aus der Hexkraft-Seite und passte inhaltlich nicht.
  Gleiche Mechanik, neuer Name: `magie.ts::MAGIE_HINWEISE.overclock` /
  `.overclockRueckstoss`, `Probe.tsx` und `WillenskraftFrage.tsx` zeigen den
  Namen jetzt abhängig vom Weg.

## Noch nicht gebaut: temporäres Deaktivieren (teilweise entschieden)

Mark, 01.11.2026 nachts: Decker und Neuroweaver sollen Waffen oder
Waffen-Upgrades temporär deaktivieren können — „damit wären sie wirklich
nützlich“. Nichts davon ist gebaut. Der `status` dieser Seite bleibt
`aktuell` für die bestehenden Regeln.

### Skizze (seine Worte, noch keine Regel)

- **Nahkampf:** die Waffe funktioniert weiter, nur die Zusatzfunktionen
  fallen aus.
- **Schusswaffen** und **Cyberware-Augments** können deaktiviert werden.
- **Decks anderer Decker** oder **Riggerkonsolen:** der betroffene Spieler
  verliert temporär den Zugriff.
- **Oberfläche:** hat er den Wurf gegen das ICE geschafft, sieht er, was er
  deaktivieren könnte, tippt es an, und es verschwindet temporär.
- **Dauer:** 1–3 Runden, je nachdem wie gut gewürfelt wurde.
- **Pro Waffe**, nicht pauschal an der Person. Ein deaktivierter Bogen
  funktioniert weiter.
- **Electronic Warfare** könnte das ICE der eigenen Party erhöhen. Vorschlag,
  die Tarn-Zeile oben bleibt stehen.
- **Eigene Party-Kollegen** darf man hacken ([[../entities/party-feature]]).
  Was man abschaltet, muss man wieder aktivieren können.
- **Kein ICE**, Nachtfassung: Objekte und Upgrades ohne Vor-Hack. Im Gespräch
  danach korrigiert, siehe unten. Die Zeile „I.C.E. 0 = offline, Person nicht
  angreifbar“ bleibt für den Matrix-Angriff auf die Person stehen.

### Entschieden 01.11.2026 (Gespräch, nicht gebaut)

- **Schalter an jeder Waffe:** komplett aus oder nur Upgrades. Default nach
  Typ. Schusswaffe: komplett aus — nicht mehr schießen, keine Upgrades,
  keine Ki-Tama-Skills. Alles andere: nur Upgrades, die Grundfunktion bleibt.
- **Nur-Upgrades und Ki-Tama:** hängt an der Waffe, Default aus. Komplett-Aus
  killt Ki-Tama-Skills immer.
- **Cyberware-Augments** = montierte Werkbank-Upgrades
  ([[augments-ausruestung]]) und Körper-Cyberware ([[cyberware-bioware]]).
  Bioware nicht.
- **Dieselbe Ansicht** für Decker und Neuroweaver. KI nicht.
- **Kein ICE:** doch ein Wurf. Die Zwischenfassung „kein Wurf, Zeug geht
  einfach aus“ ist vom Tisch. Gegen welche Schwelle der Wurf geht, wenn
  das ICE 0 ist, ist offen.
- **Deck oder Riggerkonsole:** Zugriff weg. Schon gesprungene Drohnen fallen
  sofort raus ([[drohnen-fahrzeuge]]).
- **Ausgabe:** dieselben Erfolge für Zielzahl und Dauer, beides höchstens 3.
  Der frühere Satz „Wahl zwischen Anzahl oder Runden“ ist damit ersetzt.
  2 Erfolge = bis zu 2 Ziele für 2 Runden. Ob er weniger antippen darf als
  die Erfolge hergeben, hat er nicht gesagt — naheliegend ja, nicht
  bestätigt.
- **Nur im Kampf** ([[kampf-und-initiative]]). Eine Runde ist eine
  Kampfrunde. Außerhalb nicht.
- **Wieder anschalten, eigene Leute:** jeder Decker oder Neuroweaver der
  Party ([[../entities/party-feature]]). Nicht nur der Verursacher. Das
  Ziel selbst hat er nicht genannt.
- **Electronic Warfare** kommt zur Tarnung dazu, ersetzt sie nicht. Die
  Tarn-Zeile oben bleibt. Wie viel ICE, für wen, und ob dieselbe Probe
  beides macht, ist offen.

### Offene Achsen — nicht raten

1. Welche Fertigkeit, gegen wessen ICE (Person, Commlink, Waffe, Deck,
   Konsole)? Kein ICE: welche Schwelle, wenn der Wert 0 ist?
2. Electronic Warfare zusätzlich zur Tarnung: eine Probe oder zwei? Bonus
   für die ganze Party oder jeder sein ICE? Höhe = Erfolge, fest, Deckel?
3. Weiß das Ziel Bescheid? Sieht die SL es? Feind-Effekt läuft nach den
   Runden von selbst aus, oder bleibt er hängen wie bei eigenen Leuten?
4. Widerstand zusätzlich zum ICE-Wurf, oder ist der ICE-Wurf die ganze
   Probe? Auch gegen Party-Kollegen?

Keine Datenmodell-Antwort, bis diese Achsen besprochen sind.

## Siehe auch

- [[magie-hexkraft]] — der exklusive Gegenweg
- [[willenskraft]] — gemeinsame Ressource beider Wege
- [[../entities/neo4j-datenmodell]] — TraitDef-Umbenennungs-Fallstrick im Detail
- [[augments-ausruestung]] — montierte Upgrades
- [[cyberware-bioware]] — Körper-Cyberware, Bioware ausgenommen
- [[drohnen-fahrzeuge]] — Riggerkonsole und schon gesprungene Drohnen
- [[kampf-und-initiative]] — Runden, falls die Dauer nur im Kampf gilt
