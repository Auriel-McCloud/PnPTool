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

### Kosten — eigene Design-Entscheidung, mit Mark noch nicht gegengeprüft

Gleiche Freebee-/EP-Kostentabelle wie eine normale Fertigkeit: Freebee 2
Punkte/Stufe (`FREEBEE_KOSTEN_JE_KATEGORIE["Fertigkeit"]`), EP-Tarif Faktor 2
/ Neu-Kosten 3 (`erfahrung.FAKTOR`/`NEU_KOSTEN["Fertigkeit"]`) — kein eigener
teurerer Tarif fürs Erstlernen. Naheliegendste, am wenigsten invasive Wahl.

Das Neu-Erlernen einer Zusatzfertigkeit **während der Erstellung** zieht aus
einem eigenen, kleinen Freebee-Kontingent
(`ZUSATZFERTIGKEIT_FREEBEE_BUDGET = 6`, neues Feld
`Person.zusatzfertigkeitenFreebeesAusgegeben`) — **nicht** aus dem
Haupt-Freebee-Pool (`erstellung.FREEBEES_GESAMT`). Grund: der Hauptpool wird
ausschließlich bei der finalen `POST .../erstellung`-Einreichung berechnet,
rein aus dem im selben Request eingereichten `ErstellungInput`-Body, ohne
DB-Zustand — ein separat auslösbarer Popup-Knopf, der schon während des
laufenden mehrstufigen Assistenten sofort einen DB-Schreibzugriff macht,
kann in diese Rechnung nicht eingehängt werden, ohne den gesamten
Erstellungs-Flow umzubauen. Ein eigenes kleines Budget (analog zu
`HINTERGRUND_PUNKTE_GESAMT`, ebenfalls separat budgetiert außerhalb des
Haupt-Fertigkeitspakets) ist die am wenigsten invasive Lösung — **Mark
sollte gegenprüfen, ob 6 Punkte (reicht für 3 Zusatzfertigkeiten) die
richtige Größenordnung ist.**

Nach Erstellungsabschluss (`Person.erstellungAbgeschlossen`) läuft jedes
Neu-Erlernen UND jedes Steigern über EP, exakt wie ein normaler
Fertigkeitskauf (`traits/routes.py::steigere_wert`).

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
  KI-Vorschläge"-Popup mit editierbaren Kandidaten.
- **Spieler-Popup** (`zusatzfertigkeiten/ZusatzfertigkeitPopup.tsx`):
  identisch wiederverwendet in `Charaktererstellung.tsx` (Kopfzeile,
  unabhängig vom aktuellen Schritt) UND `LevelUp.tsx` (Kopfzeile, neben
  Speichern/Zurücksetzen) — derselbe Popup-Button, kein Sonderfall (Marks
  Vorgabe). Zeigt die noch nicht gewählten Einträge mit Kurzbeschreibung +
  Suchfeld (ab >6 Einträgen), Klick fügt sofort hinzu und zeigt danach den
  neuen Freebee-/EP-Stand.
- **Charakterblatt** (`Charakterblatt.tsx`): eigener kleiner Abschnitt nach
  den Ausrüstungsfertigkeiten, NICHT ins feste `reihe(...)`-Raster der
  Hauptfertigkeiten gemischt — die Liste ist pro Person variabel. Klick löst
  wie jede andere Fertigkeit eine Probe aus (Kategorie `"Zusatzfertigkeit"`).
  Steigern nur im LevelUp, nicht direkt im Blatt.

### Verifiziert

`tsc -b` + `vite build` sauber, Backend-Import + `openapi()['paths']`-Grep,
volles `pytest` (446 grün, 2 vorbestehende unabhängige Fehlschläge einer
parallelen Session per `git stash`-Vergleich abgegrenzt), echter
End-to-End-Test gegen laufende Neo4j (Katalog anlegen/bearbeiten/löschen,
Person wählt in Erstellungsphase [Freebee-Abzug] UND Spielphase
[EP-Abzug], steigert, Löschen kaskadiert korrekt auf die Personen-Kante)
sowie ein echter KI-Vorschlag-Aufruf. **Kein Browser-Klicktest** — siehe
CLAUDE.md "Offen: Was Mark selbst testen muss".

## Noch nicht entschieden / offen

- **Freebee-Budget-Größe** (`ZUSATZFERTIGKEIT_FREEBEE_BUDGET = 6`): eigene
  Schätzung, nicht mit Mark abgestimmt.
- **Ob Zusatzfertigkeiten auch für NPCs/Begleiter gedacht sind** — bisher nur
  an `Person` (deckt PC/NPC/Critter/KI gleichermaßen ab, kein eigener
  Ausschluss), aber die Popups hängen nur an Spieler-Flows
  (Charaktererstellung, LevelUp). Die SL könnte theoretisch über die
  Backend-Route auch NPCs Zusatzfertigkeiten geben, hat dafür aber keinen
  eigenen UI-Weg (nur über die Person-Route direkt).

## Siehe auch

- [[../../api/zusatzfertigkeiten.md]] — Endpunkte
- [[rassen-baukasten-feature]] — verwandtes CRUD-Muster (globaler Katalog +
  Freigabe), bewusst NICHT übernommen (siehe oben, kein Freigabe-Schritt)
- [[ki-integration]] — KI-Vorschlag-Muster (`generiere_json`)
- [[neo4j-datenmodell]] — `Zusatzfertigkeit`-Knoten,
  `HAT_ZUSATZFERTIGKEIT`-Relation
- [[../../../CLAUDE.md]] — "Zuletzt gebaut" / "Offen: Was Mark selbst testen muss"
