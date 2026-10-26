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

**Nur GM**, MVP-Default (wie die meisten anderen Gegenstands-Mutationen) —
ob Spieler das für den eigenen Besitz auch selbst dürfen sollen (analog zu
Wegwerfen/Ablage, die Spieler-Self-Service sind), ist **offen**, siehe
CLAUDE.md "Offen: Was Mark selbst testen muss".

Knopf „⧉ Zusammenlegen…" sitzt im Umbauen-Formular (`GegenstandRow`,
`CharacterSheetPanel.tsx`) direkt neben „Menge verfolgen" — konzeptionelle
Nähe statt Implementierungsreihenfolge (Mark-Konvention, siehe
`feature-design-workflow.md` Punkt 23 der pnptool-development-Skill-Refs).
Nur sichtbar, wenn der Gegenstand einen Besitzer hat und nicht einzigartig
ist.

`ZusammenlegenPopup.tsx` (`frontend/src/items/`): lädt Kandidaten beim
Öffnen, Mehrfachauswahl per Checkbox (gleiches Grundmuster wie
`VorlagenAuswahlPopup.tsx`: Klick toggelt, ein Knopf schickt die ganze
Auswahl auf einmal ab), zeigt die neue Gesamtmenge vorab an. Text sagt
ausdrücklich "gelöscht wird nichts" (wiederverwendet `wegwerfen.css`).

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

- **Spieler-Self-Service?** Noch nicht entschieden — siehe oben.
- **UI-Platzierung/Optik nach Praxistest:** wie bei jedem neuen Feature
  entscheidet Mark Details (z.B. ob der Knopf eher im Besitz-Reiter als im
  Umbauen-Formular sitzen sollte) erst nach dem ersten echten Einsatz am
  Spieltisch, nicht vorab.

## Siehe auch

- [[gegenstand-transfer]] — anderer Gegenstands-Mutations-Pfad (Weitergabe
  zwischen Spielern), ähnliches Rückfrage-Prinzip
- `../../../CLAUDE.md` — „Offen: Was Mark selbst testen muss“
