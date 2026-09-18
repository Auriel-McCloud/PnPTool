---
title: Cyberware und Bioware
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [cyberware, versionsgeschichte]
sources: [../../reference/Neotopia_Gegenstaende.md, ../../regeln-neotopia.md, ../../../backend/app/items/chrom.py]
status: aktuell
---

# Cyberware und Bioware

## Definition

**WVerlust = Willenskraftverlust.** Preis pro Bonuspunkt bestimmt die Rate:

| Preis je Bonus | Willenskraftverlust |
|---|---|
| 500¥ | Bonus × 2 (abgerundet) |
| 2.000¥ | Bonus |
| 5.000¥ | Bonus ÷ 2 (abgerundet) |
| 10.000¥ | Bonus ÷ 3 (abgerundet) |
| 20.000¥ | Bonus ÷ 4 (abgerundet) |

Prothese 10.000¥ (Verlust 2), Prothesen-Gadget 5.000¥. **Der Verlust senkt das
Willenskraft-Maximum dauerhaft** und zählt nur für *eingebaute* (verbaute) Ware
— im Rucksack liegende Cyberware zieht nichts ab.

## Drei Kategorien (unterschiedliche Zugänglichkeit)

- **Cyberware:** alle Preisstufen (Hinterhof 500¥ bis Maßanfertigung 20.000¥)
- **Bioware & Hexware:** erst ab Klinik (5.000¥+) — kein Hinterhof-Doc kann das
- Exklusiv-Pfade: **Hexware ermöglicht Magie** (nicht für Neuroweaver),
  **Bioware ermöglicht NeuroWeaving** (nicht für Magier) — Backend-Validierung
  + Frontend-Fehlerpopup implementiert.

## Rundungsregel (31.08.2026, nicht im Excel enthalten)

**Gerundet wird erst am Ende, mindestens aber ein Punkt.** Die Brüche der
einzelnen Implantate werden zuerst summiert, dann einmal gerundet:

| Chrom | roh | Verlust |
|---|---|---|
| 1 Implantat Konzernqualität | 0,67 | **1** (Minimum) |
| 2 davon | 1,33 | **1** |
| 3 davon | 2,0 | **2** |
| Hinterhofarbeit, Bonus 3 | 6,0 | **6** |

Damit zahlt sich teure Arbeit aus: würde jedes Stück einzeln aufgerundet,
kosteten zwei Konzernimplantate zusammen 2 statt 1. Ein bewusst mit 0
eingetragenes Stück (rein kosmetisch) bleibt kostenlos.

**Als allgemeines Prinzip erklärt** (Mark, 31.08.2026, ausdrücklich generalisiert):
Rohwerte summieren, erst die Summe runden/begrenzen — gilt auch für Rüstung
(Geschicklichkeitsabzug nach der Summe aller Boni) und Traglast. **Ausdrückliche
Ausnahmen:** Cyberdecks (höchstes Deck zählt, nicht Summe), Commlinks (bestes
Gerät für Cyberwall, nicht alle summiert).

## Reflex-Booster (Beispiel-Cyberware, aus dem Excel „SL-Ideen"-Bereich)

Sandevistan-Style, Initiative-Boost + Zusatzaktionen. 3 Stufen (5.000¥/20.000¥/
50.000¥), siehe [[../../reference/Neotopia_Gegenstaende.md]] für die volle Tabelle
inkl. des versteckten Easter Eggs. Geprüft am Spieltisch 04.09.2026: unverbaut
Initiative 7, mit Stufe 2 Initiative 13, Paralyse-Fall korrekt (Ampel 0,
`setztAus=true`).

## Entwicklung

- Grundformel (Preis→Verlust-Tabelle) **unverändert aus dem Excel**.
- **31.08.2026:** Rundungsregel hinzugefügt (Excel spezifiziert das nicht) und
  zum allgemeinen Rechenprinzip erklärt.
- **02.09.2026:** Hexware läuft über dieselbe Formel wie Cyber-/Bioware, ist
  nur eine Flavor-Kategorie ohne eigene Mechanik.
- Namenskonvention: **„verbaut" statt „ausgerüstet"** — Chrom sitzt im Körper.
  Entfernen ist **chirurgisch**, kein „Ablegen"-Button.
- **Kein generisches Bonus-Feld** — Initiative-Bonus nur am Reflex-Booster,
  nicht als allgemeines Feld für jedes Item (Marks Grundsatz gegen
  Sonderfall-Felder).

## Offene Frage: Willenskraft-Overkill

`CLAUDE.md` Punkt 8: totaler Minmaxer könnte durch Chrom-Attributboni
theoretisch über 30 Willenskraft kommen. **Entschieden:** kein Cap — „wer
soweit kommt, hat's verdient".

## Siehe auch

- [[willenskraft]] — die Ressource, die hier verloren geht
- [[magie-hexkraft]] / [[neuroweaving-decking]] — die beiden exklusiven Wege
- [[../../reference/Neotopia_Gegenstaende.md]] — vollständige Excel-Preistabellen
