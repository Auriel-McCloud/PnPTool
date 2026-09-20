# PnPTool — Projektgedächtnis für Claude

Diese Datei wird von Claude Code automatisch geladen. Sie ist die Quelle der Wahrheit für den Projektstand — bei jeder größeren Änderung aktualisieren. **Bleibt bewusst schlank:** Details wandern nach `docs/api/` bzw. ins Wiki, nicht hier hinein.

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
| Rüstung | ✅ | Kästchen + Schadensreduktion, siehe `docs/api/ruestung.md` |
| Party | ✅ | Gruppen, Mitgliedschaft, aktive Party, siehe `docs/api/party.md` |
| Spotify | ✅ | Playlist an Ort/Event, Musik folgt aktiver Party, siehe `docs/api/spotify.md` |

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

**Offen:** Shop-System, KI-Integration (erste Iteration gebaut), Deploy,
Rüstungs-Reparatur (Hardware-Probe + Preis, siehe `docs/api/ruestung.md`),
PC-Vorlagen im Regelsystem,
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

### Aktuelle Messenger-UI-Todos (10.09.2026)
- **Verlauf zuverlässig ans Ende scrollen:** Beim Öffnen des Messengers und nach
  neuen Nachrichten muss immer die neueste Nachricht sichtbar sein. Der aktuelle
  Ansatz tut das auf mobilen Geräten nicht zuverlässig.
- **Eingabefeld bei geöffneter Tastatur sichtbar halten:** Wenn die mobile
  Tastatur erscheint, verschwindet das Texteingabefeld derzeit häufig aus dem
  sichtbaren Bereich. Der Chat muss den verfügbaren Visual-Viewport entsprechend
  neu einteilen bzw. zum Composer verschieben.
- **Persona-5-Chatoptik vervollständigen:** Die Nachrichten sollen noch
  asymmetrische Sprechblasen/Textboxen mit dynamisch an den Inhalt angepasster
  Größe bekommen. Die derzeitige Darstellung ist dafür noch zu gleichförmig.

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
   - **Bildgenerierung:** Portraits für Charaktere, Item-Bilder, Maps, Orte, Gebäude
   - **Wiki-Import:** Word-Dokumente hochladen, KI wandelt in Wiki-Seiten um
   - **Auto-Verknüpfung** (präzisiert 20.09.2026, Marks Wunsch): KI durchsucht
     Wiki-Text/Ideenschmiede-Einträge und verknüpft erwähnte Personen/Orte/
     Events automatisch als echte Graphkanten (nicht nur Textsuche). Existiert
     eine erwähnte Entität noch nicht, legt die KI dafür einen **Entwurf in
     der Ideenschmiede an** (Vorschlag zur Prüfung durch den SL, kein
     Autocommit in die Kampagne) und trägt die Beziehung gleich mit ein
   - **Rechtschreib-/Grammatik-/Logikprüfung** (erweitert 20.09.2026): Im
     Wiki-Editor UND in der Ideenschmiede — neben Rechtschreibung/Grammatik
     auch **Logik-/Konsistenzfehler** (z.B. Widersprüche zu bereits
     bestehenden Fakten im Wiki)
   - **Chatbot** (nice-to-have, Gag): Gegenstände mit Persönlichkeit — Decker redet mit seinem Deck, verrückter Priester redet mit seiner Bibel (und sie antwortet...)

4. **Spotify + Yamaha RX-V4A** — Playlist pro Ort/Szene, MusicCast-Steuerung.
   **Datengrundlage steht seit 18.09.2026**: die aktive Party
   (`docs/api/party.md`) trägt ihren Aufenthaltsort — die Musiksteuerung
   selbst (Playlist-Zuordnung, MusicCast-API-Anbindung) ist noch nicht gebaut.

5. **Deploy** — Debian/nginx statt localhost

6. **Drei-Ebenen-Architektur: Regelsystem → Kampagne → Ideenschmiede** ✅ FERTIG

8. **KI-/Critter-Begleiterblatt + Einfluss-System** — ✅ Backend + Frontend fertig:
   - Zwei neue `BegleiterArt`-Werte auf dem bestehenden Begleiter-System
     (siehe `docs/wiki/entities/...` und `backend/app/begleiter/`):
     - **KI**: Stadt-KI (Babel) — kein eigener Entity-Typ, sondern ein
       besonders mächtiger Sprite, damit Kampf/Zerstören (Brute Force →
       Kompilieren) automatisch mitläuft. Trägt die 6 nicht-körperlichen
       Person-Attribute (Charisma/Manipulation/Fassung/Intelligenz/
       Geistesschärfe/Entschlossenheit, Skala 1-6 wie bei Person) plus neu
       **Matrix-Präsenz** (1-6).
     - **CRITTER**: Tiere/Haustiere (Shadowrun-Anlehnung statt "Tier").
       Nutzt das Standard-Begleiterblatt unverändert (Widerstand/Angriff/
       Agilität + Waffe/Schadensart bleibt exakt gleich — "ein trainiertes
       Tier kann eine Waffe im Maul halten") plus **Loyalität** (1-6) und
       **Ausbildung/Tricks** (0-5). Bewusst ohne feste Mechanik — Mark:
       "wer soweit kommt hat's verdient", Wirkung entscheidet die SL am
       Spieltisch nach Bauchgefühl.
   - **Einfluss** (nur sinnvoll bei KI, aber technisch jeder Begleiter):
     echte Graphkante `(:Begleiter)-[:HAT_EINFLUSS_AUF {stufe}]->(:Ort|
     :Fraktion|:Event|:Gegenstand)` statt Freitext — die SL kann einer KI
     im Kampf gezielt einen echten Ort/eine Fraktion wegnehmen (Kante
     löschen) statt eine Beschreibung zu ändern. Endpunkte:
     `POST/DELETE .../begleiter/{id}/einfluss(/...)`, GM-only.
   - **Erfahrung bei Begleitern**: `erfahrung`/`erfahrungAusgegeben` als
     reine Budget-Anzeige ohne Kostenrechnung (anders als bei Personen) —
     Werte bleiben frei einstellbar, nur Erinnerung für die SL.
   - **Frontend (20.09.2026)**: `BegleiterVerwaltung.tsx` (SL-Bearbeiten:
     KI-Attribute + Critter-Werte + `EinflussVerwaltung` mit Ziel-Suche über
     Orte/Fraktionen/Events/Gegenstände), `BegleiterKachel.tsx`
     (Spieler-Ansehen inkl. `EinflussAnzeige`, reine Anzeige ohne Aktionen),
     neue Symbole ⌬ (KI) / ❖ (Critter) in `ART_SYMBOLE`. `KiAttributBlatt`/
     `CritterWerte` sind eigene, wiederverwendbare Komponenten
     (`begleiter/KiAttributBlatt.tsx`) für beide Kontexte. `tsc -b` sauber.
   - **Kachelraster + Suche + Anlegen-Popup (20.09.2026)**: die Übersicht war
     noch das alte Muster (Inline-Anlegen-Formular in der Kopfzeile, kein
     Suchfeld) — jetzt wie GegenstaendeUebersicht/PartyVerwaltung: `gg-suche`
     über Name/Art/Besitzer, "+ Neuer Begleiter" öffnet ein Commlink-Popup
     mit Name, Art-Dropdown und durchsuchbarer Besitzer-Auswahl
     (`BesitzerAuswahl`, Radiobuttons wie bei Party statt langem `<select>`
     ohne Filter). Dieselbe Auswahlkomponente ersetzt auch das bisherige
     `<select>` im Bearbeiten-Fenster, damit beide Stellen konsistent
     durchsuchbar sind.
   - **Offen**: KI-Auto-Steigerung (Gemini/Mistral lässt NPC/Begleiter/
     Critter/KI anhand Beschreibung + bereits erlebter Events wachsen) ist
     eigenes, noch nicht begonnenes Vorhaben — braucht zuerst ein
     Party-Besuchs-Log (`WAR_AN`-Kante mit Zeitstempel), weil
     `BEFINDET_SICH_AN` beim Ortswechsel überschrieben statt historisiert
     wird und "hat die Party das Event schon erlebt" sonst nicht beantwortbar
     ist. Ein Live-Test im Browser steht noch aus (Mark prüft selbst im
     laufenden Dev-Server).

9. **Decker / Neuroweaver Skill-System** — Vorschlag für Erweiterung auf 6 Skills:
   - Aktuell: Brute Force, Schleichen, Daten Verarbeiten, Kompilieren (4 Skills)
   - Vorgeschlagene Erweiterung:
     - **5. Electronic Warfare** (Verteidigung / Stören / Gegenangriffe)
     - **6. Matrix-Navigation** (Bewegung, Host-Architektur verstehen)
   - Ziel: Ausgewogenes Schere-Stein-Papier-System (Angriff ↔ Verteidigung ↔ Stealth ↔ Navigation)
   - Status: Nur als Vorschlag notiert, noch nicht entschieden

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

   **PC-Erstellung (neu):**
   - Spieler wählt: "Selbst erstellen" ODER "Vorlage wählen"
   - Vorlagen kommen aus dem Regelsystem
   - Kopiert Vorlage → Spieler passt Namen/Details an

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

11. **Charakterportrait im Spieler-Menü** — Spieler sehen aktuell kein
    Charakterportrait und haben keine Möglichkeit, eines festzulegen.
    Geplant: eigenes Popup "Neues Bild" (Commlink-Stil, wie gewohnt) mit
    4 Optionen zur Auswahl:
    1. Bild hochladen
    2. Foto machen (Kamera)
    3. Zeichentool
    4. KI-Beschreibung → generiert Bild
    Status: nur notiert, noch nicht entschieden/gebaut.

12. **Steckbrief nachträglich bearbeiten** — Konzept, Ambition, Verlangen
    und Ziel (`Charaktererstellung.tsx`) werden nur bei der Erstellung
    gesetzt und im Charakterblatt (`Steckbrief`-Komponente) nur read-only
    angezeigt. Spieler haben danach keine Möglichkeit, diese Felder zu
    ändern. Braucht irgendwo eine Bearbeiten-Funktion (Popup-Stil).
    Status: nur notiert, noch nicht entschieden/gebaut.

13. **Handy-Ansicht für Story-Wiki + Ideenschmiede** (notiert 20.09.2026) —
    Mark will auch unterwegs (ohne Laptop) an seinen Geschichten
    weiterschreiben. Beide Bereiche brauchen eine mobil taugliche Ansicht
    (Editor, Seitenbaum/Kachel-Übersicht, Verweis-Auswahl) — aktuell auf
    Desktop-Bedienung ausgelegt. Status: nur notiert, noch nicht
    entschieden/gebaut.
