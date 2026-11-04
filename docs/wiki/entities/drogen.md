---
title: Drogen schlucken
created: 2026-11-04
updated: 2026-11-04
type: entität
tags: [inventar, kampf, cyberware, geplant]
sources: [../../reference/Neotopia_Gegenstaende.md, ../../../backend/app/items/repository.py, ../../../backend/app/kampf/booster.py, ../../../backend/app/items/augments.py]
status: teilweise-umgesetzt
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
9. **Schlag und schwerheilbar sind Schaden**, nicht eine „Schwere“. Tippfehler,
   04.11.2026. Die Nebenwirkung schreibt `schadenSchlag` bzw.
   `schadenAggraviert`. Die heilen über die bestehende Rast. Tödlich bleibt
   die Uhr aus Punkt 8, nicht die Spur.
10. **Reduktion statt halbieren.** Keine Halbierungs-Funktion. Die Droge trägt
    `ruestungReduktionBasis` und addiert den Wert auf die Reduktion der
    aktiven Rüstung. Die Pool-Regel bleibt: Teile summieren sich nicht, es
    gilt die beste Basis, dann die Kästchen-Stufe
    ([[../concepts/ruestung-kaestchen-durchlass]]). Die Droge kommt danach
    obendrauf, auf die effektive Reduktion, nicht in die Basis — sonst
    würde eine kaputte Weste die Droge mitschwächen. Ohne Rüstung oder bei
    0 Kästchen ist der Rüstungsanteil 0, die Droge addiert trotzdem. Das
    „Rest wird schwerheilbar“ aus der Halbieren-Idee ist nicht mitgekommen.
11. **Heilreihenfolge** (04.11.2026):
    - minderwertig: Menge in Schlagpunkten, nur Schlag.
    - normal: Menge in tödlichen Punkten. Zuerst tödlich, 1:1. Rest × 3 =
      Schlag. Kein tödlicher Schaden da: die ganze Menge × 3 auf Schlag.
      Schwerheilbar unberührt.
    - hochwertig: Schlag und tödlich komplett weg, automatisch, verbraucht
      die Menge nicht. Die Menge geht zuerst auf schwerheilbar.
12. **Umwandeln, kein neuer Schaden** (04.11.2026). Wenn die Nebenwirkung
    einsetzt, kann ihre Funktion vorhandenen Schaden verschieben, 1:1:
    - aller Schlag wird tödlich (`schadenSchlag` → `schadenSchwer`)
    - oder, die schlimme Fassung: aller Schlag und aller tödliche Schaden
      wird schwerheilbar (beide Spuren auf `schadenAggraviert`, Quellen auf 0)
    Nichts wird addiert. Das ist nicht die 2-Rasten-Uhr aus Punkt 8. Die Uhr
    ist eine Dauer. Umwandeln schreibt auf die echten Spuren.
13. **Die Rast zählt mit**, auch die, die den Crash startet. Wie
    `schwerHeilZaehler`: die Rast, in der die Bedingung da ist, ist schon
    der erste Tick, nicht ein Freibeginn. Zwei Ticks, dann ist die
    tödliche Uhr weg. Ein Szenenwechsel ist keine Rast und tickt nicht.
    Die Sperre „Zähler steht, solange tödlicher Schaden offen ist“ gilt
    weiter nur für schwerheilbar, nicht für die Drogen-Uhr.
    Setzt der Crash in derselben Rast ein, wird zuerst umgewandelt, dann
    heilt die Rast. Sonst ist der Schlag schon auf 0, bevor er tödlich
    werden kann. Folge: Schlag→tödlich verliert in derselben Rast noch
    1 tödlichen Punkt an Schritt 2 der Rast.

## Noch offen

Nicht bauen, bevor er das sagt.

- **Granate / Wurftrank** bleibt auf [[gegenstand-transfer]]. Wird geworfen,
  nicht geschluckt.
- **Gift an einer anderen Person im Kampf**, Schaden pro Kampfrunde.
  Mark, 04.11.2026: das ist etwas anderes, später. Nicht der Schluck an
  sich selbst.

## Ersetzt, nicht mehr offen

- Heilreihenfolge — Punkt 11.
- Schlag/schwerheilbar als Uhr oder Spur — Punkt 9, es ist Schaden.
- Schaden halbieren — Punkt 10, es ist Reduktion auf der aktiven Rüstung.
- Ob die startende Rast bei der 2-Rasten-Uhr mitzählt — Punkt 13, sie zählt.

## Siehe auch

- [[../concepts/cyberware-bioware]] — die Funktionen, die der Schluck aufruft
- [[../concepts/willenskraft]] — SL-only-Rückgabe, hier die Ausnahme
- [[../concepts/kampf-und-initiative]] — Reflex-Booster
- [[party-feature]] — Aufenthaltsort als Szenenende
- [[../concepts/ruestung-kaestchen-durchlass]] — Reduktion, Droge addiert obendrauf
- [[gegenstand-transfer]] — Heiltrank-Frage, ersetzt
