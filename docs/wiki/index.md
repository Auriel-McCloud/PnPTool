# PnPTool Wiki — Index

> Content-Katalog. Jede Seite mit Kurzbeschreibung. Zuerst hier lesen, dann in
> die passende Seite eintauchen.
> Zuletzt aktualisiert: 2026-09-18 | Seiten: 27

**Siehe [[SCHEMA.md]]** für Konventionen, Tag-Taxonomie und das Verhältnis
dieses Wikis zu `CLAUDE.md`/`docs/api/`/`docs/reference/` (die bleiben die
primäre, von Claude-Instanzen gepflegte Doku — dieses Wiki synthetisiert
darüber, mit Fokus auf **Versionsgeschichte der Regeln** und **Querverweise**).

## ⭐ Einstiegspunkte für „was hat sich geändert"

- **[[comparisons/regelwerk-excel-vs-aktuell]]** — die Antwort auf Marks
  Anliegen: was hat sich seit der Excel-Transkription (Version 1) im
  Regelwerk alles weiterentwickelt, mit Datum und Grund
- **[[comparisons/veraltete-docs-vs-code]]** — zweiter, ungeklärter Fund:
  `docs/api/personen.md`/`entitaeten.md` beschreiben ein anderes System als
  der echte Code

## Konzepte — Regeln (mit Entwicklungsgeschichte)

| Seite | Zusammenfassung |
|---|---|
| [[concepts/wuerfelsystem]] | W10-Pool, 6-10 Erfolg, unverändert seit Excel |
| [[concepts/attribute-und-fertigkeiten]] | 9 Attribute/30 Fertigkeiten, Gesundheit 5→6 (10.09.), Schadensarten |
| [[concepts/charaktererschaffung]] | Rassenverteilung, Fertigkeitspakete, Freebees, Hintergründe (erfunden) |
| [[concepts/rassen]] | Vom Fixkatalog zum Baukasten (11.09.), gefundene 15er-Balance-Formel |
| [[concepts/magie-hexkraft]] | Arete→Hexkraft (10.09.), Sphären, Wilde Magie |
| [[concepts/neuroweaving-decking]] | Technomancer→Neuroweaver (10.09.), Verteidigung Fassung+Geistesschärfe (schon 29.08. vom Excel abgewichen) |
| [[concepts/kampf-und-initiative]] | Initiative, Treffen/Schaden, WebSocket noch nicht gebaut |
| [[concepts/ruestung-kaestchen-durchlass]] | Komplettes neues System (10.09.) — Kästchen+Durchlass statt flachem Bonus, am längsten diskutierte Regel im Projekt |
| [[concepts/cyberware-bioware]] | Preis→Willenskraftverlust, Rundungsregel (31.08.), Reflex-Booster |
| [[concepts/willenskraft]] | Verbrauch/Rückgewinn, Verbindung zu Magie/NeuroWeaving/Cyberware |
| [[concepts/drohnen-fahrzeuge]] | Riggen-Regel, Preisformel von Mark selbst als fraglich markiert (offen) |
| [[concepts/erfahrung-und-steigern]] | Komplett erfunden (nicht im Excel), WoD-artige Faktor-Formel |
| [[concepts/waehrung-und-preise]] | NuYen, Verweis auf alle Excel-Preistabellen, geplantes Shop-System |

## Entitäten — Architektur & Features

| Seite | Zusammenfassung |
|---|---|
| [[entities/neo4j-datenmodell]] | Node-/Beziehungstypen, TraitDef-Umbenennen-Fallstrick, 6-Schichten-Check |
| [[entities/architektur-drei-ebenen]] | Regelsystem→Kampagne→Ideenschmiede, fertig 12.09. |
| [[entities/mitteilungen-system]] | SL-Popups, kein Absender, WebSocket+Reconnect, Warnfarbe offen |
| [[entities/kontakte-messenger]] | Persona-5-Messenger, Stufe vs. chatOffen, Nachrichten als eigene Nodes |
| [[entities/ingame-wiki-feature]] | Das In-Game-Wiki-Feature (NICHT dieses Meta-Wiki!), Freigabe ohne Vererbung |
| [[entities/rassen-baukasten-feature]] | Technische Umsetzung des Rassen-Baukastens |
| [[entities/theming-system]] | Token-System, sechs Gruppen, Cytoscape-Canvas-Sonderfall |
| [[entities/ui-konzept-commlink]] | „Nie scrollen"-Prinzip, Fenstersystem, Navigation |
| [[entities/auth-und-rollen]] | GM/PLAYER, JWT-Cookie, Einladungscodes |
| [[entities/ki-integration]] | Gemini in der Ideenschmiede (erste Iteration), viele geplante Use-Cases |
| [[entities/tech-stack]] | FastAPI/Neo4j/React, lokaler Start, Windows-Stolpersteine |

## Vergleiche

| Seite | Zusammenfassung |
|---|---|
| [[comparisons/regelwerk-excel-vs-aktuell]] | Excel (Version 1) vs. heute — die zentrale Übersichtsseite |
| [[comparisons/veraltete-docs-vs-code]] | Zwei API-Docs mit altem Platzhalter-Attributsystem |

## Nicht in diesem Wiki dupliziert (bewusst nur verlinkt)

- `../../CLAUDE.md` — laufender Projektstand, Sync-Punkt zwischen Claude-Instanzen
- `../ENTWICKLUNGSHISTORIE.md` — vollständige Stolperstein-Liste + geprüfte Features
- `../api/*.md` — 10 Dateien, technische API-Referenz
- `../reference/Neotopia_*.md` + `INDEX.md` — vollständige Excel-Transkription
- `../regeln-neotopia.md` — die für die Tool-Umsetzung geglättete Regelfassung

## Noch nicht ingested (für künftige Sessions)

- `docs/phase-5-messenger.md` — nicht gelesen in diesem Durchgang
- `docs/produktvision-wiki.md` — nicht gelesen in diesem Durchgang
- `docs/entwuerfe/kaestchen-overflow.html` — Entwurf zum offenen Kästchen-Overflow-Problem
- `~/.claude/plans/gut-pnp-steht-f-r-temporal-waterfall.md` — laut CLAUDE.md
  Architektur & Roadmap, liegt aber außerhalb des Repos (Claude-Code-Plan-Ordner)
- Frontend-Code (`frontend/src/`) wurde nicht durchsucht, nur Backend
