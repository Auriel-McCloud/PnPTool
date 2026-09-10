# PnPTool — Projektgedächtnis für Claude

Diese Datei wird von Claude Code automatisch geladen. Sie ist die Quelle der Wahrheit für den Projektstand — bei jeder größeren Änderung aktualisieren.

## Was ist PnPTool

WebApp für Mark's Pen-and-Paper-Rollenspielrunden, Homebrew-System **"NeotopiA"** (WoD-artige Attribute, Shadowrun-Cyberware/Rigging, Mage-Sphären, Cyberpunk-Setting). Referenz: `docs/reference/Neotopia.xlsx`.

**Zwei Nutzerrollen:**
- **Spielleiter (GM)** — plant Kampagnen als Beziehungsgraph, sendet Live-Popups
- **Spieler** — interaktive Charakterbögen, Messenger, empfängt Popups

**Wichtige Dokumentation:**
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

## Stand der Umsetzung (07.09.2026)

| Phase | Status | Beschreibung |
|-------|--------|--------------|
| 1 | ✅ | Grundgerüst, Docker, Auth |
| 2 | ✅ | CRUD, Cytoscape-Graph |
| 3 | 🟡 | Charakterblatt (Attribute ✅, Box-Tracks ⬜) |
| 4 | ✅ | Spieler-Zugang, Sichtbarkeit |
| 5 | ✅ | **Mitteilungen + Messenger fertig** |
| Wiki | ✅ | Seitenbaum, Freigaben, TipTap-Editor |
| Themes | ✅ | Zwei Themes, Token-basiert |

**Zuletzt gebaut (07.09.2026):**
- Chat-Benachrichtigungen (💬 Popup bei neuen Nachrichten)
- Mitteilungen ausblenden (✕ Button, pro Person)
- API-Dokumentation (`docs/api/`)

**Offen:** Shop-System, KI-Integration, Spotify/MusicCast, Deploy

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

## Git-Workflow

- Remote: `https://github.com/Auriel-McCloud/PnPTool.git`
- Branch: `main` (direkt committen)
- Commit-Messages: Deutsch, eine Zeile, fachliches Ergebnis
- Session-Start: `git log --oneline -5`, `git status`
- Session-Ende: committen + pushen (Mark arbeitet von PC und Handy)

## Server-Status

- **Neo4j:** Docker, Port 7687
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

2. **KI-Integration** (Gemini Pro) — mehrere Anwendungsfälle:
   - **NPC-Generator:** NPCs mit kurzer Beschreibung automatisch erstellen lassen
   - **Bildgenerierung:** Portraits für Charaktere, Item-Bilder, Maps, Orte, Gebäude
   - **Wiki-Import:** Word-Dokumente hochladen, KI wandelt in Wiki-Seiten um
   - **Auto-Verknüpfung:** KI durchsucht Wiki und verknüpft Personen/Orte mit Objekten
   - **Rechtschreib-/Grammatikprüfung:** Im Wiki-Editor
   - **Chatbot** (nice-to-have, Gag): Gegenstände mit Persönlichkeit — Decker redet mit seinem Deck, verrückter Priester redet mit seiner Bibel (und sie antwortet...)

3. **Spotify + Yamaha RX-V4A** — Playlist pro Ort/Szene, MusicCast-Steuerung

4. **Deploy** — Debian/nginx statt localhost

5. **Ideenschmiede** (zu besprechen) — eigener Bereich außerhalb der Kampagne:
   - Ideen-Sammlung die nicht Teil des aktiven Spiels ist
   - Inhalte sollen leicht in die Kampagne verschoben werden können
   - Mögliche Auffangstation für KI-generierte Inhalte (Charaktere, Gegenstände, Orte, Story-Elemente)
   - Muss noch durchdacht werden ob das so sinnvoll ist

6. **Rüstungssystem** (Konzept steht!) — Rüstung als eigene Kästchen-Leiste:
   - **Zwei Werte pro Rüstung:**
     - **Kästchen** = wie viel die Rüstung aushält
     - **Schwelle** = wie viel Schaden IMMER durchgeht (Name evtl. ändern)
   - **Rüstung wird beschädigt:**
     - Tötlich/Unheilbar → macht immer Rüstungskästchen kaputt (1:1)
     - Schlag → macht nur kaputt wenn > doppelte Schwelle
   - **Je kaputter, desto schlechter:** Schwelle steigt wenn Kästchen sinken
   - **Schadens-Popup:** Spieler gibt nur "3 × Tötlich" ein, Tool rechnet automatisch:
     - Was geht an HP (durch die Schwelle)
     - Was macht Rüstung kaputt
     - Neue Schwelle nach Beschädigung
   - **Kumulierte Rüstung:** Helm + Jacke + Hose — Kästchen addieren, Schwelle = niedrigste?
   - **Offen:** Besserer Name für "Schwelle"? (Durchlass? Lücke? Schutzgrenze?)

7. **Augment-Preisstufen:**
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

8. **Kästchen-Overflow-Darstellung** (Willenskraft & Gesundheit):
   - Problem: Hohe Werte (20+) = zu viele Kästchen, unübersichtlich
   - **Logik:**
     - ≤10 Kästchen: normal einzeln anzeigen
     - >10: in 5er-Gruppen zusammenfassen + Rest
   - **Darstellung:** noch offen, muss cyberpunkig sein (keine Herzen!)
   - Ideen: Balken mit Zahl, Hex-Segmente, gestapelte Leisten, Chip-Symbole...
   - Bei bestehenden Farben bleiben!

9. **KI-Chatbots für Gegenstände** — Zwei Typen:
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
