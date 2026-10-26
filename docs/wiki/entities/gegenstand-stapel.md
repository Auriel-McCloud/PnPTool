---
title: Gegenstand-Stapel (Zusammenlegen)
created: 2026-10-26
updated: 2026-10-26
type: entität
tags: [inventar, gegenstände, geplant-erweiterbar]
sources: [../../../CLAUDE.md, ../../../backend/app/items/repository.py, ../../../backend/app/items/routes.py]
status: umgesetzt
---

# Gegenstand-Stapel (Zusammenlegen)

Mark probierte erstmals Gegenstände mit Mengenangabe (`hatMenge`/`menge`,
schon länger im Datenmodell für Munition/Reparaturmaterial/Maschinenteile)
und bekam dabei 3 einzelne Maschinenteile-Instanzen statt eines Stapels mit
Anzahl 3 — jede Übergabe/jeder Fund legte ein eigenes Stück an, nichts fasste
gleichwertige Stücke automatisch zusammen. Anfrage 26.10.2026: ein generelles
"mehrere gleiche Gegenstände zusammenlegen"-Feature, wiederverwendbar für
jeden stapelbaren Gegenstandstyp, nicht nur Maschinenteile.

## Datenmodell

Kein neues Feld — nutzt die bestehenden `hatMenge: bool` / `menge: int` am
Gegenstand (`items/schemas.py`). Neu ist nur die **Zusammenlegen-Operation**
selbst, kein neuer Knoten/keine neue Kante.

## Gleichheits-Check: `items/repository.py::stapel_gleich`

Zwei Gegenstände gelten als derselbe Stapel-Art, wenn sie in **allen**
Feldern übereinstimmen außer einer festen Ausnahmeliste aus Instanz-eigenen
Feldern (`_NICHT_STAPEL_RELEVANT`): `id`, `description`, `notes`, `menge`,
`hatMenge`, `bildUrl`, `sichtbarkeit`/`sichtbarFuer`, `ablage` samt Ziel,
`weggeworfen`/`weggeworfenVon`, `entfernungBeantragt`, `istEntwurf`,
`istVorlage`, `automatischImShop`. Alles andere — Preis, Gewicht, Typ,
`maschinenteilQualitaet`, `istReparaturmaterial`, Waffenwerte, Trait-Boni,
... — muss exakt gleich sein. Dasselbe Prinzip wie `_NICHT_KOPIEREN` beim
Vorlagen-Kopieren, nur für einen Gleichheits- statt einen Kopier-Zweck.

Einzigartige Stücke (`einzigartig: true`) werden nie verglichen — sie sind
per Definition kein Stapel-Kandidat und müssen von den Aufrufern vorher
ausgeschlossen werden.

## Operation: `items/repository.py::zusammenlegen`

`POST /api/campaigns/{cid}/gegenstaende/{item_id}/zusammenlegen` mit
`{quellItemIds: string[]}`. `item_id` ist das Ziel:

1. Ziel und jede Quelle dürfen nicht `einzigartig` sein, sonst `NichtStapelbar`.
2. Jede Quelle muss demselben Besitzer gehören wie das Ziel, sonst
   `NichtStapelbar`.
3. Jede Quelle muss `stapel_gleich` zum Ziel sein, sonst
   `UnterschiedlicherGegenstand`.
4. Ziel bekommt `hatMenge=true` und die Summe der effektiven Mengen (ein
   Stück ohne `hatMenge` zählt als 1).
5. Jede Quelle wird **weggeworfen** (`repository.wegwerfen`) — landet im
   Mülleimer der Spielleitung, wird nicht gelöscht. Reversibel, falls sich
   die Auswahl im Nachhinein als falsch herausstellt (Marks Standard-Vorgabe
   für destruktive Aktionen).

Bei einem Fehler (409) bleibt alles unverändert — die Prüfung läuft komplett
durch, bevor irgendetwas geschrieben wird.

`GET .../gegenstaende/{item_id}/stapelkandidaten` liefert fürs Frontend
genau die Gegenstände, die `zusammenlegen` akzeptieren würde (gleicher
Besitzer, `stapel_gleich`, nicht einzigartig) — das Popup muss die Prüfung
nicht selbst nachbauen.

## UI

**SL und Spieler** — Mark, direkt im Anschluss an die erste Fassung: "das
müssen unbedingt auch die Spieler können". Beide Richtungen prüfen den
Besitz serverseitig selbst (kein `require_campaign_gm` auf den beiden neuen
Routen, dafür eine manuelle 404-Prüfung wie bei Wegwerfen/Ablage): ein
Spieler darf nur am eigenen Besitz zusammenlegen, die Quellen müssen
zusätzlich demselben Besitzer gehören wie das Ziel (prüft
`repository.zusammenlegen` selbst). Beide neuen Routen stehen namentlich in
`tests/test_zugriffsschutz.py::OHNE_GM_ERLAUBT`.

**GM-Seite:** Knopf „⧉ Zusammenlegen…" im Umbauen-Formular
(`GegenstandRow`, `CharacterSheetPanel.tsx`) direkt neben „Menge verfolgen"
— konzeptionelle Nähe statt Implementierungsreihenfolge (Mark-Konvention).
Nur sichtbar, wenn der Gegenstand einen Besitzer hat und nicht einzigartig
ist.

**Spieler-Seite:** Knopf „⧉ Zusammenlegen" in der Fußzeile der normalen
`GegenstandKachel.tsx` (wo auch Weitergeben/Wegwerfen sitzen) — erscheint
nur, wenn `onUmlegen` gesetzt ist (das zuverlässigste "das ist mein
eigener Gegenstand"-Signal, da Wegwerfen in der Spieleransicht aktuell gar
nicht verdrahtet ist) UND `campaignId` übergeben wurde UND das Stück nicht
einzigartig ist. Gewired an drei Stellen in `SpielerAnsicht.tsx`: die
beiden direkten Kachel-Raster ("Am Körper", "Fahrzeuge und Drohnen") sowie
`Fachfenster.tsx` (Mitgeführt/Gelagert-Popups, dort nicht im `FREMD`-Fach).

Beide Seiten nutzen dasselbe `ZusammenlegenPopup.tsx` (`frontend/src/items/`):
lädt Kandidaten beim Öffnen, Mehrfachauswahl per Checkbox (gleiches
Grundmuster wie `VorlagenAuswahlPopup.tsx`: Klick toggelt, ein Knopf schickt
die ganze Auswahl auf einmal ab), zeigt die neue Gesamtmenge vorab an. Text
sagt ausdrücklich "gelöscht wird nichts" (wiederverwendet `wegwerfen.css`).
Das Popup selbst kennt keine Rolle — es ruft dieselbe API, egal ob SL oder
Spieler es öffnen; die Berechtigung entscheidet ausschließlich das Backend.

## Verifiziert

- `backend/tests/test_items_zusammenlegen.py`: `stapel_gleich` pur (4 Fälle:
  identisch trotz unterschiedlicher Menge/Notiz, unterschiedliche Qualität,
  unterschiedlicher Preis, Ablage/Bild irrelevant) + 5 Integrationstests
  gegen die Dev-Neo4j (Summieren, Wegwerfen der Quellen, Ablehnung bei
  unterschiedlicher Qualität/einzigartig/fremdem Besitzer,
  Stapelkandidaten-Filterung).
- `tsc -b` sauber.
- **Kein Browser-Klicktest** — Mark wollte zunächst nur das generelle
  Feature, nicht die 3 konkreten Maschinenteile seiner laufenden Kampagne
  live anfassen. Steht am Spieltisch noch aus.

## Offene Fragen

- **UI-Platzierung/Optik nach Praxistest:** wie bei jedem neuen Feature
  entscheidet Mark Details (z.B. ob der Knopf eher im Besitz-Reiter als im
  Umbauen-Formular sitzen sollte) erst nach dem ersten echten Einsatz am
  Spieltisch, nicht vorab.

## Nachträge

**26.10.2026, Button unsichtbar:** erste Fassung gated den Zusammenlegen-
Knopf auf `!item.einzigartig` — da `einzigartig` der Pydantic-Default für
JEDEN neu angelegten Gegenstand ist (`GegenstandCreate.einzigartig: bool =
True`), verschwand der Knopf dadurch praktisch überall, auch an Mark bisher
komplett unberührten Items. Fix: Sichtbarkeit nicht mehr aufs Feld gaten,
das Popup erklärt den Einzigartig-Fall stattdessen klar, wenn er wirklich
zutrifft (`stapelkandidaten` liefert für einzigartige Ziele ohnehin `[]`).

**26.10.2026, kein Weg das Häkchen rauszunehmen:** Mark fand zwar zwei
Checkboxen mit "Einzigartig" im Label im Umbauen-Formular, aber beide sind
an `istVorlage` gekoppelt (`vorlagenArtSetzen`) und können `einzigartig`
nie auf `false` setzen — einer der beiden Pfade erzwingt es sogar explizit
auf `true`. Es gab schlicht keine UI, die das eigentliche Lore-Feld direkt
umschaltet, obwohl Schema/Autosave es längst unterstützen. Neuer,
eigenständiger Checkbox direkt vor "Menge verfolgen" im selben Formular,
unabhängig von den beiden Vorlagen-Art-Optionen.

## Siehe auch

- [[gegenstand-transfer]] — anderer Gegenstands-Mutations-Pfad (Weitergabe
  zwischen Spielern), ähnliches Rückfrage-Prinzip
- `../../../CLAUDE.md` — „Offen: Was Mark selbst testen muss“
