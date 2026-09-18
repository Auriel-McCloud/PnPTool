---
title: Theming-System
created: 2026-09-18
updated: 2026-09-18
type: entität
tags: [theming, frontend, ui]
sources: [../../theming.md]
status: aktuell
---

# Theming-System

## Die eine Regel

**Außerhalb von `frontend/src/theme/` steht kein Farbwert mehr direkt im
Code.** Weder Hex in CSS noch `farbe: "#4d8bd8"` in TSX — nur Tokens.

Grund: solange Werte verstreut sind, färbt ein Themewechsel *fast* alles um,
und einzelne Stellen bleiben im alten Ton. Genau das war vorher der Zustand
(Graphfarben doppelt in `CampaignGraphView.tsx` mit Hand-Kommentar „beim Ändern
dort nachziehen").

## Aufbau

```
frontend/src/theme/
├── tokens.css        Token-Definitionen + Standardtheme "cyberpunk"
├── hextechpunk.css    Zweites Theme: überschreibt nur Werte, nie Namen
├── theme.ts           Zugriff aus TypeScript, Theme-Umschaltung
└── ThemeSchalter.tsx  Durchschalter (◐) in der Werkzeugleiste
```

## Sechs Token-Gruppen

Palette (`--p-*`, einzige Stelle mit Hexwerten) → Rollen (`--neon`, `--signal`,
`--ja`/`--nein`, `--gut`, `--warn` — was eine Farbe *bedeutet*) → Bereiche
(`--bereich-*`) → Wertegruppen (Charakterblatt) → Kulisse (Hintergrund,
Schimmer) → Form (Radius, Schrift).

**Kern der Trennung:** `--signal` heißt durchgehend „SL-geheim" — im Cyberpunk
Magenta, im Hextechpunk Gold. Keine Regel muss das wissen.

## Canvas-Sonderfall

Cytoscape zeichnet auf Canvas, kennt keine CSS-Variablen. `CampaignGraphView.tsx`
liest Werte zur Laufzeit über `getComputedStyle` (löst auch verkettete
Variablen bis zum Hexwert auf) + `MutationObserver` auf `data-theme` am
`<html>`, sonst bliebe der Graph nach Themewechsel in alten Farben stehen.

## Verifiziert (nicht nur behauptet)

Per Chrome DevTools Protocol gegen die laufende App: alle Tokens gesetzt, kein
unaufgelöstes `var()`; Themewechsel ändert 14/14 geprüfte Tokens; Auswahl
überlebt Neuladen; Canvas-Pixel ausgezählt (`#2fa96a`→`#38b189`).

## Siehe auch

- [[ui-konzept-commlink]] — das *Warum* der Optik, diese Seite das *Wie*
- [[../../../CLAUDE.md]] — Design-Entscheidungen im Gesamtkontext
