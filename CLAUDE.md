# PnPTool — Projektgedächtnis für Claude

Diese Datei wird von Claude Code automatisch geladen. Sie ist die Quelle der Wahrheit für den Projektstand — bei jeder größeren Änderung aktualisieren. **Bleibt bewusst schlank:** Details wandern nach `docs/api/` bzw. ins Wiki, nicht hier hinein.

## Backlog: Mark denkt noch nach (nicht einfach lostbauen)

- **Offene Popups sollen den Mobil-Reload überstehen** (01.10.2026): Nach
  dem Bereich-Fix (siehe unten) landet man zwar im richtigen Bereich, aber
  ein offenes Popup (Detail-Fenster, Inventar-Fach, Beratung, ...) ist nach
  dem erzwungenen Reload trotzdem wieder zu — mobile Browser/PWAs werfen
  Tabs im Hintergrund aus dem Speicher (OS-Verhalten, nicht verhinderbar).
  Technisch lösbar, aber NICHT mit einem einzigen generischen Mechanismus
  wie beim Bereich: jedes Popup ist State + oft eine ID (z.B. "NPC-Detail
  für Person X", ein ganzer Fach-Stapel im Inventar) — jedes bräuchte
  eigene Wiederherstellungs-Logik nach dem Neuladen der Daten.
  Mark will erst am Spieltisch beobachten, **welche Popups seine Spieler**
  tatsächlich oft offen haben, wenn das Handy gesperrt wird (Vermutung:
  Inventar-Fach oder Charakter-Detail, nicht Einstellungen/Verhandlung),
  bevor gezielt für die 1-2 wichtigsten gebaut wird — lohnt sich nicht für
  alle ~15 Popups im Tool. **Nicht von selbst anfangen, erst wenn Mark
  sagt, welche Popups es betreffen soll.**

- **Zweiter SL-Tisch / Kampagnen teilen** (02.10.2026, nur notiert):
  Richtung 1 — eigener SL, eigene Welt, nicht Marks NeotopiA. Datenmodell
  kann das schon (`GMUser -[:OWNS]-> Campaign`). Offen, nicht bauen:
  Kampagnen **nicht für alle sichtbar** (Liste/Sichtbarkeit); Kampagne in
  Status **unbespielt** ablegen, damit ein anderer SL sie spielen kann
  (Vorlage/Übernahme, Datenmodell offen). Echter Multi-User-Knackpunkt
  ist **Spotify**: Wiedergabe hängt an einem Konto und kommt sonst immer
  auf Marks Gerät. Rest der Isolation (Kampagne, Uploads, Sichtbarkeit)
  ist App-Filter, reicht für einen vertrauten zweiten Tisch. **Nicht
  von selbst anfangen.**

## Offen: Was Mark selbst testen muss

Neueste zuerst. Einmal am Spieltisch/Dev-Server gegengeprüft → hier streichen.

- **Commlink-/Cyberdeck-Anzeige + Reflex-Booster neu** (10.10.2026):
  `tsc -b` sauber (lokal + im Docker-Build auf bebop verifiziert), Backend-
  Import geprüft. **Nie im Browser angeklickt.** Commlink zeigt jetzt I.C.E.
  (Cyberwall), Cyberdeck alle 6 NeuroWeaving-Bonuswerte (B/S/D/K/Electronic
  Warfare/Matrix-Navigation) — in Übersicht UND Bearbeiten-Bereich des
  Gegenstand-Formulars (SL-Edit UND Spieler-Kachel) sowie im kompakten
  Kachel-Steckbrief (`items/steckbrief.ts`, parallel von Chibi gebaut).
  3 Reflex-Booster-Stufen (Günstig/Militärisch/Illegaler Prototyp) als
  Entwürfe importiert — beim ersten Tabellen-Import übersehen, standen im
  Excel unter einem eigenen Abschnitt. Initiative-Bonus und Zusatzaktionen
  waren danach zwar am Gegenstand gesetzt, aber im Formular weder sichtbar
  noch editierbar (Mark: "wir haben so viel Aufwand betrieben sie mechanisch
  einzubauen, wir sollten auch anzeigen was sie können") — jetzt eigenes
  Eingabefeld im Chrom-Bereich plus Steckbrief-Zeile in beiden Ansichten.
  Bitte einen Reflex-Booster aus der Ideenschmiede freigeben, am Charakter
  als Cyberware einsetzen, im Formular Initiative/Zusatzaktionen gegenprüfen
  und im Kampfmodus die tatsächliche Verschiebung testen (Mechanik selbst
  ist alt, nur Items + Anzeige fehlten).

- **KI-Shop-Anlegen: Fallback + Preis-Richtwerte neu** (10.10.2026):
  `pytest`/Backend-Import grün, live auf bebop gegen die echte Mistral-API
  verifiziert (Gemini war zum Testzeitpunkt 503 überlastet, Mistral übernahm
  automatisch, Preis traf den Richtwert). **Nie über den echten Browser-Klick
  getestet**, nur direkt per Python gegen die Repository-Funktion. Bitte im
  Tutorial-Shop (oder einem anderen Laden) „Mit KI anlegen“ klicken und
  prüfen, dass tatsächlich etwas passiert (auch wenn Gemini gerade überlastet
  sein sollte) und der Preis zur Kategorie passt.

- **Achievements neu gebaut** (siehe „Zuletzt gebaut" 10.10.2026): Backend
  + Frontend komplett, eigene Tests grün, `tsc -b` sauber, Backend startet
  fehlerfrei gegen Neo4j. **Nie im Browser angeklickt.** Mark testet bewusst
  zuerst auf Andromeda (Test-Kampagne), nicht auf bebop — Achievements sind
  komplett pro `campaignId` gescoped, ein "First Kill" auf Andromeda hat
  keinerlei Berührung mit der echten Kampagne. Falls doch mal versehentlich
  auf bebop ausgelöst: Verleihungen folgen dem Papierkorb-Prinzip (kein
  Hard-Delete) — Löschen über die SL-Verwaltung macht das Achievement sofort
  wieder frei vergebbar, kein Backend-Eingriff nötig. Bitte am Spieltisch:
  🏆-Symbol in der Werkzeugleiste (SL + Spieler), ein manuelles Achievement
  anlegen und vergeben, ein AUTO-Achievement (z. B. CHARAKTER_ERSTELLT)
  anlegen und prüfen ob der Vorschlag erscheint, EP-/Hintergrund-Belohnung
  gegenprüfen.

- **Lebenspunkte-Grundwert pro Critter neu** (siehe „Zuletzt gebaut“
  10.10.2026): `pytest tests/test_bogen.py` (5 neue Fälle) grün, volle
  Backend-Suite nur die 8 vorbestehenden (unabhängigen) Fehlschläge,
  `tsc -b` sauber. **Nie im Browser angeklickt.** Bitte im Critter-Fenster
  einer Ratte den neuen Zahleneingabe „Lebenspunkte-Grundwert“ auf 1 setzen
  und im Charakterblatt prüfen, ob die Gesundheit auf 2 sinkt (1 Grundwert +
  1 Widerstandsfähigkeit), danach das Feld wieder leeren und prüfen, ob sie
  zum Standard (6 + Widerstandsfähigkeit) zurückspringt.

- **Vorgefertigte Charaktere + PC↔NPC-Umwandlung neu** (siehe „Zuletzt
  gebaut" 09.10.2026): `pytest` (511/511 der von dieser Änderung berührten
  Tests grün, echter E2E-Test gegen laufende Neo4j für Filter + beide
  Umwandlungsrichtungen + Migration), `tsc -b` sauber. **Nie im Browser
  angeklickt.** Bitte am Spieltisch: im PC-Detail-Popup eines vorgebauten
  Charakters die neue Checkbox „Vorgefertigter Charakter" setzen, prüfen ob
  er danach (und nur dann) im Ersteinstiegs-Fenster eines neuen
  Spieler-Accounts auftaucht; „⇄ Zu NPC machen" an einem PC und „⇄ Zu PC
  machen" an einem NPC ausprobieren, dabei gegenprüfen ob Inventar/
  Charakterbogen/Beziehungen wirklich erhalten bleiben.

- **Beziehungstyp-Konsistenz + „Beziehungen aus Beschreibungen"-Knopf neu**
  (siehe „Zuletzt gebaut" 03.10.2026): nie im Browser angeklickt, nur
  `pytest`/`tsc -b` geprüft. Bitte am Spieltisch: im Verbindungen-Bereich
  den neuen Knopf „✨ Beziehungen aus Beschreibungen" neben „+ Neue
  Verbindung" klicken, prüfen ob aus Beschreibung/Notizen bestehender
  NPCs/Orte/Fraktionen sinnvolle neue Verbindungen vorgeschlagen werden und
  ob vorgeschlagene Beziehungstypen zu bereits verwendeten passen (z.B.
  „kennt" statt einer neuen Formulierung, wenn „kennt" schon existiert).


- **Lesegröße-Zoom neu** (siehe „Zuletzt gebaut" 03.10.2026 — Zoom in
  Beschreibungs-/Notizenboxen): nie im Browser angeklickt, nur `tsc -b`.
  Bitte eine Beschreibung öffnen, A+/A− in der Werkzeugleiste (Editor) bzw.
  über dem Text (Leseansicht) antippen — Schrift sollte in 5 Stufen
  (100–175%) wachsen/schrumpfen, Einstellung nach Reload erhalten bleiben
  und beim zweiten gleichzeitig offenen Popup mitziehen.
- **KI-Entwürfe mit Notizen neu** (siehe „Zuletzt gebaut" 03.10.2026 —
  KI-Entwürfe befüllen jetzt auch die Notizen): nie im Browser angeklickt,
  nur pytest. Bitte eine Beratung führen, ruhig Details reinwerfen, dann
  „Entwurf anlegen" klicken und im angelegten Entwurf das Notizen-Feld
  prüfen — sollte jetzt die Details aus dem Gespräch enthalten, während die
  Beschreibung weiterhin knapp bleibt. Gilt auch für den ✨-KI-Knopf direkt.
- **Sticky-Werkzeugleiste neu** (siehe „Zuletzt gebaut" 01.10.2026 —
  Editor-Werkzeugleiste bleibt beim Scrollen sichtbar): nie im Browser
  angeklickt. Bitte bei einer langen Beschreibung/Notiz prüfen, dass
  „🔒 SL-geheim" & Co. beim Scrollen oben kleben bleiben statt mit
  hochzuscrollen.

- **KI-Provider-Umschalter neu** (siehe „Zuletzt gebaut" 01.10.2026 —
  Kampagnen-Textprovider + Beratungs-Override): Tests (`test_ki_beratung.py`,
  `test_ki_idee_typen.py`, voller Backend-Suite) und `tsc -b`/`vite build`
  grün, aber nie im Browser angeklickt. Bitte Einstellungen-Popup → Abschnitt
  „KI" öffnen, Mistral wählen, eine Ideenschmiede-Generierung auslösen und
  prüfen ob sie merklich anders klingt; danach im Beratungs-Popup den
  kleinen Dropdown neben „+ Neu" testen (sollte die Kampagnen-Einstellung
  für eine Nachricht übersteuern können, ohne sie zu verändern).
- **Verbindungen-Bereich neu** (siehe „Zuletzt gebaut" 01.10.2026 —
  durchsuchbare Auswahl + Suchleiste): nie im Browser angeklickt, nur
  `tsc -b`/`vite build` geprüft. Bitte am Spieltisch den Verbindungen-Punkt
  öffnen und das neue „+ Neue Verbindung"-Popup samt beiden Suchfeldern
  sowie die Suchleiste über der Liste ausprobieren.

Diese Punkte wurden von Agenten gebaut, aber mangels laufendem Frontend-Dev-Server
bzw. GPU-Hardware nur eingeschränkt oder gar nicht verifiziert. Bitte am
Spieltisch/Dev-Server gegenprüfen, danach hier aus der Liste streichen:

- **Zusatzfertigkeiten** (28.09.2026, Abend-Stand — Button + Punktzeilen,
  live auf bebop als `2bf1adc`; siehe „Zuletzt gebaut“ und
  `docs/wiki/entities/zusatzfertigkeiten.md`): bitte hart neu laden, dann
  im Kampagnen-Menü Einträge anlegen (mit UND ohne KI). Charaktererstellung
  → Fertigkeiten-Popup: oben der Button **Zusatzfertigkeiten** öffnet die
  Katalogwahl; gewählte Skills erscheinen als normale Kreise im Raster
  (Paket-Slots, wie Diebeshandwerk). Freebees: nur die Gewählten, +1 aus
  dem Hauptpool. Charakterblatt: Eintrag auch bei rating 0. LevelUp:
  bisheriger "+ Zusatzfertigkeit"-Popup mit EP, unverändert.

- **Autosave für Beschreibung/Notizen** (27.09. + Fix 30.09., siehe „Zuletzt
  gebaut“): Reload-Bug (Popup zu/auf, Tab weg) ist im Code raus. Bitte am
  Spieltisch: in Beschreibung tippen, ~2 Sek. Pause — Fenster und Tab müssen
  bleiben, Text nach Reload noch da. Ort-Popup und Gegenstand-Fenster.
- **Gegenstands-Weitergabe innerhalb der Party** (`WeitergebenPopup.tsx`,
  `VerhandlungPopup.tsx` für `GEGENSTAND_WEITERGABE`, siehe „Zuletzt gebaut“
  unten und `docs/wiki/entities/gegenstand-transfer.md`): Backend-Import und
  `tsc -b` sauber, Zugriffsschutz-Whitelist ergänzt. **Nie im Browser
  angeklickt** — bitte als Spieler einen Gegenstand an ein Party-Mitglied
  anbieten und prüfen, ob das Annehmen/Ablehnen-Popup beim Empfänger kommt
  und der Besitz danach stimmt.

- **Shop-System komplett** (`frontend/src/haendler/`, siehe „Zuletzt gebaut“
  unten und `docs/api/haendler.md`): Übersicht, physisch/digital getrennte
  Shop-Seite, Seltenheitsrahmen, Verhandeln-Integration, Bestellungen,
  KI-Alltagsgegenstand-Erzeugung (Spieler fragt Verkäufer, KI schlägt Preis
  vor, SL-Popup entscheidet) und der SL-Sortiment-Editor (Ware
  hinzufügen/entfernen, Rabatt, Standort — `HaendlerBearbeiten.tsx`).
  Backend komplett per echtem E2E-Test gegen laufendes Backend + Neo4j +
  echten KI-Provider verifiziert (harmloser Wunsch UND Waffen-Ausschluss
  beide grün). **Frontend nie im Browser angeklickt**, nur `tsc -b`
  geprüft (`vite build` läuft, aber Optik/Bedienung ungetestet) —
  Seltenheitsrahmen-Effekte (Glitzern/Zacken/Wabern) sind reine
  Code-Vermutung, bitte am Spieltisch gegenprüfen.
- **Kampagnen-Export/Import** (`EinstellungenFenster.tsx`, Sektion
  „KAMPAGNE“, siehe „Zuletzt gebaut“ unten): Export-Knopf, Import-Upload.
  Backend-Logik komplett per echtem E2E-Testlauf gegen laufendes Backend +
  Neo4j verifiziert (Export → Import → alle Prüfungen bestanden). Nur die
  Frontend-Bedienung selbst ist ungetestet — nie im Browser angeklickt,
  nur `tsc -b` geprüft. Bitte einmal am Dev-Server exportieren und
  importieren, v.a. ob der Downloaddateiname stimmt und nach Import
  automatisch zur neuen Kampagne gewechselt wird.
- **Messenger-Mobil-Fixes** (`Messenger.tsx`/`messenger.css`, siehe „Zuletzt
  gebaut" unten): Hart-Scroll ans Ende, Tastatur-Sichtbarkeit via Visual
  Viewport API, dynamische Sprechblasen-Form — nur `tsc -b` geprüft, das
  Browser-Tool kann `localhost` nicht erreichen (Netzwerksperre), deshalb
  **kein DevTools-Mobil-Emulationstest möglich**, nur Code-Review. Bitte am
  echten Handy testen, v.a. ob der Composer bei geöffneter Tastatur wirklich
  sichtbar bleibt (`visualViewport`-Verhalten variiert je nach
  Android/iOS-Browser).
- **Wiki-Mobil-Drawer** (`WikiAnsicht.tsx`/`wiki.css`, siehe „Zuletzt gebaut"
  unten): Seitenbaum/Inhaltsverzeichnis als Slide-in mit Backdrop und
  Schließen-Knopf, Kachel-Raster der Ideenschmiede + Verweis-Auswähler mit
  größeren Touch-Zielen. Ebenfalls nur `tsc -b` geprüft, kein Browser-Test
  möglich (siehe oben).
- **KI-Bildgenerierung** (`KiBildPopup.tsx`): nie im Browser angeklickt, nur
  `tsc -b` geprüft. Popup öffnet sich an Person/Event/Ort/Fraktion/Gegenstand
  sowie am eigenen Spieler-Portrait. Cloud-Pfad (Gemini) UND lokaler Pfad
  (Fooocus) wurden je einmal echt getestet (siehe „Zuletzt gebaut") — die
  Optik/Bedienung im Popup selbst aber nicht.
- **Fooocus-Wrapper** (`C:\DEV\Fooocus\pnptool_server.py`): liegt außerhalb
  des Repos, kein Autostart. Muss manuell gestartet werden
  (`cd C:\DEV\Fooocus && .venv\Scripts\python.exe pnptool_server.py`), sonst
  schlägt der „lokal"-Provider im Popup fehl. Cloud-Provider funktioniert
  immer, auch ohne das.
- **Wiki-Import** (`WikiImportPopup.tsx`, Knopf „⇪✨" neben „+ Neue Seite" in
  der Wiki-Ansicht): nie im Browser angeklickt, nur `tsc -b` geprüft und ein
  Backend-only-E2E-Test (5 verschachtelte Entwürfe, Auto-Verknüpfung lief).
  Optik/Bedienung im Popup selbst ungetestet.
  - **PDF-Import ungetestet** — nur `.docx` real durchgespielt. PDFs liefern
    keine Formatvorlagen, die automatische Kapitel-Gliederung könnte deutlich
    schwächer ausfallen als bei Word-Dateien.
  - **60.000-Zeichen-Obergrenze** pro Dokument ist eine Schätzung, kein
    empirisch ermittelter Wert — bei Bedarf nachjustieren, falls größere
    Dokumente gebraucht werden oder die Grenze zu früh/spät greift.
- **SL-Beratungschat** (`BeratungPopup.tsx`, Knopf ⌬ Beratung in der
  Ideenschmiede): nie im Browser angeklickt, nur `tsc -b` + pytest +
  OpenAPI. Bitte ein Gespräch führen, prüfen dass ✨ KI unangetastet bleibt,
  und einmal „Entwurf anlegen“ — Kachel muss als Entwurf landen, nächster
  Chat darf sie nicht als Kanon kennen. Backend-Neustart nötig (Migration
  `007_ki_beratung.cypher`).
- **🔍-Prüfen-Knopf im RichTextEditor** (Personen/Orte/Events/Fraktionen/
  Gegenstände/Begleiter): nie im Browser angeklickt, nur `tsc -b` und
  Backend-Import geprüft. Siehe „Zuletzt gebaut" unten.
- **Auto-Verknüpfung: Sweep + Freitext-UI** (`app/ki/auto_verknuepfung.py` +
  neue Frontend-Popups, siehe „Zuletzt gebaut" unten): Backend per echtem
  E2E-Test gegen laufendes Backend + Neo4j verifiziert. Frontend (Sweep-
  Knopf in den Kampagnen-Einstellungen, ⧉✨-Knopf im `RichTextEditor`/
  Ideenschmiede) nie im Browser angeklickt, nur `tsc -b` und
  `vite build` geprüft.
- **Rüstungs-Reparatur-UI** (`RuestungReparatur.tsx` im Bearbeiten-Fenster
  einer Rüstung, `VerhandlungPopup.tsx` beim Spieler): nie im Browser
  angeklickt, nur `tsc -b` geprüft. Die Backend-Logik dahinter (Würfe,
  Materialverbrauch, Preisformel, Deckel, Annehmen/Ablehnen) wurde per
  echtem End-to-End-Skript gegen laufendes Backend + Neo4j durchgespielt
  und ist verifiziert — offen ist nur die Optik/Bedienung der beiden neuen
  Popups selbst (Layout, ob der Commlink-Stil passt, ob das Verhandlungs-
  Popup beim Spieler zuverlässig aufpoppt). Siehe „Zuletzt gebaut“ unten.
- **Häretiker-Flavor-Option** (Charaktererstellung, Charakterblatt,
  Kampfkarte, Probenrechner, Level-Up), siehe „Zuletzt gebaut“ unten und
  CLAUDE.md Punkt 14: Backend + Frontend komplett per echtem
  Backend-only-E2E-Test gegen laufendes Backend + Neo4j verifiziert
  (Häretiker-Weg-Karte, Katalog-Identität, Tooltip-Texte). Optik/Bedienung
  im Browser nie angeklickt, nur `tsc -b` geprüft — bitte einmal bei der
  Charaktererstellung „Häretiker“ statt „Magier“ wählen und prüfen, ob die
  Sphären-Namen (Chronos, Ehecatl, …) und „Glauben“/„Blasphemie“ überall
  im UI stimmig auftauchen (Charakterblatt, Kampfkarte, Probenrechner,
  Level-Up, Willenskraft-Rückfrage).

## Vor jedem Task: Wiki befragen

**`docs/wiki/index.md` zuerst lesen**, bevor Regeln oder Architektur-Entscheidungen neu ausgedacht werden — v.a. bei Regelfragen, weil sich NeotopiA laufend weiterentwickelt und das Excel oft nicht mehr der aktuelle Stand ist (siehe `docs/wiki/comparisons/regelwerk-excel-vs-aktuell.md`). Das Wiki hält bereits entschiedene Fragen, offene Baustellen und die Versionsgeschichte fest — Ziel ist, dieselbe Entscheidung nicht zweimal zu treffen (oder zu widersprechen). **Nach jeder inhaltlichen Änderung die passende Wiki-Seite nachziehen**, nicht nur CLAUDE.md.

## Was ist PnPTool

WebApp für Mark's Pen-and-Paper-Rollenspielrunden, Homebrew-System **"NeotopiA"** (WoD-artige Attribute, Shadowrun-Cyberware/Rigging, Mage-Sphären, Cyberpunk-Setting). Referenz: `docs/reference/Neotopia.xlsx`.

**Zwei Nutzerrollen:**
- **Spielleiter (GM)** — plant Kampagnen als Beziehungsgraph, sendet Live-Popups
- **Spieler** — interaktive Charakterbögen, Messenger, empfängt Popups

**Wichtige Dokumentation:**
- `docs/wiki/index.md` — **Projekt-Wiki**: Regeln inkl. Versionsgeschichte, Architektur, offene Fragen (siehe oben — zuerst hier nachschlagen)
- `docs/ui-konzept.md` — Leitbild fürs UI ("Commlink")
- `docs/theming.md` — Alle Farben als Tokens in `frontend/src/theme/`
- `docs/api/` — **Ausführliche API-Dokumentation** (Endpoints, Schemas, Logik)
- `~/.claude/plans/gut-pnp-steht-f-r-temporal-waterfall.md` — Architektur & Roadmap

## Tech-Stack (entschieden)

- **Backend**: FastAPI, neo4j async driver, JWT in httpOnly-Cookie, bcrypt direkt
- **Datenbank**: Neo4j 5 in Docker
- **Frontend**: React 19 + TypeScript + Vite, Cytoscape.js direkt (kein Wrapper)
- **Deployment**: Lokal Windows-Dev (`npm run dev`); produktiv auf bebop unter `pnptool.aurielmc.cloud` (seit 25.09.2026), Frontend-Image nginx + `vite build` (seit 03.10.2026)

## Projektstruktur

```
C:\DEV\PnPTool\
├── CLAUDE.md                 ← diese Datei
├── docs/
│   ├── api/                  ← API-Dokumentation (NEU 07.09.2026)
│   │   ├── README.md         — Übersicht, Konventionen
│   │   ├── mitteilungen.md   — Popups, WebSocket, Ausblenden
│   │   ├── kontakte.md       — Messenger, Stufen, Alias
│   │   ├── kampf.md          — Runden, Initiative
│   │   ├── ruestung.md       — Kästchen + Schadensreduktion (NEU 10.09.2026, Reduktion statt Durchlass 18.09.2026)
│   │   ├── rassen.md         — Baukasten, Balance, Freigabe (NEU 11.09.2026)
│   │   ├── party.md          — Gruppen, Mitgliedschaft, aktive Party (NEU 18.09.2026)
│   │   ├── spotify.md        — Playlist an Ort/Event, Musik folgt aktiver Party (NEU 19.09.2026)
│   │   ├── personen.md       — PCs/NPCs, Attribute, Cyberware
│   │   ├── wiki.md           — Seiten, Freigaben
│   │   ├── entitaeten.md     — Orte, Gegenstände, Fraktionen
│   │   ├── kampagnen.md      — Themes
│   │   └── auth.md           — Login, JWT
│   ├── ui-konzept.md
│   ├── theming.md
│   └── phase-5-messenger.md
├── backend/
│   ├── .venv/
│   ├── app/
│   │   ├── main.py
│   │   ├── auth/, campaigns/, entities/, graph/
│   │   ├── mitteilungen/     — Popups, WebSocket, Ausblenden
│   │   ├── kontakte/         — Messenger
│   │   ├── kampf/            — Rundenkampf
│   │   ├── wiki/             — Weltenbau
│   │   ├── party/            — Gruppen, Mitgliedschaft, aktive Party
│   │   ├── spotify/          — Musik: OAuth, Playlist-Suche, Wiedergabe
│   │   └── items/, traits/   — Gegenstände, Charakterwerte
│   └── scripts/create_gm.py
└── frontend/
    └── src/
        ├── theme/            — ALLE Farben hier, nirgends sonst!
        ├── mitteilungen/     — Popups, Blitz-Symbol
        ├── kontakte/         — Messenger (Persona-5-Stil)
        ├── kampf/            — Kampfmodus
        └── ...
```

## Wie man lokal startet

```powershell
# 1. Neo4j (läuft meist schon)
docker compose up -d neo4j

# 2. Backend (OHNE --reload, siehe Stolpersteine)
cd C:\DEV\PnPTool\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001

# 3. Frontend
cd C:\DEV\PnPTool\frontend
npm run dev
```

**Test-Login:** `sl` / `test-passwort-123`
**Testkampagne:** `71dc452c-6c45-4a18-aec5-24815d161053`

## Stand der Umsetzung (10.09.2026)

| Phase | Status | Beschreibung |
|-------|--------|--------------|
| 1 | ✅ | Grundgerüst, Docker, Auth |
| 2 | ✅ | CRUD, Cytoscape-Graph |
| 3 | ✅ | Charakterblatt (Attribute, Kästchen/Box-Tracks) |
| 4 | ✅ | Spieler-Zugang, Sichtbarkeit |
| 5 | ✅ | **Mitteilungen + Messenger fertig** |
| Wiki | ✅ | Seitenbaum, Freigaben, TipTap-Editor |
| Themes | ✅ | Zwei Themes, Token-basiert |
| Rüstung | ✅ | Kästchen + Schadensreduktion + Reparatur (Selbst/Händler), siehe `docs/api/ruestung.md` |
| Party | ✅ | Gruppen, Mitgliedschaft, aktive Party, siehe `docs/api/party.md` |
| Spotify | ✅ | Playlist an Ort/Event, Musik folgt aktiver Party, siehe `docs/api/spotify.md` |

**Zuletzt gebaut (10.10.2026 — Schulden/Kredithai nach Kredit-Freebees):**
- **Was:** Kredit in der Erstellung erzeugt den Systemhintergrund Schulden.
  Bestehenden NPC mit `istKredithai` wiederverwenden, sonst Stub
  „Kredithai“ in der Ideenschmiede. Kanten `HAT_KREDITHAI`,
  `VERBINDUNG` typ Schuldet, `KENNT` mit zu. Rassen-Häkchen
  `kannKredithai`, NPC-Flag im Detail. KI-Füllung kommt mit der
  Kontakt-Pipeline — Erstellung wartet nicht auf LLM.
- **Dateien:** `backend/app/hintergruende/{kredithai,spawn,repository}.py`,
  `backend/app/traits/routes.py`, `frontend/src/rassen/RassenUebersicht.tsx`,
  `frontend/src/entities/NPCDetail.tsx`
- **Verifiziert:** `tests/test_kredithai.py`. Nicht im Browser geklickt.
- **Nicht dabei:** Mentor/Kontakte-Pipeline, Blatt-Button, Achievement-IDs.

**Zuletzt gebaut (10.10.2026 — Charakter-Bildergalerie):**
- **Was:** PC- und NPC-Detail zeigen dieselbe Galerie wie Orte und Fraktionen
  (mehrere Bilder, Primärbild = Anzeigebild auf der Kachel und im
  Spielerportrait). Ein weiteres Bild klaut das Anzeigebild nicht mehr.
  Spieler-Upload ersetzt nur das Primärbild, Extra-Bilder bleiben.
- **Dateien:** `frontend/src/entities/PCDetail.tsx`, `NPCDetail.tsx`,
  `BildGalerie.tsx`, `EntityManager.tsx`, `backend/app/entities/repository.py`,
  `backend/app/players/routes.py`, `backend/tests/test_charakter_galerie.py`
- **Verifiziert:** `tsc -b` und der Galerie-Test. Nicht im Browser geklickt.
- **Nicht dabei:** Gegenstände haben weiter nur ein Bild. Das eigene
  Portrait-Menü des Spielers zeigt weiter nur das Primärbild.

**Zuletzt gebaut (10.10.2026 — KI-Charakter folgt der Spieler-Erstellung):**
- **Was:** ✨-Charakter in der Ideenschmiede schreibt keine Roh-Ratings mehr.
  Dieselbe Prüfung wie ein Spieler: Rasse, Weg, Attribut-Zusatzpunkte nach
  Kontingent (höchstens 3, StartMax 4+Mod), genau ein Fertigkeitspaket,
  Hintergründe bis 5, Freebees inkl. Kredit/Eigenkapital innerhalb des
  Budgets — Geld und ein paar Details, nicht jedes Attribut auf 6.
  Regelwidrig einmal nachgebessert, sonst 422, kein Entwurf.
- **Dateien:** `backend/app/traits/erstellung.py`, `backend/app/ki/routes.py`,
  `backend/tests/test_ki_charakter_erstellung.py`, `backend/tests/test_ki_idee_typen.py`
- **Verifiziert:** die beiden Testdateien grün. Lokales uvicorn auf 8001
  lief noch ohne den Check (Start vor dem Commit, kein `--reload`) und
  wurde neu gestartet. Nicht im Browser geklickt.

**Zuletzt gebaut (10.10.2026 — Achievements: Backend + Frontend):**
- **Was:** Komplettes Feature aus dem Konzept (`docs/wiki/entities/
  achievements.md`) gebaut. 14 AUTO-Trigger (u. a. ERSTER_KILL, MOERDER,
  MEISTE_SCHADEN_GENOMMEN/VERTEILT, CHARAKTER_ERSTELLT, GEHEIMNISTRAEGER,
  parametrisierbares ERSTER_BESITZ_ZIEL/ERSTE_BESCHREIBUNG_ZIEL,
  ERSTER_CRITTER, ERSTE_DROHNE, ENDBOSS_BESIEGT, ERSTE_SITZUNG_UEBERLEBT),
  live aus dem Ereignisprotokoll berechnet, kein persistenter
  Vorschlags-Knoten. Mechanische Belohnung (EP oder Hintergrund, fest am
  Achievement hinterlegt) — einziger Weg, wie ein Hintergrund nach der
  Charaktererstellung noch steigt. `einzigartig`-Häkchen trennt
  campaign-weit einmalige Titel von pro-Person wiederholbaren, bei
  Rekord-Triggern wandert der Titel automatisch (alte Verleihung wird
  abgelöst, bleibt aber als Historie stehen). Spontane manuelle Vergabe
  mit optionalem ✨-KI-Text.
- **Dateien:** `backend/app/achievements/` (`schemas.py`, `repository.py`,
  `trigger.py`, `belohnung.py`, `routes.py`), Migration
  `012_achievements.cypher` (`Person.istEndboss`-Backfill),
  `entities/schemas.py`/`repository.py` (neues `istEndboss`-Feld).
  Frontend: `frontend/src/achievements/` — `AchievementVerwaltung.tsx`
  (SL: Katalog, Baukasten, Auto-Vorschläge, manuelle Vergabe),
  `MeineAchievements.tsx` (Spieler: Scroll-Popup, neuestes zuerst), beide
  über 🏆-Symbol in der Werkzeugleiste (`App.tsx`/`SpielerAnsicht.tsx`).
- **Verifiziert:** `backend/tests/test_achievements.py` (8 Tests, einzeln
  alle grün — derselbe vorbestehende Windows-Proactor-Loop-Flake wie bei
  `test_flora_fauna.py` trifft auch hier jeden zweiten Test im Verbund,
  Stolperstein 8/13), volle Backend-Suite sonst nur die vorbestehenden
  13 Fehlschläge, `tsc -b --force` sauber, Backend startet fehlerfrei gegen
  Neo4j (alle Routen im OpenAPI). **Nie im Browser angeklickt** — siehe
  „Offen" oben, Mark testet bewusst zuerst auf Andromeda.

**Zuletzt gebaut (10.10.2026 — Ideenschmiede: Entwürfe laden wieder):**
- **Was:** Live „Fehler beim Laden der Entwürfe“. Die Meldung kommt aus dem
  Catch-all in `IdeenschmiedeAnsicht`, nicht von `/entwuerfe` (die Route
  schluckt Fehler und liefert `[]`). Die Schmiede lädt parallel
  `GET /personen` — der knallte mit `ResponseValidationError` (28×
  `int_type`/`bool_type`, `input: None`) für `kapitalBasis`,
  `tutorialAusgegeben`, `gratisGegenstandErhalten`, `rassenFeatureGenutzt`.
- **Ursache:** Tutorial-Shop/Rassen-Features (10.10.) stehen in
  `PERSON_FIELDS` und `PersonResponse` als Pflicht-int/bool, fehlten aber in
  `_BOGEN_DEFAULTS`. Neo4j liefert für Altbestand `null`; Pydantic-Default
  greift nur, wenn der Key fehlt, nicht bei explizitem `None` (Stolperstein 9
  / 6-Schichten-Check, Schicht DEFAULTS).
- **Fix:** die vier Felder in `_BOGEN_DEFAULTS` (0 / False). Regression in
  `test_bogenfeld_defaults.py`, plus Netz dass jedes `int`/`bool` in
  `PersonResponse` aus `PERSON_FIELDS` einen Default hat (`ist*`-Konvention
  deckt `kapitalBasis`/`gratisGegenstandErhalten` nicht ab).
- **Verifiziert:** die fünf Defaults-Tests grün. Volle Suite: dieselben
  vorbestehenden Fehlschläge (asyncio/Neo4j-Stolperstein, Zugriffsschutz).
  **In der Schmiede gegenprüfen** — hart neu laden, Entwürfe müssen wieder
  erscheinen; NPCs/PCs ohne die neuen Properties ebenfalls.

**Zuletzt gebaut (09.10.2026 — Charaktererstellung speichert den Person-Schritt als Entwurf):**
- **Was:** Mark hat auf Andromeda Quills Konzept („der Held“) getippt, später
  am Handy denselben Assistenten weitergepflegt — der Text war weg. Ursache:
  der Person-Schritt (Name/Konzept/Alter/Ambition/Verlangen/Ziel) lebte nur
  im React-State. Autosave gab es für Wiki/Beschreibung, nicht für die
  Erstellung. Nginx-/Neo4j-Logs haben keinen Body, der Text war nicht
  rekonstruierbar.
- **Fix:** `useAutosave` schreibt dieselben Felder per bestehendem
  `PATCH .../personen/{id}/steckbrief` auf den Entwurfsknoten (1200ms +
  Flush beim Verlassen). Beim Öffnen hydratisiert der Assistent aus
  `GET .../bogen`. `SteckbriefUpdate` nimmt jetzt auch `name` und `alter`
  (`None` = unangetastet). Leerer Name wird nicht geschrieben. Der Rest
  des Assistenten (Weg/Rasse/Punkte) bleibt lokal bis „Charakter anlegen“.
  Keine Statusanzeige (still, wie Wiki-Autosave).
- **Verifiziert:** `pytest tests/test_steckbrief.py` 2/2, `tsc -b` sauber.
  Zugriffsschutz-Suite: dieselben vorbestehenden Fehlschläge, Steckbrief-
  Ausnahme unverändert. **Am Handy/PC gegenprüfen** — Person-Schritt
  tippen, Tab schließen oder Gerät wechseln, Assistent neu öffnen.

**Zuletzt gebaut (09.10.2026 — Android-Tastatur bleibt über dem Text):**
- **Was:** Mark: Tastatur klappt zu beim Markieren/Caret-Setzen/Autokorrektur,
  Text verschwindet unregelmäßig darunter. Der parallele Chat (Rahmen um
  langen Editor-Text, `097541f`) war ein anderes Thema und ist fertig.
- **Ursache:** PWA fullscreen ändert oft nur den Visual Viewport. Fenster
  blieben `94svh` hoch (unter der Tastatur), `body { overflow: hidden }`
  verhinderte das Nachschieben, und `.ProseMirror { overflow-y: auto }` plus
  `.fn-inhalt` war ein doppelter Scroll-Container — Android nimmt Caret-Tipp
  als Scroll und blendet die IME aus. Messenger hat bei jedem
  `visualViewport.scroll` `scrollIntoView` gemacht, das stiehlt den Fokus.
- **Fix:** `tastatur.ts` setzt `--vv-h`/`--vv-oben`/`--tastatur` und holt
  die Caret-Stelle nur ins Bild, wenn sie wirklich verdeckt ist (nicht bei
  laufender Markierung). Fenster folgt dem Visual Viewport. Viewport-Meta
  `interactive-widget=resizes-content`. Mobil kein intern scrollendes
  contenteditable (Desktop-Rahmen bleibt). Toolbar/Zoom `pointerdown`
  preventDefault. Messenger nutzt dieselben CSS-Vars.
- **Verifiziert:** `tsc --noEmit` sauber. **Am Handy gegenprüfen** — siehe
  „Offen“ oben.

**Zuletzt gebaut (10.10.2026 — Lebenspunkte-Grundwert pro Critter):**
- **Was:** Mark fiel auf, dass Critter (wie PCs/NPCs) standardmäßig 6
  Lebenspunkte haben — für eine Ratte oder einen Rattenschwarm viel zu
  viel, die sollen z.B. nur 2 haben (1 Grundwert + 1 durch
  Widerstandsfähigkeit). Nachträglich in den Optionen änderbar war der
  Wunsch, kein genereller Baukasten für alle Critter-Typen.
- **Neues Feld `Person.gesundheitGrundwert`** (analog `willenskraftBonus`):
  ersetzt für genau DIESE Person den bisher global fixen
  `GESUNDHEIT_GRUNDWERT = 6` (`traits/bogen.py`). Widerstandsfähigkeit zählt
  weiterhin unverändert obendrauf — nur der Sockel ist jetzt personenweise
  überschreibbar. Sentinel `-1` statt `None` als "kein Override": `update_
  node` filtert `None` beim PATCH generell als "Feld nicht anfassen" heraus
  (siehe Stolperstein beim Alias-Feld), ein Zurücksetzen auf den Standard
  wäre mit `None` als Default also unmöglich gewesen.
- **Frontend:** Zahleneingabe „Lebenspunkte-Grundwert“ im Critter-Fenster
  (`CritterFenster.tsx`, Abschnitt Verwaltung) — leer lassen = Standard (6),
  jede Zahl ≥0 überschreibt ihn. Kein eigener Katalog/Dropdown für
  Critter-Typen, bewusst ein einfaches Zahlenfeld.
- **Verifiziert:** `pytest tests/test_bogen.py` (5 neue Fälle: globaler
  Standard ohne Override, Sentinel -1 wie None behandelt, Rattenschwarm-
  Beispiel ergibt exakt 2, Grundwert 0 bleibt 0 und wird nicht ersetzt),
  volle Backend-Suite 539 passed (nur die 8 vorbestehenden, unabhängigen
  Fehlschläge — per `git stash`-Vergleich bestätigt identisch mit und ohne
  diese Änderung), `tsc -b` sauber. **Nie im Browser angeklickt** — siehe
  „Offen“ oben.
- Commit: `914b998`.

**Zuletzt gebaut (09.10.2026 — Vorgefertigte Charaktere als echtes Feld + PC↔NPC-Umwandlung):**
- **Was:** Mark wollte wissen, wie er einen Charakter als "vorgefertigt"
  markiert (bisher implizit: jeder abgeschlossene PC ohne Spieler), und kam
  dabei auf den Wunsch, nicht gewählte Vorgefertigte bei Bedarf zu einem
  NPC machen zu können (und umgekehrt) — ohne den Baustand zu verlieren.
  Teaser-Text für die Spieler-Auswahlkarte ist bewusst **kein** neues Feld:
  das bestehende `konzept` übernimmt diese Rolle, der Spieler passt es nach
  der Wahl selbst an (volle `description` geht ohnehin nie an die
  Auswahl-Route — Geheimnisse waren schon vorher sicher).
- **Neues Feld `Person.istVorgefertigt`** (analog `istHaendler`/`istKI`):
  SL setzt es per Checkbox im PC-Detail-Schnellzugriff. `GET
  /api/spieler/vorgefertigte` filtert jetzt zusätzlich darauf statt wie
  bisher automatisch jeden unclaimed PC zu zeigen. Migration
  `011_istvorgefertigt.cypher` markiert beim ersten Deploy alle
  Bestands-PCs, die die alte Regel erfüllt hätten, damit niemand aus der
  Auswahl verschwindet.
- **PC↔NPC-Umwandlung in-place** (`entities/repository.py::person_zu_npc`/
  `person_zu_pc`, neue Routen `POST .../personen/{id}/zu-npc`/`zu-pc`):
  PC und NPC sind derselbe `Person`-Knoten, `personType` kippt nur ein
  Filterfeld — Inventar, Charakterbogen, Beziehungen, Bilder bleiben
  unangetastet. PC→NPC setzt `istVorgefertigt=false` zurück und löst eine
  bestehende `SPIELT`-Kante (Spieler landet wieder im Ersteinstieg).
  NPC→PC verliert `istHaendler`/`istCritter`/`istKI`/`istPflanzenCritter`
  (ergeben an einem PC keinen Sinn; Mark: "ein NPC der mal Händler war
  seinen Händler Status verliert" — Sortiment bleibt dabei in der DB,
  nur das Flag kippt). Beide loggen `CharakterEntwicklung`
  (`ZU_NPC_GEMACHT`/`ZU_PC_GEMACHT`).
- **Frontend:** Checkbox + "⇄ Zu NPC machen" im PC-Detail-Schnellzugriff,
  "⇄ Zu PC machen" im NPC-Detail — je mit Commlink-`Bestaetigung`-Dialog
  (Marks Standardregel für destruktive/folgenreiche Aktionen).
- **Verifiziert:** echter E2E-Test gegen laufende Neo4j — Filter zeigt nur
  `istVorgefertigt=true`, PC→NPC setzt Flag zurück + Baustand bleibt
  (`konzept` als Stichprobe), NPC→PC in Gegenrichtung, ehemaliger Händler
  verliert `istHaendler`, falscher Ausgangstyp liefert `None` statt Crash;
  Migration separat getestet (Bestandsdaten werden markiert, idempotent,
  überschreibt keinen manuell gesetzten Wert erneut). Backend-Suite: die
  von dieser Änderung berührten 511 Tests grün (`tsc -b` sauber).
  **Hinweis:** beim Testlauf liefen parallel 6 unabhängige Fehlschläge aus
  einer zeitgleich laufenden zweiten Session (Umbau `zeigeInGraph` →
  `storyRelevant`, Migrationen 009/010 — nicht von dieser Änderung
  verursacht, per `git diff` auf die dortigen Dateien bestätigt). Eigene
  Migration von `009` auf `011_istvorgefertigt.cypher` umbenannt, weil
  `009`/`010` von der Parallel-Session zwischenzeitlich belegt wurden.
  **Nie im Browser angeklickt** — siehe „Offen“ oben.

**Zuletzt gebaut (04.–08.10.2026 — Urlaubs-Woche mit Chibi Neko auf bebop):**
- **Was:** 45 Commits auf `main`, HEAD `be2a6ff`. Gebaut und live geschaltet von Chibi Neko
  über Telegram, während Andromeda aus war. Windows-Klon hing bis 09.10. auf
  `19c78e9` und ist per Fast-Forward nachgezogen. Live-Frontend-Image vom
  08.10. 13:54 (letzter Commit), Backend-Image vom 07.10. 20:28 (letzter
  Backend-Commit war 18:00 — Kontakte/Ideenschmiede danach nur Frontend).
- **Inhalt (alles live, chronologisch):** Ort zum Laden + Shop-Regressionen;
  Zusatzfertigkeiten zwischen Fertigkeiten und Hexkraft/Sphäre/NeuroWeaving;
  Massen-KI als Hintergrund-Job, Anzahl-Feld-Clamp, Beratung-Prompt thematisch
  fokussiert; Begleiter-Label „KI“→„Æ“; Rucksack 🎒 im Burgermenü; Alias-Feld
  plus Anzeige „Alias aka echter Name“; Charaktererstellung überlagert
  Einfluss/Verwaltung nicht mehr; Flora & Fauna (Entität Gewächs, Kante
  `LEBT_IN`, eigener Burgermenü-Punkt mit Suche/Anlegen); Rassen-Baukasten
  Stale-Closure bei Modifikator-Klicks; Gegenstand-Anlegen mit Vorlage statt
  Platzhalter; Gegenstandstyp nachträglich nur SL; Popup schließt nicht mehr
  bei Textauswahl über den Rand; Gemini HTTP-503-Retry; Beratung
  Mistral-Fallback + Anbieter-Label; Kontakte: Messenger-Hinweis statt stillem
  Fehler + Suchfeld PC/NPC; Ideenschmiede-Geschichte-Entwurf speichert wirklich
  (Autosave). Rassen-Fairness (immer 24) steht extra im nächsten Block.
- **Doku:** Bis 09.10. war hier nur die Rassen-Fairness nachgetragen. Dieser
  Block schließt die Lücke. Keine offenen Feature-Branches, Working Tree sauber.

**Zuletzt gebaut (04.10.2026 — Rassen-Fairness: Nachteile geben jetzt einen Punkt zurück):**
- **Was:** Mark meldete einen vermuteten Logikfehler bei den Rassen ("ich
  glaube es wird nur der erste - Wert gerechnet, aber alle + Werte... Und
  das führt zu einem Ungleichgewicht"). Nachgerechnet: kein Rechenfehler
  (jeder Nachteil wurde schon immer korrekt summiert, 15/15 Tests grün),
  aber die Formel selbst war unfair — Nachteile brachten keine freien
  Punkte ein, also kamen Rassen mit Schwächen am Ende auf weniger
  Gesamtpunkte (24 − Σ Nachteile) als der Mensch (immer 24). Mark wollte
  stattdessen: "ein Minus Punkt gibt einen Punkt zurück, es soll also immer
  24 rauskommen". Neue Formel: Freie Punkte + Σ Vorteile − Σ Nachteile = 15
  (statt vorher ohne das Minus). Die fünf eingebauten Rassen wurden
  entsprechend neu balanciert: Ork 6/5/3→6/6/3, Elf/Zwerg 5/5/3→5/6/3, Troll
  5/4/3→5/6/3 — alle landen jetzt exakt bei 24. Die "Nachteile = aufgerundet
  halbe Vorteile"-Mindestregel bleibt (verhindert weiterhin ein reines
  Vorteils-Volk ohne erzählerische Schwäche, ist aber kein Budget-Mechanismus
  mehr, das erledigt die neue Formel von selbst).
- **Dateien:** `rassen/balance.py` (Formel + Docstring), `traits/erstellung.py`
  (RASSEN-Werte), `tests/test_rassen_balance.py`, `rassen/RassenUebersicht.tsx`
  (Hinweistext), `docs/api/rassen.md`, `docs/regeln-neotopia.md`.
- **Verifiziert:** `pytest tests/test_rassen_balance.py tests/test_rassen_grenzen.py`
  + volle Suite + `tsc -b`/`vite build`. Im Browser: Rassen-Baukasten zeigt
  alle fünf Rassen als "✓ ausgewogen" mit der neuen Bilanz; eine testweise
  angelegte Troll-Erstellung kommt in Summe auf 24 Attributpunkte.

**Zuletzt gebaut (10.10.2026 — Shops nur noch über den Ort):**
- **Was:** Mark: Shops nicht über NPCs anlegen. Laden, Ware, Spezialisierung,
  Vertriebsart und Tutorial-Flag hängen am Ort (`OrtLadenFenster`: Zum Laden
  machen, Haken Tutorial-Shop, Sortiment). Verkäufer-NPC ist optional und nur
  für Verhandeln/Kontakte. Kein Auto-Ort mehr aus `istHaendler`. NPC-Detail
  hat keinen „Zum Händler machen“-Knopf mehr.
- **Dateien:** `haendler/repository.py`, `haendler/OrtLadenFenster.tsx`,
  `NPCDetail.tsx`, `HaendlerBearbeiten.tsx` (Standort-Dropdown weg),
  `HaendlerEinstellungenFenster.tsx` gelöscht, `ki/routes.py`
  (`shop_id_von_gesicht`).
- **Verifiziert:** pytest shop/tutorial/massenidee + `tsc -b`.


**Ältere Einträge (vor 04.10.2026):** vollständiges Build-Log in
`docs/ENTWICKLUNGSHISTORIE.md`, Abschnitt „Build-Log-Archiv“ — chronologisch,
nichts gekürzt. Viele Themen stehen zusätzlich aktuell gehalten im Wiki (immer
zuerst `docs/wiki/index.md` prüfen, siehe oben).

## Wichtige Design-Entscheidungen

*(Details in `docs/api/` — hier nur die Kurzfassung)*

### Mitteilungen (`docs/api/mitteilungen.md`)
- **Kein Absender** — Ansagen kommen "aus der Spielwelt"
- **4 Arten:** TEXT, BILD, WARNUNG (Bildschirm pulsiert), NACHRICHT (Chat)
- **Ausblenden statt Löschen** — jeder räumt seine eigene Liste auf
- **WebSocket** mit Reconnect (Android schläfert Tabs ein)

### Kontakte/Messenger (`docs/api/kontakte.md`)
- **`chatOffen` getrennt von `stufe`** — Nummer haben ≠ kennen
- **Spieler sehen NPCs nur unter Alias** (kein echter Name)
- **Persona-5-Stil** — schräge Sprechblasen, Neon-Farben

### Kampf (`docs/api/kampf.md`)
- **Initiative vom Spieler eingeben** — physische Würfel
- **Reflex-Booster** — Zusatzaktion, Ampel, Paralyse
- **NPC-Namen verborgen** — Spieler sehen "Unbekannter Ork"

### Rüstung (`docs/api/ruestung.md`)
- **Kästchen + Schadensreduktion statt flachem Bonus** — Rüstung nutzt sich ab
- **Reduktion: höher ist besser** (18.09.2026 gedreht — vorher "Durchlass",
  niedriger=besser, von Mark nach dem Praxistest als unintuitiv verworfen:
  *"Durchlass ist ein dummer Wert"*). Wie viel Schaden pro Treffer abgefangen
  wird; sinkt gestuft mit dem Kästchen-Anteil (>50% voll, >25% halb, sonst
  ein Viertel) statt einen eigenen "Aktuell"-Wert zu brauchen
- **Abstufen statt Blocken** — Unheilbar→Tödlich→Schlag, nur Schlag wird
  halbiert (unterste Stufe)
- **Kein separater Aktuell-Wert für die Reduktion mehr** — die effektive
  Reduktion wird aus dem Kästchen-Verhältnis berechnet. Das war zugleich der
  Fix für einen Bug (18.09.2026): der alte Durchlass-Aktuell-Wert zog beim
  nachträglichen Aktivieren über PATCH nicht mit, wodurch frische Rüstung
  fälschlich als zerschossen galt
- **Alles Getragene ist EIN Pool** — Kästchen summiert, Reduktion vom Teil
  mit der besten Basis. **Keine Körperzonen**, kein Zielen (zu kompliziert)
- **Beste Reduktion wird zuerst aufgebraucht**, Überlauf ins nächste. Killt
  nebenbei den "kugelsicheres Suspensorium"-Trick von selbst
- **Zerstörte Rüstung (0 Kästchen) fliegt aus der Ausrüstung** — landet im
  Mitgeführten (reparierbar, wie ausgebautes Chrom), Wiederanlegen gibt 409
- **Treffer hängt an der Person, nicht am Gegenstand** — welche Teile dran
  sind, ist Regelfrage, nicht Angabe des Aufrufers
- **Reparatur noch ohne Probe/Preis** — SL trägt das Ergebnis von Hand ein,
  bis Hardware-Skill-Check und Shop-System stehen

### Rassen (`docs/api/rassen.md`)
- **Katalog global, Freigabe je Kampagne** — der SL hakt an, was in dieser
  Runde wählbar ist; neu gebaute Rassen sind bewusst noch nicht freigegeben
- **Balance-Regel aus den Daten gefunden, nicht erfunden:** freie Punkte +
  positive Modifikatoren = 15, Nachteile = halbe Vorteile (aufgerundet).
  Alle fünf gewachsenen Rassen erfüllen sie exakt
- **Baukasten warnt, blockiert nicht** — ein übermächtiges NPC-Volk bleibt
  möglich
- **Nur Attribute** — Fertigkeitsboni o.ä. gäbe es nicht mehr nachrechenbar
- **Erstellungsgrenze ≠ Lebensmaximum:** `startmaxima` = 4+Mod (nur bei der
  Erstellung), `lebensmaxima` = 6+Mod (dauerhaft, als `maxOverride` am Blatt)
- **Rassen-Kennung ist eine UUID ohne Namen** — Lehre aus Stolperstein 6,
  damit Umbenennen im Baukasten nichts zerreisst

### Cyberware
- **`verbaut` statt `ausgeruestet`** — Chrom sitzt im Körper
- **Chirurgisch entfernen** — kein "Ablegen"-Button
- **Kein generisches Bonus-Feld** — Initiative-Bonus nur für Reflex-Booster

### Allgemein
- **Bestätigungsdialog** für destruktive Aktionen
- **Papierkorb** statt echtem Löschen (SL-sichtbar)
- **Keine harten Farbwerte** außerhalb `frontend/src/theme/`

## Bekannte Stolpersteine

1. **`uvicorn --reload` auf Windows** — Zombie-Prozesse. Beide PIDs killen, ohne `--reload` starten.
2. **Cytoscape + `text-align: center`** — Canvas verschoben. Fix: `textAlign: "left"` auf Container.
3. **Neue Pydantic-Felder + Bestandsdaten** — `coalesce`-Fallback in `_decode()` nicht vergessen!
4. **WebSocket nicht an `require_campaign_zugang`** — wirft HTTPException, Client sieht nur Abbruch.
5. **6-Schichten-Check bei neuen Feldern:** DB-Property → Repository FIELDS+DEFAULTS → Create-Schema → Update-Schema → Response-Schema → Frontend-Interface
6. **TraitDef-Umbenennen braucht eine Migration!** Die Kennung ist
   `ruleset:category:name` (`traits/seed.py`). Wer einen Wert umbenennt,
   ändert damit die Kennung — `MERGE` legt dann einen **neuen, leeren**
   Knoten an, während der alte samt aller Charakterwerte (`HAS_TRAIT`, dort
   sitzt das `rating`) stehen bleibt. Genau so entstand der Arete/Hexkraft-
   Doppelgänger (10.09.2026): Blatt zeigte die alten Punkte, Kampfkarte den
   neuen leeren Wert, und weil die alte Kategorie keine Magie-Kategorie mehr
   war, sah plötzlich jeder Charakter die Zeile. Vorlage für den Fix:
   `seed.py::_migriere_arete_zu_hexkraft` (Werte umhängen, alten Knoten erst
   löschen wenn nichts mehr dranhängt).
7. **Neo4j NIE mit `docker run` starten — sonst Datenverlust!** Das
   neo4j:5-Image deklariert `VOLUME /data`; ein `docker run` ohne explizites
   `-v` erzeugt jedes Mal ein **anonymes Volume** → DB startet leer → wirkt
   wie „Kampagne gelöscht". Die alten Daten liegen dann in verwaisten
   anonymen Volumes. Immer `docker compose up -d neo4j` nutzen (benanntes
   Volume `pnptool_neo4j_data`). Am 15.09.2026 behoben: aktuelle Daten aus
   dem anonymen Volume ins benannte Volume kopiert, Container über compose
   neu erstellt. Diagnose-Hinweis: `docker volume ls` zeigt anonyme
   Hash-Volumes als Verräter; ein Re-Start eines alten Containers
   (`docker start pnptool-neo4j-1`) endet mit Exit 3 (Server startet+stoppt
   sofort) — stattdessen `docker rm` + `docker compose up -d neo4j`.
8. **`tests/test_shop_am_ort.py` instabil im Verbund, isoliert stabil**
   (gefunden 10.10.2026, vorbestehend, siehe `docs/ENTWICKLUNGSHISTORIE.md`
   Stolperstein 13 für die volle Herleitung) — `asyncio.run()` pro Test +
   Modul-Singleton-Treiber. Ein Fehlschlag im vollen Lauf dieser Datei ist
   kein neuer Bug, Test isoliert laufen lassen.

## Git-Workflow

- Remote: `https://github.com/Auriel-McCloud/PnPTool.git`
- Branch: `main` (direkt committen)
- Commit-Messages: Deutsch, eine Zeile, fachliches Ergebnis
- Session-Start: `git log --oneline -5`, `git status`
- Session-Ende: committen + pushen (Mark arbeitet von PC und Handy)

## Server-Status

- **Neo4j:** Docker Compose, Container `pnptool-neo4j-1`, Port 7687 — benanntes Volume `pnptool_neo4j_data` (nie `docker run`, siehe Stolperstein 7)
- **Backend:** `127.0.0.1:8001` (Port 8001 wegen Zombie-Prozessen)
- **Frontend:** `localhost:5173`, Vite-Proxy → 8001


## Geplante Features — Status & Doku-Verweise

Ausführliche Herleitung/Historie jedes Punkts: `docs/ENTWICKLUNGSHISTORIE.md`,
Abschnitt „Geplante-Features-Archiv“ (nichts gekürzt, nur hierher verschoben).
Wo es bereits eine Wiki-Seite gibt, ist die die aktuellere Quelle (Stand wird
dort weitergepflegt, hier nicht mehr).

| # | Feature | Status | Doku |
|---|---|---|---|
| 1 | Shop-System + Händler-Spam | Kern+Sortiment+Verhandeln ✅ gebaut; Spam/Scammer/I.C.E.-Skalierung **offen** | `docs/api/haendler.md`, [[waehrung-und-preise]] |
| 2 | Augment-Differenzierung (Hexware/Bioware/Cyberware exklusiv) | ✅ fertig | [[cyberware-bioware]] |
| 3 | KI-Integration (NPC-Gen, Bild, Wiki-Import, Auto-Verknüpfung, Prüfung, Beratung, alle Welttypen) | ✅ größtenteils gebaut; Chatbots an Gegenständen **nicht umgesetzt**; Jev **geparkt** | [[ki-integration]], `docs/api/ki.md` |
| 4 | Spotify | ✅ fertig | [[spotify-anbindung]] |
| 5 | Deploy (Debian/nginx) | ✅ erledigt (bebop) | `docs/api/tech-stack` s.u. |
| 6 | Drei-Ebenen-Architektur (Regelsystem→Kampagne→Ideenschmiede) | ✅ fertig | [[architektur-drei-ebenen]] |
| 7 | Rüstungssystem inkl. Reparatur | ✅ fertig | `docs/api/ruestung.md`, [[ruestung-kaestchen-durchlass]] |
| 8 | KI+Critter als echte NPCs, Einfluss-System, Matrix-Attribut | ✅ Backend+Frontend fertig; KI-Auto-Steigerung **offen** (braucht Party-Besuchs-Log) | nur Archiv (noch keine eigene Wiki-Seite) |
| 9 | Decker/Neuroweaver 6-Skill-System | ✅ fertig | [[neuroweaving-decking]] |
| 10 | KI-Chatbots für Gegenstände (Decker-Deck, TTS) | reine Idee, **nicht begonnen** | nur Archiv |
| 11 | Charakterportrait im Spieler-Menü | ✅ MVP (Upload/Kamera/KI); Zeichentool **offen** | [[ki-integration]] (Bildgenerierung) |
| 12 | Steckbrief nachträglich bearbeiten | ✅ erledigt | — |
| 13 | Handy-Ansicht Story-Wiki + Ideenschmiede | ✅ gebaut | [[ingame-wiki-feature]], [[ui-konzept-commlink]] |
| 14 | Häretiker-Flavor (Magier-Reskin) | ✅ fertig | [[magie-hexkraft]] |
| 15 | Critter-Tamagotchi/Desktop-Pet | reine Idee, **explizit zuletzt** (Marks Vorgabe) | nur Archiv |
| 16 | Inventar-Transfer + neue Gegenstandstypen | Party-Weitergabe ✅; Rest (gleicher Ort, Geld, Credstick, Heiltrank, Granate) **offen**, Datenmodell nicht entschieden | [[gegenstand-transfer]] |
| 17 | Ereignisprotokoll / Sitzungs-Log | Backend+Hooks+SL-Zeitleiste ✅; Korrektur/Papierkorb-UI + NPC-Wissen + ein paar KI-Nebenpfade **offen** | [[ereignisprotokoll]], `docs/api/ereignisprotokoll.md` |

