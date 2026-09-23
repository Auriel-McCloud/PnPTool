# PnPTool — Projektgedächtnis für Claude

Diese Datei wird von Claude Code automatisch geladen. Sie ist die Quelle der Wahrheit für den Projektstand — bei jeder größeren Änderung aktualisieren. **Bleibt bewusst schlank:** Details wandern nach `docs/api/` bzw. ins Wiki, nicht hier hinein.

## Offen: Was Mark selbst testen muss (Stand 23.09.2026, nachts)

Diese Punkte wurden von Agenten gebaut, aber mangels laufendem Frontend-Dev-Server
bzw. GPU-Hardware nur eingeschränkt oder gar nicht verifiziert. Bitte am
Spieltisch/Dev-Server gegenprüfen, danach hier aus der Liste streichen:

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
- **🔍-Prüfen-Knopf im RichTextEditor** (Personen/Orte/Events/Fraktionen/
  Gegenstände/Begleiter): nie im Browser angeklickt, nur `tsc -b` und
  Backend-Import geprüft. Siehe „Zuletzt gebaut" unten.
- **Rüstungs-Reparatur-UI** (`RuestungReparatur.tsx` im Bearbeiten-Fenster
  einer Rüstung, `VerhandlungPopup.tsx` beim Spieler): nie im Browser
  angeklickt, nur `tsc -b` geprüft. Die Backend-Logik dahinter (Würfe,
  Materialverbrauch, Preisformel, Deckel, Annehmen/Ablehnen) wurde per
  echtem End-to-End-Skript gegen laufendes Backend + Neo4j durchgespielt
  und ist verifiziert — offen ist nur die Optik/Bedienung der beiden neuen
  Popups selbst (Layout, ob der Commlink-Stil passt, ob das Verhandlungs-
  Popup beim Spieler zuverlässig aufpoppt). Siehe „Zuletzt gebaut" unten.

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
- **Deployment**: Aktuell Windows-Dev, später Debian/nginx

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
| 3 | 🟡 | Charakterblatt (Attribute ✅, Box-Tracks ⬜) |
| 4 | ✅ | Spieler-Zugang, Sichtbarkeit |
| 5 | ✅ | **Mitteilungen + Messenger fertig** |
| Wiki | ✅ | Seitenbaum, Freigaben, TipTap-Editor |
| Themes | ✅ | Zwei Themes, Token-basiert |
| Rüstung | ✅ | Kästchen + Schadensreduktion + Reparatur (Selbst/Händler), siehe `docs/api/ruestung.md` |
| Party | ✅ | Gruppen, Mitgliedschaft, aktive Party, siehe `docs/api/party.md` |
| Spotify | ✅ | Playlist an Ort/Event, Musik folgt aktiver Party, siehe `docs/api/spotify.md` |

**Zuletzt gebaut (23.09.2026/24.09.2026, nachts — Messenger-Mobil-Fixes + Wiki-Mobil-Drawer):**
- **Kontext:** Mark hatte Token-Kontingent übrig und ließ nachts autonom zwei
  bereits mit ihm durchgesprochene, klar spezifizierte Baustellen bauen
  (Chat und CLAUDE.md-Punkt 3 der Messenger-Todos, Punkt 13 „Handy-Ansicht").
  Cronjob als Sicherheitsnetz lief mit, falls die Tokens vorzeitig ausgehen —
  wurde nicht gebraucht, alles in einem Durchgang geschafft.
- **Messenger (`frontend/src/kontakte/Messenger.tsx`/`messenger.css`):**
  - Hart-Scroll ans Verlaufsende **nur mobil** (`matchMedia("(max-width:
    600px)")`), Desktop bleibt beim bisherigen `behavior: "smooth"` — dort
    war das Scrollen schon zuverlässig, das Problem betraf nur Mobilgeräte.
  - Composer bei geöffneter mobiler Tastatur sichtbar: `window.
    visualViewport`-Listener setzt die Höhe der Chat-Hülle auf die
    tatsächlich sichtbare Viewport-Höhe und scrollt den Composer nach jeder
    Größenänderung ins Bild (`resize`/`scroll`-Events, mobil-only).
  - Sprechblasen bekommen eine leicht variierende Schräg-Ecke
    (`--msg-schraeg`, 6–15px, deterministisch aus der Nachrichten-ID
    gehasht) statt der bisher zwei starren Formen (eigen/fremd identisch
    geschnitten) — wirkt dadurch weniger uniform, Persona-5-typischer.
    **Bewusst nur Form/Größe geändert**, Farben und Ausrichtung (eigen
    rechts/Signal-Ton, fremd links/Neon-Ton) unangetastet, wie von Mark
    vorgegeben. `.msg-blase` ist jetzt `display: inline-block` statt einer
    impliziten Blockbreite — folgt dem Textinhalt, keine feste Breite mehr.
- **Wiki-Mobil-Drawer** (Punkt 13, zweiter Teil — Editor-Lesbarkeit war
  schon am 20.09.2026 erledigt):
  - **Seitenbaum + Inhaltsverzeichnis** (`WikiAnsicht.tsx`/`wiki.css`):
    unter 999px (bestehender Breakpoint) jetzt ein echtes Slide-in mit
    Backdrop (`wk-abdunklung`, Antippen schließt beide Schubladen) und
    Einfahr-Animation (von links bzw. rechts). Der `.wk-schublade-zu`-Knopf
    (✕) war in CSS schon vorbereitet, aber nie im JSX verdrahtet — jetzt an
    beiden Schubladen sichtbar. Größere Touch-Ziele im aufgeklappten Baum
    (44px Mindesthöhe je Zeile/Klapp-Knopf), Desktop-Dichte unangetastet
    (eigener `[data-offen="true"]`-Scope in der Media Query).
  - **Ideenschmiede-Kachelraster** (`ideenschmiede.css`, betrifft Story-Wiki
    UND Ideenschmiede gemeinsam, wie Punkt 13 verlangt — beide teilen sich
    `.is-liste`/`.is-item`): unter 599px eine Spalte statt Grid-Fallback,
    Aktionsknöpfe (Übernehmen/Löschen) jetzt nebeneinander mit 40px
    Mindesthöhe statt in der schmalen Reihe zusammengequetscht, Filter-Tabs
    horizontal scrollbar. **Bewusst NICHT** die generische `gg-raster`-
    Komponente (Gegenstände/Party/Begleiter/Fraktionen) angefasst — war
    Marks ausdrückliche Vorgabe, kleiner Scope.
  - **Verweis-Auswähler** (`VerweisWaehler.tsx`, CSS in `wiki.css`): bleibt
    ein Popup (kein Vollbild-Overlay, wie von Mark vorgegeben) — Suchfeld
    jetzt `position: sticky` am oberen Rand der Trefferliste (16px
    Schriftgröße gegen den iOS-Zoom-Sprung beim Fokussieren), Trefferzeilen
    mit 48px Mindesthöhe statt der bisherigen knappen Polsterung.
  - Slide-in gilt aktuell dem Baum/Verzeichnis, nicht einem eigenen
    Hamburger-Symbol — der bestehende ☰/☷-Knopf im Seitenkopf (schon vor
    dieser Runde vorhanden) übernimmt diese Rolle unverändert.
- **Verifiziert:** `tsc -b` fehlerfrei für beide Baustellen. **Kein
  Browser-Test** — das Browser-Werkzeug dieser Session kann `localhost`
  nicht erreichen (Netzwerksperre auf private/interne Adressen), daher war
  auch die eigentlich geplante DevTools-Mobil-Emulation nicht möglich. Nur
  Code-Review + Typprüfung. Mark muss beides am echten Handy gegenprüfen,
  siehe „Offen" oben — insbesondere das `visualViewport`-Verhalten bei der
  Tastatur-Sichtbarkeit, das je nach Mobilbrowser unterschiedlich zuverlässig
  ist.

**Zuletzt gebaut (23.09.2026, Rüstungs-Reparatur — Frontend + Verhandlungs-Popup):**
- **Backend war bereits fertig** (Formeln `repariere`/`hardware_probe_pool`/
  `selbstreparatur_ergebnis`/`haendler_reparatur_preis` in `kampf/ruestung.py`,
  Routen `ruestung/reparieren-selbst` + `ruestung/reparatur-preis` +
  `reparaturmaterial` in `items/routes.py`, generisches Verhandlungs-Popup-
  Backend in `app/verhandlung/`) — dieser Durchgang ergänzt nur noch das
  fehlende Frontend, siehe `docs/api/ruestung.md` Abschnitt „Reparatur" für
  die vollständige Formelherleitung.
- **SL-seitige Reparatur-UI** (`frontend/src/kampf/RuestungReparatur.tsx`):
  sitzt im Bearbeiten-Fenster einer Rüstung (`GegenstandRow` in
  `CharacterSheetPanel.tsx`), erscheint nur wenn tatsächlich Kästchen fehlen.
  Wahl "Selbst reparieren" (zeigt Würfe/Augen/Erfolge, Schwelle, Überschuss,
  verbrauchtes Material samt Restmenge, Ergebnis-Kästchen) vs. "Beim
  Händler" (berechneter Vorschlagspreis editierbar, Deckel-Hinweis bei
  Totalschaden, Knopf "Angebot an Spieler senden").
- **Neues Feld `istReparaturmaterial`/`reparaturKapazitaet`** jetzt auch im
  Bearbeiten-Formular jedes Gegenstands editierbar (Checkbox + Kapazitäts-
  Zahl unter "Optionen") — vorher nur im Backend-Schema vorhanden.
- **Spieler-seitiges Verhandlungs-Popup** (`frontend/src/verhandlung/
  VerhandlungPopup.tsx`): zeigt Positionen + Gesamtbetrag, Annehmen/
  Ablehnen, danach kurz das Ergebnis (bezahlt/nicht bezahlt, Restguthaben).
  Zustellung über denselben Live-Kanal wie SL-Mitteilungen — `Mitteilungen
  Kontext.tsx` trägt jetzt zusätzlich eine eigene Verhandlungs-Schlange
  (eigener Umschlag `_typ: "verhandlung"`, herausgefiltert bevor er die
  normale Mitteilungsliste erreicht) samt Aufhol-Abruf beim Verbinden
  (`GET .../verhandlungen`, da es dafür anders als bei Mitteilungen keinen
  "stand"-Schnappschuss über den WebSocket gibt).
- **Neuer API-Client** `frontend/src/verhandlung/api.ts` (anbieten/offene/
  antworten/zurueckziehen) und Erweiterung von `items/api.ts` um
  `ruestungReparierenSelbst`/`ruestungReparaturPreis`/`reparaturmaterialListe`
  + die Typen `ReparaturWurf`/`ReparaturPreisAntwort`.
- **Verifiziert:** `tsc -b` fehlerfrei, Backend-Import + Routenregistrierung
  geprüft, vollständiger `pytest`-Lauf (424 von 426 grün — die 2 Fehlschläge
  betreffen Spotify/Spieler-Routen aus einer anderen, unabhängigen Baustelle
  und bestehen unverändert auch ohne diese Änderung). **Echter End-to-End-
  Testlauf gegen eigenen Uvicorn-Testport + echte Neo4j** (Test-Rüstung
  beschädigt, Selbst-Reparatur inkl. Materialverbrauch 2→1 durchgespielt,
  Händlerpreis berechnet, Deckel-Grenzfall bei Totalschaden exakt bestätigt
  — 750¥ = 75 % von 1000¥ Neuwert —, Verhandlung erstellt/vom Spieler
  angenommen, Kapitalabzug + volle Reparatur verifiziert) — danach
  vollständig aufgeräumt, keine Spuren in der echten Kampagne.
- **Kein echter Browser-Klicktest der neuen Popups** — siehe „Offen: Was
  Mark selbst testen muss" oben.

**Zuletzt gebaut (23.09.2026, Rechtschreib-/Grammatik-/Logikprüfung für RichTextEditor):**
- **Prüfung jetzt auch an Personen/Orten/Events/Fraktionen/Gegenstände/
  Begleitern** (CLAUDE.md Punkt 3 "Fehlt noch" — jetzt geschlossen), nicht
  mehr nur im Wiki-Editor. Neue Backend-Route
  `POST .../ki/objekt-text/pruefen` (`app/ki/wiki_pruefung.py::pruefe_freitext`,
  ruft dieselbe `_pruefe_text`-Logik samt Kampagnenkontext wie die
  Wiki-Prüfung auf — nur ohne Seitenbezug/Prüfhash, da diese Felder nicht
  zum Sweep gehören und der Knopf gezielt geklickt wird). Frontend: neuer
  🔍-Knopf direkt neben dem ✨-KI-Knopf in `richtext/RichTextEditor.tsx`
  (nur sichtbar, wenn `kiKontext` gesetzt ist — genau die Stellen, die auch
  den ✨-Knopf schon hatten: Personen/Orte/Events/Fraktionen/Gegenstände/
  Begleiter-Beschreibung+Notizen). Neues Popup `ki/ObjektPruefungPopup.tsx`
  (Optik/Verhalten wie `wiki/PruefungPopup.tsx`, aber "Übernehmen" ersetzt
  die Textstelle direkt im offenen TipTap-Editor statt über die API zu
  speichern — der Aufrufer muss wie gewohnt selbst speichern). Verifiziert:
  `tsc -b` und Backend-Import fehlerfrei; **kein echter Klicktest im
  Frontend-Dev-Server** (kein KI-Call verifiziert) — Mark muss das am
  eigenen Bildschirm gegenprüfen.

**Zuletzt gebaut (23.09.2026, Wiki-Import):**
- **Wiki-Import per Dokument-Upload** (Punkt 3 unter "Geplante Features",
  "Wiki-Import" — von offen auf gebaut) — SL lädt ein Word- (.docx) oder
  PDF-Dokument (.pdf) hoch, die KI erkennt die Struktur (Überschriften/
  Kapitel) und teilt es automatisch in eine oder mehrere Wiki-Seiten-
  Entwürfe auf (`istEntwurf=true`, wie jede andere Ideenschmiede-Idee —
  kein Autocommit, SL prüft und übernimmt jeden Entwurf einzeln).
  - **Neues Modul** `backend/app/ki/wiki_import.py`: `dokument_zu_text()`
    liest .docx via `python-docx` (Überschriften-Formatvorlagen "Heading
    1".."Heading 9" werden als `#`/`##`-Präfixe mitgegeben, damit die KI
    die Gliederung sieht statt sie zu erraten) oder .pdf via `pypdf`
    (reiner Fließtext, PDF kennt keine Formatvorlagen — dort erkennt die
    KI Kapitel nur am Textmuster). Grenze `MAX_ZEICHEN = 60_000`: ein
    größeres Dokument wird bewusst abgelehnt (`DokumentZuGrossFehler`)
    statt unvollständig/abgeschnitten importiert zu werden.
  - `gliedere_dokument()` schickt den Text + Kampagnenkontext
    (`sammle_kontext()`, dieselbe Infrastruktur wie jede andere
    KI-Generierung) an die Text-KI und bekommt eine Liste von
    Seiten-Vorschlägen zurück (Titel + Inhalt + optionaler `elternIndex`
    für Unterseiten — die KI erkennt die Hierarchie selbst aus
    Kapitel/Unterkapitel, der SL gibt nichts manuell vor).
  - `importiere()` legt daraus echte Wiki-Seiten an (`wiki/repository.
    create_seite`, derselbe Weg wie der Ideenschmiede-Story-Typ) —
    Unterseiten zuerst ohne, dann mit `parentId` verknüpft (Eltern-IDs
    stehen erst nach dem Anlegen fest). **Pro neu angelegter Seite läuft
    automatisch die bestehende Auto-Verknüpfung** (`auto_verknuepfung.py`,
    unverändert wiederverwendet) — anders als der manuelle „⧉✨
    Auto-Verknüpfung"-Knopf (der jeden Fund einzeln zur Bestätigung
    zeigt) wendet der Import ALLE gefundenen Verweise/Beziehungen direkt
    an; neue Entitäten landen dabei trotzdem nur als Entwurf, kein
    Autocommit in die Kampagne selbst.
  - **Neue Route** `POST /api/campaigns/{id}/ki/wiki/import`
    (multipart/form-data, Feld `datei`, nur SL) — liefert die Liste der
    angelegten Entwürfe (`id`, `titel`, `parentId`, `verknuepfungen`:
    Anzahl automatisch angewandter Auto-Verknüpfungen).
  - **Frontend:** `frontend/src/ki/WikiImportPopup.tsx` (Commlink-Stil,
    Vorbild `KiBildPopup.tsx`) — Datei wählen → Importieren → Ergebnis-
    Liste (Eltern-Kind eingerückt) → „Zur Ideenschmiede" springt in den
    bestehenden Entwurfs-Prüfung/Freigabe-Flow, kein neuer Mechanismus.
    Knopf `⇪✨` in `WikiAnsicht.tsx` neben dem bestehenden „+ Neue Seite"-
    Knopf im Seitenbaum-Kopf.
  - **Verifiziert (23.09.2026, echter Testlauf)**: Test-.docx mit 2 Top-
    Level-Kapiteln + 2 Unterkapiteln (python-docx-generiert, Heading 1/2)
    gegen laufendes Backend + echte Neo4j + echten Mistral-Call
    (`KI_PROVIDER=mistral`) importiert — 5 Entwurfs-Seiten entstanden,
    Unterkapitel korrekt als `UNTERSEITE_VON` der jeweiligen Elternseite
    verknüpft. Eine bereits bestehende Person ("Nachtfalke", vorher
    freigegeben angelegt) wurde in allen vier erwähnenden Seiten korrekt
    per Auto-Verknüpfung erkannt und verlinkt (keine Dublette); mehrere im
    Text erwähnte, aber noch unbekannte Entitäten (Ort "Omikron² Eridiani",
    "Hafenviertel", "Docks", "Rotlichtviertel", Fraktion "Chrom-Kartelle",
    Person "Techniker") wurden automatisch als Entwürfe angelegt und mit
    echten `VERBINDUNG`-Kanten zueinander verknüpft. **Offen:** kein
    echter Klicktest von `WikiImportPopup.tsx` im Frontend-Dev-Server (nur
    `tsc -b` geprüft) — Mark muss das Popup selbst im Browser gegenprüfen.
    Blocker/Grenzen: PDF-Gliederungserkennung ist ungetestet (kein
    Test-PDF gebaut, nur die .docx-Route real durchlaufen) und dürfte
    schwächer sein als bei .docx, weil pypdf keine Formatvorlagen liefert
    — die 60.000-Zeichen-Grenze ist eine Schätzung, keine belastbar
    ermittelte Kontextfenster-Grenze.

**Zuletzt gebaut (23.09.2026, KI-Bildgenerierung):**
- **Bildgenerierung für Personen/Orte/Events/Fraktionen/Gegenstände + eigenes
  Spieler-Portrait** (Punkt 3 unter "Geplante Features", "Bildgenerierung" —
  siehe dort) — neues Modul `backend/app/ki/bildgenerierung.py` mit
  `generiere_bild(provider, prompt) -> (bytes, content_type)`, zwei Provider
  **pro Aufruf wählbar** (Commlink-Popup-Dropdown, anders als der
  Text-Provider `KI_PROVIDER` in `.env`, der global gilt):
  - **`cloud`** — Google Gemini `gemini-2.5-flash-image`
    (`generateContent` mit `responseModalities: ["IMAGE"]`, gleicher
    REST-Stil wie `gemini.py`, kein SDK). Braucht nur den bestehenden
    `gemini_api_key`.
  - **`lokal`** — spricht `pnptool_server.py` in `C:\DEV\Fooocus` an
    (eigener Wrapper-Prozess, **bewusst außerhalb dieses Repos**, nicht
    eingecheckt — Fooocus 2.5.5/Gradio 3.41.2 hat keine eigene REST-API,
    der Wrapper importiert `modules.async_worker` direkt). Neue Settings in
    `config.py`: `fooocus_url` (Default `http://127.0.0.1:7865`),
    `fooocus_breite`/`fooocus_hoehe` (768×768), `fooocus_performance`
    (`"Speed"`), `fooocus_timeout_sekunden` (300, GTX 1070 kann bei SDXL
    mehrere Minuten brauchen). Läuft der Wrapper nicht, liefert das Modul
    eine klare Fehlermeldung statt eines rohen Timeouts.
  - Beide liefern dieselbe Form (rohe Bytes + Content-Type) an den
    Aufrufer zurück — keine zwei Speicherpfade.
  - **Neue Routen** unter `/api/campaigns/{id}/ki/` (nur SL,
    `require_campaign_gm`): `POST bild-prompt` (Body: `objektTyp`,
    `objektName`, `bisherigeBeschreibung` → `{"prompt": "..."}`, schlägt
    einen Bild-Prompt aus Name+Beschreibung vor, dieselbe
    `sammle_kontext()`/`generiere_json()`-Infrastruktur wie die übrige
    KI-Anbindung) und `POST bild-generieren` (Body: `provider`
    (`"lokal"`|`"cloud"`), `prompt` → liefert die rohen Bild-Bytes als
    Vorschau zurück, **speichert nichts**). Spieler-Pendants (eigenes
    Charakterportrait, bewusst ohne `require_campaign_gm`, gleiche
    Begründung wie beim bestehenden `POST /mein-bild`):
    `POST /api/spieler/mein-bild-ki-prompt` und
    `POST /api/spieler/mein-bild-ki` (`backend/app/players/routes.py`,
    rufen dieselbe `_bild_prompt_vorschlagen()`/`generiere_bild()` auf).
    Übernommen wird die Vorschau über die jeweils **bestehende**
    Datei-Upload-Route (Frontend baut aus dem Blob eine `File` und schickt
    sie dorthin) — kein zweiter Ablage-Mechanismus, keine neuen
    Byte-Speicher-Helfer nötig (ein erster Versuch mit eigenen Helfern in
    `entities/routes.py`/`items/routes.py` wurde noch am selben Tag wieder
    entfernt, siehe Commit "Route liefert Vorschau statt sofort zu
    speichern").
  - **Frontend:** neue generische Komponente `frontend/src/ki/KiBildPopup.tsx`
    (Fenster-Stil, angelehnt an `KiTextPopup.tsx`) — Ablauf: Öffnen schlägt
    automatisch einen Prompt vor → Nutzer kann ihn im Textfeld editieren →
    Provider wählen (☁ Cloud/Gemini oder ▣ Lokal/Fooocus) →
    "✨ Generieren" → Bildvorschau → "✓ Übernehmen" (speichert über die
    bestehende Upload-Route) / "↺ Neu versuchen" / "Verwerfen". Aufrufer
    bringt nur `objektTyp`/`objektName`/`bisherigeBeschreibung` und die drei
    Callback-Funktionen mit (`onPromptVorschlagen`/`onGenerieren`/
    `onUebernehmen`) — eine Komponente statt fünf Kopien. Eingebunden an:
    `EntitaetsBild.tsx` (Person/Event, genutzt von NPCDetail/PCDetail/
    EventDetail), `BildGalerie.tsx` (Ort/Fraktion, eigenes Kachel-Kästchen
    im Galerie-Raster), `CharacterSheetPanel.tsx`
    (`GegenstandRow`-Bearbeiten-Formular), `players/
    CharakterportraitAnsicht.tsx` (Spieler-eigenes Portrait, neben
    Datei-Upload und Kamera-Aufnahme). API-Helfer in `frontend/src/ki/api.ts`
    (SL-Weg) und `frontend/src/players/api.ts` (Spieler-Weg).
  - **Verifiziert:** Backend-Import ok, alle vier Routen im OpenAPI-Schema
    registriert, `tsc -b` fehlerfrei, ein echter E2E-Call gegen laufendes
    Backend + echte Neo4j-Daten + echten Gemini-Key lieferte einen
    funktionierenden Bild-Prompt-Vorschlag (Status 200, sinnvoller
    Cyberpunk-Prompt-Text). Die eigentliche Bildgenerierung wurde für
    beide Provider (Cloud/Gemini UND lokal/Fooocus) je einmal erfolgreich
    live getestet.
  - **Zwei ehrliche Einschränkungen, noch offen:**
    1. **Kein Browser-Test des Popups** — `KiBildPopup.tsx` wurde nur gegen
       `tsc -b` geprüft, kein echter Klicktest im laufenden
       Frontend-Dev-Server. Mark muss das selbst am Spieltisch/Dev-Server
       visuell gegenprüfen, bevor es als fertig gilt.
    2. **Fooocus-Wrapper liegt außerhalb des Repos und läuft nicht von
       selbst** — `C:\DEV\Fooocus\pnptool_server.py` ist bewusst nicht
       Teil von PnPTool (eigenes venv, eigener Prozess) und muss von Mark
       manuell als Hintergrundprozess eingerichtet werden (z.B. Autostart).
       Ohne laufenden Wrapper schlägt der "lokal"-Provider im Popup mit
       einer Verbindungsfehlermeldung fehl — der "cloud"-Provider
       (Gemini) funktioniert unabhängig davon.

**Zuletzt gebaut (23.09.2026, Gegenstandstyp fix + KI-Gegenstände + Händler-KI-Vorschlag):**
- **Gegenstandstyp nach Anlegen fix** (Marks Kritik: "mir gefällt nicht das
  man gegenstände zu etwas anderem machen kann") — `typ` aus
  `GegenstandUpdate` entfernt (`backend/app/items/schemas.py`), keine
  Aufräum-Logik für Typwechsel mehr nötig (gleiche Invariante wie
  `istVorlage`). Anlegen läuft jetzt über eine **Kachel-Auswahl** statt
  Dropdown (Marks Wunsch: "ganz viele kacheln... und ich auf die klicke die
  ich gerne hätte") — neuer gemeinsamer Typ-Katalog
  `frontend/src/items/typKatalog.ts` + `TypKachelAuswahl.tsx`, eingebaut an
  allen drei Anlege-Stellen (`GegenstaendeUebersicht.tsx`, `PCInventar.tsx`,
  `CharacterSheetPanel.tsx`). Falsch gewählt → löschen, neu anlegen.
- **KI-Gegenstandsgenerator in der Ideenschmiede** — dritter KI-Ideen-Typ
  neben Story/Charakter (`typ: "gegenstand"` in `ki/routes.py::ki_idee`).
  Backend-seitiger Typ-Katalog `GEGENSTAND_TYPEN`
  (`items/schemas.py`, muss inhaltlich mit dem Frontend-Katalog
  übereinstimmen) als Enum im KI-Schema erzwungen — ungültige/erfundene
  Typen fallen hart auf "Sonstiges" zurück, weil der Typ ja fix ist.
  Entsteht als besitzerloser, SL-geheimer Ideenschmiede-Entwurf
  (istEntwurf=true), genau wie Charakter/Story. Frontend:
  `ideenschmiede/api.ts::KiTyp` um `"gegenstand"` erweitert, Auswahl im
  KI-Popup der Ideenschmiede.
- **KI-Sortiment-Vorschlag für Händler** — neues Modul
  `backend/app/haendler/ki_vorschlag.py`, zwei Endpunkte:
  `GET .../haendler/{id}/ki-vorschlaege` (SL-only, Vorschauliste, nichts
  wird gespeichert) und `POST .../ki-vorschlaege/anwenden` (übernimmt EINEN
  bestätigten Vorschlag). Bevorzugt **bestehende** Gegenstands-Vorlagen der
  Kampagne wiederzuverwenden (Namensabgleich läuft über die echte ID, die
  KI bekommt nur bereits freigegebene — istEntwurf=false — Vorlagen als
  Kandidatenliste, gefiltert auf "noch nicht im Sortiment dieses
  Händlers"), erfindet nur bei einer echten Lücke etwas Neues (dann landet
  die neue Ware als Ideenschmiede-Entwurf, bevor sie ins Sortiment kommt —
  kein Autocommit, dieselbe Vorgabe wie bei der Auto-Verknüpfung). Bewusst
  pro Vorschlag einzeln anzuwenden, kein Sammel-Übernehmen. Frontend
  (SL-Popup mit Vorschlagsliste + Einzeln-Übernehmen-Knöpfen) noch **offen**
  — Backend end-to-end gegen echte Neo4j-DB verifiziert (Wiederverwendung
  UND Neuerfindung beide getestet, Testdaten danach entfernt).
  `test_zugriffsschutz.py`: `ki-vorschlaege` (GET) in
  `NUR_SPIELLEITUNG_LESBAR` aufgenommen (Vorschläge sind
  SL-Entscheidungsgrundlage, kein Spieler-Angebot).

**Zuletzt gebaut (23.09.2026, nachts — Portrait-Löschen + Ersteinstieg):**
- **Charakterportrait: Löschen-Button** — Gegenstück zum Upload aus Punkt 11
  unten. „✕ Entfernen“ (nur sichtbar, wenn schon ein Bild gesetzt ist) fragt
  erst per `Bestaetigung`-Dialog nach (Marks Standardregel für destruktive
  Aktionen), erst danach `DELETE /api/spieler/mein-bild` (neue Route,
  `backend/app/players/routes.py::eigenes_charakterportrait_entfernen`) —
  setzt `bildUrl` nur zurück, löscht die Datei nicht vom Datenträger (gleiches
  Muster wie beim SL-`EntitaetsBild.tsx::entfernen`). Frontend:
  `frontend/src/players/CharakterportraitAnsicht.tsx` + neue Klasse
  `port-btn-loeschen` in `portrait.css`.
- **Ersteinstieg für neue Spieler ohne Charakter** — war bisher nur eine
  Design-Notiz unter Punkt 6 (\"PC-Erstellung (neu)\"), jetzt gebaut. Ein
  Spieler-Account ohne `personId` sieht in `SpielerAnsicht.tsx` statt der
  vollen Commlink-Hülle den neuen Bildschirm `frontend/src/players/
  SpielerEinstieg.tsx` mit zwei Wegen:
  - **Selbst erstellen** — `POST /api/spieler/charakter-neu` legt sofort
    einen leeren PC an und ordnet ihn per `SPIELT`-Kante zu; die bestehende
    Charaktererstellung greift danach automatisch (`erstellungAbgeschlossen
    =false`), Namensvergabe passiert dort wie gewohnt.
  - **Vorgefertigten PC fix wählen** — `GET /api/spieler/vorgefertigte`
    listet alle abgeschlossenen, nicht-Entwurfs-PCs der Kampagne **ohne**
    `SPIELT`-Kante (Mark: \"das macht am meisten Sinn\" — ein vorgefertigter
    Charakter ist bewusst kein eigenes Datenfeld, sondern schlicht ein noch
    nicht zugeordneter PC). `POST /api/spieler/charakter-waehlen` weist ihn
    **atomar** in einer einzigen Cypher-Anweisung zu (`backend/app/players/
    repository.py::charakter_waehlen`) — tippen zwei Spieler gleichzeitig
    denselben Charakter an, gewinnt nur einer, der andere bekommt `409` und
    lädt die (dann veraltete) Liste neu. Vorher per `Bestaetigung`-Dialog
    bestätigt: \"gehört danach dauerhaft dir\".
  - Beide Pfade sperren serverseitig gegen einen zweiten eigenen Charakter
    (409 „Du hast bereits einen Charakter“).
  - **Anmeldefenster vereinheitlicht** (nebenbei, gleicher Commit): altes
    `GmLoginPage.tsx`/`SpielerLogin.tsx` durch ein gemeinsames
    `frontend/src/auth/AnmeldeFenster.tsx` ersetzt — Spieler sehen das
    Login-Formular zuerst, SL-Login ist ein Extra-Klick (\"Ich bin die
    Spielleitung\"), weil am Tisch deutlich mehr Spieler- als SL-Logins
    passieren.

**Zuletzt gebaut (22.09.2026, Auto-Verknüpfung + Beziehungen):**
- **KI-Auto-Verknüpfung** (Punkt 3 unter "Geplante Features", letzter
  offener Baustein der KI-Integration) — „⧉✨ Auto-Verknüpfen"-Knopf im
  Wiki-Editor, neben „🔍 Prüfen". Zweistufig: „✨ Vorschläge holen" schickt
  den Seitentext + Namen aller freigegebenen Personen/Orte/Events/
  Fraktionen an die KI (neu: `app/ki/kontext.py::sammle_entitaeten`), die
  in EINEM Aufruf zwei Arten von Treffern liefert (Mark ist kostenbewusst —
  zwei Requests für denselben Text wären unnötig teuer):
  - **Verweise**: Zitat+Typ+Name → „✓ Verknüpfen" fügt direkt einen
    `entitaetsverweis`-Chip ein (die "Erwähnt in"-Kante zur Wiki-Seite).
  - **Beziehungen** (Marks Nachfrage, gleicher Tag: "erstellt das Tool bei
    neuen Charakteren/Orten auch Verbindungen?") — wo der Text eine
    KONKRETE Beziehung zwischen zwei erwähnten Entitäten ausdrückt (z.B.
    "arbeitet für", NICHT nur zufällige Nähe im selben Absatz), schlägt die
    KI Beziehungstyp+Kurzbeschreibung vor. „✓ Beziehung anlegen" erzeugt
    eine echte `VERBINDUNG`-Kante zwischen den beiden Entitäten selbst —
    dieselbe Route wie der „+ Neue Verbindung"-Knopf im Beziehungen-Tab.
  Der Namensabgleich gegen bestehende IDs passiert bewusst in Python
  (normalisierter Stringvergleich), NIE durch die KI — sie kennt keine
  IDs, ein Tippfehler darf nie eine falsche Verknüpfung erfinden. Jeder
  Treffer einzeln bestätigt; unbekannte Entitäten legen zuerst einen
  SL-geheimen Ideenschmiede-Entwurf an (kein Autocommit in die Kampagne,
  Marks Vorgabe). **Dedup-Schutz** (`_finde_oder_lege_an`): taucht dieselbe
  neue Person in Verweis UND Beziehung auf, entsteht sie nur EINMAL — die
  zweite Anwendung findet die zuerst angelegte wieder statt sie zu
  duplizieren. Neues Modul `backend/app/ki/auto_verknuepfung.py`, drei
  Endpunkte unter `/api/campaigns/{id}/ki/wiki/{seiten_id}/verknuepfung/*`
  (`vorschlaege`, `anwenden`, `beziehung`), neue Datei
  `frontend/src/ki/AutoVerknuepfungPopup.tsx`.
  **Nebenbei-Fix:** `ERLAUBTE_ZIELTYPEN` in `wiki/repository.py` kannte
  „Fraktion" bisher gar nicht — ein Fraktions-Chip im Wiki-Text (auch von
  Hand über „⧉ Verknüpfen" eingefügt) blieb sichtbar, erzeugte aber nie
  eine echte `VERWEIST_AUF`-Kante. Jetzt ergänzt.
  Backend end-to-end verifiziert: Server startet fehlerfrei, alle drei
  Routen im OpenAPI-Schema, Chip-Einfügelogik isoliert getestet (Text wird
  korrekt gesplittet, 🔒 SL-geheim-Marks bleiben auf beiden Textteilen
  erhalten); `tsc --noEmit` fehlerfrei. Bewusst nur Einzelseiten-Knopf (kein
  Sweep über alle Seiten, wie bei der Rechtschreibprüfung) — Mark will das
  erst bei Bedarf. Ideenschmiede-Texte (nicht nur Story-Wiki) sind noch
  offen.

**Zuletzt gebaut (22.09.2026, Shop-System Kern-Baustein):**
- **Shop-System, Kern-Baustein** (Punkt 1 unter "Geplante Features",
  Spam/Scammer/I.C.E.-Skalierung bewusst zurückgestellt) — neues Modul
  `backend/app/haendler/`. Ein Händler ist **keine eigene Entität**,
  sondern eine `Person` mit `istHaendler=true` (analog `istKI`/`istCritter`)
  — bewusst schlank, **kein Charakterblatt** (Marks Entscheidung), nur
  Name/Bild/Beschreibung über die bestehenden `/personen`-Routen. Standort
  läuft über dieselbe `BEFINDET_SICH_AN`-Kante wie bei Party, Kontakt/
  Messenger übers bestehende `KENNT`-System — beides ohne neuen Code.
  **Sortiment gemischt** (Marks Vorgabe): explizite `VERKAUFT {preis}`-Kante
  für gezielt eingetragene Ware (mit Sonderpreis möglich, Auf-/Abschlag) UND
  automatischer Bestand aus globalen Vorlagen (`automatischImShop=true`,
  bereits vorbereitete Felder aus dem September). Neues Feld
  `Person.spezialisierung: list[str]` filtert den automatischen Teil auf
  passende Gegenstandstypen (leer = Gemischtwarenladen zeigt alles; Mark:
  *"bei einem Waffenladen sollte es schließlich keinen Brokkoli geben"*) —
  explizit eingetragene Ware ist davon unabhängig immer sichtbar.
  **Bestand ergibt sich aus bestehenden Feldern, kein neues Konzept:**
  Vorlage (`istVorlage`) → unendlich verfügbar, jeder Kauf kopiert
  (`items/repository.py::assign_copy`); einzigartiges Stück → genau einmal
  kaufbar, verschwindet nach dem Kauf aus dem Sortiment (Besitzerwechsel via
  `transfer_owner`). **Kauf-Endpunkt** `POST .../haendler/{id}/kaufen`
  prüft Guthaben serverseitig (`Person.kapital`, unabhängig vom
  Bestätigungs-Popup im Frontend), zieht ab, übergibt die Ware; zu wenig
  Guthaben → `409` mit `"Guthaben reicht nicht — Xg verfügbar, Yg nötig"`.
  Spieler kaufen nur für sich selbst, SL für jeden PC (gleiches Muster wie
  der Messenger). Backend end-to-end gegen echte Neo4j-DB verifiziert:
  Spezialisierungs-Filter (Waffe erscheint, Brokkoli nicht), Kauf einer
  Vorlage (Kapital korrekt abgezogen, Vorlage bleibt im Sortiment, Kopie im
  Inventar des Käufers), Kauf eines Unikats zu Sonderpreis (verschwindet
  danach aus dem Sortiment, zweiter Kauf korrekt 404), Standort-Zuweisung,
  409 bei zu wenig Guthaben — alle Fälle über echte HTTP-Requests
  durchgespielt, nicht nur unit-getestet. `pytest` komplett grün (die zwei
  vorbestehenden Fehlschläge in `test_zugriffsschutz.py` — `spotify/suche`,
  `/spieler/mein-bild` — stammen aus fremden, unfertigen Änderungen, nicht
  von diesem Feature). **Noch offen:** Frontend (SL-Sortiment-Editor,
  Spieler-Kaufansicht, Standort-Popup), Spam/Werbe-Mechanik, Scammer-
  Storylines, I.C.E.-Spam-Skalierung — siehe Punkt 1 unten und
  `docs/api/haendler.md`.

**Zuletzt gebaut (22.09.2026, KI-Bugfix + ✨-Knopf):**
- **Bugfix Ideenschmiede-Kontext (Mark-Bug):** der Story-Pfad in
  `backend/app/ki/routes.py::ki_idee` rief `generiere_json` bisher OHNE
  `sammle_kontext()` auf — nur der Charakter-Pfad bekam die freigegebene
  Kampagnenwelt mitgeliefert. Folge: bei einer Story-Generierung erfand
  Gemini "Proxima Centauri", obwohl die Kampagne bereits "Omikron²
  Eridiani" als Sternensystem freigegeben hatte. Fix: Story-Pfad bekommt
  jetzt denselben `sammle_kontext()` + `_mit_kontext()` wie Charakter.
  Zusätzlich `_mit_kontext()` verschärft — vorher weiche Formulierung
  ("füge das Neue darin ein"), jetzt eine explizite Vorrang-Regel:
  bestehende Objekte bevorzugt wiederverwenden, nur bei echter Lücke etwas
  komplett Neues erfinden, keinen neuen Namen für etwas bereits
  Freigegebenes erfinden.
- **✨ KI-Knopf an jeder Beschreibung/Notizen** (Marks Wunsch): neben
  🔒 SL-geheim im `RichTextEditor.tsx` erscheint jetzt ein ✨ KI-Knopf,
  sobald die neue optionale `kiKontext`-Prop gesetzt ist (campaignId,
  Objekttyp, Objektname, Feldlabel) — betrifft alle Stellen, die
  `RichTextEditor` einbetten: PC/NPC/Ort/Event/Fraktion-Detail,
  Gegenstand-Beschreibung/Notizen (`CharacterSheetPanel.tsx`),
  Begleiter/Critter/KI-Fenster. Klick öffnet `ki/KiTextPopup.tsx`: freier
  Wunsch-Prompt → Backend generiert einen Vorschlag (neuer Endpunkt
  `POST /api/campaigns/{id}/ki/objekt-text`, bekommt Objektname +
  bisherigen Feldtext + Kampagnenkontext) → **Vorschau im Popup, „✓
  Übernehmen" hängt den Text erst dann ans Ende des Feldes an** (Mark
  wollte explizit keine Direktschreibung, wie bei der Wiki-Prüfung erst
  zur Kontrolle anzeigen; bisheriger Inhalt bleibt erhalten, kein Ersetzen).
  Neue Dateien: `frontend/src/ki/api.ts`, `ki/KiTextPopup.tsx`, `ki/ki.css`.
  Backend end-to-end gegen echte Route verifiziert (`/objekt-text` im
  OpenAPI-Schema, Server startet fehlerfrei); `tsc --noEmit` fehlerfrei.
  Auto-Verknüpfung (KI verlinkt erwähnte Entitäten als Graphkanten) bleibt
  weiterhin offen, als Nächstes angekündigt.

**Zuletzt gebaut (20.09.2026, KI-Prüfung):**
- **Wiki-Rechtschreib-/Grammatik-/Logikprüfung** — erster Teil von Punkt 3
  ("KI-Integration") umgesetzt, Auto-Verknüpfung folgt als nächster Schritt.
  Zwei Einstiege: ein "🔍 Prüfen"-Knopf direkt im Wiki-Editor (eine Seite,
  Story-Wiki UND Ideenschmiede-Wiki-Popup teilen sich die Editor-
  Komponente) und ein "🔍 Fließtext prüfen"-Knopf in den Kampagnen-
  Einstellungen, der ALLE Wiki-Seiten der Kampagne durchgeht — bewusst kein
  automatischer Hintergrundlauf, Mark will das gezielt ab und zu anstoßen.
  Der Sweep überspringt jede Seite, deren Inhalt sich seit der letzten
  Prüfung nicht geändert hat (SHA-256-Hash am `WikiSeite`-Knoten,
  `pruefHash`), damit nicht bei jedem Lauf alles neu an die KI geht.
  Logikfehler beziehen den freigegebenen Kampagnenkontext ein (dieselbe
  Quelle wie beim KI-Charaktergenerator, `sammle_kontext`) — geprüft NUR
  gegen echte Widersprüche zu bestehenden Fakten, ein neuer Name/Ort, der
  in der Welt noch nicht vorkommt, wird nicht gemeldet (sonst hätte jede
  neue Idee einen falschen "Fehler" ausgelöst). Jeder Befund hat ein
  wörtliches Zitat + Vorschlag; "✓ Übernehmen" ersetzt die Textstelle
  automatisch im gespeicherten Dokument — funktioniert auch für Seiten, die
  gerade nicht offen sind. `backend/app/ki/wiki_pruefung.py` (neues Modul),
  drei neue Endpunkte unter `/api/campaigns/{id}/ki/wiki/*`, siehe
  `docs/api/ki.md` (neu). Frontend: `wiki/PruefungPopup.tsx` (geteilt
  zwischen Editor und Einstellungen), `campaigns/EinstellungenFenster.tsx`.
  Backend end-to-end gegen echte Neo4j-DB + Mistral verifiziert (Umlaut-
  Rechtschreibfehler + ein Grammatikfehler korrekt erkannt und übernommen,
  zweiter Sweep-Lauf übersprang die unveränderte Seite korrekt); `tsc -b`
  fehlerfrei.

**Zuletzt gebaut (20.09.2026):**
- **Fertigkeitsmaximum 5→6** — auf Marks Wunsch mit dem Attributmaximum
  gleichgezogen (beide jetzt 6). Betrifft die 30 Kern-Fertigkeiten und die 4
  NeuroWeaving-Fertigkeiten (zählen regeltechnisch als Fertigkeit). Sphären
  bleiben bei 5 — feste Stufenbedeutung (5 = „alles"). Nur `defaultMax` im
  Katalog geändert (`backend/app/traits/seed.py`); `seed_traits()`
  überschreibt bestehende `TraitDef`-Nodes automatisch beim nächsten
  Start/Seed-Lauf, keine manuelle Migration nötig. Details siehe
  `docs/wiki/concepts/attribute-und-fertigkeiten.md`.
- **Wiki-Editor am Handy: lesbare Schriftgröße** — Marks Problem war nicht
  das Layout (das ist am Handy schon vollflächig), sondern dass der
  Fließtext im Editor bei der globalen Basisgröße (16px) unlesbar klein
  wirkte. Unter 600px bekommt `.wk-editor .ProseMirror` 18px/1.6 (Über-
  schriften 26/21/18px) — bewusst nur der Editor-Inhalt, nicht die
  restliche Wiki-UI (Baum, Werkzeugleiste bleiben eng). `frontend/src/
  wiki/wiki.css`. Rein clientseitig, kein neuer Endpunkt. Punkt 13 unter
  "Geplante Features" ist damit teilweise adressiert — Seitenbaum/
  Kachel-Übersicht und Verweis-Auswahl am Handy stehen weiterhin aus.

**Zuletzt gebaut (19.09.2026, spät):**
- **Neonflackern verstärkt** (Marks Feedback: „das Flackern ist zu kurz")
  — Dauer von 0,45s auf 1,6s mehr als verdreifacht. Optik jetzt wie ein
  gestörter alter Fernseher statt nur Farbtönung: SVG-`feTurbulence`-Filter
  erzeugt echtes Schwarz-Weiß-Bildrauschen ("Ameisenkrieg"), per
  `mix-blend-mode: overlay` über den Inhalt gelegt, dazu `backdrop-filter`
  (Blur/Kontrast/Hue), der das Bild darunter sichtbar verzerrt statt es zu
  verdecken. Mehrere harte Schübe (`steps(1, end)`) über die Dauer verteilt
  statt eines einzelnen Fades. `frontend/src/shell/CommlinkShell.tsx`
  (`Stoerung`-Komponente) + `commlink.css` (`cl-flackern`/`cl-rauschen`/
  `cl-verzerrung`). `prefers-reduced-motion` und die zufällige
  5–10-Minuten-Taktung unverändert erhalten.

**Zuletzt gebaut (10.09.2026):**
- **Rüstungssystem: Kästchen + Durchlass** — Rüstung nutzt sich im Kampf ab,
  statt konstant zu bleiben. Treffer-Endpoint rechnet HP-Schaden UND
  Kästchenschaden automatisch aus (`docs/api/ruestung.md` für die
  ausführliche Herleitung inkl. der Sackgassen unterwegs)
- **Gesundheits-Grundwert 5 → 6** — Widerstandsfähigkeit geht bis 6, macht
  12 statt 11 Kästchen natürliches Maximum (mit Chrom 18 statt 17). Keine
  Migration nötig: der Wert ist abgeleitet, alle Charaktere haben einfach
  ein Kästchen mehr
- **Rüstung im Charakterblatt** — vierte Zustandsleiste, Reihenfolge jetzt
  Gesundheit → Willenskraft → Rüstung → I.C.E. Die Initiative steht **nur
  noch im laufenden Kampf** auf dem Blatt. Der Pool kommt fertig gerechnet
  vom Server (`bogen.ruestung`), nicht im Frontend nachgebaut
- **Arete → Hexkraft aufgeräumt** — der Wert hiess im Backend längst
  Hexkraft, im Frontend noch Arete; dazu lagen zwei TraitDef-Knoten in der
  DB (siehe Stolperstein 6). Werte migriert, Frontend durchgehend umbenannt,
  Willenskraft-Logik greift damit auch in der Kampfkarte wieder

**Zuletzt gebaut (11.09.2026):**
- **Rassen-Baukasten** — eigener SL-Bereich (Kacheln + Editor-Fenster):
  Völker bauen, Live-Bilanz gegen die 15er-Regel, Bild, Freigabe je
  Kampagne. Infobox mit Beschreibung und Bild in der Charaktererstellung
- **Rassenmaxima wirken endlich dauerhaft** — der Modifikator hebt jetzt
  auch das Lebensmaximum (Troll: Körperkraft bis 8). Vorher verpuffte die
  Rasse nach der Erstellung; 12 Attribute wurden rückwirkend nachgetragen

**Vorher (07.09.2026):**
- Chat-Benachrichtigungen (💬 Popup bei neuen Nachrichten)
- Mitteilungen ausblenden (✕ Button, pro Person)
- API-Dokumentation (`docs/api/`)

**Offen:** Shop-System-Frontend (Backend-Kern fertig, siehe oben — Mark-Wunsch
23.09.2026: soll optisch sehr ansprechend werden, z.B. ein Karussell für die
Sortiment-Ansicht, und je nach Laden/Händlertyp eine eigene Optik/Theme;
Umsetzung erst wenn Mark zuhause ist, da er das Ergebnis am eigenen Bildschirm
beurteilen will; **zusätzlich 23.09.2026:** das SL↔Spieler-Verhandlungs-Popup,
das für die Rüstungs-Reparatur gebaut wurde (siehe „Zuletzt gebaut" unten),
soll später hier wiederverwendet werden — für Kaufverhandlungen beim Händler,
potenziell über mehrere Positionen gleichzeitig, sprich ein
**Warenkorb-Konzept** für den Shop wird hier mit gebraucht. Backend dafür
schon vorbereitet (`app/verhandlung/schemas.py` trägt eine Liste von
Positionen statt eines Skalars), UI noch nicht spezifiziert.), Shop-Spam/
Scammer-Mechanik, KI-Integration (erste Iteration gebaut), Deploy,
PC-Vorlagen im Regelsystem,
**Kampagnen-Export/Import** (mittlere Priorität — aktuell: Volumen-Kopier-Workaround für Deploy möglich),
Event-Log/Timeline („was ist im Spiel passiert" — niedrige Priorität,
erst grob klären was getrackt werden soll; KQL dafür Overkill, eher
`SpielEreignis`-Knoten + Cypher-Timeline)

**Zuletzt gebaut (19.09.2026):**
- **Tooltip-Popups: Kurztext + Detail-Knopf mit Langfassung** — die
  Regelwerk-Texte aus `docs/reference/Master/` (Fertigkeiten+Sphären) und
  `docs/reference/Neotopia_Attribute_und_Fertigkeiten.md` (Attribute+
  NeuroWeaving) lagen fix fertig, waren aber nie an die Tooltips
  angebunden. Jetzt: `Erklaerung.langtext` (Neo4j), `InfoTipp.tsx` zeigt
  zuerst die Kurzfassung, ein "Detail"-Knopf öffnet ein zweites Popup mit
  der ausführlichen Stufenbeschreibung — nur wenn ein Langtext hinterlegt
  ist. **In der Charaktererstellung erzwungen sichtbar** (neuer `erzwingen`-
  Prop, ignoriert den globalen "Erklärungen"-Schalter): Attribute,
  Fertigkeiten-Auswahl und Freebees zeigen das Fragezeichen immer, weil wer
  neu am Tisch sitzt die Begriffe noch nicht kennt und den Schalter nie
  gefunden hätte.
- **Kästchen-Overflow-Grenze auf 12 angehoben** (Marks Wunsch) — vorher
  kippte jede Zustandsleiste (Gesundheit, Willenskraft, Rüstung, I.C.E.) ab
  10 Kästchen in die Puffer+Enden-Leistenform. 12 ist genau das natürliche
  Gesundheitsmaximum ohne Chrom (Grundwert 6 + Widerstandsfähigkeit bis 6);
  jeder Charakter sieht seine Lebenskästchen jetzt normal einzeln, bis
  Chrom das Maximum tatsächlich darüber hebt. `frontend/src/traits/
  Kaestchen.tsx::OVERFLOW_AB`.
- **Verwundungsanzeige verstärkt** (Marks Feedback nach Praxistest: "beginnt
  erst sehr spät" und "sehr dezent") — Schleier startet jetzt erst ab der
  Hälfte verlorener Gesundheit (vorher ab dem ersten Kratzer, dafür kaum
  sichtbar), steigt danach mit Wurzel-Kurve statt linear schneller an.
  Herzschlag-Puls jetzt ab 75% Schaden relativ statt einer starren
  "≤2 Kästchen übrig"-Schwelle, die bei hoher Gesundheit (Chrom-Bonus) kaum
  je auslöste. `frontend/src/shell/Verwundung.tsx` + `verwundung.css`
- **README/`.env.example` für Neueinrichter vervollständigt** — Marks Frage:
  ob API-Keys nach GitHub transportiert werden (nein, `.env` ist seit jeher
  gitignored und nie committed) und wie ein Neu-Aufsetzer eigene Keys
  einträgt. `.env.example` deckt jetzt auch Gemini/Mistral/Spotify ab
  (vorher nur Neo4j/JWT/CORS), README bekam einen Setup-Abschnitt mit
  Tabelle, was Pflicht ist und was optional.

**Zuletzt gebaut (19.09.2026, davor):**
- **Spotify-Anbindung** — Orte und Events können eine Spotify-Playlist
  hinterlegen (Such-Popup, gleiches Muster wie `wiki/VerweisWaehler.tsx`).
  Läuft die aktive Party dort ein (Aufenthaltsort setzen oder eine Party mit
  bereits gesetztem Ort aktivieren), startet die Wiedergabe automatisch auf
  Marks gerade aktivem Spotify-Gerät — Zielgerät/Lautstärke wählt er selbst
  am Handy per Spotify Connect, das Tool greift dort nicht ein. Daneben ein
  manueller „▶"-Fallback-Knopf am Ort/Event. Ein Konto fürs ganze Tool
  (kein Kampagnenbezug), Verbinden/Trennen in den Kampagnen-Einstellungen.
  Kein Spotify-Fehler blockiert je die Party-Aktion selbst — nur ein
  Hinweistext meldet Erfolg/Grund. Details: `docs/api/spotify.md`

**Zuletzt gebaut (18.09.2026):**
- **Party-Feature** — wieder aufgegriffene Vision vom 28.08.2026 (war beim
  CLAUDE.md-Verschlankungs-Commit verlorengegangen, nur ein toter Verweis in
  `docs/ui-konzept.md` blieb übrig). Eigener Bereich (👥-Symbol): Gruppen
  anlegen, Mitglieder zuweisen (eine Person immer nur in einer Party
  gleichzeitig, automatischer Wechsel), Aufenthaltsort setzen (Ort oder
  Event, analog zur Gegenstands-Ablage). **Höchstens eine Party pro
  Kampagne ist aktiv** — Aktivieren deaktiviert automatisch alle anderen,
  Grundlage für die geplante Spotify/MusicCast-Anbindung (Musik folgt dem
  Aufenthaltsort der aktiven Party). Details: `docs/api/party.md`
- **Party-Suche** — Suchfeld in der Kachel-Übersicht, gleiches Muster wie bei
  Gegenständen (`gg-suche`, dieselbe CSS-Klasse). Rein clientseitig, kein
  eigener Endpunkt: filtert über Name, Beschreibung, Mitgliedernamen und
  Aufenthaltsort. Kein Debounce nötig, weil ohne Server-Roundtrip.
- **Party-Bearbeiten-Fenster umgebaut** (Marks Feedback 19.09.2026, nach dem
  ersten Praxistest): Mitglieder-Sektion jetzt ganz oben — man will vor
  allem sehen, wer gerade dabei ist. Beschreibung/Notizen dafür ganz unten.
  Mitglieder- und Ziel-Auswahl haben jetzt auch ein Suchfeld
  (`PersonenAuswahlListe`/`MitgliedHinzufuegenListe`/`ZielAuswahl`, gleiches
  Muster wie beim Anlegen-Popup) — Hinzufügen läuft jetzt per Klick auf die
  Trefferzeile statt über ein Dropdown mit Extra-Knopf. "Aufenthaltsort" in
  "Aufenthaltsort/Ereignis" umbenannt, weil beide Zieltypen gleichwertig
  sind. Name/Beschreibung/Notizen speichern jetzt per `onBlur` (Muster aus
  `OrtDetail`/`FraktionDetail`/`EventDetail`) statt über einen eigenen
  Speichern-Knopf. "Party auflösen" hat jetzt den `Bestaetigung`-Dialog
  statt direkt zu löschen (Marks Standardregel: destruktive Aktionen
  brauchen eine Rückfrage). Das Namensfeld sitzt bewusst ganz unten, nach
  Notizen — Umbenennen ist der Notfall, man erkennt die Party an Mitgliedern
  und Aufenthaltsort, nicht am Namen.

**Zuletzt gebaut (15.09.2026):**
- **Fraktionen als eigener Entitätstyp** — eigener Bereich (Hexagon-Symbol),
  Kacheln, Detail-Popup, Ideenschmiede-Integration, Graph-Darstellung,
  Bildergalerie. Felder: name, description, ziele, ressourcen, notes.
  `Anführer` und `Einfluss` sind bewusst keine Felder, sondern Verbindungen
  (Einfluss pro Ort/Planet/Person = Kante Fraktion→Ort mit Typ „Einfluss")
- **Ziele & Ressourcen als Kurz-Lang-Listen** — statt eines Freitext-Blocks
  eine Liste von Einträgen mit Kurzbeschreibung + ausformulierter
  Beschreibung, bearbeitet im Popup (gemeinsame Komponente `KurzLangListe`)
- **Beziehungs-Menü in den Detail-Popups** — PCs, NPCs und Fraktionen können
  jetzt direkt im Beziehungs-Tab neue Verbindungen anlegen (vorher nur im
  Verbindungen-Bereich). Gemeinsame Komponente `BeziehungsTab` + Suchfeld im
  Ziel-Dropdown. Vorschläge je Typ: Fraktionen „Anführer/Einfluss/Verbündeter",
  Personen „Schulden bei/Gläubiger/Freund/Feind" (für den Kredit-Fall)
- **Rassen-Fixes** — Bild-Upload repariert (Routing-Konflikt: generische
  `/{art}/{node_id}/bild`-Route fing `/rassen/...` ab; jetzt vier explizite
  Routen) und Rassenbeschreibung+Bild ins Fragezeichen-Popup statt Infobox
  unter den Karten (Übersicht bleibt schlank)
- **KI-Integration (erste Iteration)** — Gemini generiert direkt in der
  Ideenschmiede: „✨ KI"-Knopf öffnet ein Popup mit Typ (Charakter/Story-Part)
  und Wunsch-Text. `story` wird eine Wiki-Seite, `charakter` ein NPC — beide
  als Entwurf (`istEntwurf=true`). Backend `app/ki/` (dünner Gemini-Client +
  `POST /ki/idee`), Modell konfigurierbar (`gemini_model`, Default
  `gemini-3.6-flash`), API-Key liegt in `backend/.env` (gitignored)

**Zuletzt behoben (18.09.2026):**
- **Kästchen-Overflow-Darstellung fertiggestellt** — war schon gebaut, aber
  am Spieltisch als „nicht ganz stimmig" erkannt und in vier Runden
  nachgebessert (volle Herleitung: `docs/wiki/concepts/attribute-und-fertigkeiten.md`,
  Zusammenfassung: `CLAUDE.md` Punkt 9 weiter unten):
  1. Füllrichtung zwischen Gesundheit und Willenskraft/I.C.E. vereinheitlicht
  2. Gesundheits-Popup im Charakterblatt umging die Rüstungsrechnung — jetzt
     gesperrt, Schaden geht nur noch über „⚡ Treffer eintragen"
  3. Willenskraft-Rückfrage fehlte ab 11 Kästchen (Overflow-Schwelle) — jetzt
     auch in der Vollansicht mit Rückfrage
  4. Rüstungstreffer hatte noch ein rohes Zahlenfeld statt des Zahlenpads —
     `Zahlenpad` nach `frontend/src/shell/` extrahiert, von beiden Fenstern
     genutzt
- **Doppelter Gewicht/Traglast-Schalter entfernt** — lag sowohl im
  Zugangs-Menü (`SpielerVerwaltung.tsx`, eine der ersten Baustellen des
  Projekts) als auch im eigentlichen Einstellungen-Fenster
  (`EinstellungenFenster.tsx`, über die Werkzeugleiste erreichbar). Der
  Schalter im Zugangs-Menü hatte dort nichts zu suchen und ist raus; der im
  Einstellungen-Fenster bleibt die einzige Stelle.
- **Frisch aktivierte Rüstung ließ sich nicht ausrüsten** — neuer
  Gegenstand, im Bearbeiten-Formular zur Rüstung gemacht, landete immer im
  Mitgeführten. `update_gegenstand` (PATCH) zog `ruestungKaestchenAktuell`
  anders als `create_gegenstand` nicht auf `Max` nach, blieb bei 0 stehen —
  die 409-Sperre gegen zerschossene Rüstung griff dadurch sofort bei jedem
  frisch aktivierten Stück. Fix zieht jetzt nach, aber nur beim Übergang von
  `Max == 0`, nicht bei bereits aktiver (evtl. beschädigter) Rüstung. Details:
  `docs/wiki/concepts/ruestung-kaestchen-durchlass.md` Punkt 7
- **Rüstung: Durchlass durch Schadensreduktion ersetzt** — Mark nach dem
  ersten Praxistest: *"Durchlass ist ein dummer Wert, sorry"*. Kompletter
  Umbau des zweiten Rüstungswerts von "niedriger=besser, Größe der Lücke"
  auf "höher=besser, wie viel Schaden abgefangen wird" — klassischer
  Soak-Wert. Kein eigener "Aktuell"-Wert mehr: die effektive Reduktion sinkt
  gestuft mit dem Kästchen-Anteil (>50% voll, >25% halb, sonst ein Viertel),
  Mark: *"eine Lederjacke mit 1 Absorption bleibt immer gleich, ein
  Bombenschutzanzug der stark beschädigt wird wird schwächer"*. Betraf
  Schema, Repository, beide Rüstungs-Routen, Kernformel
  (`kampf/ruestung.py`, alle 26 Tests neu geschrieben) und vier
  Frontend-Dateien. `docs/api/ruestung.md` komplett neu geschrieben,
  Zwei alte Test-Rüstungen in der Kampagne gelöscht (auf Marks Wunsch, statt
  Migration). Details: `docs/wiki/concepts/ruestung-kaestchen-durchlass.md`

**Zuletzt behoben (15.09.2026):**
- **Charakterblatt-Ladefehler:** `KeyError: 'ruleset'` — nach dem Umbau auf
  `(:Campaign)-[:NUTZT_REGELSYSTEM]->(:Regelsystem)` lieferte `get_campaign`
  kein `ruleset`-Feld mehr, `get_bogen` und `regeln/_ruleset` crashten.
  `get_campaign` liefert jetzt zusätzlich `ruleset` als Klein-Slug
  (`toLower(regelsystem-Name)`) zurück.

**Zuletzt behoben (11.09.2026):**
- **Ideenschmiede-Ort anlegen:** Die Frontend-API verwendete für alle
  Ideenschmiede-Endpunkte den Pfad ohne `/api` und landete dadurch beim Vite-
  Server auf 404. Alle Pfade laufen jetzt über den Backend-Proxy; Anlegen und
  Löschen eines Entwurfs per LAN-Adresse end-to-end geprüft.

### Aktuelle Messenger-UI-Todos (10.09.2026) — ✅ erledigt (24.09.2026, nachts)
Alle drei Punkte gebaut, siehe „Zuletzt gebaut" oben (Messenger-Mobil-Fixes).
Kein Browser-Test möglich (Netzwerksperre der Session), Mark muss am echten
Handy gegenprüfen — siehe „Offen: Was Mark selbst testen muss" oben.
- ~~**Verlauf zuverlässig ans Ende scrollen**~~ — Hart-Scroll nur mobil.
- ~~**Eingabefeld bei geöffneter Tastatur sichtbar halten**~~ — Visual
  Viewport API.
- ~~**Persona-5-Chatoptik vervollständigen**~~ — dynamische Sprechblasenform
  (Größe folgt Inhalt, variierende Schräg-Ecke), Farben/Ausrichtung
  bewusst unverändert.

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

## Geplante Features

1. **Shop-System + Händler-Spam** — großes Feature-Set:
   - **Kern gebaut (22.09.2026, Backend)**: Händler-NPCs (`Person`,
     `istHaendler=true`) mit Sortiment (explizit + automatisch nach
     Spezialisierung), Standort, Kauf mit serverseitiger Guthabenprüfung —
     siehe "Zuletzt gebaut" oben und `docs/api/haendler.md`. Noch **kein
     Frontend**.
   - **KI-Sortiment-Vorschlag gebaut (23.09.2026, Backend)**: neues Modul
     `backend/app/haendler/ki_vorschlag.py`, zwei Endpunkte
     (`GET .../ki-vorschlaege`, `POST .../ki-vorschlaege/anwenden`) —
     bevorzugt bestehende Gegenstands-Vorlagen der Kampagne wiederzuverwenden,
     erfindet nur bei einer echten Lücke etwas Neues (dann als
     Ideenschmiede-Entwurf, kein Autocommit). Details siehe "Zuletzt gebaut"
     oben und `docs/api/haendler.md`. **Frontend noch offen** (SL-Popup mit
     Vorschlagsliste + Einzeln-Übernehmen-Knöpfen).
   - **Verhandeln — spezifiziert, noch nicht gebaut (23.09.2026)**: Spieler
     bekommt bei jedem Kauf-/Reparaturposten (Shop UND Rüstungsreparatur,
     außer Charaktererstellung + "online" gekauft) einen "Verhandeln"-Knopf,
     löst ein SL-Popup mit Preis + Händler-`notizen` + neuem Freitextfeld
     `moeglicheSidequests` aus, SL vergibt 5/10/15%/individuellen Rabatt nur
     für diesen einen Kauf. Kein Würfelsystem (existiert im Tool noch gar
     nicht). **Technischer Kanal existiert bereits** — kein neuer Mechanismus
     nötig: analog zum Messenger-Chat (`docs/api/kontakte.md`, Spieler→SL via
     `NACHRICHT`-Mitteilung mit `empfaengerIds=[]`), braucht nur eine neue
     Mitteilungsart mit strukturierter Nutzlast statt Freitext. Quest-System
     für Sidequest-Rabatte bewusst zurückgestellt. Volle Spec:
     `docs/api/haendler.md` Abschnitt "Verhandeln".
   - Händler-NPCs mit Warenangebot (KI-generierte Produktbilder)
   - Spieler kann "Kontakt austauschen" mit Händler
   - Händler schickt dann Werbung als **Nur-Lesen-Nachrichten**
   - **Spam-Frequenz skaliert mit I.C.E.** — niedriger Wert = mehr Spam!
   - **Popups erscheinen zufällig am Screen** (nicht immer gleiche Position)
   - Manche Spam-NPCs sind Scammer (SL-Storyline-Hooks)
   - SL kann "Spam-Welle" auslösen für Atmosphäre
   - **Kampagnen-Option** — Werbung/Spam passt nicht in jedes Setting

2. **Augment-Differenzierung** — ✅ Fertig:
   - **Hexware**: Ermöglicht Magie (Hexkraft/Sphären) — NICHT für Neuroweaver
   - **Bioware**: Ermöglicht NeuroWeaving — NICHT für Magier
   - **Cyberware**: Für alle (Reflex-Booster etc.)
   - Exklusiv-Pfade: Magier vs. Neuroweaver (nicht beides)
   - Backend-Validierung + Frontend-Fehlerpopup implementiert

3. **KI-Integration** (Gemini Pro) — mehrere Anwendungsfälle:
   - **NPC-Generator:** NPCs mit kurzer Beschreibung automatisch erstellen lassen
   - **Bildgenerierung** — ✅ **gebaut (23.09.2026)**, siehe "Zuletzt gebaut"
     oben: Provider-Abstraktion lokal (Fooocus, eigener Wrapper außerhalb
     des Repos) / cloud (Gemini `gemini-2.5-flash-image`), KI schlägt einen
     editierbaren Bild-Prompt aus Name+Beschreibung vor, Popup mit
     Vorschau vor dem Speichern — eingebunden an Person/Event/Ort/
     Fraktion/Gegenstand (SL) sowie am eigenen Charakterportrait (Spieler).
     Cloud-Pfad voll E2E verifiziert (inkl. echter Bildgenerierung), lokaler
     Pfad einmal live gegen den Fooocus-Wrapper getestet. **Offen:** kein
     echter Klicktest von `KiBildPopup.tsx` im Frontend-Dev-Server (nur
     `tsc -b` geprüft) — Mark muss das visuell gegenprüfen; der
     Fooocus-Wrapper muss von Mark manuell als Hintergrundprozess
     eingerichtet werden, sonst schlägt der "lokal"-Provider fehl.
   - **Wiki-Import** — ✅ **gebaut (23.09.2026)**, siehe "Zuletzt gebaut"
     oben: SL lädt .docx/.pdf hoch, KI teilt anhand erkannter Struktur
     (Überschriften/Kapitel) in Wiki-Seiten-Entwürfe auf inkl.
     Eltern-Kind-Hierarchie, Auto-Verknüpfung läuft pro Seite automatisch.
   - **Auto-Verknüpfung** (präzisiert 20.09.2026, Marks Wunsch; **gebaut**
     22.09.2026 — siehe "Zuletzt gebaut" oben) — KI durchsucht den
     Wiki-Seitentext und verknüpft erwähnte Personen/Orte/Events/Fraktionen
     automatisch als echte Graphkanten (nicht nur Textsuche). Existiert
     eine erwähnte Entität noch nicht, legt die KI dafür einen **Entwurf in
     der Ideenschmiede an** (Vorschlag zur Prüfung durch den SL, kein
     Autocommit in die Kampagne) und trägt die Beziehung gleich mit ein.
     Bisher nur Story-Wiki (Einzelseite); Ideenschmiede-Texte und ein Sweep
     über alle Seiten sind noch offen.
   - **Rechtschreib-/Grammatik-/Logikprüfung** (erweitert 20.09.2026,
     **gebaut** — siehe "Zuletzt gebaut" oben): Im Wiki-Editor UND in der
     Ideenschmiede — Rechtschreibung/Grammatik sowie Logik-/Konsistenz-
     fehler (Widersprüche zu bereits bestehenden Fakten im Wiki). **Auch für
     RichTextEditor-Felder gebaut (23.09.2026)** — siehe "Zuletzt gebaut" oben.
   - **Chatbot** (nice-to-have, Gag): Gegenstände mit Persönlichkeit — Decker redet mit seinem Deck, verrückter Priester redet mit seiner Bibel (und sie antwortet...)
   - **KI-Gegenstandsgenerator** (**gebaut** 23.09.2026 — siehe "Zuletzt
     gebaut" oben): dritter Ideenschmiede-Typ neben Story/Charakter
     (`typ: "gegenstand"` in `app/ki/routes.py::ki_idee`), Typ per festem
     Katalog `GEGENSTAND_TYPEN` (`app/items/schemas.py`, muss inhaltlich mit
     `frontend/src/items/typKatalog.ts` übereinstimmen) als Enum erzwungen —
     ungültige Werte fallen hart auf "Sonstiges" zurück, weil der Typ nach
     dem Anlegen nicht mehr änderbar ist. Entsteht als besitzerloser,
     SL-geheimer Entwurf wie Charakter/Story.

4. **Spotify** — ✅ Fertig (siehe `docs/api/spotify.md`). Playlist an Ort/Event,
   Wiedergabe folgt automatisch der aktiven Party. Yamaha RX-V4A/MusicCast-
   Anbindung ist NICHT mehr geplant — Mark steuert Zielgerät/Lautstärke direkt
   per Spotify Connect, das reicht (22.09.2026).

5. **Deploy** — Debian/nginx statt localhost

6. **Drei-Ebenen-Architektur: Regelsystem → Kampagne → Ideenschmiede** ✅ FERTIG

8. **KI + Critter als echte NPCs + Einfluss-System + Matrix-Attribut** — ✅ Backend + Frontend fertig:
   - **KI und CRITTER sind KEINE Begleiter-Art mehr (20.09.2026, zweifach
     revidiert)** — erst Mark: "wir machen critter zu richtigen NPCs", dann
     "mach jetzt das Gleiche für die KI". Beide sind echte `Person`-Knoten
     (`istCritter`/`istKI` in `app/entities/schemas.py`) mit dem vollen
     NPC-Charakterblatt (Attribute, Fertigkeiten, dieselbe Charaktererstellung
     wie jeder andere NPC), nicht mehr dem Drohne/Fahrzeug-Blatt. Grund: das
     Begleiter-Blatt wirkte für beide "seltsam" und beide sollten dasselbe
     Blatt wie jeder NPC bekommen. Verbindung zu ihrem Menschen läuft über
     dieselbe `BEGLEITET`-Kante wie bei Sprite/Geist, nur von Person zu
     Person (`app/entities/repository.py::critter_besitzer_setzen`/
     `ki_besitzer_setzen`, Routen `POST .../critter/{id}/besitzer` bzw.
     `.../ki/{id}/besitzer`). Eigene schlanke Listen `GET .../critter` und
     `GET .../ki` für die Begleiter-Übersicht (Name/Bild/Besitzer, nicht der
     volle Bogen). Erscheinen als eigene Kachel-Arten (Symbole ❖ Critter /
     ⌬ KI) gemischt mit den echten Begleitern in `BegleiterVerwaltung.tsx`,
     öffnen aber eigene Fenster (`CritterFenster.tsx`/`KiFenster.tsx`) mit
     dem echten `Charakterblatt` statt `BegleiterBlatt`.
   - **Matrix-Attribut für KI (20.09.2026)**: neue Trait-Kategorie
     `AttributMatrix` mit dem einen Wert **Matrix-Präsenz** (1-6, Skala wie
     jedes andere Attribut) — ersetzt bei `istKI=true` die (körperlose)
     `AttributKörperlich`-Spalte auf dem Blatt. `traits/bogen.py::
     sichtbare_kategorien` bekam dafür einen `ist_ki`-Parameter; das
     Charakterblatt wählt zwischen `ATTRIBUT_KATEGORIEN` und
     `ATTRIBUT_KATEGORIEN_KI` (`traits/bogenApi.ts`) je nach
     `bogen.person.istKI`. Mark, wörtlich zur Herkunft: "in wahrheit als
     4tes gesellschaftliches attribut, aber schreibe es dort hin wo die
     körperlichen wären" — kostet beim Steigern/bei Freebees wie ein
     Attribut (`traits/erfahrung.py`), keine eigene Erstellungs-Regel (KI
     wird direkt im Bearbeiten-Modus des Blatts aufgebaut, kein
     Rassen-/Fertigkeitspaket-Assistent — "mach direkt das Charakterblatt,
     ich glaub das ist einfacher").
   - **Einfluss läuft jetzt an der Person, nicht mehr am Begleiter**: echte
     Graphkante `(:Person)-[:HAT_EINFLUSS_AUF {stufe}]->(:Ort|:Fraktion|
     :Event|:Gegenstand)` — die SL kann einer KI im Kampf gezielt einen
     echten Ort/eine Fraktion wegnehmen (Kante löschen) statt eine
     Beschreibung zu ändern. Endpunkte: `GET/POST .../personen/{id}/einfluss`,
     `DELETE .../personen/{id}/einfluss/{zielKind}/{zielId}`, GM-only zum
     Schreiben. Frontend-Komponente von `begleiter/` nach
     `entities/EinflussVerwaltung.tsx` verschoben (Konzept hängt jetzt an
     Personen, nicht an Begleitern).
   - **Begleiter (Sprite/Geist/Begleiter) bleiben unverändert** auf dem
     Drohne/Fahrzeug-Blatt — nur KI und Critter sind herausgelöst.
   - **Erfahrung bei (echten) Begleitern**: `erfahrung`/`erfahrungAusgegeben`
     als reine Budget-Anzeige ohne Kostenrechnung — Werte bleiben frei
     einstellbar, nur Erinnerung für die SL.
   - **Bild + Beschreibung bei Begleitern (20.09.2026)**: `bildUrl`-Feld
     nachgezogen (Mark: "es gibt keine Möglichkeit ein Bild anzuhängen") —
     eigene Route `POST .../begleiter/{id}/bild`, Upload/Anzeige/Entfernen
     über `BegleiterBild.tsx` (dasselbe Muster wie `EntitaetsBild.tsx`, ohne
     Galerie). Beschreibung ist jetzt Rich-Text (TipTap) statt reinem Feld
     ohne Editor, im Bearbeiten-Fenster unterhalb der Werte speicherbar.
   - **Charakterblatt-Layout überarbeitet (20.09.2026, Mark: "man will das
     Charakterblatt sehen")**: Bild und Werte (Stufenblatt/Fertigkeiten/
     Gegenstand/Erfahrung) stehen im Bearbeiten-Fenster zuerst; selten
     gebrauchte Verwaltung (Name ändern, Art wechseln, Beziehung, Verbindung
     zur Person, Löschen) ist in einen eigenen "Verwaltung"-Abschnitt ganz
     unten verschoben.
   - **Kachelraster + Suche + Anlegen-Popup (20.09.2026)**: die Übersicht war
     noch das alte Muster (Inline-Anlegen-Formular in der Kopfzeile, kein
     Suchfeld) — jetzt wie GegenstaendeUebersicht/PartyVerwaltung: `gg-suche`
     über Name/Art/Besitzer, "+ Neuer Begleiter" öffnet ein Commlink-Popup
     mit Name, Art-Dropdown (inkl. Critter und KI — legen im Hintergrund
     jeweils einen NPC an) und durchsuchbarer Besitzer-Auswahl
     (`BesitzerAuswahl`, Radiobuttons wie bei Party statt langem `<select>`
     ohne Filter).
   - **Offen**: KI-Auto-Steigerung (Gemini/Mistral lässt NPC/Begleiter/
     Critter/KI anhand Beschreibung + bereits erlebter Events wachsen) ist
     eigenes, noch nicht begonnenes Vorhaben — braucht zuerst ein
     Party-Besuchs-Log (`WAR_AN`-Kante mit Zeitstempel), weil
     `BEFINDET_SICH_AN` beim Ortswechsel überschrieben statt historisiert
     wird und "hat die Party das Event schon erlebt" sonst nicht beantwortbar
     ist. Ein Live-Test im Browser steht noch aus (Mark prüft selbst im
     laufenden Dev-Server).

9. **Decker / Neuroweaver Skill-System** — ✅ Erweiterung auf 6 Skills **gebaut** (22.09.2026):
   - Alle 6: Brute Force, Schleichen, Daten Verarbeiten, Kompilieren, Electronic Warfare, Matrix-Navigation
   - **5. Electronic Warfare — „Rauschen"** (sinnbildlich Rauchgranate im Netz):
     rein tarnender Effekt, senkt NICHT gegnerische Verteidigung/Cyberwall,
     sondern erschwert Ortung/Erkennung der eigenen Gruppe. Eine Probe, ein
     Erfolgswert bestimmt **beides zugleich**: Radius UND Dauer (kein
     getrenntes Würfeln). Dauer ist kontextabhängig, nicht fix — in einer
     ahnungslosen Umgebung kann es eine ganze Szene halten, in einem
     kritischen Moment oft nur Sekunden, **im Kampf ist es immer ein
     einmaliger Soforteffekt**. Auffälliger als Schleichen — die Störung
     selbst ist bemerkbar, auch wenn sie tarnt.
   - **6. Matrix-Navigation** — Dinge im Netz aufspüren, auch Verstecktes.
     Eine Probe, Erfolgsstufen bestimmen die Tiefe des Fundes (Standard-Weave-
     Logik wie die anderen drei): wenige Erfolge finden Offensichtliches, mehr
     Erfolge decken verdeckte Systeme auf, genug Erfolge finden **Backdoors**
     in Host-Architekturen. Bewusst getrennt von Schleichen — Navigation
     findet den Weg, Schleichen sorgt fürs Unentdecktbleiben, keine
     Überschneidung, beide bleiben nötig.
   - Ziel: Ausgewogenes Schere-Stein-Papier-System (Angriff ↔ Verteidigung ↔ Stealth ↔ Navigation)
   - **Wer bekommt die Erweiterung (22.09.2026 entschieden):** NeuroWeaver,
     Decker UND KI — alle drei. Decker bekommen die neuen Deck-Werte
     zusätzlich zu B/S/D/K (`items/repository.py::DECK_WERTE`,
     `deckBruteForce`/`deckSchleichen`/`deckDaten`/`deckKompilieren` →
     erweitert um `deckElectronicWarfare`/`deckMatrixNavigation`). KI nutzt
     vermutlich dieselben Fertigkeiten wie ein NeuroWeaver (kein eigenes
     Gerät nötig, hat ja schon die Matrix-Präsenz statt Körper-Attribute) —
     beim Bauen gegenprüfen, ob das für KI-Charaktere so Sinn ergibt oder
     eine eigene Lösung braucht.
   - **Nachgelagert (Marks Wunsch, bewusst aufgeschoben):** Cyberdecks müssen
     noch als echte Gegenstände (`Gegenstand`-Knoten mit `typ = 'Cyberdeck'`)
     ins System eingepflegt werden — aktuell nur Referenztabelle im Wiki
     (`docs/reference/...`, Modelle wie Aztechnology Tlaloc/Tachikoma
     Prime/Hosaka Ghost), nicht als anlegbare/ausrüstbare Items in der
     Kampagne. Macht Mark später, nicht Teil dieser Erweiterung.
   - Status: **Gebaut und verifiziert** (`backend/app/traits/seed.py`
     Katalogeinträge + Beschreibungen, Cyberdeck-Werte in `items/schemas.py`/
     `repository.py`/`routes.py`). Wiki nachgezogen:
     `docs/wiki/concepts/neuroweaving-decking.md`, `docs/regeln-neotopia.md`.
     Backend-Tests grün (61 relevante Tests), `tsc -b` fehlerfrei (Frontend
     braucht keine Änderung — Probe/Kampfkarte/LevelUp iterieren generisch
     über Katalog/`deckBoni`), gegen echte Neo4j-DB verifiziert (alle 6
     TraitDefs korrekt angelegt, Max 6, sortOrder 1-6).
   - **Zwei Folgefehler beim ersten Praxistest gefunden und behoben
     (22.09.2026, Mark erstellt einen Neuroweaver "Cyborg"):**
     1. NeuroWeaving-Grundwert fehlte in der Freebee- und LevelUp-Anzeige
        (`NeuroWeavingWert` fehlte in der festen Reihenfolge in
        `Charaktererstellung.tsx`/`LevelUp.tsx`) — ergänzt.
     2. NeuroWeaving-Grundwert-Maximum war 10 (wie Hexkraft), sollte aber 6
        sein: Hexkraft wird allein gewürfelt und geht deshalb bis 10,
        NeuroWeaving wird aber immer mit einer Fertigkeit kombiniert
        (Pool-Deckel, `magie.ts::NEUROWEAVING_POOL_MAX`) — bei Max 10 hätte
        der Grundwert allein den Pool füllen können. Auf 6 gesenkt.
   - **Drei weitere Fixes, gleicher Praxistest (22.09.2026):**
     3. NeuroWeaving-Grundwert fehlte auch im Charakterblatt selbst (nicht
        nur bei Freebees/LevelUp) — `reihe("NeuroWeavingWert")` fehlte in
        `Charakterblatt.tsx`, ergänzt.
     4. Probenauswahl bei NeuroWeaving verlangte einen Pflichtklick ohne
        echte Wahl (nur ein möglicher Partner: der Grundwert selbst) —
        `Probe.tsx` wählt jetzt automatisch vor, wenn genau ein Kandidat
        existiert.
     5. "Wilde Magie" bei NeuroWeaving in **"Overclock"** umbenannt (war
        Copy-Paste-Rest, passte inhaltlich nicht) — gleiche Mechanik
        (Bonuswürfel bis Willenskraft, Zielwert vorher ansagen, Rückstoß-
        Willenskraftwurf bei Erfolg), neuer Name in `magie.ts`
        (`MAGIE_HINWEISE.overclock`/`.overclockRueckstoss`), `Probe.tsx` und
        `WillenskraftFrage.tsx`.
   - **Pool-Deckel 10 → 12** (22.09.2026, Mark: "wirkt das natürlicher"
     seit überall 6 das neue Skill-Maximum ist): `NEUROWEAVING_POOL_MAX` in
     `magie.ts`, dazu zwei hartkodierte `10`en in `Kampfkarte.tsx` durch die
     Konstante ersetzt (waren vorher nicht synchron mit `Probe.tsx`). Wilde
     Magie bleibt bewusst ohne Pool-Deckel — andere Ausgangslage (ein Wert
     allein bis 10 + Rückstoß-Risiko als Bremse statt Zahlenlimit).

   **Backend (2026-09-12):**
   - `:Regelsystem` Node-Typ mit CRUD-Endpunkten (`/api/regelsysteme`)
   - `(:Campaign)-[:NUTZT_REGELSYSTEM]->(:Regelsystem)` Beziehung
   - `istEntwurf: bool` auf Person, Ort, Event, WikiSeite, Gegenstand
   - NeotopiA wird beim Start automatisch angelegt

   **Frontend (2026-09-12):**
   - Neuer Tab "Schmiede" (🔧) in der Commlink-Shell
   - Zeigt alle Entwürfe mit Filter nach Typ
   - "Neue Idee" legt direkt Entwürfe an (Person, Ort, Event, Wiki, Gegenstand)
   - "✓ Übernehmen" verschiebt in die Kampagne (setzt istEntwurf=false)
   - "✗" löscht den Entwurf

   **Offen:**
   - PC-Vorlagen im Regelsystem (Phase 2)
   - KI-Import in Ideenschmiede (braucht KI-Integration)

   ```
   ┌─────────────────────────────────────────────────────┐
   │  REGELSYSTEM (:Regelsystem)                         │
   │  z.B. "NeotopiA", "D&D 5e", "WoD"                   │
   │  ├── Regel-Wiki (Kampf, Magie, Proben...)           │
   │  ├── Rassen, Sphären, Hexkraft-Stufen               │
   │  ├── Preislisten, Standard-Ausrüstung               │
   │  └── PC-Vorlagen (vorgefertigte Charaktere)         │
   │      → Spieler kann wählen ODER selbst bauen        │
   └─────────────────────────────────────────────────────┘
              │ :NUTZT_REGELSYSTEM
              ▼
   ┌─────────────────────────────────────────────────────┐
   │  KAMPAGNE (:Campaign)                               │
   │  z.B. "Berlin 2087", "Tokyo 2090"                   │
   │  ├── Story-Wiki (istEntwurf: false)                 │
   │  │   → NPCs, Orte, Events dieser Kampagne           │
   │  └── Ideenschmiede (istEntwurf: true)               │
   │      → WikiSeiten, NPCs, Orte, Gegenstände          │
   │      → KI-generiert oder manuell                    │
   │      → "In Kampagne verschieben" = Flag toggle      │
   └─────────────────────────────────────────────────────┘
   ```

   **Regelsystem:**
   - Anlegen durch SL oder KI-Import (z.B. aus Regelwerk-PDF)
   - Enthält alles was für ALLE Kampagnen dieses Systems gilt
   - Mehrere Kampagnen können dasselbe Regelsystem nutzen
   - PC-Vorlagen: "Straßensamurai", "Netrunner", "Kampfmagier"...

   **Kampagne:**
   - Verknüpft mit genau einem Regelsystem
   - Story-Wiki: Die "echten" Inhalte die im Spiel existieren
   - Ideenschmiede: Entwürfe, Ideen, KI-Output — noch nicht kanonisch

   **Ideenschmiede (pro Kampagne):**
   - Flag `istEntwurf: true` auf WikiSeiten, Personen, Orten, Gegenständen
   - KI-generierte Inhalte landen hier zur Prüfung
   - SL kann bearbeiten, dann "In Kampagne verschieben"
   - Verschieben = nur Flag toggle, keine Datenmigration

   **PC-Erstellung / Ersteinstieg — ✅ gebaut (23.09.2026):**
   - Spieler-Account ohne `personId` sieht statt der vollen Commlink-Hülle
     `frontend/src/players/SpielerEinstieg.tsx` und wählt: "Selbst
     erstellen" (`POST /api/spieler/charakter-neu`, legt sofort einen
     leeren PC an, danach greift die normale Charaktererstellung) ODER
     "Vorgefertigten Charakter wählen" (`GET /api/spieler/vorgefertigte` +
     `POST /api/spieler/charakter-waehlen`, atomare Zuweisung eines
     bestehenden, noch niemandem zugeordneten abgeschlossenen PCs). Details
     siehe "Zuletzt gebaut" oben. Ein "vorgefertigter PC" ist bewusst kein
     eigenes Datenfeld — sondern schlicht ein PC ohne `SPIELT`-Kante.
   - Nicht (mehr) aus dem Regelsystem selbst, sondern aus bestehenden
     Kampagnen-PCs — die ursprünglich angedachten separaten Regelsystem-
     Vorlagen sind damit hinfällig.

7. **Rüstungssystem** — ✅ Fertig (10.09.2026, Reduktion statt Durchlass seit
   18.09.2026), siehe `docs/api/ruestung.md`:
   - **Zwei Werte pro Rüstung:** Kästchen (was sie aushält) + **Reduktion**
     (wie viel Schaden sie pro Treffer abfängt — höher ist besser; hieß
     vorher "Durchlass" mit umgekehrter Bedeutung, von Mark nach dem
     Praxistest verworfen: *"Durchlass ist ein dummer Wert"*)
   - **Abgestuft statt geblockt:** Unheilbar→Tödlich→Schlag, Schlag wird
     zusätzlich halbiert (unterste Stufe, kein weiteres Abstufen möglich)
   - **Kästchenschaden:** Unheilbar/Tödlich anteilig aus Absorbiert+Durchkommend,
     Schlag nur ab der Hälfte der aktuellen Kästchen (Trigger)
   - **Je kaputter, desto schlechter:** die effektive Reduktion sinkt gestuft
     mit dem Kästchen-Anteil (>50% voll, >25% halb, sonst ein Viertel) — kein
     eigener "Aktuell"-Wert mehr nötig, dadurch auch keine Paradox-Gefahr mehr
   - **Kumulierte Rüstung:** alles Getragene ist ein Pool (Kästchen summiert,
     Reduktion vom Teil mit der besten Basis); aufgebraucht wird die beste
     Reduktion zuerst, zerstörte Teile fliegen aus der Ausrüstung. Keine Körperzonen
   - **Offen:** Reparatur-Endpoint rechnet nur das Ergebnis, keine
     Hardware-Skill-Probe, kein Händlerpreis (braucht Skill-Check- bzw.
     Shop-System, siehe Punkt 1 und 8)

8. **Augment-Preisstufen:**
   - **Cyberware:** alle Stufen (Hinterhof 500¥ bis Maßanfertigung 20.000¥)
   - **Bioware & Hexware:** erst ab Klinik (5.000¥+) — kein Hinterhof-Doc kann das!
   - **Offen — Willenskraft-Overkill:** Was passiert beim totalen Minmaxer?
     - Basis 2 (Entschlossenheit 1 + Fassung 1)
     - +10 Freebees → 12
     - Chrom kaufen bis runter auf 2
     - +10 EP natürlich → 22
     - Chrom-Attributboni (Entschl. + Fassung auf 6) → theoretisch 30+?
     - Aber mehr Chrom = mehr Verlust... Teufelskreis?
     - **Lösung: "Wer soweit kommt, hat's verdient"** — kein Cap!

9. **Kästchen-Overflow-Darstellung** — ✅ Fertig (Puffer+Enden-Leiste,
   `frontend/src/traits/Kaestchen.tsx`), **18.09.2026 drei Fehler behoben:**
   - **Füllrichtung war uneinheitlich:** Gesundheit (Schadensarten) füllte
     von Index 0 (Puffer zuerst), Willenskraft/I.C.E. (`verbraucht`) aber von
     hinten (Enden-Kästchen zuerst) — beide füllen jetzt von vorne
   - **Rüstungs-Umgehung im Charakterblatt:** die Gesundheitsleiste öffnete
     ein Zahlenpad, das Schaden direkt einträgt und dabei die Rüstung
     komplett umgeht. Schaden geht jetzt nur noch über „⚡ Treffer eintragen“
     (`RuestungsTreffer`), das Zahlenpad ist für Gesundheit gesperrt
     (`ZustandFenster` neues Prop `schadenErlaubt`)
   - **Willenskraft-Rückfrage fehlte ab 11 Kästchen:** ab `OVERFLOW_AB`
     kippt die Leiste zum Öffnen-Knopf, und das Zahlenpad im Fenster kannte
     die Willenskraft-Sonderregeln (1 auf einmal, Rückfrage, Spieler kann
     nicht heilen) nicht — ein Charakter mit z.B. Willenskraft 22 bekam nie
     die Rückfrage, einer mit 5 schon. Zahlenpad für Willenskraft jetzt
     ebenfalls gesperrt, echter `willenskraftWeiterschalten`-Handler auch in
     der Vollansicht durchgereicht
   - **Rüstungstreffer hatte noch die alte Optik** (rohes
     `<input type="number">` mit Systemtastatur statt Zahlenpad) — Mark
     selbst am System gefunden. Zahlenpad aus `ZustandFenster.tsx` nach
     `frontend/src/shell/Zahlenpad.tsx` extrahiert, jetzt von beiden
     Fenstern verwendet
   - Details: `docs/wiki/concepts/attribute-und-fertigkeiten.md`

10. **KI-Chatbots für Gegenstände** — Zwei Typen:
   - **Einfacher Chatbot** (Bibel, Teddybär, etc.):
     - Spam-Popups (zufällig + kontextabhängig nach Schaden/Kampf)
     - Chat-Button am Gegenstand für direktes Gespräch
     - Sieht Kampf-Status (Initiative) für akkurate Kommentare
     - *"Beim nächsten Mal weichst du besser aus..."*
   - **Fortgeschrittener Chatbot** (Decker's Deck):
     - Eigenes Matrix-Menü im Burgermenü (grün-schwarz)
     - Zugriff auf eigene Stats, Gegenstände, Infos
     - **Kann hacken/scannen** — aber Probe erforderlich!
     - Flow: Deck fragt → Spieler würfelt → Deck reagiert auf Erfolg/Misserfolg
   - **Persönlichkeit:** Freitext-Feld am Gegenstand
     - KI-generierte Gegenstände bringen Persönlichkeits-Vorschläge mit
     - Beispiele: "mürrischer alter Mann", "glaubt er ist ein Gott", "übertrieben hilfsbereit"
   - **Sprachausgabe auf Spieler-Tablets!** 🔊
     - ElevenLabs: Beste Qualität, versteht Stil-Prompts ("klingt wie alter Mann")
     - Edge TTS: Kostenlos, gute Qualität, viele Stimmen
     - **Hybrid:** Edge für Standard, ElevenLabs für wichtige Momente
     - Gegenstände reden WIRKLICH mit den Spielern!

11. **Charakterportrait im Spieler-Menü** — MVP **gebaut** (22.09.2026):
    - **Zwei der vier geplanten Optionen umgesetzt** (mit Mark als MVP-Scope
      geklärt): Bild hochladen + Foto per Kamera (`capture="environment"`
      am `<input type="file">`, fällt am Desktop ohne Kamera automatisch auf
      normale Dateiauswahl zurück). **KI-Bildgenerierung** kam am
      23.09.2026 als dritter Weg dazu (siehe Löschen-Eintrag unten und
      "Zuletzt gebaut" oben). **Offen, bewusst nicht Teil dieser Fassung:**
      Zeichentool.
    - **Neue Route `POST /api/spieler/mein-bild`** (`app/players/routes.py`)
      — bewusst OHNE `require_campaign_gm`, einzige Bild-Upload-Route im
      Projekt, die nicht GM-only ist: der Spieler darf nur sein **eigenes**
      zugeordnetes `Person`-Bild setzen (`spieler["personId"]` aus dem
      JWT-Claim, kein Pfad-Parameter für die Person-ID). Schreibt auf
      dasselbe `bildUrl`-Feld wie der SL-Upload (`entities/routes.py::
      _entitaets_bild_hochladen`), gleicher Upload-Ordner
      (`uploads/<campaign_id>/`), eigener Dateipräfix `portrait-` statt
      `personen-`.
    - `SpielerMeResponse` bekam `personBildUrl` (Backend liefert es über
      `p.bildUrl AS personBildUrl` in `finde_spieler`/`get_spieler`,
      `players/repository.py`).
    - **Eigener Burger-Menü-Punkt statt Popup über dem Blatt** (Mark,
      22.09.2026, Korrektur nach dem ersten Wurf: "damit im Charakterblatt
      mehr Platz ist" — das Blatt wächst je nach Chartyp schon mit
      zusätzlichen Skills/Werten). Frontend:
      `players/CharakterportraitAnsicht.tsx` — eigener statischer Bereich
      `{ id: "portrait", symbol: "◒" }` in `BEREICHE_STATISCH`
      (`SpielerAnsicht.tsx`), direkt nach dem Charakterblatt-Eintrag, kein
      Popup-Fenster mehr nötig.
    - Verifiziert: `tsc -b` fehlerfrei, End-to-End gegen echte Neo4j-DB
      (Spieler-Login → Bild-Upload → `GET /api/spieler/me` zeigt die neue
      URL, Testdaten wieder entfernt).
    - **Löschen-Button ergänzt (23.09.2026)** — „✕ Entfernen“ neben den
      Upload-Knöpfen (nur sichtbar, wenn schon ein Bild gesetzt ist), fragt
      per `Bestaetigung`-Dialog nach, dann `DELETE /api/spieler/mein-bild`
      (`players/routes.py::eigenes_charakterportrait_entfernen`) — setzt
      `bildUrl` zurück, Datei bleibt wie beim SL-Pendant auf dem
      Datenträger liegen.
    - **KI-Bildgenerierung ergänzt (23.09.2026)** — dritter Weg neben
      Datei-Upload und Kamera: `KiBildPopup` in
      `players/CharakterportraitAnsicht.tsx` eingebunden
      (`POST /api/spieler/mein-bild-ki-prompt` + `/mein-bild-ki`, siehe
      "Zuletzt gebaut" oben). Damit sind jetzt **alle** MVP-Wege
      vollständig; nur das Zeichentool bleibt offen.

12. **Steckbrief nachträglich bearbeiten** — ✅ erledigt (22.09.2026).
    Konzept, Ambition, Verlangen und Ziel lassen sich jetzt über einen
    "✎ Bearbeiten"-Knopf in der Kopfzeile des Charakterblatts ändern, nicht
    mehr nur bei der Erstellung. Backend: `PATCH .../personen/{id}/steckbrief`
    (traits/routes.py), gleiches Muster wie `zustand` — Spieler nur am
    eigenen Charakter, Spielleitung überall. Frontend: `SteckbriefFenster` in
    `Charakterblatt.tsx`, Commlink-Popup mit demselben Vorschläge-Knopf
    (Archetypen) wie in der Erstellung. Alter bleibt bewusst read-only.

13. **Handy-Ansicht für Story-Wiki + Ideenschmiede** (notiert 20.09.2026, Editor-Teil ✅ 20.09.2026, Rest ✅ 24.09.2026 nachts) —
    Mark will auch unterwegs (ohne Laptop) an seinen Geschichten
    weiterschreiben. Beide Bereiche brauchen eine mobil taugliche Ansicht
    (Editor, Seitenbaum/Kachel-Übersicht, Verweis-Auswahl).
    
    **Gebaut (20.09.2026):** Editor-Text am Handy lesbar — unter 600px kriegt
    `.wk-editor .ProseMirror` 18px/1.6 (Überschriften 26/21/18px), bewusst
    nur der Editor selbst, nicht Baum/Werkzeugleiste. `frontend/src/wiki/
    wiki.css` neu hinzugefügt. Rein clientseitig, kein neuer Endpunkt.

    **Gebaut (24.09.2026, nachts):** Seitenbaum + Inhaltsverzeichnis als
    echtes Slide-in-Drawer mit Backdrop und Schließen-Knopf (vorher nur
    Ein-/Ausblenden ohne Overlay-Fläche), Ideenschmiede-Kachelraster mit
    größeren Touch-Zielen (nur die Wiki-eigene Ansicht, nicht die generische
    `gg-raster`-Komponente), Verweis-Auswähler mit sticky Suchfeld + größeren
    Trefferzeilen. Details siehe „Zuletzt gebaut" oben. **Kein Browser-Test**
    (Netzwerksperre der Session verhinderte DevTools-Mobil-Emulation), nur
    `tsc -b` — Mark muss am echten Handy gegenprüfen, siehe „Offen" oben.

14. **Flavor-Option „Priester" (notiert 23.09.2026, offene Idee, nicht begonnen)** —
    alternatives Namens-Reskin für Magier-Charaktere: Hexkraft → Glaube,
    Wilde Magie → Blasphemie, die Sphären umbenannt auf Götter/Domänen
    (bestehende und eventuell neu erfundene). Reine Flavor-/Anzeige-Ebene,
    keine neue Mechanik — Regeln/Werte bleiben identisch zu Hexkraft, nur
    Beschriftung ändert sich für diesen Charaktertyp. Noch zu klären: wie
    die Umbenennung technisch je Charakter greift (globaler Schalter vs.
    pro Person) und welche Sphären welchen Göttern entsprechen.
