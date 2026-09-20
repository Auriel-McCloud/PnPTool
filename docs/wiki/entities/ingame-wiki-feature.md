---
title: In-Game-Wiki-Feature
created: 2026-09-18
updated: 2026-09-20
type: entität
tags: [wiki-feature, frontend, ui]
sources: [../../api/wiki.md, ../../../CLAUDE.md]
status: aktuell
---

# In-Game-Wiki-Feature

> **Nicht verwechseln mit diesem Meta-Wiki** (`docs/wiki/`, das Karpathy-Muster
> für Projektdokumentation). Dies hier ist das **In-Game-Feature**, mit dem die
> Spielleitung die Spielwelt für die Spieler dokumentiert — Teil des Produkts,
> nicht der Entwicklerdoku.

## Konzept

„Gedächtnis der Spielwelt": Orte, Personen, Fraktionen, Geschichte. **SL
schreibt, Spieler lesen — aber nur was sie In-Game wissen dürfen.**

**Vier Design-Entscheidungen:**
1. **Nur Seiten, kein Dokumenttyp** — „Wiki-Artikel" vs. „Wiki-Dokumente" war
   eine unnötige Unterscheidung.
2. **SL-only als Standard** — neue Seiten sind erstmal nur für die SL sichtbar,
   explizites Freigeben statt versehentlichem Spoilern.
3. **Entitätsverknüpfungen als echte Graphkanten** (`BESCHREIBT`), keine
   Textsuche — ermöglicht automatische Backlinks und Konsistenzprüfungen.
4. **Freigabe ohne Vererbung** — eine freigegebene Seite gibt die darin
   erwähnten Entitäten NICHT automatisch mit frei. Jede Entität hat ihre eigene
   Sichtbarkeit.

## „Bis hierher"-Freigabe

`POST /seiten/{id}/freigeben` mit `{bisHierher: true}` gibt die Seite UND alle
verlinkten Seiten frei, die bereits als „darf man sehen" **vorbereitet** waren.
Mark: „Ich will einen Knopf der 'diese Seite und alles was sie erwähnt'
freigibt, aber nur was ich vorher schon als 'darf man sehen' markiert habe."

## Kategorien (fix, nicht erweiterbar)

Orte, Personen, Fraktionen, Geschichte, Regeln, Sonstiges.

## Ideenschmiede-Integration

`istEntwurf`-Flag filtert Entwürfe aus dem Wiki-Baum — siehe
[[architektur-drei-ebenen]].

## Datenmodell

`(:WikiSeite {titel, kategorie, zusammenfassung, inhalt, sichtbarFuerSpieler})`
`-[:BESCHREIBT]->` `(:Person|Ort|Fraktion|...)`. Markdown-Inhalt mit internen
Links (`[[Person:Viktor]]`), Bildern, Tabellen — kein HTML (XSS-Schutz beim
Rendern).

## Editor am Handy: lesbare Schriftgröße (20.09.2026)

Mark: der Editor-Text am Handy war „so klein, dass ich nichts lesen kann" —
gemeint war explizit *nicht* das Layout (das ist am Handy schon vollflächig
über `Fenster.tsx`/`fenster.css`, siehe [[ui-konzept-commlink]]), sondern die
Fließtextgröße selbst bei der globalen Basisgröße von 16px.

Fix rein clientseitig in `frontend/src/wiki/wiki.css`: unter 600px bekommt
`.wk-editor .ProseMirror` `font-size: 18px` / `line-height: 1.6`
(Überschriften 26/21/18px). Bewusst nur der Editor-Inhalt betroffen, nicht
Baum/Werkzeugleiste/Verzeichnis — die bleiben eng, damit am Handy noch
mehrere Bedienelemente nebeneinander passen. Kein neuer Endpunkt, daher
kein Eintrag in `docs/api/`.

Noch offen aus demselben Feature-Wunsch (CLAUDE.md Punkt 13): Seitenbaum/
Kachel-Übersicht und Verweis-Auswahl (`VerweisWaehler.tsx`) am Handy sind
davon unberührt.

## Siehe auch

- [[architektur-drei-ebenen]] — Story-Wiki vs. Ideenschmiede
- [[neo4j-datenmodell]] — `BESCHREIBT`/`HAT_SEITE`/`UNTERSEITE_VON`/`VERWEIST_AUF`
- [[../../produktvision-wiki.md]] — ursprüngliche Produktvision (falls noch relevant, nicht in diesem Ingest gelesen)
