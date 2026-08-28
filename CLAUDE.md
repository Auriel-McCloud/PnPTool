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
- 🟡 **Phase 3 (teilweise, 28.08.2026)** — Charakterblatt-Grundlage: TraitDef-Katalog (52 Werte aus Neotopia.xlsx geseedet), Punkte-Anzeige (DotPool, beliebiges Maximum inkl. Per-Charakter-Override), Gegenstände 1:N an Personen mit Auto-Sichtbarkeit für den Besitzer. Siehe eigener Abschnitt unten. **Noch offen für vollständige Phase 3:** Box-Tracks (Gesundheit/Willenskraft/I.C.E.), Cyber/Bio-Ware-Slots, Rüstung/Waffen, Companion/Drohne-Sheets, Würfeln.
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

**Nicht gemacht / bewusst zurückgestellt (Rest von Phase 3):**
- Keine Box-Tracks (Gesundheit/Willenskraft/I.C.E./Arete) — die "Kästchen statt Punkte"-Werte aus dem Excel fehlen noch komplett.
- Kein Cyber/Bio-Ware, keine Rüstung/Waffen-Slots (nur generische Gegenstände ohne Schadenswerte etc.)
- Kein Companion/Drohne-Sheet, obwohl `HAS_TRAIT` dafür schon generisch genug wäre (funktioniert für jeden Knotentyp, nicht nur Person) — nur noch nicht an eine Companion-Route angebunden.
- Kein Würfeln.
- `sortOrder`-Nummerierung im Seed ist grob (Reihenfolge aus dem Excel übernommen), nicht weiter kuratiert.
- Optisches Layout ist weiterhin "unübersichtlich, nicht schön" (O-Ton Mark) — funktional korrekt, aber noch kein eigener Design-Durchgang für den Charakterbogen.
- **Neue Idee von Mark (28.08.2026, noch nicht designed):** drei eigene Ansichten/Modi für den Charakterbogen — "Charaktererstellung" (Startpunkte-Regeln, Rassen-Boni etc. aus dem Regeln-Sheet), "Spiel" (Standard-Ansicht, das was jetzt existiert), "Level Up" (EP ausgeben). Dazu ein Erfahrungspunkte-Zähler pro Charakter + eine Möglichkeit für den SL, EP an alle oder einzelne Spieler zu vergeben (soll sich automatisch im Charakterbogen niederschlagen). Braucht eigene Logik/Design-Runde, bewusst noch nicht begonnen.

## Bekannte Stolpersteine (nicht nochmal reinlaufen)

1. **`passlib` + neueres `bcrypt`**: inkompatibel (passlib ist unmaintained, `bcrypt>=4.1` hat `__about__` entfernt). Lösung: `bcrypt`-Paket direkt nutzen, kein passlib. Ist bereits so umgesetzt in `auth/security.py`.
2. **`uvicorn --reload` auf Windows**: der Reloader-Parent-Prozess kann sterben während der Worker-Kind-Prozess weiterläuft und alten Code weiter serviert (WatchFiles-Bug/Windows-Eigenheit). Wenn nach einem Reload etwas nicht wie erwartet reagiert: beide PIDs (Parent + Worker, `netstat -ano | grep :8000` dann `taskkill //F //PID X`) killen und ohne `--reload` neu starten.
3. **`react-cytoscapejs`-Wrapper**: hatte einen Bug — rief bei jedem Re-Render ein Re-Layout auf und verlor dabei den Klick-Handler. Komplett entfernt, Cytoscape wird jetzt direkt (imperativ, via `useRef`) angesteuert in `graph/CampaignGraphView.tsx`.
4. **Cytoscape + `box-sizing`**: Cytoscape hat einen eingebauten `ResizeObserver` auf dem Container. Ohne globales `box-sizing: border-box` (jetzt in `index.css` gesetzt) addiert sich ein `border` zur `width:100%`-Breite dazu → minimaler Overflow → Scrollbar erscheint/verschwindet → ResizeObserver feuert erneut → Endlosschleife, die sich sichtbar "aufschaukelt" (Container wächst langsam immer weiter). Fix: globales `box-sizing: border-box` + Cytoscape-eigenen Resize nicht durch einen zweiten, redundanten manuellen Call stören.
5. **Cytoscape Initial-Messung zu früh**: Falls der Container beim `cytoscape({container:...})`-Aufruf noch nicht final gelayoutet ist (z.B. direkt nach Tab-Wechsel), kann die interne Erstmessung falsch/zu klein ausfallen und bleibt es auch (Canvas nur "halb" befüllt, Klick-Koordinaten verschoben). Fix: `requestAnimationFrame` nach Konstruktion, das explizit `cy.resize()` + `cy.fit()` erzwingt, nachdem der Browser das Layout tatsächlich committed hat. War hier lange nur als Plan dokumentiert, aber nie tatsächlich im Code umgesetzt (Diskrepanz erst beim Debuggen von Stolperstein #8 aufgefallen) — jetzt in `CampaignGraphView.tsx` als doppeltes `requestAnimationFrame` + `window`-`resize`-Listener implementiert.
6. **TypeScript + `verbatimModuleSyntax` + `@types/cytoscape`**: der `type Stylesheet = A | B` Union-Alias aus dem `export =`-Namespace lässt sich unter `verbatimModuleSyntax` nicht als `cytoscape.Stylesheet` referenzieren (TS-Fehler "no exported member"), obwohl er existiert — vermutlich weil `type`-Aliase (im Gegensatz zu `interface`s) beim Namespace-Merge über einen Default-Import unter dieser strikten Einstellung nicht sauber aufgelöst werden. Workaround: das nominale `interface StylesheetStyle` statt des Union-`type Stylesheet` referenzieren, funktioniert identisch für unseren Anwendungsfall.
7. **Vite Hot-Reload + Cytoscape**: bei größeren Änderungen an Komponenten, die eine imperative Canvas-Bibliothek verwenden, lieber den Dev-Server komplett neu starten (`node_modules/.vite`-Cache löschen) statt sich auf HMR zu verlassen — HMR kann alte Instanzen hinterlassen, die mit neuen um denselben Container konkurrieren.
8. **Cytoscape-Canvas verschoben durch `text-align: center`**: `index.css` setzt global `#root { text-align: center; }`. Cytoscapes interne `<canvas>`-Layer sind `position: absolute` mit `left`/`right: auto` (Cytoscape selbst setzt nie ein explizites `left`). Bei `left/right: auto` berechnet der Browser die "static position" eines ursprünglich inline-artigen Elements (canvas ist von Haus aus `display: inline`) unter Berücksichtigung des geerbten `text-align` — bei `center` verschiebt das die komplette Canvas nach rechts um ungefähr die halbe Canvas-Breite (reproduzierbar auf jedem Gerät mit `devicePixelRatio != 1`, unabhängig von Bildschirmgröße). Symptom: linke Hälfte des Graphen leer/schwarz, Klick-Koordinaten um denselben Betrag versetzt. War der Bug hinter dem lange als "Graph-Sizing-Bug" verfolgten Problem — **nicht** der ursprünglich vermutete `box-sizing`/`ResizeObserver`- oder `pixelRatio`-Bug. Gefunden per Headless-Browser-Debugging (`cy.pan()`/`cy.zoom()`/Node-Positionen waren intern korrekt — nur das `<canvas>`-DOM-Element selbst war falsch positioniert). Fix: `textAlign: "left"` explizit auf dem Graph-Container in `CampaignGraphView.tsx` setzen (überschreibt lokal das geerbte `center`, ohne die globale Zentrierung zu ändern).

9. **Neue Pydantic-Response-Felder + Bestandsdaten ohne diese Property = 500 auf der ganzen Liste**: Als `Gegenstand` um `typ`/`eigenschaften`/`zeigeInGraph`/`bildUrl` erweitert wurde, hatte `items/repository.py::_decode()` Fallbacks für drei der vier neuen Felder, aber `typ` vergessen. Ein einziger alter Gegenstand ohne `typ`-Property (Neo4j gibt dafür `null` zurück) ließ die Pydantic-Validierung von `GegenstandResponse.typ: str` (nicht optional) fehlschlagen → 500 auf `GET .../gegenstaende` → riss die komplette `CharacterSheetPanel`-Anzeige mit runter (Werte UND Gegenstände laden im selben `Promise.all`, ein Fehler lässt beide leer/unsichtbar erscheinen), obwohl die Werte selbst unbeteiligt waren. Symptom war "Charakterblatt komplett weg", nicht ein Fehler zum konkreten Feld. **Lektion**: bei jeder neuen Property auf einem bestehenden Node-Typ IMMER einen `coalesce`/Fallback in der Decode-Stelle einbauen, für JEDES neue Feld einzeln prüfen, nicht nur die "offensichtlichen" (bool/JSON) — und nach Schema-Erweiterungen kurz gegen die Bestandsdaten der Testkampagne verifizieren (`MATCH (g:Gegenstand) RETURN g.typ, ...` direkt in Neo4j), nicht nur gegen frisch angelegte Testdaten.

## Nächste Schritte

1. Nutzer bestätigt den UI-Polish-Durchgang im Browser (Rich-Text-Editor, SL-geheim-Markierung, Sichtbarkeits-Auswahl, Tabellen) — noch nicht visuell bestätigt, nur backend-seitig und per Build durchgetestet
2. Danach: Phase 3 (Spieler-Charakterbogen) — dabei `TraitDef`-Katalog gleich pro `ruleset` scopen, nicht global
3. Vor Phase 4: die Sichtbarkeits-Filterung tatsächlich in eine Spieler-Route einbauen (Funktionen sind fertig, siehe oben)

**Server-Status:** Backend läuft auf `0.0.0.0:8000` (ohne `--reload`, siehe Stolperstein #2), Frontend mit `npm run dev` (hat `host:true` fest in `vite.config.ts`, kein `--host`-Flag mehr nötig) auf Port 5173. Neo4j läuft durchgehend in Docker. Falls nach einem Reboot/Neustart nichts erreichbar ist: siehe "Wie man lokal startet" oben.

## Zugriff vom Handy / LAN (eingerichtet, für Tests unterwegs)

Frontend (Vite) läuft mit `--host`, ist also im LAN erreichbar unter `http://192.168.178.21:5173` (Andromedas Ethernet-IP). Backend bleibt bewusst nur auf `127.0.0.1:8000` (kein Firewall-Zugriff nötig/gewünscht) — API-Calls laufen stattdessen über Vites Dev-Proxy (`vite.config.ts` → `server.proxy["/api"]`) auf denselben Port 5173. `frontend/src/api/client.ts` nutzt deshalb eine relative `API_BASE = ""` statt einer festen Host-Angabe. Wichtig: für Node/Vite existiert bereits eine Windows-Firewall-Freigabe, für Python/uvicorn nicht (und Claude Code hat keine Admin-Rechte, um das automatisch zu ändern) — daher unbedingt bei dieser Proxy-Lösung bleiben, nicht versuchen Port 8000 direkt freizugeben.

GM-Login ist jetzt case-insensitive (`sl` und `SL` funktionieren gleichermaßen) — `auth/repository.py` vergleicht `username` seit Kurzem über `toLower()` in der Cypher-Query.
