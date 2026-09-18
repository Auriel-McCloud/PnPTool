---
title: Rüstung — Kästchen + Durchlass
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [ruestung, kampf, versionsgeschichte]
sources: [../../api/ruestung.md, ../../../backend/app/kampf/ruestung.py, ../../reference/Neotopia_Regeln.md]
status: aktuell
---

# Rüstung — Kästchen + Durchlass

**Das jüngste und mit Abstand am längsten diskutierte Regelstück im gesamten
Projekt** (Gespräch Mark/Claude, 10.09.2026). Volle Herleitung inkl. aller
Sackgassen: [[../../api/ruestung.md]] (404 Zeilen) — hier nur die Kurzfassung mit
Fokus auf die Entwicklung vom Excel weg.

## Excel-Ursprung (Version 1)

Flacher `kraft`-Bonus: Waffenschaden+Nettoerfolge **gegen** die Rüstung
gerechnet. Bonus **konstant** — eine Weste mit Rüstung 3 blieb immer Rüstung 3,
egal wie oft getroffen. Rüstungsboni werden addiert; ab Wert 3 gibt es −1 auf
Geschicklichkeit, ab 4 entsprechend −2.

Dieses alte Feld existiert weiterhin für Bestandsdaten/einfache Fälle, wird von
den neuen Endpunkten aber nicht mehr angefasst.

## Aktuelles System (10.09.2026)

**Grundidee: zwei Werte statt einem**, und **niedriger ist besser**:

- **Kästchen** (Max/Aktuell) — Substanz, die Treffer schluckt, bevor sie reißt.
- **Durchlass** (Basis/Aktuell) — Größe der Lücke: was garantiert ungehindert
  durchkommt. 0 = hermetisch dicht. Lederjacke hat hohen Durchlass (von Haus
  aus löchrig), Bombenschutzweste startet bei 0.

**Warum Basis UND Aktuell getrennt:** die erste Fassung hatte nur einen
steigenden Durchlass-Wert für beide Rechnungen — Ergebnis: volle Rüstung war
am *leichtesten* zu zerstören, angeschlagene praktisch unzerstörbar (genaues
Gegenteil vom Ziel). Fix: Kästchenschaden rechnet immer gegen die **fixe
Basis**, nur der HP-Durchlass gegen die **steigende Aktuell**-Schwelle.

**Abstufung statt Blocken:** Unheilbar→Tödlich (gleiche Menge), Tödlich→Schlag
(gleiche Menge), Schlag→Schlag halbiert (unterste Stufe). Menge ist immer
`garantiert = min(Stärke, Durchlass-Aktuell)`.

**Kästchenschaden unterscheidet sich stark je Schadensart:**
- Unheilbar: immer volle Stärke 1:1 („das wäre wie eine Explosion")
- Tödlich: Anteil bis zur Basis-Schwelle nur halb, Anteil darüber voll
- Schlag: löst nur aus wenn `2×Stärke ≥ Kästchen-Aktuell` (laues Klopfen prallt ab)

**Mehrere Teile = ein Pool** (Mark: „ich will keine Körperzonen, das ist zu
kompliziert"): Kästchen summiert, Durchlass vom **dichtesten** Teil.
Verbrauchsreihenfolge: dichtestes Teil zuerst, killt dadurch von selbst den
„kugelsicheres Suspensorium"-Trick (kleines dichtes Teil wäre sonst permanent
tragbar, ist aber nach einem Kästchen weg).

**Zerstörte Rüstung (0 Kästchen) fliegt aus der Ausrüstung** ins Mitgeführte
(reparierbar, wie ausgebautes Chrom); Wiederanlegen gibt 409.

**Reparatur:** Rechnung fertig (`kampf/ruestung.py::repariere`), aber ohne
Skill-Probe/Preis — SL trägt Ergebnis von Hand ein. **Status:
teilweise-umgesetzt**, wartet auf Hardware-Skill-Check bzw. Shop-System.

## Entwicklung (Zusammenfassung — Details in `docs/api/ruestung.md`)

1. Problem erkannt: flacher Bonus nutzt sich nicht ab
2. Erste Fassung: ein Durchlass-Wert → Paradox entdeckt (kaputt = unzerstörbar)
3. Fix: Basis/Aktuell-Trennung
4. Pool-Regel für mehrere Teile, Verbrauchsreihenfolge nach Durchlass
5. Suspensorium-Missbrauch identifiziert und durch Reihenfolge selbst gelöst
6. Zerstörungs-/Wiederanlegen-Sperre ergänzt

## Siehe auch

- [[../../api/ruestung.md]] — vollständige Herleitung mit Testfällen
- [[attribute-und-fertigkeiten]] — vierte Zustandsleiste auf dem Charakterblatt
- [[../comparisons/regelwerk-excel-vs-aktuell]] — Einordnung im Gesamtüberblick
