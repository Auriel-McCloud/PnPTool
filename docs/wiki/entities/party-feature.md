---
title: Party-Feature
created: 2026-09-18
updated: 2026-09-26
type: entität
tags: [party, backend, frontend, geplant]
sources: [../../api/party.md, ../../../backend/app/party/]
status: aktuell
---

# Party-Feature

Wer gerade zusammen unterwegs ist — eine wiederentdeckte Vision.

## Herkunft: eine verlorene Idee

Am 28.08.2026 hatte Mark diese Idee schon einmal skizziert und in `CLAUDE.md`
festgehalten. Beim großen Verschlankungs-Commit (2500→170 Zeilen) ging der
Abschnitt "Vision — Party/Gruppen, Suche & Kategorisierung" verloren — nur
ein toter Verweis in `docs/ui-konzept.md` blieb übrig ("siehe CLAUDE.md,
Abschnitt..."), der ins Leere zeigte. Am 18.09.2026 beim gemeinsamen
Durchgehen offener Themen wieder aufgetaucht und diesmal umgesetzt.

Marks ursprüngliche Formulierung, wortgetreu erhalten, weil sie präziser war
als eine spätere Nacherzählung: *"Spieler bilden nicht immer eine einzige
feste Gruppe — sie können sich aufteilen (2 gehen shoppen, 2 gehen zu einem
NPC), wodurch mehrere gleichzeitige, temporäre Partys entstehen."*

## Abgrenzung zu Fraktion

Eine Fraktion (siehe `docs/api/entitaeten.md`) ist eine dauerhafte
Organisation mit eigenen Zielen und Ressourcen — Konzern, Gang, Regierung.
Eine Party hat keine eigenen Absichten, sie ist schlicht "wer gerade
beisammen ist". Deshalb ein **eigenes Modul** (`backend/app/party/`) statt
einer Erweiterung der generischen Entitäten (Person/Ort/Event/Fraktion),
weil Party eigene Beziehungslogik braucht (Mitgliedschafts- und
Aufenthaltsort-Exklusivität), die im generischen Entitäten-Muster nicht
vorgesehen ist.

## Design-Entscheidungen (Mark, 18.09.2026)

1. **Eine Person ist höchstens in einer Party gleichzeitig.** Neue
   Mitgliedschaft löst automatisch die alte — kein Doppel.
2. **Dauerhaftes Objekt**, kein Ad-hoc-Wegwerfobjekt — bleibt bestehen, auch
   leer, bis explizit gelöscht.
3. **Gemischte Mitgliedschaft** — PCs, NPCs, Begleiter in derselben Party.
4. **Höchstens eine Party pro Kampagne ist aktiv.** Aktivieren deaktiviert
   automatisch alle anderen — dieselbe Exklusivität wie ein laufender Kampf
   (siehe [[../concepts/kampf-und-initiative]]).

## Warum "aktive Party": die Spotify-Verbindung

Der Auslöser für die Aktiv-Exklusivität war nicht reine Übersichtlichkeit,
sondern eine konkrete Zukunftsanbindung: Mark plant Spotify über die Yamaha
RX-V4A/MusicCast-Anlage, mit einer Playlist pro Szene/Ort. Die aktive Party
trägt ihren Aufenthaltsort — das ist die Datengrundlage, aus der später
"welche Musik läuft gerade" abgeleitet werden kann. **Am 19.09.2026
umgesetzt** — siehe [[../../api/spotify.md]]: Aktivieren einer Party mit
gesetztem Aufenthaltsort (oder das Setzen eines neuen Aufenthaltsorts an der
aktiven Party) startet automatisch die dort hinterlegte Playlist auf Marks
gerade aktivem Spotify-Gerät. Kein Yamaha-Direktzugriff — Spotify Connect
übernimmt Geräteauswahl/Lautstärke, Mark steuert das am Handy selbst.

## Datenmodell

Zwei neue Beziehungstypen, beide nach dem "alte Kante weg, neue rein"-Muster
aus `begleiter/repository.py::besitzer_setzen` und
`items/repository.py::set_ablage`:

- `(:Person)-[:MITGLIED_VON]->(:Party)` — Mitgliedschaft, exklusiv
- `(:Party)-[:BEFINDET_SICH_AN]->(:Ort|:Event)` — Aufenthaltsort, optional

`aktiv` ist eine reine Property am `:Party`-Knoten, keine eigene Kante nötig.

Vollständige API-Referenz: [[../../api/party.md]].

## Frontend

Eigener Bereich (👥-Symbol, Farbe `--bereich-party`) in der Commlink-Shell,
nach demselben Muster wie Begleiter/Rassen: Kachelraster mit
Party-Kacheln (aktive Party leuchtet in der Leitfarbe), Fenster zum
Bearbeiten mit Mitglieder-Verwaltung und Aufenthaltsort-Dropdown.

**Anlegen als Popup, nicht Inline** (18.09.2026, Mark: "es ist leider nicht
im Stil vom Rest" — Erstfassung hatte ein Inline-Formular auf der
Übersichtsseite, gegen die Konvention "alle Dialoge als gestylte
Commlink-Popups, nie native Browser-Dialoge oder Inline-Formulare"): der
"+ Neue Party"-Knopf öffnet jetzt ein `Fenster`-Popup mit Namensfeld **und
gleich einer Checkbox-Liste aller Personen** zur Sofort-Zuordnung — Marks
Wunsch, die Party nicht erst leer anzulegen und dann separat zu füllen.

## Offen (Phase 2, bewusst zurückgestellt)

- **Inventar-Erweiterung**: Party-Mitgliedern gegenseitig Gegenstände geben
  — **Teil erledigt 26.09.2026** (`GEGENSTAND_WEITERGABE`, siehe
  [[gegenstand-transfer]]). Offen bleibt: Weitergabe an Leute am gleichen Ort
  außerhalb der Party (PCs haben keinen eigenen Standort), Geld-Transfer,
  SL-NPC-Belohnung.
- **Party-Anzeige am Ort/Event-Popup** — momentan nur von der Party-Kachel
  aus sichtbar, nicht umgekehrt.

## Siehe auch

- [[../../api/party.md]] — vollständige Endpunkt-Referenz
- [[gegenstand-transfer]] — Party-interne Gegenstands-Weitergabe (26.09.2026)
- [[neo4j-datenmodell]] — `MITGLIED_VON`/`BEFINDET_SICH_AN` im Gesamtkontext
- [[../../../CLAUDE.md]] — Spotify/MusicCast als geplantes Feature (Punkt 4)
