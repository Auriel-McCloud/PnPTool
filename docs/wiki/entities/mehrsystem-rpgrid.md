---
title: Mehrsystem-Kern (RPGrid) — NeotopiA und GridMonster umschalten
created: 2026-11-26
updated: 2026-11-26
type: entität
tags: [regelsystem-kampagne-ideenschmiede, datenmodell, gridmonster]
sources: [Gespräch 2026-11-26]
status: teilweise-umgesetzt
---

# Mehrsystem-Kern (RPGrid)

**Mark (26.11.2026):** „Wollen wir das Grundgerüst für den RPGrid bauen, so
dass wir ein wenig an GridMonster basteln können? Und zwischen NeotopiA und
GridMonster umschalten können?“

RPGrid = Arbeitsname der Plattform („Role Play Grid“, alle Systeme darin),
siehe Marks persönliches Wiki `entities/pnptool.md`. GridMonster-Regelstand
(Attribute, Fertigkeiten, Stufen/Würfel, Partnerschaft) steht in Marks
persönlichem Wiki `concepts/gridmonster.md` — dort nachlesen, nicht hierher
kopieren.

## Befund im Code (26.11.2026)

- Backend hat die Ebene schon: `(:Campaign)-[:NUTZT_REGELSYSTEM]->(:Regelsystem)`,
  CRUD unter `/api/regelsysteme`, `seed_neotopia()` beim Start
  (siehe [[architektur-drei-ebenen]]).
- `get_campaign` liefert `ruleset` als Klein-Slug (`toLower(Name)`) →
  GridMonster würde automatisch `gridmonster`.
- `TraitDef` (Attribute/Fertigkeiten), `Erklaerung` (Regeltexte) sind schon
  nach `ruleset` getrennt → GridMonster-Katalog kann daneben liegen.
- Frontend nutzt das Regelsystem nirgends; Kampagnen anlegen ohne Systemwahl.
- Rund 50 Stellen im Backend setzen `"neotopia"` fest (Fallbacks,
  `hintergruende`, `kampf/repository.py` Rassen-Match, `wuerfel/logic.py`,
  `traits/bogen.py` …) — die müssen beim Umbau einzeln geprüft werden.

## Entschieden: Startseite mit Spiele-Kacheln (Mark, 26.11.2026)

> „Ich logge mich in den RPGrid ein, und dann sehe ich Kacheln von Spielen,
> die ich spielen kann, im Moment NeotopiA und GridMonster, und dann klicke ich
> auf das, das ich spielen möchte. … Ein SL sieht alle Spiele, ein Spieler nur
> die, in denen er mitspielt.“

- Nach dem Login kommt eine Kachel-Startseite **über** den Kampagnen: eine
  Kachel je Regelsystem (Spiel).
- SL sieht alle Spiele; Spieler nur die, in denen er einen Zugang hat.
- Datenmodell bleibt `Kampagne -NUTZT_REGELSYSTEM-> Regelsystem`; die Kacheln
  gruppieren nur.
- **Mark (26.11.2026):** Ein Spiel kann mehrere Kampagnen haben, auch unter
  derselben SL.
- **Annahme Neko:** Hat das Spiel genau eine Kampagne, führt der Klick direkt
  hinein; bei mehreren kommt die Kampagnen-Auswahl dieses Spiels. Ein Knopf
  „Spiel wechseln“ führt zurück zu den Kacheln.
- Spieler-Seite der Kacheln braucht das `Konto` über mehreren Kampagnen
  ([[konten-login-und-abo]]); heute hängt ein Spieler-Zugang an genau einer
  Kampagne und geht weiter direkt hinein.

## Entschieden: Umfang erstes Gerüst (Mark, 26.11.2026)

Kacheln + GridMonster-Kampagne anlegen + Monster & Mensch mit Attributen,
Fertigkeiten, Würfelstufen W4–W20, LP/Energie als Zahl. Partnerschaft und
zwei Charaktere je Spieler kommen im nächsten Schritt.

## Figuren in GridMonster (Mark, 26.11.2026)

> „Es gibt 2 Dinge: PC — jeder PC ist gleichzeitig ein Mensch und ein Monster —
> und NPCs. NPCs sind entweder Menschen oder Monster, aber es gibt auch
> NPC-Tamer, bei denen ein Mensch und ein Monster verknüpft werden.“

**Bestätigt (Mark, 26.11.2026):** „Ja, beides sind Figuren. Bei einem PC hat
sein Mensch und das Monster, das er spielt, auch jeweils ein eigenes Inventar.“

Mensch und Monster sind je eine eigene Figur mit eigenem Blatt. PC = die zwei Figuren eines Spielers.
NPC = eine Figur (Mensch oder Monster). Tamer-Verknüpfung Mensch↔Monster gibt
es bei PCs (über Spielergrenzen, SL-änderbar) und bei NPC-Tamern — dieselbe
Kante.

## Idee Spieler-Ansicht: Mensch-/Monster-Schalter (Mark, 26.11.2026, nicht gebaut)

> „Ich würde oben in der Menüleiste einfach einen Schalter machen, der geswitcht
> werden kann, mit einem Menschen-Symbol und einem Monster-Symbol, und daraufhin
> ändert sich das komplette Menü zum Menschen- oder Monster-Menü, was wir auch
> mit eigenen Farben anzeigen — das Monster-Menü wird ganz anders aussehen als
> das Menschen-Menü.“

Gehört zur Spieler-Seite (nächster Schritt, zusammen mit „Spieler spielt zwei
Figuren“). **Nur für Spieler, nicht für die SL (Mark, 26.11.2026).** Offen: was
steht in den beiden Menüs.

## Eigene Optik für GridMonster (Mark, 26.11.2026, gebaut als Entwurf)

> „Wir haben die Oberfläche von NeotopiA, das schaut natürlich gar nicht
> digimonig aus. Wir haben außerdem auch das Rauschen, das sollte auch nur ein
> NeotopiA-Ding sein.“

Gebaut: Spiel-Optik `frontend/src/theme/gridmonster.css` greift automatisch in
GridMonster-Kampagnen (`data-spiel` am `<html>`, siehe `docs/theming.md`).
Rauschen/Bildstörung, Röhrenflackern und Theme-Schalter nur noch in NeotopiA,
Menü-Marke „GridMonster / RPGrid“.

**Annahmen Neko (erster Entwurf, Mark entscheidet am Tisch):** Digitale Welt
statt Neon-Gasse — tiefes Himmelsblau mit leuchtendem Gitter im Hintergrund,
Orange als Aktiv-Farbe, Menschen himmelblau, Monster digitalgrün, runde Ecken
(12px), dickere weiche Ränder, runde Schrift statt Monospace, kaum
Buchstaben-Sperrung.

**3D-Gitter (Mark, 26.11.2026, gebaut):** „Ob der Grid 3D ins Endlose gehen
könnte?“ — dann: „Oder er läuft immer nur für ein paar Sekunden, wenn man in
einen anderen Menüpunkt geht.“ Gebaut als Gitterboden in Perspektive mit
Horizont-Leuchten (`gridmonster/GridBoden.tsx`), steht still und fährt bei
jedem Menüwechsel 2,6 s weich abbremsend auf den Betrachter zu.
*Annahmen Neko:* Horizont knapp über der Bildmitte, Fahrt 10 Zellen, auch beim
Betreten des Spiels; „Bewegung reduzieren“ am Gerät = keine Fahrt.

**Menüwechsel „wegfahren und einparken“ (Mark, 26.11.2026, gebaut):** „Was wir
bei GridMonster nicht brauchen, ist der Balken, der von oben durchzischt, das
war unser Ding für NeotopiA. Könnten wir es so machen, dass wir von dem
aktuellen Menü wegfahren, also dass das unten den Rand verlässt, und das neue
Menü von oben reinkommt, bei dem wir dann parken?“ Gebaut als
`CommlinkShell wechsel="fahrt"`: alte Ansicht beschleunigt unten raus
(0,34 s), neue kommt von oben und parkt mit kleinem Nachfedern ein (0,65 s),
der 3D-Boden fährt gleichzeitig mit dem Wegfahren an. NeotopiA behält den
Ladebalken. Fliegender Menüname zur Überschrift bleibt (Mark bestätigt).

**Nachschärfung (Mark, 26.11.2026):** „Das Rausfahren ist ok, aber das
Wiederreinkommen wirkt überhaupt nicht, als wäre es mit dem Hintergrund in
sync … ich hätte gern, dass es aussieht, als würde man dort ankommen.“
Umgebaut: Die neue Ansicht kommt jetzt aus der Tiefe vom Horizont
(`translateZ` unter derselben Perspektive wie der Boden) und wächst, während
der Boden ausrollt — gleiche Dauer (1,2 s) und Kurve, beide stehen im selben
Moment, kein Nachfedern mehr. Boden in zwei Teilen: anfahren (0,34 s, mit dem
Wegfahren) + ausrollen (1,2 s, mit dem Ankommen). Mark: „genial“.

**Fundstücke auf dem Gitter (Mark, 26.11.2026, gebaut):** „In Digimon gibt es
zufällige Gegenstände, die ab und zu in der Digiwelt herumstehen, wie
Telefonzellen, Kühlschränke, Disketten, CD-Player, Videorekorder, Fernseher …
vor allem Elektronikzeug. Wäre es möglich, dass wir ab und zu so einen
Gegenstand in ein Kastl vom Grid reinstellen … zufällig, nicht immer im Menü X.“
Gebaut: `gridmonster/GridDinge.tsx` (8 eigene Linienzeichnungen: Telefonzelle,
Kühlschrank, Diskette, CD-Player, Videorekorder, Röhrenfernseher,
Ghettoblaster, Computer-Monitor) stehen aufrecht in einem Gitterfeld
(`GridBoden.tsx`), bauen sich beim Auftauchen von unten nach oben auf und
fahren beim nächsten Menüwechsel mit dem Boden davon.
*Annahmen Neko:* 30 % Chance nach jedem Ankommen, in der Ruhe alle 45–120 s
eine 50-%-Chance, höchstens 2 gleichzeitig, nur die zwei vorderen Feldreihen
(weiter hinten zu klein, weiter vorn zu groß).

**Nachschärfung (Mark, 26.11.2026):** „Ich hätte gern, dass sie nicht blau
sind, sie sollen ja mehr so Störfaktoren im Bild sein, wie in der Digiwelt —
ein Wald, wo plötzlich ein Fernseher steht … oder ein Gameboy.“ Dazu
gewünscht: Kassettenrekorder, Ampel, Handheld. Umgebaut: echte Gegenstände
als flache Illustration in Materialfarben (rote Telefonzelle, Holz-Fernseher,
Beige-Computer, Chrom-Ghettoblaster …) mit dunkler Kontur und Bodenschatten,
kein Leuchten. Jetzt 11 Dinge, jedes mit eigener Größe (Telefonzelle/Ampel
groß, Diskette/Handheld klein, aber leicht übertrieben). Das Handheld ist ein
generisches Gerät ohne Logo (kein Nachbau).

## Gebaut: Grundgerüst (26.11.2026)

- Startseite `frontend/src/campaigns/SpielStart.tsx` (nur SL), Spielwahl in
  `sessionStorage` `rpgrid:spiel`, ⌂ „Spiel wechseln“ in der Kopfleiste.
- GridMonster-Kampagne: Bereiche Menschen/Monster (`gridmonster/GridFiguren.tsx`)
  plus systemneutrale Bereiche; NeotopiA-Bereiche, Achievements und
  Spieler-Vorschau ausgeblendet. Ideenschmiede ausgeblendet (KI erzeugt
  NeotopiA-Bögen).
- Backend `app/gridmonster/`: Regelsystem + `TraitDef`-Katalog geseedet; Figur =
  `Person {istMonster, personType}`, Werte per `HAS_TRAIT` (Würfelgröße, 0 =
  nicht gelernt; feste Zahlen). Wegwerfen setzt `geloescht` (Papierkorb).
- Blatt: Würfelknöpfe W4–W20 je Attribut/Fertigkeit, Zahlen mit −/+;
  Monster zeigt Angriff/Verteidigung aus der Stufe, Mensch „Karten pro Zug“
  aus dem Tamer-Level.

**Annahmen Neko (reversibel, sag wenn anders):**
- Startwerte: Attribute W4, Fertigkeiten „–“; Monster Stufe 2, LP 30, Energie 10;
  Mensch LP 10, Tamer-Level 1, Deckkapazität 10; Level 1.
- Stufen heißen im Code neutral „Stufe 1–5“ (keine Digimon-Namen im Repo).
- Menschen haben keine Mystik und noch keinen Ersatz (Neko-Vorschlag „Technik“ offen).
- Kraft hat 3 Fertigkeiten (4. offen, wie im Regel-Entwurf).

## Offene Achsen

1. ~~Umschalten~~ → entschieden, siehe oben.
2. ~~Umfang~~ → entschieden, siehe oben. War: nur Schalter (GridMonster-Kampagne, NeotopiA-
   Bereiche ausgeblendet) / + Monster & Mensch mit Attributen, Fertigkeiten,
   Würfelstufen, LP/Energie / + Partnerschaft Mensch↔Monster und Spieler mit
   zwei Charakteren.
3. ~~Monster im Datenmodell~~ → Person mit `istMonster` (gebaut). War: Person mit Flag `istMonster` (Kampf, Graph,
   Zugang, Listen spielen sofort mit; Standardweg laut Projektregel) **oder**
   eigenes Label `Monster`.

## Vorschlag Neko (nicht entschieden)

- Achse 3: Flag an `Person`. Achse 2: mittlere Stufe,
  Partnerschaft als zweiter Schritt (Graph-Idee aus Marks Wiki:
  Zugang -SPIELT-> Mensch/Monster fix, Mensch -PARTNER-> Monster SL-änderbar).
- In einer GridMonster-Kampagne ausblenden (Annahme, reversibel): Augments,
  Rassen, Zusatzfertigkeiten, Hintergründe, Begleiter, Shop.
- Würfelstufen als eigene GridMonster-Würfellogik (W4–W20, explodierend,
  höherer von Attribut-/Fertigkeitswürfel), nicht in den NeotopiA-W10-Pool
  hineinbiegen.
- IP: Stufennamen (Rookie/Champion/…) und private Digimon-Daten gehören nicht
  ins Repo (`C:\DEV\GridMonster-privat\` bleibt getrennt); im Code neutrale
  Stufen 1–5 mit Anzeigenamen als Einstellung.
