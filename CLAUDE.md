# PnPTool — Projektgedächtnis für Claude

Diese Datei wird von Claude Code automatisch geladen, sobald in diesem Ordner gearbeitet wird (egal von welchem Gerät/welcher Session aus). Sie ist die Quelle der Wahrheit für den Projektstand — bitte bei jeder größeren Änderung aktualisieren, damit parallele Sessions (z.B. Desktop + Handy) synchron bleiben.

## Was ist PnPTool

WebApp für Mark's Pen-and-Paper-Rollenspielrunden, Homebrew-System **"NeotopiA"** (WoD-artige Attribute/Fähigkeiten, Shadowrun-Cyberware/Rigging/Drohnen, Mage-Sphären, Cyberpunk-Setting). Referenzmaterial: `docs/reference/Neotopia.xlsx` (Charakterblatt, Drohne/Fahrzeug, komplettes Regelwerk inkl. GM-only "SL Ideen Gadgets"-Abschnitt).

Zwei Nutzerrollen:
1. **Spielleiter (GM)** — plant Kampagnen als **Beziehungsgraph**: Personen, Orte, Events mit typisierten Verbindungen zueinander (wer kennt wen, wer war wo, was geschah wann). Manche Inhalte sind strukturell immer GM-geheim (z.B. NPC-Hintergedanken).
2. **Spieler** — eigene interaktive Charakterbögen (Dot-Pool-Attribute/Fähigkeiten, Box-Tracks für Gesundheit/Willenskraft), Live-Pop-ups vom SL während der Session (noch nicht gebaut).

Der volle Plan (Architektur-Entscheidungen, Datenmodell, Phasen-Roadmap) liegt hier: `C:\Users\Mark\.claude\plans\gut-pnp-steht-f-r-temporal-waterfall.md` — bei Bedarf dort nachlesen, diese Datei hier ist die kompaktere Zusammenfassung + laufender Status.

## Tech-Stack (entschieden, nicht neu diskutieren)

- **Backend**: FastAPI (async), `neo4j` async driver, JWT in httpOnly-Cookie, `bcrypt` direkt (NICHT passlib — siehe "Bekannte Stolpersteine" unten)
- **Datenbank**: Neo4j 5 Community Edition, läuft in Docker
- **Frontend**: React 19 + TypeScript + Vite, Cytoscape.js **direkt** (nicht der `react-cytoscapejs`-Wrapper — siehe unten)
- **Auth**: GM hat echten Login (Username/Passwort). Spieler-Zugang (Zugangscode/Link) ist noch nicht gebaut (Phase 4)
- **Deployment-Ziel**: später Debian-Heimserver hinter nginx, aktuell Windows-Dev-Maschine. Docker Desktop ist installiert (WSL2-Backend)

## Projektstruktur

```
C:\DEV\PnPTool\
├── CLAUDE.md                 ← diese Datei
├── docker-compose.yml        (neo4j + backend + frontend Services)
├── .env.example               (kopieren zu .env falls von Defaults abgewichen werden soll)
├── docs/reference/Neotopia.xlsx
├── backend/
│   ├── .venv/                 (lokales Python venv, NICHT in git)
│   ├── pyproject.toml
│   ├── scripts/create_gm.py   (CLI zum Anlegen von SL-Accounts)
│   └── app/
│       ├── main.py            (FastAPI app + Router-Includes + Migrations beim Start)
│       ├── config.py          (pydantic-settings, liest .env falls vorhanden)
│       ├── db/                (neo4j_driver.py, migrate.py, migrations/001_constraints.cypher)
│       ├── auth/               (security.py=bcrypt+JWT, dependencies.py=require_gm/require_campaign_gm, routes.py, repository.py)
│       ├── campaigns/          (routes.py, repository.py inkl. campaign_owned_by Ownership-Check)
│       ├── entities/           (Personen/Orte/Events/Verbindungen CRUD — routes.py, repository.py, schemas.py)
│       └── graph/               (routes.py, repository.py — GET .../graph?focus=&depth= für Cytoscape-JSON)
└── frontend/
    └── src/
        ├── api/client.ts        (fetch-Wrapper mit credentials:include)
        ├── auth/                 (AuthContext, GmLoginPage)
        ├── campaigns/useCampaign.ts
        ├── entities/             (api.ts, EntityManager.tsx — Listen+Formulare für Personen/Orte/Events/Verbindungen)
        ├── graph/                (api.ts, CampaignGraphView.tsx — Cytoscape-Graph-Ansicht)
        └── App.tsx               (Tab-Umschalter Liste/Beziehungsgraph)
```

**Kein git-Repo bisher.** Für paralleles Arbeiten von mehreren Geräten wäre ein Git-Remote (GitHub o.ä.) sinnvoll — noch nicht eingerichtet, auf Wunsch nachholen.

## Wie man lokal startet

```powershell
# 1. Neo4j (falls Container nicht schon läuft — meist läuft er durchgehend im Hintergrund)
cd C:\DEV\PnPTool
docker compose up -d neo4j
# Neo4j Browser: http://localhost:7474  (Auth: neo4j / changeme — Compose-Defaults, kein .env vorhanden)

# 2. Backend (aus backend/.venv, kein --reload verwenden, siehe Stolpersteine unten)
cd C:\DEV\PnPTool\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# http://localhost:8000/api/health sollte {"status":"ok"} liefern

# 3. Frontend
cd C:\DEV\PnPTool\frontend
npm run dev
# http://localhost:5173
```

**Falls die venv fehlt:** `python -m venv .venv` im `backend/`-Ordner, dann `.\.venv\Scripts\python.exe -m pip install -e .`

**Test-GM-Account** (bereits angelegt in der laufenden Neo4j-Instanz): `sl` / `test-passwort-123`
Weiteren Account anlegen: `.\.venv\Scripts\python.exe scripts\create_gm.py --username X --password Y`

**Test-Kampagne** "Neotopia Testkampagne" (id `71dc452c-6c45-4a18-aec5-24815d161053`) enthält Demo-Daten: Kira Voss (Person, spieler-sichtbar), Mr. Chrome (Person, SL-geheim), Neon Alley Bar (Ort), "Der Deal geht schief" (Event), plus 3 Verbindungen zwischen ihnen — zum Testen der Graph-Ansicht.

## Stand der Umsetzung

- ✅ **Phase 1** — Grundgerüst: Docker-Compose, Neo4j-Constraints, FastAPI-Skeleton, GM-Login (JWT-Cookie), React-Grundgerüst
- ✅ **Phase 2a** — Backend-CRUD (Personen/Orte/Events/generische `VERBINDUNG`-Relationships) + Frontend-Listen/Formulare
- ✅ **Phase 2b** — Cytoscape-Graph-Ansicht: `GET /api/campaigns/{cid}/graph?focus=&depth=` liefert Cytoscape-JSON (voller Graph oder BFS-begrenzte Nachbarschaft), Frontend zeigt Personen/Orte/Events als farbige Knoten, Klick fokussiert auf Nachbarschaft. Cytoscape-Canvas-Offset-Bug (Stolperstein #8) gefunden, gefixt und vom Nutzer live am Handy bestätigt — Phase 2 damit komplett.
- ✅ **UI-Polish-Durchgang (28.08.2026)** — siehe eigener Abschnitt unten, ersetzt die alte binäre Sichtbarkeit + fügt Rich-Text-Editor hinzu
- ⬜ **Phase 3** — Spieler-Charakterbogen CRUD (Dot-Pools, Box-Tracks, Würfeln)
- ⬜ **Phase 4** — Zugangscode/Link-Beitritt für Spieler, Charakter beanspruchen. **Wichtig:** die Sichtbarkeits-Filterung (`entities/visibility.py`) ist bereits fertig und getestet, aber in KEINE Route eingebaut — es gibt noch keine Spieler-Route, die `viewer_role="PLAYER"` überhaupt übergibt. Das ist der erste Schritt in Phase 4: eine Spieler-Version der `entities`-Routen (oder ein Query-Param/Claim am bestehenden Endpoint), die `filter_entities_for_viewer`/`filter_verbindungen_for_viewer` tatsächlich aufruft.
- ⬜ **Phase 5** — Live-WebSocket-Pop-ups vom SL an Spieler
- ⬜ **Phase 6+** — optionaler echter Spieler-Account, Debian/nginx-Deploy, Google Gemini API Integration (Mark hat Gemini Pro Account) für Regel-Chatbot/kreative Item-Ideen — noch unspezifiziert

## UI-Polish-Durchgang (28.08.2026) — Sichtbarkeit v2 + Rich-Text

Ausgangspunkt: Mark wollte (a) Sichtbarkeit nicht nur GM/Alle sondern auch "nur bestimmte Spieler", (b) Text-Abschnitte *innerhalb* eines Feldes vor Spielern verstecken können (nicht nur ganze Felder), ohne dass ein Spieler-Edit den GM-Text kaputt macht, (c) Tabellen für den künftigen Regel-Bereich, (d) eine kleine Weiche für später weitere Regelsysteme (Splittermond, D&D) neben dem aktuellen Neotopia-Homebrew.

**Umgesetzt:**
- `Campaign.ruleset` (String, Default `"neotopia"`) — noch keine Logik verzweigt darauf, ist nur die Vorbereitung. Fähigkeits-Kataloge (`TraitDef`, kommt in Phase 3) sollten pro Ruleset gescoped werden, nicht global.
- Sichtbarkeits-Datenmodell v2: statt einem binären `sichtbarkeit: GM|SPIELER` jetzt `sichtbarkeit: GM|ALLE|SPEZIFISCH` + `sichtbarFuer: string[]` (Person-IDs, nur bei SPEZIFISCH). Getrennt für Haupt-Inhalt (`sichtbarkeit`/`sichtbarFuer`) und Notizen (`notizenSichtbarkeit`/`notizenSichtbarFuer`) — auf Person, Ort, Event UND Verbindung (Verbindung hat nur eine Sichtbarkeits-Ebene, keine separaten Notizen).
- `backend/app/entities/visibility.py`: `filter_entity_for_viewer`/`filter_verbindungen_for_viewer` — server-seitige Durchsetzung, inkl. **inline-Redaktion**: `redact_rich_text()` parst das TipTap-JSON-Dokument und entfernt Text-Knoten mit dem `gmSecret`-Mark, bevor es an einen Nicht-GM-Viewer geht. GM bekommt immer die rohe, unredigierte Version. Per Unit-Test + curl-Roundtrip verifiziert (siehe Stolperstein-Abschnitt falls es nochmal kaputtgeht).
- Frontend: `description`/`notes` sind jetzt Rich-Text (TipTap, gespeichert als JSON-String in denselben String-Feldern wie vorher — Backend-Schema dafür unverändert, nur die Konvention des Inhalts). Editor unter `frontend/src/richtext/` (`RichTextEditor.tsx` fürs Bearbeiten, `RichTextView.tsx` fürs Anzeigen, `GmSecretMark.ts` = die "🔒 SL-geheim"-Markierung wie Fett/Kursiv, `content.ts` = Parsing mit Rückwärtskompatibilität für alte Klartext-Strings). Tabellen-Extension ist mit drin (Toolbar-Button "▦ Tabelle").
- `frontend/src/entities/VisibilitySelector.tsx`: wiederverwendbare 3-stufige Sichtbarkeits-Auswahl, bei SPEZIFISCH Mehrfachauswahl aus den PC-Personen der Kampagne.
- `EntityManager.tsx` komplett überarbeitet: größere Formulare, Notizen-Feld ergänzt (fehlte vorher komplett in der UI), jede Entität hat jetzt zwei Sichtbarkeits-Einstellungen (Beschreibung + Notizen) sichtbar als Badges in der Liste.
- Bestandsdaten in der Testkampagne wurden per Einmal-Migration (Cypher, nicht als Code hinterlegt — siehe Git-Historie falls nötig) von altem `GM`/`SPIELER` auf `GM`/`ALLE` + neue Felder mit Defaults migriert.

**Nicht gemacht / bewusst zurückgestellt:**
- Multi-Ruleset ist nur die Weiche (ein String-Feld), kein echtes pluggable System — Würfelmechanik/Regelwerk-Engine ist ein Splittermond/D&D-Projekt für später.
- Die Redaktions-Logik ist fertig, aber **ungenutzt** bis Phase 4 eine Spieler-Route hat (siehe oben).
- Cytoscape-Graph-Ansicht zeigt weiterhin nur zweistufig GM(rot)/nicht-GM(grau) als Kantenfarbe — SPEZIFISCH sieht optisch wie ALLE aus. Kann man später verfeinern, war kein Teil dieses Durchgangs.

## Bekannte Stolpersteine (nicht nochmal reinlaufen)

1. **`passlib` + neueres `bcrypt`**: inkompatibel (passlib ist unmaintained, `bcrypt>=4.1` hat `__about__` entfernt). Lösung: `bcrypt`-Paket direkt nutzen, kein passlib. Ist bereits so umgesetzt in `auth/security.py`.
2. **`uvicorn --reload` auf Windows**: der Reloader-Parent-Prozess kann sterben während der Worker-Kind-Prozess weiterläuft und alten Code weiter serviert (WatchFiles-Bug/Windows-Eigenheit). Wenn nach einem Reload etwas nicht wie erwartet reagiert: beide PIDs (Parent + Worker, `netstat -ano | grep :8000` dann `taskkill //F //PID X`) killen und ohne `--reload` neu starten.
3. **`react-cytoscapejs`-Wrapper**: hatte einen Bug — rief bei jedem Re-Render ein Re-Layout auf und verlor dabei den Klick-Handler. Komplett entfernt, Cytoscape wird jetzt direkt (imperativ, via `useRef`) angesteuert in `graph/CampaignGraphView.tsx`.
4. **Cytoscape + `box-sizing`**: Cytoscape hat einen eingebauten `ResizeObserver` auf dem Container. Ohne globales `box-sizing: border-box` (jetzt in `index.css` gesetzt) addiert sich ein `border` zur `width:100%`-Breite dazu → minimaler Overflow → Scrollbar erscheint/verschwindet → ResizeObserver feuert erneut → Endlosschleife, die sich sichtbar "aufschaukelt" (Container wächst langsam immer weiter). Fix: globales `box-sizing: border-box` + Cytoscape-eigenen Resize nicht durch einen zweiten, redundanten manuellen Call stören.
5. **Cytoscape Initial-Messung zu früh**: Falls der Container beim `cytoscape({container:...})`-Aufruf noch nicht final gelayoutet ist (z.B. direkt nach Tab-Wechsel), kann die interne Erstmessung falsch/zu klein ausfallen und bleibt es auch (Canvas nur "halb" befüllt, Klick-Koordinaten verschoben). Fix: `requestAnimationFrame` nach Konstruktion, das explizit `cy.resize()` + `cy.fit()` erzwingt, nachdem der Browser das Layout tatsächlich committed hat. War hier lange nur als Plan dokumentiert, aber nie tatsächlich im Code umgesetzt (Diskrepanz erst beim Debuggen von Stolperstein #8 aufgefallen) — jetzt in `CampaignGraphView.tsx` als doppeltes `requestAnimationFrame` + `window`-`resize`-Listener implementiert.
6. **TypeScript + `verbatimModuleSyntax` + `@types/cytoscape`**: der `type Stylesheet = A | B` Union-Alias aus dem `export =`-Namespace lässt sich unter `verbatimModuleSyntax` nicht als `cytoscape.Stylesheet` referenzieren (TS-Fehler "no exported member"), obwohl er existiert — vermutlich weil `type`-Aliase (im Gegensatz zu `interface`s) beim Namespace-Merge über einen Default-Import unter dieser strikten Einstellung nicht sauber aufgelöst werden. Workaround: das nominale `interface StylesheetStyle` statt des Union-`type Stylesheet` referenzieren, funktioniert identisch für unseren Anwendungsfall.
7. **Vite Hot-Reload + Cytoscape**: bei größeren Änderungen an Komponenten, die eine imperative Canvas-Bibliothek verwenden, lieber den Dev-Server komplett neu starten (`node_modules/.vite`-Cache löschen) statt sich auf HMR zu verlassen — HMR kann alte Instanzen hinterlassen, die mit neuen um denselben Container konkurrieren.
8. **Cytoscape-Canvas verschoben durch `text-align: center`**: `index.css` setzt global `#root { text-align: center; }`. Cytoscapes interne `<canvas>`-Layer sind `position: absolute` mit `left`/`right: auto` (Cytoscape selbst setzt nie ein explizites `left`). Bei `left/right: auto` berechnet der Browser die "static position" eines ursprünglich inline-artigen Elements (canvas ist von Haus aus `display: inline`) unter Berücksichtigung des geerbten `text-align` — bei `center` verschiebt das die komplette Canvas nach rechts um ungefähr die halbe Canvas-Breite (reproduzierbar auf jedem Gerät mit `devicePixelRatio != 1`, unabhängig von Bildschirmgröße). Symptom: linke Hälfte des Graphen leer/schwarz, Klick-Koordinaten um denselben Betrag versetzt. War der Bug hinter dem lange als "Graph-Sizing-Bug" verfolgten Problem — **nicht** der ursprünglich vermutete `box-sizing`/`ResizeObserver`- oder `pixelRatio`-Bug. Gefunden per Headless-Browser-Debugging (`cy.pan()`/`cy.zoom()`/Node-Positionen waren intern korrekt — nur das `<canvas>`-DOM-Element selbst war falsch positioniert). Fix: `textAlign: "left"` explizit auf dem Graph-Container in `CampaignGraphView.tsx` setzen (überschreibt lokal das geerbte `center`, ohne die globale Zentrierung zu ändern).

## Nächste Schritte

1. Nutzer bestätigt den UI-Polish-Durchgang im Browser (Rich-Text-Editor, SL-geheim-Markierung, Sichtbarkeits-Auswahl, Tabellen) — noch nicht visuell bestätigt, nur backend-seitig und per Build durchgetestet
2. Danach: Phase 3 (Spieler-Charakterbogen) — dabei `TraitDef`-Katalog gleich pro `ruleset` scopen, nicht global
3. Vor Phase 4: die Sichtbarkeits-Filterung tatsächlich in eine Spieler-Route einbauen (Funktionen sind fertig, siehe oben)

**Server-Status:** Backend läuft auf `0.0.0.0:8000` (ohne `--reload`, siehe Stolperstein #2), Frontend mit `npm run dev` (hat `host:true` fest in `vite.config.ts`, kein `--host`-Flag mehr nötig) auf Port 5173. Neo4j läuft durchgehend in Docker. Falls nach einem Reboot/Neustart nichts erreichbar ist: siehe "Wie man lokal startet" oben.

## Zugriff vom Handy / LAN (eingerichtet, für Tests unterwegs)

Frontend (Vite) läuft mit `--host`, ist also im LAN erreichbar unter `http://192.168.178.21:5173` (Andromedas Ethernet-IP). Backend bleibt bewusst nur auf `127.0.0.1:8000` (kein Firewall-Zugriff nötig/gewünscht) — API-Calls laufen stattdessen über Vites Dev-Proxy (`vite.config.ts` → `server.proxy["/api"]`) auf denselben Port 5173. `frontend/src/api/client.ts` nutzt deshalb eine relative `API_BASE = ""` statt einer festen Host-Angabe. Wichtig: für Node/Vite existiert bereits eine Windows-Firewall-Freigabe, für Python/uvicorn nicht (und Claude Code hat keine Admin-Rechte, um das automatisch zu ändern) — daher unbedingt bei dieser Proxy-Lösung bleiben, nicht versuchen Port 8000 direkt freizugeben.

GM-Login ist jetzt case-insensitive (`sl` und `SL` funktionieren gleichermaßen) — `auth/repository.py` vergleicht `username` seit Kurzem über `toLower()` in der Cypher-Query.
