---
title: Gegenstand- und Geld-Transfer
created: 2026-09-26
updated: 2026-09-26
type: entität
tags: [inventar, verhandlung, party, wirtschaft, geplant, offen]
sources: [../../../CLAUDE.md, ../../api/verhandlung.md, ../../../backend/app/verhandlung/, ../../../ideen für später.txt]
status: teilweise-umgesetzt
---

# Gegenstand- und Geld-Transfer

Spieler sollen einander Kram und Geld geben können — nicht die SL
stellvertretend umlegen. Zustimmung über dasselbe Verhandlungs-Popup wie
Rüstungsreparatur und Shop-Kauf (`app/verhandlung/`), damit niemandem ungefragt
etwas ins Inventar oder aufs Kapital geschoben wird.

Notiert 26.09.2026 in `ideen für später.txt` (zwei Commits), erster Baustein
am selben Tag gebaut (`50321a6`).

## Gebaut (26.09.2026) — Gegenstand innerhalb der Party

Neue Verhandlungsart `GEGENSTAND_WEITERGABE`. Spieler bietet einem Mitglied
**derselben Party** einen **eigenen** Gegenstand an. Empfänger bekommt das
bestehende `VerhandlungPopup` (ohne ¥-Betrag) und nimmt an oder lehnt ab.
Bei Annahme: `items/repository.py::transfer_owner` — Besitzkante wandert,
Gegenstand bleibt derselbe Node.

**Warum Party, nicht „gleicher Ort“:** PCs haben keinen eigenen
`BEFINDET_SICH_AN`-Standort, nur die Party (siehe [[party-feature]]). Für
Party-intern reicht die Mitgliedschaft. „Leute am gleichen Ort, die nicht in
derselben Party sind“ braucht erst einen Personen-Standort — **nicht gebaut,
nicht entschieden**.

**Wer darf:** nur Spieler, nur eigener Besitz, nicht an sich selbst, nur
Party-Mitglieder. Die SL hat diese Route nicht (403) — sie legt weiter über
die bestehenden SL-Zuweisen-/Umlegen-Wege um. Zwischen Angebot und Annahme
wird der Besitz noch einmal geprüft (Gegenstand kann zwischenzeitlich
verkauft oder weggeworfen worden sein).

**UI:** „Weitergeben“-Knopf neben „Wegwerfen“ in der Gegenstands-Kachel,
Empfänger-Auswahl als Commlink-Popup (`WeitergebenPopup.tsx`) aus der eigenen
Party. Nur in der Spieler-Ansicht (`Fachfenster` in `SpielerAnsicht.tsx`),
nicht in der SL-Inventarverwaltung. Fremde Fächer (`FREMD`) ohne den Knopf.

**Verifiziert:** `tsc -b` sauber, Backend-Import ok, Zugriffsschutz-Whitelist
um die Spieler-Route ergänzt. **Kein Browser-Klicktest** — siehe CLAUDE.md
„Offen: Was Mark selbst testen muss“.

API: [[../../api/verhandlung.md]]. Live-Zustellung über denselben Kanal wie
SL-Mitteilungen (`_typ: "verhandlung"`), siehe [[mitteilungen-system]].

## Noch nicht gebaut (Ideen vom 26.09.2026)

Alles unten steht in `ideen für später.txt` und CLAUDE.md „Geplante Features“.
**Datenmodell nicht durchgesprochen** — vor dem Bauen die offenen Achsen
klären, nicht stillschweigend entscheiden.

### Geld-Weitergabe (Party / gleicher Ort)

Gleicher Annehmen/Ablehnen-Mechanismus wie bei Gegenständen. Kapital hängt an
`Person.kapital` (NuYen), nicht an einem Gegenstand — siehe
[[../concepts/waehrung-und-preise]]. Technisch naheliegend: neue
Verhandlungsart (z. B. `GELD_WEITERGABE`) statt das Gegenstands-Angebot zu
verbiegen.

### NPC → Spieler-Belohnung (SL)

SL soll Geld von NPCs direkt an Spieler als Belohnung buchen können. Ob der
Spieler das ablehnen darf, ist **offen** (ein SL-Befehl ohne Popup wäre der
naheliegende Kontrast zur Spieler-zu-Spieler-Zustimmung — nicht entschieden).

### Credstick (neuer Gegenstandstyp)

Digitaler Geldträger: Geld drauf-/runterladen das man besitzt; Credstick
weitergeben oder finden — wer ihn hat, hat Zugriff auf das geladene Geld.
**Offen:** nur Tresor (erst aufs eigene Kapital runterladen, dann ausgeben)
oder direkt im Shop vom Stick zahlen? Ändert das Datenmodell.

Liegt **nicht** in `GEGENSTAND_TYPEN` (`items/schemas.py` /
`frontend/src/items/typKatalog.ts`). Typ nach dem Anlegen fix — neuer Eintrag
muss an beiden Katalogen plus KI-Generator.

### Heiltrank

Verbrauchsgegenstand, der beim Einsatz **automatisch heilt**. **Offen:**
eigener Typ `Heiltrank` (klare Felder, z. B. Heilmenge) oder Eigenschaft auf
dem bestehenden Typ `Verbrauchsgegenstand`? Projektregel: keine allgemeinen
Felder für Sonderfälle — eigener Typ wäre die naheliegende Lesart, nicht
entschieden.

### Granate / Alchemisten-Wurftrank

Gegenstück zum Heiltrank: Schaden oder Effekte, **ohne volle eigene Mechanik**
(erzählerisch / durch die SL). Darf nicht still verpuffen — Einsatz muss
sichtbar sein (z. B. Schaden berechnen und anzeigen). **Offen:** reicht eine
Mitteilung/Popup an SL+Ziel, oder soll es in die Kampfkarte einschlagen?

## Entwicklung

- **18.09.2026** — Party-Feature bewusst ohne Inventar-Tausch gebaut
  („aktuell nur SL darf Besitzer wechseln“), siehe [[party-feature]] „Offen“.
- **26.09.2026** — Mark notiert: Gegenstände innerhalb der Party **und** an
  Leute am gleichen Ort, Popup Annehmen/Ablehnen. Kurz darauf Geld ebenso,
  NPC-Belohnung, Credstick, Heiltrank, Granate.
- **26.09.2026, `50321a6`** — Party-interne Gegenstands-Weitergabe gebaut.
  „Gleicher Ort“, Geld, neue Typen: nicht begonnen.

## Siehe auch

- [[party-feature]] — Mitgliedschaft als Reichweiten-Kriterium
- [[../concepts/waehrung-und-preise]] — NuYen, `kapital`, Shop
- [[mitteilungen-system]] — Live-Kanal, den Verhandlungen mitbenutzen
- [[neo4j-datenmodell]] — `BESITZT`, `MITGLIED_VON`
- [[../../api/verhandlung.md]] — Endpunkte
- [[../../../CLAUDE.md]] — „Zuletzt gebaut“ / „Geplante Features“
