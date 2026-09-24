# PnPTool Wiki Log

> Chronologischer Verlauf aller Wiki-Aktionen. Nur anhängen.
> Format: `## [YYYY-MM-DD] aktion | betreff`

## [2026-09-24] update | concepts/waehrung-und-preise (KI-Alltagsgegenstand-Erzeugung)

Neues Modul `backend/app/haendler/alltagswunsch.py`: Spieler fragt einen
Verkäufer im Shop nach einem Alltagsgegenstand, der nicht im Sortiment
steht (z.B. Panzerklebeband), die KI schätzt sofort Preis + Typ und schickt
den Vorschlag als Popup an die SL zur Freigabe — der Spieler muss nicht
warten. Harter Ausschluss von Waffen/Rüstung über zwei unabhängige Sperren
(Typ-Whitelist + KI-Selbsteinschätzung `istVerboten`). Backend UND Frontend
fertig (SL-Freigabe-Popup, Spieler-Ergebnis-Popup, Eingabefeld im Shop),
per echtem E2E-Test gegen laufendes Backend + Neo4j + echten KI-Provider
verifiziert (harmloser Wunsch UND Waffen-Ausschluss beide grün). Frontend
nur `tsc -b` geprüft, kein Browser-Klicktest.

## [2026-09-24] update | concepts/waehrung-und-preise

Shop-Frontend Phase 1+2: Backend um Vertriebsart (PHYSISCH/DIGITAL),
Sonderangebote (rabattProzent) und Online-Bestellungen mit SL-Freigabe
erweitert; Verhandeln um SHOP_KAUF erweitert (bestehender generischer
Mechanismus, unverändert). Frontend erster Wurf: eigener Burgermenü-Punkt
"Shop", Kachelraster, physisch/digital getrennte Shop-Seiten,
CSS-Seltenheitsrahmen (grau/blau/silbern-glitzernd/orange-gezackt/
violett-wabernd). Backend end-to-end verifiziert, Frontend nur `tsc -b`
geprüft (kein Browser-Klicktest möglich).

## [2026-09-24] update | concepts/magie-hexkraft

Häretiker-Flavor-Option ergänzt: zweite, mechanisch identische Alternative
zu „Magier" bei der Charaktererstellung, reine Anzeige-Ebene (neues Feld
`magieFlavor`, `weg` bleibt intern immer `MAGIER`). Hexkraft→Glauben, Wilde
Magie→Blasphemie, neun Sphären→Götternamen aus acht Mythologien (Details
CLAUDE.md Punkt 14). Backend + Frontend über 7 Commits gebaut, echtes
Backend-only-E2E-Skript gegen laufendes Backend + echte Neo4j bestanden
(Katalog-Identität Magier/Häretiker, alle Tooltip-Texte abrufbar),
Testdaten danach entfernt.

## [2026-09-24] create | entities/kampagnen-export-import

Nachts autonom gebaut (Mark schlief, Token-Kontingent lief nach Fertigstellung
in ein Rate-Limit — Cronjob hat den Rest am Morgen verifiziert/aufgeräumt).
Neue Seite `entities/kampagnen-export-import.md` + `docs/api/
campaigns-export-import.md`. SL kann eine komplette Kampagne (Knoten, Kanten,
Bilder, Spieler-Accounts) als ZIP exportieren und als neue Kampagne wieder
importieren. Generische Cypher-Sammlung statt Sonderfall je Entitätstyp,
ID-Neuvergabe per Text-Ersetzungsrunde auf dem rohen JSON, Weisslisten gegen
manipulierte Importpakete. Echter E2E-Testlauf gegen laufendes Backend +
echte Neo4j bestanden, beide Testkampagnen danach entfernt.

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

## [2026-09-20] update | Wiki-Editor am Handy: lesbare Schriftgröße

Mark berichtete, der Editor-Text im Story-Wiki sei am Handy nicht lesbar
(zu klein), Vollbild-Layout sollte aber bleiben. Ursache: globale
Basisschriftgröße 16px, keine Handy-spezifische Anpassung im Editor.

Fix: `frontend/src/wiki/wiki.css`, neue `@media (max-width: 599px)`-Regel
für `.wk-editor .ProseMirror` (18px/1.6, Überschriften 26/21/18px). Rein
clientseitig, kein neuer/geänderter Endpunkt, daher kein `docs/api/`-Eintrag.
`tsc -b` fehlerfrei.

Dokumentiert: `docs/wiki/entities/ingame-wiki-feature.md` (neuer Abschnitt),
`docs/wiki/index.md` (Zusammenfassungszeile), `CLAUDE.md` (Zuletzt gebaut).
Betrifft nur einen Teilaspekt von CLAUDE.md Punkt 13 („Handy-Ansicht für
Story-Wiki + Ideenschmiede") — Seitenbaum/Kachel-Übersicht/Verweis-Auswahl
am Handy bleiben offen.

## [2026-09-20] create | Wiki-Rechtschreib-/Grammatik-/Logikprüfung

Erster Teil von Marks angekündigtem KI-Auftrag ("Auto-Verknüpfung machen wir
danach") — die Fehlerprüfung im Wiki-Editor. Neues Backend-Modul
`backend/app/ki/wiki_pruefung.py`: `pruefe_seite()` (eine Seite, Editor-
Knopf) und `sweep()` (alle Seiten, Einstellungen-Knopf, überspringt
unveränderte via SHA-256-Hash `pruefHash` am `WikiSeite`-Knoten). Drei neue
Endpunkte unter `/api/campaigns/{id}/ki/wiki/*`, dokumentiert in
`docs/api/ki.md` (neu angelegt, `docs/api/README.md` verlinkt es).

Logikfehler nutzen den freigegebenen Kampagnenkontext (`sammle_kontext()`,
dieselbe Quelle wie der NPC-Generator). Erster Testlauf zeigte einen
Fehlalarm: ein neu eingeführter, in der Welt noch unbekannter Name wurde als
"Logikfehler" gemeldet — Prompt nachgeschärft ("NUR ein direkter Widerspruch
zu einer bereits bestehenden Tatsache, ein unbekannter Name ist KEIN
Fehler"), danach korrekt: nur echte Rechtschreib-/Grammatikfehler blieben.

Frontend: `frontend/src/wiki/PruefungPopup.tsx` (neu, gemeinsam genutzt von
`WikiEditor.tsx` und `campaigns/EinstellungenFenster.tsx`). Jeder Befund
zeigt Zitat+Vorschlag, "✓ Übernehmen" ruft die Backend-Route (ersetzt den
Text direkt im gespeicherten TipTap-Dokument, auch wenn die Seite nicht
offen ist), "↷ Zur Textstelle" nur im Editor verdrahtet (sucht/markiert via
`editor.state.doc.descendants()`).

Verifiziert: Backend-Import-Check, Routenregistrierung (`openapi.json`
zeigt alle drei Pfade), End-to-End gegen echte Neo4j-DB + echten
Mistral-Call (5 Rechtschreibfehler + 1 Grammatikfehler korrekt erkannt,
"Übernehmen" ersetzte den Text im Dokument, zweiter Sweep-Lauf übersprang
die unveränderte Seite korrekt), `tsc -b` fehlerfrei.

Dokumentiert: `docs/wiki/entities/ki-integration.md` (neuer Abschnitt),
`docs/wiki/index.md` (Zusammenfassungszeile), `CLAUDE.md` (Zuletzt gebaut +
Punkt 3 als teilweise erledigt markiert), `docs/api/ki.md` (neu),
`docs/api/README.md` (Tabellenzeile). Skill-Referenz
`ki-gemini-integration.md` um den vollen Bauverlauf ergänzt.

## [2026-09-22] update | Decker/Neuroweaver/KI-Skills auf 6 erweitert + drei Folgefixes

Marks Vorschlag vom 20.09. (siehe `CLAUDE.md` Punkt 9) umgesetzt: zwei neue
NeuroWeaving-Fertigkeiten **Electronic Warfare** ("Rauschen" — Ortungs-
tarnung, kein Angriff, Radius+Dauer aus einer Probe) und **Matrix-Navigation**
(Erfolgsstufen finden Systeme bis hin zu Backdoors). Gilt für NeuroWeaver,
Decker (neue Deck-Werte `deckElectronicWarfare`/`deckMatrixNavigation`) UND
KI. Katalog: `backend/app/traits/seed.py`. Cyberdecks als echte Gegenstände
bewusst nicht Teil dieser Arbeit (Mark macht das separat).

Auch: Spotify-Eintrag in `CLAUDE.md` Punkt 4 auf "fertig, keine Yamaha-
Anbindung geplant" korrigiert (war zuvor fälschlich noch als offen markiert).

**Vier Folgefehler beim ersten Praxistest gefunden** (Mark erstellt einen
Neuroweaver "Cyborg") — alle in `docs/wiki/concepts/neuroweaving-decking.md`
unter "Entwicklung" im Detail:

1. NeuroWeaving-Grundwert fehlte in der Freebee- und LevelUp-Anzeige
   (`Charaktererstellung.tsx`/`LevelUp.tsx`) — feste Kategorienliste kannte
   `NeuroWeavingWert` nicht, nur die sechs Fertigkeiten darunter.
2. Grundwert-Maximum stand auf 10 (wie Hexkraft), sollte aber 6 sein: anders
   als Hexkraft (allein gewürfelt) wird NeuroWeaving immer mit einer
   Fertigkeit kombiniert — bei Max 10 hätte der Grundwert allein den
   Pool-Deckel ausschöpfen können.
3. Derselbe Anzeige-Fehler wie Punkt 1 auch im Charakterblatt selbst
   (`Charakterblatt.tsx`) — dritte, unabhängige Fundstelle.
4. Probenauswahl (`Probe.tsx`) verlangte beim Klick auf eine Fertigkeit
   einen Pflichtklick auf den einzigen möglichen Partner (den Grundwert) —
   jetzt automatisch vorausgewählt, wenn nur ein Kandidat existiert.

**Zwei weitere Anpassungen auf Marks Wunsch:**

5. "Wilde Magie" bei NeuroWeaving in **"Overclock"** umbenannt — war ein
   Copy-Paste-Rest von der Hexkraft-Seite und passte inhaltlich nicht
   (Nervensystem übers Limit pushen statt Magie wirken). Gleiche Mechanik
   (Bonuswürfel bis Willenskraft, Zielwert ansagen, Rückstoß-Willenskraftwurf
   bei Erfolg) — nur Name und Hinweistexte geändert, `magie.ts`/`Probe.tsx`/
   `WillenskraftFrage.tsx`.
6. NeuroWeaving-Pool-Deckel von 10 auf **12** angehoben — seit der
   Skill-Erweiterung ist überall 6 das neue Maximum, 10 wirkte als
   Pool-Deckel unpassend niedrig; 12 passt zum bereits etablierten "rundes
   Maximum"-Muster im Tool (natürliches Gesundheitsmaximum). Wilde Magie hat
   bewusst weiterhin **keinen** Pool-Deckel — andere Ausgangslage (ein Wert
   allein bis 10, Rückstoß-Risiko als Bremse statt Zahlenlimit); auf
   Nachfrage mit Mark bestätigt, kein Widerspruch.

Verifiziert: Backend-Tests grün (61 relevante + Gesamtlauf bis auf einen
vorbestehenden, unrelated Fehler bei der Spotify-Route), `tsc -b` fehlerfrei
nach jedem Schritt, gegen echte Neo4j-DB verifiziert (6 TraitDefs korrekt
angelegt, Max 6, sortOrder 1-6, Grundwert-Max 6 nach `seed_traits()`-Neustart
übernommen).

Dokumentiert: `CLAUDE.md` Punkt 9 (vollständig, alle sechs Fixes),
`docs/regeln-neotopia.md`, `docs/wiki/concepts/neuroweaving-decking.md`
(Haupt-Zielseite, "Entwicklung"-Abschnitt), `docs/wiki/index.md`
(Zusammenfassungszeile + Datum).

## [2026-09-23] update | KI-Bildgenerierung (lokal Fooocus + cloud Gemini)

Sechster Anwendungsfall auf `entities/ki-integration.md`: neues Modul
`backend/app/ki/bildgenerierung.py`, zwei pro Aufruf wählbare Provider
(Dropdown im neuen `frontend/src/ki/KiBildPopup.tsx`) — cloud (Gemini
`gemini-2.5-flash-image`) und lokal (Fooocus über einen eigenen
Wrapper-Prozess `C:\DEV\Fooocus\pnptool_server.py`, bewusst außerhalb des
Repos). Neue Routen `POST .../ki/bild-prompt` (Prompt-Vorschlag) und
`POST .../ki/bild-generieren` (liefert nur eine Vorschau, speichert nichts)
sowie die Spieler-Pendants `/api/spieler/mein-bild-ki-prompt` +
`/mein-bild-ki` fürs eigene Charakterportrait. Eingebunden an Person/Event/
Ort/Fraktion/Gegenstand (SL) und Spieler-Portrait. Details: `docs/api/ki.md`,
`docs/api/auth.md`, `docs/wiki/entities/ki-integration.md`.

Verifiziert: Backend-Import, alle Routen im OpenAPI-Schema, `tsc -b`
fehlerfrei, echter E2E-Call (Prompt-Vorschlag) gegen laufendes Backend +
echte Neo4j-Daten + echten Gemini-Key erfolgreich; Bildgenerierung für
beide Provider je einmal live getestet. **Offen:** kein Klicktest von
`KiBildPopup.tsx` im laufenden Frontend (nur `tsc -b` geprüft) — Mark prüft
das selbst; der Fooocus-Wrapper muss manuell als Hintergrundprozess laufen,
sonst schlägt der "lokal"-Provider fehl.

Dokumentiert: `CLAUDE.md` ("Zuletzt gebaut" + Punkt 3 "KI-Integration" +
Punkt 11 "Charakterportrait im Spieler-Menü"), `docs/api/ki.md`,
`docs/api/auth.md`, `docs/wiki/entities/ki-integration.md`,
`docs/wiki/index.md` (Zusammenfassungszeile).

## [2026-09-23] update | Wiki-Import per Dokument-Upload (.docx/.pdf)

Siebter Anwendungsfall auf `entities/ki-integration.md`: neues Modul
`backend/app/ki/wiki_import.py`. SL lädt ein Word- oder PDF-Dokument hoch
(`POST .../ki/wiki/import`, Multipart) — die KI erkennt die Struktur
(Überschriften/Kapitel: .docx-Formatvorlagen "Heading 1".."Heading 9" als
`#`-Präfixe mitgegeben, .pdf rein am Textmuster) und teilt den Text
automatisch in eine oder mehrere Wiki-Seiten-Entwürfe auf
(`istEntwurf=true`, Eltern-Kind-Hierarchie über `elternIndex` aus der
KI-Antwort). Dokumente über 60.000 Zeichen werden abgelehnt statt
unvollständig importiert.

Pro neu angelegter Seite läuft automatisch die bestehende
Auto-Verknüpfung (`auto_verknuepfung.py`, unverändert wiederverwendet,
alle Vorschläge sofort angewandt statt einzeln bestätigt wie beim
manuellen Knopf). Frontend: `frontend/src/ki/WikiImportPopup.tsx`
(Commlink-Stil), Knopf `⇪✨` in `WikiAnsicht.tsx` neben "+ Neue Seite",
Ergebnis-Liste springt zur Prüfung in die bestehende Ideenschmiede.

Verifiziert: Backend-Import ok, Route im OpenAPI-Schema, `tsc -b`
fehlerfrei, echter E2E-Testlauf gegen laufendes Backend + echte Neo4j +
echten Mistral-Call — Test-.docx mit 2 Kapiteln + 2 Unterkapiteln ergab 5
korrekt verschachtelte Entwurfs-Seiten; eine vorab angelegte Person wurde
per Auto-Verknüpfung korrekt wiedererkannt (keine Dublette), mehrere
unbekannte erwähnte Entitäten automatisch als Entwürfe samt
Beziehungskanten angelegt. **Offen:** kein Klicktest von
`WikiImportPopup.tsx` im laufenden Frontend (nur `tsc -b`); PDF-Pfad
ungetestet (nur .docx real durchlaufen); die 60.000-Zeichen-Grenze ist
eine Schätzung, kein ermitteltes Kontextfenster-Limit.

Dokumentiert: `CLAUDE.md` ("Zuletzt gebaut" + Punkt 3 "KI-Integration",
Wiki-Import von offen auf gebaut gesetzt), `docs/api/ki.md`,
`docs/wiki/entities/ki-integration.md`, `docs/wiki/index.md`
(Zusammenfassungszeile).
