---
title: Battlemap
created: 2026-11-06
updated: 2026-11-06
type: entität
tags: [kampf, frontend, backend, websocket, ui, datenmodell, geplant]
sources: [../../../CLAUDE.md, ../../../backend/app/zeichnungen/repository.py, ../../../backend/app/kampf/repository.py, ../../api/kampf.md, ../concepts/kampf-und-initiative.md]
status: teilweise-umgesetzt
---

# Battlemap

Hex-Kampfkarte. Gebaut 06.11.2026, Spieltisch-Klicktest offen.

## Auslöser

Mark, 06.11.2026: ein Grid (am liebsten Hex) auf eine Zeichnung oder ein Bild
legen. Charakterportraits der Leute in der Initiative als kleine Hex-Tokens,
Drag-and-Drop rastet ein. Jeder Spieler darf den eigenen Charakter bewegen,
dazu die eigenen Drohnen und Beschwörungen. Um den Token herum die Felder in
Reichweite grün umrandet: `3 + Sportlichkeit`, bei Drohnen `3 + Fliegen`.
Große Monster nehmen 4 benachbarte Felder. Wer gerade dran ist, wird
hervorgehoben. Frage: Whiteboard kopieren oder erweitern?

## Whiteboard nicht erweitern, Leinwand kopieren

Eigenes Feature, kein Aufsatz auf `Zeichnung`. Die bestehende Whiteboard-Liste
bleibt Zeichenbrett ohne Tokens.

Kopiert wird das Whiteboard-Muster inklusive Leinwand: Hintergrundbild,
`pfade` (react-sketch-canvas), `spielerDuerfenZeichnen`, Sichtbarkeit,
Papierkorb, Verteiler mit vollem Zustand. Darauf liegen Hex-Grid und Tokens.
Kein `EntityKind`.

Erste Skizze sagte „keine Zeichenpfade“. Ersetzt 06.11.2026: Mark will auf der
Battlemap live zeichnen und Spieler mitzeichnen lassen, plus Grid skalieren.
Deshalb der Vergleich mit dem Whiteboard — nicht weil Tokens Striche wären.

`docs/api/kampf.md` zeigt schon `position: { x, y }` an der Kante `KAEMPFT`.
Der echte Code speichert Teilnehmer als `KampfTeilnehmer`-Knoten, ohne
Position. Das API-Beispiel nicht als Modell nehmen.

## Entschieden 06.11.2026 (nicht gebaut)

Zwei Schichten:

1. **Karte** als Kampagnen-Asset, eigener Burgermenü-Punkt zum Vorbereiten
   (Liste wie Whiteboard). Name, Hintergrundbild, Zeichenpfade, Zeichenfreigabe
   für Spieler, skalierbares Hex-Grid (Größe, Ursprung), Sichtbarkeit,
   Papierkorb. Der laufende Kampf hängt eine vorbereitete Karte an.
2. **Tokens** am laufenden Kampf: Position am `KampfTeilnehmer`, Portrait aus
   `Person.bildUrl`. Kein unplatzierter Stapel — sie entstehen an den zwei
   Spawn-Feldern der Karte (siehe Nachschärfung). `amZug` ist das Highlight.
   Ein Zusatzzug (Reflex-Booster) ist dieselbe Person, kein zweiter Token.
   Spieler schiebt eigenen Charakter, eigene Drohnen und Beschwörungen nur am
   eigenen Zug. Die SL schiebt immer alle.

Bewegung: Drop überall, rastet auf Hex. Grün ist nur die Hilfe — Sprint,
Teleport, SL räumt. Laufen `3 + Sportlichkeit`. Drohnen `3 + Fliegen × 2`
(06.11. Nachschärfung, ersetzt `3 + Fliegen`: Fliegen ist schneller als
Laufen). Die Formel steht auf keiner Regel-Seite, neu, nicht Excel. Fliegen
ist Zusatzfertigkeit, siehe [[../concepts/drohnen-fahrzeuge]].

Grün nur während des Ziehens, vom Feld wo der Token angehoben wurde, bleibt
bis zum Loslassen. Dieses Startfeld bleibt danach grau, bis der Teilnehmer
nicht mehr am Zug ist — dann weg. Ohne Anheben kein Grau.

Große Monster: **3 Felder im Y, Kreis drumherum.** Die 4-Felder-Idee aus dem
Auslöser ist ersetzt. Belegt sind die drei Hex; der Kreis gruppiert sie optisch.

Live-Sync: Token-Züge über den geplanten Kampf-WebSocket
([[../concepts/kampf-und-initiative]], ungebaut). Zeichnen wie beim Whiteboard
(voller Pfad-Stand). Karten-CRUD bleibt REST.

Konflikt mit [[../concepts/kampf-und-initiative]] „keine Würfel-Simulation“:
Token-Position ist „was auf dem Feld steht“. Reichweite sperrt den Drop nicht.
Zwei Tokens auf einem Hex sperren den Drop — das ist Belegung, keine Probe.

Nicht in der Anfrage, nicht Teil dieses Designs: Fog of War, Facing,
Quadrat-Grid-Umschalter. Belegungssperre stand hier zuerst als „nicht Teil“;
ersetzt 06.11. (Nachschärfung): zwei Charaktere nicht auf demselben Feld.

## Nachschärfung 06.11.2026 — Spawn, Rand, Größe (nicht gebaut)

Damit die SL nicht jeden Token einzeln setzt: auf der Karte zwei Spawn-Felder
(Vorbereitung). **Blau** für PCs, **Magenta** für NPCs. Tokens der Initiative
erscheinen dort; ist das Feld belegt, auf einem freien Nachbarn — dieselbe
Regel wie unten bei Drohne/Beschwörung.

Randfarben, vorhandene Tokens: PC `--p-blau`, NPC `--p-magenta`. Drohne und
Beschwörung in der Farbe des Besitzers (`personType` der Drohne ist NPC, zählt
trotzdem nicht als Magenta-NPC). Wer dran ist: `--p-gold` und pulsiert —
dasselbe Puls-Muster wie Hot (`gg-hot-puls`), Gold statt Magenta.
`prefers-reduced-motion` bleibt.

Zwei Charaktere nicht auf demselben Hex, auch die SL nicht. Das eigene
Startfeld (grau) zählt als frei für den, der dort steht. Groß belegt alle
drei Y-Hex.

Beschwörung oder Drohne aktivieren: Token auf einem freien Feld neben dem
Charakter. Kein freier Nachbar → nächstes freies Feld.

Größe: Umschalter **Normal / Groß** in der SL-PC- und NPC-Übersicht, Default
Normal. Derselbe Schalter im Rassen-Baukasten (`istGross`, kein Rassenname im
Code). Neue Person übernimmt den Rassen-Default, danach gilt der Personen-Wert.
Normal = 1 Hex, Groß = 3 im Y plus Kreis.

## Nachgezogen 06.11.2026 — Größe an der Person, Rasse nur Vorlage

Checkbox „Groß“ auf der PC- und NPC-Kachel. Die Rasse setzt den Startwert beim Anlegen, danach gilt die Person. Die Karte liest `Person.istGross`.

## Offene Achsen 06.11. (erste Fassung, ersetzt)

1. Bewegung — entschieden: überall droppen, Grün ist Hilfe.
2. Nur am eigenen Zug — entschieden: ja, SL immer alle.
3. Große Monster — erste Frage war 4 Hex; ersetzt durch 3 im Y plus Kreis.
4. Oberfläche — entschieden: Burgermenü zum Vorbereiten, Kampf hängt eine Karte an.
5. Unterlage — erste Frage war Bild oder Whiteboard-Standbild; ersetzt durch
   eigenes Bild plus Live-Zeichnen auf der Karte plus skalierbares Grid.

## Gebaut 06.11.2026

Modul `backend/app/battlemap/` (CRUD, Papierkorb, Live-Zeichnen wie Whiteboard).
Tokens am `KampfTeilnehmer` (`hexQ`/`hexR`). Kampf hängt `battlemapId` an.
Spieler-Move `PATCH .../kampf/teilnehmer/{id}/position` (nur eigener Token am Zug).
`istGross` an Person und Rasse. Burgermenü Battlemap, Kartenwahl im Kampfmodus.
Spieltisch-Klicktest offen. SL schiebt den Grid-Ursprung per „Grid schieben“;
Größe bleibt der Slider. Größe-Schalter auf den PC-/NPC-Kacheln zeichnet sofort
neu. Spieler schiebt eigene Drohnen und Beschwörungen (`besitzerId`).
Token-Rundruf ist die volle Teilnehmerliste (Portrait, neu Hinzugekommene),
nicht nur Positionen. Zugwechsel und Aufnehmen rufen mit. Kampfmodus hat
„Karte öffnen“. Öffnen einer Karte ohne angehängten Kampf hängt sie an und
spawnt. Grid-SVG stiehlt keine Zeichenklicks mehr.
Hex-Rand wie Spawn: aktive Party (PCs plus NPCs/Drohnen dabei) `--p-blau`,
andere NPCs `--p-magenta`, am Zug Gold. Raster füllt das Rechteck, keine
leeren Ecken.

## Verknüpfung mit Ort/Event, Karte öffnen für Spieler (06.11.2026)

Mark: Battlemaps mit Orten oder Events verknüpfen können, Karte-öffnen-Knopf
auch für Spieler (rechtsbündig neben der Rundenanzeige, wie bei der SL).

Zwei neue Listenfelder an der Battlemap, `ortIds`/`eventIds` — rein
organisatorisch fürs Vorbereiten/den Überblick, kein automatisches Anhängen
beim Kampfbeginn (das bleibt die bewusste SL-Auswahl im Kampfmodus, siehe
„Entschieden 06.11.2026“ oben). Editierbar als Mehrfachauswahl in den
Karten-Einstellungen (`BattlemapEinstellungen.tsx`, gleiches
`<select multiple>`-Muster wie `Ort.versteckVonPersonIds`); Badges in der
Vorbereiten-Übersicht zeigen die Verknüpfung auf einen Blick
(`BattlemapAnsicht.tsx`, nur für die SL).

Spieler sehen jetzt denselben „Karte öffnen“-Knopf wie die SL, sobald ein
Kampf eine Battlemap angehängt hat — rechtsbündig neben „Runde N“
(`SpielerAnsicht.tsx`), dieselbe `BattlemapPopup`-Komponente, nur ohne
Grid-/Spawn-Werkzeuge (`istGm=false`). Zeichnen nur, wenn die Karte es
freigibt (`spielerDuerfenZeichnen`). Serverseitig schon auf sichtbare Karten
beschränkt — eine SL-geheime Karte zeigt den Knopf dadurch gar nicht erst.

**Verifiziert:** Live-E2E-Skript gegen echte Neo4j (erstellen/aktualisieren/
holen/leeren der neuen Felder, inkl. Leeren per PATCH mit `[]`), `npx tsc -b`
sauber. **Kein Klicktest** — bitte am Spieltisch: eine Karte einem Ort
zuordnen, prüfen dass die Badge erscheint, und dass ein Spieler im Kampf die
angehängte Karte per Knopf öffnen kann.

## Siehe auch

- [[../concepts/kampf-und-initiative]]
- [[../concepts/drohnen-fahrzeuge]]
- [[../concepts/rassen]]
- [[ui-konzept-commlink]]
