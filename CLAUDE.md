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
│   │   ├── ruestung.md       — Kästchen + Durchlass (NEU 10.09.2026)
│   │   ├── rassen.md         — Baukasten, Balance, Freigabe (NEU 11.09.2026)
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
| Rüstung | ✅ | Kästchen + Durchlass, siehe `docs/api/ruestung.md` |

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

**Offen:** Shop-System, KI-Integration, Spotify/MusicCast, Deploy,
Rüstungs-Reparatur (Hardware-Probe + Preis, siehe `docs/api/ruestung.md`)

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
- **Kästchen + Durchlass statt flachem Bonus** — Rüstung nutzt sich ab
- **Durchlass: niedriger ist besser** — 0 = dicht, ist die Größe der Lücke,
  nicht wie viel geblockt wird (Lederjacke hat hohen Durchlass, Bombenweste
  startet bei 0)
- **Abstufen statt Blocken** — Unheilbar→Tödlich→Schlag, nur Schlag wird
  halbiert (unterste Stufe)
- **Basis- und Aktuell-Wert getrennt** — sonst wird beschädigte Rüstung
  paradoxerweise *unzerstörbarer* statt kaputter (siehe Doku, war ein
  echter Denkfehler unterwegs)
- **Alles Getragene ist EIN Pool** — Kästchen summiert, Durchlass vom
  dichtesten Teil. **Keine Körperzonen**, kein Zielen (zu kompliziert)
- **Dichtestes Teil wird zuerst aufgebraucht**, Überlauf ins nächste. Killt
  nebenbei den "kugelsicheres Suspensorium"-Trick von selbst: das dichte
  Kleinteil ist nach einem Kästchen weg und der Pool-Durchlass springt hoch
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

3. **KI-Integration** (Gemini Pro) — mehrere Anwendungsfälle:
   - **NPC-Generator:** NPCs mit kurzer Beschreibung automatisch erstellen lassen
   - **Bildgenerierung:** Portraits für Charaktere, Item-Bilder, Maps, Orte, Gebäude
   - **Wiki-Import:** Word-Dokumente hochladen, KI wandelt in Wiki-Seiten um
   - **Auto-Verknüpfung:** KI durchsucht Wiki und verknüpft Personen/Orte mit Objekten
   - **Rechtschreib-/Grammatikprüfung:** Im Wiki-Editor
   - **Chatbot** (nice-to-have, Gag): Gegenstände mit Persönlichkeit — Decker redet mit seinem Deck, verrückter Priester redet mit seiner Bibel (und sie antwortet...)

4. **Spotify + Yamaha RX-V4A** — Playlist pro Ort/Szene, MusicCast-Steuerung

5. **Deploy** — Debian/nginx statt localhost

6. **Drei-Ebenen-Architektur: Regelsystem → Kampagne → Ideenschmiede** ✨ NEU

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

7. **Rüstungssystem** — ✅ Fertig (10.09.2026), siehe `docs/api/ruestung.md`:
   - **Zwei Werte pro Rüstung:** Kästchen (was sie aushält) + **Durchlass**
     (wie groß ihre Lücke ist — niedriger ist besser, umbenannt von "Schwelle")
   - **Abgestuft statt geblockt:** Unheilbar→Tödlich→Schlag, Schlag wird
     zusätzlich halbiert (unterste Stufe, kein weiteres Abstufen möglich)
   - **Kästchenschaden:** Unheilbar/Tödlich anteilig aus Basis+Überschuss,
     Schlag nur ab der Hälfte der aktuellen Kästchen (Trigger)
   - **Je kaputter, desto schlechter:** Durchlass-Aktuell steigt mit jedem
     Treffer; Kästchenschaden rechnet dagegen gegen die fixe Durchlass-Basis
     (sonst wird beschädigte Rüstung paradox unzerstörbar, siehe Doku)
   - **Kumulierte Rüstung:** alles Getragene ist ein Pool (Kästchen summiert,
     Durchlass vom dichtesten Teil); aufgebraucht wird das dichteste zuerst,
     zerstörte Teile fliegen aus der Ausrüstung. Keine Körperzonen
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

9. **Kästchen-Overflow-Darstellung** (Gesundheit, Willenskraft **und
   Rüstung** — die Lösung soll für alle drei Leisten gelten):
   - Problem: Hohe Werte = zu viele Kästchen, unübersichtlich. **Seit dem
     Grundwert 6 schon im Normalfall relevant**: Gesundheit erreicht
     natürlich 12 und liegt damit über den 10 gedruckten Kästchen des
     Papierblatts (mit Chrom bis 18)
   - **Logik:**
     - ≤10 Kästchen: normal einzeln anzeigen
     - >10: in 5er-Gruppen zusammenfassen + Rest
   - **Darstellung:** noch offen, muss cyberpunkig sein (keine Herzen!)
   - Ideen: Balken mit Zahl, Hex-Segmente, gestapelte Leisten, Chip-Symbole...
   - Bei bestehenden Farben bleiben!

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
