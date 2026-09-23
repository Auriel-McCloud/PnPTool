---
title: Währung und Preise
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [wirtschaft, versionsgeschichte, offen]
sources: [../../reference/Neotopia_Gegenstaende.md, ../../regeln-neotopia.md]
status: aktuell
---

# Währung und Preise

## Definition

**NuYen (¥)** ist die Weltwährung, **1¥ = 1€** — vereinfacht reale Preise
recherchierbar zu machen. Preise für nicht gelistete Gegenstände: recherchieren
oder die Spielleitung fragen.

Vollständige Excel-Preistabellen (Rüstung, Waffen, Technik, Commlinks,
Cyberdecks, Riggerkonsolen, Drogen, SL-Ideen-Gadgets) stehen unverändert in
[[../../reference/Neotopia_Gegenstaende.md]] — diese Seite verlinkt nur, dupliziert
nicht.

## Bereiche, in denen sich Preise vom Excel entfernt haben

- **Cyberware/Bioware:** Rundungsregel ergänzt, siehe [[cyberware-bioware]]
- **Rüstung:** komplett neues Kästchen+Durchlass-System ersetzt den reinen
  Kaufpreis-Kontext, siehe [[ruestung-kaestchen-durchlass]]
- **Erfahrung/Steigern:** komplett neu erfunden, nicht im Excel, siehe
  [[erfahrung-und-steigern]]

## Offene Preisfrage

Fahrzeug/Drohnen-Preisstaffel wirkt für kleine Fahrzeuge zu teuer — siehe
[[drohnen-fahrzeuge]] für Details. **Status: offen.**

## Shop-System: Kern gebaut (22.09.2026)

`CLAUDE.md` Punkt 1: Händler-NPCs mit Sortiment (explizit eingetragene Ware
+ automatischer Bestand nach Spezialisierung gefiltert), Kauf mit
serverseitiger Guthabenprüfung. **Status: Backend fertig und end-to-end
verifiziert, Frontend noch offen.** Details: `docs/api/haendler.md`.

Bestand nutzt die bestehende `einzigartig`/`istVorlage`-Unterscheidung
(kein neues Konzept): Vorlagen unendlich kaufbar, einzigartige Stücke
verschwinden nach dem Kauf aus dem Sortiment.

Noch offen: Spam/Werbe-Mechanik (Frequenz skaliert mit I.C.E.),
Scammer-Storylines, Frontend. Würde — sobald das Frontend steht — auch die
Rüstungsreparatur-Kosten und die Fahrzeug-Preisdiskussion mit auflösen
können.

**KI-Sortiment-Vorschlag (23.09.2026):** neues Modul
`backend/app/haendler/ki_vorschlag.py` — die KI schlägt passende Waren für
einen bestimmten Händler vor (bevorzugt bestehende Vorlagen, erfindet nur
bei echter Lücke etwas Neues), SL bestätigt jeden Vorschlag einzeln.
Backend end-to-end verifiziert, Frontend-Popup noch offen. Details:
`docs/api/haendler.md`.

## Siehe auch

- [[../../reference/Neotopia_Gegenstaende.md]] — alle Preistabellen im Volltext
- [[cyberware-bioware]] — Preis→Willenskraftverlust
- [[ruestung-kaestchen-durchlass]] — Reparaturkosten noch offen
