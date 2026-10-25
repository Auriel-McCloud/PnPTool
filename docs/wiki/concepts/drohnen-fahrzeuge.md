---
title: Drohnen und Fahrzeuge
created: 2026-09-18
updated: 2026-10-25
type: konzept
tags: [drohnen, fahrzeuge, kampf, erfahrung, wirtschaft, inventar, versionsgeschichte, entschieden, offen]
sources: [../../CLAUDE.md, ../../../backend/app/begleiter/, ../../../backend/app/entities/schemas.py, ../../../backend/app/traits/bogen.py, ../../../backend/app/traits/erfahrung.py, ../../../backend/app/kampf/ruestung.py, ../../../backend/app/kampf/initiative.py, ../../../backend/app/items/schemas.py, ../../../backend/app/items/chrom.py]
status: teilweise-umgesetzt
---

# Drohnen und Fahrzeuge

## Definition (Stand 25.10.2026 — komplett neu entschieden, siehe „Entwicklung“)

Mark baute einen Rigger-Charakter und merkte: das bisherige Drohne-Gegenstandsfeld
(Stufe/Widerstand/Angriff/Agilität direkt am `Gegenstand`, siehe „Alte Version“
unten) reicht nicht — eine Drohne soll Rüstung tragen, Waffen ausrüsten, eigene
Fertigkeiten haben und zusammen mit ihrem Rigger an der Initiative teilnehmen.
Das geht mit einem reinen Item nicht (ein Gegenstand kann nicht selbst Besitzer
eines anderen Gegenstands sein, siehe Architekturbegründung unten). Komplette
Neuentscheidung, im Chat mit Mark Punkt für Punkt durchgesprochen.

### Architekturentscheidung: eigener Person-artiger Knotentyp

`Gegenstand`-Besitz läuft im ganzen Projekt ausschließlich über
`(:Person)-[:BESITZT]->(:Gegenstand)` (siehe
[[../entities/neo4j-datenmodell]]). Damit eine Drohne Waffen/Rüstung tragen
kann, muss sie selbst ein `Person`-Knoten sein — alles andere würde das
komplette Besitz-/Ausrüstungssystem für einen zweiten Knotentyp duplizieren.

Neue Flags `istDrohne`/`istFahrzeug` an `Person`, nach demselben Muster wie
`istCritter`/`istKI` (20.09.2026): `sichtbare_kategorien()` tauscht die
Blattstruktur komplett aus, statt eine eigene Blattvariante zu pflegen. Damit
sind Ausrüstungssystem (`BESITZT`/`AUSGERÜSTET`), Initiative-Pool-Mechanismus
und die Rigger-Beziehung (`BEGLEITET` Person→Person, wie bei Critter) **ohne
Parallelimplementierung** mit dabei.

Das alte Begleiter-Sheet (Sprite/Geist, `app/begleiter/`) bleibt für Sprites
und Geister unverändert bestehen — andere Mechanik (kein Körper, kein
Rucksack), bewusst nicht angefasst.

### Die 8 Attribute — zwei Spalten statt drei

Keine dritte (soziale) Spalte, Drohnen/Fahrzeuge haben keine Sozialwerte.

| Körperlich | Technisch |
|---|---|
| Stärke | CPU |
| Geschick | Arbeitsspeicher |
| Geschwindigkeit | Außenhülle (Rüstungsreduktion — teurer, siehe Kosten) |
| Widerstandsfähigkeit | I.C.E. (Matrix-Verteidigung — **eigenes steigerbares Attribut**, nicht abgeleitet wie bei Menschen/Neuroweavern) |

### Initiative

`Geschwindigkeit + CPU` — neuer Formel-Zweig in `bogen.py::initiative()`
neben der bestehenden `Geistesschärfe + Geschicklichkeit + Cyberware-Mod` für
Menschen. Gleiches Muster wie `ice_max()`, das für Neuroweaver schon einen
Sonderzweig hat.

### Fertigkeiten

**Entschieden (25.10.2026): die volle Fertigkeitenliste, kein Filter.** Mark:
auch soziale Fertigkeiten wie Etiketten/Menschenkenntnis/Darbietung können bei
einem Roboter Sinn ergeben (Benimm-Programme, Gesichtserkennung) — keine
Kategorie wird grundsätzlich ausgeschlossen. Drohnen/Fahrzeuge nutzen damit
dieselbe `Fertigkeit`-Kategorie wie Menschen, keine eigene
`FertigkeitDrohne`-Kategorie nötig.

**Neue Fertigkeit „Fliegen" läuft über die bestehenden Zusatzfertigkeiten**
(`app/zusatzfertigkeiten/`, campaign-gebundener SL-Katalog), nicht über den
Kern-Trait-Katalog — Marks eigene, bessere Lösung: keine Katalog-Änderung,
kein Code. `HAT_ZUSATZFERTIGKEIT` hängt generisch an `Person`, ohne
Typ-Ausschluss — sobald Drohne/Fahrzeug ein Person-Knoten ist (siehe oben),
ist „Fliegen" dort automatisch genauso wählbar wie bei einem menschlichen
Piloten. Mark trägt es einfach in die SL-Tabelle „Zusatzfertigkeiten" ein.

### Lebenspunkte / Struktur

Kein neues System nötig: `bogen.py::gesundheit_max()` ist bereits
`personenspezifischer Grundwert + Widerstandsfähigkeit` (seit dem
Critter-Feature vom 10.10.2026, siehe [[attribute-und-fertigkeiten]]). Ein
Raumschiff bekommt einfach einen hohen Grundwert, das Kästchen-Tracking im
Blatt skaliert automatisch mit — exakt dieselbe Mechanik wie bei einer Ratte
mit Grundwert 1.

### Erschaffung & Steigerung: Nuyen statt XP

Gleiche Formel-Mechanik wie `traits/erfahrung.py` (Preis = aktueller Wert ×
Faktor, Einstieg per `NEU_KOSTEN`), aber in Nuyen statt Erfahrungspunkten:

- **`AttributDrohne`** (Stärke/Geschick/Geschwindigkeit/Widerstandsfähigkeit/
  CPU/Arbeitsspeicher/I.C.E.) — Standard-Attribut-Faktor, wie bei Menschen.
- **`AttributDrohneAussenhuelle`** — gleicher Einstiegspreis wie die anderen
  Drohnen-Attribute, aber **doppelter Faktor** (Marks Vorgabe: „der erste ist
  noch günstig, aber ab dem zweiten wird's rapide teurer“) — reiner
  Zahlendreh in derselben Formel, kein neuer Mechanismus.
- Fertigkeiten laufen über die normale **`Fertigkeit`**-Kategorie, dieselbe
  wie bei Menschen (siehe oben — keine eigene Kategorie nötig).
- Neue Kampagnen-Einstellung **`nuyenProXp`** (Default **200¥**, Mark kann sie
  jederzeit im Einstellungen-Popup ändern — Startwert zum Playtesten, keine
  endgültige Zahl). Rechnet den XP-Formel-Preis in Nuyen um. Der Kauf läuft
  über den bestehenden `VerhandlungPopup`-Mechanismus (Spieler bietet,
  Mark bestätigt/ändert) — gleiches Muster wie Rüstungsreparatur beim Händler.
- **Anzeige-Deckel:** Punkte werden als Kreise angezeigt bis zu einer
  Obergrenze (Vorschlag: 10, analog zur Waffenschaden-Skala 1–12, wo ab 8 nur
  noch Schiffswaffen stehen), darüber nur die nackte Zahl — sonst hätte ein
  Raumschiff-Attribut 30+ Kreise. **Exakte Zahl noch offen.**

### Riggerkonsole & aktive Slots

- `riggerBonus` und `maxDrohnen` existieren bereits als Felder am
  Riggerkonsole-`Gegenstand` (`items/schemas.py`) — bisher nur Datenablage,
  nirgends ausgewertet. Werden jetzt zum Slot-Limit.
- Neues Feld `riggerAktiv` am Drohnen/Fahrzeug-Knoten. Aktivieren/Deaktivieren
  serverseitig gegen `maxDrohnen` der ausgerüsteten Konsole gedeckelt.
- Neues Burgermenü **„Fahrzeuge & Drohnen“**, auch für Spieler sichtbar:
  - **Ohne Riggerkonsole:** eine einzelne Steckbrief-Kachel (Bild, Zustand,
    Werte), Klick öffnet das Detail-„Charakterblatt“-Popup.
  - **Mit Riggerkonsole:** oben visuell umrandete **aktive Slots** (Bild +
    Kurz-Steckbrief je Drohne), darunter eine Liste aller übrigen
    Drohnen/Fahrzeuge mit Aktivieren/Deaktivieren-Knopf.
- **Inaktive Drohnen erscheinen NICHT im Kampf** — die
  Teilnehmer-Hinzufügen-Liste filtert auf `riggerAktiv=true`.

### Ausrüstung

Da `Person`-Knoten: Waffen und Rüstung laufen 1:1 über das bestehende
`BESITZT`/`AUSGERÜSTET`-System, keine Parallelimplementierung.

### Reparatur (neues eigenständiges Feature, gilt für Rüstung UND Drohne/Fahrzeug)

`kampf/ruestung.py` hat die komplette Formel schon fertig, bisher nur an
Rüstung gebunden — wird generisch auf jedes „Kästchen“-tragende Ziel
ausgeweitet:

- `hardware_probe_pool()` = **Maker (Hardware) + Intelligenz** (Würfelpool
  für die technische Reparatur-Probe).
- `reparatur_schwelle()`/`selbstreparatur_ergebnis()` — Erfolgs-Überschuss
  über die halbe Kästchen-Max wird zu reparierten Kästchen, gedeckelt vom
  eingesetzten Material.
- `haendler_reparatur_preis()` — fertige quadratisch-progressive Preisformel
  mit 75 %-Totalschaden-Deckel, schon generisch (`fehlende_kaestchen`/
  `kaestchen_max`/`neuwert`, kennt „Rüstung“ gar nicht explizit).
- **Ein Skill reicht am Fahrzeug** (Mark: Handwerk *oder* Maker (Hardware)
  können ein Fahrzeug reparieren, kein getrennter Struktur-/
  Elektronik-Schadenspool).
- Neues eigenständiges Burgermenü **„Reparatur“**: ein Slot für das Ziel
  (Rüstung/Drohne/Fahrzeug), ein Slot für das Verbrauchsmaterial — statt wie
  bisher im Bearbeiten-Popup des einzelnen Gegenstands versteckt
  (`RuestungReparatur.tsx`).
- Neuer Verbrauchsgegenstand **„Maschinenteil“**, analog zu
  `istReparaturmaterial`/`reparaturKapazitaet`: Qualitätsstufen
  minderwertig/normal/hochwertig — hochwertig für Attribute, normal für
  Fertigkeiten, minderwertig nur für Reparatur.
- Neues Händler-Flag **`bietetReparatur`** (analog `istTutorialHaendler`) —
  nicht jeder Laden repariert gegen Geld.

## Entwicklung

- **18.09.2026 (Version 1):** Begleiter-Sheet-basiertes Konzept, siehe „Alte
  Version“ unten.
- **25.10.2026 (komplette Neuentscheidung):** im Chat mit Mark Punkt für
  Punkt durchgesprochen (Architektur, 8 Attribute, Initiative, I.C.E.,
  Nuyen-Kosten, Riggerkonsole-Slots, Reparatursystem) — siehe „Definition“
  oben. Auslöser: Mark baute einen Rigger-Charakter, das alte
  Drohne-Gegenstandsfeld reichte nicht mehr.
- **25.10.2026 (Phase 1 — Datenmodell-Fundament gebaut, direkt im Anschluss):**
  `istDrohne`/`istFahrzeug`/`riggerAktiv` an `Person`, acht TraitDef-Attribute
  (`AttributDrohne`×7, `AttributDrohneAussenhuelle`×1), `sichtbare_kategorien()`/
  `initiative()`/`ice_max()` mit `ist_drohne`-Zweig, neue Kosten-Kategorien in
  `erfahrung.py`. `gesundheit_max()` brauchte keine Änderung. **Verifiziert:**
  `pytest tests/test_bogen.py tests/test_drohnen_kosten.py` grün, volle Suite
  ohne Regression. Details siehe `CLAUDE.md`. **Phase 2 (Nuyen-Kauf-Endpoint,
  Riggerkonsole-Aktiv-Slot-Durchsetzung, Kampf-Filter, Frontend-Burgermenü,
  Reparatur-Menü, Maschinenteil) noch nicht gebaut.**
## Alte Version (bis 25.10.2026, status: veraltet — abgelöst durch obige Neuentscheidung)

Beim Kauf wurde die **Stufe** festgelegt und frei auf Werte/Fertigkeiten
verteilt:
- Gesundheit = Stufe
- Widerstand = Schadensreduktion
- Angriff = Treffen und Schaden
- Agilität = Geschwindigkeit

**Riggen:** nutzte eigene Werte, aber höchstens bis zur Stufe der Drohne.
Charakterblatt und eigenes `DrohneFahrzeug`-Sheet enthielten je bis zu 4 Slots
für „Drohne/Fahrzeug/Sprite/Geist“ (`Neotopia.xlsx`) — siehe
[[../../reference/Neotopia_Drohnen_Fahrzeuge.md]].

**Preisformel (Excel, abgelöst durch das neue Nuyen-pro-Attribut-System):**

| Typ | Formel |
|---|---|
| Fahrzeug | Stufe×5.000¥ bis Stufe 5, ab 5×20.000¥, ab 10×40.000¥ |
| Drohne | Stufe×500¥ bis Stufe 5, ab 5×1.000¥, ab 10×5.000¥ |

Mark hatte diese Formel schon am 30.08.2026 selbst infrage gestellt (Motorrad
Stufe 3 = 15.000¥, kaum leistbar) — das war mit ein Auslöser für die
Neuentscheidung vom 25.10.2026.

## Offene Fragen (vor dem Bauen noch zu klären)

- **Punkte-Anzeige-Deckel:** Vorschlag 10 Kreise, dann nur Zahl — exakte
  Zahl noch offen.
- **Start-Faktoren für `AttributDrohne`:**
  Stufe×500¥/5.000¥-Tabelle angelehnt, oder komplett neu kalibrieren?
- **`nuyenProXp` = 200¥** ist ein bewusster Startwert zum Playtesten am
  Spieltisch, keine endgültige Zahl.

## Siehe auch

- [[../entities/neo4j-datenmodell]] — `BESITZT`/`BEGLEITET`-Kanten, Grund für
  die Person-Knoten-Entscheidung
- [[erfahrung-und-steigern]] — Faktor-Formel, die für Nuyen-Kosten wiederverwendet wird
- [[kampf-und-initiative]] — Initiative-Formel-Erweiterung
- [[cyberware-bioware]] — Vorbild für Qualitätsstufen-Preislogik (Chrom)
- [[ruestung-kaestchen-durchlass]] — Vorbild für die wiederverwendete Reparaturformel
- [[attribute-und-fertigkeiten]] — Grundwert-pro-Entität-Mechanismus (Critter-Feature)
- [[../../CLAUDE.md]]
