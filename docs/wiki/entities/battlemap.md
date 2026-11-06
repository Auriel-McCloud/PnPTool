---
title: Battlemap
created: 2026-11-06
updated: 2026-11-06
type: entität
tags: [kampf, frontend, backend, websocket, ui, datenmodell, geplant, offen]
sources: [../../../CLAUDE.md, ../../../backend/app/zeichnungen/repository.py, ../../../backend/app/kampf/repository.py, ../../api/kampf.md, ../concepts/kampf-und-initiative.md]
status: offen
---

# Battlemap

Hex-Kampfkarte. Nicht gebaut. Skizze vom 06.11.2026, Achsen offen.

## Auslöser

Mark, 06.11.2026: ein Grid (am liebsten Hex) auf eine Zeichnung oder ein Bild
legen. Charakterportraits der Leute in der Initiative als kleine Hex-Tokens,
Drag-and-Drop rastet ein. Jeder Spieler darf den eigenen Charakter bewegen,
dazu die eigenen Drohnen und Beschwörungen. Um den Token herum die Felder in
Reichweite grün umrandet: `3 + Sportlichkeit`, bei Drohnen `3 + Fliegen`.
Große Monster nehmen 4 benachbarte Felder. Wer gerade dran ist, wird
hervorgehoben. Frage: Whiteboard kopieren oder erweitern?

## Whiteboard nicht erweitern

Vorläufige Richtung dieser Skizze, keine Bau-Freigabe.

Das Whiteboard (`Zeichnung`, `backend/app/zeichnungen/`) ist freie Striche plus
optionalem Hintergrundbild. Permission dort: `spielerDuerfenZeichnen`. Die
Battlemap ist ein diskretes Hex-Raster plus Tokens aus der Initiative.
Permission dort: eigener Charakter, eigene Drohne, eigene Beschwörung. Die
Leinwand (`react-sketch-canvas`, `pfade`-JSON) taugt nicht als Token-Layer.

Kopieren, nicht mergen:

- Bild-Upload, Sichtbarkeit, Papierkorb, eigener Verteiler, voller Zustand
  statt Diff — Whiteboard-Verteiler und der geplante Kampf-WebSocket
  ([[../concepts/kampf-und-initiative]])
- Nicht: Zeichenpfade, `spielerDuerfenZeichnen`, kein `EntityKind`

`docs/api/kampf.md` zeigt schon `position: { x, y }` an der Kante `KAEMPFT`.
Der echte Code speichert Teilnehmer als `KampfTeilnehmer`-Knoten, ohne
Position. Das API-Beispiel nicht als Modell nehmen.

## Skizze (nicht entschieden)

Zwei Schichten, nicht eine:

1. **Karte** als Kampagnen-Asset (analog zur Whiteboard-Liste): Name,
   Hintergrundbild, Hex-Kalibrierung (Ursprung, Größe, Spitz oder Flach),
   Sichtbarkeit, Papierkorb.
2. **Tokens** am laufenden Kampf: Position am `KampfTeilnehmer`, Portrait aus
   `Person.bildUrl`. Unplatziert, bis jemand sie aufs Raster zieht. `amZug` ist
   das Highlight. Ein Zusatzzug (Reflex-Booster) ist dieselbe Person, kein
   zweiter Token.

Live-Sync: der geplante Kampf-WebSocket in `docs/api/kampf.md` (ungebaut) ist
der natürliche Kanal für Token-Züge, nicht der Whiteboard-Socket. Karten-CRUD
bleibt REST.

Die Formel `3 + Sportlichkeit` / `3 + Fliegen` steht auf keiner Regel-Seite.
Neu, nicht Excel. Fliegen ist Zusatzfertigkeit, siehe
[[../concepts/drohnen-fahrzeuge]].

Konflikt mit [[../concepts/kampf-und-initiative]]: das Tool simuliert keine
Würfel, es verwaltet wer dran ist und was auf dem Feld steht. Token-Position
ist „was auf dem Feld steht“. Ob die grüne Reichweite nur Hilfe ist oder Drops
sperrt, ist offen — eine harte Sperre wäre Regel-Simulation.

Hex und „4 benachbarte Felder“: ein Quadrat 2×2 gibt es auf Hex nicht. Die Form
ist offen.

## Offene Achsen

Nicht still beantworten.

1. Bewegung: Drop nur auf grün, oder überall und Grün ist nur Hilfe?
2. Spieler schiebt den eigenen Token nur am eigenen Zug, oder immer?
3. Große Monster: welche vier Hex (feste Raute am Anker, oder vier
   zusammenhängende frei)?
4. Oberfläche: Knopf im Kampfmodus, oder eigener Burgermenü-Punkt zum
   Vorbereiten von Karten?
5. Unterlage: nur eigenes Bild, oder zusätzlich eine Whiteboard-Zeichnung als
   Standbild?

Nicht in der Anfrage, deshalb nicht Teil dieser Skizze: Fog of War, Facing,
Quadrat-Grid-Umschalter, Belegungssperre (zwei Tokens ein Hex).

## Siehe auch

- [[../concepts/kampf-und-initiative]]
- [[../concepts/drohnen-fahrzeuge]]
- [[ui-konzept-commlink]]
