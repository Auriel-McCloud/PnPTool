---
title: Rüstung — Kästchen + Schadensreduktion
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [ruestung, kampf, versionsgeschichte]
sources: [../../api/ruestung.md, ../../../backend/app/kampf/ruestung.py, ../../reference/Neotopia_Regeln.md]
status: aktuell
---

# Rüstung — Kästchen + Schadensreduktion

**Das am längsten diskutierte Regelstück im gesamten Projekt** — erst
Gespräch Mark/Claude am 10.09.2026, dann ein kompletter Umbau am 18.09.2026,
nachdem Mark das erste System selbst am Spieltisch ausprobiert hatte. Volle
Herleitung inkl. aller Sackgassen: [[../../api/ruestung.md]] — hier nur die
Kurzfassung mit Fokus auf die Entwicklung.

## Excel-Ursprung (Version 1)

Flacher `kraft`-Bonus: Waffenschaden+Nettoerfolge **gegen** die Rüstung
gerechnet. Bonus **konstant** — eine Weste mit Rüstung 3 blieb immer Rüstung 3,
egal wie oft getroffen. Dieses alte Feld existiert weiterhin für
Bestandsdaten/einfache Fälle, wird von den neuen Endpunkten aber nicht mehr
angefasst.

## Aktuelles System (18.09.2026 — Schadensreduktion)

**Zwei Werte, und diesmal: höher ist besser** (klassischer Soak-Wert):

- **Kästchen** (Max/Aktuell) — Substanz, die Treffer schluckt, bevor sie reißt.
- **Reduktion** (nur `ruestungReduktionBasis`, **kein** eigener Aktuell-Wert
  mehr) — wie viel Schaden die Rüstung pro Treffer direkt abfängt.

**Die effektive Reduktion wird aus dem Kästchen-Verhältnis abgeleitet**, statt
einen eigenen Zustand zu führen — Mark: *"könnte sich die Reduktion aufgrund
halbieren wenn die Kästchen halbiert werden? und dann beim 4tel? somit
bleibt eine Lederjacke mit 1 Absorption immer gleich, aber ein
Bombenschutzanzug der stark beschädigt wird wird schwächer"*:

| Kästchen-Anteil | Effektive Reduktion |
|---|---|
| über 50 % | volle Basis |
| über 25 % | halbe Basis (abgerundet) |
| darüber, aber >0 | ein Viertel (abgerundet) |
| 0 | keine |

Pro Treffer: `absorbiert = min(Stärke, Reduktion)`, `durchkommend = Stärke −
absorbiert`. Abstufung wie gehabt (Unheilbar→Tödlich→Schlag, Schlag halbiert),
angewandt auf `durchkommend`. Kästchenschaden unterscheidet sich weiter nach
Schadensart (Unheilbar immer volle Stärke, Tödlich = `absorbiert÷2 +
durchkommend`, Schlag nur bei Trigger `2×Stärke ≥ Kästchen-Aktuell`).

**Mehrere Teile = ein Pool** (unverändert, nur Sortierung gedreht): Kästchen
summiert, Reduktion vom Teil mit der **besten** Basis. Verbrauchsreihenfolge:
beste Reduktion zuerst.

## Die Durchlass-Fassung (10.09.2026 – 18.09.2026, abgelöst)

**Diese Version gilt nicht mehr — hier nur zum Verständnis der Historie.**

Ursprünglich hieß der zweite Wert "Durchlass", **niedriger war besser**: 0
bedeutete "hermetisch dicht", eine Lederjacke hatte hohen Durchlass (von
Haus aus löchrig), eine Bombenschutzweste startete bei 0. Es gab zwei
Unterwerte (Basis + Aktuell), weil die erste Fassung davon nur *einen*
(steigenden) Wert für beide Rechnungen nutzte — Ergebnis: volle Rüstung war
am *leichtesten* zu zerstören, angeschlagene praktisch unzerstörbar (genaues
Gegenteil vom Ziel). Der Fix trennte Basis (fix, für Kästchenschaden) von
Aktuell (steigend, für den HP-Schaden).

**Warum es weg ist:** Mark nach dem ersten Praxistest am Spieltisch:
*"Durchlass ist ein dummer Wert, sorry... wir ersetzen ihn durch
Schadensreduktion"*. Der Denkfehler-artige Charakter des Werts
("niedriger=besser" bei einem Rüstungswert widerspricht jeder Intuition) war
in der Theorie schon spürbar, zeigte sich aber erst in der Praxis als
störend genug für einen Umbau.

**Kollateralnutzen des Umbaus:** die neue Fassung braucht keinen eigenen
Aktuell-Wert für die Reduktion mehr (sie wird berechnet, nicht gespeichert)
— das hat zugleich eine Bug-Klasse eliminiert, siehe „Entwicklung" Punkt 7.

## Entwicklung (Zusammenfassung — Details in `docs/api/ruestung.md`)

1. Problem erkannt: flacher Bonus nutzt sich nicht ab
2. Erste Fassung (Durchlass): ein Wert → Paradox entdeckt (kaputt = unzerstörbar)
3. Fix: Basis/Aktuell-Trennung beim Durchlass
4. Pool-Regel für mehrere Teile, Verbrauchsreihenfolge nach Durchlass
5. Suspensorium-Missbrauch identifiziert und durch Reihenfolge selbst gelöst
6. Zerstörungs-/Wiederanlegen-Sperre ergänzt
7. **18.09.2026 — Bug: frisch aktivierte Rüstung ließ sich nicht ausrüsten.**
   Mark: neuen Gegenstand angelegt, im Bearbeiten-Formular zu einer Rüstung
   gemacht (Typ + `ruestungKaestchenMax` gesetzt) — landete beim Anlegen aber
   immer im Mitgeführten, egal als SL oder Spieler versucht. Ursache:
   `create_gegenstand` zieht `ruestungKaestchenAktuell` auf `Max` nach, wenn
   nicht ausdrücklich anders angegeben — das Bearbeiten-Formular geht aber
   über `PATCH` (`update_gegenstand`), und dort fehlte dieses Nachziehen
   komplett. Fix in `items/repository.py::update_gegenstand`: zieht `Aktuell`
   jetzt ebenfalls nach — aber **nur** wenn das Stück vorher
   `ruestungKaestchenMax == 0` hatte, nicht wenn eine bereits aktive,
   beschädigte Rüstung nachträglich bearbeitet wird.
8. **18.09.2026, direkt danach — Durchlass durch Schadensreduktion ersetzt.**
   Mark hatte das System zum ersten Mal selbst am Spieltisch benutzt und den
   Durchlass-Wert als unintuitiv verworfen (siehe oben). Kompletter Umbau:
   Formel (`kampf/ruestung.py`, alle 26 Tests neu geschrieben), Schema
   (`ruestungDurchlassBasis`/`Aktuell` → `ruestungReduktionBasis`, kein
   Aktuell-Feld mehr), beide Rüstungs-Routen (Treffer, Reparatur), vier
   Frontend-Dateien. Die zwei einzigen betroffenen Test-Rüstungen in der
   Kampagne wurden auf Marks Wunsch gelöscht statt migriert. Praxistest
   live gegen die echte Kampagne verifiziert (Ausrüsten, Treffer, Reparatur),
   keine Testspuren hinterlassen.

## Siehe auch

- [[../../api/ruestung.md]] — vollständige Herleitung mit Testfällen
- [[attribute-und-fertigkeiten]] — vierte Zustandsleiste auf dem Charakterblatt
- [[../comparisons/regelwerk-excel-vs-aktuell]] — Einordnung im Gesamtüberblick
