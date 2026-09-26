---
title: Mitteilungen-System (SL-Popups)
created: 2026-09-18
updated: 2026-09-26
type: entität
tags: [mitteilungen, websocket, frontend]
sources: [../../api/mitteilungen.md, ../../../CLAUDE.md]
status: aktuell
---

# Mitteilungen-System (SL-Popups)

## Konzept

Popup der Spielleitung an Spieler, **bewusst ohne sichtbaren Absender** — kommt
„aus der Spielwelt". Vier Arten: TEXT, BILD, WARNUNG (Bildschirm pulsiert),
NACHRICHT (interne Chat-Benachrichtigung, siehe [[kontakte-messenger]]).
Mitteilungen werden **gespeichert**, nicht nur gesendet — ein Tablet im Standby
kann nachlesen.

**Push:** WebSocket (`.../mitteilungen/live`) mit Reconnect + exponential
Backoff (1s→15s) — wichtig, weil Android Hintergrund-Tabs einschläfert.
Auth via Cookie; ungültiger Token → Close Code 1008.

## Zielrichtung: an alle oder gezielt

- **Text:** an alle **oder** an einzelne (`empfaengerIds`)
- **Bild per Blitz-Knopf:** **immer nur an alle** — Mark: „einzeln werde ich
  wohl nur Nachrichten verschicken wollen"

## Warnung

Ganzer Bildschirm pulsiert in wählbarer Farbe (rot/blau/violett — bewusst
**offen gelassen**, Mark will das erst am Spieltisch festlegen). Für
Initiative-Aufrufe und dramatische Momente; optional mit Initiative-Eingabefeld
direkt im Popup, siehe [[../concepts/kampf-und-initiative]].
`prefers-reduced-motion`: kein Puls, Ansage bleibt stehen.

## Mitbenutzung: Verhandlungen

Seit der Rüstungsreparatur (23.09.) teilen Verhandlungen denselben
WebSocket-Umschlag (`_typ: "verhandlung"`), ohne eigenen Kanal. Arten:
`RUESTUNG_REPARATUR`, `SHOP_KAUF`, seit 26.09. `GEGENSTAND_WEITERGABE`
(Spieler-zu-Spieler, siehe [[gegenstand-transfer]]). API:
[[../../api/verhandlung.md]].

## Ausblenden statt Löschen

Jeder Betrachter räumt seine **eigene** Liste auf (`ausblenden`), unabhängig
von anderen — echtes Löschen (`DELETE`) ist SL-only und zieht auch bereits
offene Bildschirme zurück (WebSocket-Push `zurueckgezogen`). Mark: „Ich will
dass sie ausblenden, weil die Liste sonst schnell unübersichtlich wird."

## Geprüft am 03.09.2026 (End-to-End, zwei Browser-Kontexte)

Rundruf kam live an; gerichtete Ansage an anderen PC erschien korrekt nicht
(kein Leak); Zurückziehen ließ offenes Popup verschwinden; alle drei
Warnfarben einzeln mit aufgelösten CSS-Werten geprüft; Bild-Upload/-Anzeige
funktionierte (naturalWidth > 0).

## Datenmodell

`(:Mitteilung {art, inhalt, bildUrl, farbe, initiative, anAlle, empfaengerIds,
gelesenVon, verstecktVon, erstelltAm})` — **keine Beziehungen** zu anderen
Nodes, reine Broadcast-Pakete (siehe [[neo4j-datenmodell]]).

## Siehe auch

- [[kontakte-messenger]] — NACHRICHT-Art wird von hier automatisch erzeugt
- [[gegenstand-transfer]] — Verhandlungsart `GEGENSTAND_WEITERGABE` (26.09.)
- [[../concepts/kampf-und-initiative]] — Initiative-Eingabe im WARNUNG-Popup
- [[neo4j-datenmodell]] — Datenmodell-Gesamtüberblick
