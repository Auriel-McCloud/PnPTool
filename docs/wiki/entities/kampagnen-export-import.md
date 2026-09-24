---
title: Kampagnen-Export/Import
created: 2026-09-24
updated: 2026-09-24
type: entität
tags: [export-import, backend, datenmodell, zip]
sources: [../../api/campaigns-export-import.md, ../../../CLAUDE.md]
status: aktuell
---

# Kampagnen-Export/Import

**Gebaut 24.09.2026, nachts** (autonomer Lauf während Mark schlief, Token-
Kontingent noch übrig). SL kann eine komplette Kampagne als ZIP-Datei
exportieren und als **neue** Kampagne wieder importieren.

Vollständige technische Referenz: [[../../api/campaigns-export-import.md]].

## Kernidee

Zwei generische Cypher-Abfragen statt eines Sonderfalls je Entitätstyp —
die meisten Knoten tragen `campaignId` direkt, zwei Ausnahmen (`Spieler`,
`KampfTeilnehmer`) werden explizit über ihre Kanten nachgezogen. ID-Neuvergabe
läuft über eine einzige Text-Ersetzungsrunde auf dem rohen JSON (UUID als
String kommt an vielen Stellen vor: Kanten-Endpunkte, `campaignId`-Felder,
aber auch versteckt in JSON-als-Text-Listen wie `sichtbarFuer`).

**Globale Katalogknoten** (`Rasse`, `TraitDef`, `Regelsystem`) werden beim
Import **nicht** neu vergeben — sie müssen in der Zieldatenbank bereits
existieren (Seed-Funktionen beim Backend-Start). Fehlt ein solcher
Zielknoten, fällt nur die einzelne Kante weg, der restliche Import läuft
durch.

Import legt **immer** eine neue Kampagne an (Marks Entscheidung gegen
versehentlichen Datenverlust) — nie wird eine bestehende überschrieben.

## Sicherheit

Cypher kann Labels/Beziehungstypen nicht parametrisieren — Weisslisten
(`KNOWN_LABELS`, `KNOWN_REL_TYPES` in `export_import.py`) verhindern, dass
ein manipuliertes ZIP beliebigen Cypher-Text einschleust.

## Frontend

`EinstellungenFenster.tsx`, neue Sektion „KAMPAGNE“: Export-Knopf (simpler
`<a download>`-Anker, Cookie-Auth läuft mit), Import-Upload (verstecktes
`<input type="file">` in einem `.cl-roehre`-Label, Multipart-`fetch`). Nach
erfolgreichem Import wechselt die Kampagnenauswahl automatisch zur neuen
Kampagne.

## Verifiziert

Echter E2E-Lauf gegen laufendes Backend + echte Neo4j (Kampagne mit PC, NPC,
Ort, Gegenstand, Wiki-Seite, Spieler-Account → Export → Import → alle
Prüfungen bestanden, referenzielle Integrität intakt, globale Katalogdaten
unverändert). Beide Testkampagnen danach wieder entfernt. 6 Unit-Tests für
`remap_ids`. `tsc -b` fehlerfrei.

**Offen:** kein Klicktest im laufenden Frontend — Mark sollte Export-Knopf
und Import-Upload einmal am Dev-Server ausprobieren.

## Siehe auch

- [[neo4j-datenmodell]] — die zugrundeliegenden Node-/Beziehungstypen
- [[architektur-drei-ebenen]] — Regelsystem/Kampagne-Trennung, wichtig für
  das Verständnis, warum Katalogknoten beim Export/Import anders behandelt
  werden als kampagnen-eigene Daten
