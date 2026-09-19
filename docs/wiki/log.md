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
