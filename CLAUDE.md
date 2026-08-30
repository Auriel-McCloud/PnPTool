# PnPTool — Projektgedächtnis für Claude

Diese Datei wird von Claude Code automatisch geladen, sobald in diesem Ordner gearbeitet wird (egal von welchem Gerät/welcher Session aus). Sie ist die Quelle der Wahrheit für den Projektstand — bitte bei jeder größeren Änderung aktualisieren, damit parallele Sessions (z.B. Desktop + Handy) synchron bleiben.

## Was ist PnPTool

WebApp für Mark's Pen-and-Paper-Rollenspielrunden, Homebrew-System **"NeotopiA"** (WoD-artige Attribute/Fähigkeiten, Shadowrun-Cyberware/Rigging/Drohnen, Mage-Sphären, Cyberpunk-Setting). Referenzmaterial: `docs/reference/Neotopia.xlsx` (Charakterblatt, Drohne/Fahrzeug, komplettes Regelwerk inkl. GM-only "SL Ideen Gadgets"-Abschnitt).

Zwei Nutzerrollen:
1. **Spielleiter (GM)** — plant Kampagnen als **Beziehungsgraph**: Personen, Orte, Events mit typisierten Verbindungen zueinander (wer kennt wen, wer war wo, was geschah wann). Manche Inhalte sind strukturell immer GM-geheim (z.B. NPC-Hintergedanken).
2. **Spieler** — eigene interaktive Charakterbögen (Dot-Pool-Attribute/Fähigkeiten, Box-Tracks für Gesundheit/Willenskraft), Live-Pop-ups vom SL während der Session (noch nicht gebaut).

Der volle Plan (Architektur-Entscheidungen, Datenmodell, Phasen-Roadmap) liegt hier: `C:\Users\Mark\.claude\plans\gut-pnp-steht-f-r-temporal-waterfall.md` — bei Bedarf dort nachlesen, diese Datei hier ist die kompaktere Zusammenfassung + laufender Status.

**Das UI-Konzept ("Commlink") steht in `docs/ui-konzept.md`** — Leitbild, Aufbau, Bereichsschnitt, Kampfmodus, Tooltip-System. Vor UI-Arbeit dort nachlesen, das ist die Quelle der Wahrheit fürs Aussehen.

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
        ├── items/                (api.ts, GegenstaendeUebersicht.tsx — kampagnenweite Gegenstände-Übersicht über alle Personen hinweg)
        └── App.tsx               (Tab-Umschalter Liste/Beziehungsgraph/Gegenstände)
```

**Git ist eingerichtet.** Remote `origin` = `https://github.com/Auriel-McCloud/PnPTool.git`, Arbeitsbranch `main` (es wird direkt auf `main` committet, keine Feature-Branches). Commit-Messages auf Deutsch, eine Zeile, beschreiben das fachliche Ergebnis statt der Dateien (z.B. "Vorlagen sind jetzt besitzerlos statt einer Person zugeordnet"). Ignoriert sind `.env`, `backend/.venv/`, `backend/uploads/`, `frontend/node_modules/`, `frontend/dist/` und `__pycache__`. Da Mark abwechselnd vom PC und vom Handy aus arbeitet: zu Session-Beginn `git log --oneline -5` + `git status` prüfen, am Ende committen und pushen, damit das jeweils andere Gerät den Stand hat.

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
- 🟡 **Phase 3 (teilweise, 28.08.2026)** — Charakterblatt-Grundlage: TraitDef-Katalog (52 Werte aus Neotopia.xlsx geseedet), Punkte-Anzeige (DotPool, beliebiges Maximum inkl. Per-Charakter-Override), Gegenstände 1:N an Personen mit Auto-Sichtbarkeit für den Besitzer. Siehe eigener Abschnitt unten. **Noch offen für vollständige Phase 3:** Box-Tracks (Gesundheit/Willenskraft/I.C.E.), Cyber/Bio-Ware-Slots, Rüstung/Waffen, Companion/Drohne-Sheets, Würfeln.
- ✅ **Phase 4 (29.08.2026)** — **Spieler-Zugang steht.** Sichtbarkeits-Filterung läuft in allen Lese-Routen, ansteuerbar über die SL-Vorschau `?alsSpieler=` **und** über echte Spieler-Sitzungen. Beitritt per Zugangscode, Charakter beanspruchen, eigene Oberfläche. Siehe eigener Abschnitt unten. Offen bleibt nur die Live-Kommunikation (Phase 5).
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

## Phase 3 (teilweise, 28.08.2026) — Charakterblatt-Grundlage + Gegenstände

Ausgangspunkt: Mark wollte (a) Gegenstände 1:N an Personen hängen können, automatisch sichtbar für den Besitzer, (b) ein generalisierbares "Charakterblatt" (nicht nur PCs, auch NPCs/Fahrzeuge) mit Punkte-Werten wie im Excel — meist 0-5/0-6, aber einzelne mächtige Sachen sollen auch 0-15 oder 0-20 gehen können, ohne dass das System das global deckelt.

**Umgesetzt:**
- `TraitDef`-Katalog (`app/traits/`): 52 Werte aus `Neotopia.xlsx` geseedet (9 Attribute max 6, 30 Fertigkeiten, 4 NeuroWeaving, 9 Sphären je max 5), ruleset-gescoped (`neotopia`), deterministische IDs (`ruleset:category:name`) + `MERGE` → Seeding läuft bei jedem Backend-Start erneut, idempotent, überschreibt nie individuelle Charakter-Werte. Seed-Liste in `app/traits/seed.py`, bei Bedarf dort erweitern.
- `HAS_TRAIT`-Relationship (`Person`/später `Companion` → `TraitDef`) trägt `rating` UND optional `maxOverride` — **das Maximum ist pro Charakter überschreibbar**, nicht nur pro Fähigkeit global. So kann eine einzelne Elder-NPC bei Schusswaffen auf 8/10 stehen, während normale Charaktere bei 5 gedeckelt bleiben. Effektives Maximum = `maxOverride ?? TraitDef.defaultMax`.
- `GET /api/campaigns/{cid}/personen/{id}/werte` liefert nur explizit gesetzte Werte — das Frontend merged das clientseitig mit dem vollen Katalog (`CharacterSheetPanel.tsx`, `mergeCatalogWithRatings`), damit ein frischer Charakter alle 52 Werte auf 0 zeigt statt einer leeren Liste.
- `DotPool`-Komponente (`frontend/src/traits/DotPool.tsx`): generische Punkte-Anzeige, rendert exakt `max` Kreise, funktioniert unverändert für 5, 15 oder 20. Klick-UX wie klassischer WoD-Bogen (Klick auf obersten gefüllten Punkt reduziert um 1, sonst direkt setzen).
- `Gegenstand`-Knoten (`app/items/`), verbunden über `Person -[:BESITZT]-> Gegenstand` (1:N). Sichtbarkeit wird beim Anlegen **automatisch** vorbelegt (PC-Besitzer → `SPEZIFISCH` nur für diesen einen Spieler, NPC-Besitzer → `GM`), aber der SL kann das beim Erstellen explizit übersteuern (`sichtbarkeit`/`sichtbarFuer` im Request setzen). `visibility.py` hat dafür `filter_gegenstand_for_viewer`/`filter_gegenstaende_for_viewer` (gleiches Muster wie bei Entities, ungenutzt bis Phase 4).
- Nebenbei gefixt: `delete_node` (Personen/Orte/Events löschen) hat vorher Gegenstände verwaister Personen im Graph zurückgelassen (`DETACH DELETE n` löscht nur den Knoten selbst, nicht was er besaß) — räumt jetzt via `OPTIONAL MATCH (n)-[:BESITZT]->(owned)` mit auf.
- UI: "Charakterblatt öffnen"-Button pro Person in `EntityManager.tsx`, klappt `CharacterSheetPanel` auf (Werte nach Kategorie gruppiert + Gegenstände-Liste mit Anlegen/Entfernen).

**Nachgezogen (28.08.2026, nach Feedback "Gegenstand ist nicht bearbeitbar"):**
- `PATCH /api/campaigns/{cid}/personen/{personId}/gegenstaende/{itemId}` — Gegenstände waren vorher nur anlegbar (nur Name) und löschbar, nicht bearbeitbar. Jetzt volles Update für Name/Beschreibung(Rich-Text)/Notizen(Rich-Text)/Sichtbarkeit.
- `frontend/src/traits/CharacterSheetPanel.tsx` → `GegenstandRow`: jeder Gegenstand ist über "Bearbeiten" aufklappbar, editiert Name + Rich-Text-Beschreibung/Notizen + `VisibilitySelector` (Sichtbarkeit nachträglich änderbar, z.B. wenn ein Spieler seinen eigenen Gegenstand doch entdecken soll).
- Die `+max`/`−max`-Knöpfe sind jetzt hinter einem "⚙ Optionen anzeigen"-Schalter versteckt (waren vorher immer sichtbar, wirkte unübersichtlich/würde Spieler verwirren).

**Nachgezogen (28.08.2026, Runde 2 — Bild, MacGuffins im Graph, typisierte Gegenstände):**
- `Gegenstand` hat jetzt: `typ` (freier String im Backend — bewusst kein starres Enum, damit neue Typen kein Backend-Update brauchen; Frontend-Dropdown s.u.), `eigenschaften` (freie Key-Value-Paare wie Munition/Schaden/Level, als JSON-String in Neo4j gespeichert weil Neo4j keine Map-Properties unterstützt — De/Encoding passiert in `items/repository.py`, Schema/Routes sehen ein normales `dict[str,str]`), `zeigeInGraph` (bool), `bildUrl`.
- **Echter Datei-Upload**: `POST .../gegenstaende/{itemId}/bild` (multipart, `python-multipart` — war schon in den Dependencies), speichert unter `backend/uploads/{campaignId}/{uuid}.{ext}` (Verzeichnis gitignored, wird automatisch angelegt), ausgeliefert über `StaticFiles`-Mount auf `/uploads`. **Wichtig für Vite-Proxy**: `/uploads` musste zusätzlich zu `/api` in `vite.config.ts` mitgeproxyt werden, sonst funktioniert das Bild vom Handy/LAN aus nicht (gleicher Grund wie bei `/api`: Port 8000 ist per Firewall blockiert). Erlaubte Typen: PNG/JPEG/WEBP/GIF, max. 8 MB. **Absichtlich noch offen:** Mark plant hier später eine KI-Bildgenerierung (Gemini "Nano Banana" o.ä.) direkt aus dem Gegenstand heraus — noch nicht spezifiziert, aber die Architektur (Upload liefert eine URL zurück, die einfach auf `bildUrl` gesetzt wird) sollte sich dafür eignen: ein zukünftiger "KI-generieren"-Button müsste nur intern ein Bild erzeugen und denselben Set-Bild-Mechanismus aufrufen.
- **MacGuffins im Beziehungsgraph**: `EntityKind` (Backend UND Frontend) um `"Gegenstand"` erweitert, `graph/repository.py::get_all_nodes` inkludiert jetzt `Gegenstand`-Knoten wenn `zeigeInGraph=true` (normale Items bleiben unsichtbar, um den Graphen nicht zu überladen). `VERBINDUNG`-Relationships funktionieren bereits generisch für jedes Label (keine Änderung nötig). Cytoscape zeigt Gegenstände als lila Sterne (`graph/CampaignGraphView.tsx`, `KIND_SHAPE`/`KIND_COLOR`).
- **Wichtige Ergänzung, sonst nutzlos**: Das "Verbindungen"-Formular in `EntityManager.tsx` konnte vorher nur Person/Ort/Event als Endpunkte anbieten. `refreshAll()` lädt jetzt zusätzlich `getGraph(campaignId)` und filtert `kind==='Gegenstand'` raus, damit graph-sichtbare Gegenstände (nicht normale Inventar-Items!) im Verbindungen-Dropdown erscheinen — sonst hätte der SL MacGuffins zwar sehen, aber nie im UI mit ihnen verknüpfen können.
- Komplett end-to-end getestet: Gegenstand mit Typ+Eigenschaften+zeigeInGraph anlegen, Bild hochladen (via echtem PNG), Verbindung Person→Gegenstand anlegen, Graph enthält den Knoten — alles über den Vite-Proxy-Pfad verifiziert.

**Nachgezogen (28.08.2026, Runde 3 — nach Feedback "Typ-Auswahl funktioniert nicht"):**
- Das `<datalist>`-Textfeld für `typ` war browserseitig unzuverlässig (v.a. mobil, iOS Safari unterstützt `<datalist>` z.B. praktisch gar nicht) — ersetzt durch ein echtes `<select>` mit fester Werteliste `TYP_OPTIONEN = [Waffe, Rüstung, Cyberware, Droge, Verbrauchsgegenstand, Werkzeug, Sonstiges]` in `CharacterSheetPanel.tsx`. MacGuffin ist **kein** Typ mehr (war es nie wirklich, nur ein Vorschlag) — MacGuffin-Zugehörigkeit läuft ausschließlich über den `zeigeInGraph`-Schalter. Falls ein Gegenstand einen alten/nicht-gelisteten Typ hat, zeigt das Dropdown ihn trotzdem als zusätzliche "(alt)"-Option, damit nichts stillschweigend überschrieben wird.
- `Gegenstand.preis` (int, ¥) und `Gegenstand.kraft` (int, 0-7) sind jetzt eigene erstklassige Felder statt Einträge in `eigenschaften` — Preis für den späteren Shop (Name/Typ/Preis direkt abfragbar statt aus einem JSON-Blob geparst), Kraft als Punkte-Wert (`DotPool`-Komponente wiederverwendet, Skala 0-7 aus dem Regeln-Sheet für Waffenschaden/Rüstungsbonus), nur eingeblendet wenn `typ` Waffe oder Rüstung ist (`KRAFT_TYPEN`-Set in `CharacterSheetPanel.tsx`).
- "Bild entfernen"-Button ergänzt (`GegenstandUpdate.bildUrl` ist jetzt PATCH-bar, leerer String löscht die Referenz — die Datei selbst bleibt aktuell noch auf der Platte liegen, kein Cleanup, siehe unten).
- **Wichtige Lektion nochmal angewendet**: bei den zwei neuen Feldern (`preis`, `kraft`) diesmal sofort Fallbacks in `_decode()` ergänzt (siehe Stolperstein #9) UND direkt nach dem Backend-Neustart gegen **alle** Bestandsdaten (nicht nur frisch angelegte) getestet, bevor zum Frontend übergegangen wurde — kein Rückfall in denselben Fehler.
- **Bekannte kleine Schuld**: beim "Bild entfernen" wird nur die `bildUrl`-Property gelöscht, die Datei unter `backend/uploads/...` bleibt liegen (verwaist). Unkritisch (gitignored, kein Funktionsproblem), aber bei Bedarf später aufräumen.
- **Explizit vertagt** (Mark: "wir müssen hier noch ein wenig mehr differenzieren"): Typ-spezifische Zusatzfelder über Waffe/Rüstung hinaus (Cyberware→WVerlust, Drogen→Wirkung/Nebenwirkung/Dauer, ...) sowie das Verbesserungs-/Upgrade-System aus dem Regeln-Sheet (Erweiterungen erhöhen den Preis um feste Prozentsätze, z.B. SmartLink +50%) — beides noch nicht angegangen.

**Nachgezogen (28.08.2026, Runde 4 — einzigartig vs. stapelbar):**
- `Gegenstand.einzigartig` (bool, Default `true`) + `Gegenstand.menge` (int, Default `1`). Einzigartig = genau ein Exemplar in der Welt (Das Amulett von Neotopia, ein individuell verbessertes Bustersword). Nicht-einzigartig = Verbrauchs-/Stapel-Gegenstand (Munition, eine Dose Cola) — **jede besitzende Person führt ihre eigene, unabhängige Menge**, es gibt bewusst noch KEINE geteilte Vorlage/Katalog über Personen hinweg (das wäre erst für einen echten Shop nötig, wo z.B. "9mm Munition" eine campaign-weite Vorlage wäre und "kaufen" eine Instanz beim Käufer erzeugt/erhöht — expliziter Architektur-Fork, noch nicht gebaut, siehe unten).
- **Falsy-Falle bewusst vermieden**: `menge=0` (verbraucht) und `einzigartig=false` sind beides gültige Werte, die mit dem bisherigen `x or default`-Muster fälschlich auf den Default zurückgesetzt worden wären (0 ist falsy in Python!). Neuer Helper `_or_default(value, default)` in `items/repository.py` prüft explizit auf `is not None` statt auf Truthiness. Mit `{"menge": 0}` per PATCH getestet, bleibt korrekt bei 0.
- UI: Checkbox "Einzigartig" + (nur wenn nicht einzigartig) ein Mengen-Zahlenfeld, Zusammenfassungszeile zeigt `×{menge}` wenn nicht einzigartig.
- **Für später (wenn der Shop drankommt)**: eine echte Vorlage/Instanz-Trennung (`GegenstandVorlage` campaign-weit + `Gegenstand`-Instanzen die darauf referenzieren) wäre der nächste Schritt, sobald mehrere Spieler denselben Gegenstand kaufen/haben sollen UND der SL die Vorlage zentral pflegen will (z.B. Preis einmal ändern statt bei jeder Instanz einzeln). Jetzige Lösung (unabhängige Menge pro Person) ist bewusst der einfachere Zwischenschritt.

**Nachgezogen (28.08.2026, Runde 5 — Gegenstands-Meta hinter Optionen-Schalter):**
- "Im Beziehungsgraph anzeigen" (MacGuffin), "Einzigartig" und "Menge" sind hinter einem Optionen-Schalter versteckt. Rein clientseitiges Ausblenden — sobald es echte Spieler-Routen gibt (Phase 4), muss diese Trennung serverseitig in `visibility.py` nachgezogen werden, das reine Verstecken im UI ist kein Sicherheitsmechanismus.
- **Korrektur 1 nach Feedback ("ganz hochscrollen ist unpraktisch")**: erst als EIN globaler Schalter oben im `CharacterSheetPanel` gebaut, der sowohl Trait-Max-Buttons als auch Gegenstands-Meta steuerte. Dann auf zwei Schalter aufgeteilt: `showTraitOptions` über der Werte-Liste, `showItemOptions` über der Gegenstände-Liste — aber `showItemOptions` war immer noch EIN Schalter für ALLE Gegenstände gemeinsam.
- **Korrektur 2 nach weiterem Feedback ("Optionen-Button müsste es bei jedem Gegenstand geben, nicht im Gegenstands-Menü")**: `showOptions` ist jetzt lokaler State **innerhalb** jeder einzelnen `GegenstandRow` (kein Prop mehr von außen), der Button sitzt am **Ende** des aufgeklappten Bearbeiten-Formulars (nach Sichtbarkeit, vor "Speichern") statt am Anfang neben Name/Typ verstreut — Klick öffnet die Optionen direkt darunter, kein Scrollen nötig. Zusätzlich: `hatMenge` (bool) als **von `einzigartig` unabhängiges** Feld ergänzt, weil "nicht jeder nicht-einzigartige Gegenstand braucht eine Menge" (Beispiel Mark: ein Seil ist nicht einzigartig, aber niemand zählt die Stückzahl). Menge-Feld erscheint jetzt bei `hatMenge=true`, nicht mehr bei `!einzigartig`. Getestet: `einzigartig=false` + `hatMenge=false` gleichzeitig funktioniert wie vorgesehen.

**Nachgezogen (28.08.2026, Runde 6 — Gegenstands-Vorlagen + Zuweisen + Seltenheit):**
- `Gegenstand.istVorlage` (bool): markiert einen Gegenstand als Vorlage, die beliebig oft über eine neue Aktion **"Zuweisen"** an eine Person (PC oder NPC) vergeben werden kann. Jede Zuweisung erzeugt eine unabhängige, echte Kopie — die Vorlage selbst bleibt unverändert bestehen (kein Verbrauch). Use Case: ein Pistolenmodell, das zwei Spieler kaufen und danach unterschiedlich individualisieren (Zielfernrohr vs. größerer Magazinclip).
- Neue Route `POST .../gegenstaende/{itemId}/zuweisen` (`{zielPersonId}`) in `backend/app/items/routes.py`, neue Repository-Funktion `assign_copy` in `repository.py`. Kopie-Regeln: `istVorlage=false, einzigartig=true` werden **immer erzwungen** (die Kopie ist jetzt ein Einzelstück, keine Vorlage mehr), aber `hatMenge`/`menge` werden **von der Vorlage übernommen, nicht zurückgesetzt** (Korrektur nach Rückfrage — eine Munitions-Vorlage könnte so weiterhin mengenbasierte Kopien erzeugen). `bildUrl` wird ebenfalls kopiert. Sichtbarkeit wird für die Zielperson frisch berechnet (PC→SPEZIFISCH, NPC→GM), nicht die alte `sichtbarFuer`-Liste übernommen. 400 falls Quell-Item nicht `istVorlage` ist.
- Die Default-Sichtbarkeits-Berechnung (PC→SPEZIFISCH+[id], NPC→GM) war in `create_item` inline dupliziert — jetzt als `_default_sichtbarkeit()` in `routes.py` extrahiert, von `create_item` UND `zuweisen` genutzt.
- `Gegenstand.seltenheit` (int, 1-5, DotPool direkt neben Preis sichtbar): 1 = überall verfügbar, 5 = nur Speziallabor/Schwarzmarkt. Aktuell nur ein reines Datenfeld ohne Logik — die automatische Shop-Bestückung danach ist Phase-5-Zukunft (siehe Plandatei).
- Frontend: `alleOptionen` (ungefilterte Personen-Liste, Label mit `(PC)`/`(NPC)`-Kennzeichnung) neu von `EntityManager.tsx` durch `CharacterSheetPanel.tsx` bis zu `GegenstandRow` durchgereicht — nötig weil die Zuweisen-Zielauswahl auch NPCs anbieten soll, während `pcOptions` (nur PCs) weiterhin exklusiv für den `VisibilitySelector` reserviert bleibt.
- Komplett end-to-end getestet: Vorlage mit `hatMenge=true, menge=20` angelegt, an einen echten PC UND einen NPC zugewiesen, beide Kopien korrekt mit übernommener Menge und frisch berechneter Sichtbarkeit — sowie die 400-Ablehnung für Nicht-Vorlagen. Alles über den Vite-Proxy-Pfad.
- **Größere Vision, bewusst nur dokumentiert, nicht gebaut** (siehe Plandatei `C:\Users\Mark\.claude\plans\gut-pnp-steht-f-r-temporal-waterfall.md` für Details): komplett neue Menüführung (eigene Bereiche für PCs/NPCs/Gegenstände/Orte/Regeln/Graph, Gegenstände als fokussiertes Popup statt Inline-Akkordeon), Shop = Ort mit Angebot + Live-WebSocket-Popup (minimierbar, zuweisbar/entziehbar, Teil von Phase 5), Popup-Animation (klappt von der Klick-Stelle bzw. einem Benachrichtigungs-Symbol oben rechts auf), Munition als Waffen-Untereigenschaft statt eigener Gegenstand.

**Nachgezogen (28.08.2026, Runde 7 — kampagnenweite Gegenstände-Übersicht):**
- Auslöser: Gegenstände existierten nur verschachtelt im Charakterblatt einer einzelnen Person (Kira Voss) — dadurch kaum testbar, ohne extra für jeden Test ein Charakterblatt aufzuklappen. Statt des großen Menüführungs-Umbaus (weiterhin nur dokumentierte Vision, s.o.) jetzt bewusst die leichtgewichtige Zwischenlösung: eine dritte, kampagnenweite Ansicht.
- Backend: neuer `campaign_router` in `backend/app/items/routes.py` (Prefix `/api/campaigns/{campaign_id}/gegenstaende`, ohne `{person_id}` — daher eigener Router statt einer weiteren Route auf dem bestehenden personen-gescopten Router) mit `GET ""`. Neue Repository-Funktion `list_alle_gegenstaende()` matched `Person -[:BESITZT]-> Gegenstand` ohne Personen-Filter, liefert zusätzlich `ownerId`/`ownerName`/`ownerPersonType` pro Gegenstand. Neues Response-Schema `GegenstandMitBesitzer(GegenstandResponse)` mit denselben drei Zusatzfeldern. In `main.py` als zweiter Items-Router eingehängt.
- Frontend: `GegenstandRow` in `CharacterSheetPanel.tsx` ist jetzt `export`iert und wird unverändert wiederverwendet (kein Duplikat-Code für Bearbeiten/Löschen/Zuweisen/Bild-Upload). Neue Komponente `frontend/src/items/GegenstaendeUebersicht.tsx`: lädt `entitiesApi.listPersonen` (für `pcOptions`/`alleOptionen`, gleiches Muster wie `EntityManager.tsx`) + `itemsApi.listAlle`, gruppiert die Items clientseitig nach `ownerId` und rendert pro Besitzer eine Überschrift + die zugehörigen `GegenstandRow`s. Dritter Tab "Gegenstände" in `App.tsx`s `Dashboard()` neben Liste/Beziehungsgraph.
- End-to-end über den Vite-Proxy-Pfad getestet (GM-Login `sl`/`test-passwort-123`, dann `GET /api/campaigns/{cid}/gegenstaende`): alle 7 Bestands-Gegenstände korrekt nach Besitzer gruppiert zurückgegeben (Kira Voss NPC: 6 Items inkl. einer Vorlage + ihrer eigenen Kopie, Mr. Chrome NPC: 1 zugewiesene Kopie). `npm run build` sauber, Vite-Dev-Server nach dem etablierten Muster (exakte PID killen, `node_modules/.vite` löschen, neu starten) neu gestartet, neue Module (`GegenstaendeUebersicht.tsx`, `App.tsx`) liefern beim direkten Abruf über den Dev-Server-Transform-Endpoint 200 ohne Fehler.
- Bewusst nicht Teil dieser Runde: kein eigenes "Gegenstand neu anlegen"-Formular in der Übersicht (Neuanlage bleibt vorerst am Charakterblatt einer Person hängen, da jeder Gegenstand einen Besitzer braucht) — reine Lese-/Bearbeiten-/Zuweisen-Übersicht.

**Nachgezogen (28.08.2026, nach Feedback "beim Optionen-Button verbreitert sich der Rahmen"):**
- Mehrere Flex-Zeilen im Optionen-Block von `GegenstandRow` (Menge-Checkbox+Zahlenfeld) sowie in der Werte-Liste von `CharacterSheetPanel` (+max/−max-Buttons neben dem DotPool) hatten kein `flexWrap`/`minWidth: 0` gesetzt. Standardverhalten von Flexbox (`min-width: auto` auf Flex-Items) kann in Kombination mit langen Checkbox-Beschriftungen und fixbreiten Nachbar-Elementen (Zahlenfeld, Buttons) dazu führen, dass eine Zeile nicht mehr sauber umbricht und stattdessen die ganze Karte horizontal aufreißt. Fix versucht: `flexWrap: "wrap"` + `minWidth: 0` + `overflowWrap: "break-word"` auf den betroffenen Zeilen/Labels, plus dieselbe Absicherung auf der "Diesem Gegenstand zuweisen"-Zeile (`<select>`-Elemente sind notorisch schlechte Flex-Kinder, schrumpfen von Haus aus nicht).
- **Fix hat den Bug laut Mark NICHT behoben** ("es passt nicht, der Fehler passiert weiterhin") — Ursache also noch nicht wirklich gefunden, nur Symptome an der falschen Stelle bekämpft. **Bewusst zurückgestellt auf Marks Entscheidung**: sobald Gegenstände als fokussiertes Popup/Modal statt Inline-Akkordeon dargestellt werden (Teil der großen Navigations-Vision, s.o.), bekommt das Popup ohnehin eine fixe Größe — das Breite-Problem erledigt sich dann strukturell mit. Nicht weiter debuggen, bis dieser Umbau ansteht (und dann ohnehin nochmal neu betrachten). Kein Browser-Automatisierungswerkzeug in dieser Umgebung verfügbar, das erschwert das Debuggen von rein visuellen CSS-Bugs zusätzlich.

**Nachgezogen (28.08.2026, Runde 8 — Besitzer wechseln + Neuanlage in der Übersicht):**
- Auslöser: In der neuen kampagnenweiten Übersicht (Runde 7) gab es nur "Zuweisen" (= Kopie erzeugen) für als `istVorlage` markierte Gegenstände, aber keine Möglichkeit, einen ganz normalen (nicht-Vorlagen-)Gegenstand einer anderen Person — insbesondere einem NPC — zu übergeben. Mark: "ich kann den Gegenstand im Gegenstands Menü keinem NPC zuweisen, dafür fehlt mir denke ich einfach die Option."
- Neue Route `POST .../gegenstaende/{itemId}/besitzer` (`{zielPersonId}`, wiederverwendet `ZuweisenRequest`) + Repository-Funktionen `get_owner_id`/`transfer_owner` in `backend/app/items/repository.py`. **Verschiebt** den bestehenden Gegenstand-Knoten zu einer neuen Person (löscht die alte `BESITZT`-Relationship, erstellt eine neue) — im Unterschied zu `zuweisen`/`assign_copy`, das eine unabhängige Kopie erzeugt und nur für Vorlagen gedacht ist.
- Sichtbarkeit wird beim Übertragen nur dann neu berechnet, wenn sie erkennbar automatisch auf den alten Besitzer zugeschnitten war (`sichtbarkeit == SPEZIFISCH` UND `sichtbarFuer == [alterBesitzer]` exakt) — dann frisch für die Zielperson berechnet (PC→SPEZIFISCH, NPC→GM). War die Sichtbarkeit bewusst breiter gewählt (ALLE, GM, oder mehrere Spieler in `sichtbarFuer`), bleibt sie unangetastet, da der SL das dann bewusst so eingestellt hatte.
- Frontend: neuer Abschnitt "Besitzer wechseln" in `GegenstandRow` — **für jeden Gegenstand sichtbar** (nicht nur Vorlagen, im Gegensatz zum bestehenden "Zuweisen"-Abschnitt), Ziel-Dropdown aus `alleOptionen` (schließt den aktuellen Besitzer aus der Auswahl aus), Button "Übertragen". Neue API-Funktion `itemsApi.changeOwner`.
- Zweiter Punkt aus demselben Feedback: In der Übersicht ließen sich bisher keine neuen Gegenstände anlegen (nur Bearbeiten/Löschen/Zuweisen), weil jeder Gegenstand einen Besitzer braucht und die Übersicht selbst keinen "aktuellen" Besitzer hat. Gelöst mit einem kleinen Formular oben in `GegenstaendeUebersicht.tsx`: Besitzer-Dropdown (`alleOptionen`) + Namensfeld + "Hinzufügen", ruft den bereits bestehenden personen-gescopten Create-Endpoint auf (keine neue Backend-Route nötig).
- End-to-end getestet über den Vite-Proxy-Pfad: einen normalen (nicht-Vorlagen-)Gegenstand mit `sichtbarkeit=SPEZIFISCH` von Kira Voss zu Mr. Chrome (NPC) übertragen → Sichtbarkeit korrekt auf `GM` umgerechnet, Item taucht bei Kira nicht mehr auf, bei Mr. Chrome schon; neuen Testgegenstand für einen gewählten Besitzer angelegt und wieder gelöscht; Regressionscheck auf der kampagnenweiten Liste (200, alle Items weiterhin korrekt). Testdaten (Sichtbarkeit des "Gefälschter Ausweis"-Items) danach auf den ursprünglichen Stand zurückgesetzt.

**Vision — Party/Gruppen, Suche & Kategorisierung (28.08.2026, noch nicht designed, nur festgehalten):**
Mark hat beim Testen der Übersicht mehrere zusammenhängende Bedürfnisse skizziert, bewusst noch nicht zu Ende gedacht ("das müssten wir uns überlegen wie man sehr dynamisch damit arbeiten kann") — hier nur eingesammelt, damit nichts verloren geht:
- **Suche** über alle Gegenstände der Kampagne (aktuell nur nach Besitzer gruppiert, kein Filter/keine Suche).
- **Kategorisierung/Filter** der Übersicht: z.B. nur MacGuffins anzeigen (`zeigeInGraph`-Items), nur Waffen mit Munitionsstand der Spieler, nur PCs statt PCs+NPCs, oder PCs + eine bestimmte Teilmenge von NPCs.
- **"Party"/Gruppe als eigenes Beziehungskonzept**: Spieler bilden nicht immer eine einzige feste Gruppe — sie können sich aufteilen (2 gehen shoppen, 2 gehen zu einem NPC), wodurch mehrere gleichzeitige, **temporäre** Partys entstehen. Mark will z.B. einer Party einen Ort (Shop) zuweisen und einer anderen Party einen NPC. Das ist explizit als **sehr dynamisches/kurzlebiges** Objekt gedacht, nicht wie Personen/Orte/Events, die über die ganze Kampagne hinweg bestehen — Datenmodell dafür ist noch offen (z.B. ad-hoc `Gruppe`-Knoten mit `MITGLIED`-Relationships zu Personen? Rein clientseitiger, nicht-persistenter Zustand? Session-gebunden statt kampagnenweit?). Hängt vermutlich eng mit der Phase-5-Popup-Architektur zusammen (eine Party "sieht" gemeinsam ein Popup/einen Shop).
- Noch keine Entscheidung zu Datenmodell oder Umsetzungsreihenfolge — bei Bedarf eigenen Plan-Durchgang dafür machen, sobald klarer ist, welches der drei Bedürfnisse (Suche, Filter/Kategorien, Party) zuerst drankommt.

**Nachgezogen (28.08.2026, Runde 9 — Besitzer wechseln nur für Nicht-Vorlagen + `automatischImShop`-Feld):**
- "Besitzer wechseln" (Runde 8) ergibt für eine Vorlage keinen Sinn — Vorlagen werden über "Zuweisen" (Kopie erzeugen) verteilt, nicht verschoben. `GegenstandRow` zeigt den "Besitzer wechseln"-Abschnitt jetzt nur noch, wenn `item.istVorlage` (der gespeicherte Stand, gleiches Muster wie beim "Zuweisen"-Abschnitt) `false` ist — Vorlagen zeigen stattdessen weiterhin nur "Diesem Gegenstand zuweisen".
- `Gegenstand.automatischImShop` (bool, Default `false`) ergänzt — analog zu `seltenheit` in Runde 6 ein reines Datenfeld ohne Logik, da es noch keine Shops gibt (Phase 5). Checkbox im Optionen-Block mit Hinweistext, dass es sich erst auswirkt, sobald Shops existieren. Neue Kopien einer Vorlage (`assign_copy`) setzen `automatischImShop` immer auf `false` — eine zugewiesene, individualisierte Kopie ist kein Shop-Template mehr, unabhängig davon, ob die Vorlage selbst automatisch gelistet werden soll.
- Übliche Reihenfolge eingehalten: Fallback in `_decode()` sofort ergänzt, direkt gegen alle Bestandsdaten (7 Items, keins hatte das neue Feld) getestet — `GET .../gegenstaende` blieb 200, alle Items zeigen korrekt `automatischImShop: false`. Zusätzlich verifiziert: Vorlage auf `automatischImShop=true` gesetzt, davon eine Kopie erzeugt → Kopie hat korrekt wieder `false`.

**Nachgezogen (28.08.2026, Runde 10 — Vorlagen sind besitzerlos, größerer Architektur-Schnitt):**
- Auslöser: Mark bemerkte beim Testen, dass jeder Gegenstand (auch Vorlagen) einer Person zugeordnet sein musste — sinnvoll für normale Gegenstände, aber falsch für Vorlagen ("aktuell ist jeder Gegenstand einem NPC zugeordnet, das wollen wir nicht... Vorlagen sollten niemanden zugewiesen sein"). Gewünscht: im "Besitzer wählen"-Dropdown (Neuanlage) soll es einen Punkt "Vorlage" geben, der statt einer Person eben keinen Besitzer setzt.
- **Neue Invariante**: `istVorlage == true` ⟺ der Gegenstand hat keinen `BESITZT`-Besitzer. Owned ⟹ nie Vorlage, Vorlage ⟹ nie besessen. Die frühere manuelle "Ist eine Vorlage"-Checkbox im Optionen-Block ist damit gestrichen (hätte sonst widersprüchliche Zustände erlaubt) — ob ein Gegenstand Vorlage ist, ergibt sich jetzt ausschließlich aus Besitz-Aktionen (Neuanlage-Auswahl, "Besitzer wechseln → Vorlage", "Zuweisen").
- **Backend-Umbau**: `create_gegenstand(campaign_id, owner_person_id, data)` akzeptiert jetzt `owner_person_id=None` (erzeugt den `Gegenstand`-Knoten ohne `BESITZT`-Relationship). `list_alle_gegenstaende` nutzt jetzt `OPTIONAL MATCH (p:Person)-[:BESITZT]->(g)` statt striktem `MATCH`, damit besitzerlose Vorlagen mit auftauchen (`ownerId/-Name/-PersonType` sind dafür jetzt `null`, `GegenstandMitBesitzer`-Schema entsprechend auf `str | None` umgestellt). Neue Repository-Funktion `remove_owner` (löscht die `BESITZT`-Relationship, setzt `istVorlage=true`) als Gegenstück zu `transfer_owner`.
- **Wichtige Erkenntnis beim Umbau**: der `person_id`-Pfadparameter war bei `update_item`, `upload_bild`, `zuweisen`, `besitzer_wechseln` und `delete_item` schon immer **funktional ungenutzt** (nur Routing-Altlast aus dem ursprünglichen Design) — item-scoped Operationen liefen intern längst nur über `campaign_id + item_id`. Diese fünf Endpoints wurden deshalb ohne Funktionsverlust vom personen-gescopten `router` auf den `campaign_router` verschoben (Pfad ohne `{person_id}`), was besitzerlose Vorlagen automatisch unterstützt, ohne die Operationen selbst zu duplizieren. Nur `POST ""` (create, jetzt zusätzlich `create_vorlage` auf `campaign_router`) und `GET ""` (list, personen-gescopt) bleiben zwingend an eine Person gebunden.
- Neue Route `POST /api/campaigns/{cid}/gegenstaende` (campaign-gescopt, ohne Besitzer) erzwingt `istVorlage=true`; die bestehende personen-gescopte `POST .../personen/{pid}/gegenstaende` erzwingt jetzt umgekehrt `istVorlage=false` (ignoriert `body.istVorlage` in beiden Fällen bewusst, um die Invariante serverseitig durchzusetzen). Neue Route `POST .../gegenstaende/{itemId}/vorlage` (kein Body) entfernt den Besitzer eines bestehenden Gegenstands.
- **Frontend**: `items/api.ts` — alle item-scoped Funktionen (`update`, `remove`, `assign`, `changeOwner`, `uploadBild`) brauchen jetzt kein `personId` mehr, neue `createVorlage`/`removeOwner`, neue Konstante `VORLAGE_SENTINEL` für Besitzer-Dropdowns. `GegenstandRow`s `personId`-Prop ist jetzt optional (fehlt bei Vorlagen). Die "Besitzer wechseln"-Dropdown (nur bei Nicht-Vorlagen sichtbar) hat jetzt zusätzlich den Eintrag "— Vorlage (kein Besitzer) —", der `removeOwner` statt `changeOwner` aufruft. `GegenstaendeUebersicht.tsx` gruppiert Items jetzt zusätzlich in eine Pseudo-Gruppe "Vorlagen (kein Besitzer)" (immer zuerst angezeigt) für alle `ownerId===null`-Items, und das Neuanlage-Formular hat denselben "— Vorlage —"-Eintrag im Besitzer-Dropdown.
- Bestandsdaten korrigiert: die einzige existierende Vorlage ("Standard-Pistole Modell X", war fälschlich bei Kira Voss geführt) wurde per neuem `.../vorlage`-Endpoint besitzerlos gemacht, um die neue Invariante auch in den Testdaten zu erfüllen.
- End-to-end über den Vite-Proxy getestet: kampagnenweite Liste weiterhin 200 (inkl. `OPTIONAL MATCH`), Vorlage-Item taucht jetzt mit `ownerId:null` auf und nicht mehr in Kiras personen-gescopter Liste, neue besitzerlose Vorlage angelegt (`istVorlage:true` automatisch gesetzt), davon eine Kopie einer Person zugewiesen (funktioniert unverändert), Test-Items wieder gelöscht.

**Nachgezogen (28.08.2026, nach Feedback "Vorlage ist verschwunden, als ich Menge abgewählt habe"):**
- Mark berichtete, eine Vorlage sei aus der Ansicht verschwunden, nachdem er die Option "Menge verfolgen" abgewählt hatte — vermutete einen Zusammenhang zwischen "Menge" und "Vorlage".
- Per curl nachgestellt und verifiziert: **kein Backend-Bug** — eine Vorlage mit `hatMenge=true` behält nach `hatMenge=false` weiterhin `istVorlage=true, ownerId=null` und bleibt in der kampagnenweiten Liste. Die Vorlage war also nie wirklich weg.
- Wahrscheinlichste Ursache: rein optisch. Die einzigen sichtbaren Vorlagen-Hinweise waren winzig (`×N`-Mengenbadge, das nach dem Abwählen verschwindet, plus ein kleines "· Vorlage" ganz am Ende der Zusammenfassungszeile) — beim Abwählen von "Menge verfolgen" verlor die Zeile ihr auffälligstes Merkmal (`×N`) und wirkte dadurch "verschwunden", obwohl der Gegenstand unverändert da war.
- Trotzdem umgesetzt, da unabhängig davon sinnvoll: **"Menge" und "Vorlage" klar voneinander getrennt.** Der lange Erklärtext bei "Menge verfolgen" (Munition-Beispiel) sowie der zusätzliche Absatz "Jede besitzende Person führt ihre eigene Menge..." wurden entfernt (Mark: "die Beschreibung von was eine Menge ist, ist nicht nötig" — der zweite Satz ergab für Vorlagen ohnehin keinen Sinn, da die gar keine "besitzende Person" haben). Checkbox heißt jetzt schlicht "Menge verfolgen". Neu: ein eigener, klar abgesetzter Hinweis "📋 Vorlage — hat keinen Besitzer" ganz oben im aufgeklappten Bearbeiten-Formular (vor den Namens-/Typ-Feldern, deutlich getrennt vom Optionen-Block mit der Menge-Checkbox weiter unten) — nur sichtbar wenn `item.istVorlage`, rein informativ (kein Toggle, siehe Invariante oben).

**Nachgezogen (28.08.2026, nach Rückfrage "wo ist die Vorlagen-Option?" + Folge-Feedback zu Einzigartig/MacGuffin):**
- Kurz erklärt: "Vorlage" ist kein Toggle mehr, sondern ergibt sich aus dem Besitzer-Dropdown beim Anlegen bzw. aus "Besitzer wechseln → Vorlage machen" bei Bestandsgegenständen (siehe Runde 10 oben).
- Mark bestätigte daraufhin das Verständnis "Besitzer wechseln = verschiebt den Gegenstand selbst, Zuweisen = erstellt eine Kopie" — das war schon exakt der Stand (keine Änderung nötig), aber er wies auf eine echte Lücke hin: eine **einzigartige** oder **MacGuffin** (`zeigeInGraph`) Vorlage durfte bisher trotzdem per "Zuweisen" **kopiert** werden — das widerspricht "einzigartig" (es dürfte ja nur ein Exemplar geben).
- Fix: `routes.py::zuweisen` prüft jetzt `source["einzigartig"] or source["zeigeInGraph"]` und **verschiebt** in diesem Fall den Gegenstand selbst (neue Repository-Funktion `assign_owner` — Gegenstück zu `remove_owner`: gibt einer besitzerlosen Vorlage eine Besitzer:in, OHNE zu kopieren, setzt `istVorlage=false`, schlägt fehl/no-op falls doch schon ein Besitzer existiert). Nur bei normalen (nicht-einzigartigen, nicht-MacGuffin) Vorlagen läuft weiterhin `assign_copy` wie bisher.
- Frontend: die "Diesem Gegenstand zuweisen"-Sektion prüft `item.einzigartig || item.zeigeInGraph` (bewusst der **gespeicherte** Stand, nicht der lokale Edit-State, da die Aktion auf dem gespeicherten Gegenstand wirkt) und zeigt dann Label "...übergibt den Gegenstand selbst — einzigartig/MacGuffin, keine Kopie möglich" + Button "Übergeben" statt "...erstellt eine Kopie" + Button "Kopie erstellen".
- End-to-end getestet: einzigartige MacGuffin-Vorlage angelegt, zugewiesen → dieselbe ID landet bei der Zielperson, kein Duplikat, `istVorlage` korrekt auf `false`. Regressionscheck: normale (nicht-einzigartige) Vorlage "Standard-Pistole Modell X" erzeugt bei Zuweisen weiterhin eine unabhängige Kopie, Quelle bleibt unverändert besitzerlose Vorlage. Test-Items wieder gelöscht.

**Nicht gemacht / bewusst zurückgestellt (Rest von Phase 3):**
- Keine Box-Tracks (Gesundheit/Willenskraft/I.C.E./Arete) — die "Kästchen statt Punkte"-Werte aus dem Excel fehlen noch komplett.
- Kein Cyber/Bio-Ware, keine Rüstung/Waffen-Slots (nur generische Gegenstände ohne Schadenswerte etc.)
- Kein Companion/Drohne-Sheet, obwohl `HAS_TRAIT` dafür schon generisch genug wäre (funktioniert für jeden Knotentyp, nicht nur Person) — nur noch nicht an eine Companion-Route angebunden.
- Kein Würfeln.
- `sortOrder`-Nummerierung im Seed ist grob (Reihenfolge aus dem Excel übernommen), nicht weiter kuratiert.
- Optisches Layout ist weiterhin "unübersichtlich, nicht schön" (O-Ton Mark) — funktional korrekt, aber noch kein eigener Design-Durchgang für den Charakterbogen.
- **Neue Idee von Mark (28.08.2026, noch nicht designed):** drei eigene Ansichten/Modi für den Charakterbogen — "Charaktererstellung" (Startpunkte-Regeln, Rassen-Boni etc. aus dem Regeln-Sheet), "Spiel" (Standard-Ansicht, das was jetzt existiert), "Level Up" (EP ausgeben). Dazu ein Erfahrungspunkte-Zähler pro Charakter + eine Möglichkeit für den SL, EP an alle oder einzelne Spieler zu vergeben (soll sich automatisch im Charakterbogen niederschlagen). Braucht eigene Logik/Design-Runde, bewusst noch nicht begonnen.

## Sichtbarkeit scharf geschaltet + SL-Vorschau (28.08.2026)

Ausgangslage: `entities/visibility.py` war seit dem UI-Polish-Durchgang fertig geschrieben, wurde aber von **keiner** Route aufgerufen — reiner toter Code, im Echtbetrieb nie gelaufen. Statt dafür gleich den ganzen Spieler-Login (Phase 4) zu bauen, wurde bewusst der kleinere Schritt gewählt: der SL kann die Kampagne durch die Augen eines Charakters ansehen.

**Wie es funktioniert:** alle Lese-Routen nehmen einen optionalen Query-Parameter `?alsSpieler=<personId>`. Ohne ihn antwortet die API wie bisher als SL, mit ihm gefiltert. Umgesetzt über die Dependency `Viewer`/`get_viewer` in `backend/app/auth/dependencies.py` — **die eine Stelle, die sich für echte Spieler-Logins ändern muss** (dann kommt der `Viewer` aus der Spieler-Session statt aus dem Query-Parameter, der Filterpfad dahinter bleibt identisch).

Betroffen sind genau 10 GET-Routen (Personen/Orte/Events je Liste+Einzelabruf, Verbindungen, Graph, beide Gegenstands-Listen). **Keine einzige Schreib-Route** nimmt die Dependency — eine Vorschau darf nichts verändern können. Prüfbar mit einem Blick ins OpenAPI-Schema: nur GETs führen `alsSpieler`.

**Zwei echte Lücken, die dabei gefunden und geschlossen wurden** (beide waren nur deshalb unauffällig, weil die Funktionen nie liefen):
1. **Gegenstands-Notizen gingen ungefiltert raus.** `filter_gegenstand_for_viewer` redigierte nur `description`, `notes` wurde unangetastet durchgereicht. Ein Spieler hätte die SL-Notizen zu jedem Gegenstand mitbekommen, den er sehen darf. Gegenstände haben — anders als Person/Ort/Event — gar kein `notizenSichtbarkeit`-Feld, es gibt also keine Freigabe-Stufe. Deshalb werden Item-Notizen für Nicht-SL jetzt **komplett zurückgehalten** statt redigiert (redigieren hätte alle unmarkierten Sätze trotzdem ausgeliefert). Falls spieler-sichtbare Gegenstandsnotizen mal gewünscht sind: analog zu den Entities ein `notizenSichtbarkeit`-Feld ergänzen, nicht diese Sperre aufweichen.
2. **Verbindungen verrieten verborgene Endpunkte.** Eine für alle sichtbare Verbindung, die an einem SL-geheimen NPC hängt, wurde ausgeliefert — und verriet damit dessen Existenz und ID. `list_verbindungen` liefert jetzt zusätzlich die Sichtbarkeit beider Endpunkte mit (`von*`/`zu*`, nicht Teil von `VerbindungResponse`, geht also nicht an den Client), und `filter_verbindungen_for_viewer` wirft solche Kanten weg. Im Graph läuft dasselbe über die bereits gefilterte Knotenmenge (`filter_graph_edges_for_viewer`).

**Weitere bewusste Entscheidungen:**
- **Fail closed**: fehlende oder `null`-Sichtbarkeitsfelder gelten als `GM` (verborgen), nicht als `ALLE`. Altbestand ohne die Felder bleibt so unsichtbar statt zu leaken — und ein Tippfehler im Feldnamen versteckt zu viel statt zu wenig. Das ist auch der Grund, warum `filter_entity_for_viewer` jetzt durchgehend `.get(...) or "GM"` statt `entity["..."]` nutzt: vorher hätte ein Bestandsknoten ohne `notizenSichtbarkeit` einen `KeyError` → 500 ausgelöst (dasselbe Muster wie Stolperstein #9).
- **Unsichtbar ⇒ 404, nicht 403** beim Einzelabruf (`_visible_or_404` in `entities/routes.py`): ein 403 würde bestätigen, dass es das Objekt gibt.
- **Im Graph wird erst gefiltert, dann die Nachbarschaft gesucht.** Andersherum liefe die BFS durch verborgene Knoten hindurch und zöge Dinge heran, zu denen der Spieler gar keinen sichtbaren Pfad hat.
- Noch offen (relevant erst für echte Spieler-Routen, bei der SL-Vorschau unkritisch, da der Empfänger der SL selbst ist): `sichtbarFuer` wird in den Responses mitgeliefert und verrät einem Spieler, für welche anderen Charaktere etwas freigegeben ist. Bei echtem Spieler-Login rausfiltern.
- Ebenfalls offen: `GET /personen/{id}/werte` (Charakterwerte) ist **nicht** gefiltert — ein Spieler dürfte die Werte fremder Charaktere vermutlich nicht sehen, aber das ist eine eigene Design-Entscheidung (eigene Werte ja, fremde PCs? NPCs?) und wurde bewusst nicht mitentschieden.

**Frontend-Umschalter** (`frontend/src/auth/ViewAsSwitcher.tsx`): Leiste über den Tabs mit Dropdown "Spielleiter (alles sichtbar)" / "als \<Name\>". Bei aktiver Vorschau färbt sich die Leiste gelb mit Hinweistext + "Zurück zur SL-Sicht"-Knopf, damit nicht vergessen wird, dass man gefiltert schaut.

Der gewählte Charakter liegt als Modul-Zustand im API-Client (`setViewAs`/`getViewAs` in `api/client.ts`), der ihn an jeden `api.get` anhängt — bewusst kein Prop-Drilling durch jede Komponente. Zwei Dinge, die dabei wichtig sind:
- `api.getAsGm` umgeht die Vorschau. Nötig für die Auswahlliste des Umschalters selbst: würde sie mitgefiltert, verschwände womöglich genau der betrachtete Charakter aus dem Dropdown und man käme nicht mehr zurück. Genutzt von `entitiesApi.listPersonenAlsGm`.
- Die Ansichten bekommen `key={viewAs ?? "gm"}` in `App.tsx`. Beim Wechsel werden sie damit komplett neu aufgebaut und laden frisch — sonst müsste in jeder Komponente einzeln eine `useEffect`-Abhängigkeit nachgezogen werden (leicht zu vergessen, und ein Vergessen hieße: veraltete, ungefilterte Daten bleiben stehen).

**Tests**: `backend/tests/test_visibility.py`, 38 Stück, reine Unit-Tests ohne DB. Laufen mit `.\.venv\Scripts\python.exe -m pytest` aus `backend/`. `pytest` ist als optionale Dev-Abhängigkeit im `pyproject.toml` (`pip install -e ".[dev]"`). Achtung: das `tests/`-Verzeichnis existierte vorher zwar, war aber **leer** — die in früheren CLAUDE.md-Einträgen erwähnten "Unit-Tests" waren offenbar ad-hoc und nie eingecheckt.

End-to-end gegen die echte Testkampagne verifiziert (SL-Sicht vs. `?alsSpieler=<Kira>`): Personen 2→1 (Mr. Chrome verschwindet), Events 1→0, Verbindungen 4→2, Graph 6 Knoten/4 Kanten → 4/2, Gegenstände 7→2. Für den Beweis der Inline-Redaktion wurde ein Testgegenstand mit `gmSecret`-markiertem Satz angelegt: SL sah "Eine schlichte Silberkette. In Wahrheit ein Peilsender von Mr. Chrome.", die Spieler-Sicht nur "Eine schlichte Silberkette." — Notizen dort leer. Testgegenstand danach wieder gelöscht.

## Spieler-Zugang (Phase 4, überarbeitet 29.08.2026)

> **Achtung, das Beitrittscode-Verfahren ist abgelöst.** Ältere Abschnitte weiter unten beschreiben es noch; maßgeblich ist dieser hier.

**Spieler haben feste Benutzernamen, ein Charakter gehört dauerhaft dazu.**

Grund für den Umbau: Der Code führte laufend zu Konflikten. Wer sich von einem zweiten Gerät anmeldete, fand seinen eigenen Charakter belegt — von der eigenen alten Sitzung. Beim Testen ist das mehrfach passiert, zuletzt hat sogar ein Testlauf von mir Mark den Charakter weggenommen.

- `Spieler`-Knoten mit `benutzername`, optionalem `passwortHash`, `-[:GEHOERT_ZU]->` Kampagne und `-[:SPIELT]->` Person.
- **Anmeldung ohne Rücksicht auf Groß-/Kleinschreibung**, Leerzeichen werden abgeschnitten.
- **Passwort ist freiwillig.** Ohne gesetztes Passwort genügt der Name — in einer privaten Runde soll sich niemand erst eines ausdenken müssen. Wer eines vergibt (`POST /api/spieler/passwort`), wird ab dann danach gefragt; ein leerer Wert entfernt es wieder.
- Anmeldung meldet bei falschem Namen **und** falschem Passwort dasselbe zurück, damit sich nicht herausfinden lässt, welche Namen vergeben sind.
- Verwaltung unter **Spieler** im SL-Menü: anlegen, Charakter zuordnen, entfernen.
- Es gibt **keine Charakterwahl durch den Spieler mehr** — die Zuordnung macht die Spielleitung.

> ⚠️ **Ohne Passwort kann jeder, der den Namen kennt, den Zugang nutzen.** Für eine Runde im eigenen Heimnetz ist das die bewusste Entscheidung gegen Umstände. Sollte das Werkzeug je aus dem Heimnetz erreichbar sein, muss das neu bewertet werden.

**Test-Zugang:** `Auriel`, ohne Passwort, spielt Ryu Tanaka.

## Früheres Beitrittscode-Verfahren (abgelöst)

**Ablauf:** Spielleitung erzeugt im Bereich *Zugang* einen sechsstelligen Code → Spieler öffnet dieselbe Adresse, klickt "Ich bin Spieler und habe einen Zugangscode", gibt Code und seinen Namen ein → wählt einen freien Spielercharakter → sieht ab da die Kampagne durch dessen Augen.

**Datenmodell:** `Campaign.zugangscode` (Klartext — die Spielleitung muss ihn vorlesen können), `PlayerSession {id, name, createdAt}` `-[:GEHOERT_ZU]->` `Campaign`, `PlayerSession -[:SPIELT]-> Person`. Ein PC kann nur einmal beansprucht werden.

**Code-Format:** 6 Zeichen aus `ACDEFGHJKMNPQRTUVWXY2345679` — ohne 0/O, 1/I/L, 8/B, weil er am Spieltisch vorgelesen wird. Beitritt vergleicht case-insensitiv.

**Rollen teilen sich ein Cookie.** Es kann pro Browser immer nur eine Rolle aktiv sein. Für Marks Aufbau (ein Gerät, eine Rolle) richtig; wer SL und Spieler gleichzeitig sein will, braucht ein zweites Browserprofil oder ein privates Fenster.

**Neuer Code macht den alten ungültig, wirft aber niemanden raus** — der Code regelt nur den Beitritt. Wer draußen bleiben soll, wird im Bereich *Zugang* einzeln entfernt; sein Token wird dadurch sofort wertlos, weil `get_viewer` die Sitzung bei jedem Zugriff nachschlägt.

**Sicherheitskritischer Umbau — hier besonders aufpassen:** Die Kampagnen-Router hingen pauschal an `require_campaign_gm`. Damit Spieler lesen können, wurde das auf `require_campaign_zugang` gelockert. Dadurch standen **20 schreibende Routen offen** — jede hat jetzt `dependencies=[Depends(require_campaign_gm)]` am Decorator.

> **Bei jeder neuen Route auf einem Kampagnen-Router gilt:** schreibt sie etwas, muss sie `require_campaign_gm` mitbringen. `tests/test_zugriffsschutz.py` prüft das strukturell und schlägt sonst fehl. Diesen Test nicht abschalten — er ist die einzige Absicherung dagegen, dass Spieler Daten verändern.

*Stolperstein beim Schreiben dieses Tests:* diese FastAPI-Fassung hängt Router **verzögert** ein (`_IncludedRouter` in `app.routes`). Eine naive Schleife über `app.routes` fand genau eine Route und wäre still grün geblieben — der Test steigt deshalb über `original_router` ab.

**Was Spieler dürfen:** ausschließlich lesen. Der `alsSpieler`-Parameter wirkt nur für die Spielleitung; für Spieler wird er ignoriert, sonst könnte man sich durch fremde Charaktere klicken.

**Spieler-Oberfläche** (`frontend/src/players/`): dieselbe Commlink-Hülle wie beim SL, nur mit weniger Bereichen (Kontakte, Meine Sachen, Orte, Beziehungen; Charakterblatt und Notizen als "bald") und ohne Bearbeiten. Sie versteckt selbst nichts — die Daten sind schlicht nicht da, gefiltert wird serverseitig.

**Geprüft:** SL sieht 3 Personen/2 Orte/1 Event/4 Verbindungen/7 Gegenstände, der Spieler 2/1/0/2/1, Graph 7→4 Knoten. SL-Notizen am eigenen Charakter bleiben beim Spieler leer. Alle Schreibversuche 403, fremde Kampagne 404, `alsSpieler`-Missbrauch wirkungslos. Beitritt und Charakterwahl im Browser durchgespielt.

**Testdaten:** die Kampagne hat jetzt einen Spielercharakter **Ryu Tanaka** (vorher gab es keinen einzigen PC, was Vorschau und Spielertests unmöglich machte). Seine Notizen sind absichtlich SL-geheim, damit die Filterung sichtbar bleibt. Ein Zugangscode ist erzeugt; Testsitzungen wurden wieder entfernt, damit du selbst beitreten kannst.

## Aufbewahrungsorte / Inventar (29.08.2026)

Auf Marks Wunsch, Gegenstände unterteilen zu können: "ausgerüstet, im Rucksack, in einem Fahrzeug, im Versteck".

**Modell:** `Gegenstand.ablage` ist `AUSGERUESTET` | `RUCKSACK` | `GELAGERT`. Gelagertes verweist über `-[:LIEGT_IN]->` auf ein konkretes Ziel — einen `Ort` oder einen anderen `Gegenstand`.

**Ein Fahrzeug ist kein eigener Entitätstyp, sondern selbst ein Gegenstand.** Man besitzt es, es hat Preis, Bild und Beschreibung — dieselbe Struktur. Als Ablageziel gelten Gegenstände mit `typ` **Fahrzeug** oder **Behälter** (beide neu in `TYP_OPTIONEN`). Dasselbe Konzept trägt später Rucksäcke als echte Objekte und Schließfächer, ohne dass etwas dazukommen muss.

**Erste Schreibberechtigung für Spieler:** `POST .../gegenstaende/{id}/ablage` dürfen auch Spieler aufrufen — aber nur an Gegenständen ihres eigenen Charakters und nur für dieses eine Feld. Die Route prüft die Besitzverhältnisse selbst und antwortet bei fremden Gegenständen mit **404 statt 403**, damit deren Existenz nicht verraten wird. Sie ist namentlich in der Ausnahmeliste von `tests/test_zugriffsschutz.py` eingetragen — jede weitere Ausnahme dort muss genauso streng selbst prüfen.

Spieler legen nur die **Art** fest (ausgerüstet/Rucksack/gelagert), nicht das genaue Ziel — in welchem Fahrzeug oder an welchem Ort etwas liegt, bleibt Sache der Spielleitung.

**Darstellung:** Unterteilt wird über **Reiter**, nicht über Gruppen-Überschriften. Gruppen im Kachelraster würden die Ausmessung der Kachelzahl pro Seite zunichtemachen (Leitprinzip "nie scrollen"). Der Bereich heißt für Spieler **Inventar**, für die Spielleitung weiterhin Gegenstände.

**Cypher-Stolperstein:** zwischen `CREATE` und einem folgenden `MATCH` verlangt Neo4j ein `WITH` ("WITH is required between CREATE and MATCH"). Die Item-Abfragen haben deshalb zwei Varianten des `OPTIONAL MATCH` — `LIEGT_IN` und `LIEGT_IN_NACH_CREATE`. Die WITH-Variante **nur** dort einsetzen, wo außer `g` keine weitere Variable ins `RETURN` muss: `WITH g` wirft alles andere weg, was z.B. `list_alle_gegenstaende` (braucht `p` für den Besitzer) zerstören würde.

**Testdaten:** Ryu Tanaka besitzt jetzt ein Fahrzeug (*Yamaha Rapier*) und eine *Monoklinge* — damit lässt sich das Einlagern in ein Fahrzeug und in *Kiras Geheimversteck* ausprobieren, ohne erst etwas anlegen zu müssen.

## Kampagnen-Einstellungen und Gewicht (29.08.2026)

**Kampagnen haben jetzt Spieleinstellungen** — eine bewusst offene Sammlung (`EINSTELLUNGEN_DEFAULTS` in `campaigns/repository.py`). Gespeichert wird nur, was vom Standard abweicht; neue Einstellungen wirken dadurch sofort für Bestandskampagnen, ohne Migration. Die PATCH-Route nimmt ein offenes `dict` und verwirft unbekannte Schlüssel — so muss beim Hinzufügen einer Regel weder Schema noch Route angefasst werden.

**Erste Einstellung: Gewicht.** Marks Vorgabe war ausdrücklich *"kein mechanischer Effekt"* — nur eine Anzeige, die rot wird, und eine Übersicht für die Spielleitung, die dann selbst Konsequenzen zieht. Das System verhindert also nichts.

- `Gegenstand.gewicht` (Eigengewicht) und `Gegenstand.kapazitaet` (was es fasst; 0 = kein Behälter).
- Die Traglast einer **Person** ergibt sich aus `traglastAttribut` × `traglastProPunkt`. Beides ist einstellbar, weil das Attribut in NeotopiA **Körperkraft** heißt und in D&D **Stärke** — fest verdrahtet wäre das System auf ein Regelwerk festgenagelt.
- **Stückzahlen zählen mit**: 50 Schuss Munition wiegen fünfzigmal so viel wie einer.
- `GET .../gegenstaende/traglast` liefert alle Träger mit Last und Grenze. Spieler bekommen davon nur sich selbst und ihre eigenen Behälter zu sehen.
- Der Schalter sitzt beim Spielleiter unter **Zugang → Spielregeln**.

**Nicht rekursiv:** liegt ein gefüllter Rucksack im Auto, zählt gegen das Auto nur das Eigengewicht des Rucksacks, nicht dessen Inhalt. Für eine reine Anzeige vertretbar — sollte daraus je eine echte Mechanik werden, muss `traglast_uebersicht` nachgezogen werden.

**Fahrzeuge werden beim Anlegen als `GELAGERT` vorbelegt** (`NICHT_AM_KOERPER` in `items/routes.py`). Sonst läge ein 180-kg-Motorrad "im Rucksack" und zählte gegen die Traglast seines Besitzers — genau das ist beim Testen passiert. Änderbar, ein Modellauto darf durchaus mitgeführt werden.

**Aufbewahrungsbereiche sind datengetrieben, nicht fest** (`items/aufbewahrung.ts`). Statt der drei starren Ablage-Arten leitet die Oberfläche ab, was tatsächlich existiert:
- *Ausgerüstet* gibt es immer.
- Der zweite Bereich heißt nach dem **getragenen Behälter** ("Abgewetzter Rucksack"), sofern einer vom Typ Behälter/Fahrzeug ausgerüstet ist — sonst neutral *Mitgeführt*. Marks Einwand: nicht jeder hat einen Rucksack, und ohne einen trägt man Dinge trotzdem am Gürtel.
- **Je Lagerort ein eigener Bereich** (Yamaha Rapier, Kiras Geheimversteck), aber nur wenn dort etwas liegt.

**Mehrfachauswahl statt Entweder-oder:** man kann mehrere Bereiche gleichzeitig anzeigen. Der eigentliche Gedanke dahinter ist *Zugriff* — am Körper hat man Ausrüstung und Rucksack, im Auto zusätzlich dessen Inhalt, im Versteck wieder etwas anderes, aber eben nicht das Auto. Vorgewählt ist "am Körper"; leere Auswahl bedeutet alles.

*Fallstrick dabei:* die Vorauswahl darf erst gesetzt werden, **wenn die Gegenstände geladen sind**. Läuft der Effekt vorher, kennt `ermittleBereiche` nur "Ausgerüstet", und die Vorauswahl bleibt unvollständig stehen — genau das ist beim ersten Anlauf passiert.

**Randnotiz:** `TraitDef`-Kennungen enthalten Umlaute (`neotopia:AttributKörperlich:Körperkraft`). Im Browser wird das beim Aufruf automatisch kodiert; in Skripten muss man `quote()` verwenden, sonst scheitert die Anfrage.

## Offen: Drogen und temporäre Effekte (29.08.2026 notiert, nicht gebaut)

Mark: *„wir brauchen dann auch eine Logik die Drogen temporär zu den Werten rechnet… die geben teilweise Statusboni über den möglichen Wert."*

Im Regelwerk gibt es ab Zeile 172 bereits eine Drogentabelle mit Name, Wirkung, Nebenwirkung und Preis. Beispiel „Dash" (Combat Speed): *Geschicklichkeit +2, Initiative +2 für 3 Runden; danach −2 auf alle Würfe für 10 Minuten.*

Was das verlangt — deutlich mehr als ein Zahlenfeld:

- **Effekte dürfen das Maximum überschreiten.** Geschicklichkeit 6 + 2 ergibt 8, obwohl 6 die Obergrenze ist. Die Anzeige muss den Grundwert und den Aufschlag unterscheidbar zeigen, sonst hält man 8 für den echten Wert.
- **Dauer wird über Szenen gezählt, nicht über die Uhr.** Mark (29.08.2026): In der World of Darkness gilt üblicherweise alles *bis zum Ende der Szene* — eine Droge wirkt also die laufende Szene, ihre **Nachwirkung greift in der nächsten**. Den Szenenwechsel bestimmt die Spielleitung von Hand.
- **Daraus folgt eine Anzeige für den Spielleiter:** er muss sehen, dass gerade Verstärkungen oder Schwächungen aktiv sind, damit er den Wechsel überhaupt bewusst auslöst. Ohne diese Sichtbarkeit wird der Szenenwechsel vergessen und die Werte bleiben stehen.
- Ein Szenenzähler wäre damit ein eigenes, kampagnenweites Konzept — vermutlich verwandt mit den Spieleinstellungen.
- **Effekte wirken auf Verschiedenes**: einzelne Attribute, abgeleitete Werte (Initiative), oder pauschal auf alle Würfe.
- Marks weitere Idee: eine Droge, die das I.C.E. eines Technomancers anhebt — trifft also auch berechnete Werte.

Betrifft `traits/bogen.py` (dort werden die abgeleiteten Werte gebildet) und das Charakterblatt. **Vor dem Bauen eine eigene Design-Runde**, insbesondere zur Frage, wie viel Zeitverwaltung das Werkzeug übernehmen soll und was die Spielleitung von Hand macht.

## Feinschliff Charakterblatt und Menuespalte (29.08.2026)

Marks Wunsch: die Symbolspalte links schmaler, dafuer die Schrift eine Stufe
groesser — und die Symbole selbst groesser (welche es werden, legt er noch fest).

- `--rail-breite` 60px → **48px**, Symbole 16px → **20px**, Rand 13px (13+22+13
  ergibt genau die 48px). Am Tablet hochkant (800px) bleiben damit 752px Buehne.
- Wertenamen 13px → **14px**. Gemessen: bei 800px wird nichts abgeschnitten und
  es entsteht kein Querlauf. Unter 700px faellt es auf 13px.
- **Arete steht mittig.** Als einziger Wert seiner Gruppe klebte er im
  Dreispaltenraster links am Rand. Gruppen mit genau einem Eintrag bekommen
  `cb-werte-einzeln` (eine Spalte, `justify-content: center`, Breite begrenzt).
- **Initiative zeigt einen W10 neben der Zahl** (`traits/WuerfelZehn.tsx`, reines
  SVG, erbt die Textfarbe). Marks Begruendung: "ihre Initiative ist nicht 7,
  sondern 7 Wuerfel" — ausgeschrieben sprengt es die Zeile, das Symbol nicht.
  Die Komponente ist bewusst allgemein gehalten, die Wuerfelpools brauchen sie
  spaeter genauso.

**Dabei gefunden — Media Queries erhoehen die Spezifitaet nicht.** Der Block
`@media (max-width: 900px)` stand *vor* den Grundregeln `.cb-wert` und
`.cb-wert-name`. Bei gleicher Spezifitaet gewinnt die spaetere Regel, also war
die Haelfte des Blocks (Schriftgroesse, Abstaende, Zeilenhoehe) wirkungslos —
still, ohne Fehlermeldung. Der Block steht jetzt am Dateiende. **Merke: enger
gesetzte Varianten gehoeren hinter die Regel, die sie ueberschreiben sollen.**

**Bekannt und unveraendert:** zwischen 560px und 700px Fensterbreite werden
lange Namen (Widerstandsfaehigkeit, Geisteswissenschaften) mit Auslassungspunkten
gekuerzt — drei Spalten gehen sich dort schlicht nicht aus. Betrifft kein Geraet
aus der Runde, faellt nur bei einem schmalen Browserfenster auf.

## Nachtarbeit 29./30.08.2026 — Fenster, Erstellung, Level Up

Marks Auftrag: Fensteranimation, Level-Up-System und ein **Prototyp der
Charaktererstellung** ("das fine Tuning machen wir wenn ich wieder wach bin").
Alles gebaut und durchgeklickt; was daran erfunden statt belegt ist, steht
unten und in `docs/regeln-neotopia.md`.

### Fenster ziehen aus der Tipp-Stelle auf

`shell/tippPosition.ts` schreibt die letzte `pointerdown`-Position mit — **ein**
Mitschnitt am Dokument in der Erfassungsphase, statt die Koordinaten durch rund
zwanzig Klick-Handler zu reichen (und an jedem neuen zu vergessen). Das Fenster
misst nach dem Aufbau seine eigene Mitte, rechnet die Verschiebung dorthin aus
und legt sie als `--fn-von-x/y` an; die Keyframes greifen darauf zu.

**Zwei Fallen, beide umschifft:** Die Animation darf erst starten, wenn gemessen
ist — sonst liefe das erste Bild noch mit 0/0 und der Sprung wäre als Ruckler zu
sehen. Deshalb hängt sie an der Klasse `.fn-fenster-auf`, die erst ein
`useLayoutEffect` setzt (läuft vor dem Zeichnen, das Nachziehen bleibt
unsichtbar). Und `.fn-fenster` steht auf `opacity: 0`, damit es vorher nicht
aufblitzt — die Animation trägt `forwards`, sonst fiele es danach zurück.
Tastaturbedienung löscht die gemerkte Position: ohne Finger soll das Fenster aus
seiner eigenen Mitte wachsen statt aus einer zufälligen alten Ecke.

Am Handy bleibt es beim Hereinschieben von unten — dort füllt das Fenster den
Bildschirm, ein Aufziehen aus einem Punkt sähe nach Zerren aus.

### Charaktererstellung (Prototyp)

**Backend** `traits/erstellung.py` — die Regeln aus `Neotopia.xlsx` (Blatt
*Regeln*, Zeilen 1-42) als Daten: Rassen mit Anpassungen und Punktekontingenten,
die drei Fertigkeitspakete, Freebee-Preise, Hintergründe. Dazu `pruefe()`, das
eine Einreichung gegen alles davon prüft und **alle** Verstöße auf einmal
zurückgibt statt beim ersten abzubrechen.

**Wichtig zur Form der Einreichung:** geschickt werden nicht die Endwerte,
sondern die Punkte getrennt nach Herkunft (Kontingent / Paket / Hintergrund /
Freebee). Anders ginge es nicht — ein Attribut über dem Startmaximum ist
erlaubt, *wenn* Freebees dafür bezahlt wurden. Aus einer blossen Endzahl liesse
sich das nicht mehr ablesen und die Prüfung wäre geraten.

**Frontend** `traits/Charaktererstellung.tsx` — sieben Schritte (Weg, Rasse,
Attribute, Fertigkeiten, Hintergrund, Freebees, Person). Die Oberfläche kennt
**keine einzige Regel**: Rassen, Pakete und Preise kommen von
`GET /erstellung/regeln`. Sie rechnet nur mit, was noch offen ist.

Zum Leitprinzip *nie scrollen*: die Erstellung hält sich als einzige Ansicht
nicht daran, und zwar mit Absicht. Neunzehn Fertigkeiten mit Punktreihen passen
auf kein Tablet. Sie ist aber auch keine Übersicht, sondern ein Vorgang mit
Anfang und Ende — wie ein Fenster. Gescrollt wird nur in `.er-buehne`, Kopf mit
den Schritten und Fuss mit den Knöpfen stehen fest.

**Bestandscharaktere sind geschützt:** `bogen_uebersicht` meldet
`erstellungAbgeschlossen` auch dann, wenn zwar das Feld fehlt, aber schon Werte
gesetzt sind. Ohne das hätte Ryu Tanaka beim nächsten Öffnen die Erstellung
vorgesetzt bekommen — und wäre beim Durchklicken überschrieben worden.

### Level Up

`traits/erfahrung.py` + `traits/LevelUp.tsx`. **Blau ist bezahlbar, rot noch
nicht** — die ganze Ansicht lebt von dieser einen Unterscheidung, damit man
nicht Preise vergleichen muss. Der Weg dorthin führt über den EP-Kasten in der
Kopfzeile des Blatts, der jetzt ein Knopf ist.

Die Preise berechnet **immer der Server neu**; die Ansicht schickt nur mit,
*was* gesteigert werden soll. Andernfalls könnte man sich seinen Preis selbst
aussuchen.

> **Die Erfahrungspreise stehen nicht im Regelwerk.** Das Excel beschreibt die
> Erstellung, nicht das Steigern. Die Tabelle in `erfahrung.py` ist ein
> Vorschlag (WoD-Muster: Preis = aktueller Wert × Faktor) und zum Ändern
> gedacht — nur `FAKTOR` und `NEU_KOSTEN` anfassen, die Oberfläche zeigt die
> Preise an, statt sie zu kennen.

### Neue Felder am Charakter

`konzept`, `alter`, `ambition`, `verlangen`, `ziel`, `kapital`, `schulden`,
`willenskraftBonus`, `erstellungAbgeschlossen` — die Kopfzeile des Papierblatts
(Charakterblatt-Sheet, Zeilen 3-7). Auf dem Blatt erscheint nur, was ausgefüllt
ist; ein Raster leerer Beschriftungen sagt niemandem etwas.

**Dabei eine Lücke geschlossen, bevor sie eine wurde:** diese Felder gehen über
`PersonResponse` auch bei *fremden* Personen mit hinaus. Bei einem NPC ist genau
das der Stoff, aus dem die Kampagne besteht — was er will, was er fürchtet,
wieviel Geld er hat. Es gibt dafür keine eigene Sichtbarkeitsstufe, deshalb
bekommt sie ausser dem Spielleiter nur, wem der Charakter gehört
(`BOGEN_KOPF_FELDER` in `entities/visibility.py`). Gleiche Entscheidung wie
seinerzeit bei den Gegenstandsnotizen: lieber ganz zurückhalten als halb
redigieren.

`willenskraftBonus` wird gespeichert statt abgeleitet — Willenskraft lässt sich
mit Freebees und Erfahrung einzeln steigern, ohne dass sich Entschlossenheit
oder Fassung ändern.

### Zwei neue Routen, die auch Spieler schreiben dürfen

Damit sind es vier (vorher: Ablage umlegen, Zustand eintragen):

- `POST .../personen/{id}/erstellung` — nur am eigenen Charakter, **nur einmal**
  (danach 409; die Spielleitung darf erneut einreichen, sie muss Fehler
  korrigieren können), und alles läuft durch `erstellung.pruefe`.
- `POST .../personen/{id}/steigern` — nur am eigenen Charakter, Preis
  serverseitig gerechnet, gegen den vorhandenen Punktestand geprüft.

Beide sind namentlich in `tests/test_zugriffsschutz.py` eingetragen. **Der Test
hat beim ersten Lauf zugeschlagen** und beide Routen als ungeschützt gemeldet —
genau wozu er da ist. Erfahrung *vergeben* bleibt der Spielleitung
(`POST .../personen/{id}/erfahrung` mit `require_campaign_gm`).

### Kleinigkeiten aus derselben Nacht

- **Arete steht mittig, Name über den Punkten.** Als einziger Wert seiner Gruppe
  klebte er im Dreispaltenraster links am Rand. Gruppen mit genau einem Eintrag
  bekommen `cb-werte-einzeln`.
- **Initiative zeigt einen W10** (`traits/WuerfelZehn.tsx`, reines SVG, erbt die
  Textfarbe). Marks Begründung: "ihre Initiative ist nicht 7, sondern 7 Würfel".
  Die Komponente ist allgemein gehalten, die Würfelpools brauchen sie genauso.
- Level Up nimmt am Tablet **zwei** Spalten statt drei — anders als das Blatt
  braucht jede Zeile zusätzlich einen Preis, drei Spalten schnitten die Namen ab.

### Was Mark noch entscheiden muss

1. **Hintergrundliste** — zehn Vorschläge, keiner davon aus dem Regelwerk.
2. **Erfahrungspreise** — die Faktoren oben.
3. **Sphären beim Freebee-Kauf**: wie Fertigkeit (2, aktuell) oder wie Arete (5)?
4. **Fertigkeitspakete und Sphären**: aktuell zählt eine Sphäre als eine der acht
   Profi-Fertigkeiten. Gewollt, oder sollen Sphären ein eigenes Kontingent haben?
5. Ob die Erstellung auch der Spielleitung offenstehen soll, um einen NPC damit
   zu bauen — technisch geht es bereits, es gibt nur keinen Knopf dafür.

## Tooltip-System, Fremdmaterial, Gegenstands-Klarstellungen (30.08.2026)

### Fremdmaterial im Referenzordner bleibt lokal

Mark hat `docs/reference/Regel Details - infotipp optionen.txt` abgelegt —
Texte aus dem **Magus-Regelwerk**, die inhaltlich noch nicht auf NeotopiA
passen. Sie sollen erst *im Werkzeug selbst* überarbeitet und auf Cyberpunk
umgeschrieben werden (das ist der eigentliche Grund für die geplante
Claude-/Gemini-Anbindung), bevor irgendetwas davon das Gerät verlässt.

`.gitignore` sperrt deshalb **den ganzen Ordner** und nimmt nur
`Neotopia.xlsx` aus — Marks eigenes Blatt. So ist auch alles geschützt, was
er künftig dort ablegt, ohne dass jemand daran denken muss. Geprüft: die
Datei war in keinem Commit und in keiner Verlaufsversion.

### Tooltip-System (`backend/app/regeln/`, `frontend/src/regeln/`)

Aus dem UI-Konzept, jetzt gebaut: **neben jedem Fachbegriff lässt sich eine
Erklärung aufklappen, ein Schieberegler in der oberen Leiste schaltet die
Zeichen überall zugleich an und aus.** Ohne den Schalter stünde neben 53
Begriffen dauerhaft ein Fragezeichen; wer die Regeln kennt, will das nicht.

- **Eigener Knoten `Erklaerung`**, nicht eine Eigenschaft am `TraitDef`.
  Zwei Gründe: erklärt werden soll *alles* auf dem Blatt, und Gesundheit,
  Initiative oder I.C.E. stehen gar nicht im Katalog. Und das Seeding setzt
  die `TraitDef`-Felder bei jedem Start neu — Texte, die dort lägen, wären
  bei der nächsten Katalogänderung in Gefahr.
- **Schlüssel** über den Helfer `schluessel` in `regeln/erklaerungen.ts`:
  `trait:Körperkraft`, `bogen:gesundheit`, `regel:<begriff>`. Nie von Hand
  zusammenbauen, sonst laufen Anzeige und Ablage auseinander.
- **Pro Regelwerk, nicht pro Kampagne** — was Widerstandsfähigkeit bedeutet,
  ist in jeder NeotopiA-Runde dasselbe.
- **Alle Texte werden einmal geladen** und liegen in einem Modulzustand.
  Einzeln nachzuladen hiesse eine Anfrage je Antippen, und die Oberfläche
  muss vorher wissen, wozu etwas hinterlegt ist — sonst stünde neben jedem
  Begriff ein Zeichen, das ins Leere führt. Bewusst kein Kontext: die Zeichen
  sitzen quer durch die Oberfläche, ein Provider müsste um alles herumgelegt
  und in jeder neuen Ansicht mitgedacht werden.
- **Schreiben darf nur die Spielleitung**, direkt im aufgeklappten Fenster.
  `InfoTipp` fragt die Rolle über `useAuthFallsVorhanden()` selbst ab — die
  Spielersicht steht ausserhalb des `AuthProvider`, deshalb die nicht
  werfende Variante. Der Server prüft ohnehin (`require_campaign_gm`).
- `quelle` unterscheidet `HAND` von `KI`: sobald Texte maschinell erzeugt
  werden, bleibt erkennbar, was noch niemand gegengelesen hat. Das Fenster
  schreibt es in die Unterzeile.
- Ein blasses Zeichen heisst "dazu ist noch nichts da" — die Spielleitung
  sieht so auf einen Blick, wo Text fehlt.

**Ein Knopf darf nicht in einem Knopf stecken.** Die Wertezeile `.cb-wert`
ist selbst ein Knopf (später: würfeln), das Erklärungszeichen auch. Deshalb
die Hülle `.cb-wert-zeile`, die beide nebeneinander hält.

### Erfahrungspreise nach Marks Zuordnung

*"Sphären haben auch nur ×2 und Arete ×4 wie ein Attribut."* Damit deckt sich
das Steigern mit den Freebees: **Arete zählt zu den Attributen, Sphären zu den
Fertigkeiten** — an beiden Stellen gleich. NeuroWeaving blieb auf ×5, weil
Mark "den Rest lassen wir so" gesagt hat; es ist beim Technomancer allerdings
das Gegenstück zu den Sphären. Bei Gelegenheit nachfragen.

### Erstellung auch für NPCs

Knopf *"Erstellung durchlaufen"* bei jeder Person in der Welt-Ansicht, öffnet
den Assistenten im Fenster. Auch für fertige Charaktere — die Spielleitung
muss eine verkorkste Erstellung nachbessern können; beim Absenden werden alle
Werte neu gesetzt. Im Fenster gibt die Erstellung ihre eigene Scrollfläche ab
(`.fn-inhalt .er-buehne`), zwei ineinander wären unbedienbar.

### Zwei Gegenstands-Klarstellungen

**"Ich kann bei Besitzer wechseln nur NPCs auswählen."** Kein Fehler: die
Auswahl blendet den *aktuellen* Besitzer aus, und die Monoklinge gehörte Ryu
bereits. Das Formular sagte aber nirgends, wem der Gegenstand gehört — in der
kampagnenweiten Übersicht ist die Besitzer-Überschrift oft weggescrollt.
Jetzt steht **"Gehört Ryu Tanaka (PC)"** über der Auswahl, und diese heisst
"An jemand anderen übergeben".

**Reitername in der SL-Übersicht.** `ermittleBereiche` benannte den
"mitgeführt"-Reiter nach dem ersten getragenen Behälter — quer über alle
Charaktere also nach dem Rucksack irgendeines Spielers, obwohl darin die
Sachen aller steckten. Der Parameter `einBesitzer` schaltet das ab, wenn
nicht nach genau einer Person gefiltert ist.

**Nicht nachstellbar:** Marks Bericht, Ryu sehe keine Gegenstände. Frisch
angemeldet zeigt das Inventar korrekt *Ausgerüstet 3* (Rucksack, Hermes Ikon,
Monoklinge), *Sonst gelagert 1* (Yamaha Rapier) und die Amulett-Karte unter
"Anderswo gesehen"; die Daten stimmen serverseitig ebenfalls. Verdacht: eine
Seite, die seit vielen HMR-Durchläufen offenstand (Stolperstein 7). Beim
nächsten Auftreten zuerst neu laden.

### Fenster bleiben auf dem Bildschirm

Die gestreute Lage (36-64 %) war nur ein Wunsch: bei 800px Breite ist das
Fenster 752px breit und ragte bei 64 % zur Hälfte hinaus. `Fenster.tsx` fängt
die Mitte jetzt nach dem Messen ein und rechnet die Aufzieh-Verschiebung
gegen die *eingefangene* Mitte — sonst zöge es an der falschen Stelle vorbei.
Passt es überhaupt nicht, steht es mittig.

### Zurückgestellt

**Wie Sphären mit Fertigkeitspunkten steigerbar werden**, hat Mark vertagt
(*"ich weiß die Logik noch nicht… frag mich später nochmal"*). Aktuell zählt
eine Sphäre als eine der acht Profi-Fertigkeiten. **Nicht eigenmächtig
umbauen** — nachfragen.

## Spieler-Inventar: Kacheln statt Liste (30.08.2026)

Marks Befund: *"das Inventar ist nur nicht gerade übersichtlich, diese →
Rucksack und → gelagert Buttons sollten im Gegenstand sein, und nicht außen,
es gibt als Ryu keine Möglichkeit die Gegenstände zu öffnen, hier ist nur
Text."*

Beides stimmte. Die Spielersicht war eine flache Textliste, unter jedem
Eintrag ein Knopfpaar zum Umlegen — die einzige hervorstechende Handlung der
ganzen Seite, und das Einzige, was man antippen konnte. Die Gegenstände
selbst liessen sich nicht öffnen.

**Jetzt dasselbe Kachelraster wie bei der Spielleitung**, und die Kachel
öffnet ein Fenster mit Bild, Beschreibung, Schaden/Rüstungsbonus,
Eigenschaften — und dem Umlegen. Wo etwas liegt, entscheidet man beim Ansehen
des Dings, nicht in der Übersicht.

- `items/GegenstandKachel.tsx` ist bewusst **nicht** `GegenstandRow` der
  Spielleitung: die trägt Sichtbarkeit, Besitzerwechsel, Vorlagen und
  Bild-Upload mit sich, von denen ein Spieler nichts sehen soll.
- Der aktuelle Aufbewahrungsort ist markiert **und abgeschaltet** — sonst
  sucht man, was der Knopf noch bewirken soll.
- Fremdes lässt sich ansehen, aber nicht umlegen (`onUmlegen` entfällt).
- **"Anderswo gesehen" ist jetzt ein Reiter** statt eines angehängten zweiten
  Blocks. Dadurch gibt es genau ein Raster, das sich ausmessen lässt, und die
  Auswahl bleibt eine einzige Entscheidung. Die eigenen Bereiche prüfen dafür
  zusätzlich den Besitz — sonst fischte "Mitgeführt" auch den Rucksackinhalt
  anderer heraus.
- Das Inventar ist der erste Spielerbereich mit `statisch`: feste Fläche,
  gemessenes Raster, geblättert statt gescrollt. Die Ausmessung liegt jetzt
  in `items/kachelraster.ts` und wird von beiden Seiten genutzt.

**Selbst hineingelaufen — Hooks hinter einer Abbruchbedingung.** Der neue
`useEffect`, der die Seitenzahl zurücksetzt, landete beim Einfügen *hinter*
`if (!ich) return null;`. Beim ersten Aufbau (noch kein angemeldeter Spieler)
lief er damit nicht, nach der Anmeldung schon — React bricht dann mit
*"Rendered more hooks than during the previous render"* ab und die Seite
blieb **komplett schwarz**. `npm run build` und TypeScript blieben grün; nur
im Browser war es zu sehen. Bei neuen Hooks in `SpielerAnsicht` und ähnlichen
Komponenten immer prüfen, ob sie vor der Abbruchbedingung stehen.

## Inventar als Fächer (30.08.2026)

Zweiter Anlauf nach Marks *"mir gefällt das Inventar noch nicht… ich hätte
gerne dass das mehr nach Computerspiel aussieht"*. Konzept und Begründung
stehen in `docs/ui-konzept.md`; hier nur, was technisch daran hängt.

**Fenster hängen jetzt am Seitenkörper (`createPortal`).** Das war die
Voraussetzung für Fenster in Fenstern: `.fn-fenster` trägt eine `transform`,
und ein `position: fixed` **innerhalb** eines transformierten Elements bezieht
sich nicht mehr auf den Bildschirm, sondern auf dieses Element. Ohne Portal
säße ein Fenster, das aus einem Fenster heraus aufgeht, im falschen
Bezugsrahmen. Mit Portal stapeln sie sich richtig, weil das später gehängte
später gezeichnet wird.

**`Bereich` hat ein Feld `greifbar`.** Nur der ausgerüstete Bereich ist es;
alles andere wird zum Fach in der unteren Leiste. Die frühere Mehrfachauswahl
über Reiter ist damit weg — es gibt genau eine Hauptansicht und Fächer, die
man aufmacht.

**Eigene Fahrzeuge und Behälter werden zu Fächern, auch leere.** Sie stehen
zusätzlich als gewöhnlicher Gegenstand in dem Bereich, in dem sie liegen —
das Fach zeigt nur, *was darin ist*, der Gegenstand hat Gewicht,
Beschreibung und lässt sich umlegen. Beides wird gebraucht.

*Zwischenschritt, den Mark verworfen hat:* das Fachfenster zeigte den
Behälter zuerst selbst unter einer Überschrift "Der Behälter". Sein Einwand:
*"das steht doch schon oben drüber, was das für ein Behälter ist, der Inhalt
reicht."* Stimmt — der Fenstertitel nennt ihn bereits. Die Erreichbarkeit
löst jetzt der Eintrag im Bereich statt eines eigenen Abschnitts.

**Umbenannt:** "Ausgerüstet" → **Am Körper**, "Sonst gelagert" → **Depot**
(klang nach Restposten), "Gelagert" → **Weggelegt**. Der mittlere Ablageplatz
heißt nach dem getragenen Behälter ("Abgewetzter Rucksack") statt abstrakt
"Mitgeführt" — wer einen Rucksack trägt, legt Dinge da hinein.

**Fächer stapeln sich (nachgezogen).** Aus dem Rucksack heraus soll sich ein
Behälter darin öffnen lassen — deshalb ist der Zustand ein *Stapel*
(`fachStapel: string[]`), kein einzelnes offenes Fach. Jede Stufe bekommt ein
eigenes Fenster; Schliessen auf Stufe *i* kürzt den Stapel auf *i* und räumt
damit alles darüber mit ab. Ein Behälter zeigt im Gegenstandsfenster einen
Knopf **"Hineinsehen"**, der die nächste Stufe aufmacht.

**Nichts kann in sich selbst liegen.** Der Ablageplatz "im Rucksack" wird für
den Rucksack selbst ausgeblendet (`behaelterId` an `GegenstandKachel`).
Vorher liess sich der getragene Behälter in sich hineinlegen — von Mark
gefunden.

**`.gg-fachraster` trägt Rückfallwerte für `--gg-kachel-*`.** Nötig, weil das
Fenster durchs Portal außerhalb von `.gg-seite` hängt und die dort gesetzten
Variablen nicht erbt.

## Fahrzeuge, Drohnen und Begleiter (30.08.2026)

Marks Vorgabe: Fahrzeuge sind *bestimmte* Objekte, nicht bloss Behälter — ein
Motorrad hat keinen Stauraum. Ein Rigger führt viele Drohnen und braucht dafür
eine eigene Übersicht. Und Sprites, Geister und Verbündete gehören in einen
gemeinsamen Bereich, weil sie eigene Blätter haben.

**Ein Blatt für vier Dinge.** Das Papierblatt in `Neotopia.xlsx` ist mit
*"Drohne / Fahrzeug / Sprite / Geist"* überschrieben — dieselben vier Werte
(Stufe, Widerstand, Angriff, Agilität), dieselben vier freien Fertigkeiten,
derselbe Gegenstand mit Schadensbonus. Die Stufe wird beim Erschaffen frei
darauf verteilt; **Gesundheit = Stufe**, Widerstand = Schadensreduktion,
Agilität = Geschwindigkeit.

**Fahrzeug und Drohne bleiben Gegenstände**, Sprite und Geist werden ein
eigener Knotentyp. Der Schnitt läuft entlang der Frage, ob man das Ding
besitzt und mit sich führt: ein Fahrzeug hat Preis, Gewicht und einen
Aufbewahrungsort und muss ins Inventar; einen Geist trägt man nicht im
Rucksack, und alles, was Gegenstände an Inventarlogik mitbringen, wäre bei ihm
sinnlos. Die Werte selbst sind in beiden Fällen dieselben.

- `Gegenstand`: neue Felder `istBehaelter`, `stufe`, `widerstand`, `angriff`,
  `agilitaet`, `fahrzeugFertigkeiten`. Neuer Typ **Drohne**.
- `app/begleiter/`: Knoten `Begleiter` mit `art` (SPRITE/GEIST/BEGLEITER),
  `-[:BEGLEITET]->` Person. Lesen darf jeder mit Zugang, schreiben nur die
  Spielleitung.

**`istBehaelter` ersetzt das Raten nach dem Typ.** Vorher galt "Typ Fahrzeug
oder Behälter ⇒ es passt etwas hinein". Jetzt steht es am Gegenstand und wird
in den Optionen angehakt. **Der Rückfall für Bestandsdaten muss an beiden
Stellen derselbe sein** — `_decode` *und* die Abfrage in
`moegliche_ablageziele`. Beim ersten Anlauf hatte ich in der Abfrage noch
`typ IN ['Fahrzeug','Behälter']` stehen, während `_decode` schon
`typ = 'Behälter'` lieferte: die Auswahl hätte ein Fahrzeug als Ziel
angeboten, das die Oberfläche gar nicht als Fach führt.

**Neue Bereiche im Menü** — beim Spieler *Fahrzeuge* und *Begleiter*, bei der
Spielleitung *Begleiter* (Fahrzeuge liegen dort in der Gegenstandsübersicht,
die ohnehin filtern kann). Beide neuen Spielerbereiche sind `statisch`:
Kachelraster, ausgemessen, geblättert.

**Ein Begleiter ist für seinen Besitzer immer sichtbar** — sonst müsste die
Spielleitung bei jedem Sprite an die Freigabe denken, und vergässe sie es,
stünde der Technomancer ohne sein Sprite da. Gleiches Muster wie bei den
Gegenständen. Notizen bleiben trotzdem beim Spielleiter.

**Testdaten:** Ryu hat jetzt ein Sprite *Kettenhund* (Stufe 4). Von mir
erfunden, damit der Bereich nicht leer ist — kann weg.

### Noch offen an dieser Ecke

- Das Fahrzeugblatt lässt sich bisher nur über die Gegenstandsoptionen
  pflegen; freie **Fertigkeiten** am Fahrzeug haben noch keine Oberfläche
  (Feld und Speicherung stehen, `fahrzeugFertigkeiten`).
- Die Regel *"Fertigkeiten werden zu den Drohnen-Attributen addiert, wenn sie
  kompatibel sind"* und das Riggen (eigene Werte bis zur Stufe der Drohne)
  sind nicht abgebildet.
- Für Begleiter fehlt eine serverseitige Prüfung, dass die verteilten Punkte
  die Stufe nicht übersteigen — die Oberfläche warnt nur.

## Als App auf dem Startbildschirm (30.08.2026)

`frontend/public/manifest.webmanifest` + Verweise in `index.html`. `display`
steht auf **fullscreen** (mit `display_override` auf standalone als Rückfall),
Hintergrund und Themenfarbe auf `#08080d`, damit beim Start kein weisses Bild
aufblitzt.

**Eigene Symbole** (`symbol-192.png`, `symbol-512.png`, `symbol-maskable-512.png`)
— das Sechseck mit Ring aus der Oberfläche, gezeichnet als Geometrie statt als
Schriftzeichen: ob ein Gerät die Glyphe "⌬" hat, ist Glückssache. Die
maskable-Fassung hat ein kleineres Motiv, weil Android die Ecken rund
abschneidet. Erzeugt mit einem Wegwerf-Skript und Pillow (danach wieder
deinstalliert); zum Ändern neu zeichnen, nicht nachbearbeiten. Die
Vite-Starter-Dateien `favicon.svg`/`icons.svg` (Bluesky-Symbolsatz) sind
entfernt.

> ⚠️ **`display: fullscreen` gilt nicht überall.** Auf dem **Desktop** kennt
> Chrome den Modus nicht und fällt auf `standalone` zurück: eigenes Fenster
> ohne Adressleiste, aber kein Vollbild. Das ist kein Fehler, sondern die
> Obergrenze dessen, was dort geht — echtes Vollbild gibt es am Desktop nur
> über F11 bzw. den Vollbildknopf in der Leiste. Randlos startet es nur auf
> **Android**.

> ⚠️ **Chrome installiert nur von einem sicheren Ursprung.** Über
> `http://192.168.178.21:5173` gilt die Seite als unsicher; "Zum
> Startbildschirm hinzufügen" legt dann nur eine Verknüpfung an, die im
> Browser-Tab aufgeht — **nicht** im Vollbild. Drei Wege: (a) auf dem Tablet
> unter `chrome://flags/#unsafely-treat-insecure-origin-as-secure` die Adresse
> `http://192.168.178.21:5173` eintragen und Chrome neu starten, (b) den
> Dev-Server mit HTTPS und selbstsigniertem Zertifikat betreiben und dieses am
> Tablet vertrauen, (c) beim späteren Deploy hinter nginx ohnehin mit echtem
> Zertifikat. Für den Heimgebrauch ist (a) der kürzeste Weg.

### Vollbild überlebt das Sperren nicht (Krücke gebaut)

Sperrt das Tablet den Bildschirm, beendet das System das Vollbild — und beim
Entsperren steht man wieder mit Adressleiste da. Von selbst zurückschalten
darf die Seite nicht: `requestFullscreen` ist **nur als Antwort auf eine
Nutzeraktion** erlaubt, sonst könnte jede Seite ungefragt den Bildschirm
übernehmen.

`shell/vollbild.ts` merkt sich deshalb den Wunsch und stellt ihn **beim
nächsten Antippen** wieder her. Scharf gestellt wird nur, wenn die Seite aus
dem Verborgenen zurückkommt — wer selbst Escape drückt, will heraus und bleibt
draussen. In der Praxis: entsperren, einmal irgendwohin tippen.

**Das ist die Krücke für den Browser-Tab.** Als installierte App entfällt das
Problem, weil dort das Fenster selbst randlos ist; der Vollbildknopf blendet
sich dann aus (`alsAppGestartet()`).

*Noch möglich, falls die Krücke nicht reicht:* ein **Wake Lock**, der den
Bildschirm während einer Sitzung gar nicht erst schlafen lässt. Bewusst nicht
eingebaut — das kostet Akku und gehört an einen Schalter, nicht in den
Autopiloten.

## Offene Punkte von Mark (30.08.2026, noch nicht gebaut)

1. **Reihenfolge auf dem Begleiter-/Fahrzeugblatt.** Derzeit steht die Stufe
   in einer Zeile mit Widerstand und Angriff. Sie gehört **allein ganz nach
   oben**: sie ist kein gleichrangiger Wert, sondern das Gesamtbudget — die
   Stufenpunkte *werden* in die anderen Werte gesteckt. Darunter dann Angriff,
   Widerstand, Agilität. Betrifft `BegleiterKachel.tsx`,
   `BegleiterVerwaltung.tsx` und den Fahrzeugblock in `CharacterSheetPanel.tsx`.

2. **Gegenstände: Schalter "immer sichtbar".** Ein Schwert oder Sturmgewehr
   kann man nicht am Körper tragen, ohne dass es jeder sofort sieht; anderes
   lässt sich unter der Kleidung verstecken. Marks Worte: *"das ist nicht
   wichtig, aber ich glaub es gefällt mir."* Also ein Feld am Gegenstand, das
   nur anzeigt — offen bleibt, ob und wo es Folgen hat (Heimlichkeit?
   Reaktionen von NPCs?).

3. **Riggen im Kampfmodus** — Antwort auf meine Rückfrage, wann eine
   Fertigkeit "kompatibel" ist:
   - Steuert der Rigger eine Drohne **manuell**, addiert sich seine passende
     Fertigkeit zum Wert der Drohne (Fahren → Fliegen/Bewegung, Schusswaffen →
     Angriff).
   - Handelt die Drohne **selbstständig**, zählen nur ihre eigenen Werte.
   - **Pro Kampfrunde lässt sich nur eine Drohne manuell steuern**, alle
     übrigen greifen automatisch an.
   - Welche Fertigkeit auf welchen Drohnenwert geht, ist **noch nicht
     festgelegt** — Mark will das gemeinsam definieren. Nicht eigenmächtig
     entscheiden.

   Gehört in den Kampfmodus, für den im Menü schon ein Platzhalter steht.

## Erstellung nach Marks erstem Durchklicken (30.08.2026)

- **"Normal" heisst jetzt "Weg des Chrom".** Marks Einwand: klingt fad. Wer
  weder zaubert noch webt, ist nicht der Rest — er hat sich für Chrom
  entschieden.
- **Attributzeilen gestapelt**: Name darüber, Punkte darunter linksbündig.
  Nebeneinander begannen die Punktreihen je nach Namenslänge woanders.
- **Fertigkeitswahl liegt im Fenster** (`er-spaltenraster`, spaltenweise
  gefüllt wie auf dem Blatt). Vorher hingen dreissig Fertigkeiten unter den
  Paketkarten: man musste scrollen, und die Spalten gerieten durcheinander.
- **Freebees arbeiten jetzt mit Punktreihen statt Plus-Knöpfen.** Damit sieht
  man den aktuellen Wert *und* wo die Reihe endet. Sie stehen für **alle**
  Werte offen, nicht nur für die bereits gewählten — vorher war eine neue
  Fertigkeit per Freebee gar nicht erreichbar. Hintergründe sind mit dabei,
  damit sich über die fünf freien Punkte hinaus welche kaufen lassen.

**Echter Fehler, von Mark gefunden: Freebees kamen über das Maximum.** Er hat
Körperkraft auf 9 gekauft. Zeile 24 des Regelblatts hebt nur den **StartMax**
der Rasse für Freebees auf, nicht das Maximum des Wertes selbst — ein Attribut
endet bei 6, eine Fertigkeit bei 5. `erstellung.pruefe` prüft das jetzt gegen
`defaultMax` aus dem Katalog; die Punktreihe in der Oberfläche zeigt dieselbe
Grenze.

### Vorlagen für Ambition und Verlangen

Zwanzig Archetypen als Anregung, abrufbar über einen Knopf neben den beiden
Feldern. **Die Texte liegen nicht im Code**, sondern in
`backend/data/vorlagen.local.json` — sie stammen aus dem Magus-Regelwerk und
sollen das Gerät nicht verlassen, bevor sie auf NeotopiA umgeschrieben sind.
Die Datei ist ignoriert; fehlt sie, liefert die Route eine leere Liste und der
Knopf erscheint gar nicht. Erzeugt wurde sie mit einem Wegwerf-Skript aus
`docs/reference/Regel Details - infotipp optionen.txt`.

### Nach dem zweiten Durchklicken

- **Freebees stehen dreispaltig** wie das Blatt (`er-spaltenraster`).
- **Vorschläge zeigen nur den Namen**, der Text steht hinter einem
  Fragezeichen und geht als weiteres Fenster auf — teils zwanzig Zeilen lang,
  in der Liste war das unlesbar. Das Fragezeichen benutzt bewusst dieselbe
  Klasse `.it-zeichen` wie das Tooltip-System, damit es überall gleich aussieht.
- **Die Spielleitung sieht denselben dreispaltigen Bogen wie der Spieler** —
  Knopf *"Bogen ansehen"* je Person. Die Bearbeitungsmaske daneben bleibt für
  alles, was man *ändert*.

**Fenster können jetzt `breit`.** Der Bogen passt in die üblichen 680px nicht:
die Punktreihen brachen um und die Namen wurden gekürzt. `fn-fenster-breit`
gibt 1040px. Dazu setzt `.fn-inhalt .cb-blatt` dieselben engeren Masse wie die
900px-Media-Query — **die misst den Bildschirm, nicht das Fenster**, und griff
deshalb nie. Wer künftig Blattinhalte in Fenster steckt, muss daran denken.

### Weiter offen an der Erstellung

- **Mehr Hintergründe kaufbar**: Mark überlegt, ob es mehr als fünf freie
  Punkte geben soll und ob beim Antippen eines Hintergrunds ein Fenster mit
  der Erklärung aufgehen soll. Vorerst bleibt es bei fünf plus Zukauf über
  Freebees.
- Der eigene Schritt für Hintergründe ist streng genommen redundant, seit sie
  auch bei den Freebees stehen — bewusst gelassen, weil die fünf Punkte sonst
  zwischen allem anderen untergehen.

## Ein Blatt statt zweier Ansichten (30.08.2026)

Mark hatte die Wahl gestellt: das Bearbeitungsformular ebenfalls dreispaltig
machen — oder **eine** Ansicht mit einem Schalter aufs Bearbeiten. Der zweite
Weg ist der bessere und ist umgesetzt.

`Charakterblatt` nimmt jetzt `bearbeitbar` (die Spielleitung setzt es). Dann
steht in der Kopfzeile **⚙ Bearbeiten**; eingeschaltet werden aus den
Wertezeilen gestrichelte Zeilen mit anklickbaren Punkten, und ein zweiter
Schalter **Maxima** blendet je Wert ein `−  6  +` ein, um die Obergrenze
einzelner Werte anzuheben (die Elder-NPC mit Schusswaffen 8).

**Im Bearbeiten-Modus ist die Zeile kein Knopf mehr**, sondern ein `div`: das
umschliessende `<button>` fing sonst den Klick ab, bevor er bei den Punkten
ankam. Und nach jeder Änderung wird das ganze Blatt neu geladen, weil die
abgeleiteten Werte daran hängen — Widerstandsfähigkeit auf 5 zu setzen hob die
Gesundheit im Test korrekt von 7 auf 10.

**Knöpfe umbenannt**: *Charakterblatt* öffnet den Bogen (mit dem Schalter),
*Gegenstände* öffnet die alte Maske. Deren Werte-Liste ist damit doppelt und
könnte weg, sobald klar ist, dass niemand sie vermisst — der Gegenstandsteil
dort ist weiterhin die einzige personenbezogene Item-Ansicht neben dem
kampagnenweiten Bereich.

## Die Probe: eine Rechenhilfe, kein Würfel (30.08.2026)

`traits/Probe.tsx`. Fertigkeit antippen → Fenster mit den neun Attributen in
drei Spalten (jede Zeile zeigt schon die Summe, dann sieht man beim Wählen,
worauf es hinausläuft) → zweites Fenster darüber mit der **Zahl gross**, dem
W10 daneben, der Rechnung darunter und einer Zeile "1-5 Misserfolg · 6-10
Erfolg".

> **Das Werkzeug würfelt nicht.** Marks Vorgabe: gewürfelt wird am Tisch, mit
> echten Würfeln. Die Anzeige sagt nur, wie viele man nehmen darf.

**Arete geht nicht mit Attributen** (Zeilen 81-86, `traits/magie.ts`). Ein
kontrollierter Zauber ist nur der Arete-Wert; dazunehmen lässt sich allein
**Willenskraft** — das ist *Wilde Magie*, Bonuswürfel bis zur Höhe der eigenen
Willenskraft. Die Anzeige hat dafür eine eigene Reihe mit −/+, begrenzt auf die
Willenskraft, und blendet ab dem ersten wilden Würfel den **Rückstoss** ein:
Zielwert vorher ansagen, danach Willenskraftwurf gegen die Erfolge, was nicht
abgedeckt ist, kommt als Schlagschaden zurück.

**Auf Sphären wird nicht gewürfelt** (Zeile 87). Antippen zeigt stattdessen,
*was damit geht*: die Kurzbeschreibung der Sphäre und die fünf Stufen von
"wahrnehmbar" bis "nach meiner Größe beurteilst du mich", die erreichte
hervorgehoben. Sie sind Fähigkeit und Begrenzung, keine Bonuswürfel.

Die Regeltexte dafür stehen in `traits/magie.ts` — aus Marks eigenem Blatt,
nicht aus fremdem Material, deshalb dürfen sie im Code stehen.

Der Aufhänger `onWertGewaehlt` am Charakterblatt bleibt bestehen und hat
Vorrang: wer die Zeile für etwas anderes braucht (Kampfmodus), hängt sich dort
ein, sonst geht die Rechenhilfe auf.

*Selbst hineingelaufen:* die Werte-Karte des Blatts ist nach **TraitDef-Kennung**
verschlüsselt, nicht nach Namen. Beim ersten Anlauf suchte `Probe` nach Namen —
alle Attribute hätten 0 angezeigt. Vor dem Ausliefern gemerkt, aber der Build
war grün.

### Zwei Regelfragen, die dabei aufgetaucht sind

1. **Wann folgt der Willenskraftwurf?** Zeile 80 ("Magie Regeln neu") sagt
   *nach dem Zaubern* — also nach jedem. Zeile 84 sagt *nach jedem gelungenen
   **wilden** Zauber*. Die Anzeige nennt den Rückstoss derzeit nur bei wilder
   Magie. Gilt Zeile 80, muss der Hinweis immer stehen. **Mark fragen.**
2. **Woraus besteht der Pool beim NeuroWeaving?** Zeile 96: die Punkte sind
   *Bonuswürfel für die jeweilige Aktion*, und man darf auch Fertigkeiten ohne
   Punkte einsetzen. Der Grundwurf ist damit ein anderer (beim Decken etwa
   Intelligenz + Matrix, Zeile 101), auf den NeuroWeaving obendrauf kommt.
   Derzeit behandelt die Anzeige NeuroWeaving wie Arete — die vorsichtige
   Näherung, nicht die Regel. **Mark fragen.**

### Idee für später: doch würfeln lassen

Mark: *"grundsätzlich soll das Programm nicht für einen würfeln… wir können
einen globalen Schalter machen der das erlaubt, ähnlich wie der mit dem
Gewicht, eventuell will mal jemand anders das Tool verwenden."* Zieht nach
sich, dass **Spielleitung und Mitspieler die Ergebnisse sehen müssen** — sonst
könnte jeder nachwürfeln, bis es passt. Also: Wurf-Ereignisse mit Zeitstempel,
eine Anzeige für die Runde, vermutlich über dieselbe Live-Verbindung wie die
SL-Popups (Phase 5). Eigene Design-Runde.

## NeuroWeaving bekommt einen eigenen Wert, Decks geben Bonuswürfel (30.08.2026)

Marks Frage: *"ich überlege ob es Sinn macht einen eigenen NeuroWeaving-Wert
zu machen, und dann würde man NeuroWeaving + einen der 4 NeuroWeaving-Werte
würfeln — das würde es vereinfachen oder?"* Ja. Damit ist NeuroWeaving
strukturgleich zu Arete + Sphären, mit **einem** Unterschied: die vier
Fertigkeiten zählen mit (Zeile 45/96), Sphären nicht (Zeile 87).

- Neuer Katalogwert **NeuroWeaving** in eigener Kategorie `NeuroWeavingWert`
  (Maximum 10, wie Arete). Die vier Fertigkeiten bleiben in `NeuroWeaving`.
  Eigene Kategorie statt Namensprüfung, damit Preise, Sichtbarkeit und
  Gruppierung sauber daran hängen — dieselbe Trennung wie Arete/Sphäre.
- **Preise entsprechend**: der Wert kostet wie ein Attribut (Freebee 5,
  Erfahrung ×4), die Fertigkeiten wie Fertigkeiten (2 bzw. ×2).
- **Pool-Deckel 10** (`NEUROWEAVING_POOL_MAX` in `traits/magie.ts`): Wert +
  Fertigkeit ergeben höchstens zehn Würfel. Bewusst ein Deckel auf dem *Pool*,
  nicht auf den Werten — die dürfen weiter steigen, es gibt nur keine Würfel
  mehr dafür. Die Probe zeigt "gedeckelt auf 10" statt still zu kürzen.

### Cyberdecks

`Gegenstand` bekommt **B/S/D/K** (`deckBruteForce`, `deckSchleichen`,
`deckDaten`, `deckKompilieren`, Regelblatt Zeile 157). `deck_boni()` liefert
sie je Person, und zwar:

- nur aus **ausgerüsteten** Decks — eines im Rucksack nützt niemandem,
- **je Aktion das höchste, nicht die Summe** (Marks Vorgabe). Sonst wäre das
  Stapeln von Geräten die einzige sinnvolle Bauweise.

Der Bogen liefert sie als `deckBoni` neben der Übersicht — sie gehören zur
Ausrüstung, nicht zu den Werten der Person. Die Probe bietet sie im
Ergebnisfenster als *eine* wählbare Zugabe an; man tut ja eines nach dem
anderen.

Geprüft mit zwei Wegwerf-Decks (4/1/2/2 und 1/3/2/5): heraus kam 4/3/2/5, also
je Aktion das beste. Eines weggelegt → Werte fallen auf das verbliebene zurück.

### Offen

- **Wie hoch dürfen NeuroWeaving-Fertigkeiten steigen?** Mark wusste es nicht.
  Derzeit 5 wie Fertigkeiten, der Wert selbst 10 wie Arete — der Pool-Deckel
  greift also ab Wert 5 + Fertigkeit 5.
- Welche Matrix-Aktion welchen Buchstaben nutzt, steht im Regelblatt; **womit
  der Decker grundsätzlich würfelt** (Zeile 101: Intelligenz + Matrix) ist in
  der Probe noch nicht verdrahtet — man wählt Fertigkeit und Attribut von Hand
  und legt den Deck-Bonus dazu.
- **Erledigt:** alle elf Cyberdecks aus dem Regelblatt (Zeilen 159-169) liegen
  als besitzerlose **Vorlagen** in der Testkampagne, mit B/S/D/K, Cyberwall-
  Bonus und Preis. Vier waren schon da und wurden ergänzt, sieben neu angelegt.
  Sie sind `einzigartig: false` — mehrere Spieler dürfen dasselbe Modell haben.
  Für Proteus Poseidon, Tlaloc, Tachikoma und Hosaka nennt das Blatt **keinen
  Preis**; dort steht 0, was hier "nicht im Regelwerk" heisst, nicht "gratis".
- Die sechs **Commlinks** waren bereits vollständig (Cyberwall 1-6, Preise
  100-8.000¥). **Riggerkonsolen** gibt es noch keine — die Tabelle daneben
  (Zeilen 159-167: Rigger-Bonus und maximale Drohnenzahl) ist noch nicht
  abgebildet, und für "Rigger-Bonus" und "Max Drohnen" fehlen die Felder.

## Kampfmodus (30.08.2026)

Die Initiativliste, **die alle am Tisch sehen** — Marks Kernpunkt: jeder soll
wissen, wann er dran ist, ohne zu fragen. Die Spielleitung führt sie, alle
anderen lesen mit.

**Reihenfolge nach Regelblatt** (Zeilen 57-59), sortiert **serverseitig**,
damit niemand eine andere Reihenfolge sieht als sein Nachbar:

- Initiative absteigend (Geistesschärfe + Geschicklichkeit + Cyberware),
- bei Gleichstand **Matrix vor Nahkampf vor Fernkampf**,
- bei völligem Gleichstand nach Namen — sonst springt die Liste bei jedem
  Nachladen, und das mitten im Kampf.
- Die **Ansagereihenfolge** (umgekehrt, Zeile 59) steht als Zeile darunter.

`backend/app/kampf/`, ein `Kampf`-Knoten je Kampagne mit
`KampfTeilnehmer`-Knoten daran. Teilnehmer als eigene Knoten, weil Neo4j keine
Listen aus Objekten kann und ein Teilnehmer ohnehin auf eine Person oder einen
Begleiter zeigt. Wer **weder noch** ist (namenlose Wache), braucht keinen — der
Verweis ist optional.

**`amZug` speichert eine Kennung, keine Position.** Kommt jemand mitten im
Kampf dazu, verschiebt sich die Reihenfolge; eine Position zeigte danach auf
jemand anderen.

### Was die Spielleitung kann

Kampf beginnen und beenden, Teilnehmer aufnehmen (Personen und Begleiter aus
der Auswahl, oder frei benannt für die Wache Nummer drei), **Nächster ›**,
jemanden direkt ans Ruder setzen, abhaken, entfernen — und **▤ öffnet den
Bogen** des Betreffenden, egal ob PC, NPC oder Begleiter. Die Initiative wird
beim Aufnehmen aus dem Bogen **vorgeschlagen**, nicht verordnet: Cyberware und
Drogen kennt das Werkzeug noch nicht.

### Nachladen statt Live-Verbindung

Marks Frage, ob das nicht Phase 5 sei: der **Live**-Teil schon. Gebaut ist es
mit einer Abfrage alle drei Sekunden (`useKampf`) — die Oberfläche sieht
genauso aus, wie sie später aussehen wird, nur die Bezugsquelle wird
ausgetauscht. Für eine Runde mit vier Leuten ist das nichts, und es läuft nur,
solange die Seite sichtbar ist; ein Tablet in der Tasche zählt nicht mit.

Die Schleife läuft in der Spieleransicht **dauerhaft**, nicht nur im
Kampfbereich — damit später eine Meldung "du bist dran" von überall aufgehen
kann.

**Geprüft:** Straßensamurai 9 vor drei Gleichständen auf 7, dort Decker
(Matrix) vor Ryu (Nahkampf) vor Wache (Fernkampf). Fünfmal weiter → Runde 2.
Der Spieler sieht dieselbe Liste, seine Zeile mit "du" markiert, ohne
Bedienknöpfe, und zieht nach dem Weiterschalten innerhalb des Takts nach.
Schreibversuch als Spieler: 403.

### Offen

- **Meldung "du bist dran"** ausserhalb des Kampfbereichs — dafür ist die
  Schleife schon da, es fehlt die Anzeige (gehört zum Blitz-Symbol aus dem
  UI-Konzept).
- **Rigger im Kampf**: die Regel steht (manuell gesteuerte Drohne addiert die
  Fertigkeit, eine pro Runde, der Rest handelt selbstständig), die Zuordnung
  Fertigkeit → Drohnenwert fehlt noch. Ohne sie keine Umsetzung.
- Ausweichen und Parieren mit ihrem kumulativen −1 je Einsatz pro Runde
  (Zeilen 62-63) sind nicht abgebildet.

## Kampfkarte und das mitblutende Gerät (30.08.2026)

### Kampfkarte

`kampf/Kampfkarte.tsx` — alles, was im Gefecht gebraucht wird, **fertig
ausgerechnet**, statt es im Bogen zu suchen:

- Gesundheit und Willenskraft als Kästchen, Initiative
- **Treffen** je Kampffertigkeit (Geschicklichkeit + Fertigkeit, Zeile 62)
- **Ausweichen** (Geschicklichkeit + Sportlichkeit) und **Parieren**
  (Geschicklichkeit + Waffenfertigkeit), beide mit dem Hinweis auf das
  kumulative −1 je weiterem Einsatz in derselben Runde (Zeilen 62-63)
- **Rüstung** als Summe der ausgerüsteten Stücke, **Schaden** je Waffe —
  im Nahkampf mit Körperkraft dazu (Zeile 67)
- je nach Weg **Arete + Sphären** oder **NeuroWeaving + Fertigkeiten**,
  dazu die **Deck-Boni**, wenn ein Cyberdeck ausgerüstet ist
- **Begleiter und Fahrzeuge** als Kacheln, ihre Blätter gehen als Fenster auf
- ganz unten *Ganzer Bogen* — Fenster über Fenster

Die Spielleitung erreicht sie über ▤ in der Initiativliste (statt wie vorher
den ganzen Bogen — im Gefecht braucht man die Werte, nicht die Biografie), der
Spieler sieht seine eigene unter der Liste.

**Der Rüstungsabzug ist eine Auslegung.** Zeilen 131-132 sagen, Rüstung 3
kostet 1 Geschicklichkeit und 4 kostet 2 — aber nicht, ob der Wert je Stück
oder in Summe zählt. Umgesetzt ist die **Summe**, sonst bliebe der Abzug bei
drei leichten Westen aus, die zusammen mehr schützen als ein schwerer Anzug.
Der Abzug ist in Treffen, Ausweichen und Parieren schon eingerechnet und steht
als Hinweis an der Rüstung.

### Das Gerät blutet mit

`shell/Verwundung.tsx`. Vom unteren Rand steigt ein dunkles Rot auf, je mehr
Gesundheit fehlt — **nicht flächig**: ein rot überzogener Bildschirm wäre nach
zwei Minuten unerträglich, ein Schein am Rand bleibt lesbar. Bleiben zwei
Kästchen oder weniger, pulst es langsam (2,4 s — Herzschlag, nicht Alarm).

Liegt auf `z-index: 90`, also über dem Inhalt und unter den Fenstern, und
nimmt keine Eingaben an. `prefers-reduced-motion` schaltet das Pulsen global ab
(Regel in `index.css`).

Der Zustand kommt über `useZustand` alle fünf Sekunden — nötig, weil auch die
Spielleitung Schaden einträgt; ohne Nachfragen bliebe der Bildschirm heil,
während die Figur längst blutet. Gleiche Bauart wie `useKampf`, läuft nur bei
sichtbarer Seite.

**Geprüft** bei 6 von 8 Schaden: Anteil 0,75, Pulsen an, über dem Inhalt, keine
Fehler. Die Kampfkarte zeigte alle Blöcke mit den gerechneten Zahlen.
Ryus Schaden danach wieder zurückgesetzt.

### Offen an dieser Ecke

- **Wie stark soll das Rot werden?** Aktuell bewusst zurückhaltend. Ohne Marks
  Blick darauf ist jede Verstärkung geraten.
- **Soaken**: das Regelblatt kennt nur "Rüstungsbonus wird abgezogen"
  (Zeilen 66-67), keinen Widerstandswurf. Falls Widerstandsfähigkeit doch
  mitspielt, fehlt die Zahl auf der Karte.
- **Riggen** steht weiter aus (Zuordnung Fertigkeit → Drohnenwert), ebenso das
  kumulative −1, das derzeit nur als Hinweis dasteht statt mitgezählt zu werden.

## Willenskraft, Herzschlag, antippbares Arete (30.08.2026)

### Willenskraft ist eine Einbahnstrasse für Spieler

Marks Regel: *"der Spieler kann Willenskraft verbrauchen, aber nur der SL kann
sie wieder herstellen."* Sonst wäre der Vorrat unbegrenzt und das Erzwingen von
Erfolgen gratis.

Die Regel steht als `zustand_verboten()` in `traits/bogen.py` — eine reine
Funktion, damit sie prüfbar ist (`tests/test_zustand.py`), und die Route ruft
sie nur auf. **Schaden bleibt bewusst in beide Richtungen offen**: Verletzungen
heilen nach eigenen Regeln, und wer sich vertippt, soll das richtigstellen
können.

Die Oberfläche bietet den Klick gar nicht erst an, wenn er verboten wäre —
niemand soll gegen eine stumme Wand tippen. Der Server lehnt trotzdem ab
(403), die Anzeige ist kein Schutz.

**Vor dem Ausgeben kommt eine Rückfrage** (`traits/WillenskraftFrage.tsx`).
Marks Einwand: ein Kästchen ist schnell versehentlich getroffen, und
zurückholen kann es nur die Spielleitung — ein Fehlgriff kostet also echt
etwas. Das Fenster nennt, wieviel danach übrig bleibt, und hat **Ja in Blau,
Nein in Rot**, beide 56px hoch und weit auseinander. Dieselbe Farbsprache wie
das Level Up: blau heisst weiter, rot heisst lass es.

**Wie Willenskraft zurückkommt** steht mit dabei — durch **Schlaf**, oder wenn
der Charakter seiner **Ambition** oder seinem **Verlangen** entsprechend
handelt, oder ein **Ziel** erreicht. Erste Fassung hiess "Zurück gibt sie nur
die Spielleitung"; Marks Einwand traf: das sagt nur, wen man fragen muss, nicht
wofür es sich lohnt. Damit hängen die drei Textfelder der Bogen-Kopfzeile
erstmals an einer Regel — sie sind nicht bloss Beiwerk.

**Damit hängt zusammen:** wilde Magie darf nur die **übrige** Willenskraft
nutzen, nicht den Gesamtwert. Wer sie ausgegeben hat, um Erfolge zu erzwingen,
kann sie nicht nochmal in einen Zauber stecken. Vorher rechnete die Probe mit
`willenskraftMax` — das war schlicht falsch.

### Arete und NeuroWeaving sind auf der Kampfkarte antippbar

Öffnet dieselbe Probe wie im Bogen, also die Reihe für wilde Magie mitsamt
Rückstoss-Hinweis. Die Zahl-Kachel wird dafür zum Knopf (`kk-zahl-knopf`).

### Herzschlag statt Pulsen

Ein Herzschlag ist kein gleichmässiges Auf und Ab, sondern **zwei Stösse dicht
hintereinander und dann eine Pause** — genau das macht ihn erkennbar. Die
Animation hat deshalb zwei Spitzen im ersten Drittel und danach Ruhe, dazu
einen leichten `scaleY` vom unteren Rand her. Deutlich kräftiger als vorher
(Marks Wunsch), aber immer noch am unteren Rand statt flächig.

## Bekannte Stolpersteine (nicht nochmal reinlaufen)

1. **`passlib` + neueres `bcrypt`**: inkompatibel (passlib ist unmaintained, `bcrypt>=4.1` hat `__about__` entfernt). Lösung: `bcrypt`-Paket direkt nutzen, kein passlib. Ist bereits so umgesetzt in `auth/security.py`.
2. **`uvicorn --reload` auf Windows**: der Reloader-Parent-Prozess kann sterben während der Worker-Kind-Prozess weiterläuft und alten Code weiter serviert (WatchFiles-Bug/Windows-Eigenheit). Wenn nach einem Reload etwas nicht wie erwartet reagiert: beide PIDs (Parent + Worker, `netstat -ano | grep :8000` dann `taskkill //F //PID X`) killen und ohne `--reload` neu starten.
3. **`react-cytoscapejs`-Wrapper**: hatte einen Bug — rief bei jedem Re-Render ein Re-Layout auf und verlor dabei den Klick-Handler. Komplett entfernt, Cytoscape wird jetzt direkt (imperativ, via `useRef`) angesteuert in `graph/CampaignGraphView.tsx`.
4. **Cytoscape + `box-sizing`**: Cytoscape hat einen eingebauten `ResizeObserver` auf dem Container. Ohne globales `box-sizing: border-box` (jetzt in `index.css` gesetzt) addiert sich ein `border` zur `width:100%`-Breite dazu → minimaler Overflow → Scrollbar erscheint/verschwindet → ResizeObserver feuert erneut → Endlosschleife, die sich sichtbar "aufschaukelt" (Container wächst langsam immer weiter). Fix: globales `box-sizing: border-box` + Cytoscape-eigenen Resize nicht durch einen zweiten, redundanten manuellen Call stören.
5. **Cytoscape Initial-Messung zu früh**: Falls der Container beim `cytoscape({container:...})`-Aufruf noch nicht final gelayoutet ist (z.B. direkt nach Tab-Wechsel), kann die interne Erstmessung falsch/zu klein ausfallen und bleibt es auch (Canvas nur "halb" befüllt, Klick-Koordinaten verschoben). Fix: `requestAnimationFrame` nach Konstruktion, das explizit `cy.resize()` + `cy.fit()` erzwingt, nachdem der Browser das Layout tatsächlich committed hat. War hier lange nur als Plan dokumentiert, aber nie tatsächlich im Code umgesetzt (Diskrepanz erst beim Debuggen von Stolperstein #8 aufgefallen) — jetzt in `CampaignGraphView.tsx` als doppeltes `requestAnimationFrame` + `window`-`resize`-Listener implementiert.
6. **TypeScript + `verbatimModuleSyntax` + `@types/cytoscape`**: der `type Stylesheet = A | B` Union-Alias aus dem `export =`-Namespace lässt sich unter `verbatimModuleSyntax` nicht als `cytoscape.Stylesheet` referenzieren (TS-Fehler "no exported member"), obwohl er existiert — vermutlich weil `type`-Aliase (im Gegensatz zu `interface`s) beim Namespace-Merge über einen Default-Import unter dieser strikten Einstellung nicht sauber aufgelöst werden. Workaround: das nominale `interface StylesheetStyle` statt des Union-`type Stylesheet` referenzieren, funktioniert identisch für unseren Anwendungsfall.
7. **Vite Hot-Reload + Cytoscape**: bei größeren Änderungen an Komponenten, die eine imperative Canvas-Bibliothek verwenden, lieber den Dev-Server komplett neu starten (`node_modules/.vite`-Cache löschen) statt sich auf HMR zu verlassen — HMR kann alte Instanzen hinterlassen, die mit neuen um denselben Container konkurrieren.
8c. **Browser-Pruefungen veraendern echte Daten.** Ein Testlauf, der "den
   ersten freien Ablage-Knopf" antippt, verschiebt tatsaechlich einen
   Gegenstand — nach einem Durchgang lag Ryus Monoklinge im Rucksack statt am
   Guertel. Bei Skripten, die Knoepfe druecken: entweder auf eigens angelegten
   Testdaten arbeiten oder den Ausgangszustand am Ende wiederherstellen — und
   danach nachsehen, ob er wirklich wieder stimmt.

8b. **Blindes Ersetzen kurzer CSS-Selektoren zerschneidet Regeln.** Beim
   Einfuegen der `.cb-wert-zeile`-Regeln habe ich auf `".cb-wert {"` ersetzt —
   und damit die *erste* Fundstelle getroffen, die zu
   `.cb-werte-einzeln .cb-wert {` gehoerte. Uebrig blieb ein globales
   `.cb-wert { flex-direction: column }`: **jede** Wertezeile im Blatt stand
   danach untereinander statt nebeneinander. Der Build blieb gruen, TypeScript
   auch — aufgefallen ist es erst beim Nachmessen im Browser. Bei kurzen
   Selektoren immer genug Kontext mitnehmen (die Zeile davor) oder an einem
   eindeutigen Anker einfuegen.

8. **Cytoscape-Canvas verschoben durch `text-align: center`**: `index.css` setzt global `#root { text-align: center; }`. Cytoscapes interne `<canvas>`-Layer sind `position: absolute` mit `left`/`right: auto` (Cytoscape selbst setzt nie ein explizites `left`). Bei `left/right: auto` berechnet der Browser die "static position" eines ursprünglich inline-artigen Elements (canvas ist von Haus aus `display: inline`) unter Berücksichtigung des geerbten `text-align` — bei `center` verschiebt das die komplette Canvas nach rechts um ungefähr die halbe Canvas-Breite (reproduzierbar auf jedem Gerät mit `devicePixelRatio != 1`, unabhängig von Bildschirmgröße). Symptom: linke Hälfte des Graphen leer/schwarz, Klick-Koordinaten um denselben Betrag versetzt. War der Bug hinter dem lange als "Graph-Sizing-Bug" verfolgten Problem — **nicht** der ursprünglich vermutete `box-sizing`/`ResizeObserver`- oder `pixelRatio`-Bug. Gefunden per Headless-Browser-Debugging (`cy.pan()`/`cy.zoom()`/Node-Positionen waren intern korrekt — nur das `<canvas>`-DOM-Element selbst war falsch positioniert). Fix: `textAlign: "left"` explizit auf dem Graph-Container in `CampaignGraphView.tsx` setzen (überschreibt lokal das geerbte `center`, ohne die globale Zentrierung zu ändern).

9b. **Cypher: `WITH` zwischen schreibender Klausel und `MATCH`.** Nach `CREATE`, `SET` oder `DELETE` verlangt Neo4j ein `WITH`, bevor erneut gematcht werden darf ("WITH is required between SET and MATCH"). Die Item-Abfragen haben deshalb zwei Varianten desselben `OPTIONAL MATCH`: `LIEGT_IN` und `LIEGT_IN_NACH_CREATE`. **Die WITH-Variante nur dort einsetzen, wo ausser `g` keine weitere Variable ins `RETURN` muss** — `WITH g` wirft alles andere weg und würde z.B. `list_alle_gegenstaende` zerstören, das `p` für den Besitzer braucht. Beim ersten Anlauf nur an `CREATE` gedacht; `SET` fiel erst beim Testen auf.

9. **Neue Pydantic-Response-Felder + Bestandsdaten ohne diese Property = 500 auf der ganzen Liste**: Als `Gegenstand` um `typ`/`eigenschaften`/`zeigeInGraph`/`bildUrl` erweitert wurde, hatte `items/repository.py::_decode()` Fallbacks für drei der vier neuen Felder, aber `typ` vergessen. Ein einziger alter Gegenstand ohne `typ`-Property (Neo4j gibt dafür `null` zurück) ließ die Pydantic-Validierung von `GegenstandResponse.typ: str` (nicht optional) fehlschlagen → 500 auf `GET .../gegenstaende` → riss die komplette `CharacterSheetPanel`-Anzeige mit runter (Werte UND Gegenstände laden im selben `Promise.all`, ein Fehler lässt beide leer/unsichtbar erscheinen), obwohl die Werte selbst unbeteiligt waren. Symptom war "Charakterblatt komplett weg", nicht ein Fehler zum konkreten Feld. **Lektion**: bei jeder neuen Property auf einem bestehenden Node-Typ IMMER einen `coalesce`/Fallback in der Decode-Stelle einbauen, für JEDES neue Feld einzeln prüfen, nicht nur die "offensichtlichen" (bool/JSON) — und nach Schema-Erweiterungen kurz gegen die Bestandsdaten der Testkampagne verifizieren (`MATCH (g:Gegenstand) RETURN g.typ, ...` direkt in Neo4j), nicht nur gegen frisch angelegte Testdaten.

## Nächste Schritte

*(Stand 29.08.2026. Seit dem letzten Eintrag dazugekommen: Fenstersystem, "nie scrollen" für Gegenstände und Graph, kompletter Spieler-Zugang inkl. Oberfläche, Aufbewahrungsorte und Gewicht.)*

1. **Bereich "Welt" scrollt noch als einziger** — er muss sich erst selbst einteilen, bevor er `statisch` bekommen kann. Dieselbe Frage wie bei den Gegenständen: Kacheln oder Tabelle, Blättern, Suche. Bewusst nicht blind nach dem Kachel-Muster umgebaut, solange Mark das nicht bestätigt hat. Zielbild bleibt der feinere Schnitt (PCs und NPCs getrennt, Orte und Events einzeln).
2. **Rest von Phase 3** — Box-Tracks (Gesundheit/Willenskraft/I.C.E.), Cyber-/Bio-Ware-Slots, Waffen-/Rüstungswerte am Charakter, Companion-/Drohnen-Bögen, Würfeln.
3. **Aus dem UI-Konzept noch offen**: Kampfmodus, Regeln-Bereich, Notizen, das Tooltip-System mit Schalter in der oberen Leiste — alle drei stehen als "bald" im Menü.
4. **Offene Design-Runden** (Datenmodell jeweils ungeklärt): Party/Gruppen-Konzept · EP-System mit den drei Charakterbogen-Modi · typspezifische Gegenstandsfelder (Cyberware→WVerlust, Drogen→Wirkung/Dauer) + Upgrade-System.
5. **Kleinere Schulden** — verwaiste Bilddateien nach "Bild entfernen" · Graph zeigt `SPEZIFISCH` optisch wie `ALLE` · Traglast rechnet nicht rekursiv (gefüllter Rucksack im Auto zählt nur mit Eigengewicht) · Spieler dürfen bisher nur die Ablage-Art ändern, nicht das konkrete Ziel.

**Server-Status:** Neo4j läuft durchgehend in Docker (Port 7687). Backend auf `127.0.0.1:8000` (bewusst nur localhost, siehe LAN-Abschnitt unten; ohne `--reload`, siehe Stolperstein #2). Frontend mit `npm run dev` auf Port 5173, lauscht dank `host:true` in `vite.config.ts` auf allen Interfaces (kein `--host`-Flag mehr nötig). Falls nach einem Reboot nichts erreichbar ist: siehe "Wie man lokal startet" oben.

## Zugriff vom Handy / LAN (eingerichtet, für Tests unterwegs)

Frontend (Vite) läuft mit `--host`, ist also im LAN erreichbar unter `http://192.168.178.21:5173` (Andromedas Ethernet-IP). Backend bleibt bewusst nur auf `127.0.0.1:8000` (kein Firewall-Zugriff nötig/gewünscht) — API-Calls laufen stattdessen über Vites Dev-Proxy (`vite.config.ts` → `server.proxy["/api"]`) auf denselben Port 5173. `frontend/src/api/client.ts` nutzt deshalb eine relative `API_BASE = ""` statt einer festen Host-Angabe. Wichtig: für Node/Vite existiert bereits eine Windows-Firewall-Freigabe, für Python/uvicorn nicht (und Claude Code hat keine Admin-Rechte, um das automatisch zu ändern) — daher unbedingt bei dieser Proxy-Lösung bleiben, nicht versuchen Port 8000 direkt freizugeben.

GM-Login ist jetzt case-insensitive (`sl` und `SL` funktionieren gleichermaßen) — `auth/repository.py` vergleicht `username` seit Kurzem über `toLower()` in der Cypher-Query.
