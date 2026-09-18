---
title: Kampf und Initiative
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [kampf, versionsgeschichte]
sources: [../../api/kampf.md, ../../reference/Neotopia_Regeln.md, ../../regeln-neotopia.md]
status: teilweise-umgesetzt
---

# Kampf und Initiative

## Definition

Rundenbasiert, mit Initiative-Reihenfolge. **Nicht simuliert:** Würfelergebnisse
und Regelwerk bleiben am Tisch — das Tool verwaltet nur *wer wann dran ist* und
*was auf dem Feld steht*. **Ausnahme: Rüstungsschaden wird gerechnet** (siehe
[[ruestung-kaestchen-durchlass]]), weil die Formel dafür zu komplex für den Tisch ist.

- **Initiative** = Geistesschärfe + Geschicklichkeit + Cyberware-Modifikator.
  Reihenfolge: Matrixnutzer vor Nahkämpfern vor Fernkämpfern. In umgekehrter
  Reihenfolge sagen alle an, was sie vorhaben — die schnellste Person kann so
  reagieren; gewürfelt wird dann in der richtigen Reihenfolge.
- **Treffen:** Geschick+Kampfskill+Mod vs. Ausweichen (Geschick+Sportlichkeit)
  oder Parieren (Geschick+Waffenfertigkeit, gegen Fernkampf nur mit
  Cyberware/Magie) — beide kumulativ −1 pro Einsatz/Runde.
- **Schaden:** Fernkampf = Waffenschaden+Nettoerfolge vs. Rüstung; Nahkampf =
  Waffenschaden+Stärke+Nettoerfolge vs. Rüstung.

## Initiative-Eingabe im Tool

Kommt als WARNUNG-Mitteilung mit Eingabefeld direkt im Popup auf dem
Spieler-Tablet (siehe [[../entities/mitteilungen-system]]) — physische Würfel,
der Spieler tippt nur das Ergebnis ein. Begründung: kein separater Screen, ein
Klick weniger.

## Status-Werte

`aktiv`, `bewusstlos`, `geflohen`, `tot` — **manuell von der SL gesetzt**, keine
automatische „0 HP = tot"-Logik.

## Entwicklung

- Initiative steht laut `CLAUDE.md` (10.09.2026) **nur noch während eines
  laufenden Kampfs** auf dem Charakterblatt, nicht mehr permanent.
- **Reflex-Booster** (Cyberware, siehe [[cyberware-bioware]]) gibt
  Initiative-Boni bis +6 sowie Zusatzaktionen — geprüft am 04.09.2026
  (Initiative 7 unverbaut vs. 13 mit Stufe-2-Booster, Zweitwurf-Pool ohne Bonus,
  Paralyse-Fall).

## Was noch fehlt

- **Eigener WebSocket für Kampf** — laut `docs/api/kampf.md` noch nicht gebaut,
  Updates laufen über Page-Refresh/Polling. Geplante Events:
  `teilnehmerHinzugefuegt`, `initiativeGesetzt`, `zugGewechselt`,
  `kampfBeendet`. **Status: geplant, nicht umgesetzt.**
- Widerspruch: das Beispiel-JSON in `docs/api/kampf.md` zeigt noch das alte
  generische Attributsystem — siehe [[../comparisons/veraltete-docs-vs-code]].

## Siehe auch

- [[ruestung-kaestchen-durchlass]] — die einzige tatsächlich gerechnete Kampfformel
- [[cyberware-bioware]] — Reflex-Booster und Initiative-Boni
- [[../entities/mitteilungen-system]] — wie die Initiative-Ansage technisch ankommt
