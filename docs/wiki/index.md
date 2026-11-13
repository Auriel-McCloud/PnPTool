# PnPTool Wiki — Index

> Content-Katalog. Jede Seite mit Kurzbeschreibung. Zuerst hier lesen, dann in
> die passende Seite eintauchen.
> Zuletzt aktualisiert: 2026-11-10 | Seiten: 40 | Nebenfiguren (Personen ohne Bogen, eigenes Menü)

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
| [[concepts/attribute-und-fertigkeiten]] | 9 Attribute/30 Fertigkeiten, Gesundheit 5→6 (10.09.), Overflow-Grenze 10→12 (19.09.), Schadensarten; SL kann hängende Spezialisierungs-Slots löschen (24.10.); Critter als Vorlage markierbar, Kopieren übernimmt Bild/Bogen/Gegenstände (06.11.) |
| [[concepts/charaktererschaffung]] | Rassenverteilung, Fertigkeitspakete, Freebees, Hintergründe; Zusatzfertigkeiten (28.09.); Person-Schritt als Entwurf per Autosave (09.10.); Hintergrund-Baukasten entschieden 10.10.; × nimmt einen vergebenen Fertigkeiten-Slot auf einmal zurück (01.11.) |
| [[concepts/rassen]] | Vom Fixkatalog zum Baukasten (11.09.), gefundene 15er-Balance-Formel; Auswahlkarte mit Bild, Steckbrief listet Extras (24.10.); erster Gratis-Kauf auch „alle Typen“, nur einmal (24.10.). Battlemap-Größe: Rasse ist Vorlage, Checkbox an der Person entscheidet (06.11.) |
| [[concepts/magie-hexkraft]] | Arete→Hexkraft (10.09.), Sphären 5→6 (23.10.), Geister→Schattenwelten, Korrespondenz→Raum, Zeit→Chronurgie, Entropie→Schicksal (09.11.). Gedanken offen. Wilde Magie, Häretiker-Flavor (24.09.). |
| [[concepts/neuroweaving-decking]] | Technomancer→Neuroweaver (10.09.), 6 Skills (22.09.), Overclock; Kampfkarte schaltet beim Neuroweaver wie beim Decker zwischen Kampf und Cyberkampf (01.11.). Overclock ist dort eine Funktion mit Würfel und Willenskraft, seit 06.11. ohne Pool-Deckel (Rückschlag begrenzt von allein) und auch für den Decker im Matrix-Hot nutzbar. Deaktivieren teilweise umgesetzt (01.11.): Kampf-Fenster, Umbau-Feld, Kampfkarte zeigt Ausgeschaltetes. Gehacktes Deck zieht von allein nach. Neuroweaver-Hack: restliche Willenskraft ist das Kampf-ICE, Überschuss ist ungedeckelter Schlagschaden; Hot-Decker wählt schalten oder Schaden. Drohne ebenso: Wahl, nicht nur schalten; Fahrzeug bleibt beim Schalten. Überschrift „Würfeln“ ist weg, die Knöpfe bleiben (05.11.). Vierte Umbau-Option „Nicht hackbar“ (05.11.). Offen: Ki-Tama-Zeile, Automata als eigener Typ |
| [[concepts/kampf-und-initiative]] | Initiative, Treffen mit Ausrüstungsbonus, Waffen-Skill, Schaden, Parade-Bonus nur an der Waffe (31.10.). SL bekommt Booster- und Hot-Popups, wenn ein NPC dran ist (04.11.). Kampfmenü ohne die Zeilen Ansage von hinten, Schutz und Schaden, Würfeln (05.11.) — Pools, Waffen und der Umschalter bleiben. Klick auf die Initiative-Zahl trägt die Erfolge ein, auch wenn Charakter oder Drohne noch nicht in der Liste stehen (05.11.). Große Parieren-Kachel nimmt die Nahkampfwaffe, Nahkampf-Schaden zeigt Waffe+Körperkraft (06.11.). Reichweite an Nahkampf-Waffen: nur mittel/lang im Steckbrief (12.11.). Battlemap-Design 06.11. entschieden, nicht gebaut — siehe [[entities/battlemap]] |
| [[concepts/ruestung-kaestchen-durchlass]] | Kästchen+Schadensreduktion (18.09., höher=besser, abgelöst "Durchlass") — am längsten diskutierte Regel im Projekt |
| [[concepts/cyberware-bioware]] | Preis→Willenskraftverlust, Rundungsregel (31.08.), Reflex-Booster; unverbautes Chrom mit natürlicher Rüstung bleibt umlegbar bis zum Einsetzen (04.11.) |
| [[concepts/willenskraft]] | Verbrauch/Rückgewinn, Verbindung zu Magie/NeuroWeaving/Cyberware |
| [[concepts/drohnen-fahrzeuge]] | Drohne/Fahrzeug als Person-Knoten. Umbau schreibt Attributnamen aus, Punkte darunter (31.10.). Charakterblatt zeigt nur Fertigkeiten mit Punkten. Spieler setzt das Bild der eigenen Drohne (31.10.). Decker-Hot sitzt neben der Überschrift Cyberdeck, nicht neben der Runde (01.11.). Hot lässt sich nicht ausknipsen: beim nächsten Zug zuerst bleiben, Nein heißt keine Zusatzaktion (01.11.). Matrix-Hack an der Drohne: Wahl schalten oder Schlagschaden, Hot-Rigger nimmt die Hälfte (01.11.). Werkbank-Reparatur zeigt den neuen Gesundheitsstand sofort, ohne Seiten-Reload (04.11.). SL bekommt die Hot-Fragen, wenn ein NPC-Decker oder NPC-Rigger dran ist (04.11.). |
| [[concepts/augments-ausruestung]] | **Gebaut (29.10.2026):** Burgermenü "Werkbank" (Reparatur + Augments) — montierbare Boni (Zielfernrohr & Co.) für Waffe/Rüstung/Cyberdeck/Riggerkonsole/Drohne/Fahrzeug, `upgradeSlots` 0-6, Maker/Handwerk-Probe zum Montieren/Demontieren, Patzer macht defekt, Reparatur wie Rüstung/Drohne. Ki-Tama-Beschwörung einmal pro Kampf gebaut (01.11.): Fehlwurf frei, Patzer verbraucht den Ruf. Verbrauchte Kachel verschwindet statt Hinweistext. Upgrade-Material hat im Umbauen Initiative und Zusatzaktionen wie Chrom; Besitz hat ein Menü „Passt an“ (01.11.). I.C.E.-Feld am Upgrade, Träger sind Commlink, Cyberdeck, Riggerkonsole und Drohne/Fahrzeug (05.11.). Offen: Ki-Tamas und Rüstung von Ifrit und Shiva, Blizzard/Inferno/Feuer/Eis |
| [[concepts/erfahrung-und-steigern]] | Komplett erfunden (nicht im Excel), WoD-artige Faktor-Formel; Plan-Autosteigerung für NPCs entschieden 10.10. (nicht Resteverwertung) |
| [[concepts/waehrung-und-preise]] | NuYen, Verweis auf alle Excel-Preistabellen, Shop-System-Kern gebaut (22.09.), KI-Sortiment-Vorschlag für Händler (23.09.), Shop-Frontend Phase 1+2: physisch/digital, Rarity-Rahmen, Bestellungen, KI-Alltagsgegenstand-Erzeugung mit Waffen-Ausschluss (24.09.), Credstick gebaut (05.11.), Shop-Preis folgt live dem Gegenstand (05.11., Nachzug 06.11.: KI-Anlegen/Cache/Editor), Geld-Weitergabe noch offen |

## Entitäten — Architektur & Features

| Seite | Zusammenfassung |
|---|---|
| [[entities/neo4j-datenmodell]] | Node-/Beziehungstypen, TraitDef-Umbenennen-Fallstrick; VERBINDUNG seit 01.10. per PATCH (Typ/Sichtbarkeit); Rechtsklick im Beziehungsgraphen öffnet Objekt oder Kante (23.10.); SpielerNotiz privat seit 02.10.; `_BOGEN_DEFAULTS` für Tutorial-Shop-Felder (10.10., Ideenschmiede). Offen (01.11.): Critter und NPCs kopieren für 0815-Mobs |
| [[entities/architektur-drei-ebenen]] | Regelsystem→Kampagne→Ideenschmiede, fertig 12.09. |
| [[entities/critter-pet]] | Tamagotchi-Pet an einem Critter, wandert als Overlay auf andere Spieler-Displays; Skizze 24.09., nachgeschärft 11.11. (Mushu-artiger Pixel-Drache, mehr Animationen). Teilweise umgesetzt 11.11.: Laufen/Wandern/Streicheln/Häufchen; Bärbel = fliegendes Buch als Gegenstand-Pet, liest Bibelverse im großen aufgeschlagenen Buch vor (12.11.), trifft den Drachen; Drache läuft auf Wolken nach oben und schüttelt Ruß ab (12.11.); Eis- und Blitzdrache als Farbvarianten mit eigenem Atem (12.11.); Ei/Baby, Futternapf (12.11.); vier größere Gestalten als chinesische Drachen und Einkringeln zum Schlafen (13.11.) |
| [[entities/mitteilungen-system]] | SL-Popups, kein Absender, WebSocket+Reconnect, Warnfarbe offen |
| [[entities/kontakte-messenger]] | Persona-5-Messenger, Stufe vs. chatOffen; leere Plätze als „Undefinierter Kontakt“ in derselben Liste (01.11.); Verlauf folgt chatOffen (07.11.); Spieler↔Spieler-Chat PC↔PC (07.11.), Gruppenchat PC+NPC gebaut (07.11.); befüllte Kontakt-Plätze werden Nebenfiguren, nur Mentoren volle NPCs (10.11.) |
| [[entities/nebenfiguren]] | Person ohne Bogen/Inventar (`istNebenfigur`), eigenes Burgermenü, kein Kampf; Rasse/Alter/Persönlichkeit/freie Fähigkeiten; Einbahnstraße „Zu NPC machen“ per Charakter-KI (10.11.); leere Kontakt-Plätze schon Nebenfigur, Ideenschmiede ✨ mit Anzahl + Verbindung (10.11.) |
| [[entities/ingame-wiki-feature]] | Das In-Game-Wiki-Feature (NICHT dieses Meta-Wiki!), Freigabe ohne Vererbung, Editor-Schriftgröße am Handy (20.09.) |
| [[entities/rassen-baukasten-feature]] | Technische Umsetzung des Rassen-Baukastens; Erstellung zeigt Bild auf der Karte und Extras im Steckbrief (24.10.); Gratis-Erstkauf-Option „alle Typen“ verbraucht das Feature nach einem Kauf (24.10.). Battlemap-Größe: Vorlage hier, Entscheidung an der Kachel (06.11.) |
| [[entities/theming-system]] | Token-System, sechs Gruppen, Cytoscape-Canvas-Sonderfall |
| [[entities/ui-konzept-commlink]] | Nie-scrollen-Prinzip, Fenstersystem, Navigation, Verwundungsanzeige (19.09.), Neonflackern (19.09., Ameisenkrieg wieder sichtbar 12.11.), Autosave Beschreibung/Notizen (27.09.), Burgermenü blättert per Pfeil statt Scrollbar (29.09.), ☰-Customizen in der Rail sichtbar (02.10.), Spieler-☰ unten im Burger (23.10.), Probenfenster zeigt Kurztext + Detail (31.10.), Spieler-Inventar: Knopf „Beschreibung“ im Gegenstandfenster rechts neben Name und Wert, Text nur im Readonly-Popup (12.11.) |
| [[entities/auth-und-rollen]] | GM/PLAYER, JWT-Cookie, Einladungscodes, Ersteinstieg (23.09.). Vorgefertigte Signifikanz: Normal / hervorheben (Magenta) / Wichtig (Gold), Sortierung wichtig zuerst (01.11.). Häretiker-Anzeige in der Auswahl zeigt „Häretiker“, `weg` bleibt MAGIER (01.11.) |
| [[entities/ki-integration]] | Gemini in der Ideenschmiede; ✨ KI + Beratung legen seit 01.10. Charakter/Story/Gegenstand/Ort/Event/Fraktion/Verbindung an. Prüfung, Auto-Verknüpfung, Bild, Wiki-Import, Beratungschat (30.09.), Jev geparkt. Charakter-Galerie wie bei Orten (10.10.) |
| [[entities/tech-stack]] | FastAPI/Neo4j/React, lokaler Start, Windows-Stolpersteine, `.env`-Secrets |
| [[entities/party-feature]] | Gruppen, aktive Party, wiederentdeckte Vision vom 28.08., Grundlage für Spotify; Party-interne Gegenstands-Weitergabe (26.09.) |
| [[entities/spotify-anbindung]] | Musik folgt aktiver Party, ein Konto fürs Tool, Spotify Connect statt fester Geräte-ID |
| [[entities/kampagnen-export-import]] | Komplette Kampagne als ZIP (24.09.); Weissliste 29.09. um Protokoll/Zusatzfertigkeiten/Shop nachgezogen; Nacht-Dump auf bebop (täglich 30 Tage, 1. im Monat 1 Jahr) |
| [[entities/gegenstand-transfer]] | Party-interne Gegenstands-Weitergabe via Verhandlungs-Popup gebaut (26.09.). Credstick gebaut (05.11.), Laden im Objekt und im Spieler-Fenster. Geld, NPC-Belohnung, Granate und „gleicher Ort“ noch offen. Heiltrank-Typfrage ersetzt, siehe [[entities/drogen]] |
| [[entities/drogen]] | Schlucken gebaut (04.11.). Umbauen: Wirkung oben, Nebenwirkung darunter. Schaden dort ist Schlag, tödlich, schwerheilbar auf den normalen Spuren (05.11.). Gift an jemand anderem im Kampf später. Im SL-Kampfmenü über „Inventar“ am Kampfbogen erreichbar (10.11.). |
| [[entities/ereignisprotokoll]] | Sitzungs-Log: Backend 27.09., Auto-Hooks + SL-Zeitleiste 29.09. Achievements nur Konzept |
| [[entities/achievements]] | **Gebaut (10.10.2026):** Backend-Modul + Frontend (SL-Verwaltung + Spieler-Popup, 🏆-Symbol). `einzigartig`-Häkchen trennt campaign-weit einmalige Titel von pro-Person wiederholbaren; mechanische Belohnung (EP oder Hintergrund, fest hinterlegt) — einziger Weg, Hintergründe nach der Erstellung zu steigern; 14 AUTO-Trigger inkl. parametrisierbarem Ziel-Gegenstand (Isotop/Kristalle), Endboss, Critter/Drohne, erste Sitzung überlebt; Auto-Erkennung live aus dem Ereignisprotokoll + spontane manuelle Vergabe; KI-Text bezogen auf auslösenden Log-Eintrag+Kontext. Browser-Klicktest offen |
| [[entities/zusatzfertigkeiten]] | Campaign-gebundener Katalog optionaler Fertigkeiten. SL-Tabelle + KI. In der Erstellung: Button im Fertigkeiten-Popup öffnet Auswahl, danach normale Punktzeilen im Raster (Paket) und Freebees; LevelUp eigener Popup mit EP |
| [[entities/hintergrund-baukasten-feature]] | **Teilweise (10.10.2026):** KI durch `pruefe()`; narrativer SL-Katalog (Seed ohne Mentor/Kontakte); Mentor-Pipeline/Blatt-Button noch offen |
| [[entities/spieler-lexikon]] | Burgermenü „Lexikon" (Welt/Fauna/Flora/Objekte), entschieden-nicht-umgesetzt (09.10.): automatische `ENTDECKT`-Kante per Erreichbarkeits-Hook (max. 7 Hops, bricht an SL-geheimen Kanten ab) schaltet nur Existenz frei, `sichtbarkeit` weiter die Beschreibung; `zeigeInGraph`→`storyRelevant` für MacGuffin-Objekte; Favoriten, Notizen pro Objekt |
| [[entities/ring-raetsel]] | Burgermenü „Rätsel“: Modus Leicht (acht Räume) oder Mittel (zwei Ebenen nebeneinander, abwechselnd Ebene/Drehen), freie SL-Markierung pro Feld, Lage der Gruppe extra, Spieler sehen nach Freigabe nur zu ohne Lösungshinweise (03.11.) |
| [[entities/battlemap]] | Hex-Kampfkarte. Party-Hex blau, Gegner magenta. Raster füllt Ecken. Fog of War optional in den Einstellungen, Standard aus (06.11.2026). Matrix-Navigation pingt die Kartenerinnerung, Hot gibt dem Decker Live-Sicht wie die SL (06.11.2026). 90°-Dreh-Button fürs Tablet-Hochkant, SL und Spieler, rein lokal pro Gerät (07.11.2026). Ansicht schwenkt per Ziehen auf der Karte, „Grid schieben“ nur SL; großer Token füllt drei Felder mit Blick-Ring drumherum (08.11.2026). ALT-Tokens bleiben drei Kampfrunden sichtbar, auch hinter Wänden und nach Bewegung (09.11.2026) |

## Vergleiche

| Seite | Zusammenfassung |
|---|---|
| [[comparisons/regelwerk-excel-vs-aktuell]] | Excel (Version 1) vs. heute — die zentrale Übersichtsseite |
| [[comparisons/veraltete-docs-vs-code]] | Zwei API-Docs mit altem Platzhalter-Attributsystem |

## Nicht in diesem Wiki dupliziert (bewusst nur verlinkt)

- `../../CLAUDE.md` — laufender Projektstand, Sync-Punkt zwischen Claude-Instanzen
- `../ENTWICKLUNGSHISTORIE.md` — vollständige Stolperstein-Liste + geprüfte Features
- `../api/*.md` — 11 Dateien, technische API-Referenz
- `../reference/Neotopia_*.md` + `INDEX.md` — vollständige Excel-Transkription
- `../regeln-neotopia.md` — die für die Tool-Umsetzung geglättete Regelfassung

## Noch nicht ingested (für künftige Sessions)

- `docs/phase-5-messenger.md` — nicht gelesen in diesem Durchgang
- `docs/produktvision-wiki.md` — nicht gelesen in diesem Durchgang
- `docs/entwuerfe/kaestchen-overflow.html` — Entwurf zum offenen Kästchen-Overflow-Problem
- `~/.claude/plans/gut-pnp-steht-f-r-temporal-waterfall.md` — laut CLAUDE.md
  Architektur & Roadmap, liegt aber außerhalb des Repos (Claude-Code-Plan-Ordner)
- Frontend-Code (`frontend/src/`) wurde nicht durchsucht, nur Backend
