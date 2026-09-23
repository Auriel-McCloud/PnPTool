# Shop-System: Händler, Sortiment, Kauf

Kern-Baustein (22.09.2026) von "Shop-System + Händler-Spam"
(`CLAUDE.md`, Punkt 1). Spam/Werbung/Scammer/I.C.E.-Skalierung sind bewusst
zurückgestellt — dieser Teil deckt nur Händler-NPC, Sortiment und Kaufen.
Code: `backend/app/haendler/`.

## Konzept

**Ein Händler ist keine eigene Entität.** Er ist ein `Person`-Knoten mit
`istHaendler=true` — dasselbe Muster wie `istKI`/`istCritter`
(`app/entities/schemas.py`). Anlegen und Bearbeiten (Name, Bild,
Beschreibung, Spezialisierung) läuft über die bestehenden `/personen`-Routen,
nicht über dieses Modul.

**Bewusst schlank: kein Charakterblatt.** Marks Entscheidung im Erstgespräch
— anders als KI/Critter braucht ein Händler keine Attribute/Fertigkeiten,
nur Name/Bild/Beschreibung + Sortiment. Lässt sich später nachziehen, falls
z.B. Verhandeln-Proben gegen den Händler gewürfelt werden sollen.

**Zwei bestehende Systeme werden mitgenutzt, kein neuer Code nötig:**
- **Standort** (der Laden) — dieselbe `BEFINDET_SICH_AN`-Kante wie bei Party
  (`app/party/repository.py`), diesmal von `Person` statt `Party` zu `Ort`.
- **Kontakt/Messenger** ("Kontakt austauschen") — das bestehende
  `KENNT`-System (`docs/api/kontakte.md`). Ein Händler ist für den Messenger
  einfach ein NPC wie jeder andere.

## Bild

Sowohl Händler-Portrait als auch Laden-Bild nutzen bestehende Infrastruktur,
keine neuen Upload-Routen:
- Händler: `POST /api/campaigns/{id}/personen/{node_id}/bild` (Bildergalerie,
  `Person.bilder`)
- Laden: `POST /api/campaigns/{id}/orte/{node_id}/bild` (`Ort.bilder`)

## Sortiment: explizit + automatisch, gemischt

Marks Vorgabe: *"es gibt einen Globalen Warenkorb aber Händler haben
durchaus individuelle Ware, oder sind vielleicht so speziell das sie nur
spezielle Sachen und keinen Standardwarenkorb haben."*

**Zwei Quellen, zusammengeführt in `GET .../sortiment`:**

1. **Explizit** — eine `VERKAUFT`-Kante vom Händler zu einem bestimmten
   `Gegenstand`, mit eigenem Preis:
   ```cypher
   (:Person {istHaendler:true})-[:VERKAUFT {preis: 1200}]->(:Gegenstand)
   ```
   Preis kann vom Grundpreis abweichen (Auf-/Abschlag: Schwarzmarkt teurer,
   Kontakt-Rabatt günstiger). SL trägt das gezielt über
   `POST .../sortiment` ein.

2. **Automatisch** — globale Vorlagen mit `automatischImShop=true`
   (Feld existiert an `Gegenstand` bereits seit September, siehe
   `items/schemas.py::GegenstandCreate`), gefiltert nach
   `Person.spezialisierung`.

**Spezialisierung löst das Brokkoli-Problem.** Mark: *"bei einem
Gemischtwarenladen sollte es schließlich keine Handfeuerwaffen geben...
wobei das wahrscheinlicher ist als das es bei einem Waffenladen Brokkoli
gibt."* `Person.spezialisierung: list[str]` — leer heißt Gemischtwarenladen
(zeigt alle passenden automatischen Vorlagen), gesetzt (z.B. `["Waffe"]`)
beschränkt den **automatischen** Teil auf diese Gegenstandstypen. Explizit
eingetragene Ware ist davon unabhängig immer sichtbar — ein Waffenladen kann
über die explizite Route trotzdem eine besondere Ration Feldrationen führen,
wenn der SL das so will.

Eine Vorlage, die zufällig sowohl automatisch passend als auch explizit
eingetragen ist, erscheint nur einmal — mit dem expliziten (Sonder-)Preis.

## Bestand: aus bestehenden Feldern abgeleitet, kein neues Konzept

Mark: *"wir haben bei Gegenständen schon definiert ob sie einzigartig sind
oder eine Vorlage, Vorlagen gibt es unendlich, einzigartige Gegenstände gibt
es nur ein Mal."* Genau diese Unterscheidung trägt den Bestand:

| Ware ist... | Verhalten beim Kauf |
|---|---|
| eine **Vorlage** (`istVorlage=true`) | unendlich verfügbar — jeder Kauf erzeugt eine unabhängige Kopie (`items/repository.py::assign_copy`, dasselbe wie beim bestehenden `POST .../gegenstaende/{id}/zuweisen`). Bleibt danach weiter im Sortiment. |
| ein **einzigartiges Stück**, das dem Händler gehört | genau einmal kaufbar — Besitzerwechsel vom Händler zum Käufer (`items/repository.py::transfer_owner`), die `VERKAUFT`-Kante wird gelöscht. Verschwindet danach aus dem Sortiment; ein zweiter Kaufversuch liefert `404`. |

Kein `bestand`-Feld, keine Stückzahl-Logik — die Invariante steckt bereits
in `einzigartig`/`istVorlage`.

## Kauf-Flow

**Bestätigung passiert im Frontend** (Commlink-Popup, Marks Vorgabe für
destruktive/geldwirksame Aktionen — "bist du sicher"). Der Server prüft
Guthaben zusätzlich **serverseitig noch einmal**: ein Popup ist UX, kein
Sicherheitsmechanismus.

```
POST /api/campaigns/{campaign_id}/haendler/{haendler_id}/kaufen
{ "gegenstandId": "...", "kaeuferPersonId": "..." }  // kaeuferPersonId nur von der SL beachtet
```

- **Spieler kaufen nur für sich selbst** — `kaeuferPersonId` im Body wird
  ignoriert, der eigene Charakter aus der Sitzung gilt (dasselbe Muster wie
  beim Messenger: niemand kann sich als fremder Charakter ausgeben).
- **Die SL kann für jeden PC kaufen** — z.B. wenn ein NPC im Spiel spontan
  etwas verkauft/schenkt.
- Guthaben (`Person.kapital`) reicht nicht → `409 Conflict`:
  `"Guthaben reicht nicht — {kapital}¥ verfügbar, {preis}¥ nötig"`
- Erfolgreich → `200` mit dem übergebenen Gegenstand und dem neuen Kapital.

**Schreibroute, die auch Spieler nutzen dürfen** — steht in der Allowlist
`tests/test_zugriffsschutz.py::OHNE_GM_ERLAUBT`, geprüft ist die
Käufer-Identität serverseitig in der Route selbst, nicht über
`require_campaign_gm`.

## Endpunkte

Basis: `/api/campaigns/{campaign_id}/haendler`

| Methode | Pfad | Wer | Zweck |
|---|---|---|---|
| GET | `` | alle mit Zugang | Alle Händler dieser Kampagne (Kachel/Kontaktliste) |
| GET | `/{id}` | alle mit Zugang | Ein Händler |
| PUT | `/{id}/standort` | nur SL | Laden-Ort setzen/lösen |
| GET | `/{id}/sortiment` | alle mit Zugang | Was dieser Händler verkauft |
| POST | `/{id}/sortiment` | nur SL | Ware explizit eintragen (optional Sonderpreis) |
| DELETE | `/{id}/sortiment/{gegenstandId}` | nur SL | Explizite Ware wieder entfernen (wirkt nicht auf automatische) |
| POST | `/{id}/kaufen` | SL + Spieler (eigener Charakter) | Kauf durchführen |

Anlegen/Bearbeiten des Händlers selbst: `POST`/`PATCH .../personen` mit
`istHaendler: true` (siehe `docs/api/personen.md`).

## Verifiziert (22.09.2026)

Backend end-to-end gegen echte Neo4j-DB durchgespielt (nicht nur
Unit-Tests): Spezialisierungs-Filter (Waffe erscheint im Waffenladen,
Brokkoli nicht), Kauf einer Vorlage (Kapital korrekt abgezogen, Vorlage
bleibt im Sortiment, unabhängige Kopie landet im Inventar des Käufers), Kauf
eines Unikats zu explizitem Sonderpreis (verschwindet danach aus dem
Sortiment, zweiter Kaufversuch korrekt `404`), Standort-Zuweisung, `409` bei
zu wenig Guthaben mit der erwarteten Meldung. `pytest` komplett grün.

## Noch offen

- **Frontend** — SL-Sortiment-Editor, Spieler-Kaufansicht (Commlink-Popup),
  Standort-Zuweisung-Popup, KI-Sortiment-Vorschlag-Popup (siehe unten).
  Kompletter Kern-Endpunktsatz steht, nichts davon ist im Frontend
  angebunden.
- **Spam/Werbung** — Händler schickt Nur-Lesen-Nachrichten, Frequenz
  skaliert mit I.C.E., Popups an zufälliger Screen-Position, SL kann eine
  "Spam-Welle" auslösen, Kampagnen-Option zum Ein/Ausschalten.
- **Scammer-Storylines** — manche Spam-NPCs sind SL-Story-Hooks.
- Hängt mit dran: Rüstungs-Reparatur-Händlerpreis
  (`docs/api/ruestung.md`), Fahrzeug/Drohnen-Preisfrage
  (`docs/wiki/concepts/drohnen-fahrzeuge.md`) könnten über denselben
  Sortiments-Mechanismus laufen, sobald das Frontend steht.

## KI-Sortiment-Vorschlag (23.09.2026)

Neues Modul `backend/app/haendler/ki_vorschlag.py`, baut auf dem
KI-Gegenstandsgenerator der Ideenschmiede auf (`docs/api/ki.md`,
`GEGENSTAND_TYPEN` aus `items/schemas.py`). Schlägt passende Sortiment-Waren
für einen bestimmten Händler vor, basierend auf Name/Beschreibung/
Spezialisierung.

**Bevorzugt Wiederverwendung:** die KI bekommt eine Liste aller bereits
freigegebenen (`istEntwurf=false`) Gegenstands-Vorlagen der Kampagne, die
noch NICHT im Sortiment dieses Händlers stehen, und soll zuerst daraus
wählen (Namensabgleich über die echte ID, nicht per KI-Text — dieselbe
Regel wie bei der Auto-Verknüpfung, Tippfehler dürfen keine falsche
Zuordnung erzeugen). Nur bei einer echten Lücke erfindet sie etwas Neues.

**Zweistufig, wie `auto_verknuepfung.py`:**

| Methode | Pfad | Wer | Zweck |
|---|---|---|---|
| GET | `/{haendler_id}/ki-vorschlaege?anzahl=5` | nur SL | Vorschauliste, nichts wird gespeichert |
| POST | `/{haendler_id}/ki-vorschlaege/anwenden` | nur SL | Übernimmt EINEN bestätigten Vorschlag |

Eine neu erfundene Ware landet beim Anwenden zuerst als
Ideenschmiede-Entwurf (`istEntwurf=true`), bevor sie ins Sortiment kommt —
kein Autocommit. Bewusst pro Vorschlag einzeln anzuwenden, kein
Sammel-Übernehmen (SL prüft jede neue Ware). `GET .../ki-vorschlaege` steht
in `NUR_SPIELLEITUNG_LESBAR` (`tests/test_zugriffsschutz.py`) — Vorschläge
sind SL-Entscheidungsgrundlage, kein Spieler-Angebot.

Backend end-to-end gegen echte Neo4j-DB verifiziert (Wiederverwendung UND
Neuerfindung beide getestet, Testdaten danach entfernt). **Frontend noch
offen** — SL-Popup mit Vorschlagsliste + Einzeln-Übernehmen-Knöpfen.
