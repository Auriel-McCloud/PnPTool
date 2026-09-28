---
title: Zusatzfertigkeiten
created: 2026-09-28
updated: 2026-09-28
type: entität
tags: [charaktererstellung, fertigkeiten, ki, campaign-gebunden, gebaut]
sources: [../../../CLAUDE.md, ../../api/zusatzfertigkeiten.md, ../../../backend/app/zusatzfertigkeiten/, ../../reference/Master/Optionale_Fertigkeiten.md]
status: teilweise-umgesetzt
---

# Zusatzfertigkeiten

Campaign-gebundener Katalog optionaler Fertigkeiten (Sprengstoffe, Esoterik,
Gesetzeskunde, Kosmologie, Rätsel — siehe
`docs/reference/Master/Optionale_Fertigkeiten.md`). Bis 28.09.2026 nur ein
Konzept-Dokument, weder im Trait-Katalog (`backend/app/traits/seed.py`) noch
in irgendeiner UI. Charaktererstellung und EP-Verteilung/LevelUp kannten
diese Fertigkeiten nicht.

## Gebaut (28.09.2026)

**Kein globaler Fixkatalog und kein Freigabe-Schalter wie bei Rassen**
(Marks Vorgabe, wörtlich: "im Kampagnen Menü eine einfache Tabelle machen
in der man Skills eintragen kann, nach dem diese ja grundsätzlich keine
Mechanik mit sich bringen müsste man nur einen Namen eine Kurz und Detail
Beschreibung hinzufügen können"). Jeder Katalogeintrag hängt direkt an einer
Kampagne (`Zusatzfertigkeit.campaignId`, wie die meisten anderen Entitäten)
und ist sofort für Spieler dieser Kampagne wählbar — kein zweiter
Freigabe-Schritt wie `(:Campaign)-[:ERLAUBT_RASSE]->(:Rasse)`.

**Keine eigene Mechanik.** Reiner Name + Kurz-/Detailbeschreibung, wie eine
normale Fertigkeit auf der üblichen 0-6-Skala. Kanten:
`(:Person)-[:HAT_ZUSATZFERTIGKEIT {rating: int}]->(:Zusatzfertigkeit)` —
läuft bewusst NICHT über `HAS_TRAIT`/`TraitDef` (der Katalog ist
ruleset-weit, nicht campaign-gebunden).

### Kosten — KORRIGIERT 28.09.2026, siehe unten "Umbau"

~~Gleiche Freebee-/EP-Kostentabelle wie eine normale Fertigkeit: Freebee 2
Punkte/Stufe (`FREEBEE_KOSTEN_JE_KATEGORIE["Fertigkeit"]`), EP-Tarif Faktor 2
/ Neu-Kosten 3 (`erfahrung.FAKTOR`/`NEU_KOSTEN["Fertigkeit"]`) — kein eigener
teurerer Tarif fürs Erstlernen. Naheliegendste, am wenigsten invasive Wahl.~~
*(EP-Tarif in der Spielphase gilt weiterhin unverändert — nur der
Erstellungsphase-Teil unten war der überholte Stand.)*

~~Das Neu-Erlernen einer Zusatzfertigkeit **während der Erstellung** zieht aus
einem eigenen, kleinen Freebee-Kontingent
(`ZUSATZFERTIGKEIT_FREEBEE_BUDGET = 6`, neues Feld
`Person.zusatzfertigkeitenFreebeesAusgegeben`) — **nicht** aus dem
Haupt-Freebee-Pool (`erstellung.FREEBEES_GESAMT`).~~ **ÜBERHOLT (28.09.2026,
noch am selben Tag von Mark korrigiert)** — siehe "Umbau" unten. Das
separate Budget existierte nur wenige Stunden und wurde nie in echten
Kampagnendaten verwendet.

Nach Erstellungsabschluss (`Person.erstellungAbgeschlossen`) läuft jedes
Neu-Erlernen UND jedes Steigern über EP, exakt wie ein normaler
Fertigkeitskauf (`traits/routes.py::steigere_wert`). **Das bleibt
unverändert** — nur die Erstellungsphase wurde umgebaut.

## Button + Punktzeilen im Fertigkeiten-Raster (28.09.2026, Abend)

Mark, nach dem ersten Umbau: die Klick-Liste ohne Punkte reicht nicht.
Gewünscht: Button „Zusatzfertigkeiten“ im Fertigkeiten-Popup → nested
Auswahl-Fenster → gewählte Skills erscheinen als normale Punktzeilen
(DotPool) im selben Raster, verbrauchen Paket-Slots, wandern ins Blatt.

- `ErstellungInput.zusatzfertigkeitPunkte` = Paketpunkte (0 = gewählt ohne Slot)
- `ErstellungInput.zusatzfertigkeitFreebees` = Freebee-Aufschlag (0 oder 1)
- Rating = Paket + Freebee; Kante auch bei rating 0

## Umbau: Auswahl im Fertigkeiten-Schritt, Bezahlung im Freebees-Schritt (28.09.2026)

Mark, wörtlich, zur ersten Version (Popup-Button in der Erstellungs-
Kopfzeile + eigenes Freebee-Budget): *"Nein das passt nicht, bei den
freebees erscheinen die einfach nicht wenn sie nicht zuvor schon bei der
Fertigkeiten Vergabe ausgewählt wurden, und wenn diese dort ausgewählt
wurden werden die skills im CharakterBlatt erweitert und sollten dann auch
mit den normalen freebees abgerechnet werden könne weil sie in keinem
Untermenü mehr sind."*

Konkret geändert:

1. **Kein separates Freebee-Budget mehr.** `ZUSATZFERTIGKEIT_FREEBEE_BUDGET`
   und `Person.zusatzfertigkeitenFreebeesAusgegeben` sind vollständig
   entfernt (aus `_BOGEN_DEFAULTS`/`PERSON_FIELDS`, allen drei
   Person-Schemas, `zusatzfertigkeiten/routes.py`).
2. **Auswahl passiert im Fertigkeiten-Schritt** der Charaktererstellung
   (`frontend/src/traits/Charaktererstellung.tsx::SchrittFertigkeiten`,
   neuer Abschnitt "Zusatzfertigkeiten" im Fertigkeitswahl-Fenster). Rein
   lokaler React-State (`zusatzfertigkeiten: Zusatzfertigkeit[]`) — KEIN
   Server-Write, genau wie Attribut-/Fertigkeits-/Hintergrundwahl auch erst
   beim finalen Submit (`bogenApi.erstellen`) persistiert wird. Neue,
   schlanke Komponente `zusatzfertigkeiten/ZusatzfertigkeitAuswahl.tsx`
   (Katalog laden, Liste anzeigen, `onWaehlen(z)`/`onAbwaehlen(id)` ohne
   API-Write) statt `ZusatzfertigkeitPopup.tsx` mit Modus-Flag zu verbiegen
   — der bleibt unverändert für LevelUp (siehe Punkt 6).
3. **Bezahlung im Freebees-Schritt** (`SchrittFreebees`, neuer Abschnitt
   direkt nach den normalen Fertigkeiten-Kategorien) aus dem GEMEINSAMEN
   Hauptpool (`regeln.freebees.gesamt`), dieselbe `freebeesVerbraucht`-
   Rechnung wie jede andere Kategorie. Kosten-Kategorie "Fertigkeit" (2
   Freebees, höchstens 1 Punkt beim Ersterwerb — `FREEBEE_MAX_JE_
   FERTIGKEIT`, dieselbe Regel wie bei normalen Fertigkeiten). State
   `zusatzfertigkeitFreebees: Record<zusatzfertigkeitId, punkte>` — keyed
   nach Zusatzfertigkeit-ID statt Traitname (eigener Record statt
   Wiederverwendung von `freebeePunkte`, weil die Kategorie-Zuordnung dort
   über Traitnamen aus dem TraitDef-Katalog läuft, Zusatzfertigkeiten aber
   campaign-gebunden und nicht Teil dieses Katalogs sind).
4. **Nicht im Fertigkeiten-Schritt gewählte Zusatzfertigkeiten erscheinen im
   Freebees-Schritt nicht.** Die Liste im Freebees-Schritt iteriert exakt
   über den `zusatzfertigkeiten`-State aus Schritt 2, kein separater
   Katalog-Fetch.
5. **Backend:** `ErstellungInput.zusatzfertigkeitPunkte: dict[str, int]`
   (Zusatzfertigkeit-ID → Freebee-Punkte, 0 oder 1). `erstelle_charakter`
   prüft die IDs gegen den campaign-gebundenen Katalog, addiert die Kosten
   in `erstellung.freebee_kosten()` (Kategorie "Fertigkeit" je gewählter,
   bezahlter Eintrag) und in `erstellung.pruefe()` (Freebee-Obergrenze pro
   Eintrag), setzt danach die `HAT_ZUSATZFERTIGKEIT`-Kanten mit
   `rating = zusatzfertigkeitPunkte[id]` — nur für Einträge mit Punkten > 0
   (gewählt, aber nicht bezahlt landet NICHT auf dem Charakterblatt, exakt
   wie Mark es verlangt hat: "gewählten+bezahlten"). Bei erneuter
   Einreichung (SL-Korrektur) werden zwischenzeitlich abgewählte/nicht mehr
   bezahlte Einträge über `zusatzfertigkeiten_repository.entferne_von_person`
   wieder entfernt — analog zum "auf 0 zurückfallen" bei normalen Traits.
6. **LevelUp bleibt vollständig unverändert.** Der Popup-Button mit
   sofortigem EP-Abzug (`ZusatzfertigkeitPopup.tsx` in `LevelUp.tsx`) ist
   strukturell korrekt: kein Vorab-Sammelschritt, jeder Punktkauf ist ohnehin
   ein sofortiger Server-Roundtrip, genau wie das normale
   `steigere_wert`-Einzelkauf-Muster. `zusatzfertigkeiten/routes.py::
   zusatzfertigkeit_hinzufuegen` (POST) lehnt jetzt VOR Erstellungsabschluss
   explizit mit 409 ab ("... werden im Fertigkeiten-Schritt der
   Charaktererstellung gewählt, nicht hier"), weil dieser Codepfad während
   der Erstellungsphase nicht mehr genutzt wird.

### Löschen aus dem Katalog

Hartes `DETACH DELETE` inklusive der Kanten zu Personen, die die
Zusatzfertigkeit gewählt haben — anders als bei Rassen (`Person.rasse`
bleibt dort als reiner Textwert bestehen, weil er unabhängig vom
Katalogknoten existiert). Eine Zusatzfertigkeit hat kein eigenes Textfeld am
Charakter, sie IST die Kante `HAT_ZUSATZFERTIGKEIT` zum Katalogknoten — bliebe
der Knoten weg, aber die Kante bestehen, zeigte das Charakterblatt eine
kaputte Referenz ins Leere. Der Verlust eines gewählten Eintrags beim
Katalog-Löschen ist hinnehmbar, weil Zusatzfertigkeiten ohnehin reiner
Name + Beschreibung ohne Mechanik sind.

### Endpunkte

Siehe [[../../api/zusatzfertigkeiten.md]]. Kurz: `GET/POST/PATCH/DELETE
.../zusatzfertigkeiten` (Katalog-CRUD, Schreiben nur SL), `GET
.../zusatzfertigkeiten/ki-vorschlaege` + `POST .../uebernehmen` (SL-only,
siehe KI-Vorschlag unten), `GET/POST
.../personen/{id}/zusatzfertigkeiten` (Wählen, Spieler am eigenen
Charakter erlaubt) und `POST .../{zid}/steigern` (Spieler-Selbstbedienung).

### KI-Vorschlag

Zweistufig wie beim Händler-Sortiment-Vorschlag
(`haendler/ki_vorschlag.py`): `vorschlaege()` liefert 3-5 Kandidaten zur
Ansicht (nichts wird gespeichert), die SL übernimmt jeden Vorschlag einzeln
(bewusst kein Sammel-Übernehmen). Der Prompt bekommt die bereits
existierenden Zusatzfertigkeiten dieser Kampagne mit (keine Duplikate) und
den NeotopiA-Cyberpunk-Kontext; Ton/Umfang orientiert an
`Optionale_Fertigkeiten.md` (Kurzbeschreibung ein Satz, Detailbeschreibung
ein Absatz). Echt verifiziert (28.09.2026) mit realem Gemini/Mistral-Aufruf
— drei plausible, settinggerechte Vorschläge ("Neurales Datenarchivieren",
"Stadtgeflüster-Dechiffrierung", "Magische Signalstörung"), einer
übernommen und im Katalog bestätigt.

### Frontend

- **SL-Tabelle** (`zusatzfertigkeiten/ZusatzfertigkeitenVerwaltung.tsx`,
  neuer Burgermenü-Punkt): schlichte Tabelle (Marks Vorgabe "eine einfache
  Tabelle"), Zeile öffnet Bearbeiten-Popup mit `onBlur`-Speichern (wie
  Rassen-Editor), Löschen mit `Bestaetigung`-Rückfrage, "+ Neu"-Popup, "✨
  KI-Vorschläge"-Popup mit editierbaren Kandidaten. **Unverändert seit
  28.09.2026 Vormittag.**
- **Charaktererstellung** (28.09.2026, nach dem Umbau — siehe Abschnitt
  oben): KEIN eigenständiger Popup-Button in der Kopfzeile mehr. Auswahl im
  Fertigkeiten-Schritt (`Charaktererstellung.tsx::SchrittFertigkeiten`,
  neuer Abschnitt "Zusatzfertigkeiten" unten im Fertigkeitswahl-Fenster,
  Komponente `zusatzfertigkeiten/ZusatzfertigkeitAuswahl.tsx`), Bezahlung im
  Freebees-Schritt (`SchrittFreebees`, neuer Abschnitt direkt nach den
  Fertigkeiten-Kategorien) — ganz normale `DotPool`-Zeile wie jede andere
  Fertigkeit, kein Untermenü/Popup mehr.
- **LevelUp-Popup** (`zusatzfertigkeiten/ZusatzfertigkeitPopup.tsx`,
  eingebunden in `LevelUp.tsx`): **unverändert**, sofortiger Server-Write mit
  EP-Abzug — strukturell korrekt, weil LevelUp ohnehin jeden Punktkauf
  einzeln an den Server schickt (kein Sammelschritt).
- **Charakterblatt** (`Charakterblatt.tsx`): eigener kleiner Abschnitt nach
  den Ausrüstungsfertigkeiten, NICHT ins feste `reihe(...)`-Raster der
  Hauptfertigkeiten gemischt — die Liste ist pro Person variabel. Klick löst
  wie jede andere Fertigkeit eine Probe aus (Kategorie `"Zusatzfertigkeit"`).
  Steigern nur im LevelUp, nicht direkt im Blatt. **Unverändert** — die
  Dateneinspeisung kommt jetzt aus der neuen Erstellungslogik
  (`HAT_ZUSATZFERTIGKEIT`-Kanten, direkt beim `erstelle_charakter`-Submit
  gesetzt statt über den alten Popup-Sofort-Write), die Anzeige selbst
  brauchte keine Anpassung.

### Verifiziert

`tsc -b` sauber, Backend-Import + `openapi()['paths']`-Grep, volles
`pytest` (446 grün, 2 vorbestehende unabhängige Fehlschläge einer
parallelen Session — `ereignisprotokoll`/`haendler`-Baustelle, unabhängig
per `git stash`-Vergleich bestätigt), echter End-to-End-Test gegen laufende
Neo4j (28.09.2026, nach dem Umbau): Kampagne + Mensch-Rasse freigegeben,
zwei Zusatzfertigkeiten im Katalog angelegt, Erstellung mit NUR einer davon
+ 1 Freebee-Punkt eingereicht — bestätigt (a) `freebeesVerbraucht` korrekt
um +2 erhöht, (b) `HAT_ZUSATZFERTIGKEIT`-Kante mit `rating=1` existiert nur
für die gewählte, (c) die nicht gewählte taucht weder in der
Personen-Antwort noch in der DB auf, (d) eine überzogene Freebee-Einreichung
(>15 gesamt) wird korrekt mit 422 abgelehnt. Testdaten aufgeräumt. **Kein
Browser-Klicktest** — siehe CLAUDE.md "Offen: Was Mark selbst testen muss".

## Noch nicht entschieden / offen

- **Ob Zusatzfertigkeiten auch für NPCs/Begleiter gedacht sind** — bisher nur
  an `Person` (deckt PC/NPC/Critter/KI gleichermaßen ab, kein eigener
  Ausschluss), aber die Erstellungs-/LevelUp-Flows hängen nur an
  Spieler-Charakteren. Die SL könnte theoretisch über die Backend-Route
  auch NPCs Zusatzfertigkeiten geben, hat dafür aber keinen eigenen UI-Weg
  (nur über die Person-Route direkt).

## Siehe auch

- [[../../api/zusatzfertigkeiten.md]] — Endpunkte
- [[rassen-baukasten-feature]] — verwandtes CRUD-Muster (globaler Katalog +
  Freigabe), bewusst NICHT übernommen (siehe oben, kein Freigabe-Schritt)
- [[ki-integration]] — KI-Vorschlag-Muster (`generiere_json`)
- [[neo4j-datenmodell]] — `Zusatzfertigkeit`-Knoten,
  `HAT_ZUSATZFERTIGKEIT`-Relation
- [[../../../CLAUDE.md]] — "Zuletzt gebaut" / "Offen: Was Mark selbst testen muss"
