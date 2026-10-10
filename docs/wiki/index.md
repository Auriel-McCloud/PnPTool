# PnPTool Wiki — Index

> Content-Katalog. Jede Seite mit Kurzbeschreibung. Zuerst hier lesen, dann in
> die passende Seite eintauchen.
> Zuletzt aktualisiert: 2026-10-10 | Seiten: 36

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
| [[concepts/attribute-und-fertigkeiten]] | 9 Attribute/30 Fertigkeiten, Gesundheit 5→6 (10.09.), Overflow-Grenze 10→12 (19.09.), Schadensarten |
| [[concepts/charaktererschaffung]] | Rassenverteilung, Fertigkeitspakete, Freebees, Hintergründe; Zusatzfertigkeiten (28.09.); Person-Schritt als Entwurf per Autosave (09.10.); Hintergrund-Baukasten entschieden 10.10. |
| [[concepts/rassen]] | Vom Fixkatalog zum Baukasten (11.09.), gefundene 15er-Balance-Formel |
| [[concepts/magie-hexkraft]] | Arete→Hexkraft (10.09.), Sphären, Wilde Magie, Häretiker-Flavor (24.09.) |
| [[concepts/neuroweaving-decking]] | Technomancer→Neuroweaver (10.09.), Erweiterung auf 6 Skills (22.09.), Overclock statt Wilde Magie, Pool-Deckel 10→12 |
| [[concepts/kampf-und-initiative]] | Initiative, Treffen/Schaden, WebSocket noch nicht gebaut |
| [[concepts/ruestung-kaestchen-durchlass]] | Kästchen+Schadensreduktion (18.09., höher=besser, abgelöst "Durchlass") — am längsten diskutierte Regel im Projekt |
| [[concepts/cyberware-bioware]] | Preis→Willenskraftverlust, Rundungsregel (31.08.), Reflex-Booster |
| [[concepts/willenskraft]] | Verbrauch/Rückgewinn, Verbindung zu Magie/NeuroWeaving/Cyberware |
| [[concepts/drohnen-fahrzeuge]] | Riggen-Regel, Preisformel von Mark selbst als fraglich markiert (offen) |
| [[concepts/erfahrung-und-steigern]] | Komplett erfunden (nicht im Excel), WoD-artige Faktor-Formel; Plan-Autosteigerung für NPCs entschieden 10.10. (nicht Resteverwertung) |
| [[concepts/waehrung-und-preise]] | NuYen, Verweis auf alle Excel-Preistabellen, Shop-System-Kern gebaut (22.09.), KI-Sortiment-Vorschlag für Händler (23.09.), Shop-Frontend Phase 1+2: physisch/digital, Rarity-Rahmen, Bestellungen, KI-Alltagsgegenstand-Erzeugung mit Waffen-Ausschluss (24.09.), Geld-Weitergabe/Credstick geplant (26.09.) |

## Entitäten — Architektur & Features

| Seite | Zusammenfassung |
|---|---|
| [[entities/neo4j-datenmodell]] | Node-/Beziehungstypen, TraitDef-Umbenennen-Fallstrick; VERBINDUNG seit 01.10. per PATCH (Typ/Sichtbarkeit); SpielerNotiz privat seit 02.10.; `_BOGEN_DEFAULTS` für Tutorial-Shop-Felder (10.10., Ideenschmiede) |
| [[entities/architektur-drei-ebenen]] | Regelsystem→Kampagne→Ideenschmiede, fertig 12.09. |
| [[entities/mitteilungen-system]] | SL-Popups, kein Absender, WebSocket+Reconnect, Warnfarbe offen |
| [[entities/kontakte-messenger]] | Persona-5-Messenger, Stufe vs. chatOffen, Nachrichten als eigene Nodes |
| [[entities/ingame-wiki-feature]] | Das In-Game-Wiki-Feature (NICHT dieses Meta-Wiki!), Freigabe ohne Vererbung, Editor-Schriftgröße am Handy (20.09.) |
| [[entities/rassen-baukasten-feature]] | Technische Umsetzung des Rassen-Baukastens |
| [[entities/theming-system]] | Token-System, sechs Gruppen, Cytoscape-Canvas-Sonderfall |
| [[entities/ui-konzept-commlink]] | Nie-scrollen-Prinzip, Fenstersystem, Navigation, Verwundungsanzeige (19.09.), Neonflackern (19.09.), Autosave Beschreibung/Notizen (27.09.), Burgermenü blättert per Pfeil statt Scrollbar (29.09.), ☰-Customizen in der Rail sichtbar (02.10.) |
| [[entities/auth-und-rollen]] | GM/PLAYER, JWT-Cookie, Einladungscodes, Ersteinstieg für neue Spieler ohne Charakter (23.09.) |
| [[entities/ki-integration]] | Gemini in der Ideenschmiede; ✨ KI + Beratung legen seit 01.10. Charakter/Story/Gegenstand/Ort/Event/Fraktion/Verbindung an. Prüfung, Auto-Verknüpfung, Bild, Wiki-Import, Beratungschat (30.09.), Jev geparkt. Charakter-Galerie wie bei Orten (10.10.) |
| [[entities/tech-stack]] | FastAPI/Neo4j/React, lokaler Start, Windows-Stolpersteine, `.env`-Secrets |
| [[entities/party-feature]] | Gruppen, aktive Party, wiederentdeckte Vision vom 28.08., Grundlage für Spotify; Party-interne Gegenstands-Weitergabe (26.09.) |
| [[entities/spotify-anbindung]] | Musik folgt aktiver Party, ein Konto fürs Tool, Spotify Connect statt fester Geräte-ID |
| [[entities/kampagnen-export-import]] | Komplette Kampagne als ZIP (24.09.); Weissliste 29.09. um Protokoll/Zusatzfertigkeiten/Shop nachgezogen; Nacht-Dump auf bebop (täglich 30 Tage, 1. im Monat 1 Jahr) |
| [[entities/gegenstand-transfer]] | Party-interne Gegenstands-Weitergabe via Verhandlungs-Popup gebaut (26.09.); Geld, NPC-Belohnung, Credstick/Heiltrank/Granate und „gleicher Ort“ noch offen |
| [[entities/ereignisprotokoll]] | Sitzungs-Log: Backend 27.09., Auto-Hooks + SL-Zeitleiste 29.09. Achievements nur Konzept |
| [[entities/achievements]] | **Gebaut (10.10.2026):** Backend-Modul + Frontend (SL-Verwaltung + Spieler-Popup, 🏆-Symbol). `einzigartig`-Häkchen trennt campaign-weit einmalige Titel von pro-Person wiederholbaren; mechanische Belohnung (EP oder Hintergrund, fest hinterlegt) — einziger Weg, Hintergründe nach der Erstellung zu steigern; 14 AUTO-Trigger inkl. parametrisierbarem Ziel-Gegenstand (Isotop/Kristalle), Endboss, Critter/Drohne, erste Sitzung überlebt; Auto-Erkennung live aus dem Ereignisprotokoll + spontane manuelle Vergabe; KI-Text bezogen auf auslösenden Log-Eintrag+Kontext. Browser-Klicktest offen |
| [[entities/zusatzfertigkeiten]] | Campaign-gebundener Katalog optionaler Fertigkeiten. SL-Tabelle + KI. In der Erstellung: Button im Fertigkeiten-Popup öffnet Auswahl, danach normale Punktzeilen im Raster (Paket) und Freebees; LevelUp eigener Popup mit EP |
| [[entities/hintergrund-baukasten-feature]] | **Teilweise (10.10.2026):** KI durch `pruefe()`; narrativer SL-Katalog (Seed ohne Mentor/Kontakte); Mentor-Pipeline/Blatt-Button noch offen |
| [[entities/spieler-lexikon]] | Burgermenü „Lexikon" (Welt/Fauna/Flora/Objekte), entschieden-nicht-umgesetzt (09.10.): automatische `ENTDECKT`-Kante per Erreichbarkeits-Hook (max. 7 Hops, bricht an SL-geheimen Kanten ab) schaltet nur Existenz frei, `sichtbarkeit` weiter die Beschreibung; `zeigeInGraph`→`storyRelevant` für MacGuffin-Objekte; Favoriten, Notizen pro Objekt |

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
