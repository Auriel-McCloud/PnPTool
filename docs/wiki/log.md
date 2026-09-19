# PnPTool Wiki Log

> Chronologischer Verlauf aller Wiki-Aktionen. Nur anhängen.
> Format: `## [YYYY-MM-DD] aktion | betreff`

## [2026-09-18] create | Wiki initialisiert

- Domain: NeotopiA-Regelsystem (mit Versionsgeschichte) + PnPTool-Architektur
- Struktur angelegt: SCHEMA.md, index.md, log.md, concepts/, entities/, comparisons/
- Auslöser: Mark wollte einen Gesamt-Index von Regeln, Datenbank und Projektstand,
  nach dem Karpathy-LLM-Wiki-Muster, mit ausdrücklichem Hinweis dass die
  Excel-Transkription vom Vortag nur "Version 1" der Regeln ist und die
  Weiterentwicklung im Projekt mitdokumentiert werden soll

## [2026-09-18] ingest | Erstbefüllung aus CLAUDE.md, ENTWICKLUNGSHISTORIE.md, docs/api/*, docs/regeln-neotopia.md, Git-Log, Backend-Code

Quellen gelesen: `CLAUDE.md` (459 Zeilen komplett), `docs/regeln-neotopia.md`
(242 Zeilen komplett), alle 10 `docs/api/*.md`, `docs/theming.md`,
`docs/ui-konzept.md` (Auszug), `docs/ENTWICKLUNGSHISTORIE.md`, Git-Log von
`docs/regeln-neotopia.md` und `CLAUDE.md`, Cypher-Migrationsdateien,
Repository-Dateien in `backend/app/*/repository.py` (Beziehungstypen).

Angelegt (siehe `index.md` für die vollständige Liste mit Zusammenfassung):

**Konzepte (Regeln, mit Entwicklungsgeschichte):**
`wuerfelsystem`, `attribute-und-fertigkeiten`, `charaktererschaffung`, `rassen`,
`magie-hexkraft`, `neuroweaving-decking`, `kampf-und-initiative`,
`ruestung-kaestchen-durchlass`, `cyberware-bioware`, `willenskraft`,
`drohnen-fahrzeuge`, `erfahrung-und-steigern`, `waehrung-und-preise`

**Entitäten (Architektur/Features):**
`architektur-drei-ebenen`, `neo4j-datenmodell`, `mitteilungen-system`,
`kontakte-messenger`, `ingame-wiki-feature`, `rassen-baukasten-feature`,
`theming-system`, `ui-konzept-commlink`, `auth-und-rollen`, `ki-integration`,
`tech-stack`

**Vergleiche:**
`regelwerk-excel-vs-aktuell` (zentrale Seite für Marks Anliegen — was hat sich
seit der Excel-Transkription alles geändert), `veraltete-docs-vs-code` (Fund:
`docs/api/personen.md` und `docs/api/entitaeten.md` beschreiben ein anderes
Attribut-/Essenzsystem als der tatsächliche Code — für Mark zur Prüfung markiert)

**Wichtigster Befund:** Die Excel-Datei (`Neotopia.xlsx`, zuletzt bearbeitet
29.08.2026) ist der Regelstand vor Projektstart. Seit Projektbeginn (28.08.2026)
gab es u. a.: Arete→Hexkraft, Technomancer→Neuroweaver, Gesundheit 5→6,
komplettes neues Rüstungssystem (Kästchen+Durchlass statt flachem Bonus),
Matrix-Verteidigung des Neuroweavers auf Fassung+Geistesschärfe umgestellt
(Excel sagt noch Willenskraft), Chrom-Rundungsregel, Rassen-Baukasten mit
gefundener 15er-Balance-Formel, Drei-Ebenen-Architektur Regelsystem→Kampagne→
Ideenschmiede. Details je Konzeptseite unter "Entwicklung".

## [2026-09-18] update | Verbindliche Wiki-Pflicht in CLAUDE.md + SCHEMA.md verankert

Mark: CLAUDE.md soll klein bleiben (Details wandern nach docs/api/ bzw. ins
Wiki), aber das Wiki muss aktiv befragt werden, um "Erfindungen" (doppelte
oder widersprüchliche Entscheidungen) zu vermeiden.

- `CLAUDE.md`: neuer Abschnitt "Vor jedem Task: Wiki befragen" — `docs/wiki/index.md`
  zuerst lesen, betroffene Wiki-Seite nach jeder inhaltlichen Änderung nachziehen.
  Wiki-Link in die "Wichtige Dokumentation"-Liste aufgenommen.
- `SCHEMA.md`: Update-Policy um explizite "vorher lesen / nachher nachziehen"-Regel
  ergänzt, direkt über der Widerspruchs-Regel.

## [2026-09-18] update | Kästchen-Overflow-Bugfix (Füllrichtung, Rüstungs-/Willenskraft-Umgehung)

Mark hatte die Kästchen-Overflow-Darstellung schon gebaut (nicht im Wiki
erfasst gewesen — Erstbefüllung hatte sie fälschlich als "offen" markiert,
siehe `CLAUDE.md` Punkt 9 zum Zeitpunkt des ersten Ingests), fand sie aber
"nicht 100%ig" beim Ausprobieren am Spieltisch. Code-Analyse (kein Erraten)
fand drei konkrete, unabhängig behobene Fehler:

1. Füllrichtung uneinheitlich zwischen Gesundheit (Puffer zuerst) und
   Willenskraft/I.C.E. (Enden zuerst) — durchgerechnet mit Python, bestätigt.
   Fix: beide füllen jetzt von vorne (Puffer zuerst), Marks ausdrücklicher
   Wunsch nach Rückfrage ("die Schmalen zuerst, die Großen erst wenn's
   kritisch wird").
2. Charakterblatt-Gesundheitsleiste hatte einen zweiten, direkten
   Schaden-Weg (Zahlenpad), der die Rüstungsrechnung (`RuestungsTreffer`,
   ⚡-Knopf) komplett umging. Neues `ZustandFenster`-Prop `schadenErlaubt`
   sperrt diesen Weg für Gesundheit.
3. **Von Mark selbst am System entdeckt, nicht vorher vermutet:** Ryu
   (22 Willenskraft) bekam nie die Pflicht-Rückfrage vor dem Ausgeben,
   "Mark" (wenig Willenskraft) schon — weil ab 11 Kästchen die Leiste zum
   Öffnen-Knopf kippt und das dortige Zahlenpad die Willenskraft-
   Sonderregeln (1 auf einmal, Rückfrage, kein Selbst-Heilen) nicht kennt.
   Fix: Zahlenpad für Willenskraft ebenfalls gesperrt, echter Klick-Handler
   mit Rückfrage auch in der Vollansicht durchgereicht.

Geändert: `frontend/src/traits/Kaestchen.tsx`, `ZustandFenster.tsx`,
`Charakterblatt.tsx`, `frontend/src/kampf/Kampfkarte.tsx`. Verifiziert per
`tsc --noEmit` (keine Typfehler) und Nachrechnen der Füllreihenfolge in
Python — nicht im Browser durchgeklickt (Login-Automatisierung nicht
abgeschlossen), Mark sollte am Tisch nochmal gegenprüfen.
`docs/wiki/concepts/attribute-und-fertigkeiten.md` und `CLAUDE.md` Punkt 9
nachgezogen (Status offen → fertig, mit Datum).

## [2026-09-18] update | Rüstungstreffer-Zahleneingabe vereinheitlicht

Mark hat beim Gegenprüfen des Kästchen-Overflow-Fixes selbst einen vierten
Punkt gefunden (mit Screenshots belegt): der „⚡ Treffer eintragen"-Knopf
(Rüstungsrechnung) hatte noch ein rohes `<input type="number">` für die
Stärke, optisch inkonsistent zum neuen Zahlenpad in Gesundheit/Willenskraft.
Fix: `frontend/src/shell/Zahlenpad.tsx` — den Ziffernblock aus
`ZustandFenster.tsx` als eigene Komponente extrahiert, jetzt in beiden
Fenstern verwendet. `docs/wiki/concepts/attribute-und-fertigkeiten.md`
nachgezogen.

## [2026-09-18] update | Rüstung: Durchlass durch Schadensreduktion ersetzt

Mark, nach dem ersten echten Praxistest am Spieltisch: "Durchlass ist ein
dummer Wert, sorry... wir ersetzen ihn durch Schadensreduktion, wieviel
Schaden von der Rüstung absorbiert wird, und alles darüber hinaus geht durch
bzw. wird eben eins runter gesetzt." Kompletter Umbau des zweiten
Rüstungswerts:

- Bedeutung gedreht: "niedriger=besser, Größe der Lücke" → "höher=besser,
  wie viel Schaden abgefangen wird" (klassischer Soak-Wert)
- Design-Entscheidung im Gespräch geklärt: absorbiert = min(Stärke,
  Reduktion), Rest kommt durch; Reduktion sinkt gestuft mit dem
  Kästchen-Anteil (>50% voll, >25% halb, sonst ein Viertel) statt einen
  eigenen Aktuell-Wert zu brauchen — Marks Idee, mit dem Vergleich
  Lederjacke (bleibt konstant) vs. Bombenschutzanzug (wird spürbar
  schwächer); Kästchen-System und Abstufung blieben unverändert
- Zwei alte Test-Rüstungen in der echten Kampagne auf Marks Wunsch gelöscht
  statt migriert ("einfach löschen")

Geändert: `backend/app/kampf/ruestung.py` (Kernformel neu), `items/schemas.py`,
`items/repository.py`, `items/routes.py`, `traits/routes.py`,
`tests/test_ruestung.py` (alle 26 Tests neu geschrieben), sowie
`frontend/src/items/api.ts`, `traits/bogenApi.ts`, `traits/Charakterblatt.tsx`,
`traits/CharacterSheetPanel.tsx`, `kampf/Kampfkarte.tsx`. `docs/api/ruestung.md`
komplett neu geschrieben (mit Abschnitt zur abgelösten Durchlass-Fassung),
`docs/wiki/concepts/ruestung-kaestchen-durchlass.md` überarbeitet.

Verifiziert: `tsc --noEmit` fehlerfrei, alle 408 Backend-Tests grün, live
gegen die echte Kampagne getestet (Anlegen, Ausrüsten, Treffer mit
absorbiert/durchkommend-Rechnung nachvollzogen, Reparatur) — alle
Testgegenstände danach wieder gelöscht.

## [2026-09-18] update | Rüstungstreffer: Vorschlags-1 wurde angehängt statt ersetzt

Mark: „steht automatisch 1 als Vorschlag, tippe ich 4 wird daraus 14 statt 4".
Fix: `staerkeIstVorschlag`-Flag in `RuestungsTreffer.tsx` — der erste
Tastendruck ersetzt die Vorgabe komplett (wie ein markiertes Eingabefeld),
danach hängt das Pad normal an. Gesundheit/Willenskraft waren nicht
betroffen, die starten leer statt mit einer Vorgabe.

## [2026-09-18] update | Doppelter Gewicht/Traglast-Schalter entfernt

Mark: der „Zugang"-Bereich hatte einen eigenen „Spielregeln"-Abschnitt mit
demselben Gewicht/Traglast-Schalter wie das eigentliche Einstellungen-Fenster
— „das war einfach eine der ersten Sachen, die wir gemacht haben", nie
aufgeräumt. Fix: Abschnitt aus `frontend/src/players/SpielerVerwaltung.tsx`
entfernt (inkl. ungenutztem `einstellungenApi`-Import und State), der
Schalter existiert unverändert weiter in `campaigns/EinstellungenFenster.tsx`
(über die Werkzeugleiste erreichbar, nicht bereichsgebunden) — kein
Verschieben von Logik nötig, reines Duplikat-Löschen.

`docs/wiki/entities/ui-konzept-commlink.md` um neuen Abschnitt
„Kampagnenweite Einstellungen — ein Ort, nicht zwei" ergänzt, `CLAUDE.md`
Stand-Sektion (18.09.2026) nachgezogen.

## [2026-09-18] update | Bug: frisch aktivierte Rüstung nicht ausrüstbar

Mark: neuen Gegenstand erstellt, im Bearbeiten-Formular zur Rüstung gemacht,
landete beim Ausrüsten immer im Mitgeführten (SL und Spieler gleichermaßen).
Ursache gefunden: `create_gegenstand` zieht `ruestungKaestchenAktuell` auf
`Max` nach, `update_gegenstand` (der PATCH-Pfad des Bearbeiten-Formulars)
tat das nicht — die 409-Wiederanlegen-Sperre gegen zerschossene Rüstung
(siehe `docs/wiki/concepts/ruestung-kaestchen-durchlass.md` Punkt 6) griff
dadurch bei jeder frisch aktivierten Rüstung sofort, obwohl nie getroffen.

Fix in `backend/app/items/repository.py::update_gegenstand`: zieht
`ruestungKaestchenAktuell`/`ruestungDurchlassAktuell` nach, aber nur wenn das
Stück vorher `ruestungKaestchenMax == 0` hatte — bereits aktive, beschädigte
Rüstung bleibt beim Bearbeiten anderer Felder unangetastet (durch zwei
Gegenproben gegen die echte Kampagne bestätigt, testgegenstände wieder
gelöscht, kein Unittest ergänzt mangels DB-Fixture im bestehenden Testmuster).

`docs/wiki/concepts/ruestung-kaestchen-durchlass.md` Punkt 7 und `CLAUDE.md`
nachgezogen.

## [2026-09-18] create | Party-Feature: wiederentdeckte Vision umgesetzt

Mark wollte Spieler zu einer "Party"/"Spielgruppe" zusammenfassen können,
um sie gemeinsam einem Ort oder Event zuzuordnen (z.B. "die Gruppe betritt
eine Bar"), abgegrenzt von Fraktionen (dauerhafte Organisationen mit Zielen/
Ressourcen). Beim Nachschauen im Git-Verlauf gefunden: **diese Idee gab es
schon** — 28.08.2026 in `CLAUDE.md` festgehalten, beim großen
Verschlankungs-Commit (2500→170 Zeilen) verlorengegangen, nur ein toter
Verweis in `docs/ui-konzept.md` blieb übrig. Marks damalige Formulierung war
sogar präziser: *"Spieler bilden nicht immer eine einzige feste Gruppe —
sie können sich aufteilen, wodurch mehrere gleichzeitige, temporäre Partys
entstehen."*

Design-Entscheidungen im Gespräch geklärt:
- Eine Person ist höchstens in einer Party gleichzeitig (automatischer
  Wechsel statt Doppelmitgliedschaft)
- Party ist ein dauerhaftes Objekt, kein Wegwerfobjekt
- Gemischte Mitgliedschaft (PC+NPC+Begleiter) erlaubt
- **Neu gegenüber der alten Notiz:** höchstens eine Party pro Kampagne ist
  "aktiv" — Mark: die aktive Party soll später die Musik auslösen, die zu
  ihrem Aufenthaltsort gehört (Spotify/Yamaha-MusicCast-Anbindung). Damit
  bekommt die alte Vision einen konkreten neuen Zweck, den es 28.08. noch
  nicht gab.

Neues Backend-Modul `backend/app/party/` (Schema, Repository, Routes) nach
dem Muster von `begleiter/` — zwei neue Beziehungstypen
(`MITGLIED_VON`, `BEFINDET_SICH_AN`), beide mit "alte Kante weg, neue rein"-
Logik wie bei der Gegenstands-Ablage. Neuer Frontend-Bereich (👥-Symbol,
Kachelraster + Bearbeiten-Fenster) nach dem Muster von `begleiter/`.

Verifiziert live gegen die echte Kampagne: Party anlegen, zwei Mitglieder
aufnehmen, Aufenthaltsort setzen, Aktiv-Exklusivität geprüft (zweite Party
aktivieren deaktiviert automatisch die erste), Mitgliedschaftswechsel ohne
Doppelmitgliedschaft bestätigt — alle Testobjekte wieder gelöscht.
`tsc --noEmit` fehlerfrei, alle 408 Backend-Tests weiterhin grün.

Dokumentiert: `docs/api/party.md` (neu), `docs/wiki/entities/party-feature.md`
(neu), `docs/wiki/entities/neo4j-datenmodell.md` (neue Beziehungstypen
ergänzt), `CLAUDE.md` (Projektstruktur, Stand der Umsetzung, Zuletzt gebaut,
Spotify-Punkt bei geplanten Features verlinkt).

**Bewusst zurückgestellt (Phase 2):** Marks Inventar-Idee (Party-Mitgliedern
gegenseitig Gegenstände geben können) — eigenes, unabhängiges Feature mit
neuer Berechtigungsregel, sollte Phase 1 nicht aufblähen.

## [2026-09-18] update | Anlegen-Popup statt Inline-Formular

Mark hatte den fertigen Bereich getestet und bemängelt: "es ist leider
nicht im Stil vom Rest, bitte mache den party anlege button so das ein
popup aufgeht das nach dem namen fragt, vielleicht kann man in dem popup
auch gleich angeben wer in der Party ist" — Verstoß gegen die UI-
Konvention (Dialoge/Listen-Bearbeitung immer als Commlink-Popup, nie
Inline-Formular). Fix nach dem Muster von `rassen/RassenUebersicht.tsx`
(dort schon korrekt umgesetzt): "+ Neue Party" öffnet jetzt ein
`Fenster`-Popup mit Namensfeld und einer Checkbox-Liste aller Personen zur
Sofortauswahl, statt eines Inline-`<form>` auf der Übersichtsseite.

## [2026-09-19] update | Neonflackern verstärkt (Ameisenkrieg-Rauschen + Bildverzerrung)

Mark nach dem Praxistest: *"das flackern ist zu kurz, könntest du die länge
mindestens verdreifachen"*, gewünschtes Bild: *"wie bei einem alten
Fernseher wo das Bild kurzzeitig mit schwarz-weißen Ameisenkrieg-Flecken
übersäht ist aber das Bild drunter noch verzerrt durchscheint"*.

Umsetzung in `frontend/src/shell/CommlinkShell.tsx` (`Stoerung`) +
`commlink.css` (`.cl-stoerung`):
- Dauer 0,45s → 1,6s (mehr als verdreifacht, `STOERUNG_MS`)
- Drei übereinanderliegende Schichten statt nur Farbtönung: Neon-Tint
  (Basis, wie zuvor), SVG-`feTurbulence`-Filter für Schwarz-Weiß-Rauschen
  (`mix-blend-mode: overlay`), `backdrop-filter` für sichtbare Verzerrung
  des durchscheinenden Inhalts
- `steps(1, end)` in mehreren harten Schüben statt weichem Fade

`tsc --noEmit` fehlerfrei geprüft. Commit `6450f62`.

Dokumentiert: `docs/wiki/entities/ui-konzept-commlink.md` (neuer Abschnitt
„Das Gerät stört mit"), `docs/ui-konzept.md`, `CLAUDE.md` (Zuletzt gebaut),
`docs/wiki/index.md` (Zusammenfassungszeile).
