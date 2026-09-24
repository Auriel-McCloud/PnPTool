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
| PUT | `/{id}/sortiment/{gegenstandId}/rabatt` | nur SL | Sonderangebot setzen (`prozent`, `hinweis`), `prozent=0` nimmt es weg |
| POST | `/{id}/kaufen` | SL + Spieler (eigener Charakter) | Kauf durchführen — bei `vertriebsart=DIGITAL` entsteht eine Bestellung statt sofortiger Übergabe |
| GET | `/bestellungen/offen` | nur SL | Alle offenen Online-Bestellungen der Kampagne |
| GET | `/bestellungen/eigene` | alle mit Zugang | Eigene Bestellungen (Spieler-Sicht) |
| POST | `/bestellungen/{id}/liefern` | nur SL | Lieferung freigeben — übergibt die Ware jetzt tatsächlich |

Anlegen/Bearbeiten des Händlers selbst: `POST`/`PATCH .../personen` mit
`istHaendler: true`, `vertriebsart: "PHYSISCH"|"DIGITAL"`,
`shopHintergrundUrl: str` (siehe `docs/api/personen.md`).

## Vertriebsart, Sonderangebote, Online-Bestellungen (24.09.2026)

Marks Konzept: Shop-Optik/-Mechanik hängt komplett an
`Person.vertriebsart`:

- **PHYSISCH** (Standard): "Fancy"-Optik im Frontend (Hintergrundbild,
  Händlerporträt), Verhandeln möglich (siehe unten), Ware sofort im
  Inventar des Käufers.
- **DIGITAL**: schlichte Online-Shop-Optik, **kein Verhandeln**, Kauf
  zieht das Kapital sofort ab, legt aber nur eine `Bestellung` an — die
  Ware wird erst übergeben, wenn die SL `POST .../bestellungen/{id}/liefern`
  aufruft. Kein fester Liefertermin, bewusst nur ein Knopf ("jetzt
  liefern", Marks Vorgabe: SL entscheidet spontan, wann es ankommt).

**Sonderangebote** sitzen auf der `VERKAUFT`-Kante (`rabattProzent: int`,
`rabattHinweis: str`) — nur bei explizit eingetragener Ware möglich, nicht
bei automatischen Katalog-Einträgen (die haben keine eigene Kante). Der
tatsächliche Kaufpreis wird serverseitig aus `preis` und `rabattProzent`
berechnet (`repository.py::effektiver_preis`); der Client bekommt beide
Werte, um den Grundpreis durchgestrichen neben dem Angebotspreis zu zeigen.

**Bestellung** (`Bestellung`-Knoten, nicht an `Gegenstand`/`Person`
gebunden außer über Felder) trägt Status `OFFEN`→`GELIEFERT`. Bei einer
Vorlage bleibt das Sortiment beim Bestellen unverändert (unendlich
verfügbar); bei einem Unikat verschwindet die Ware sofort aus dem
Sortiment (ist ja verkauft), nur die physische Übergabe wartet auf die
Lieferung. Eine zweite Lieferung auf dieselbe Bestellung liefert `409`.

`shopHintergrundUrl` ist ein einfaches String-Feld an `Person` — kein
eigener Upload-Endpunkt, wird wie andere Bild-URLs gesetzt.

## Verifiziert (22.09.2026)

Backend end-to-end gegen echte Neo4j-DB durchgespielt (nicht nur
Unit-Tests): Spezialisierungs-Filter (Waffe erscheint im Waffenladen,
Brokkoli nicht), Kauf einer Vorlage (Kapital korrekt abgezogen, Vorlage
bleibt im Sortiment, unabhängige Kopie landet im Inventar des Käufers), Kauf
eines Unikats zu explizitem Sonderpreis (verschwindet danach aus dem
Sortiment, zweiter Kaufversuch korrekt `404`), Standort-Zuweisung, `409` bei
zu wenig Guthaben mit der erwarteten Meldung. `pytest` komplett grün.

## Verifiziert (24.09.2026 — Vertriebsart/Rabatt/Bestellungen/Verhandeln)

Echtes E2E-Skript gegen laufendes Backend (eigener Testserver) + echte
Neo4j: Rabatt setzen/entfernen inkl. korrekter Preisberechnung, digitaler
Kauf (Kapital sofort weg, Ware NICHT im Inventar vor Lieferung, danach
schon), doppelte Lieferung korrekt mit `409` abgelehnt, Verhandeln
`SHOP_KAUF` von Angebot bis angenommenem Kauf komplett durchgespielt. Alle
Schritte grün, Testdaten danach entfernt. **Frontend** (`frontend/src/haendler/`)
nur `tsc -b` geprüft, kein Browser-Klicktest (siehe CLAUDE.md "Offen").

## Noch offen

- **Frontend** — SL-Sortiment-Editor (Sortiment eintragen/entfernen/Rabatt
  setzen ist im Backend fertig, aber kein Bearbeiten-Popup), Standort-
  Zuweisung-Popup, KI-Sortiment-Vorschlag-Popup. Kauf-Flow, Bestellungen-
  Ansicht und KI-Alltagsgegenstand-Erzeugung sind seit 24.09.2026 im
  Frontend angebunden (nur `tsc -b`, kein Browser-Klicktest).
- **Spam/Werbung** — Händler schickt Nur-Lesen-Nachrichten, Frequenz
  skaliert mit I.C.E., Popups an zufälliger Screen-Position, SL kann eine
  "Spam-Welle" auslösen, Kampagnen-Option zum Ein/Ausschalten.
- **Scammer-Storylines** — manche Spam-NPCs sind SL-Story-Hooks.
- Hängt mit dran: Rüstungs-Reparatur-Händlerpreis
  (`docs/api/ruestung.md`), Fahrzeug/Drohnen-Preisfrage
  (`docs/wiki/concepts/drohnen-fahrzeuge.md`) könnten über denselben
  Sortiments-Mechanismus laufen, sobald das Frontend steht.

## Verhandeln (Spezifikation 23.09.2026, Backend gebaut 24.09.2026)

Marks Wunsch: wenn ein Spieler beim Händler (oder bei der Rüstungsreparatur,
siehe `docs/api/ruestung.md`) Geld ausgeben soll, will er die Möglichkeit
haben zu verhandeln, statt den Preis stumm zu akzeptieren. **Gilt überall,
wo ein Spieler im Spiel Geld für etwas ausgibt** — außer Charaktererstellung
(Startausrüstung) und DIGITAL/online gekaufter Ware (kein Verhandeln, so
entschieden und gebaut 24.09.2026). Shop-Frontend und Reparatur-Frontend
sind gebaut; Browser-Klicktest offen.

**Auslöser:** ein "Verhandeln"-Knopf direkt bei jedem einzelnen Posten (pro
Gegenstand im Sortiment, bzw. pro Reparaturposten) — kein pauschaler Knopf
für den ganzen Warenkorb. Klick sendet eine Verhandlungsanfrage an die SL.

**Kein Würfelwurf.** Es existiert aktuell kein generisches Proben-System im
Tool (keine Attribut+Fertigkeit-gegen-Schwierigkeit-Mechanik). Verhandeln
läuft rein am Tisch/Rollenspiel ab — der Spieler klickt, die SL entscheidet
nach Bauchgefühl. Keine Würfel-Anbindung vorgesehen.

**SL-Popup zeigt:**
- Was der Spieler kaufen/reparieren will (Name, Menge) + aktueller Preis
- Händler-Persönlichkeit — das **bestehende `notizen`-Feld** der `Person`
  (SL-only, existiert schon, siehe `docs/api/personen.md`), einfach mit
  angezeigt. Kein neues strukturiertes Feld.
- **Neues Feld** `Person.moeglicheSidequests: str` (SL-only, nur bei
  `istHaendler=true` relevant) — freier Text, reine Gedächtnisstütze für die
  SL ("könnte contra Ware auch etwas brauchen/wollen"). Bewusst **kein**
  Quest-Datenmodell (Status/Belohnung/Verknüpfung) — das ist ein eigenes,
  größeres Thema und wird hier nur vorgemerkt, nicht gebaut.
- Rabatt-Schnellauswahl 5% / 10% / 15% + Freitextfeld für einen individuellen
  Preis
- SL bestätigt (oder lehnt ab/ignoriert → Normalpreis bleibt)

**Gültigkeit:** der gewährte Preis gilt **nur für diesen einen Kauf gerade**,
nicht dauerhaft. Kein Sonderpreis-Gedächtnis pro Spieler/Händler — beim
nächsten Besuch wieder Normalpreis, es sei denn die SL trägt separat über
die bestehende explizite `VERKAUFT {preis}`-Route einen dauerhaften
Sonderpreis ein (das ist bereits vorhanden, unabhängig von diesem Feature).

**Technischer Kanal (korrigiert 23.09.2026 — Spieler→SL-Live-Push existiert
bereits, keine neue Architektur nötig):** `docs/api/mitteilungen.md` selbst
ist zwar `POST` = "Nur SL", aber `docs/api/kontakte.md` zeigt den
Rückkanal: `POST .../kontakte/{kontakt_id}/chat` dürfen **Spieler und SL**
aufrufen; schreibt ein Spieler, erzeugt das intern automatisch eine
`NACHRICHT`-Mitteilung mit `empfaengerIds = []` (= an SL), die genauso per
WebSocket gepusht wird wie eine SL-Mitteilung. Umgekehrt kann die SL gezielt
an einen einzelnen Spieler pushen (`anAlle:false, empfaengerIds:[spielerId]`).
Verhandeln braucht also **keinen neuen Mechanismus**, sondern eine neue
Mitteilungsart nach demselben Muster wie `NACHRICHT`: statt Freitext trägt
sie strukturierte Nutzlast (Gegenstand/Posten, aktueller Preis). Spieler-Klick
auf "Verhandeln" erzeugt diese Mitteilung Richtung SL (wie beim Chat, nicht
über die "Nur SL"-Route), SL bekommt ein Popup statt Chattext, antwortet mit
Rabatt-Wahl → das erzeugt eine gezielte Mitteilung zurück an genau diesen
Spieler, die den Preis im offenen Verhandeln-Popup aktualisiert. Kein
`chatOffen`-Kontakt mit dem Händler nötig — das ist ein eigener
Mitteilungstyp, kein Wiederverwenden der Chat-UI.

**Bewusst zurückgestellt:** ein echtes Quest/Auftrag-System für
"Ware gratis/50% off gegen erledigte Sidequest" — dafür braucht es eigene
Konzepte (Status, Belohnung, Verknüpfung zum Händler), die noch nicht
spezifiziert sind. `moeglicheSidequests` oben ist nur die Notiz-Vorstufe.

**Online-Käufe / DIGITAL (gebaut 24.09.2026):** kein Verhandeln, Kauf legt
eine Bestellung an, Kapital geht sofort ab, Ware erst nach SL-Liefer-Freigabe.

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

## KI-Alltagsgegenstand-Erzeugung (24.09.2026)

Marks Konzept: ein Spieler fragt einen Verkäufer im Shop nach etwas, das
nicht im Sortiment steht ("Hast du Panzerklebeband?"). Die KI schätzt
Realpreis + Typ und erzeugt einen fertigen Gegenstand — **anders als
`ki_vorschlag.py` (SL fragt aktiv nach Sortiment-Ideen) ist dieser Weg
spielergetrieben und braucht sofortige SL-Freigabe, bevor irgendetwas
entsteht.** Neues Modul `backend/app/haendler/alltagswunsch.py`, nutzt
denselben KI-Client (`app/ki/gemini.py`/`mistral.py`) wie `ki_vorschlag.py`.

**Harter Ausschluss von Waffen/Rüstung — Sicherheits-/Balance-Vorgabe, kein
Stilwunsch.** Zwei unabhängige Sperren, nicht nur ein Prompt-Hinweis:
1. Die KI bekommt nur eine Whitelist erlaubter `GEGENSTAND_TYPEN`
   (Verbrauchsgegenstand, Werkzeug, Behälter, Sonstiges — nie Waffe/Rüstung)
   und MUSS einen dieser Typen zurückgeben.
2. Zusätzlich schätzt die KI selbst ein, ob die Anfrage überhaupt eine
   Waffe/Rüstung/Kampfausrüstung meint (`istVerboten: bool` im selben
   KI-Aufruf) — ein Spieler, der "eine Panzerung fürs Handy" verlangt, soll
   nicht durch eine zu enge Typ-Liste durchrutschen, nur weil die KI dann
   hilfsweise "Sonstiges" wählt. Beide Signale zusammen ergeben
   `AUTO_ABGELEHNT`, ohne dass die SL überhaupt gefragt wird.

**Ablauf:**
```
POST /{haendler_id}/alltagswunsch { "text": "Hast du Panzerklebeband?" }
```
- KI antwortet sofort mit Name/Beschreibung/Preis/Typ (oder lehnt automatisch
  ab, siehe oben) — der Spieler muss nicht warten, kann weiterspielen.
- Ist der Vorschlag zulässig (`status=OFFEN`), geht er **sofort als Popup an
  die SL** über denselben Live-Kanal wie Verhandlungen (`_typ:
  "alltagswunsch"` im Mitteilungs-Umschlag, siehe `verhandlung/routes.py`
  als Vorbild). Die SL kann Name/Beschreibung/Preis vor der Freigabe
  überschreiben, oder mit optionalem Grund ablehnen.
- Bei Annahme entsteht der Gegenstand sofort (als Vorlage,
  `istEntwurf=false` — kein Ideenschmiede-Umweg nötig, das ist ein
  einzelner Alltagsgegenstand, keine Sortiment-Strategie) und landet direkt
  im Sortiment des fragenden Händlers zum vereinbarten Preis. Der normale
  Kauf-Flow (`POST .../kaufen`) greift danach unverändert.
- Der Spieler bekommt die Entscheidung als eigenes Ergebnis-Popup, sobald
  die SL fertig ist — kein Polling, kein Chat-Text.

| Methode | Pfad | Wer | Zweck |
|---|---|---|---|
| POST | `/{haendler_id}/alltagswunsch` | Spieler (eigener Charakter) | Wunsch stellen, KI antwortet sofort |
| GET | `/alltagswuensche/offen` | nur SL | Aufhol-Liste offener Freigaben |
| GET | `/alltagswuensche/eigene` | Spieler | Eigene Wünsche, alle Status |
| POST | `/alltagswuensche/{id}/antwort` | nur SL | Annehmen (mit optionaler Überschreibung) oder ablehnen |

**Verifiziert (24.09.2026):** echtes E2E-Skript gegen laufendes Backend +
echte Neo4j + echten KI-Provider: harmloser Wunsch (Panzerklebeband) korrekt
mit Preis/Typ vorgeschlagen, SL-Freigabe erzeugt Gegenstand im Sortiment,
danach normal käuflich; eindeutige Waffenanfrage ("Pistole oder
Kampfmesser") korrekt `AUTO_ABGELEHNT`, taucht nicht in der SL-Liste auf,
kein Gegenstand entsteht. **Frontend fertig, nur `tsc -b` geprüft, kein
Browser-Klicktest** (SL-Popup `AlltagswunschFreigabePopup.tsx`,
Spieler-Eingabe direkt in `ShopSeite.tsx`, Ergebnis-Popup
`AlltagswunschErgebnisPopup.tsx`).
