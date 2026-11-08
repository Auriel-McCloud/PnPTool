---
title: Battlemap
created: 2026-11-06
updated: 2026-11-08
type: entität
tags: [kampf, frontend, backend, websocket, ui, datenmodell, geplant]
sources: [../../../CLAUDE.md, ../../../backend/app/zeichnungen/repository.py, ../../../backend/app/kampf/repository.py, ../../api/kampf.md, ../concepts/kampf-und-initiative.md]
status: teilweise-umgesetzt
---

# Battlemap

Hex-Kampfkarte. Gebaut 06.11.2026, Spieltisch-Klicktest offen.

## Auslöser

Mark, 06.11.2026: ein Grid (am liebsten Hex) auf eine Zeichnung oder ein Bild
legen. Charakterportraits der Leute in der Initiative als kleine Hex-Tokens,
Drag-and-Drop rastet ein. Jeder Spieler darf den eigenen Charakter bewegen,
dazu die eigenen Drohnen und Beschwörungen. Um den Token herum die Felder in
Reichweite grün umrandet: `3 + Sportlichkeit`, bei Drohnen `3 + Fliegen`.
Große Monster nehmen 4 benachbarte Felder. Wer gerade dran ist, wird
hervorgehoben. Frage: Whiteboard kopieren oder erweitern?

## Whiteboard nicht erweitern, Leinwand kopieren

Eigenes Feature, kein Aufsatz auf `Zeichnung`. Die bestehende Whiteboard-Liste
bleibt Zeichenbrett ohne Tokens.

Kopiert wird das Whiteboard-Muster inklusive Leinwand: Hintergrundbild,
`pfade` (react-sketch-canvas), `spielerDuerfenZeichnen`, Sichtbarkeit,
Papierkorb, Verteiler mit vollem Zustand. Darauf liegen Hex-Grid und Tokens.
Kein `EntityKind`.

Erste Skizze sagte „keine Zeichenpfade“. Ersetzt 06.11.2026: Mark will auf der
Battlemap live zeichnen und Spieler mitzeichnen lassen, plus Grid skalieren.
Deshalb der Vergleich mit dem Whiteboard — nicht weil Tokens Striche wären.

`docs/api/kampf.md` zeigt schon `position: { x, y }` an der Kante `KAEMPFT`.
Der echte Code speichert Teilnehmer als `KampfTeilnehmer`-Knoten, ohne
Position. Das API-Beispiel nicht als Modell nehmen.

## Entschieden 06.11.2026 (nicht gebaut)

Zwei Schichten:

1. **Karte** als Kampagnen-Asset, eigener Burgermenü-Punkt zum Vorbereiten
   (Liste wie Whiteboard). Name, Hintergrundbild, Zeichenpfade, Zeichenfreigabe
   für Spieler, skalierbares Hex-Grid (Größe, Ursprung), Sichtbarkeit,
   Papierkorb. Der laufende Kampf hängt eine vorbereitete Karte an.
2. **Tokens** am laufenden Kampf: Position am `KampfTeilnehmer`, Portrait aus
   `Person.bildUrl`. Kein unplatzierter Stapel — sie entstehen an den zwei
   Spawn-Feldern der Karte (siehe Nachschärfung). `amZug` ist das Highlight.
   Ein Zusatzzug (Reflex-Booster) ist dieselbe Person, kein zweiter Token.
   Spieler schiebt eigenen Charakter, eigene Drohnen und Beschwörungen nur am
   eigenen Zug. Die SL schiebt immer alle.

Bewegung: Drop überall, rastet auf Hex. Grün ist nur die Hilfe — Sprint,
Teleport, SL räumt. Laufen `3 + Sportlichkeit`. Drohnen `3 + Fliegen × 2`
(06.11. Nachschärfung, ersetzt `3 + Fliegen`: Fliegen ist schneller als
Laufen). Die Formel steht auf keiner Regel-Seite, neu, nicht Excel. Fliegen
ist Zusatzfertigkeit, siehe [[../concepts/drohnen-fahrzeuge]].

Grün nur während des Ziehens, vom Feld wo der Token angehoben wurde, bleibt
bis zum Loslassen. Dieses Startfeld bleibt danach grau, bis der Teilnehmer
nicht mehr am Zug ist — dann weg. Ohne Anheben kein Grau.

Große Monster: **3 Felder im Y, Kreis drumherum.** Die 4-Felder-Idee aus dem
Auslöser ist ersetzt. Belegt sind die drei Hex; der Kreis gruppiert sie optisch.

Live-Sync: Token-Züge über den geplanten Kampf-WebSocket
([[../concepts/kampf-und-initiative]], ungebaut). Zeichnen wie beim Whiteboard
(voller Pfad-Stand). Karten-CRUD bleibt REST.

Konflikt mit [[../concepts/kampf-und-initiative]] „keine Würfel-Simulation“:
Token-Position ist „was auf dem Feld steht“. Reichweite sperrt den Drop nicht.
Zwei Tokens auf einem Hex sperren den Drop — das ist Belegung, keine Probe.

Nicht in der Anfrage, nicht Teil dieses Designs: Fog of War, Facing,
Quadrat-Grid-Umschalter. Belegungssperre stand hier zuerst als „nicht Teil“;
ersetzt 06.11. (Nachschärfung): zwei Charaktere nicht auf demselben Feld.

## Nachschärfung 06.11.2026 — Spawn, Rand, Größe (nicht gebaut)

Damit die SL nicht jeden Token einzeln setzt: auf der Karte zwei Spawn-Felder
(Vorbereitung). **Blau** für PCs, **Magenta** für NPCs. Tokens der Initiative
erscheinen dort; ist das Feld belegt, auf einem freien Nachbarn — dieselbe
Regel wie unten bei Drohne/Beschwörung.

Randfarben, vorhandene Tokens: PC `--p-blau`, NPC `--p-magenta`. Drohne und
Beschwörung in der Farbe des Besitzers (`personType` der Drohne ist NPC, zählt
trotzdem nicht als Magenta-NPC). Wer dran ist: `--p-gold` und pulsiert —
dasselbe Puls-Muster wie Hot (`gg-hot-puls`), Gold statt Magenta.
`prefers-reduced-motion` bleibt.

Zwei Charaktere nicht auf demselben Hex, auch die SL nicht. Das eigene
Startfeld (grau) zählt als frei für den, der dort steht. Groß belegt alle
drei Y-Hex.

Beschwörung oder Drohne aktivieren: Token auf einem freien Feld neben dem
Charakter. Kein freier Nachbar → nächstes freies Feld.

Größe: Umschalter **Normal / Groß** in der SL-PC- und NPC-Übersicht, Default
Normal. Derselbe Schalter im Rassen-Baukasten (`istGross`, kein Rassenname im
Code). Neue Person übernimmt den Rassen-Default, danach gilt der Personen-Wert.
Normal = 1 Hex, Groß = 3 im Y plus Kreis.

## Nachgezogen 06.11.2026 — Größe an der Person, Rasse nur Vorlage

Checkbox „Groß“ auf der PC- und NPC-Kachel. Die Rasse setzt den Startwert beim Anlegen, danach gilt die Person. Die Karte liest `Person.istGross`.

## Offene Achsen 06.11. (erste Fassung, ersetzt)

1. Bewegung — entschieden: überall droppen, Grün ist Hilfe.
2. Nur am eigenen Zug — entschieden: ja, SL immer alle.
3. Große Monster — erste Frage war 4 Hex; ersetzt durch 3 im Y plus Kreis.
4. Oberfläche — entschieden: Burgermenü zum Vorbereiten, Kampf hängt eine Karte an.
5. Unterlage — erste Frage war Bild oder Whiteboard-Standbild; ersetzt durch
   eigenes Bild plus Live-Zeichnen auf der Karte plus skalierbares Grid.

## Gebaut 06.11.2026

Modul `backend/app/battlemap/` (CRUD, Papierkorb, Live-Zeichnen wie Whiteboard).
Tokens am `KampfTeilnehmer` (`hexQ`/`hexR`). Kampf hängt `battlemapId` an.
Spieler-Move `PATCH .../kampf/teilnehmer/{id}/position` (nur eigener Token am Zug).
`istGross` an Person und Rasse. Burgermenü Battlemap, Kartenwahl im Kampfmodus.
Spieltisch-Klicktest offen. SL schiebt den Grid-Ursprung per „Grid schieben“;
Größe bleibt der Slider. Größe-Schalter auf den PC-/NPC-Kacheln zeichnet sofort
neu. Spieler schiebt eigene Drohnen und Beschwörungen (`besitzerId`).
Token-Rundruf ist die volle Teilnehmerliste (Portrait, neu Hinzugekommene),
nicht nur Positionen. Zugwechsel und Aufnehmen rufen mit. Kampfmodus hat
„Karte öffnen“. Öffnen einer Karte ohne angehängten Kampf hängt sie an und
spawnt. Grid-SVG stiehlt keine Zeichenklicks mehr.
Hex-Rand wie Spawn: aktive Party (PCs plus NPCs/Drohnen dabei) `--p-blau`,
andere NPCs `--p-magenta`, am Zug Gold. Raster füllt das Rechteck, keine
leeren Ecken.

## Verknüpfung mit Ort/Event, Karte öffnen für Spieler (06.11.2026)

Mark: Battlemaps mit Orten oder Events verknüpfen können, Karte-öffnen-Knopf
auch für Spieler (rechtsbündig neben der Rundenanzeige, wie bei der SL).

Zwei neue Listenfelder an der Battlemap, `ortIds`/`eventIds` — rein
organisatorisch fürs Vorbereiten/den Überblick, kein automatisches Anhängen
beim Kampfbeginn (das bleibt die bewusste SL-Auswahl im Kampfmodus, siehe
„Entschieden 06.11.2026“ oben). Editierbar als Mehrfachauswahl in den
Karten-Einstellungen (`BattlemapEinstellungen.tsx`, gleiches
`<select multiple>`-Muster wie `Ort.versteckVonPersonIds`); Badges in der
Vorbereiten-Übersicht zeigen die Verknüpfung auf einen Blick
(`BattlemapAnsicht.tsx`, nur für die SL).

Spieler sehen jetzt denselben „Karte öffnen“-Knopf wie die SL, sobald ein
Kampf eine Battlemap angehängt hat — rechtsbündig neben „Runde N“
(`SpielerAnsicht.tsx`), dieselbe `BattlemapPopup`-Komponente, nur ohne
Grid-/Spawn-Werkzeuge (`istGm=false`). Zeichnen nur, wenn die Karte es
freigibt (`spielerDuerfenZeichnen`). Serverseitig schon auf sichtbare Karten
beschränkt — eine SL-geheime Karte zeigt den Knopf dadurch gar nicht erst.

**Verifiziert:** Live-E2E-Skript gegen echte Neo4j (erstellen/aktualisieren/
holen/leeren der neuen Felder, inkl. Leeren per PATCH mit `[]`), `npx tsc -b`
sauber. **Kein Klicktest** — bitte am Spieltisch: eine Karte einem Ort
zuordnen, prüfen dass die Badge erscheint, und dass ein Spieler im Kampf die
angehängte Karte per Knopf öffnen kann.

## Entschieden 06.11.2026 — Blickrichtung, Verstecken, letzte Sicht (nicht gebaut)

Widerspricht der Zeile oben „Fog of War, Facing sind nicht Teil dieses Designs“.
Die Zeile bleibt als erste Ausschluss-Fassung. Ersetzt durch diesen Abschnitt.

Mark, nach der Idee seiner Frau:

- Blickrichtung am Token (`blickrichtung` 0–5). Nicht `hexDrehung` — das dreht
  nur die Drei-Hex-Lage großer Tokens.
- Vorne sind drei von sechs Hex-Richtungen. Dahinter bleibt der Stand vom
  letzten Hinsehen, kein schwarzes Loch. Zu Kampfbeginn liegt überall der
  Startstand, der hintere Halbkreis friert, bis man sich umdreht.
- Umschauen und Bewegen sind zwei Schritte. Umschauen setzt die Blickrichtung
  und frischt den vorderen Halbkreis, ohne das Feld zu wechseln. Beim
  Verschieben sucht er sich die Blickrichtung aus und sieht dann, was dort
  liegt. Der Vorschlag ist die Schrittrichtung, eine andere ist erlaubt.
  Dieselbe Erlaubnis wie Schieben: eigener Token am eigenen Zug, die SL immer.
  „Kein Aus-Schalter“ ist ersetzt: Fog of War ist ein Schalter in den
  Kampagnen-Einstellungen, Standard aus. An = die letzte Sicht gilt.
  Aus = alle sehen die Wahrheit, wie bisher.
- Rundumsicht (Hören, Ultraschall): immer der aktuelle Stand, kein
  Hinterkopf. Feld an der Rasse, kein Rassenname im Code. Dasselbe Flag an
  verbautem Chrom, nicht im Rucksack. Dug'rah setzt die SL im Baukasten.
  Eine Drohne hat eigene Augen; das Chrom des Riggers gilt nicht für sie.
- Augen eines Spielers: eigener Charakter plus eigene Drohnen und
  Beschwörungen, Vereinigung. Die Party teilt die Sicht nicht.
- Versteckt schlägt den Kegel. Spieler schaltet den eigenen Token, die SL
  alle. Knopf im Namens-Chip, kein Doppelklick. Die SL sieht Versteckte
  abgeblendet. Kein automatischer Wahrnehmungs-Wurf.
- Einmal antippen zeigt den Namen groß. Ziehen bleibt Bewegen.
- Spieler bekommen nicht die volle Teilnehmerliste, sonst steht die Wahrheit
  im Client. Die SL sieht immer die Wahrheit.

Die erste Fassung „nicht gebaut“ ist ersetzt durch den Abschnitt darunter.

## Gebaut 06.11.2026 — Fog of War, optional

Schalter `fogOfWar` in den Kampagnen-Einstellungen, Standard aus. An: Spieler
bekommen nur ihre Augen (eigener Charakter, eigene Drohnen, eigene
Beschwörungen). Vorne drei von sechs Richtungen live, hinten der letzte Stand.
Versteckt schlägt den Kegel. Rundumsicht an der Rasse und an verbautem Chrom.
Antippen des eigenen Tokens (oder der eigenen Drohne) färbt die sechs
Nachbarfelder, auch außerhalb des Zugs. Ein Feld antippen setzt die
Blickrichtung nur am eigenen Zug. Gesehenes bleibt als Erinnerung (ALT, ohne Farbring), bis man wieder hinsieht. Spawn-Punkte nur für die SL. Hot: Körper bleibt liegen, gesteuert wird die Drohne.

**Verifiziert:** `tests/test_battlemap_sicht.py`, `npx tsc -b`. **Kein Klicktest.**

## Entschieden + gebaut 06.11.2026 — Matrix-Ping und Hot-Live-Sicht für den Decker

Mark, nach der Idee mit Matrix-Navigation als Ping fürs Battlemap. Baut direkt
auf der Fog-of-War-Erinnerung oben auf, kein neues System.

Entschieden (per `clarify`):

- **Normaler Ping (Matrix-Navigation-Erfolg, nicht Hot):** aktualisiert NUR
  die eigene Erinnerung des Deckers auf den aktuellen Stand ALLER Ziele —
  auch die, die gerade hinter ihm liegen. Die Party teilt das nicht, wie
  bisher. Technisch: wie ein einmaliger Rundumsicht-Blick nur für dieses eine
  Auge (`battlemap/sicht.py::ping`), kein Dauerzustand — was hinter ihm
  liegt, bleibt dabei trotzdem als Erinnerung (`veraltet: true`, kein
  Farbring), nur mit frischerer Position. Erst ein erneuter Ping oder
  tatsächliches Hinsehen frischt wieder auf.
- **Versteckt schlägt auch den Ping.** Wände blockieren weiterhin — der Ping
  ist kein Durchblick, nur ein Rundumblick.
- **Hot + Matrix-Navigation-Erfolg: Live-Sicht wie die SL**, inklusive echter
  Namen (kein Alias-Filter). Hält für den Rest des Kampfes, solange Hot
  bleibt — kein erneutes Pingen jede Runde nötig. Schaltet Hot ab, ist die
  Live-Sicht sofort weg (geprüft live gegen `matrixHot`, kein Aufräumcode an
  jeder Hot-Aus-Stelle nötig). Bleibt rein auf dem Bildschirm des Deckers;
  dass er damit seinem Team hilft, ist Ansage am Spieltisch, keine geteilte
  Sicht fürs Tool.
- **Bekannte Lücke:** Hot aus und im selben Kampf wieder an zählt den alten
  Ping-Erfolg weiter mit (kein erzwungener Neu-Ping). Seltener Randfall,
  bewusst nicht behandelt — bei Bedarf später verschärfen.

Gebaut: `battlemap/sicht.py::ping()` (reine Funktion, wie `start_speicher`
aber für ein einzelnes Auge, Kegel ignoriert). `kampf/matrix_routes.py::
navigation()` ruft das nach einem Erfolg für den Decker auf und pingt per
WebSocket-Rundruf sofort (`_tokens_senden`), damit die Karte ohne
Extra-Reload aktualisiert. Hot-Erfolg merkt sich `matrixStand.
matrixLiveSicht` (Person-IDs); `kampf/routes.py::_karte_fuer` liefert diesen
Personen die volle `karten_liste()` statt der gefilterten `ansicht()` —
geprüft gegen das aktuelle `matrixHot` bei jedem Lesen. Frontend:
`MatrixFenster.tsx` zeigt die passende Rückmeldung (nichts/ICE/Ping/Live).

**Verifiziert:** `tests/test_battlemap_sicht.py::TestMatrixPing` (5 neue
Fälle), volle Testsuite ohne neue Fehlschläge (55 vorbestehende, unverändert),
`npx tsc -b` sauber. **Kein Klicktest** — bitte am Spieltisch: Decker mit
Neurolink+Deck, Matrix-Navigation erfolgreich würfeln (einmal normal, einmal
im Hot-Zustand), prüfen dass die eigene Karte sich aktualisiert bzw. bei Hot
komplett live bleibt.

**Gefundener Seiteneffekt, nicht Teil dieser Änderung:** die Kampagnen-
Einstellung `fogOfWar` wird beim Umschalten zwar gespeichert und löscht die
Erinnerung, aber `kampf/routes.py::_fog_an()` (liest die Einstellung) wird
nirgends aufgerufen — die Erinnerungs-Filterung (`ansicht()`) läuft für
Spieler unabhängig vom Schalterstand immer. „Fog of War aus = alle sehen die
Wahrheit“ ist dadurch vermutlich noch nicht wirksam. Nicht im Rahmen dieser
Änderung angefasst, da unabhängiger Fund ohne Bezug zum Ping — separat prüfen.

## Bugfix 06.11.2026 — Fog of War aus zeigte trotzdem nur die Erinnerung

Mark, direkt im Anschluss an den Nebenfund oben: „repariere das bitte mit“.

Ursache: `_fog_an()` las die Kampagnen-Einstellung korrekt, wurde aber
nirgends aufgerufen — `_karte_fuer` filterte für Spieler IMMER über
`ansicht()` (Erinnerung/Kegel), unabhängig vom `fogOfWar`-Schalterstand.

Fix: `_karte_fuer` bekommt einen `fog_an`-Parameter (`_fog_an(kampf)`,
in `_fuer_spieler_kampf` und `_tokens_senden` einmal pro Aufruf geholt, wie
schon bei `live_sicht_ids`). Ist Fog aus, läuft die bereits vorhandene, aber
ebenfalls nie aufgerufene `battlemap/sicht.py::ansicht_waende()`
(360-Grad-Wahrheit, Wände blockieren falls vorhanden, kein Gedächtnis) statt
`ansicht()`. Die Matrix-Hot-Live-Sicht von oben hat weiterhin Vorrang vor
beidem.

**Zweiter Bugfix unterwegs gefunden:** `ansicht_waende()` gab Versteckte
lautlos frei, sobald keine Wand auf der Karte gezeichnet war (`not waende`
sprang vorzeitig auf „alles sichtbar“, noch vor der Versteckt-Prüfung).
Versteckt ist aber ein eigener Schalter, unabhängig von Fog of War oder
Wänden — gefixt: die Versteckt-Prüfung läuft jetzt immer zuerst, Wände
blockieren nur zusätzlich, wenn welche existieren.

**Verifiziert:** `tests/test_battlemap_sicht.py::TestAnsichtWaendeVersteckt`
(3 neue Fälle) und neue Datei `tests/test_kampf_karte_fuer.py` (6 Fälle,
testen `_karte_fuer` direkt: Fog aus zeigt Wahrheit, Versteckt bleibt
trotzdem verborgen, Fog an zeigt weiter Erinnerung, SL sieht immer alles,
Hot-Live-Sicht schlägt beides). Volle Testsuite weiter ohne neue
Fehlschläge (55 vorbestehende), `npx tsc -b` sauber (keine
Frontend-Änderung nötig — der Schalter existiert im Frontend schon).
**Kein Klicktest** — bitte am Spieltisch: Fog of War in den
Kampagnen-Einstellungen ausschalten, prüfen dass Spieler jetzt sofort die
echten aktuellen Positionen sehen (nur Wände/Versteckte bleiben
ausgenommen), dann wieder einschalten und prüfen dass die Erinnerungs-Logik
von oben wieder greift.

## Bugfix 06.11.2026 — Matrix-Ping zeigte nur wenige Tokens, Wände blockierten ihn

Mark: „was leider nicht funktioniert ist der ping mit den Erinnerungen der Positionen, wenn ich nicht hot bin werden mir die leider nicht angezeigt“.

Live-Diagnose auf bebop (echte Kampagne, 10 Teilnehmer, 3 Wandsegmente auf der Karte): der Ping zeigte nur 3 von 10 — exakt die drei, deren Sichtlinie zum Decker nicht durch eine Wand lief. Ursache: zwei Stellen prüften fälschlich auf Sichtlinie.

1. **`ping()` selbst respektierte Wände** wie Rundumsicht. Matrix-Ortung ist aber kein Sichtkontakt (Geräte-/Signatur-Ortung im Netz) — eine Mauer hält kein Funksignal auf. Fix: `ping()` prüft `blockiert()` nicht mehr, nur noch Versteckt.
2. **Selbst ohne Wand-Check in `ping()` hätte der nächste Kartenzug irgendwo auf der Karte die frisch geortete, wandblockierte Position sofort wieder gelöscht** — `aktualisiere()` (läuft bei JEDEM Token-Zug im Kampf, nicht nur beim Decker selbst) prüft serienmäßig, ob eine Wand zwischen Beobachter und gespeicherter Position steht, und verwirft die Erinnerung sonst (das ist die korrekte, gewollte Regel für physische Sichterinnerung — ein Geist hinter einer neu gezeichneten Wand soll verschwinden). Fix: jeder Ping-Eintrag trägt intern ein Flag `matrixGeortet: true` (nie Teil der API-Antwort); `aktualisiere()` lässt Einträge mit diesem Flag beim Wand-Verfallscheck unangetastet, sowohl im Kegel-Durchlauf als auch im zweiten Verfalls-Durchlauf. Versteckt schlägt weiterhin auch ein matrix-geortetes Ziel. Ein frischer Sichtkontakt (Kegel + keine Wand) überschreibt die Markierung ganz normal mit echten Live-Daten.

**Verifiziert:** `TestMatrixPing` erweitert (`test_ping_ignoriert_waende`, `test_ping_ueberlebt_aktualisiere_trotz_wand`), zusätzlich die komplette Live-Szene von bebop (10 Teilnehmer, dieselben 3 Wandkoordinaten) als Python-Reproduktion direkt gegen den Code gefahren — vorher 3/10, nachher 10/10, auch nach einem zweiten `aktualisiere()`-Durchlauf stabil. Volle Testsuite weiter ohne neue Fehlschläge (55 vorbestehende), `npx tsc -b` sauber. **Kein Klicktest** — bitte am Spieltisch erneut prüfen, jetzt mit echten Wänden auf der Karte.

## Textkorrektur 06.11.2026 — Hot-Hinweistext ohne SL-Erwähnung

Mark: der Erfolgstext bei Hot soll nur „Du siehst die Karte live, solange du hot bleibst“ sagen, ohne den Vergleich zur SL. `MatrixFenster.tsx` angepasst, der Rest (ICE-Text, Ping-Text) bleibt.

## Bugfix 06.11.2026 — sichtDa flippte nur per WS, nie per REST (Battlemap blieb leer)

Nach dem Wand-Fix meldete Mark per Screenshot weiterhin: Decker sieht fast niemanden, nur sich selbst. Ein roher WebSocket-Test (genau der Verbindungsaufbau, den der Browser macht) auf `/battlemaps/{id}/live` zeigte: der Server liefert beim Connect sofort alle 11 Teilnehmer korrekt aus — die Backend-Pipeline ist nachweislich fehlerfrei bis auf die Leitung.

Gefundener Rest-Bug im Frontend: `BattlemapPopup.tsx` hält einen Zustand `sichtDa` (Spieler startet mit `false`, GM mit `true`), der beim Rendern der Tokens gilt (`sichtDa && kampf.teilnehmer`). Gesetzt wurde er bisher **nur** von der WS-"tokens"-Nachricht, nicht vom initialen REST-Aufruf `kampfApi.fuerKarte()` — obwohl dessen Antwort für Spieler serverseitig bereits genauso gefiltert ist. Kam der WS-Connect auch nur geringfügig später als der REST-Call, blieb die Karte leer, bis zufällig irgendeine andere Aktion eine neue WS-"tokens"-Nachricht auslöste. Fix: `setSichtDa(true)` jetzt auch im REST-Pfad.

**Verifiziert:** `npx tsc -b` sauber. Rohe WebSocket-Probe gegen den echten Kampf von Mark (10 Teilnehmer, 3 Wände) bestätigt 11/11 auf der Leitung. **Kein Klicktest** — Mark bitte erneut am Tisch probieren (Matrix-Navigation würfeln, Karte öffnen).

## Bugfix 06.11.2026 — dritte Fundstelle: `ansicht()` filterte Ping-Ziele beim Lesen nochmal raus

Trotz der beiden vorherigen Fixes (ping() ignoriert Wände, aktualisiere() lässt matrixGeortet-Einträge beim Wand-Verfall in Ruhe) zeigte `GET /kampf/karte` am echten Tisch live nur den Decker selbst, obwohl der gespeicherte `_sichtSpeicher` nachweislich alle 10 Ziele korrekt mit `matrixGeortet: true` enthielt (per SSH direkt im Container geprüft). Ursache: `battlemap/sicht.py::ansicht()` — die Funktion, die den gespeicherten Speicher beim LESEN in die tatsächliche Teilnehmerliste für die Antwort umwandelt — hat eine DRITTE, von `aktualisiere()` komplett unabhängige Wandprüfung: beim Aufbau der Geister-Liste wird für jeden gespeicherten Schnappschuss nochmal `blockiert()` geprüft, ohne von `matrixGeortet` zu wissen. Diese Stelle hatte ich beim ersten Fix übersehen, weil meine Python-Reproduktion zufällig mit einer Decker-Position getestet hatte, bei der `sieht_live()` für die Testziele schon vorher zugeschlagen hatte.

Gefunden erst durch einen echten Klick-Test im Browser (Login per JWT-Cookie, `document.hidden`-Override gegen den reinen `useKampf()`-Polling-Stillstand, dann Matrix-Navigation wirklich angeklickt) — der Hinweistext kam korrekt ("Ping: Kartenpositionen auf den aktuellen Stand gebracht"), aber `GET /kampf/karte` direkt danach lieferte nur 1 Teilnehmer. Ein SSH-Dump des rohen `_sichtSpeicher` zeigte: Speicher korrekt, Lesepfad kaputt.

Fix: dieselbe `matrixGeortet`-Ausnahme jetzt auch im Geister-Zweig von `ansicht()`.

**Verifiziert:** neuer Test `test_ansicht_zeigt_ping_trotz_wand`, volle Suite weiter ohne neue Fehlschläge (55 vorbestehende), `npx tsc -b` sauber (keine Frontend-Änderung diesmal). **Kein Klicktest durch Mark nötig für diesen Teil** — direkt gegen seinen echten laufenden Kampf per Browser-Klick UND Backend-Dump verifiziert.

## Gebaut 07.11.2026 — Tablet-Hochkant: 90°-Dreh-Button

Mark: auf dem Tablet, am Hochkant gehaltenen Gerät, einen Knopf, der
Battlemap+Grid+alles-darin um 90° dreht, damit man ohne das Tablet
physisch zu drehen mehr von der Karte sieht. Für SL und Spieler gleich.

Rein clientseitige Anzeige-Einstellung, kein Backend-Feld, kein
WebSocket-Sync — jedes Gerät entscheidet für sich. Button „⟳ 90° drehen“
in der Battlemap-Werkzeugleiste (`BattlemapPopup.tsx`), außerhalb des
`istGm`-Blocks, also auch für Spieler sichtbar. Zustand pro Karte in
`localStorage` gemerkt (`bm-gedreht-<karteId>`), damit ein erneutes Öffnen
derselben Karte auf demselben Gerät die Drehung nicht vergisst.

Technik: neuer `.bm-dreh`-Wrapper um Bild-/Grid-/Wände-SVG, Zeichenfläche
und Tokens (alles, was vorher direkt in `.bm-buehne` lag). Normal
deckungsgleich mit der Bühne; gedreht bekommt er per `ResizeObserver`
vertauschte Breite/Höhe und wird mittig per CSS um 90° gedreht — dadurch
füllt er wieder exakt dieselbe Fläche, nur quergestellt. Tap-/Klick-
Koordinaten werden in `schirmNachInnenrahmen()` zurückgerechnet (Inverse
der Drehung: `cx = ly, cy = bühnenBreite − lx`), bevor sie an
`pixelNachHex`/`naechsteEcke` gehen — sonst würde man an der falschen
Stelle klicken. `hexRasterRechteck` bekommt bei gedreht ebenfalls
vertauschte Maße, damit das Grid die quergestellte Fläche komplett füllt.

**Verifiziert:** `npx tsc -b` sauber. Echter Klicktest lokal (GM-JWT,
Dev-Stack): PC-Spawn bei gedrehter Ansicht an eine Bildschirmposition
gesetzt, Marker erschien exakt an dieser Stelle (nicht verschoben/
gespiegelt) — bestätigt die Rückrechnung der Klick-Koordinaten. Noch nicht
mit einem echten Kartenbild und am echten Tablet geprüft.

## Gebaut 07.11.2026 — kein Burgermenü-Punkt für Spieler

Spieler öffnen die Karte nur noch über „Karte öffnen“ im Kampfmenü; der Bereich `battlemap` fehlt in `BEREICHE_STATISCH` (`SpielerAnsicht.tsx`). SL-Menü unverändert. Ohne laufenden Kampf mit angehängter Karte hat ein Spieler keinen Zugang.

## Gebaut 08.11.2026 — Ansicht per Ziehen schwenken, großer Token füllt drei Felder

Mark: großes Token-Bild saß nicht mittig, „Ansicht verschieben“ machte seltsame Dinge. Er schlug vor, den SL-Knopf „Grid schieben“ den Spielern zu geben.

Entscheidung: „Grid schieben“ bleibt SL-only. Es schreibt `originX`/`originY` und verschiebt die Karte für alle (Zeichenebene bleibt stehen). Das Schwenken der eigenen Ansicht geht stattdessen ohne Knopf per Ziehen auf der leeren Karte im Modus „Schieben“, lokal, für SL und Spieler. Der Button „Ansicht schieben“ entfällt. Seltsam war: Raster nur für den ungeschwenkten Ausschnitt, Bühne `overflow: auto` mit Scrollbalken und Treffer-Koordinaten ohne Scrollposition. Jetzt `overflow: hidden`, Raster aus dem sichtbaren Ausschnitt.

Großer Token: Mitte = Schwerpunkt der drei Felder, Bild füllt den Umriss der drei Hex, Blick-Ring um alle drei Felder (9 Ringfelder), Richtung aus dem Winkel Schwerpunkt→Ringfeld. Sicht/Backend unverändert am Ankerfeld. Tablet-Test offen.

## Siehe auch

- [[../concepts/kampf-und-initiative]]
- [[../concepts/drohnen-fahrzeuge]]
- [[../concepts/rassen]]
- [[ui-konzept-commlink]]
