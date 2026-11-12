# PnPTool Wiki Log

> Chronologischer Verlauf aller Wiki-Aktionen. Nur anhängen.
> Format: `## [YYYY-MM-DD] aktion | betreff`

## [2026-11-12] gebaut | Nahkampf-Reichweite im Steckbrief

Feld `reichweite` an Nahkampf- und Handgemenge-Waffen: 1 kurz, 2 mittel, 3 lang. Steckbrief zeigt nur mittel und lang. Siehe [[concepts/kampf-und-initiative]].

## [2026-11-12] gebaut | Spieler-Inventar: Beschreibung und Steckbrief lesen

Knopf „Beschreibung“ an der Inventar-Kachel und im Gegenstandfenster. Readonly-Popup mit Steckbrief und Beschreibung. SL-Notizen bleiben unsichtbar. Siehe [[entities/ui-konzept-commlink]].

## [2026-11-12] update | Neonflackern: Ameisenkrieg wieder sichtbar

Gewürfeltes Rausch-SVG war ein schwarzes Rechteck, overlay auf Schwarz unsichtbar. Intensität hoch, Bild bleibt lesbar. Siehe [[entities/ui-konzept-commlink]].

## [2026-11-11] update | Critter-Pet: Häufchen am Element, Ruß am Display

Siehe [[entities/critter-pet]].

## [2026-11-11] update | Critter-Pet klettert am Burgermenü

Zieht einen Menüpunkt heraus und schläft darauf. Siehe [[entities/critter-pet]].

## [2026-11-11] update | Critter-Pet packen und werfen

3 s halten packt ihn, rauswerfen schickt ihn weiter. Siehe [[entities/critter-pet]].

## [2026-11-11] update | Critter-Pet Feuer länger, Schlaf bis 5 min

Siehe [[entities/critter-pet]].

## [2026-11-11] update | Critter-Pet niest Feuer

Feuerniesen mit Brandflecken zum Wegwischen, Häufchen auch auf Text. Siehe [[entities/critter-pet]].

## [2026-11-11] update | Critter-Pet Übergänge und Text-Flächen

Übergangs-Animationen, mühsames Klettern, Laufen auf Wörtern/Linien/Kästchen. Siehe [[entities/critter-pet]].

## [2026-11-11] update | Critter-Pet klettert und springt

Springt auf Popups, klettert seitlich hoch, schläft oben, klettert am Bildschirmrand. Siehe [[entities/critter-pet]].

## [2026-11-11] update | Critter-Pet erste Ausbaustufe gebaut

Drache läuft über die Party-Tablets, Server-Wandern, Streicheln, Häufchen. Status teilweise-umgesetzt. Siehe [[entities/critter-pet]].

## [2026-11-11] create | Critter-Pet (Tamagotchi)

Skizze vom 24.09. plus Nachschärfung: an Critter gekoppelt, wandert auf andere Displays, Mushu-artiger Pixel-Drache, mehr Animationen. Achsen offen. Siehe [[entities/critter-pet]].

## [2026-11-10] update | Nebenfigur-Fenster macht Händler

Laden direkt im Nebenfigur-Fenster wählen oder abziehen. Siehe [[entities/nebenfiguren]].

## [2026-11-10] update | Nebenfiguren als Händler

Nebenfigur kann Laden-Verkäufer sein, Reparatur-Schalter im Nebenfigur-Fenster.
Siehe [[entities/nebenfiguren]].

## [2026-11-10] update | Nebenfiguren: Platzhalter und Ideenschmiede

Leere Kontakt-Plätze sind schon Nebenfiguren (Migration 014). Ideenschmiede ✨
legt Nebenfiguren an, mehrere auf einmal und mit Verbindung, die KI schlägt
je Figur die Beziehung vor. Siehe [[entities/nebenfiguren]].

## [2026-11-10] neu | Nebenfiguren

Personen ohne Bogen und Inventar, eigenes Burgermenü, kein Kampf. Zu NPC
machen ist eine Einbahnstraße per Charakter-KI. Kontakt-Plätze werden
Nebenfiguren, nur Mentoren volle NPCs. Siehe [[entities/nebenfiguren]],
[[entities/kontakte-messenger]].

## [2026-11-09] rename | Sphären Raum, Chronurgie, Schicksal

Korrespondenz→Raum, Zeit→Chronurgie, Entropie→Schicksal. Auf dem Blatt.
Häretiker bleiben Shu, Chronos, Kali. Gedanken nicht angefasst.
Siehe [[concepts/magie-hexkraft]].

## [2026-11-09] entscheidung | Sphärennamen Raum, Chronurgie, Schicksal

Korrespondenz→Raum, Zeit→Chronurgie, Entropie→Schicksal. Entschieden, nicht
umbenannt. Götter bleiben. Kräfte, Leben, Materie bleiben. Gedanken offen.
Siehe [[concepts/magie-hexkraft]].

## [2026-11-09] rename | Sphäre Geister → Schattenwelten

Der Magier-Name der Sphäre ist Schattenwelten. Häretiker sehen weiter Izanami.
Wesen in den Stufentexten („Geister binden“) bleiben Geister. Punkte, Slots
und Tooltips hängen per Seed-Migration um. Siehe [[concepts/magie-hexkraft]].

## [2026-11-09] feature | Battlemap: ALT-Erinnerung hält drei Runden

Ausgegraute ALT-Tokens verschwanden, sobald man sich wegbewegte oder hinter eine Wand ging. Letzte echte Sichtung bleibt jetzt die laufende Kampfrunde und zwei weitere, auch hinter Wänden. Versteckt löscht sofort, Matrix-Ping läuft nicht nach Runden ab. Siehe [[entities/battlemap]].

## [2026-11-08] feature | Messenger: Chats als Popup, Liste nach letzter Nachricht

Spieler-Chats (Einzel und Gruppe) öffnen wie bei der SL als Popup über der Liste statt als
Vollbild. Die Liste mischt Einzelchats und Gruppen und sortiert nach der letzten Nachricht
(`letzteAktivitaet`), neuester oben. Siehe [[entities/kontakte-messenger]].

## [2026-11-07] feature | Nachrichten-Popup: „Zum Chat“-Knopf

Chat-Mitteilungen verweisen auf ihren Chat (`chatArt`, `chatId`); neben OK öffnet „Zum Chat“
direkt den Einzelchat, Spielerchat oder die Gruppe, für Spieler und SL. Siehe
[[entities/kontakte-messenger]].

## [2026-11-07] feature | Messenger: Gruppenchat (Phase 2) gebaut

Gruppen mit PCs und NPCs gemischt, nur die SL legt sie an und verwaltet Mitglieder
(Schließen umkehrbar, Löschen mit Bestätigung). Die SL schreibt als gewähltes NPC-
Mitglied, Spieler sehen NPCs unter Alias, Portraits wie im Einzelchat. Neue Knoten
`Gruppenchat`, Kanten `TEILNEHMER` und `IN`. Nebenbei: Popup im Einzelchat nennt beim
Spieler nicht mehr den echten NPC-Namen. Siehe [[entities/kontakte-messenger]].

## [2026-11-07] feature | Messenger: Spieler↔Spieler-Chat (Phase 1), Gruppenchat entschieden

Spieler chatten untereinander. Kontakt per Anfrage zwischen den Spielern
(Verhandlungsart `SPIELER_KONTAKT`, Zustimmungs-Popup), je Seite eine
`KENNT`-Kante PC→PC. Die SL sieht und liest nichts mit, wird nicht benachrichtigt.
Gruppenchat (SL legt an, PCs+NPCs gemischt, Dropdown für sprechenden NPC)
als Phase 2 entschieden, nicht gebaut. Siehe [[entities/kontakte-messenger]].

## [2026-11-07] feature | Battlemap: 90°-Dreh-Button fürs Tablet-Hochkant

Knopf „⟳ 90° drehen“ in der Battlemap-Werkzeugleiste, für SL und Spieler
gleich. Rein lokale Anzeige-Einstellung (kein Backend/WS), pro Karte in
localStorage gemerkt. `.bm-dreh`-Wrapper um Bild/Grid/Wände/Tokens,
Pointer-Koordinaten werden per Inverse der Drehung zurückgerechnet.
Echter Klicktest lokal bestätigt die Koordinaten-Rückrechnung. Siehe
[[entities/battlemap]].

## [2026-11-06] bugfix | dritte Fundstelle: ansicht() filterte Ping-Ziele beim Lesen raus

Speicher korrekt (matrixGeortet überall gesetzt), aber ansicht() hat eine
DRITTE, unabhängige Wandprüfung im Geister-Zweig beim Lesen, die davon
nichts wusste. Per echtem Browser-Klicktest + SSH-Dump gefunden. Lehre:
Wand-Check existiert an 3 Stellen (ping/aktualisiere/ansicht), alle prüfen.
Siehe [[entities/battlemap]].

## [2026-11-06] bugfix | sichtDa flippte nur per WS, nie per REST, Karte blieb leer

Roher WS-Test bewies: Backend liefert alle Teilnehmer sofort korrekt.
sichtDa in BattlemapPopup.tsx wurde aber nur vom WS-"tokens"-Push gesetzt,
nie vom (ebenso gefilterten) REST-Fetch — bei langsamem WS-Connect blieb
die Karte leer. Fix: setSichtDa auch im REST-Pfad. Siehe [[entities/battlemap]].

## [2026-11-06] bugfix | Matrix-Ping zeigte nur wenige Tokens, Wände blockierten ihn

Ping respektierte Wände wie Rundumsicht, und aktualisiere() hätte das
Ergebnis beim nächsten Kartenzug sowieso wieder verworfen. Fix:
matrixGeortet-Flag macht Ping-Einträge wand-immun. Live mit echter
bebop-Szene (10 Teilnehmer, 3 Wände) verifiziert: 3/10 -> 10/10. Siehe
[[entities/battlemap]].

## [2026-11-06] bugfix | Fog of War aus zeigte trotzdem nur die Erinnerung

`_fog_an()` wurde nie aufgerufen. Fix: `ansicht_waende()` (bisher auch
ungenutzt) läuft jetzt bei Fog aus, zeigt Wahrheit, Wände/Versteckt bleiben
wirksam. Zweiter Fund: `ansicht_waende` gab Versteckte ohne Wände frei,
jetzt gefixt. Siehe [[entities/battlemap]].

## [2026-11-06] entschieden+gebaut | Battlemap: Matrix-Ping und Hot-Live-Sicht

Matrix-Navigation-Erfolg pingt die eigene Kartenerinnerung (Party teilt nicht,
einmaliger Schnappschuss, Versteckt/Wände bleiben). Hot macht daraus
Live-Sicht wie die SL für den Rest des Kampfes. Siehe [[entities/battlemap]].

## [2026-11-06] gebaut | Battlemap: Wände auch ohne Fog, Blick per Nachbarfeld

Spieler sehen die SL-Linien. Dahinter ist nichts, auch wenn Fog of War aus ist.
Blickrichtung: eigenen Token antippen, Nachbarfeld antippen. Siehe [[entities/battlemap]].

## [2026-11-06] gebaut | Battlemap: Sichtlinien blockieren auch Rundumsicht

SL-Modus Wand, Linien an der Karte. Fog of War wertet sie mit, auch bei
360-Grad. Siehe [[entities/battlemap]].

## [2026-11-06] gebaut | Battlemap: Fog of War optional

Schalter in den Einstellungen, Standard aus. Letzte Sicht, Verstecken,
Rundumsicht an Rasse und verbautem Chrom. Klicktest offen. Siehe
[[entities/battlemap]].

## [2026-11-06] entschieden | Battlemap: Blickrichtung und letzte Sicht

Halbkreis nach vorn, Startstand friert hinten. Umschauen, dann bewegen.
Augen: eigener Charakter, eigene Drohnen, eigene Beschwörungen. Verstecken
im Namens-Chip. Kein Kampf-Schalter. Nicht gebaut. Siehe [[entities/battlemap]].

## [2026-11-06] skizziert | Battlemap: Blickrichtung, Verstecken, letzte Sicht

Idee, nicht entschieden. Widerspricht der Ausschluss-Zeile zu Facing und
Fog of War, die stehen bleibt. Achsen offen. Siehe [[entities/battlemap]].

## [2026-11-06] nachgezogen | Battlemap-Größe: Checkbox an der Person

Rasse bleibt die Vorlage. Checkbox „Groß“ auf PC- und NPC-Kachel entscheidet.
Karte liest `Person.istGross`. Siehe [[entities/battlemap]].

## [2026-11-06] nachgezogen | Battlemap-Größe nur an der Rasse

Schalter von den PC-/NPC-Kacheln weg. Baukasten bleibt. Karte liest
`Rasse.istGross`. Siehe [[entities/battlemap]].

## [2026-11-06] gebaut | Battlemap mit Ort/Event verknüpfbar, Karte öffnen für Spieler

Neue Listenfelder `ortIds`/`eventIds`, rein organisatorisch, kein Auto-
Anhängen beim Kampfbeginn. Spieler bekommen denselben „Karte öffnen“-Knopf
wie die SL, rechtsbündig neben der Rundenanzeige. Siehe [[entities/battlemap]].

## [2026-11-06] gebaut | Battlemap: Party-Hex blau, Raster füllt Ecken

Aktive Party (inkl. NPCs/Drohnen dabei) leuchtet blau wie Spawn, andere NPCs
magenta. Grid rechteckig, Fenster breiter. Siehe [[entities/battlemap]].

## [2026-11-06] gebaut | Battlemap: Zeichnen + Spawn ohne Kartenwahl

Grid-SVG blockierte den Stift. Kampf ohne `battlemapId` spawnte nicht —
Öffnen der Karte hängt sie an. Siehe [[entities/battlemap]].

## [2026-11-06] gebaut | Critter als Vorlage, Kopieren mit Bild/Bogen/Gegenständen

`Person.istVorlage` markiert einen Critter als Muster. Kopieren übernimmt
Name/Bild/Charakterbogen 1:1, dazu unabhängige Kopien aller Gegenstände
(`items/repository.py::assign_copy`). Kopie startet unverbunden, unbeschadet,
Sichtbarkeit ALLE. Siehe [[concepts/attribute-und-fertigkeiten]].

## [2026-11-06] gebaut | Battlemap-Tokens live (Zugwechsel, neue Teilnehmer)

Rundruf enthält Portrait und neue Tokens. Kampfmodus „Karte öffnen“.
Siehe [[entities/battlemap]].

## [2026-11-06] gebaut | Battlemap Grid-Ursprung, Drohnen-Tokens

SL schiebt den Hex-Ursprung. Größe-Schalter auf den Kacheln zeichnet neu.
Spieler schiebt eigene Drohnen/Beschwörungen. Siehe [[entities/battlemap]].

## [2026-11-06] gebaut | Battlemap (Hex, Tokens, Live-Zeichnen)

Eigenes Modul, Whiteboard bleibt getrennt. Burgermenü, Kampf hängt eine Karte
an, Spieler schiebt eigenen Token am Zug. `istGross` an Person und Rasse.
Klicktest offen. Siehe [[entities/battlemap]].

## [2026-11-06] nachgeschärft | Battlemap: Spawn, Randfarben, Belegung, Größe

Zwei Spawn-Felder auf der Karte (Blau PC, Magenta NPC). Rand `--p-blau` /
`--p-magenta`, am Zug `--p-gold` plus Hot-Puls. Zwei Tokens nicht auf einem
Hex. Drohne/Beschwörung auf freiem Nachbarfeld. `istGross` an Person und
Rasse, Default Normal. Nicht gebaut. Siehe [[entities/battlemap]].

## [2026-11-06] nachgeschärft | Battlemap: Grün bis Loslassen, Startfeld grau, Fliegen ×2

Grün nur während des Drags, bleibt bis Mouseup. Das Anheb-Feld bleibt grau,
bis der Teilnehmer nicht mehr am Zug ist. Drohnen-Reichweite `3 + Fliegen × 2`
(ersetzt `3 + Fliegen`). Nicht gebaut. Siehe [[entities/battlemap]].

## [2026-11-06] entschieden | Battlemap-Design (nicht gebaut)

Whiteboard bleibt getrennt, Leinwand wird kopiert (Bild, Live-Zeichnen,
Spieler-Mitzeichnen, skalierbares Hex-Grid). Burgermenü bereitet Karten vor,
Kampf hängt eine an. Drop überall, Grün nur Hilfe, Spieler nur am eigenen Zug.
Große Monster: 3 Felder im Y plus Kreis, 4-Felder-Idee ersetzt.
Siehe [[entities/battlemap]].

## [2026-11-06] skizziert | Battlemap (Hex, Tokens aus der Initiative)

Neue Seite [[entities/battlemap]]. Whiteboard nicht erweitern. Tokens am
Kampf, Karte als eigenes Asset. Fünf Achsen offen (Drop hart/weich, nur am
Zug, 4-Hex-Form, Einstieg, Unterlage). Nicht gebaut.
Siehe [[concepts/kampf-und-initiative]].

## [2026-11-06] gebaut | Kampfkarte: Parade der Nahkampfwaffe, Schaden inkl. Körperkraft

Große Parieren-Kachel zeigt die ausgerüstete Nahkampfwaffe (Pistole kann
nicht parieren). Nahkampf-Schadenszeile rechnet Körperkraft in die Zahl.
Siehe [[concepts/kampf-und-initiative]].

## [2026-11-06] gebaut | Shop-Preis zieht nach, wenn der Gegenstand sich ändert

KI-/Unikat-Anlegen fror den Preis erneut auf der `VERKAUFT`-Kante ein,
GET-Sortiment konnte im Browser hängen, der Sortiment-Editor lud nicht
nach. Jetzt live `g.preis`, Fetch `no-store`, Editor pollt.
Siehe [[concepts/waehrung-und-preise]].

## [2026-11-06] gebaut | Shop-Bild-Großansicht zeigt das ganze Bild

Hochformatige Warenbilder im Großansicht-Popup wurden oben/unten
abgeschnitten: Klasse `.bg-bild` gehörte den Begleitern (`cover`, 220px).
Jetzt `.bild-gross` mit `object-fit: contain`, skaliert in die Schale.
Normaler Shop hat denselben Klick im Kauf-Fenster.

## [2026-11-05] gebaut | I.C.E.-Upgrade auch an der Riggerkonsole

Montiert zählt der Bonus wie beim Cyberdeck auf das I.C.E. der Person.
Ohne Commlink bleibt sie offline. Siehe [[concepts/augments-ausruestung]].

## [2026-11-05] gebaut | Upgrade hebt I.C.E., Commlink ist Träger

Upgrade-Material hat ein I.C.E.-Feld. Montiert zählt es am Commlink, am
Cyberdeck und an Drohne/Fahrzeug. Commlink bekommt Upgrade-Slots. Siehe
[[concepts/augments-ausruestung]].

## [2026-11-05] gebaut | Waffe nicht hackbar

Vierte Option beim Deaktivieren: Nicht hackbar. Die Waffe und ihre
Upgrades stehen nicht in der Hack-Liste. Siehe
[[concepts/neuroweaving-decking]].

## [2026-11-05] gebaut | Initiative per Klick eintragen

Klick auf die Initiative-Zahl trägt die Erfolge ein. Charakter und Drohne
kommen damit in die Liste, wenn sie noch nicht drin sind. Siehe
[[concepts/kampf-und-initiative]].

## [2026-11-05] gebaut | Kampfmenü ohne drei Zeilen

Ansage von hinten, Schutz und Schaden, Würfeln sind aus der Kampfansicht.
Pools, Waffen und der Umschalter bleiben. Siehe [[concepts/kampf-und-initiative]].

## [2026-11-05] gebaut | Nebenwirkungs-Schaden ist normaler Schaden

Schlag, tödlich und schwerheilbar landen auf den bestehenden Spuren. Die
2-Rasten-Uhr für tödlichen Crash-Schaden startet nicht mehr. Siehe
[[entities/drogen]].

## [2026-11-05] gebaut | Drogen-Umbauen: Wirkung und Nebenwirkung getrennt

Im Umbauen einer Droge steht die Wirkung oben, darunter eine dicke Linie und dieselben Würfelzeilen für die Nebenwirkung. Der Zeitraum der Nebenwirkung folgt weiter der Wirkung. Siehe [[entities/drogen]].

## [2026-11-04] gebaut | Drogen schlucken

Schluck am eigenen Gegenstand, SL an allem. Heilung, Willenskraft, Crash,
Szenenwechsel, Rast. Gift an einer anderen Person im Kampf bleibt später.
Siehe [[entities/drogen]].

## [2026-11-04] entschieden | Drogen: Crash wandelt Schaden um, Rast zählt mit

Nebenwirkung kann vorhandenen Schlag zu tödlich machen, oder Schlag und
tödlich zu schwerheilbar. Kein neuer Schaden. Die Rast, die den Crash
startet, ist Tick 1 der 2-Rasten-Uhr. Umwandeln vor der Heilung derselben
Rast. Siehe [[entities/drogen]].

## [2026-11-04] entschieden | Drogen: Reduktion und Heilreihenfolge

Halbieren wird Reduktion auf der aktiven Rüstung, nicht eine neue Funktion.
Schlag und schwerheilbar sind Schaden. Hochwertig heilt schwerheilbar mit
der Menge, Schlag und tödlich komplett. Normal: tödlich zuerst, Rest × 3
Schlag. Offen bleibt nur die 2-Rasten-Zählung. Siehe [[entities/drogen]].

## [2026-11-04] entschieden | Drogen schlucken, nicht gebaut

Wirkung sofort, Szene oder Rast. Nebenwirkung danach. Chrom-Funktionen,
kein eigener Heiltrank-Typ. Willenskraft-Ausnahme und tödliche Schwere als
2-Rasten-Uhr entschieden. Heilreihenfolge und Schaden-halbieren offen.
Siehe [[entities/drogen]].

## [2026-11-04] gebaut | SL bekommt Booster- und Hot-Popups für NPCs

Kommt ein NPC mit Reflex-Booster, Matrix-Hot oder Hot-Drohne dran, fragt
dasselbe Fenster die SL. Spielercharaktere entscheiden weiter selbst. Siehe
[[concepts/kampf-und-initiative]] und [[concepts/drohnen-fahrzeuge]].

## [2026-11-04] gebaut | Werkbank: Drohnen-Reparatur aktualisiert die Anzeige sofort

Nach bestätigter Reparatur blieb der Gesundheitsstand im Fenster und auf der
Kachel der alte Schnappschuss, das Material war schon weg. Siehe
[[concepts/drohnen-fahrzeuge]].

## [2026-11-04] gebaut | Unverbautes Chrom mit natürlicher Rüstung bleibt umlegbar

`istNatuerlich` an noch nicht eingesetztem Cyber-/Bio-/Hexware sperrt nicht
mehr Ablage, Besitzwechsel oder Tutorial-Rückgabe. Erst `verbaut` macht es
zum Körperteil. Siehe [[concepts/cyberware-bioware]].

## [2026-11-04] gebaut | Ring-Rätsel: Umbenennen-Route entfernt

Stift-Knopf, Popup und `POST /raetsel/name` entfernt — Räume haben gute feste
Namen, sollen nicht mehr aus Versehen umbenannt werden. Backend-Feld `namen`
bleibt. Türkise Neonkante bei Spielern war schon vom 03.11. gefixt, nur
Mark-seitiges Caching. Siehe [[entities/ring-raetsel]].

## [2026-11-03] gebaut | Ring-Rätsel: Praxistest-Korrekturen

Namensfeld im Popup breiter. Neonkante (zeigt zur Mitte) nur noch für die SL
sichtbar. Fester Ausgang ersetzt durch freie Mehrfachmarkierung (aus/blau/rot
pro Feld, beliebig viele, ohne Logik). Räume ohne eigenen Namen zeigen
automatisch `<Identität>-<aktuelles Feld>`, live mit der Drehung. Siehe
[[entities/ring-raetsel]].

## [2026-11-03] gebaut | Ring-Rätsel: zwei Ebenen (Mittel), feste Ausgänge, Umschalter

Umschalter Leicht/Mittel. Mittel: 16 Räume, zwei Ringe nebeneinander, Tür zu
wechselt abwechselnd Ebene oder dreht beide Ringe. Pro Ring ein fester Ausgang
(Feld, nicht Raum), nur der SL sieht ihn, Markierung in der Mitte bei „Ziel“.
Siehe [[entities/ring-raetsel]].

## [2026-11-03] gebaut | Ring-Rätsel, eine Ebene

Burgermenü-Tafel: acht Räume, Tür zu dreht gegen den Uhrzeigersinn, Lage der
Gruppe extra. Spieler sehen nach Freigabe nur zu. Zwei Ringe nicht gebaut.
Siehe [[entities/ring-raetsel]].

## [2026-11-01] gebaut | Fertigkeiten-Erstellung: alle Punkte auf einmal zurück

Im Fertigkeiten-Fenster sitzt ein × links neben den Punkten und nimmt den
ganzen vergebenen Slot zurück. Feste Rassenpunkte bleiben. Siehe
[[concepts/charaktererschaffung]].

## [2026-11-01] gebaut | Matrix-Schlagschaden an Drohnen

Decker und Neuroweaver können eine Drohne schalten oder den Überschuss als
Schlagschaden buchen, ohne Rüstung. Fahrzeug bleibt beim Schalten. Hot-Rigger
nimmt die Hälfte, bei 0 Gesundheit Dumpshock. Automata ist kein eigener Typ.
Siehe [[concepts/neuroweaving-decking]] und [[concepts/drohnen-fahrzeuge]].

## [2026-11-01] gebaut | Decker-Hot bleibt bis zur Bleiben-Frage

Der Knopf schaltet nur ein. Beim nächsten eigenen Zug zuerst „Hot bleiben?“.
Nein klinkt aus, die Zusatzaktion aus dem Deck kommt dann nicht. Siehe
[[concepts/drohnen-fahrzeuge]].

## [2026-11-01] gebaut | Hot im eigenen Zug fragt nach der Zusatzaktion

War der Decker schon dran und ging erst dann Hot, kam die Booster-Frage nicht.
Der Klick holt den Stand neu und öffnet dasselbe Fenster, solange noch eine
Zusatzaktion frei ist. Siehe [[concepts/drohnen-fahrzeuge]].

## [2026-11-01] gebaut | Upgrade-Material: Booster im Umbauen, ein Ziel-Menü

Initiative-Bonus und Zusatzaktionen stehen beim Upgrade-Material im Umbauen,
dieselbe Auswahl wie beim Chrom. Im Besitz bleibt ein Dropdown „Passt an“.
Siehe [[concepts/augments-ausruestung]].

## [2026-11-01] gebaut | Overclock in der Kampfkarte

Neben den NeuroWeaving-Funktionen, gleiches Format, Würfel sichtbar.
Willenskraft legt man als Bonuswürfel drauf, auch in den Matrix-Fenstern.
Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] gebaut | Neuroweaver-Hack und Hot-Decker-Schaden

Im Kampf ist die restliche Willenskraft das ICE des Neuroweavers. Überschuss
wird Schlagschaden, ohne Deckel 3, ohne Rüstung, nichts an ihm schalten.
Ein Decker im Matrix-Hot wählt: schalten oder denselben Überschuss als
Schlagschaden. Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] gebaut | Gehacktes Deck zieht von allein nach

Kampfkarte und Charakterblatt holen die Deck-Sperre alle drei Sekunden.
Auf der Karte steht „aus“, auf dem Blatt verschwindet die Zeile. Beides
kommt wieder, ohne Neuladen.
Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] gebaut | Decker-Hot neben Cyberdeck

Der Knopf hing neben der Runde. Jetzt in der eigenen Kampfkarte neben der
Überschrift Cyberdeck, sobald Cyberkampf an ist.
Siehe [[concepts/drohnen-fahrzeuge]].

## [2026-11-01] gebaut | Neuroweaver schaltet Kampf/Cyberkampf

Dieselben Knöpfe wie beim Decker, auch ohne Deck. Cyberkampf zeigt die
NeuroWeaving-Pools, der feste Block darunter ist weg.
Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] teilweise-umgesetzt | Hot endet mit Konsole oder Neurolink

Konsole aus: Drohnen fallen und der Drohnen-Hot ist weg, Matrix-Hot bleibt.
Kommt die Konsole wieder, ist der Sprung wieder da. Initiative nicht.
Neurolink aus: beides Hot ist weg und bleibt zu. Die Drohnenkarten holen
den Stand alle drei Sekunden.
Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] teilweise-umgesetzt | Deaktivieren kommt beim Ziel an

Umbau-Feld an der Waffe: komplett oder nur Upgrades, Standard nach Typ.
Kampfkarte des Ziels zeigt eine komplett ausgeschaltete Waffe als tot.
Offen bleibt die Ki-Tama-Zeile in der Hack-Liste.
Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] teilweise-umgesetzt | Deaktivieren im Kampf

Fenster an Brute Force, Schleichen, Navigation und Electronic Warfare.
ICE-Pool, Aufteilung, Sicht, EW-Bonus, Deck-Sperre, Drohnen fallen bei
Konsole. Offen: Waffen-Feld, Ki-Tama-Zeile, Kampfkarte blendet nicht aus.
Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] entschieden-nicht-umgesetzt | Erfolge aufteilen, nicht koppeln

Mark: jeder Netto-Erfolg ist entweder ein Ziel mehr oder eine Runde mehr.
2 Erfolge: 1 Ziel für 2 Runden oder 2 Ziele für 1 Runde. 3 Erfolge können
2 Ziele sein, eines 2 Runden und eines 1. Nicht gleich viele Ziele für
gleich viele Runden. Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] entschieden-nicht-umgesetzt | Navigation-Probe zeigt gegnerisches ICE

Mark: Matrix-Navigation ist eine Probe, die Sicht hält den Kampf.
Ungesehener Gegner steht in der Liste, Zahl verdeckt, nicht klickbar.
Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] entschieden-nicht-umgesetzt | Deaktivieren-Fenster und Punktebudget

Mark: Brute Force oder Schleichen öffnet die Teilnehmer mit ICE. Probe
eintragen, bei Netto ab 1 das zweite Fenster mit Schaltern 1/2/3 und
freien Punkten. Bestätigen übernimmt, Zurücksetzen verwirft nur die
Schalter. „Dieselben Erfolge für Ziele und Runden, höchstens 9“ ist
ersetzt. Party-ICE immer sichtbar, Gegner-ICE nach Matrix-Navigation.
Offen: Wurf und Dauer der Sicht, ungesehene Gegner. Siehe
[[concepts/neuroweaving-decking]].

## [2026-11-01] entschieden-nicht-umgesetzt | EW-Bonus hält 3 Runden

Mark: der Electronic-Warfare-Bonus auf dem ICE hält 3 Kampfrunden. In
diesen Runden füllt sich der Pool auf Maximum plus Bonus auf. Die Tarnung
bleibt der Soforteffekt. Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] entschieden-nicht-umgesetzt | ICE-Pool und EW +1 je 2 Erfolge

Mark: ICE nimmt im Kampf Schaden wie Gesundheit und füllt sich jede
Kampfrunde vollständig auf. Zwei Angriffe in der Runde sehen den Rest.
EW hebt das Party-ICE um +1 je 2 Erfolge, auch über dem Maximum. Der
+3-Deckel ist ersetzt. Offen nur, ob der Bonus im Kampf den Soforteffekt
teilt. Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] entschieden-nicht-umgesetzt | Deaktivieren: Netto-Erfolge

Mark: die Zahl ist Erfolge minus ICE, höchstens 3, unter 1 passiert
nichts. Damit ist die Deaktivieren-Skizze entschieden, nicht gebaut.
Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] entschieden-nicht-umgesetzt | Deaktivieren, vierte Runde

Mark: Einstieg über Brute Force oder Schleichen, Wurf gegen das ICE.
Ohne ICE Schwelle 0, Deckel bleibt 3 Ziele und 3 Runden, höchstens 9.
EW dieselbe Probe, Party-ICE +Erfolge max 3, Tarnung bleibt. Feind läuft
aus, Ziel merkt es, SL sieht es. ICE-Wurf ist die ganze Probe. Offen nur
noch die Verrechnung der Erfolge am ICE. Siehe
[[concepts/neuroweaving-decking]].

## [2026-11-01] entschieden-nicht-umgesetzt | Deaktivieren, dritte Runde

Mark: dieselben Erfolge für Zielzahl und Dauer, beides höchstens 3. Der
Wahl-Satz ist ersetzt. Schusswaffe komplett, alles andere nur Upgrades.
Nur im Kampf. Jeder Decker oder Neuroweaver der Party schaltet eigene
Leute wieder an. Electronic Warfare kommt zur Tarnung dazu, Höhe offen.
Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] entschieden-nicht-umgesetzt | Deaktivieren, zweite Runde

Mark: Schalter an jeder Waffe, Default nach Typ, Typ-Map außer Schusswaffe
offen. Ki-Tama im Nur-Upgrades-Modus hängt an der Waffe, Default aus. Kein
ICE ist doch ein Wurf. Konsole weg, gesprungene Drohnen fallen sofort.
Ausgabe der Erfolge: zwei Sätze, nicht zusammengezogen (Wahl oder beides).
Siehe [[concepts/neuroweaving-decking]].

## [2026-11-01] notiz | Critter und NPCs kopieren, offen

Mark will Critter und NPCs kopieren können, für 0815-Mobs. Was mitkopiert
wird, ist offen. Personen haben keinen Kopier-Weg, Gegenstands-Vorlagen
schon — nicht verwechseln. Siehe [[entities/neo4j-datenmodell]].

## [2026-11-01] notiz | Ifrit/Shiva, Blizzard/Inferno/Feuer/Eis, offen

Mark: Ki-Tamas und Rüstung von Ifrit und Shiva, dazu Blizzard, Inferno,
Feuer, Eis. Zuordnung und Datenmodell offen. Siehe
[[concepts/augments-ausruestung]].

## [2026-11-01] gebaut | Undefinierter Mentor in der Chatliste

Mentor-Punkte legen „Undefinierter Mentor“ unter ◍ Kontakte. Beschreibung
erzeugt den NPC, 20 EP je Punkt gehen auf vorhandene Werte. Siehe
[[entities/hintergrund-baukasten-feature]].

## [2026-11-01] gebaut | Undefinierter Kontakt in der Chatliste

Leere Plätze aus dem Kontakte-Hintergrund stehen unter ◍ Kontakte, nicht
nur offene Chats. Erster Klick beschreibt, die KI legt den Kontakt an.
Siehe [[entities/kontakte-messenger]].

## [2026-11-01] gebaut | Magenta-Puls halb so stark wie Gold

Mark nach dem Sehen: Gold bleibt, hervorheben soll sichtbar leuchten und
pulsieren, etwa die Hälfte vom Gold. Siehe [[entities/auth-und-rollen]].

## [2026-11-01] gebaut | Signifikanz vorgefertigter Charaktere

SL setzt am Häkchen Normal, hervorheben oder Wichtig. Magenta- bzw.
Gold-Puls, Sortierung wichtig zuerst. Siehe [[entities/auth-und-rollen]].

## [2026-11-01] gebaut | Ki-Tama-Kachel verschwindet nach dem Ruf

Verbrauchte Beschwörung ohne Critter in der Initiative zeigt nicht mehr
„Diesen Kampf schon gerufen“. Die Kachel ist weg, der Abschnitt auch, wenn
nichts mehr zu rufen oder zu öffnen ist. Siehe [[concepts/augments-ausruestung]].

## [2026-11-01] gebaut | Häretiker in der Vorgefertigten-Auswahl

Die Auswahl zeigt „Häretiker“, wenn `magieFlavor` so steht. `weg` bleibt
`MAGIER`. Liste, Karte und Steckbrief. Siehe [[entities/auth-und-rollen]].

## [2026-11-01] gebaut | Ki-Tama-Beschwörung einmal pro Kampf

Gelungener Ruf und Patzer schreiben die Item-ID an den Kampf
(`verbrauchteBeschwoerungen`). Fehlwurf nicht. Knopf bleibt auch nach Ablauf
der Runden weg. Siehe [[concepts/augments-ausruestung]].

## [2026-10-31] gebaut | Parade-Bonus an der Waffe

Extra-Würfel nur beim Parieren mit genau dieser Waffe, nicht auf den Angriff
und nicht auf die globale P-Zahl. Schild = Schaden 0 + Parade-Bonus.
Mindeststärke besprochen und verworfen. Siehe [[concepts/kampf-und-initiative]].

## [2026-10-31] gebaut | Spieler setzen Drohnen- und Gegenstandsbilder, Zeichnen neben Upload und KI

Mark als Spieler: Bild an der Drohne scheiterte mit „GM role required“.
Dieselbe Sperre lag auf Gegenstandsbildern. Rigger darf das Bild der eigenen
Drohne/des eigenen Fahrzeugs setzen und leeren, Spieler das Bild der eigenen
Ausrüstung (eigener Kreis). Überall wo hochgeladen oder per KI erzeugt wird,
liegen jetzt Skizze und Zeichentisch daneben. Siehe [[concepts/drohnen-fahrzeuge]].

## [2026-10-31] gebaut | Drohnen-Umbau: Attributnamen ausgeschrieben, Blatt nur Fertigkeiten mit Punkten

Mark im Drohnen-Umbau: „Stär…“ und zwei „Ges…“ waren nicht zu lesen.
`.lu-wert` stapelt den Namen über die Punkte (Umbau, Level-Up, Weitere
Fertigkeiten). Charakterblatt einer Drohne/eines Fahrzeugs blendet
Fertigkeiten und Zusatzfertigkeiten ohne Punkte aus; der Katalog bleibt im
Umbau. Siehe [[concepts/drohnen-fahrzeuge]].

## [2026-10-29] gebaut | Werkbank: Rüstungs-Reparatur ebenfalls Self-Service, Spieler-Werkbank bekommt Reparatur-Reiter

Mark: "ja bitte unbedingt! das war alles für die Spieler gedacht!" —
`ruestung/reparieren-material` war `require_campaign_gm`, jetzt
`_eigener_kreis`-geprüftes Self-Service wie das Drohnen-Pendant (das schon
immer so war). Händler-Weg und manuelle Kästchen-Eintragung bleiben
bewusst SL-only (Verhandlungs-Modell bzw. Sonderfall-Weg, kein Versehen).
`ReparaturFenster.tsx` bekommt `erlaubeHaendler`-Prop, neue
`werkbank/ReparaturUebersichtSpieler.tsx` + `WerkbankUebersichtSpieler.tsx`
(zwei Reiter Reparatur/Augments für Spieler, eigener Drohnen-Fetch).
`pytest`/`tsc -b` grün. Siehe [[concepts/augments-ausruestung]].

## [2026-10-29] gebaut | Werkbank-Augments: Self-Service für Spieler statt GM-only

Korrektur nach Marks Hinweis ("natürlich war das für die Spieler
gedacht... damit das für sie dann auch angezeigt wird, und ihre
Materialien verwendet werden"): Montieren/Demontieren/Reparieren waren
`require_campaign_gm`, jetzt Besitz-geprüftes Self-Service
(`_eigener_kreis`, wie Ablage/Besitzer-Wechsel) — Ziel UND Material müssen
im selben Besitzkreis liegen wie das Augment. Neuer Spieler-Bereich
"Werkbank" (nur Augments, kein Reparatur-Reiter — dafür existiert bis
heute keine Spieler-UI). Drohnen-Ziel-Liste beim Montieren filtert jetzt
auf denselben Rigger statt alle Kampagnen-Drohnen anzubieten. `pytest`/
`tsc -b` grün. Siehe [[concepts/augments-ausruestung]].

## [2026-10-29] gebaut | Werkbank-Augments Nachbesserung: eigener Typ "Upgrade-Material", Slot-Feld sichtbar gemacht

Marks erster Klicktest: eigener Gegenstandstyp "Upgrade-Material"
(🔩) in der Kachel-Auswahl ergänzt (reiner Frontend-Katalogeintrag).
Bugfix: Upgrade-Slots-Feld sass hinter dem eingeklappten
"Optionen"-Schalter und war unauffindbar — jetzt direkt neben Seltenheit
sichtbar für Waffe/Rüstung/Cyberdeck/Riggerkonsole. `tsc -b` grün. Siehe
[[concepts/augments-ausruestung]].

## [2026-10-29] gebaut | Werkbank-Augments: Montieren/Demontieren/Reparieren für Waffe/Rüstung/Cyberdeck/Riggerkonsole/Drohne/Fahrzeug

Zweiter Baustein der Werkbank nach der Reparatur (siehe Eintrag direkt
darunter). Neues `upgradeSlots`-Feld (0–6) an Gegenstand
(`AUGMENT_TRAEGER_TYPEN`: Waffe/Rüstung/Cyberdeck/Riggerkonsole) und an
Person (Drohne/Fahrzeug). Augment-Gegenstände (`istAugment=true`)
montieren sich über eine neue `:MONTIERT_AN`-Kante (Ziel: Gegenstand ODER
Person) an ein Ziel mit freiem Slot; Bonus steckt im wiederverwendeten
`traitBoni`-Feld. Montieren/Demontieren: Maker- oder Handwerk-Probe (frei
wählbar), benötigte Erfolge = Level+1. Patzer beschädigt das Augment
(`defekt=true`); Reparatur wiederverwendet exakt die Reparatur-Formeln aus
`kampf/ruestung.py`, nur mit Level statt Materialmenge/fehlenden Kästchen.
Backend: `items/augments.py` (neu), `items/repository.py`/`routes.py`
erweitert, `entities/schemas.py`/`repository.py` um `upgradeSlots`
ergänzt. Frontend: Burgermenü "Reparatur" zu "Werkbank" umbenannt
(`werkbank/WerkbankUebersicht.tsx`, zwei Reiter), neue
`werkbank/AugmentUebersicht.tsx`/`AugmentFenster.tsx`.
`pytest`/`tsc -b` grün, kein Klicktest. Siehe
[[concepts/augments-ausruestung]].

## [2026-10-29] gebaut | Reparatur-Burgermenü: Material-Stufen, Erfolgsformel

Backend: `kampf/ruestung.py` neue Formeln (Materialmenge−1/Min.1,
feste Kästchen-Wirkung je Qualität, Gesundheitsheilung Drohne/Fahrzeug),
alte Erfolgs-Überschuss-Formel entfernt. Neue Routen für Rüstung (GM-only)
und Drohne/Fahrzeug (Self-Service wie Umbau). Neues Händlerflag
`bietetReparatur`. Frontend: eigenständiges Burgermenü „Reparatur" ersetzt
die alte im Gegenstands-Popup versteckte UI. Händler-Nuyen-Weg nur für
Rüstung gebaut. `pytest`/`tsc -b` grün, kein Klicktest. Siehe
[[concepts/drohnen-fahrzeuge]].

## [2026-10-29] entschieden | Reparatur-System: Material-Stufen, Erfolgsformel, Burgermenü

Im Chat mit Mark das generische Reparatur-Feature (Rüstung/Drohne/Fahrzeug)
fertig ausgearbeitet, noch nicht gebaut. Eigenständiges Burgermenü
„Reparatur" (Ziel-Slot + Material-Slot) statt Verstecken im
Gegenstands-Popup. Material-Qualität (`istMaschinenteil`/
`maschinenteilQualitaet`) bekommt im Reparatur-Kontext eigene Bedeutung:
hochwertig = 1 Stück repariert vollständig, normal = 5 Kästchen/Stück,
minderwertig = 1 Kästchen/Stück — mehrere Stück EINER Qualität pro Versuch
kombinierbar, kein Mischen verschiedener Qualitäten. Löst die alte
Erfolgs-Überschuss-Formel ab: benötigte Erfolge = eingesetzte Materialmenge
− 1 (Minimum 1), 3 Buttons wie beim Maker-Umbau (Erfolg/Misserfolg/Patzer).
Probe-Pool ist je Ziel verschieden: Rüstung nur Handwerk, Drohne nur Maker
(Hardware), Fahrzeug Handwerk ODER Maker (Hardware) nach Wahl. Händler-Weg
bleibt Nuyen+Verhandlung (`haendler_reparatur_preis` als Vorschlag, SL kann
ihn im Popup ändern), neu ist nur die Freischaltung über das Händlerflag
`bietetReparatur`. Siehe [[concepts/drohnen-fahrzeuge]] „Reparatur".

## [2026-10-29] fix | Hot-Drohne im Kampf wieder antippbar

Der Slot zeigte den Steckbrief nicht und der Klick tat nichts, sobald die
Drohne Hot aus der Initiativliste gefaltet war. Kleines Feld zeigt GS/TN/TS/A/P/I,
Klick öffnet den großen Steckbrief.

## [2026-10-28] gebaut | Hot-Proben und Dumpshock

Solange Hot: Geschick plus gedeckeltes Riggen, Fahren/Fliegen der bessere Wert,
Intelligenz und Geistesschärfe vom Rigger. Anzeige, nicht gespeichert.
Dumpshock: Hot-Drohne auf 0 Gesundheit löst die Verbindung, Rigger setzt den
Rest der Runde aus. Kein extra Würfelwurf.

## [2026-10-28] update | Hot-Slots im Kampf, Name neben dem Rigger

Hot-Drohne teilt den Initiative-Slot des Riggers (Name daneben, kein Magenta
dort). Magenta nur an der Slot-Box. Kampf bekommt dieselbe Slot-Reihe wie
Drohnen & Fahrzeuge, Hot-Knopf unter der Box, eine Drohne pro Runde. Andere
Drohnen bleiben selbstständig, der Spieler würfelt sie mit ihren eigenen
Werten.

## [2026-10-28] update | Hot-Knopf, Ampel, magenta pulsierende Drohne

Mark schließt die offene Risiko-Frage: Decker-Hot zieht Ampel und zweiten
Initiative-Wurf mit, aber erst nach einem eigenen Hot-Knopf im Kampf
(Decker und Rigger). Rigger haben den Knopf zusätzlich unter Drohnen &
Fahrzeuge. Die Hot-Drohne ist magenta pulsierend umrandet, in beiden
Menüs. Siehe `concepts/drohnen-fahrzeuge.md`.

## [2026-10-28] update | Hot-Gehen: Neurolink ist Stufe-1-Chrom, Deck bekommt Zusatzaktionen

Mark präzisiert die offene Neurolink-Spec: keine Sonderkosten, normale
Cyberware Bonus 1, bestehende Chrom-Tabelle. Decker-Hot schaltet die
Zusatzaktionen des ausgerüsteten Decks frei (Feld existiert im Umbau, Kampf
liest es bisher nur von Chrom). Rigger-Hot bleibt Drohnen-Übernahme. Offen:
Booster-Risiko (Ampel/Paralyse) oder schlichte Extra-Aktion. Siehe
`concepts/drohnen-fahrzeuge.md`.

## [2026-10-28] gebaut | Sichtbarkeits-Standard umgedreht: ALLE statt SL-geheim

Mark: "ich hätte gerne das alles was so erstellt wird ... standardmäßig auf
Für alle sichtbar ist, und nicht auf SL-Geheim, somit muss ich nur Dinge
umstellen, die geheim sind." Betrifft Gegenstand/Person/Ort/Event/Fraktion/
Begleiter/Party/Zeichnung — Standard-`sichtbarkeit` beim Anlegen jetzt
`ALLE` statt `GM` (13 Pydantic-Feld-Defaults in 5 Backend-`schemas.py`,
16 hartkodierte Anlege-Payloads in 6 Frontend-Dateien, plus
`items/routes.py::_default_sichtbarkeit` radikal vereinfacht — kein
PC/NPC-Unterschied mehr, immer ALLE). **Bewusst ausgenommen:**
`notizenSichtbarkeit` (SL-Innenperspektive/Planungsnotizen, eigene
Privatsphäre-Ebene, unverändert GM) und die Ingame-Wiki-Seiten
(`wiki/schemas.py::SeiteCreate` — Kommentar im Code warnt ausdrücklich: "eine
Planungsseite, die versehentlich offen steht, verrät den Plot", deshalb
unangetastet gelassen und Mark zur Bestätigung vorgelegt statt
stillschweigend mitgeflippt). `FreigabeRequest` im selben File war
schon vorher ALLE (Freigeben-Aktion zeigt Inhalt absichtlich). **Verifiziert:**
volle Backend-Suite dieselben 55 vorbestehenden Fehlschläge, `npx tsc -b`
sauber. **Nicht rückwirkend** — nur neu angelegte Einträge, Bestandsdaten
bleiben wie gespeichert.

## [2026-10-28] gebaut | Bugfix: Gegenstände an die eigene Drohne verschwanden

Mark live auf bebop: Pistole dem Rigger "Rigger" übergeben und an die
Drohne "Absar 1.7" ausgerüstet — danach weder im Drohnen-Inventar noch im
eigenen Rucksack sichtbar, nicht zurückholbar. Ursache in Neo4j bestätigt:
Besitz/Ablage stimmten (`BESITZT`→Drohne, `ablage=AUSGERUESTET`), aber
`sichtbarkeit` sprang beim Besitzerwechsel auf `GM`/`[]`. Grund:
`_default_sichtbarkeit` (`items/routes.py`) kannte nur PC→sichtbar für sich
selbst, alles andere→SL-geheim — eine Drohne hat `personType` NPC, auch
wenn sie an einen PC-Rigger gebunden ist. Traf `besitzer_wechseln`,
`create_item` UND die KI-Gegenstandsverknüpfung (`ki/routes.py`) gleichermaßen.
Fix: gebundene Drohne/Fahrzeug fällt jetzt auf die Sichtbarkeit ihres
Riggers zurück (`drohne_rigger()`-Lookup) statt auf GM. Betroffene
Live-Pistole direkt in der DB nachkorrigiert. **Verifiziert:** neuer
Regressionstest in `test_zugriffsschutz_drohnen_ausruestung.py` (traf exakt
den Pfad, den die alten Tests nie ausgelöst hatten, weil deren Fixture
schon mit `sichtbarkeit=GM` startete), volle Suite dieselben 55
vorbestehenden Fehlschläge mit und ohne Fix (`git stash` gegengeprüft).
Deployed auf bebop (`9bc765a`). Siehe [[concepts/drohnen-fahrzeuge]].

## [2026-10-28] gebaut | Drohnen-Inventar: Typ-/Textfilter

Mark: "ich muss filtern können und ich brauche den Steckbrief des
Gegenstands, damit ich weiß welche Waffe ich der Drohne zuweise." Übergeben/
Steckbrief liefen schon (26.10.), der Filter fehlte. `DrohnenAusruestung.tsx`
(Ausgerüstet/Übrige Ausrüstung) und `UebergebenPopup.tsx` (Auswahl aus dem
eigenen Rigger-Inventar) bekommen jetzt beide dieselbe `KategorienAuswahl`
+ Textsuche wie `GegenstaendeUebersicht.tsx`. `UebergebenPopup` zeigte bisher
nur nackte Namensknöpfe ohne Typ/Steckbrief — jetzt `mu-liste`/`mu-zeile`
(Mülleimer-Muster) mit Steckbrief-Kurzzeile je Eintrag. Reiner Frontend-Job,
kein Backend/Schema geändert. **Verifiziert:** `npx tsc -b` sauber. Siehe
[[concepts/drohnen-fahrzeuge]].

## [2026-10-25] gebaut | Drohnen/Fahrzeuge Phase 2: Riggerkonsole-Slots + Nuyen-Formel

`nuyenProXp`-Kampagneneinstellung (Start 200¥), `erfahrung.nuyen_kosten()`.
Riggerkonsole-`maxDrohnen` jetzt durchgesetzt (neue Repository-Funktionen in
`items`/`entities`, reine Deckel-Regel in `traits/drohnen.py`), neue Routen
für Liste/Rigger-Bindung/Aktivieren (Spieler-Selbstbedienung für die eigene
Drohne). Kampf lehnt inaktive Drohnen als Teilnehmer ab. 52 Tests grün,
echter E2E-Test gegen laufende Neo4j, volle Suite ohne Regression. Offene
Entscheidung vor dem echten Kauf-Endpoint: Rigger-Kapital oder eigenes
Drohnen-Kapital? Siehe [[concepts/drohnen-fahrzeuge]].

## [2026-10-25] gebaut | Drohnen/Fahrzeuge Phase 1: Datenmodell-Fundament

`istDrohne`/`istFahrzeug`/`riggerAktiv` an `Person`, acht neue
TraitDef-Attribute (`AttributDrohne`×7, `AttributDrohneAussenhuelle`×1),
`sichtbare_kategorien()`/`initiative()`/`ice_max()` mit `ist_drohne`-Zweig
(Initiative Geschwindigkeit+CPU, I.C.E. eigenes Attribut), neue
Kosten-Kategorien in `erfahrung.py` (Außenhülle doppelter Faktor).
`gesundheit_max()` unverändert wiederverwendet. 41 neue/bestehende Tests
grün, volle Suite ohne Regression. Phase 2 (Nuyen-Kauf, Riggerkonsole-Slots,
Frontend, Reparatur-Menü) offen. Siehe [[concepts/drohnen-fahrzeuge]].

## [2026-10-25] entschieden | Drohnen/Fahrzeuge komplett neu konzipiert

Im Chat mit Mark: Drohne/Fahrzeug wird eigener Person-Knoten
(`istDrohne`/`istFahrzeug`, wie `istCritter`/`istKI`) statt Item-Feld, damit
Waffen/Rüstung über das bestehende Besitz-System laufen. 8 Attribute in zwei
Spalten (Körperlich/Technisch, keine soziale Spalte), Initiative
Geschwindigkeit+CPU, I.C.E. eigenes steigerbares Attribut, Außenhülle mit
doppeltem Steigerungs-Faktor. Erschaffung/Steigerung in Nuyen statt XP
(gleiche Faktor-Formel, neue Kampagnen-Einstellung `nuyenProXp`, Start 200¥).
Riggerkonsole bekommt aktive Slots (`maxDrohnen`, bisher ungenutztes Feld),
inaktive Drohnen erscheinen nicht im Kampf. Neues eigenständiges
Reparatur-Burgermenü, reine Formel-Wiederverwendung aus der
Rüstungsreparatur. **Noch nicht implementiert**, siehe
[[concepts/drohnen-fahrzeuge]] für das volle Datenmodell und offene Fragen.

## [2026-10-25] neu | Whiteboard: mehrere live mitzeichenbare Boards

Neuer Burgermenü-Punkt bei SL und Spielern. Knotentyp `Zeichnung`
(campaign-scoped), SL schaltet Zeichenfreigabe pro Board frei
(`spielerDuerfenZeichnen`), Standard-Sichtbarkeitsschema, Papierkorb statt
Hard-Delete. Live-Sync über eigenen WebSocket nach dem Muster der
SL-Mitteilungen (kompletter Gesamtstand pro Nachricht, kein inkrementelles
Protokoll). Details siehe `CLAUDE.md` (Zuletzt gebaut 25.10.2026).

## [2026-10-24] update | SL kann Spezialisierungs-Slots entfernen

Punkte abziehen lässt einen schon vergebenen Slot liegen. Die SL löscht ihn
im Zusatzfertigkeiten-Menü (Tab Vergebene Slots) oder im Klick-Fenster der
Fertigkeit. Siehe [[concepts/attribute-und-fertigkeiten]].

## [2026-10-24] update | Tutorial-Shop sperrt Gratis-Erstkauf nicht mehr

Der erste passende Kauf (konkreter Typ oder „alle Typen“) wird im
Tutorial-Shop als gratis angezeigt. Die Rasse steht dafür schon am Entwurf,
nicht erst nach dem Anlegen. Siehe [[entities/rassen-baukasten-feature]].

## [2026-10-24] update | Rassen-Gratis-Kauf alle Typen

Im Rassen-Menü gibt es bei „Erster Kauf dieses Typs“ die Option „alle Typen“.
Der erste Shop-Kauf ist dann kostenlos, der zweite wieder zum normalen Preis
(`rassenFeatureGenutzt`). Siehe [[entities/rassen-baukasten-feature]].

## [2026-10-24] update | Rassenauswahl mit Bild und Steckbrief

Charaktererstellung: Bild auf der Rassenkarte, Steckbrief mit großem Bild,
Text darunter und den Rassen-Extras. Namen über `/erstellung/regeln`.
Pytest 1/1 für die Namensauflösung. Nicht im Browser geklickt.
Siehe [[concepts/rassen]] und [[entities/rassen-baukasten-feature]].

## [2026-10-23] update | Kampfkarte Ausrüstung und Waffen-Skill

Kampfkarte zählt Ausrüstungsboni in Treffen/Ausweichen/Parieren.
Waffen und Chrom-als-Waffe haben `kampfFertigkeit` (Schusswaffen,
Nahkampf, Handgemenge). Schadenszeile nur noch Schaden + Nettoerfolge.
`pytest tests/test_waffenbonus.py` 8/8, `tsc -b` sauber. Nicht im
Browser geklickt. Siehe [[concepts/kampf-und-initiative]].

## [2026-10-23] update | Spieler-Burgermenü anpassen

Spieler haben unten im Burger denselben ☰ wie die SL: ausblenden und
Reihenfolge, PC und Tablet getrennt, Handy scrollt die volle Liste.
Gespeichert an `Spieler.menueLayouts` (Zugang, nicht Charakter).
`pytest tests/test_spieler_menue.py` 3/3, `tsc -b` sauber. Nicht im
Browser geklickt. Siehe [[entities/ui-konzept-commlink]].

## [2026-10-23] update | Rechtsklick im Beziehungsgraphen

SL-Bereich Beziehungen: Rechtsklick auf einen Knoten öffnet das bestehende
Detailfenster, Rechtsklick auf eine Kante `VerbindungBearbeiten`. Linksklick
bleibt die Nachbarschaft. `tsc -b` sauber, nicht im Browser geklickt.
Siehe CLAUDE.md 23.10.2026 und [[entities/neo4j-datenmodell]].

## [2026-10-10] update | Charakter-Bildergalerie

PC- und NPC-Detail nutzen `BildGalerie` (dasselbe Muster wie Ort/Fraktion).
Primärbild bleibt `bildUrl` (Kachel und Spielerportrait). Spieler-Upload
ersetzt nur das Primärbild. Gegenstände weiter ein Bild. Nicht im Browser
geklickt. Siehe CLAUDE.md 10.10.2026 und [[entities/ki-integration]].

## [2026-10-10] update | entities/achievements gebaut (Backend + Frontend)

Konzept vollständig umgesetzt: `backend/app/achievements/` (schemas,
repository, trigger-Katalog mit allen 14 auslöseArt-Werten, belohnung.py
für EP/Hintergrund-Einlösung, routes.py). Frontend
`frontend/src/achievements/` — SL-Verwaltungsfenster (Katalog, Baukasten,
Auto-Vorschläge, manuelle Vergabe, ✨-KI-Text) und Spieler-Popup, beide über
🏆-Symbol in der Werkzeugleiste. Migration `012_achievements.cypher`
(`Person.istEndboss`-Backfill). Eigene Tests
(`backend/tests/test_achievements.py`), `tsc -b` sauber, Backend startet
fehlerfrei gegen Neo4j. Browser-Klicktest am Spieltisch offen.

## [2026-10-10] update | entities/achievements (Mechanik + neue Trigger)

Konzept-Runde erweitert, immer noch nicht gebaut: Achievements können jetzt
EP oder Hintergrundpunkte verleihen (`belohnungsArt`/`belohnungsMenge`/
`belohnungsHintergrund`, fest am Achievement hinterlegt) — der einzige Weg,
wie ein Hintergrund nach der Erstellung noch steigt (`LevelUp.tsx` schließt
sie sonst aus, siehe [[concepts/erfahrung-und-steigern]]). Fünf neue
`auslöseArt`-Werte: `GEHEIMNISTRAEGER` (Geheimwissen an eine Person),
`ERSTER_BESITZ_ZIEL`/`ERSTE_BESCHREIBUNG_ZIEL` (parametrisierbar über
`zielGegenstandId`, z. B. β⁺-Isotop/Ki-Kristalle), `ERSTER_CRITTER`/
`ERSTE_DROHNE` (Begleiter-Erwerb), `ENDBOSS_BESIEGT` (neues
`Person.istEndboss`-Flag), `ERSTE_SITZUNG_UEBERLEBT` (rückwirkend beim
Anlegen der zweiten Sitzung geprüft, kein neuer Sitzungs-Abschluss-Knopf).
„Alle erfahren etwas“ bleibt bewusst `MANUELL`, kein Auto-Trigger.

## [2026-10-10] update | Ideenschmiede Entwürfe laden wieder

`GET /personen` riss Altbestand wegen fehlender `_BOGEN_DEFAULTS` für
Tutorial-Shop/Rassen-Feature-Felder. Die Schmiede zeigte das als
„Fehler beim Laden der Entwürfe“. Siehe CLAUDE.md 10.10.2026 und
[[entities/neo4j-datenmodell]].

## [2026-10-09] update | Charaktererstellung Person-Schritt als Entwurf

Autosave auf den Entwurfsknoten (`PATCH .../steckbrief`, inkl. Name/Alter).
Öffnen hydratisiert aus dem Bogen. Siehe CLAUDE.md 09.10.2026 und
[[concepts/charaktererschaffung]].

## [2026-10-09] update | Android-Tastatur über dem Text

Fenster folgen dem Visual Viewport, Editor scrollt am Handy nicht in sich
selbst. Siehe CLAUDE.md 09.10.2026.

## [2026-10-09] create | Spieler-Lexikon (Welt/Fauna/Flora/Objekte) entworfen

Neue Seite [[entities/spieler-lexikon]], Status entschieden-nicht-umgesetzt.
Mark will Wissenswurf-Ergebnisse (Ort/Critter/Gewächs/MacGuffin-Objekt) als
Burgermenü-Lexikon zeigen statt per Mitteilung. Zentrale Design-Entscheidung:
zwei Sichtbarkeits-Schichten — neue automatische `ENTDECKT`-Kante (per
Erreichbarkeits-Hook, max. 7 Hops ab PC über Party/Event/Ort/NPC, bricht hart
an SL-geheimen Verbindungen/unsichtbaren Knoten ab, pro PC statt
campagnenweit, dauerhaft gespeichert wie beim Ereignisprotokoll) schaltet nur
Existenz frei; bestehendes `sichtbarkeit`-Feld bleibt wie bisher für die
Beschreibung zuständig. `Gegenstand.zeigeInGraph` wird zu `storyRelevant`
umbenannt für MacGuffin-Objekte, gleiche Entdeckungs-Kette wie Orte/Critter.
Dazu Favoriten-Kante `FAVORISIERT`, Spieler-Notizen bekommen optionalen
Objektbezug (`bezugTyp`/`bezugId`), SL-Geheim-Knopf bei Spielern als
kosmetischer Nebenbefund notiert. `ENTDECKT`/`FAVORISIERT` in
[[entities/neo4j-datenmodell]] nachgetragen, Tag `spieler-lexikon` in
SCHEMA.md ergänzt. Code noch nicht gebaut — folgt direkt im Anschluss.

## [2026-10-09] update | Chibi-Woche 04.–08.10. nachgezogen

HEAD/Live `be2a6ff`. Windows-Klon war auf `19c78e9`, Fast-Forward am 09.10.
45 Commits von Chibi Neko (bebop/Telegram), alles auf `main` und live.
Siehe CLAUDE.md „Zuletzt gebaut 04.–08.10.2026“. Kurz: Laden-am-Ort-Fixes,
Massen-KI als Job, Æ-Begleiter, Alias aka Name, Flora/Fauna (Gewächs +
`LEBT_IN`), Gegenstand-Vorlage/Typ-ändern, Gemini-Retry + Mistral-Fallback,
Kontakte-Suche, Ideenschmiede-Autosave.

## [2026-10-04] update | Shop hängt am Ort

Ort = Laden (Beschreibung, Kulisse, Sortiment). Person bleibt Händler
für Kontakt/Verhandeln, nur Porträt. Mehrere Händler pro Ort möglich.
Kante `BETREIBT`, `VERKAUFT` vom Ort. Siehe CLAUDE.md 04.10.2026.

## [2026-10-03] update | Frontend Production-Build für PWA

Live-Frontend ist nginx + `vite build`, nicht mehr Vite-Dev.
Weiße Handy-PWA-Starts (hundert Module + leeres Auth-`null`) sollten
damit weg sein. Siehe CLAUDE.md Zuletzt gebaut 03.10.2026.

## [2026-10-02] update | Bildgenerierung Gemini 3.1

Cloud-Provider wechselt auf `gemini-3.1-flash-image`
(`gemini-2.5-flash-image` seit 02.10.2026 abgeschaltet). Parser zieht
Bild auch hinter Text-Parts und nennt Safety-Grund statt
„unerwartete Antwort“. Siehe [[entities/ki-integration]], `docs/api/ki.md`.

## [2026-10-02] update | Backlog zweiter SL-Tisch

Nur notiert, nicht gebaut: eigener SL/eigene Welt; Kampagnen nicht
für alle sichtbar; Status unbespielt zur Übernahme; Spotify pro User
(sonst Marks Gerät). CLAUDE.md Backlog, [[entities/spotify-anbindung]].

## [2026-10-02] update | Bild-Autotext zieht Notizen heran

KI-Bild-Prompt nimmt Beschreibung **und** Entitäts-Notizen.
Spieler-Portrait liest `description`/`notes` statt des toten Felds
`beschreibung`. Siehe [[entities/ki-integration]], `docs/api/ki.md`.

## [2026-10-02] update | Spieler-Notizen privat

Privater Schmierzettel (Titel+Text) am Spieler-Zugang, SL sieht nichts.
SL-Menüpunkt „Notizen / bald“ entfernt. Kein Wiki. API
`docs/api/spielernotizen.md`, Knoten `SpielerNotiz` / Kante `HAT_NOTIZ`.

## [2026-10-02] update | Burgermenü-Customizen in der Symbolspalte

☰-Knopf „Burgermenü anpassen“ war in der PC/Tablet-Rail unsichtbar
(`opacity: 0` am ganzen Fuß). Jetzt sichtbar, Name/Rolle nur in der
Handy-Schublade. Siehe [[entities/ui-konzept-commlink]].

## [2026-10-01] update | Verbindungen nachträglich bearbeiten

PATCH auf `VERBINDUNG`-Kanten: Typ, Beschreibung, Sichtbarkeit.
Endpunkte unveränderlich. UI `VerbindungBearbeiten` in Beziehungsliste
und Bereich Verbindungen. Siehe [[entities/neo4j-datenmodell]].

## [2026-10-01] update | KI-Idee/Beratung: Ort Event Fraktion Verbindung

✨ KI und Beratung-Entwurf können dieselben Welttypen anlegen:
story/charakter/gegenstand/ort/event/fraktion plus Verbindung als Kante.
Abschnitt in [[entities/ki-integration]], Tabelle in `docs/api/ki.md`.
Commit `e67dc54`.

## [2026-09-30] update | SL-Beratungschat in der Ideenschmiede

Chat neben ✨ KI: nur Freigegebenes als Kanon, Entwurf erst auf Knopf
(`istEntwurf`). Knoten KiBeratung/KiBeratungNachricht, nicht in sammle_kontext.
Live auf bebop `86f9267` (git pull + `--build` backend/frontend).
Jev/TypeSafe System One recherchiert und **geparkt** (kein Code, Hosting/Schnitt
offen) — siehe [[entities/ki-integration]].

## [2026-09-30] update | Gegenstand-Fenster mit Reitern

Gegenstands-Detail wie Ort/NPC: Übersicht (Name, Bild, Ablage, Steckbrief),
Beschreibung, Umbauen, Notizen, Besitz. Preis/Seltenheit nicht auf Seite 1.

## [2026-09-30] update | Ideenschmiede-Gegenstand öffnet Detailfenster

Klick auf einen Gegenstands-Entwurf öffnet dasselbe Bearbeiten-Fenster wie
in der Übersicht. GET einzelner Gegenstand ergänzt.

## [2026-09-30] update | Formeln in Namen ($\\beta^+$ → β⁺)

`$...$` in Namen wird in Kachel und Fenster-Titel als Unicode gesetzt
(β⁺-Isotop), ohne KaTeX.

## [2026-09-30] update | Autosave ohne Popup-Reload

Beschreibung/Notizen-Autosave patched still, ohne Listen-Reload. Der Reload
hat das Detail-Fenster unmountet (Animation, Tab zurück auf Übersicht).

## [2026-09-29] update | Burgermenü blättert ohne Scrollbar

Symbolspalte: keine `overflow-y: auto`-Leiste mehr. Flache Pfeile oben/unten
blättern eine Seite, vorgefahrener Name bleibt sichtbar. Handy-Schublade
weiter volle Liste, Scrollbar unsichtbar.

## [2026-09-29] update | kampagnen-export-import Weissliste + Nacht-Dump

Import-Weissliste um Zusatzfertigkeiten, Shop-Bestellung/Alltagswunsch und
Ereignisprotokoll-Knoten nachgezogen. Nacht-Dump auf bebop
(`scripts/bebop-pnptool-backup.sh`): Neo4j-Volume + Uploads, 30 Tage täglich,
1. im Monat ein Jahr.

## [2026-09-29] update | ereignisprotokoll Zeitleiste-Frontend + Burgermenü

SL-Bereich `Protokoll` (nur SL): Sitzung, Kategoriefilter, Suche, Liste.
`kurz` in der Zeitleiste-UNION. Burgermenü ausblenden/Reihenfolge am
GM-Account, PC≠Tablet (`/api/auth/gm/menue`). Handy scrollt. Korrektur/
Papierkorb in der UI später.

## [2026-09-29] update | ereignisprotokoll Auto-Hooks

Fachmodule schreiben ins Sitzungs-Log über `hooks.py`: Kampf, Verhandlung,
Shop/Items/Geld, Party-Aufenthalt, Charakterentwicklung, KI-Hauptpfade.
Tests ohne Neo4j. Frontend und NPC-Wissen weiter offen.

## [2026-09-29] update | ereignisprotokoll Doku-Nachzug

Backend-Modul stand seit Commit `233c939` (27.09.), Wiki/CLAUDE.md sagten
noch „kein Code“. Status auf `teilweise-umgesetzt`: Sitzungen, 8 Kategorien,
Zeitleiste, Papierkorb, `Person.erstelltAm`. Auto-Hooks uncommitted,
Frontend fehlt, Achievements nur Konzept. Neu: `docs/api/ereignisprotokoll.md`.
`index.md`, `neo4j-datenmodell.md`, `achievements.md`, `CLAUDE.md` nachgezogen.

## [2026-09-28] update | zusatzfertigkeiten wiki-konsistent für Kontextreset

Aktueller Stand (Button + Paket-Punktzeilen, Commit `2bf1adc`, live bebop)
als eigener Abschnitt in `entities/zusatzfertigkeiten.md`; Mittags-Umbau
als „teilweise überholt“ markiert; Frontend-Bullet und CLAUDE.md-Klicktest
nachgezogen; `concepts/charaktererschaffung.md` verlinkt.

## [2026-09-28] update | entities/zusatzfertigkeiten (Button + Punktzeilen)

Mark: Auswahl-Liste ohne Punkte reicht nicht. Umbau: Button „Zusatzfertigkeiten“
oben im Fertigkeiten-Popup öffnet ein nested Fenster zur Katalogwahl; gewählte
Einträge erscheinen als DotPool-Zeilen im selben Raster und verbrauchen
Paket-Slots. Freebees bleiben Aufschlag (+1, Kosten 2). Backend:
`zusatzfertigkeitPunkte` = Paket, neu `zusatzfertigkeitFreebees` = Freebee.
Kante auch bei rating 0 (wandern ins Blatt).

## [2026-09-28] update | entities/zusatzfertigkeiten (Erstellung korrigiert)

Mark hat die morgens gebaute Erstellungs-Integration (eigenständiger
Popup-Button + separates Freebee-Budget) noch am selben Tag zurückgewiesen:
*"bei den freebees erscheinen die einfach nicht wenn sie nicht zuvor schon
bei der Fertigkeiten Vergabe ausgewählt wurden [...] sollten dann auch mit
den normalen freebees abgerechnet werden könne."* Umgebaut: Auswahl jetzt im
bestehenden Fertigkeiten-Schritt (neue Komponente
`ZusatzfertigkeitAuswahl.tsx`, rein clientseitig), Bezahlung im
Freebees-Schritt aus dem gemeinsamen Hauptpool (neues Backend-Feld
`ErstellungInput.zusatzfertigkeitPunkte`). Eigenes Freebee-Budget
(`ZUSATZFERTIGKEIT_FREEBEE_BUDGET`, `Person.zusatzfertigkeitenFreebees
Ausgegeben`) vollständig entfernt. LevelUp und Charakterblatt-Anzeige
unverändert. Verifiziert: `tsc -b`, `pytest` (446 grün, 2 vorbestehende
unabhängige Fehlschläge unverändert), echter E2E-Test gegen Neo4j (Freebee-
Rechnung, Kanten-Existenz, Nicht-Auftauchen ungewählter Einträge, Ablehnung
bei Überziehung). `docs/api/zusatzfertigkeiten.md` + `CLAUDE.md` nachgezogen.

## [2026-09-28] create | entities/zusatzfertigkeiten

Neues Backend-Modul `app/zusatzfertigkeiten/` gebaut: campaign-gebundener
Katalog optionaler Fertigkeiten (Sprengstoffe, Esoterik, Gesetzeskunde,
Kosmologie, Rätsel — bisher nur `docs/reference/Master/
Optionale_Fertigkeiten.md`, nirgends im Code). Kein globaler Fixkatalog und
kein Freigabe-Schalter wie bei Rassen (Marks Vorgabe: SL pflegt eine
einfache Tabelle je Kampagne, jeder Eintrag sofort wählbar). Eigene
Relation `HAT_ZUSATZFERTIGKEIT`, nicht `HAS_TRAIT`. "+ Zusatzfertigkeit"-
Popup identisch in Charaktererstellung UND LevelUp. Kosten wie normale
Fertigkeit (Freebee 2/Stufe, EP-Faktor 2/Neu-Kosten 3) — eigene, mit Mark
noch nicht gegengeprüfte Design-Entscheidung, ebenso das separate
Freebee-Kontingent (6 Punkte) für Neu-Erlernen während der Erstellung.
KI-Vorschlag-Knopf (zweistufig wie beim Händler-Sortiment) echt mit
Gemini/Mistral getestet. Vollständig per Backend-E2E-Test verifiziert,
Frontend nur `tsc -b`/`vite build`, kein Browser-Klicktest.

`index.md` Zusammenfassungszeile + Seitenzahl nachgezogen.

## [2026-09-27] update | entities/achievements (UI)

Fünfte Runde: Mark beantwortet "wo finde ich die Achievements? gibts dafür
ein neues Burgermenü?" — Antwort war zunächst ehrlich "noch gar nichts
gebaut, reines Konzept", danach hat Mark die UI selbst festgelegt:

**🏆-Symbol in der oberen Werkzeugleiste** (`cl-leiste-werkzeuge` in
`CommlinkShell.tsx`, derselbe Slot wie Erklärungs-/Theme-Schalter) statt
einem neuen Burgermenü-Eintrag in der Symbolspalte. Klick-Verhalten je
Rolle unterschiedlich: **Spieler** sehen ein scrollbares Popup mit den
eigenen Achievements, neuestes zuerst, jederzeit erneut aufklappbar;
**SL** bekommt stattdessen ein volles Verwaltungsfenster im
Burgermenü-Stil ("damit man sich mit dem Entwerfen leichter tut") —
Katalog, Baukasten, offene Auto-Trigger-Vorschläge, manuelle Vergabe.

**Auto-Popup bei neuer Verleihung, außer während eines laufenden Kampfs**
(Mark: "die man während dem Kampf erhält sollten nach dem Kampf
aufpoppen") — Verleihungen während `Kampf` aktiv werden zurückgehalten und
erst beim Kampfende (`DELETE .../kampf`) nachgeliefert, damit ein Popup
nicht mitten im Gefecht ablenkt. Wiederverwendet dieselbe Live-Push-
Infrastruktur wie das bestehende Mitteilungssystem.

`index.md` Zusammenfassungszeile nachgezogen.

## [2026-09-27] create | entities/achievements

Vierte und letzte Runde des Ereignisprotokoll-Gesprächs: eigene Seite für
Achievements, ausgelagert aus `ereignisprotokoll.md` (Thema eigenständig
genug für mehr Tiefe). Mark wollte "beides" — automatische Erkennung UND
spontane manuelle Vergabe — plus Beispiele: "First Blood"/"erster Kill",
"meisten Schaden genommen/verteilt", "erster gekaufter Gegenstand außerhalb
der Erstellung", "Hello World", "erste Verhandlung".

**Kernentscheidung: `einzigartig`-Häkchen, wiederverwendet von
`Gegenstand.einzigartig`** (Marks eigener Vorschlag nach Rückfrage) — trennt
campaign-weit einmalige Titel ("First Kill", nur der Allererste) von
pro-Person wiederholbaren ("Mörder", jeder kriegt seins). Kein
Zusatzfeld nötig, ob ein Titel den Träger wechseln kann (Rekord vs.
Meilenstein) — ergibt sich automatisch aus der Auslöseart: ein
"war der Erste"-Trigger kann nach der ersten Vergabe nie wieder zutreffen,
ein Rekord-Trigger ("höchster Schaden") wird bei jedem neuen Log-Eintrag neu
geprüft und kann den Titel weiterreichen, exakt wie ein einzigartiger
Gegenstand den Besitzer wechselt.

Sieben `auslöseArt`-Werte als erster Trigger-Katalog spezifiziert
(`ERSTER_KILL`, `MOERDER`, `MEISTE_SCHADEN_GENOMMEN`/`_VERTEILT`,
`ERSTER_KAUF`, `ERSTE_VERHANDLUNG`, `CHARAKTER_ERSTELLT`), alle direkt gegen
die im Ereignisprotokoll spezifizierten Log-Kategorien geprüft. Bewusst
**kein persistenter Vorschlags-Knoten** — Trigger sind jederzeit live aus
dem bestehenden Log neu berechenbar, gleiches Muster wie der bestehende
KI-Sortiment-Vorschlag (`GET .../ki-vorschlaege`, nichts gespeichert bis
Bestätigung).

KI-Text bezieht den auslösenden Log-Eintrag + Ort/Event/Sitzung als
Zusatzkontext ein (Mark: "thematisch auf die letzten Ereignisse, den Ort
und das Event bezogen"), dieselbe `sammle_kontext()`-Infrastruktur wie
überall sonst, Vorschau vor dem Speichern wie beim ✨-Knopf-Muster.

Spontane Vergabe: eigener Baukasten (analog Rassen-Baukasten), jederzeit
anlegbar und zuweisbar, mit optionalem KI-Text oder freiem SL-Text.

`ereignisprotokoll.md` (Abschnitt 5 verweist jetzt hierher), `index.md`,
`CLAUDE.md` Punkt 17 nachgezogen.

## [2026-09-27] update | entities/ereignisprotokoll (Kampf-Log + Verhandlungsausgänge)

Mark wollte den Kampf-Aspekt genauer klären: *"wenn mein Spieler dran ist,
und ein NPC leben verliert, der Spieler diesen NPC verletzt hat, und
umgekehrt natürlich auch!"* — neue Kategorie `KampfLogEintrag` mit
**automatischer Angreifer-Zuordnung** aus der bestehenden Zugreihenfolge
(`Kampf.amZug`, siehe `backend/app/kampf/repository.py`), kein manuelles
Zusatzfeld im Regelfall nötig, nur ein optionales Override für
Ausnahmen (Umweltschaden, Treffer außerhalb der Zugreihenfolge).

Zweite neue Kategorie `VerhandlungsAusgang` (Marks Zustimmung: "die
Verhandlungsausgänge finde ich auch gut") — Ergebnis jeder beantworteten
Verhandlung (Shop-Kauf, Rüstungsreparatur, Gegenstands-Weitergabe), auch
abgelehnter Angebote, mit einem Positions-Schnappschuss statt Live-Referenz
(ein später geänderter Händlerpreis darf die Historie nicht rückwirkend
verfälschen).

Zusätzlich Marks Frage beantwortet, ob Neo4j fürs Logging die richtige
Wahl ist oder ein Zeitreihen-Tool besser wäre: **Neo4j bleibt richtig**,
neuer Abschnitt in der Seite begründet das (Log-Einträge hängen per Kante
an bestehenden Knoten, ein zweites Tool bräuchte für jede Abfrage einen
Rück-Join in den Graph — bei diesem Datenvolumen unnötiger Aufwand).

`CLAUDE.md` Punkt 17 nachgezogen (zwei neue Kategorien + Neo4j-Begründung),
`index.md` Zusammenfassungszeile aktualisiert.

## [2026-09-27] update | entities/ereignisprotokoll (Charakterentwicklung)

Dritte Runde zur Frage "was fehlt noch bei der Charakterentwicklung":
neue Kategorie `CharakterEntwicklung` — Steigerungs-Käufe, Willenskraft,
EP-Vergabe (mit optionaler Begründung, nutzt das bestehende `slNotiz`-Feld,
Mark: "vor allem bei den extra XP macht das Sinn") und nachträgliche
Rassenwechsel (`RASSE_GEAENDERT`, Mark: "kann ja auch storytechnisch
begründet passieren... Body Swap oder sowas"). Charaktererstellung selbst
bewusst NICHT geloggt (Mark: "es reicht wann der Charakter erstellt wurde").

**Beim Durchsuchen des Codes eine echte Lücke gefunden:** `Person` hat
aktuell überhaupt kein `erstelltAm`-Feld (`entities/repository.py`) — jeder
Charakter entsteht ohne Zeitstempel. Muss vor dem eigentlichen
Ereignisprotokoll-Bau als Voraussetzung ergänzt werden, sonst bleibt "wann
wurde X erstellt" für jeden bestehenden UND neuen Charakter unbeantwortbar.

`CLAUDE.md` Punkt 17, `index.md` nachgezogen.

## [2026-09-27] create | entities/ereignisprotokoll

Auslöser: Mark verlor eine KI-generierte Nachricht, die nirgends dauerhaft
gespeichert war — daraus wurde ein vollständiges Design-Gespräch fürs
Sitzungs-Logging, weit über den ursprünglichen Anlass hinaus. Neue Seite
`entities/ereignisprotokoll.md`: eigener Knotentyp je Kategorie (nicht ein
generischer `typ`-Knoten — Mark entschied sich für saubere Einzeltypen,
passend zum bestehenden Projektstil), gemeinsame Basis-Properties
(`zeitpunkt`, `ingameZeitpunkt`, `sitzungId`, `slNotiz`, `geloescht`) für
eine spätere Cypher-`UNION`-Zeitleiste.

Sechs konkret spezifizierte Kategorien: `KiProtokollEintrag` (loggt jede
KI-Ausgabe dauerhaft, unabhängig von Übernahme — schließt genau die Lücke,
die Mark getroffen hat), `GegenstandsBewegung` (volle Besitzerkette,
Marks MacGuffin-Beispiel durchgespielt), `GeldBewegung` (Kapital, per
`handelId` mit passender Gegenstandsbewegung verknüpfbar statt eigenem
Handels-Knoten), `Aufenthalt` (Party-/Personenbewegung — löst nebenbei den
in `CLAUDE.md` Punkt 8 notierten Blocker für die geplante
KI-Auto-Steigerung), `Achievement`+`AchievementVerleihung` (Inhalt bewusst
offen, nur Verleihungs-Logging schon gedacht), `NpcWissenszuwachs`.

Zeitstempel: reales Datum Pflicht (Marks Anliegen war ausdrücklich "an
welchem Abend ist das passiert"), In-Game-Datum als optionales
Freitextfeld — echtes Kalendersystem explizit vertagt ("müssen wir dann
schön machen"). Löschen folgt der bestehenden Papierkorb-Konvention
(SL darf nachträglich korrigieren, nichts wird hart gelöscht).

Für später vorgemerkt, gleiches Muster: Kampf-Log, Charakterentwicklung,
Verwundungs-/Todesmeilensteine, Beziehungsänderungen (evtl. reicht die
bestehende `VERBINDUNG`-Kante), freies SL-Ereignis ohne feste Entität.

**Reines Konzept-Dokument — kein Code, keine Migration, kein Backend.**
`SCHEMA.md` (neuer Tag `ereignisprotokoll`), `index.md` (neue Zeile),
`CLAUDE.md` (neuer Punkt 17 unter "Geplante Features") nachgezogen.

## [2026-09-26] create | entities/gegenstand-transfer

Neue Seite für Inventar-Transfer. Party-interne Gegenstands-Weitergabe
(`GEGENSTAND_WEITERGABE`, Commit `50321a6`) ist gebaut: Spieler bietet einem
Party-Mitglied einen eigenen Gegenstand an, Empfänger nimmt an/lehnt ab über
das bestehende Verhandlungs-Popup. API-Referenz neu: `docs/api/verhandlung.md`
(vorher nur als „falls vorhanden“ in `ruestung.md` erwähnt).

Nicht gebaut, nur notiert (Datenmodell nicht durchgesprochen): Geld-Weitergabe,
SL-NPC-Belohnung, Credstick, Heiltrank, Granate/Wurftrank, Weitergabe an Leute
am gleichen Ort außerhalb der Party. Party-Seite „Offen: Inventar-Erweiterung“
nachgezogen (Teil erledigt). Währung-Seite um die geplanten Geld-/Credstick-
Punkte ergänzt.

## [2026-09-24] update | concepts/waehrung-und-preise (SL-Sortiment-Editor)

Neue Frontend-Komponente `haendler/HaendlerBearbeiten.tsx` — SL-Popup für
die seit 22.09./24.09. im Backend fertigen Sortiment-/Standort-Endpunkte:
Vorlage aus Dropdown hinzufügen (optionaler Sonderpreis), explizite Ware
entfernen, Rabatt setzen/entfernen, Standort zuweisen. Damit ist das
Shop-Frontend bis auf den KI-Sortiment-Vorschlag komplett angebunden. Nur
`tsc -b` geprüft, kein Browser-Klicktest.

## [2026-09-24] update | Doku-Stand nachgezogen (Shop/KI/Häretiker)

CLAUDE.md „Geplante Features“ und die Wiki-Seiten `waehrung-und-preise` plus
`ki-integration` waren hinter dem Code zurück: Shop-Spieler-Frontend,
Verhandeln, KI-Alltagsgegenstand, Auto-Verknüpfung-Sweep-Frontend,
Bildgenerierung, RichText-Prüfung und Häretiker-Technik standen noch als
offen. Nachgezogen, ohne die echten Restpunkte (SL-Sortiment-Editor,
KI-Vorschlag-Popup, Händler-Spam, Chatbots, Deploy, Critter-Pet) zu
streichen.

## [2026-09-24] update | concepts/waehrung-und-preise (KI-Alltagsgegenstand-Erzeugung)

Neues Modul `backend/app/haendler/alltagswunsch.py`: Spieler fragt einen
Verkäufer im Shop nach einem Alltagsgegenstand, der nicht im Sortiment
steht (z.B. Panzerklebeband), die KI schätzt sofort Preis + Typ und schickt
den Vorschlag als Popup an die SL zur Freigabe — der Spieler muss nicht
warten. Harter Ausschluss von Waffen/Rüstung über zwei unabhängige Sperren
(Typ-Whitelist + KI-Selbsteinschätzung `istVerboten`). Backend UND Frontend
fertig (SL-Freigabe-Popup, Spieler-Ergebnis-Popup, Eingabefeld im Shop),
per echtem E2E-Test gegen laufendes Backend + Neo4j + echten KI-Provider
verifiziert (harmloser Wunsch UND Waffen-Ausschluss beide grün). Frontend
nur `tsc -b` geprüft, kein Browser-Klicktest.

## [2026-09-24] update | concepts/waehrung-und-preise

Shop-Frontend Phase 1+2: Backend um Vertriebsart (PHYSISCH/DIGITAL),
Sonderangebote (rabattProzent) und Online-Bestellungen mit SL-Freigabe
erweitert; Verhandeln um SHOP_KAUF erweitert (bestehender generischer
Mechanismus, unverändert). Frontend erster Wurf: eigener Burgermenü-Punkt
"Shop", Kachelraster, physisch/digital getrennte Shop-Seiten,
CSS-Seltenheitsrahmen (grau/blau/silbern-glitzernd/orange-gezackt/
violett-wabernd). Backend end-to-end verifiziert, Frontend nur `tsc -b`
geprüft (kein Browser-Klicktest möglich).

## [2026-09-24] update | concepts/magie-hexkraft

Häretiker-Flavor-Option ergänzt: zweite, mechanisch identische Alternative
zu „Magier" bei der Charaktererstellung, reine Anzeige-Ebene (neues Feld
`magieFlavor`, `weg` bleibt intern immer `MAGIER`). Hexkraft→Glauben, Wilde
Magie→Blasphemie, neun Sphären→Götternamen aus acht Mythologien (Details
CLAUDE.md Punkt 14). Backend + Frontend über 7 Commits gebaut, echtes
Backend-only-E2E-Skript gegen laufendes Backend + echte Neo4j bestanden
(Katalog-Identität Magier/Häretiker, alle Tooltip-Texte abrufbar),
Testdaten danach entfernt.

## [2026-09-24] create | entities/kampagnen-export-import

Nachts autonom gebaut (Mark schlief, Token-Kontingent lief nach Fertigstellung
in ein Rate-Limit — Cronjob hat den Rest am Morgen verifiziert/aufgeräumt).
Neue Seite `entities/kampagnen-export-import.md` + `docs/api/
campaigns-export-import.md`. SL kann eine komplette Kampagne (Knoten, Kanten,
Bilder, Spieler-Accounts) als ZIP exportieren und als neue Kampagne wieder
importieren. Generische Cypher-Sammlung statt Sonderfall je Entitätstyp,
ID-Neuvergabe per Text-Ersetzungsrunde auf dem rohen JSON, Weisslisten gegen
manipulierte Importpakete. Echter E2E-Testlauf gegen laufendes Backend +
echte Neo4j bestanden, beide Testkampagnen danach entfernt.

## [2026-09-18] create | Wiki initialisiert

- Domain: NeotopiA-Regelsystem (mit Versionsgeschichte) + PnPTool-Architektur
- Struktur angelegt: SCHEMA.md, index.md, log.md, concepts/, entities/, comparisons/
- Auslöser: Mark wollte einen Gesamt-Index von Regeln, Datenbank und Projektstand,
  nach dem Karpathy-LLM-Wiki-Muster, mit ausdrücklichem Hinweis dass die
  Excel-Transkription vom Vortag nur "Version 1" der Regeln ist und die
  Weiterentwicklung im Projekt mitdokumentiert werden soll

## [2026-09-18] ingest | Erstbefüllung aus CLAUDE.md, ENTWICKLUNGSHISTORIE.md, docs/api/*, docs/regeln-neotopia.md, Git-Log, Backend-Code

Quellen gelesen: `CLAUDE.md` (459 Zeilen komplett), `docs/regeln-neotopia.md`
(242 Zeilen komplett), alle 10 `docs/api/*.md`, `docs/theming.md`,
`docs/ui-konzept.md` (Auszug), `docs/ENTWICKLUNGSHISTORIE.md`, Git-Log von
`docs/regeln-neotopia.md` und `CLAUDE.md`, Cypher-Migrationsdateien,
Repository-Dateien in `backend/app/*/repository.py` (Beziehungstypen).

Angelegt (siehe `index.md` für die vollständige Liste mit Zusammenfassung):

**Konzepte (Regeln, mit Entwicklungsgeschichte):**
`wuerfelsystem`, `attribute-und-fertigkeiten`, `charaktererschaffung`, `rassen`,
`magie-hexkraft`, `neuroweaving-decking`, `kampf-und-initiative`,
`ruestung-kaestchen-durchlass`, `cyberware-bioware`, `willenskraft`,
`drohnen-fahrzeuge`, `erfahrung-und-steigern`, `waehrung-und-preise`

**Entitäten (Architektur/Features):**
`architektur-drei-ebenen`, `neo4j-datenmodell`, `mitteilungen-system`,
`kontakte-messenger`, `ingame-wiki-feature`, `rassen-baukasten-feature`,
`theming-system`, `ui-konzept-commlink`, `auth-und-rollen`, `ki-integration`,
`tech-stack`

**Vergleiche:**
`regelwerk-excel-vs-aktuell` (zentrale Seite für Marks Anliegen — was hat sich
seit der Excel-Transkription alles geändert), `veraltete-docs-vs-code` (Fund:
`docs/api/personen.md` und `docs/api/entitaeten.md` beschreiben ein anderes
Attribut-/Essenzsystem als der tatsächliche Code — für Mark zur Prüfung markiert)

**Wichtigster Befund:** Die Excel-Datei (`Neotopia.xlsx`, zuletzt bearbeitet
29.08.2026) ist der Regelstand vor Projektstart. Seit Projektbeginn (28.08.2026)
gab es u. a.: Arete→Hexkraft, Technomancer→Neuroweaver, Gesundheit 5→6,
komplettes neues Rüstungssystem (Kästchen+Durchlass statt flachem Bonus),
Matrix-Verteidigung des Neuroweavers auf Fassung+Geistesschärfe umgestellt
(Excel sagt noch Willenskraft), Chrom-Rundungsregel, Rassen-Baukasten mit
gefundener 15er-Balance-Formel, Drei-Ebenen-Architektur Regelsystem→Kampagne→
Ideenschmiede. Details je Konzeptseite unter "Entwicklung".

## [2026-09-18] update | Verbindliche Wiki-Pflicht in CLAUDE.md + SCHEMA.md verankert

Mark: CLAUDE.md soll klein bleiben (Details wandern nach docs/api/ bzw. ins
Wiki), aber das Wiki muss aktiv befragt werden, um "Erfindungen" (doppelte
oder widersprüchliche Entscheidungen) zu vermeiden.

- `CLAUDE.md`: neuer Abschnitt "Vor jedem Task: Wiki befragen" — `docs/wiki/index.md`
  zuerst lesen, betroffene Wiki-Seite nach jeder inhaltlichen Änderung nachziehen.
  Wiki-Link in die "Wichtige Dokumentation"-Liste aufgenommen.
- `SCHEMA.md`: Update-Policy um explizite "vorher lesen / nachher nachziehen"-Regel
  ergänzt, direkt über der Widerspruchs-Regel.

## [2026-09-18] update | Kästchen-Overflow-Bugfix (Füllrichtung, Rüstungs-/Willenskraft-Umgehung)

Mark hatte die Kästchen-Overflow-Darstellung schon gebaut (nicht im Wiki
erfasst gewesen — Erstbefüllung hatte sie fälschlich als "offen" markiert,
siehe `CLAUDE.md` Punkt 9 zum Zeitpunkt des ersten Ingests), fand sie aber
"nicht 100%ig" beim Ausprobieren am Spieltisch. Code-Analyse (kein Erraten)
fand drei konkrete, unabhängig behobene Fehler:

1. Füllrichtung uneinheitlich zwischen Gesundheit (Puffer zuerst) und
   Willenskraft/I.C.E. (Enden zuerst) — durchgerechnet mit Python, bestätigt.
   Fix: beide füllen jetzt von vorne (Puffer zuerst), Marks ausdrücklicher
   Wunsch nach Rückfrage ("die Schmalen zuerst, die Großen erst wenn's
   kritisch wird").
2. Charakterblatt-Gesundheitsleiste hatte einen zweiten, direkten
   Schaden-Weg (Zahlenpad), der die Rüstungsrechnung (`RuestungsTreffer`,
   ⚡-Knopf) komplett umging. Neues `ZustandFenster`-Prop `schadenErlaubt`
   sperrt diesen Weg für Gesundheit.
3. **Von Mark selbst am System entdeckt, nicht vorher vermutet:** Ryu
   (22 Willenskraft) bekam nie die Pflicht-Rückfrage vor dem Ausgeben,
   "Mark" (wenig Willenskraft) schon — weil ab 11 Kästchen die Leiste zum
   Öffnen-Knopf kippt und das dortige Zahlenpad die Willenskraft-
   Sonderregeln (1 auf einmal, Rückfrage, kein Selbst-Heilen) nicht kennt.
   Fix: Zahlenpad für Willenskraft ebenfalls gesperrt, echter Klick-Handler
   mit Rückfrage auch in der Vollansicht durchgereicht.

Geändert: `frontend/src/traits/Kaestchen.tsx`, `ZustandFenster.tsx`,
`Charakterblatt.tsx`, `frontend/src/kampf/Kampfkarte.tsx`. Verifiziert per
`tsc --noEmit` (keine Typfehler) und Nachrechnen der Füllreihenfolge in
Python — nicht im Browser durchgeklickt (Login-Automatisierung nicht
abgeschlossen), Mark sollte am Tisch nochmal gegenprüfen.
`docs/wiki/concepts/attribute-und-fertigkeiten.md` und `CLAUDE.md` Punkt 9
nachgezogen (Status offen → fertig, mit Datum).

## [2026-09-18] update | Rüstungstreffer-Zahleneingabe vereinheitlicht

Mark hat beim Gegenprüfen des Kästchen-Overflow-Fixes selbst einen vierten
Punkt gefunden (mit Screenshots belegt): der „⚡ Treffer eintragen"-Knopf
(Rüstungsrechnung) hatte noch ein rohes `<input type="number">` für die
Stärke, optisch inkonsistent zum neuen Zahlenpad in Gesundheit/Willenskraft.
Fix: `frontend/src/shell/Zahlenpad.tsx` — den Ziffernblock aus
`ZustandFenster.tsx` als eigene Komponente extrahiert, jetzt in beiden
Fenstern verwendet. `docs/wiki/concepts/attribute-und-fertigkeiten.md`
nachgezogen.

## [2026-09-18] update | Rüstung: Durchlass durch Schadensreduktion ersetzt

Mark, nach dem ersten echten Praxistest am Spieltisch: "Durchlass ist ein
dummer Wert, sorry... wir ersetzen ihn durch Schadensreduktion, wieviel
Schaden von der Rüstung absorbiert wird, und alles darüber hinaus geht durch
bzw. wird eben eins runter gesetzt." Kompletter Umbau des zweiten
Rüstungswerts:

- Bedeutung gedreht: "niedriger=besser, Größe der Lücke" → "höher=besser,
  wie viel Schaden abgefangen wird" (klassischer Soak-Wert)
- Design-Entscheidung im Gespräch geklärt: absorbiert = min(Stärke,
  Reduktion), Rest kommt durch; Reduktion sinkt gestuft mit dem
  Kästchen-Anteil (>50% voll, >25% halb, sonst ein Viertel) statt einen
  eigenen Aktuell-Wert zu brauchen — Marks Idee, mit dem Vergleich
  Lederjacke (bleibt konstant) vs. Bombenschutzanzug (wird spürbar
  schwächer); Kästchen-System und Abstufung blieben unverändert
- Zwei alte Test-Rüstungen in der echten Kampagne auf Marks Wunsch gelöscht
  statt migriert ("einfach löschen")

Geändert: `backend/app/kampf/ruestung.py` (Kernformel neu), `items/schemas.py`,
`items/repository.py`, `items/routes.py`, `traits/routes.py`,
`tests/test_ruestung.py` (alle 26 Tests neu geschrieben), sowie
`frontend/src/items/api.ts`, `traits/bogenApi.ts`, `traits/Charakterblatt.tsx`,
`traits/CharacterSheetPanel.tsx`, `kampf/Kampfkarte.tsx`. `docs/api/ruestung.md`
komplett neu geschrieben (mit Abschnitt zur abgelösten Durchlass-Fassung),
`docs/wiki/concepts/ruestung-kaestchen-durchlass.md` überarbeitet.

Verifiziert: `tsc --noEmit` fehlerfrei, alle 408 Backend-Tests grün, live
gegen die echte Kampagne getestet (Anlegen, Ausrüsten, Treffer mit
absorbiert/durchkommend-Rechnung nachvollzogen, Reparatur) — alle
Testgegenstände danach wieder gelöscht.

## [2026-09-18] update | Rüstungstreffer: Vorschlags-1 wurde angehängt statt ersetzt

Mark: „steht automatisch 1 als Vorschlag, tippe ich 4 wird daraus 14 statt 4".
Fix: `staerkeIstVorschlag`-Flag in `RuestungsTreffer.tsx` — der erste
Tastendruck ersetzt die Vorgabe komplett (wie ein markiertes Eingabefeld),
danach hängt das Pad normal an. Gesundheit/Willenskraft waren nicht
betroffen, die starten leer statt mit einer Vorgabe.

## [2026-09-18] update | Doppelter Gewicht/Traglast-Schalter entfernt

Mark: der „Zugang"-Bereich hatte einen eigenen „Spielregeln"-Abschnitt mit
demselben Gewicht/Traglast-Schalter wie das eigentliche Einstellungen-Fenster
— „das war einfach eine der ersten Sachen, die wir gemacht haben", nie
aufgeräumt. Fix: Abschnitt aus `frontend/src/players/SpielerVerwaltung.tsx`
entfernt (inkl. ungenutztem `einstellungenApi`-Import und State), der
Schalter existiert unverändert weiter in `campaigns/EinstellungenFenster.tsx`
(über die Werkzeugleiste erreichbar, nicht bereichsgebunden) — kein
Verschieben von Logik nötig, reines Duplikat-Löschen.

`docs/wiki/entities/ui-konzept-commlink.md` um neuen Abschnitt
„Kampagnenweite Einstellungen — ein Ort, nicht zwei" ergänzt, `CLAUDE.md`
Stand-Sektion (18.09.2026) nachgezogen.

## [2026-09-18] update | Bug: frisch aktivierte Rüstung nicht ausrüstbar

Mark: neuen Gegenstand erstellt, im Bearbeiten-Formular zur Rüstung gemacht,
landete beim Ausrüsten immer im Mitgeführten (SL und Spieler gleichermaßen).
Ursache gefunden: `create_gegenstand` zieht `ruestungKaestchenAktuell` auf
`Max` nach, `update_gegenstand` (der PATCH-Pfad des Bearbeiten-Formulars)
tat das nicht — die 409-Wiederanlegen-Sperre gegen zerschossene Rüstung
(siehe `docs/wiki/concepts/ruestung-kaestchen-durchlass.md` Punkt 6) griff
dadurch bei jeder frisch aktivierten Rüstung sofort, obwohl nie getroffen.

Fix in `backend/app/items/repository.py::update_gegenstand`: zieht
`ruestungKaestchenAktuell`/`ruestungDurchlassAktuell` nach, aber nur wenn das
Stück vorher `ruestungKaestchenMax == 0` hatte — bereits aktive, beschädigte
Rüstung bleibt beim Bearbeiten anderer Felder unangetastet (durch zwei
Gegenproben gegen die echte Kampagne bestätigt, testgegenstände wieder
gelöscht, kein Unittest ergänzt mangels DB-Fixture im bestehenden Testmuster).

`docs/wiki/concepts/ruestung-kaestchen-durchlass.md` Punkt 7 und `CLAUDE.md`
nachgezogen.

## [2026-09-18] create | Party-Feature: wiederentdeckte Vision umgesetzt

Mark wollte Spieler zu einer "Party"/"Spielgruppe" zusammenfassen können,
um sie gemeinsam einem Ort oder Event zuzuordnen (z.B. "die Gruppe betritt
eine Bar"), abgegrenzt von Fraktionen (dauerhafte Organisationen mit Zielen/
Ressourcen). Beim Nachschauen im Git-Verlauf gefunden: **diese Idee gab es
schon** — 28.08.2026 in `CLAUDE.md` festgehalten, beim großen
Verschlankungs-Commit (2500→170 Zeilen) verlorengegangen, nur ein toter
Verweis in `docs/ui-konzept.md` blieb übrig. Marks damalige Formulierung war
sogar präziser: *"Spieler bilden nicht immer eine einzige feste Gruppe —
sie können sich aufteilen, wodurch mehrere gleichzeitige, temporäre Partys
entstehen."*

Design-Entscheidungen im Gespräch geklärt:
- Eine Person ist höchstens in einer Party gleichzeitig (automatischer
  Wechsel statt Doppelmitgliedschaft)
- Party ist ein dauerhaftes Objekt, kein Wegwerfobjekt
- Gemischte Mitgliedschaft (PC+NPC+Begleiter) erlaubt
- **Neu gegenüber der alten Notiz:** höchstens eine Party pro Kampagne ist
  "aktiv" — Mark: die aktive Party soll später die Musik auslösen, die zu
  ihrem Aufenthaltsort gehört (Spotify/Yamaha-MusicCast-Anbindung). Damit
  bekommt die alte Vision einen konkreten neuen Zweck, den es 28.08. noch
  nicht gab.

Neues Backend-Modul `backend/app/party/` (Schema, Repository, Routes) nach
dem Muster von `begleiter/` — zwei neue Beziehungstypen
(`MITGLIED_VON`, `BEFINDET_SICH_AN`), beide mit "alte Kante weg, neue rein"-
Logik wie bei der Gegenstands-Ablage. Neuer Frontend-Bereich (👥-Symbol,
Kachelraster + Bearbeiten-Fenster) nach dem Muster von `begleiter/`.

Verifiziert live gegen die echte Kampagne: Party anlegen, zwei Mitglieder
aufnehmen, Aufenthaltsort setzen, Aktiv-Exklusivität geprüft (zweite Party
aktivieren deaktiviert automatisch die erste), Mitgliedschaftswechsel ohne
Doppelmitgliedschaft bestätigt — alle Testobjekte wieder gelöscht.
`tsc --noEmit` fehlerfrei, alle 408 Backend-Tests weiterhin grün.

Dokumentiert: `docs/api/party.md` (neu), `docs/wiki/entities/party-feature.md`
(neu), `docs/wiki/entities/neo4j-datenmodell.md` (neue Beziehungstypen
ergänzt), `CLAUDE.md` (Projektstruktur, Stand der Umsetzung, Zuletzt gebaut,
Spotify-Punkt bei geplanten Features verlinkt).

**Bewusst zurückgestellt (Phase 2):** Marks Inventar-Idee (Party-Mitgliedern
gegenseitig Gegenstände geben können) — eigenes, unabhängiges Feature mit
neuer Berechtigungsregel, sollte Phase 1 nicht aufblähen.

## [2026-09-18] update | Anlegen-Popup statt Inline-Formular

Mark hatte den fertigen Bereich getestet und bemängelt: "es ist leider
nicht im Stil vom Rest, bitte mache den party anlege button so das ein
popup aufgeht das nach dem namen fragt, vielleicht kann man in dem popup
auch gleich angeben wer in der Party ist" — Verstoß gegen die UI-
Konvention (Dialoge/Listen-Bearbeitung immer als Commlink-Popup, nie
Inline-Formular). Fix nach dem Muster von `rassen/RassenUebersicht.tsx`
(dort schon korrekt umgesetzt): "+ Neue Party" öffnet jetzt ein
`Fenster`-Popup mit Namensfeld und einer Checkbox-Liste aller Personen zur
Sofortauswahl, statt eines Inline-`<form>` auf der Übersichtsseite.

## [2026-09-19] update | Neonflackern verstärkt (Ameisenkrieg-Rauschen + Bildverzerrung)

Mark nach dem Praxistest: *"das flackern ist zu kurz, könntest du die länge
mindestens verdreifachen"*, gewünschtes Bild: *"wie bei einem alten
Fernseher wo das Bild kurzzeitig mit schwarz-weißen Ameisenkrieg-Flecken
übersäht ist aber das Bild drunter noch verzerrt durchscheint"*.

Umsetzung in `frontend/src/shell/CommlinkShell.tsx` (`Stoerung`) +
`commlink.css` (`.cl-stoerung`):
- Dauer 0,45s → 1,6s (mehr als verdreifacht, `STOERUNG_MS`)
- Drei übereinanderliegende Schichten statt nur Farbtönung: Neon-Tint
  (Basis, wie zuvor), SVG-`feTurbulence`-Filter für Schwarz-Weiß-Rauschen
  (`mix-blend-mode: overlay`), `backdrop-filter` für sichtbare Verzerrung
  des durchscheinenden Inhalts
- `steps(1, end)` in mehreren harten Schüben statt weichem Fade

`tsc --noEmit` fehlerfrei geprüft. Commit `6450f62`.

Dokumentiert: `docs/wiki/entities/ui-konzept-commlink.md` (neuer Abschnitt
„Das Gerät stört mit"), `docs/ui-konzept.md`, `CLAUDE.md` (Zuletzt gebaut),
`docs/wiki/index.md` (Zusammenfassungszeile).

## [2026-09-20] update | Wiki-Editor am Handy: lesbare Schriftgröße

Mark berichtete, der Editor-Text im Story-Wiki sei am Handy nicht lesbar
(zu klein), Vollbild-Layout sollte aber bleiben. Ursache: globale
Basisschriftgröße 16px, keine Handy-spezifische Anpassung im Editor.

Fix: `frontend/src/wiki/wiki.css`, neue `@media (max-width: 599px)`-Regel
für `.wk-editor .ProseMirror` (18px/1.6, Überschriften 26/21/18px). Rein
clientseitig, kein neuer/geänderter Endpunkt, daher kein `docs/api/`-Eintrag.
`tsc -b` fehlerfrei.

Dokumentiert: `docs/wiki/entities/ingame-wiki-feature.md` (neuer Abschnitt),
`docs/wiki/index.md` (Zusammenfassungszeile), `CLAUDE.md` (Zuletzt gebaut).
Betrifft nur einen Teilaspekt von CLAUDE.md Punkt 13 („Handy-Ansicht für
Story-Wiki + Ideenschmiede") — Seitenbaum/Kachel-Übersicht/Verweis-Auswahl
am Handy bleiben offen.

## [2026-09-20] create | Wiki-Rechtschreib-/Grammatik-/Logikprüfung

Erster Teil von Marks angekündigtem KI-Auftrag ("Auto-Verknüpfung machen wir
danach") — die Fehlerprüfung im Wiki-Editor. Neues Backend-Modul
`backend/app/ki/wiki_pruefung.py`: `pruefe_seite()` (eine Seite, Editor-
Knopf) und `sweep()` (alle Seiten, Einstellungen-Knopf, überspringt
unveränderte via SHA-256-Hash `pruefHash` am `WikiSeite`-Knoten). Drei neue
Endpunkte unter `/api/campaigns/{id}/ki/wiki/*`, dokumentiert in
`docs/api/ki.md` (neu angelegt, `docs/api/README.md` verlinkt es).

Logikfehler nutzen den freigegebenen Kampagnenkontext (`sammle_kontext()`,
dieselbe Quelle wie der NPC-Generator). Erster Testlauf zeigte einen
Fehlalarm: ein neu eingeführter, in der Welt noch unbekannter Name wurde als
"Logikfehler" gemeldet — Prompt nachgeschärft ("NUR ein direkter Widerspruch
zu einer bereits bestehenden Tatsache, ein unbekannter Name ist KEIN
Fehler"), danach korrekt: nur echte Rechtschreib-/Grammatikfehler blieben.

Frontend: `frontend/src/wiki/PruefungPopup.tsx` (neu, gemeinsam genutzt von
`WikiEditor.tsx` und `campaigns/EinstellungenFenster.tsx`). Jeder Befund
zeigt Zitat+Vorschlag, "✓ Übernehmen" ruft die Backend-Route (ersetzt den
Text direkt im gespeicherten TipTap-Dokument, auch wenn die Seite nicht
offen ist), "↷ Zur Textstelle" nur im Editor verdrahtet (sucht/markiert via
`editor.state.doc.descendants()`).

Verifiziert: Backend-Import-Check, Routenregistrierung (`openapi.json`
zeigt alle drei Pfade), End-to-End gegen echte Neo4j-DB + echten
Mistral-Call (5 Rechtschreibfehler + 1 Grammatikfehler korrekt erkannt,
"Übernehmen" ersetzte den Text im Dokument, zweiter Sweep-Lauf übersprang
die unveränderte Seite korrekt), `tsc -b` fehlerfrei.

Dokumentiert: `docs/wiki/entities/ki-integration.md` (neuer Abschnitt),
`docs/wiki/index.md` (Zusammenfassungszeile), `CLAUDE.md` (Zuletzt gebaut +
Punkt 3 als teilweise erledigt markiert), `docs/api/ki.md` (neu),
`docs/api/README.md` (Tabellenzeile). Skill-Referenz
`ki-gemini-integration.md` um den vollen Bauverlauf ergänzt.

## [2026-09-22] update | Decker/Neuroweaver/KI-Skills auf 6 erweitert + drei Folgefixes

Marks Vorschlag vom 20.09. (siehe `CLAUDE.md` Punkt 9) umgesetzt: zwei neue
NeuroWeaving-Fertigkeiten **Electronic Warfare** ("Rauschen" — Ortungs-
tarnung, kein Angriff, Radius+Dauer aus einer Probe) und **Matrix-Navigation**
(Erfolgsstufen finden Systeme bis hin zu Backdoors). Gilt für NeuroWeaver,
Decker (neue Deck-Werte `deckElectronicWarfare`/`deckMatrixNavigation`) UND
KI. Katalog: `backend/app/traits/seed.py`. Cyberdecks als echte Gegenstände
bewusst nicht Teil dieser Arbeit (Mark macht das separat).

Auch: Spotify-Eintrag in `CLAUDE.md` Punkt 4 auf "fertig, keine Yamaha-
Anbindung geplant" korrigiert (war zuvor fälschlich noch als offen markiert).

**Vier Folgefehler beim ersten Praxistest gefunden** (Mark erstellt einen
Neuroweaver "Cyborg") — alle in `docs/wiki/concepts/neuroweaving-decking.md`
unter "Entwicklung" im Detail:

1. NeuroWeaving-Grundwert fehlte in der Freebee- und LevelUp-Anzeige
   (`Charaktererstellung.tsx`/`LevelUp.tsx`) — feste Kategorienliste kannte
   `NeuroWeavingWert` nicht, nur die sechs Fertigkeiten darunter.
2. Grundwert-Maximum stand auf 10 (wie Hexkraft), sollte aber 6 sein: anders
   als Hexkraft (allein gewürfelt) wird NeuroWeaving immer mit einer
   Fertigkeit kombiniert — bei Max 10 hätte der Grundwert allein den
   Pool-Deckel ausschöpfen können.
3. Derselbe Anzeige-Fehler wie Punkt 1 auch im Charakterblatt selbst
   (`Charakterblatt.tsx`) — dritte, unabhängige Fundstelle.
4. Probenauswahl (`Probe.tsx`) verlangte beim Klick auf eine Fertigkeit
   einen Pflichtklick auf den einzigen möglichen Partner (den Grundwert) —
   jetzt automatisch vorausgewählt, wenn nur ein Kandidat existiert.

**Zwei weitere Anpassungen auf Marks Wunsch:**

5. "Wilde Magie" bei NeuroWeaving in **"Overclock"** umbenannt — war ein
   Copy-Paste-Rest von der Hexkraft-Seite und passte inhaltlich nicht
   (Nervensystem übers Limit pushen statt Magie wirken). Gleiche Mechanik
   (Bonuswürfel bis Willenskraft, Zielwert ansagen, Rückstoß-Willenskraftwurf
   bei Erfolg) — nur Name und Hinweistexte geändert, `magie.ts`/`Probe.tsx`/
   `WillenskraftFrage.tsx`.
6. NeuroWeaving-Pool-Deckel von 10 auf **12** angehoben — seit der
   Skill-Erweiterung ist überall 6 das neue Maximum, 10 wirkte als
   Pool-Deckel unpassend niedrig; 12 passt zum bereits etablierten "rundes
   Maximum"-Muster im Tool (natürliches Gesundheitsmaximum). Wilde Magie hat
   bewusst weiterhin **keinen** Pool-Deckel — andere Ausgangslage (ein Wert
   allein bis 10, Rückstoß-Risiko als Bremse statt Zahlenlimit); auf
   Nachfrage mit Mark bestätigt, kein Widerspruch.

Verifiziert: Backend-Tests grün (61 relevante + Gesamtlauf bis auf einen
vorbestehenden, unrelated Fehler bei der Spotify-Route), `tsc -b` fehlerfrei
nach jedem Schritt, gegen echte Neo4j-DB verifiziert (6 TraitDefs korrekt
angelegt, Max 6, sortOrder 1-6, Grundwert-Max 6 nach `seed_traits()`-Neustart
übernommen).

Dokumentiert: `CLAUDE.md` Punkt 9 (vollständig, alle sechs Fixes),
`docs/regeln-neotopia.md`, `docs/wiki/concepts/neuroweaving-decking.md`
(Haupt-Zielseite, "Entwicklung"-Abschnitt), `docs/wiki/index.md`
(Zusammenfassungszeile + Datum).

## [2026-09-23] update | KI-Bildgenerierung (lokal Fooocus + cloud Gemini)

Sechster Anwendungsfall auf `entities/ki-integration.md`: neues Modul
`backend/app/ki/bildgenerierung.py`, zwei pro Aufruf wählbare Provider
(Dropdown im neuen `frontend/src/ki/KiBildPopup.tsx`) — cloud (Gemini
`gemini-2.5-flash-image`) und lokal (Fooocus über einen eigenen
Wrapper-Prozess `C:\DEV\Fooocus\pnptool_server.py`, bewusst außerhalb des
Repos). Neue Routen `POST .../ki/bild-prompt` (Prompt-Vorschlag) und
`POST .../ki/bild-generieren` (liefert nur eine Vorschau, speichert nichts)
sowie die Spieler-Pendants `/api/spieler/mein-bild-ki-prompt` +
`/mein-bild-ki` fürs eigene Charakterportrait. Eingebunden an Person/Event/
Ort/Fraktion/Gegenstand (SL) und Spieler-Portrait. Details: `docs/api/ki.md`,
`docs/api/auth.md`, `docs/wiki/entities/ki-integration.md`.

Verifiziert: Backend-Import, alle Routen im OpenAPI-Schema, `tsc -b`
fehlerfrei, echter E2E-Call (Prompt-Vorschlag) gegen laufendes Backend +
echte Neo4j-Daten + echten Gemini-Key erfolgreich; Bildgenerierung für
beide Provider je einmal live getestet. **Offen:** kein Klicktest von
`KiBildPopup.tsx` im laufenden Frontend (nur `tsc -b` geprüft) — Mark prüft
das selbst; der Fooocus-Wrapper muss manuell als Hintergrundprozess laufen,
sonst schlägt der "lokal"-Provider fehl.

Dokumentiert: `CLAUDE.md` ("Zuletzt gebaut" + Punkt 3 "KI-Integration" +
Punkt 11 "Charakterportrait im Spieler-Menü"), `docs/api/ki.md`,
`docs/api/auth.md`, `docs/wiki/entities/ki-integration.md`,
`docs/wiki/index.md` (Zusammenfassungszeile).

## [2026-09-23] update | Wiki-Import per Dokument-Upload (.docx/.pdf)

Siebter Anwendungsfall auf `entities/ki-integration.md`: neues Modul
`backend/app/ki/wiki_import.py`. SL lädt ein Word- oder PDF-Dokument hoch
(`POST .../ki/wiki/import`, Multipart) — die KI erkennt die Struktur
(Überschriften/Kapitel: .docx-Formatvorlagen "Heading 1".."Heading 9" als
`#`-Präfixe mitgegeben, .pdf rein am Textmuster) und teilt den Text
automatisch in eine oder mehrere Wiki-Seiten-Entwürfe auf
(`istEntwurf=true`, Eltern-Kind-Hierarchie über `elternIndex` aus der
KI-Antwort). Dokumente über 60.000 Zeichen werden abgelehnt statt
unvollständig importiert.

Pro neu angelegter Seite läuft automatisch die bestehende
Auto-Verknüpfung (`auto_verknuepfung.py`, unverändert wiederverwendet,
alle Vorschläge sofort angewandt statt einzeln bestätigt wie beim
manuellen Knopf). Frontend: `frontend/src/ki/WikiImportPopup.tsx`
(Commlink-Stil), Knopf `⇪✨` in `WikiAnsicht.tsx` neben "+ Neue Seite",
Ergebnis-Liste springt zur Prüfung in die bestehende Ideenschmiede.

Verifiziert: Backend-Import ok, Route im OpenAPI-Schema, `tsc -b`
fehlerfrei, echter E2E-Testlauf gegen laufendes Backend + echte Neo4j +
echten Mistral-Call — Test-.docx mit 2 Kapiteln + 2 Unterkapiteln ergab 5
korrekt verschachtelte Entwurfs-Seiten; eine vorab angelegte Person wurde
per Auto-Verknüpfung korrekt wiedererkannt (keine Dublette), mehrere
unbekannte erwähnte Entitäten automatisch als Entwürfe samt
Beziehungskanten angelegt. **Offen:** kein Klicktest von
`WikiImportPopup.tsx` im laufenden Frontend (nur `tsc -b`); PDF-Pfad
ungetestet (nur .docx real durchlaufen); die 60.000-Zeichen-Grenze ist
eine Schätzung, kein ermitteltes Kontextfenster-Limit.

Dokumentiert: `CLAUDE.md` ("Zuletzt gebaut" + Punkt 3 "KI-Integration",
Wiki-Import von offen auf gebaut gesetzt), `docs/api/ki.md`,
`docs/wiki/entities/ki-integration.md`, `docs/wiki/index.md`
(Zusammenfassungszeile).

## [2026-09-27] update | entities/ui-konzept-commlink

Autosave für Beschreibung/Notizen außerhalb des Wikis: Mark verliert am
Tablet regelmäßig ungespeicherten Text (Standby → Reload → Text weg). Neuer
generischer Hook `frontend/src/shell/autosave.ts` (`useAutosave`), gleiches
Timing wie im Ingame-Wiki (1200ms Debounce + Flush beim Verlassen), aber
eigenständig statt eine Kopie der Wiki-Logik.

Eingebaut in alle Beschreibungs-/Notizen-RichTextEditoren: Ort-, Fraktion-,
Event-, NPC-, PC-, Begleiter-, Critter-, KI-Detail-Popups sowie das
Gegenstand-Bearbeiten-Fenster (`CharacterSheetPanel.tsx`, dort NUR
Beschreibung/Notizen — der Rest des Formulars bleibt hinter dem
bestehenden "Speichern"-Knopf, Marks ausdrückliche Entscheidung). Bewusst
ausgenommen: Namensfelder (bleiben `onBlur`), `KurzLangListe.tsx`
(Ziele/Ressourcen), `VerbindungAnlegen.tsx`. Keine Statusanzeige wie im
Wiki — still im Hintergrund.

Verifiziert: `tsc -b` sauber, alle Diffs vor dem Commit einzeln
gegengelesen. **Kein Klicktest** — Mark bittet, am Tablet zu prüfen, ob
Standby+Reload den Text jetzt hält.

Dokumentiert: `CLAUDE.md` ("Zuletzt gebaut" + neuer "Offen"-Punkt),
`docs/wiki/entities/ui-konzept-commlink.md` (neuer Abschnitt),
`docs/wiki/index.md` (Zusammenfassungszeile).

## [2026-10-10] create | entities/hintergrund-baukasten-feature (geplant)

Mark fragte beim Andromeda-Test der neuen Achievements, ob eine
Hintergrund-Bearbeitung automatisch mit den Achievement-Belohnungen
synchronisiert. Antwort: teilweise, mit bekannter Schwachstelle —
`Achievement.belohnungsHintergrund` referenziert den Hintergrund-Namen als
Text, kein ID-Fremdschlüssel; Umbenennen/Löschen bricht die Verknüpfung
still. Neue Seite dokumentiert Ist-Zustand (Hintergründe fest im Code,
`traits/erstellung.py::HINTERGRUENDE`, ruleset-weiter TraitDef-Katalog,
keine UI zum Bearbeiten), die Schwachstelle im Detail und die zentrale
offene Designfrage für die nächste Session: campaign-gebundener Baukasten
wie bei Zusatzfertigkeiten, oder Editor direkt auf dem bestehenden
ruleset-weiten Katalog. Gegenseite in `achievements.md` (neuer Punkt unter
"Offene Fragen") verlinkt. `index.md` um Zeile ergänzt (Seiten 35→36).
Reine Konzept-Session, kein Code.

## [2026-10-10] update | hintergrund-baukasten-feature entschieden

Mark: Baukasten ja. Zwei Schichten — narrativer campaign-Katalog (wie
Zusatzfertigkeiten, alter Zehner-Katalog minus Mentor/Kontakte als Seed)
und Mechanik fest im Code (Mentor, Kontakte). Kein generisches
Mechanik-Feld. KI-Charaktere müssen `erstellung.pruefe()` überstehen
(Roh-Ratings waren zu hoch). Mentor: Beschreibung darf Weg verbiegen,
Rasse aus Kontext wenn freigegeben sonst PC, Paket Profi, 20×N EP,
Plan-Autosteigerung (sparen statt Resteverwertung), Auto-Verbindungen,
Auto-Bild, Ideenschmiede bis Übernehmen. Kontakte: voller KI-Charakter
ohne EP-Leiter. Spieler-UI: Button am Blatt. Gegenstände am Mentor nicht
v1. `achievements.md`, `charaktererschaffung.md`, `erfahrung-und-steigern.md`,
`ki-integration.md`, `SCHEMA.md`, `index.md` nachgezogen. Code folgt.

## [2026-10-10] update | KI-Charaktere durch Spieler-Erstellung

✨-NPC-Generator schreibt keine Roh-Ratings mehr (`_setze_traits`).
`erstellung.aus_ki_antwort` mappt das KI-JSON auf das Erstellungsformular
und lässt `pruefe()`/`endwerte()` entscheiden. Regelwidrig → 422, kein
Knoten. Tests: `test_ki_charakter_erstellung.py`, zwei Fälle in
`test_ki_idee_typen.py`. Mentor/Kontakte können denselben Pfad später
nutzen.

## [2026-10-10] update | narrativer Hintergrund-Katalog

Campaign-Knoten `Hintergrund` wie Zusatzfertigkeiten (kein Freigabe-
Schalter). Seed der alten Liste minus Mentor/Kontakte, wenn der Katalog
leer ist. SL-Tabelle im Burgermenü. Erstellung und Mentor-Pipeline
nutzen den Katalog noch nicht.

## [2026-10-10] update | Mentor-Text ist VERBINDUNG.beschreibung

Mark: das Beschreibungsfeld Mentor ist kein extra Hintergrund-Text,
sondern die `beschreibung` der Neo4j-`VERBINDUNG` (typ „Mentor“, analog
Kontakt). KI liest denselben Kantentext. Kein zweites Property.

## [2026-10-10] update | Schulden / Kredithai entschieden

Hintergrund heißt **Schulden**. Kredit-Freebees 1:1 Punkte, nicht aus dem
5er-Budget. Rassen-Häkchen `kannKredithai`, NPC-Flag `istKredithai`
(bestehenden Hai wiederverwenden).

## [2026-10-10] update | Schulden-Spawn an der Erstellung

Kredit-Freebees > 0: bestehenden `istKredithai` wiederverwenden, sonst
Stub in der Schmiede. Kanten `HAT_KREDITHAI`, `VERBINDUNG` Schuldet,
`KENNT` (Chat zu). KI-Füllung bewusst später.

## [2026-10-10] update | KI-Charakter an Spieler-Erstellung gebunden

✨-Charakter muss Rasse, Weg, Attributkontingente, ein Fertigkeitspaket
und Freebees (Geld + Details, Budget) durch `pruefe()` bringen. Schema
kennt Kredit/Eigenkapital. Ein Nachbesser-Versuch, kein Roh-Rating-Fallback.

## [2026-10-23] update | KI-Ambition nur aus Vorlagen

✨-Charakter darf Ambition und Verlangen nicht mehr frei schreiben. Beides
ist ein Enum der Archetyp-Namen aus `vorlagen.local.json`. Unbekannter Text
landet leer. Erklärungstexte gehen nicht in den Prompt. Spieler-Erstellung
bleibt Freitext. Siehe [[entities/ki-integration]].

## [2026-10-31] update | Sphären-Stufen in der Regelfassung nachgezogen

Die 6-Stufen-Texte (Magier und Götter) lagen seit 23.10. in den Tooltips.
`docs/regeln-neotopia.md`, [[concepts/attribute-und-fertigkeiten]] und
[[comparisons/regelwerk-excel-vs-aktuell]] sagten noch „Sphären bleiben bei 5“.
Stufentitel aus dem 23.10.-Gespräch jetzt in der Regelfassung, neue
Zwischenstufe je Sphäre fett. Siehe [[concepts/magie-hexkraft]].

## [2026-10-31] gebaut | Probenfenster zeigt Fertigkeits- und Sphären-Kurztext

Klick auf Sphäre/Gott oder Fertigkeit zeigt den Tooltip-Kurztext im
Probenfenster, Detail-Knopf öffnet die Langfassung. Größenleiter und
Würfel/Attribute bleiben. Siehe [[entities/ui-konzept-commlink]].

## [2026-11-05] update | Credstick-Laden im Objekt

Aufladen, Abheben und SL-Geld-erzeugen sitzen oben im Credstick-Objekt
(`CharacterSheetPanel`) und oben im Spieler-Fenster (`GegenstandKachel`),
nicht mehr nur in der Inventar-Kachel. Betrag steht auf der Kachel.
Siehe [[entities/gegenstand-transfer]].

## [2026-11-07] update | Kampfende klinkt Rigger und Decker aus

Kampfende löscht neben Matrix-Hot jetzt auch die Hot-Drohne des Riggers. Siehe [[concepts/drohnen-fahrzeuge]].

## [2026-11-07] update | Battlemap-Menüpunkt für Spieler entfernt

Spieler erreichen die Karte nur über „Karte öffnen“ im Kampf. Siehe [[entities/battlemap]].

## [2026-11-07] update | Messenger-Verlauf folgt chatOffen

Lesen und Senden nutzen dieselbe Offen-Regel wie die Liste. Siehe [[entities/kontakte-messenger]].

## [2026-11-07] update | SL-Chatfenster im Messenger-Stil

Verlaufs-Popup der SL nutzt Fenster und msg-Klassen statt eigenem durchsichtigem Overlay. Siehe [[entities/kontakte-messenger]].

## [2026-11-08] update | Battlemap: Schwenken per Ziehen, großer Token füllt drei Felder

Ansicht-Schieben-Knopf entfällt, Ziehen auf der leeren Karte schwenkt lokal. Großer Token mit Blick-Ring um alle drei Felder. Siehe [[entities/battlemap]].

## [2026-11-10] update | Drogen: Inventar-Knopf im SL-Kampfmenü

Kampfwerte-Fenster eines NPC hat neben „Ganzer Bogen“ einen Knopf „Inventar“, dort schlucken. Wirkung geht an den Besitzer der Droge. Siehe [[entities/drogen]].

## [2026-11-10] update | Augments: NPC-Inventar Upgraden mit Auswahl und Ausbau

Upgraden-Knopf im NPC-Inventar öffnet das Träger-Fach der Werkbank statt blind das erste freie Upgrade. Siehe [[concepts/augments-ausruestung]].

## [2026-11-11] update | Tutorial-Shop: KI-Kommentar nach dem Einkauf entfernt

Mark: stört und ist nicht lustig. Kein Popup, kein KI-Aufruf beim Schließen des Tutorial-Shops mehr. Route bleibt ungenutzt. Siehe [[entities/nebenfiguren]] für den Tutorial-Shop-Verkäufer.

## [2026-11-11] update | Bärbel: fliegendes Buch als Pet an einem Gegenstand

`petArt` auch am Gegenstand (Besitz reicht, verschlossene Kiste/weggeworfen sperrt), Flug-Logik `flug.ts`, drei Gestalten mit Verwandlung, Blinzeln, verlorene Seiten. Siehe [[entities/critter-pet]].

## [2026-11-11] update | Bärbel liest vor, Pets treffen sich

Lesung alle 15 Minuten Anwesenheit bis zum Antippen. Drache niest sie an, Blitz verkohlt ihn, Tentakel schleimt ihn. Spuren im Kampf ausgeblendet. Siehe [[entities/critter-pet]].

## [2026-11-12] update | Bärbel liest im großen Buch

Statt Tafel mit frechem Kommentar: großes aufschlagendes Buch, nur der (umformulierte) Vers, alte Schrift. Siehe [[entities/critter-pet]].

## [2026-11-12] update | Drache läuft auf Wolken, Bärbel ohne Wiederholung

Wolkenlauf zu Flächen außer Sprungweite (oben am Tablet), Bärbel-Abstand 15–45 min, keine wiederholten Stellen. Siehe [[entities/critter-pet]].

## [2026-11-12] update | Drache schüttelt Ruß ab

Nach Bärbels Blitz bleibt er verrußt, bis er sich schüttelt; Flocken fallen zu Boden. Siehe [[entities/critter-pet]].

## [2026-11-12] update | Eisdrache und Blitzdrache

Zwei neue Pet-Arten (blau/Eis mit Raureif-Spur, silbern/Blitz), gleiche Figur wie der Drache. Siehe [[entities/critter-pet]].

## [2026-11-12] update | Idee: Pets wachsen

Drachen sollen je Sitzung größer/eleganter werden, Bärbel neue Fähigkeiten bekommen — notiert mit Skizze und offenen Achsen. Siehe [[entities/critter-pet]].
