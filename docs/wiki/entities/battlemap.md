---
title: Battlemap
created: 2026-11-06
updated: 2026-11-06
type: entität
tags: [kampf, frontend, backend, websocket, ui, datenmodell, geplant]
sources: [../../../CLAUDE.md, ../../../backend/app/zeichnungen/repository.py, ../../../backend/app/kampf/repository.py, ../../api/kampf.md, ../concepts/kampf-und-initiative.md]
status: entschieden-nicht-umgesetzt
---

# Battlemap

Hex-Kampfkarte. Design 06.11.2026, nicht gebaut.

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
   `Person.bildUrl`. Unplatziert, bis jemand sie aufs Raster zieht. `amZug` ist
   das Highlight. Ein Zusatzzug (Reflex-Booster) ist dieselbe Person, kein
   zweiter Token. Spieler schiebt eigenen Charakter, eigene Drohnen und
   Beschwörungen nur am eigenen Zug. Die SL schiebt immer alle.

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

Nicht in der Anfrage, nicht Teil dieses Designs: Fog of War, Facing,
Quadrat-Grid-Umschalter, Belegungssperre (zwei Tokens ein Hex).

## Offene Achsen 06.11. (erste Fassung, ersetzt)

1. Bewegung — entschieden: überall droppen, Grün ist Hilfe.
2. Nur am eigenen Zug — entschieden: ja, SL immer alle.
3. Große Monster — erste Frage war 4 Hex; ersetzt durch 3 im Y plus Kreis.
4. Oberfläche — entschieden: Burgermenü zum Vorbereiten, Kampf hängt eine Karte an.
5. Unterlage — erste Frage war Bild oder Whiteboard-Standbild; ersetzt durch
   eigenes Bild plus Live-Zeichnen auf der Karte plus skalierbares Grid.

## Siehe auch

- [[../concepts/kampf-und-initiative]]
- [[../concepts/drohnen-fahrzeuge]]
- [[ui-konzept-commlink]]
