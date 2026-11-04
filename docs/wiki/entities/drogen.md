---
title: Drogen schlucken
created: 2026-11-04
updated: 2026-11-04
type: entität
tags: [inventar, kampf, cyberware, geplant]
sources: [../../reference/Neotopia_Gegenstaende.md, ../../../backend/app/items/repository.py, ../../../backend/app/kampf/booster.py, ../../../backend/app/items/augments.py]
status: entschieden-nicht-umgesetzt
---

# Drogen schlucken

Mark, 04.11.2026. Dinge, die eine Person schluckt. Einmal wirken, dann ist der
Stapel um eins kleiner. Kein neuer Effekt-Baukasten. Die Droge ruft die
Funktionen auf, die Cyberware schon hat, und hängt nur eine Uhr darum.

Nicht gebaut. Die offenen Stellen unten nicht still schließen.

## Was schon da ist

`Droge` ist ein Gegenstandstyp. Wirkung und Nebenwirkung aus dem Excel stehen
nur als Text in der Beschreibung (`docs/reference/Neotopia_Gegenstaende.md`,
Zeilen 120–131). Die Summen für Würfelboni, Initiative und
Spezialisierungstexte zählen heute nur, was ausgerüstet oder verbaut ist
(`items/repository.py`, `WIRKT`). Der Kommentar bei der Initiative nennt Dash
schon, zählt ihn aber nur angezogen. Schlucken ersetzt das Anziehen.

Excel-Zeiten (3 Runden, 10 Minuten, 3 Stunden, 48 Stunden) werden nicht
nachgebaut. Sie fallen auf die drei Dauern unten.

## Entscheidungen (04.11.2026)

1. **Kein eigener Typ `Heiltrank`.** Heilen ist eine Droge. Mark: Drogen sind
   auch Medizin. Die alte offene Frage auf [[gegenstand-transfer]] ist damit
   ersetzt, nicht gelöscht.
2. **Kopie, nicht das Stück.** Schlucken zieht 1 vom Stapel. Bei 0 in den
   Müll, nicht ins Nichts. Der laufende Effekt ist eine Kopie an der Person.
   Die Vorlage später umschreiben ändert den Rausch nicht. Kein Cap — zwei
   Dash addieren sich. Spieler am eigenen Zeug, die SL an allem.
3. **Dieselben Funktionen wie Chrom**, an der Person, nichts an die Waffe
   geschraubt:
   - Würfelboni (`traitBoni`)
   - Initiative (`initiativeBonus`)
   - Spezialisierungstexte an genau diesen Boni
   - Zusatzaktion über den Reflex-Booster (`kampf/booster.py`): zweiter
     Initiativwurf, Ampel, Paralyse. Keine saubere Extra-Aktion daneben.
   - Augment-Zahlen (Schaden, Rüstung, Initiative) über
     `wende_augment_boni_an`, an der Person, nicht montiert.
   Willenskraftverlust aus `chrom.py` bleibt am verbauten Chrom. Den ruft
   eine Droge nicht auf.
4. **Drei Dauern für die Wirkung:** sofort, Szene, Rast. Umschalter an der
   Droge.
   - Sofort: Heilung, Zusatzaktion, Willenskraft. Keine Runden-Uhr.
   - Szene: endet, wenn die Party dieser Person Ort oder Event wechselt
     (`BEFINDET_SICH_AN`, siehe [[party-feature]]). Wer in keiner Party
     steckt, hat keinen Szenenwechsel — das Plus hält bei dem bis zur Rast.
     Kein Extra-Knopf.
   - Rast: die bestehende Rast (`docs/api/rast.md`).
5. **Nebenwirkung startet, wenn die Wirkung vorbei ist.** Bis dahin nur das
   Plus. Dieselben Felder, negatives Vorzeichen.
   - Wirkung bis Rast: die Nebenwirkung startet bei dieser Rast und hält
     noch eine weitere Rast.
   - Wirkung sofort: die Nebenwirkung startet mit dem Schluck. Folgt aus
     der Reihenfolge, nicht nochmal gefragt.
   - Wirkung bis Szene: die Nebenwirkung startet beim Szenenwechsel und
     hält bis zur Rast. Das war die erste Fassung, die spätere Frage hat
     nur den Bis-Rast-Fall geändert.
6. **Willenskraft: der ausgegebene Stand**, nicht das Maximum. Schlucken
   darf ihn heben, auch der Spieler. Das ist eine Ausnahme zur SL-only-Regel
   auf [[../concepts/willenskraft]]. Senken darf der Schluck ebenfalls.
   Heben und Senken können Wirkung oder Nebenwirkung sein.
7. **Heilen** sitzt an der Droge, Menge plus Qualität. Dieselben drei Wörter
   wie beim Material, nicht die Chrom-Leiter Hinterhof–Maßanfertigung:
   - minderwertig: nur Schlagschaden
   - normal: auch tödlich
   - hochwertig: auch schwerheilbar, selten und teuer — das ist der Preis
     im Katalog, kein Extra-Code
   Heilt eine Droge nur und hat kein Plus, ist das sofort, und die
   Nebenwirkung startet mit dem Schluck.
8. **Tödliche Schwere** der Nebenwirkung ist eine eigene Uhr: nach 2 Rasten
   weg. Nicht `schadenSchwer`. Die tödliche Spur heilt einen Punkt pro Rast,
   das wollte er hier nicht.

## Noch offen

Nicht bauen, bevor er das sagt.

- **Heilreihenfolge.** In welcher Reihenfolge eine Heilmenge die erlaubten
  Stufen frisst. Die Rast macht leichten zuerst, die Drohnen-Reparatur
  schweren. Nicht entschieden.
- **Schlag- und schwerheilbare Schwere.** Er hat sie als „heilt wie
  Schlagschaden / schwerheilbarer Schaden“ beschrieben. Nur die tödliche
  Schwere ist entschieden (eigene Uhr, nicht die Spur). Ob Schlag und
  schwerheilbar echte Spuren sind oder ebenfalls Uhren, ist nicht gefragt
  worden. Nicht als Spur festschreiben.
- **Zählt die Rast, die einen Crash startet, bei der 2-Rasten-Uhr mit?**
  Der Bis-Rast-Fall sagt: startet bei der Rast, hält noch eine weitere.
  „Nach 2 Rasten weg“ sagt nicht, ob die startende Rast eine der zwei ist.
- **Schaden halbieren**, Rest danach schwerheilbar. Keine bestehende
  Funktion. Kein Menü an jeder Droge. Wartet als eigene Mechanik, wenn er
  die eine Droge will.
- **Granate / Wurftrank** bleibt auf [[gegenstand-transfer]]. Wird geworfen,
  nicht geschluckt.

## Siehe auch

- [[../concepts/cyberware-bioware]] — die Funktionen, die der Schluck aufruft
- [[../concepts/willenskraft]] — SL-only-Rückgabe, hier die Ausnahme
- [[../concepts/kampf-und-initiative]] — Reflex-Booster
- [[party-feature]] — Aufenthaltsort als Szenenende
- [[gegenstand-transfer]] — Heiltrank-Frage, ersetzt
