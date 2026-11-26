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
Figuren“). Offen: gilt der Schalter auch für die SL, und was steht in den
beiden Menüs.

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
