---
title: Hintergrund-Baukasten (geplant)
created: 2026-10-10
updated: 2026-10-10
type: entität
tags: [charaktererstellung, hintergrund, erfahrung, achievements, geplant]
sources: [../../../CLAUDE.md, ../../../backend/app/traits/erstellung.py, zusatzfertigkeiten.md, achievements.md]
status: geplant-nicht-begonnen
---

# Hintergrund-Baukasten (geplant)

Mark will die Hintergründe bearbeiten können, aktuell gibt es dafür **keine
UI** — die Liste ist fest im Code (`backend/app/traits/erstellung.py::
HINTERGRUENDE`). Auslöser der Runde: Nachfrage, ob eine Hintergrund-Änderung
automatisch mit den Achievements abgeglichen wird, die Hintergrundpunkte als
Belohnung vergeben (siehe [[achievements]], Abschnitt "Mechanische
Belohnung"). Antwort: **teilweise, mit einer bekannten Schwachstelle** — s.
unten.

## Ist-Zustand

- `HINTERGRUENDE: list[dict]` in `erstellung.py` — zehn feste Einträge
  (Kontakte, Ressourcen, Straßenruf, Verbündete, Mentor, Unterschlupf,
  Schwarzmarkt, Konzernzugang, Ausrüstung, Geheimwissen), je `name` +
  `beschreibung`. **Nicht campaign-gebunden, nicht editierbar.**
- Landen wie jeder andere Wert im **ruleset-weiten `TraitDef`-Katalog**
  (`traits/seed.py` importiert `HINTERGRUENDE` und hängt sie mit Kategorie
  `"Hintergrund"` an `NEOTOPIA_TRAITS` an) — Kanten laufen über das
  bestehende `HAS_TRAIT`, **nicht** über das campaign-gebundene Muster von
  Zusatzfertigkeiten (`HAT_ZUSATZFERTIGKEIT`).
- `HINTERGRUND_MAX = 5` (Deckel je Hintergrund), `HINTERGRUND_PUNKTE_GESAMT
  = 5` (Summe bei der Erstellung).
- Bei der Erstellung: freie Verteilung bis zum Gesamtdeckel, wie eine
  Fertigkeit.
- **Nach der Erstellung NICHT mehr vom Spieler steigerbar** — `LevelUp.tsx`
  schließt die Kategorie `Hintergrund` bewusst aus der
  Spieler-Selbstbedienung aus (Kommentar: "die kann nach der
  Charaktererstellung nur noch die SL vergeben"). Das war bis 10.10.2026
  eine Sackgasse ohne jeden SL-Weg — **Achievements mit
  `belohnungsArt: "HINTERGRUND"` sind seitdem der einzige Weg**, wie ein
  Hintergrund nach der Erstellung noch steigt (siehe [[achievements]]).

## Bekannte Schwachstelle: Achievement-Bezug über Namen, nicht ID

`Achievement.belohnungsHintergrund` speichert den Hintergrund-**Namen** als
reinen Text (z. B. `"Ruf"` — Achtung, der tatsächliche Name in der Liste
heißt `"Straßenruf"`, Beispiel nur illustrativ). Beim Einlösen
(`backend/app/achievements/belohnung.py::einloesen`) sucht das Backend im
`TraitDef`-Katalog nach **exakt diesem Namen** in Kategorie `"Hintergrund"`.

- **Beschreibung ändern** → unkritisch, der Name bleibt stabil.
- **Hintergrund umbenennen** → bricht die Verknüpfung **still**: das
  Achievement findet den alten Namen nicht mehr, die Belohnung verpufft
  beim Vergeben ohne Fehlermeldung (kein Crash, einfach keine Wirkung).
- **Hintergrund löschen** → dasselbe Problem.
- **Neuer Hintergrund** → unkritisch, taucht automatisch im
  Achievement-Baukasten-Dropdown auf (`bogenApi.regeln().hintergruende`).

**Empfehlung für die neue Session:** sobald ein Baukasten existiert, den
Bezug in `Achievement.belohnungsHintergrund` von Name auf eine echte
`TraitDef`-ID (oder künftige Hintergrund-Katalog-ID) umstellen. Bis dahin:
Mark **nicht** vor Augen führen, Hintergrund-Namen zu ändern, ohne vorher
alle Achievements zu prüfen, die darauf verweisen (`GET
/api/campaigns/{id}/achievements`, Feld `belohnungsHintergrund`).

## Offene Design-Frage für die neue Session

**Campaign-gebundener Baukasten wie Zusatzfertigkeiten, oder
ruleset-weiter Katalog mit Editor?** Das ist die zentrale Weichenstellung,
bevor irgendetwas gebaut wird:

- **Pro campaign-gebunden** (wie [[zusatzfertigkeiten]]): passt zum
  bisherigen Stil "jede Kampagne kann eigene Fiktion haben", einfacher zu
  bauen (kein Freigabe-Schritt, kein ruleset-weiter Sync).
- **Contra:** Hintergründe sind aktuell **ruleset-weit** im `TraitDef`-
  Katalog, nicht campaign-gebunden wie Zusatzfertigkeiten — eine Umstellung
  wäre ein Daten-Migrationsschritt für alle Bestandskampagnen (bestehende
  `HAS_TRAIT`-Kanten pro Person müssten erhalten bleiben).
- **Alternative:** ruleset-weiter Editor direkt auf dem bestehenden
  `TraitDef`-Katalog (Kategorie `"Hintergrund"`) — kein Umzug nötig, aber
  dann sind Hintergründe nicht mehr frei "nur für diese Kampagne"
  erfindbar, sondern gelten serverweit für alle Kampagnen desselben
  Rulesets (aktuell gibt es nur ein Ruleset: NeotopiA).

Mark muss das zuerst entscheiden, dann lässt sich der Rest (Backend-CRUD,
Frontend-Tabelle analog `ZusatzfertigkeitenVerwaltung.tsx`, Migration
Bestandsdaten, Achievement-ID-Fix) ableiten.

## Siehe auch

- [[achievements]] — Abschnitt "Mechanische Belohnung" + "Bekannte
  Schwachstelle" dort referenziert dieses Dokument
- [[zusatzfertigkeiten]] — Vorbild für einen campaign-gebundenen Katalog
  ohne Freigabe-Schalter, inkl. SL-Tabelle + Löschen-Verhalten
- [[../concepts/erfahrung-und-steigern]] — Hintergrund-Steigerungssperre
  nach der Erstellung, Faktor/Neu-Kosten-Tabelle
- [[rassen-baukasten-feature]] — alternatives CRUD-Vorbild mit
  Freigabe-Schalter (falls campaign-gebunden MIT Freigabe gewünscht wird)
- [[../../../CLAUDE.md]] — laufender Projektstand
