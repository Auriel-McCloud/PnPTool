---
title: Charaktererschaffung
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [charaktererschaffung, attribute, fertigkeiten, versionsgeschichte]
sources: [../../reference/Neotopia_Charaktererschaffung.md, ../../regeln-neotopia.md, ../../../backend/app/traits/erstellung.py]
status: aktuell
---

# Charaktererschaffung

## Definition

1. **Alle Attribute starten auf 1**, verändert durch die Rasse (siehe [[rassen]]).
2. **Rassen** geben Startmaximum + frei verteilbare Punkte für die drei
   Attributspalten (Körperlich/Gesellschaftlich/Geistig), frei zuordenbar
   welche Spalte welche Zahl bekommt.
3. **Fertigkeiten** — eines von drei Paketen:
   - *Profi*: 1×4, 3×3, 3×2, 1×1 (8 Fertigkeiten)
   - *Ausgeglichen*: 3×3, 5×2, 7×1 (15 Fertigkeiten)
   - *Jack of all Trades*: 1×3, 8×2, 10×1 (19 Fertigkeiten)
4. **Startkapital: 10.000¥**
5. **15 Freebees**, Kosten: Attribut/Hexkraft/NeuroWeaving 5 (darf Startmaximum
   übersteigen), Fertigkeit 2 (höchstens +1), Willenskraft 1, Kredit 10.000¥=1,
   Eigenkapital 10.000¥=2. Das Startmaximum gilt nicht für Freebees.

**Code-Ableitung:** Die Startmaximum-Tabelle des Excels ist durchgehend
„4 + Rassenmodifikator" — im Code (`backend/app/traits/erstellung.py`) steht
deshalb nur die Grundzahl 4, verrechnet mit dem Modifikator, statt die Tabelle
doppelt zu führen.

## Was NICHT aus dem Excel kommt (im Tool erfunden)

- **Hintergründe** (Kontakte, Ressourcen, Straßenruf, Verbündete, Mentor,
  Unterschlupf, Schwarzmarkt, Konzernzugang, Ausrüstung, Geheimwissen) — Marks
  Wunsch, „bis zu 5 Punkte als Freebees", Liste selbst ein Vorschlag
  (`HINTERGRUENDE` in `erstellung.py`), **zum Umbau frei**.
- **Erfahrung/Steigern nach der Erstellung** — siehe [[erfahrung-und-steigern]],
  eigene Konzeptseite, weil eigenständig genug.

## Entwicklung

Kein grundlegender Regelwechsel seit dem Excel bei der Erschaffung selbst — die
Veränderungen liegen bei den **abgeleiteten** und **später gebauten** Systemen
(Gesundheit, Rassen-Baukasten, Erfahrung), nicht in der Erschaffungslogik selbst.
Siehe [[rassen]] für den größten Umbau (Baukasten statt Fixtabelle, 11.09.2026).

## Offene Fragen

- Sphären beim Freebee-Kauf: Excel-Zeile 39 nennt nur „Attribut/Hexkraft/
  NeuroWeaving 5", Zeile 27 stellt Sphären aber zu den Fertigkeiten (Kosten 2).
  Umgesetzt ist vorerst der Fertigkeitspreis. **Status: offen.**

## Siehe auch

- [[attribute-und-fertigkeiten]] — was verteilt wird
- [[rassen]] — Modifikatoren und der Baukasten
- [[waehrung-und-preise]] — Startkapital-Kontext
