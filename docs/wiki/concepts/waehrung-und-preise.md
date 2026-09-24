---
title: Währung und Preise
created: 2026-09-18
updated: 2026-09-24
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
Scammer-Storylines, Frontend, Fahrzeug-Preisdiskussion. **Die
Rüstungsreparatur-Kosten sind seit 23.09.2026 geklärt** (eigene, vom
Shop-System unabhängige Preisformel — quadratisch/progressiv mit hartem
75%-Deckel bei Totalschaden, siehe `docs/api/ruestung.md` "Reparatur beim
Händler" und `ruestung-kaestchen-durchlass.md` Punkt 9) und brauchten das
Shop-System letztlich gar nicht.

**KI-Sortiment-Vorschlag (23.09.2026):** neues Modul
`backend/app/haendler/ki_vorschlag.py` — die KI schlägt passende Waren für
einen bestimmten Händler vor (bevorzugt bestehende Vorlagen, erfindet nur
bei echter Lücke etwas Neues), SL bestätigt jeden Vorschlag einzeln.
Backend end-to-end verifiziert, Frontend-Popup noch offen. Details:
`docs/api/haendler.md`.

**Shop-Frontend Phase 1+2 (24.09.2026):** Backend um Vertriebsart
(`PHYSISCH`/`DIGITAL`), Sonderangebote (`rabattProzent`) und Online-
Bestellungen erweitert — ein digitaler Kauf zieht das Kapital sofort ab,
übergibt die Ware aber erst, wenn die SL manuell "liefert" (kein fester
Termin, nur ein Freigabe-Knopf). Verhandeln (bisher nur bei
Rüstungsreparatur) um `SHOP_KAUF` erweitert, ohne den Mechanismus selbst
anzufassen — komplett generisch vorbereitet gewesen. Frontend erster Wurf:
eigener Burgermenü-Punkt "Shop" (SL + Spieler), Kachelraster aller Händler,
je eine "Fancy"-Seite für physische Shops (Hintergrundbild + Händlerporträt
+ Verhandeln-Knopf) und eine schlichte Seite für digitale
(kein Verhandeln), Seltenheitsrahmen als CSS-Effekt (grau/blau/silbern-
glitzernd/orange-gezackt/violett-wabernd, Marks exaktes Farbschema).
**Status: Backend end-to-end verifiziert, Frontend nur `tsc -b` geprüft,
CSS-Rarity-Effekte optisch ungegengeprüft (Browser-Tool erreicht kein
localhost).** Noch offen: KI-Item-Erzeugung für Alltagsgegenstände (nie
für Waffen/Rüstung), SL-Editor fürs Sortiment, KI-Sortiment-Vorschlag-
Popup. Details: `docs/api/haendler.md`, `CLAUDE.md` "Zuletzt gebaut".

**KI-Alltagsgegenstand-Erzeugung (24.09.2026):** neues Modul
`backend/app/haendler/alltagswunsch.py` — Spieler fragt einen Verkäufer im
Shop nach etwas, das nicht im Sortiment steht (z.B. Panzerklebeband), die
KI schätzt sofort Preis + Typ, geht als Popup an die SL zur Freigabe. Harter
Ausschluss von Waffen/Rüstung über zwei unabhängige Sperren (Typ-Whitelist +
KI-Selbsteinschätzung). Backend und Frontend fertig, E2E-verifiziert. Siehe
`docs/api/haendler.md`.

## Siehe auch

- [[../../reference/Neotopia_Gegenstaende.md]] — alle Preistabellen im Volltext
- [[cyberware-bioware]] — Preis→Willenskraftverlust
- [[ruestung-kaestchen-durchlass]] — Reparaturkosten geklärt (23.09.2026, Punkt 9)
