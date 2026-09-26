# PnPTool Wiki — Schema

## Domain

Projekt-Wiki für **PnPTool** (`C:\DEV\PnPTool`) — FastAPI+Neo4j+React-Werkzeug für
Marks Pen-and-Paper-Runden, Homebrew-Regelsystem **NeotopiA**. Deckt zwei Bereiche ab:

1. **Regelsystem NeotopiA** — Spielregeln, ihre Herkunft (Excel/M20/WoD/Shadowrun)
   und ihre **Weiterentwicklung im Projektverlauf** (die Excel-Datei ist "Version 1",
   viele Regeln wurden seither im Tool weiterentwickelt und weichen bewusst ab).
2. **Werkzeug-Architektur** — Datenmodell (Neo4j), Backend-Module, Frontend-Konzepte,
   Features und ihre Design-Entscheidungen.

## Verhältnis zu bestehender Dokumentation

**Dieses Wiki ersetzt nichts.** `CLAUDE.md`, `docs/ENTWICKLUNGSHISTORIE.md`,
`docs/api/*.md`, `docs/regeln-neotopia.md`, `docs/reference/Neotopia_*.md` bleiben
unverändert der bisherige Sync-Punkt zwischen Claude-Instanzen (Mark: "CLAUDE.md
eigenständig editieren erlaubt"). Das Wiki hier ist eine **zusätzliche, synthetisierende
Schicht** darüber: es liest diese Dateien plus den Git-Verlauf plus den Code, verlinkt
querbeet und macht Entwicklung/Widersprüche/offene Fragen sichtbar, die in einer
einzelnen linearen Doku schwer zu sehen sind.

**Quellen werden hier NIE kopiert, immer per Pfad referenziert** — es gibt bewusst
kein `raw/`-Verzeichnis mit Duplikaten. "Raw sources" in diesem Wiki sind:
- `CLAUDE.md`, `docs/ENTWICKLUNGSHISTORIE.md`, `docs/api/*.md`, `docs/*.md`
- `docs/reference/Neotopia_*.md` (Excel-Transkription) + `docs/reference/Neotopia.xlsx`
- Git-Historie (`git log --oneline --follow -- <pfad>`)
- Code unter `backend/app/`, `frontend/src/`

## Konventionen

- Dateinamen: kleinschreibung-mit-bindestrichen.md
- Jede Wiki-Seite startet mit YAML-Frontmatter (siehe unten)
- `[[wikilinks]]` zwischen Seiten, mindestens 2 ausgehende Links pro Seite
- Beim Update: `updated`-Datum hochziehen
- Jede neue Seite kommt in `index.md`, jede Aktion in `log.md`
- **Quellenverweise:** `sources:` im Frontmatter verweist auf echte Repo-Pfade
  relativ zu `docs/wiki/` (z. B. `../../CLAUDE.md`, `../api/ruestung.md`,
  `../../backend/app/kampf/ruestung.py`). Bei Aussagen mit Datum: das Datum
  aus der Quelle übernehmen (Commit, CLAUDE.md-Abschnitt), nicht erfinden.
- **Sprache:** Deutsch, wie im gesamten Projekt.

## Frontmatter

```yaml
---
title: Seitentitel
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: konzept | entität | vergleich | query
tags: [aus der Taxonomie unten]
sources: [../../CLAUDE.md, ../api/ruestung.md]
status: aktuell | veraltet | teilweise-umgesetzt | offen | entschieden-nicht-umgesetzt
---
```

`status` ist hier wichtiger als das generische `confidence` aus dem Standard-Schema,
weil die Kernfrage bei diesem Projekt oft ist: *gilt das Excel noch, oder hat das Tool
die Regel überholt?* Werte:
- `aktuell` — so spielt das Tool es heute
- `veraltet` — Excel/alte Doku sagt das, ist aber überholt (mit Verweis auf die Ablösung)
- `teilweise-umgesetzt` — Regel entschieden, Code deckt nur einen Teil ab
- `offen` — explizit unentschieden (siehe CLAUDE.md "Offen"-Abschnitte)
- `entschieden-nicht-umgesetzt` — Design steht, Code fehlt noch

## Tag-Taxonomie

**Regeln:** wuerfelsystem, attribute, fertigkeiten, charaktererschaffung, magie,
neuroweaving, kampf, ruestung, cyberware, drohnen, erfahrung, wirtschaft, rassen

**Architektur:** datenmodell, backend, frontend, websocket, auth, api

**Features:** mitteilungen, kontakte, wiki-feature (= das In-Game-Wiki-Feature des
Tools, nicht dieses Meta-Wiki!), rassen-baukasten, theming, ki-integration, ui,
regelsystem-kampagne-ideenschmiede, party, verhandlung, inventar

**Meta:** versionsgeschichte, widerspruch, offen, geplant

Regel: neue Tags erst hier eintragen, dann benutzen.

## Seiten-Schwellen

- Seite anlegen: Konzept/Feature ist zentral für ≥1 Quelle oder wird in ≥2 erwähnt
- Bei Versions-Historie (Excel → heute): **immer eigener Abschnitt "Entwicklung"**
  mit Datum + Commit, nicht nur der aktuelle Stand — das war Marks expliziter Auftrag
- Seite splitten ab ~200 Zeilen
- **NeotopiA-Regeln ändern sich laufend.** Bei jedem künftigen Ingest (neuer Commit,
  neue CLAUDE.md-Sektion) zuerst `index.md` und die betroffene Konzept-Seite prüfen,
  ob eine bestehende Aussage jetzt veraltet ist — dann den alten Stand nicht löschen,
  sondern in "Entwicklung" verschieben und mit Datum markieren.

## Entity- / Konzept- / Vergleichsseiten

**Konzeptseiten** (`concepts/`): Definition, aktueller Stand, **Entwicklung**
(chronologisch, mit Commit-Hash wo vorhanden), offene Fragen, Cross-Links.

**Entitätsseiten** (`entities/`): Für Architektur-Bausteine (Module, Systeme,
Datenmodell-Ausschnitte). Überblick, Aufbau, Design-Entscheidungen, Cross-Links.

**Vergleichsseiten** (`comparisons/`): Excel/altes Regelwerk vs. aktueller Stand,
oder zwischen widersprüchlichen Dokumenten. Tabelle + Verdikt + Quellen.

## Update-Policy

**Vor jeder neuen Task-Bearbeitung:** `index.md` (und bei Regelfragen zusätzlich
`comparisons/regelwerk-excel-vs-aktuell.md`) lesen, bevor eine Regel oder
Architektur-Entscheidung neu ausgedacht wird — das ist der ganze Zweck dieses
Wikis: **Erfindungen verhindern**, wenn die Frage längst entschieden (oder
bewusst offen gelassen) wurde. Bei Unsicherheit lieber die Konzeptseite
gegenlesen als eine Annahme treffen.

**Nach jeder inhaltlichen Änderung am Projekt:** die betroffene Konzept-/
Entitätsseite nachziehen (neuer „Entwicklung"-Eintrag mit Datum), `index.md`
bei neuen Seiten aktualisieren, `log.md` ergänzen. Das Wiki verfällt sonst
genauso wie eine unbenutzte Doku — sein Wert hängt davon ab, aktuell zu sein.

Bei Widerspruch zwischen Quellen (z. B. Excel sagt X, `CLAUDE.md` sagt Y):
1. Neuere Quelle gewinnt inhaltlich (Datum vergleichen)
2. Beide Positionen mit Datum/Quelle nennen, nicht nur die aktuelle
3. `status: veraltet` an der abgelösten Aussage, mit Link zur Ablösung
4. Bei echtem *ungeklärtem* Widerspruch (z. B. veraltete API-Docs vs. Code):
   eigene `comparisons/`-Seite, für Mark zur Prüfung markiert
