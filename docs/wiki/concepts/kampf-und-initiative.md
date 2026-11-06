---
title: Kampf und Initiative
created: 2026-09-18
updated: 2026-11-06
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
- **Treffen:** Geschick+Kampfskill+Ausrüstungsbonus vs. Ausweichen (Geschick+Sportlichkeit)
  oder Parieren (Geschick+Nahkampf, gegen Fernkampf nur mit
  Cyberware/Magie) — beide kumulativ −1 pro Einsatz/Runde. Welche Waffe
  welchen Skill würfelt, steht am Gegenstand (`kampfFertigkeit`:
  Schusswaffen, Nahkampf oder Handgemenge). Leer heißt: noch nicht
  markiert, das Tool rät nicht. **Parade-Bonus** (`paradeBonus`) addiert
  Extra-Würfel nur beim Parieren mit genau dieser Waffe, nicht auf den
  Angriff. Die große Parieren-Kachel zeigt die ausgerüstete Nahkampf-/
  Handgemenge-Waffe (Pistole kann nicht parieren); ohne solche Waffe bleibt
  es Geschick+Nahkampf. 0 = kein Bonus. Ein Schild ist eine Waffe mit
  Schaden 0 und Parade-Bonus.
- **Schaden:** Fernkampf = Waffenschaden+Nettoerfolge vs. Rüstung; Nahkampf =
  Waffenschaden+Körperkraft+Nettoerfolge vs. Rüstung. Die Kampfkarte rechnet
  die Körperkraft in die Schadenszahl der Nahkampf-/Handgemenge-Waffe ein.

## Initiative-Eingabe im Tool

Kommt als WARNUNG-Mitteilung mit Eingabefeld direkt im Popup auf dem
Spieler-Tablet (siehe [[../entities/mitteilungen-system]]) — physische Würfel,
der Spieler tippt nur das Ergebnis ein. Begründung: kein separater Screen, ein
Klick weniger.

## Status-Werte

`aktiv`, `bewusstlos`, `geflohen`, `tot` — **manuell von der SL gesetzt**, keine
automatische „0 HP = tot"-Logik.

## Entwicklung

- **06.11.2026:** Große Parieren-Kachel nimmt die Parade der ausgerüsteten
  Nahkampfwaffe (Mark am Tisch: Pistole kann nicht parieren, 6 neben 8
  verwirrt). Nahkampf-Schadenszeile zeigt Waffe+Körperkraft, Fernkampf
  bleibt nur die Waffe.
- **05.11.2026:** Klick auf die Initiative-Zahl trägt die Erfolge ein, für den
  eigenen Charakter, die eigene Drohne und die Beschwörung. Steht der
  Charakter oder die Drohne noch nicht in der Liste, kommt sie mit diesem
  Wert dazu. Die SL klickt dieselbe Zahl im Bogen.
- **05.11.2026:** Kampfmenü ohne die Zeilen „Ansage von hinten“, „Schutz und
  Schaden“ und „Würfeln“. Die Ansage-Reihenfolge gilt weiter am Tisch, steht
  nur nicht mehr unter der Liste. Waffen, Pools und der Umschalter Kampf /
  Cyberkampf bleiben. Grund: die Seite hat gescrollt, obwohl alles draufpassen
  soll.
- Initiative steht laut `CLAUDE.md` (10.09.2026) **nur noch während eines
  laufenden Kampfs** auf dem Charakterblatt, nicht mehr permanent.
- **Reflex-Booster** (Cyberware, siehe [[cyberware-bioware]]) gibt
  Initiative-Boni bis +6 sowie Zusatzaktionen — geprüft am 04.09.2026
  (Initiative 7 unverbaut vs. 13 mit Stufe-2-Booster, Zweitwurf-Pool ohne Bonus,
  Paralyse-Fall).
- **23.10.2026:** Kampfkarte zählt Ausrüstungsboni in den Würfelpool.
  Waffen (und Chrom mit `istWaffe`) können `kampfFertigkeit` tragen.
  Schadenszeile ist nur noch Waffenschaden + Nettoerfolge.
- **04.11.2026:** Kommt ein NPC mit Reflex-Booster dran, fragt dasselbe Popup
  die SL — sie steuert alle NPCs. Spielercharaktere entscheiden weiter
  selbst, auf ihrem Tablet. Paralyse danach ebenso.
- **31.10.2026:** `paradeBonus` an der Waffe. Gilt nur beim Parieren mit
  dieser Waffe. Angriff und die globale P-Zahl bleiben ohne den Bonus.
  Schild = Schaden 0 + Parade-Bonus. Mindeststärke wurde besprochen und
  verworfen.

## Was noch fehlt

- **Eigener WebSocket für Kampf** — laut `docs/api/kampf.md` noch nicht gebaut,
  Updates laufen über Page-Refresh/Polling. Geplante Events:
  `teilnehmerHinzugefuegt`, `initiativeGesetzt`, `zugGewechselt`,
  `kampfBeendet`. **Status: geplant, nicht umgesetzt.**
- **Battlemap** — Hex-Grid auf Bild, Tokens aus der Initiative, Spieler
  bewegt eigenen Charakter/Drohnen/Beschwörungen. Skizze 06.11.2026, Achsen
  offen, nicht gebaut. Siehe [[../entities/battlemap]]. Die Zeile oben
  („keine Würfel-Simulation“) bleibt; ob Reichweite nur markiert oder Drops
  sperrt, ist dort die offene Achse.
- Widerspruch: das Beispiel-JSON in `docs/api/kampf.md` zeigt noch das alte
  generische Attributsystem — siehe [[../comparisons/veraltete-docs-vs-code]].

## Siehe auch

- [[ruestung-kaestchen-durchlass]] — die einzige tatsächlich gerechnete Kampfformel
- [[cyberware-bioware]] — Reflex-Booster und Initiative-Boni
- [[../entities/mitteilungen-system]] — wie die Initiative-Ansage technisch ankommt
