# PnPTool — Projektgedächtnis für Claude

Diese Datei wird von Claude Code automatisch geladen. Sie ist die Quelle der Wahrheit für den Projektstand — bei jeder größeren Änderung aktualisieren. **Bleibt bewusst schlank:** Details wandern nach `docs/api/` bzw. ins Wiki, nicht hier hinein.

## Backlog: Mark denkt noch nach (nicht einfach lostbauen)

- **Offene Popups sollen den Mobil-Reload überstehen** (01.10.2026): Nach
  dem Bereich-Fix (siehe unten) landet man zwar im richtigen Bereich, aber
  ein offenes Popup (Detail-Fenster, Inventar-Fach, Beratung, ...) ist nach
  dem erzwungenen Reload trotzdem wieder zu — mobile Browser/PWAs werfen
  Tabs im Hintergrund aus dem Speicher (OS-Verhalten, nicht verhinderbar).
  Technisch lösbar, aber NICHT mit einem einzigen generischen Mechanismus
  wie beim Bereich: jedes Popup ist State + oft eine ID (z.B. "NPC-Detail
  für Person X", ein ganzer Fach-Stapel im Inventar) — jedes bräuchte
  eigene Wiederherstellungs-Logik nach dem Neuladen der Daten.
  Mark will erst am Spieltisch beobachten, **welche Popups seine Spieler**
  tatsächlich oft offen haben, wenn das Handy gesperrt wird (Vermutung:
  Inventar-Fach oder Charakter-Detail, nicht Einstellungen/Verhandlung),
  bevor gezielt für die 1-2 wichtigsten gebaut wird — lohnt sich nicht für
  alle ~15 Popups im Tool. **Nicht von selbst anfangen, erst wenn Mark
  sagt, welche Popups es betreffen soll.**

- **Zweiter SL-Tisch / Kampagnen teilen** (02.10.2026, nur notiert):
  Richtung 1 — eigener SL, eigene Welt, nicht Marks NeotopiA. Datenmodell
  kann das schon (`GMUser -[:OWNS]-> Campaign`). Offen, nicht bauen:
  Kampagnen **nicht für alle sichtbar** (Liste/Sichtbarkeit); Kampagne in
  Status **unbespielt** ablegen, damit ein anderer SL sie spielen kann
  (Vorlage/Übernahme, Datenmodell offen). Echter Multi-User-Knackpunkt
  ist **Spotify**: Wiedergabe hängt an einem Konto und kommt sonst immer
  auf Marks Gerät. Rest der Isolation (Kampagne, Uploads, Sichtbarkeit)
  ist App-Filter, reicht für einen vertrauten zweiten Tisch. **Nicht
  von selbst anfangen.**

## Offen: Was Mark selbst testen muss

Neueste zuerst. Einmal am Spieltisch/Dev-Server gegengeprüft → hier streichen.

- **Willenskraft-Kostenformel (Chrom) erweitert + Doppel-Bug behoben**
  (12.10.2026, siehe `traits/CharacterSheetPanel.tsx` Zeilen ~275-295, Commits
  `c68df9c`/`2f631d5`/`6aa388e`, alle drei live auf bebop): Ausgangspunkt war
  Marks Quill-Talon-Klingen „Kri'tah" — Steckbrief zeigte 16/32 WK statt der
  erwarteten 4/8. **Root Cause:** ein `useEffect` multiplizierte den vom
  Server bereits bonus-skalierten `wVerlustGenau` ein zweites Mal mit dem
  Bonus (quadratisch statt linear). Nur ein echter Live-Fall gefunden +
  korrigiert (`Unterarm Knochengyroskop`, Vorlage, wVerlust 4→2 per
  Cypher auf bebop); die Klingen selbst waren in der DB bereits korrekt,
  nur die offene Bearbeiten-Vorschau zeigte den Bug unsaved an.
  **Danach erweitert:** `Gesamt-Bonus` zählt jetzt zusätzlich
  `Initiative-Bonus` (1:1) und `Zusatzaktionen` (Bonus-Aktionen pro Kampf) mit.
  Bei Zusatzaktionen `-1` ("jede Runde") wird NICHT der rohe Sentinel addiert
  (würde den Bonus senken), sondern `AMPEL_MAX_FUER_KOSTEN = 3` — dieselbe
  Zahl wie `kampf/booster.py::AMPEL_MAX` (Runden bis zum Überhitzungs-
  Willenskraftwurf). Die Konstante ist in beiden Dateien dupliziert, kein
  gemeinsamer Import — ändert sich `AMPEL_MAX` in `booster.py`, bitte in
  `CharacterSheetPanel.tsx` nachziehen. **Betrifft nur neu/aktiv
  bearbeitete Chrom-Items** (Effekt feuert erst, wenn im Umbauen-Tab eine
  Stufe angeklickt wird) — die 3 bestehenden Reflex-Booster-Vorlagen mit
  fest aus dem Regelwerk importierten Werten sind unangetastet. **Noch nicht
  am Spieltisch getestet:** bitte ein Cyberware-Item mit Initiative-Bonus
  und/oder Zusatzaktionen anlegen/bearbeiten und die resultierende
  Willenskraft-Stufenliste gegenprüfen.

- **Ideenschmiede ✨-Gegenstand: Qualitätsstufe/Preis/WK-Verlust bei Cyberware/
  Bioware/Hexware automatisch** (12.10.2026, siehe `ki/routes.py::
  _chrom_felder_aus_ki`, `items/chrom.py::stufe_fuer_name`/`CHROM_TYPEN`):
  Mark-Wunsch — bisher musste man nach dem KI-Anlegen eines Chrom-Gegenstands
  immer noch manuell die Qualitätsstufe (Hinterhof..Maßanfertigung) anklicken,
  bevor Preis/WK-Verlust/Kraft stimmten. Jetzt wählt die KI `qualitaetsstufe`
  passend zur Beschreibung selbst (Prompt-Beispiele je Stufe), optional
  `koerperzone` und `istWaffe`+`schaden`/`schadenArt` (eingebaute Waffe wie
  Cyberklinge/Kraftarm) — Preis/WK-Verlust/Kraft errechnen sich serverseitig
  aus Gesamtbonus (traitBoni + neueFertigkeiten + Waffenschaden) und
  Qualitätsstufe, exakt dieselbe Formel wie beim manuellen Anlegen. Das
  Bearbeiten-Fenster markiert die so gewählte Stufe jetzt auch beim Öffnen
  (vorher immer unmarkiert, selbst wenn längst ein Preis dranhing). Nur
  `pytest`/Import geprüft, **nie gegen einen echten KI-Call getestet**: bitte
  in der Ideenschmiede „✨ Gegenstand“ einen Cyberware-Wunsch mit erkennbarer
  Qualität eingeben (z.B. "billiges Hinterhof-Chrom" vs. "teuerste
  Konzern-Maßanfertigung") und prüfen, dass Stufe/Preis/WK-Verlust stimmen
  und im Bearbeiten-Fenster markiert sind.

- **Bugfix: Zerstörte natürliche Rüstung heilte nach Rast nicht mehr**
  (12.10.2026, siehe `items/repository.py::natuerliche_ruestungsteile`,
  `traits/routes.py::personen_rasten`/`personen_vollstaendige_heilung`):
  Mark hatte recht — zerstörte Rüstung wird bei 0 Kästchen automatisch ins
  Mitgeführte gelegt (`ablage = RUCKSACK`, siehe `ruestungstreffer`), aber
  `ruestungsteile()` für die Rast-Heilung filtert nur `AUSGERUESTET`. Ein
  zerstörtes Stück fiel damit aus jeder weiteren Abfrage heraus und konnte
  nie mehr heilen, egal wie oft gerastet wurde. Fix: neue Abfrage
  `natuerliche_ruestungsteile` holt `istNatuerlich`-Teile unabhängig von der
  Ablage; nach einer heilenden Rast bzw. der Vollheilung wird ein Stück, das
  dadurch wieder über 0 Kästchen steht, automatisch erneut ausgerüstet
  (`set_ablage(..., "AUSGERUESTET", ...)`). **Bewusst nur für
  `istNatuerlich`** — normale Rüstung bleibt im Mitgeführten liegen und
  braucht weiter den regulären Reparaturweg (Hardware-Probe/Händler). Noch
  nicht am Spieltisch gegengeprüft: eine natürliche Rüstung zerstören lassen,
  rasten, prüfen dass sie wieder im Charakterblatt als ausgerüstet auftaucht.

- **Bugfix: Natürliche Rüstung (Dug'Rah) fehlte im Charakterblatt** (12.10.2026,
  siehe `kampf/ruestung.py::anwende_natuerliche_ruestung`/`traits/routes.py`):
  bestätigter Live-Root-Cause auf bebop (per cypher-shell geprüft):
  `ruestungKaestchenAktuell` kam bei der automatischen `gratisGegenstandId`-
  Zuweisung als Vorlagen-Platzhalter `0` mit und wurde nie auf die
  Widerstandsfähigkeit hochgezogen — `anwende_natuerliche_ruestung` klemmt
  das Kästchen-Max zwar live auf den aktuellen Attributwert, hebt aber nie
  ein zu niedriges Aktuell an. `reihenfolge()` filtert 0-Kästchen-Teile aus
  dem Pool, das Blatt zeigte die ganze Zeile deshalb gar nicht
  (`bogen.ruestung.kaestchenMax > 0`-Check). Zusätzlich defensiv gefixt:
  `ablage` wird bei der Zuweisung jetzt immer explizit auf `AUSGERUESTET`
  gesetzt (war bei Dug'Rah zufällig schon korrekt, muss es aber nicht sein —
  `assign_copy` übernimmt sonst den Vorlagen-Wert unverändert, Schema-Default
  ist `RUCKSACK`). Betroffenes Bestandsitem (Dug'Rah Arena Kämpfer) direkt in
  der Live-DB auf `ruestungKaestchenAktuell=5` korrigiert, Fix committed +
  auf bebop deployed (`10dea3c`). Mark muss nur noch kurz im Browser
  gegenprüfen, dass die Rüstungszeile jetzt am Charakterblatt erscheint.

- **KI-Charakter geht im Tutorial-Shop einkaufen, Mentor/Kontakte-Pipeline**
  (11.10.2026, siehe „Zuletzt gebaut" unten): kompletter neuer Flow, nie im
  Browser angeklickt und nie gegen einen echten KI-Call getestet. Bitte: (1)
  in einem Tutorial-Shop ein paar Waren eintragen, dann in der Ideenschmiede
  „✨ Charakter" auslösen und prüfen, dass der neue NPC tatsächlich Sachen im
  Inventar hat und sein Kapital gesunken ist; (2) einen PC mit Mentor-
  Hintergrundpunkten erstellen und prüfen, dass ein voll ausgearbeiteter
  Mentor-NPC mit Kontakt-Eintrag entsteht; (3) einen PC mit Kontakte-
  Hintergrundpunkten erstellen, prüfen dass leere „Unbekannter Kontakt"-
  Plätze auftauchen, einen antippen, einen Wunsch eingeben und prüfen dass
  daraus ein echter Kontakt mit offenem Chat wird.

- **Mechanik-Hintergründe im SL-Baukasten sichtbar + abschaltbar** (12.10.2026,
  siehe „Zuletzt gebaut" unten): Backend-Tests grün (neue Fälle für die
  Einstellungen-Gates), `tsc -b` sauber. **Nie im Browser angeklickt.** Bitte
  in der Hintergründe-Verwaltung prüfen: oben erscheint ein Block „Mechanik-
  Hintergründe" mit Mentor/Kontakte/Schulden und je einer Checkbox; eine
  ausschalten, dann in der Charaktererstellung eines Spielers prüfen, dass
  der Eintrag aus dem Hintergrund-Pool verschwindet (Schulden: der
  Kredit-Freebee-Regler verschwindet komplett) und wieder auftaucht, sobald
  man es zurückschaltet.

- **Waffenschaden aus der Beratung** (10.10.2026): Sechs Entwürfe auf bebop
  haben jetzt einen Schaden (Kachel und Kampf lesen `kraft`, nicht die
  WoD-Würfel in den Notizen). Nächste KI-Waffe setzt das Feld selbst.
  Bitte die Stufen in der Schmiede gegenlesen — Monofilament und Vibroklinge 4,
  Nadelpistole und Schockstab 2, Plasma-Katana 5, Plasma-Brecher 7.

- **Commlink-/Cyberdeck-Anzeige + Reflex-Booster neu** (10.10.2026):
  `tsc -b` sauber (lokal + im Docker-Build auf bebop verifiziert), Backend-
  Import geprüft. **Nie im Browser angeklickt.** Commlink zeigt jetzt I.C.E.
  (Cyberwall), Cyberdeck alle 6 NeuroWeaving-Bonuswerte (B/S/D/K/Electronic
  Warfare/Matrix-Navigation) — in Übersicht UND Bearbeiten-Bereich des
  Gegenstand-Formulars (SL-Edit UND Spieler-Kachel) sowie im kompakten
  Kachel-Steckbrief (`items/steckbrief.ts`, parallel von Chibi gebaut).
  3 Reflex-Booster-Stufen (Günstig/Militärisch/Illegaler Prototyp) als
  Entwürfe importiert — beim ersten Tabellen-Import übersehen, standen im
  Excel unter einem eigenen Abschnitt. Initiative-Bonus und Zusatzaktionen
  waren danach zwar am Gegenstand gesetzt, aber im Formular weder sichtbar
  noch editierbar (Mark: "wir haben so viel Aufwand betrieben sie mechanisch
  einzubauen, wir sollten auch anzeigen was sie können") — jetzt eigenes
  Eingabefeld im Chrom-Bereich plus Steckbrief-Zeile in beiden Ansichten.
  Bitte einen Reflex-Booster aus der Ideenschmiede freigeben, am Charakter
  als Cyberware einsetzen, im Formular Initiative/Zusatzaktionen gegenprüfen
  und im Kampfmodus die tatsächliche Verschiebung testen (Mechanik selbst
  ist alt, nur Items + Anzeige fehlten).

- **KI-Shop-Anlegen: Fallback + Preis-Richtwerte neu** (10.10.2026):
  `pytest`/Backend-Import grün, live auf bebop gegen die echte Mistral-API
  verifiziert (Gemini war zum Testzeitpunkt 503 überlastet, Mistral übernahm
  automatisch, Preis traf den Richtwert). **Nie über den echten Browser-Klick
  getestet**, nur direkt per Python gegen die Repository-Funktion. Bitte im
  Tutorial-Shop (oder einem anderen Laden) „Mit KI anlegen“ klicken und
  prüfen, dass tatsächlich etwas passiert (auch wenn Gemini gerade überlastet
  sein sollte) und der Preis zur Kategorie passt.

- **Achievements neu gebaut** (siehe „Zuletzt gebaut" 10.10.2026): Backend
  + Frontend komplett, eigene Tests grün, `tsc -b` sauber, Backend startet
  fehlerfrei gegen Neo4j. **Nie im Browser angeklickt.** Mark testet bewusst
  zuerst auf Andromeda (Test-Kampagne), nicht auf bebop — Achievements sind
  komplett pro `campaignId` gescoped, ein "First Kill" auf Andromeda hat
  keinerlei Berührung mit der echten Kampagne. Falls doch mal versehentlich
  auf bebop ausgelöst: Verleihungen folgen dem Papierkorb-Prinzip (kein
  Hard-Delete) — Löschen über die SL-Verwaltung macht das Achievement sofort
  wieder frei vergebbar, kein Backend-Eingriff nötig. Bitte am Spieltisch:
  🏆-Symbol in der Werkzeugleiste (SL + Spieler), ein manuelles Achievement
  anlegen und vergeben, ein AUTO-Achievement (z. B. CHARAKTER_ERSTELLT)
  anlegen und prüfen ob der Vorschlag erscheint, EP-/Hintergrund-Belohnung
  gegenprüfen.

- **Lebenspunkte-Grundwert pro Critter neu** (siehe „Zuletzt gebaut“
  10.10.2026): `pytest tests/test_bogen.py` (5 neue Fälle) grün, volle
  Backend-Suite nur die 8 vorbestehenden (unabhängigen) Fehlschläge,
  `tsc -b` sauber. **Nie im Browser angeklickt.** Bitte im Critter-Fenster
  einer Ratte den neuen Zahleneingabe „Lebenspunkte-Grundwert“ auf 1 setzen
  und im Charakterblatt prüfen, ob die Gesundheit auf 2 sinkt (1 Grundwert +
  1 Widerstandsfähigkeit), danach das Feld wieder leeren und prüfen, ob sie
  zum Standard (6 + Widerstandsfähigkeit) zurückspringt.

- **Vorgefertigte Charaktere + PC↔NPC-Umwandlung neu** (siehe „Zuletzt
  gebaut" 09.10.2026): `pytest` (511/511 der von dieser Änderung berührten
  Tests grün, echter E2E-Test gegen laufende Neo4j für Filter + beide
  Umwandlungsrichtungen + Migration), `tsc -b` sauber. **Nie im Browser
  angeklickt.** Bitte am Spieltisch: im PC-Detail-Popup eines vorgebauten
  Charakters die neue Checkbox „Vorgefertigter Charakter" setzen, prüfen ob
  er danach (und nur dann) im Ersteinstiegs-Fenster eines neuen
  Spieler-Accounts auftaucht; „⇄ Zu NPC machen" an einem PC und „⇄ Zu PC
  machen" an einem NPC ausprobieren, dabei gegenprüfen ob Inventar/
  Charakterbogen/Beziehungen wirklich erhalten bleiben.

- **Beziehungstyp-Konsistenz + „Beziehungen aus Beschreibungen"-Knopf neu**
  (siehe „Zuletzt gebaut" 03.10.2026): nie im Browser angeklickt, nur
  `pytest`/`tsc -b` geprüft. Bitte am Spieltisch: im Verbindungen-Bereich
  den neuen Knopf „✨ Beziehungen aus Beschreibungen" neben „+ Neue
  Verbindung" klicken, prüfen ob aus Beschreibung/Notizen bestehender
  NPCs/Orte/Fraktionen sinnvolle neue Verbindungen vorgeschlagen werden und
  ob vorgeschlagene Beziehungstypen zu bereits verwendeten passen (z.B.
  „kennt" statt einer neuen Formulierung, wenn „kennt" schon existiert).


- **Lesegröße-Zoom neu** (siehe „Zuletzt gebaut" 03.10.2026 — Zoom in
  Beschreibungs-/Notizenboxen): nie im Browser angeklickt, nur `tsc -b`.
  Bitte eine Beschreibung öffnen, A+/A− in der Werkzeugleiste (Editor) bzw.
  über dem Text (Leseansicht) antippen — Schrift sollte in 5 Stufen
  (100–175%) wachsen/schrumpfen, Einstellung nach Reload erhalten bleiben
  und beim zweiten gleichzeitig offenen Popup mitziehen.
- **KI-Entwürfe mit Notizen neu** (siehe „Zuletzt gebaut" 03.10.2026 —
  KI-Entwürfe befüllen jetzt auch die Notizen): nie im Browser angeklickt,
  nur pytest. Bitte eine Beratung führen, ruhig Details reinwerfen, dann
  „Entwurf anlegen" klicken und im angelegten Entwurf das Notizen-Feld
  prüfen — sollte jetzt die Details aus dem Gespräch enthalten, während die
  Beschreibung weiterhin knapp bleibt. Gilt auch für den ✨-KI-Knopf direkt.
- **Sticky-Werkzeugleiste neu** (siehe „Zuletzt gebaut" 01.10.2026 —
  Editor-Werkzeugleiste bleibt beim Scrollen sichtbar): nie im Browser
  angeklickt. Bitte bei einer langen Beschreibung/Notiz prüfen, dass
  „🔒 SL-geheim" & Co. beim Scrollen oben kleben bleiben statt mit
  hochzuscrollen.

- **KI-Provider-Umschalter neu** (siehe „Zuletzt gebaut" 01.10.2026 —
  Kampagnen-Textprovider + Beratungs-Override): Tests (`test_ki_beratung.py`,
  `test_ki_idee_typen.py`, voller Backend-Suite) und `tsc -b`/`vite build`
  grün, aber nie im Browser angeklickt. Bitte Einstellungen-Popup → Abschnitt
  „KI" öffnen, Mistral wählen, eine Ideenschmiede-Generierung auslösen und
  prüfen ob sie merklich anders klingt; danach im Beratungs-Popup den
  kleinen Dropdown neben „+ Neu" testen (sollte die Kampagnen-Einstellung
  für eine Nachricht übersteuern können, ohne sie zu verändern).
- **Verbindungen-Bereich neu** (siehe „Zuletzt gebaut" 01.10.2026 —
  durchsuchbare Auswahl + Suchleiste): nie im Browser angeklickt, nur
  `tsc -b`/`vite build` geprüft. Bitte am Spieltisch den Verbindungen-Punkt
  öffnen und das neue „+ Neue Verbindung"-Popup samt beiden Suchfeldern
  sowie die Suchleiste über der Liste ausprobieren.

Diese Punkte wurden von Agenten gebaut, aber mangels laufendem Frontend-Dev-Server
bzw. GPU-Hardware nur eingeschränkt oder gar nicht verifiziert. Bitte am
Spieltisch/Dev-Server gegenprüfen, danach hier aus der Liste streichen:

- **Zusatzfertigkeiten** (28.09.2026, Abend-Stand — Button + Punktzeilen,
  live auf bebop als `2bf1adc`; siehe „Zuletzt gebaut“ und
  `docs/wiki/entities/zusatzfertigkeiten.md`): bitte hart neu laden, dann
  im Kampagnen-Menü Einträge anlegen (mit UND ohne KI). Charaktererstellung
  → Fertigkeiten-Popup: oben der Button **Zusatzfertigkeiten** öffnet die
  Katalogwahl; gewählte Skills erscheinen als normale Kreise im Raster
  (Paket-Slots, wie Diebeshandwerk). Freebees: nur die Gewählten, +1 aus
  dem Hauptpool. Charakterblatt: Eintrag auch bei rating 0. LevelUp:
  bisheriger "+ Zusatzfertigkeit"-Popup mit EP, unverändert.

- **Autosave für Beschreibung/Notizen** (27.09. + Fix 30.09., siehe „Zuletzt
  gebaut“): Reload-Bug (Popup zu/auf, Tab weg) ist im Code raus. Bitte am
  Spieltisch: in Beschreibung tippen, ~2 Sek. Pause — Fenster und Tab müssen
  bleiben, Text nach Reload noch da. Ort-Popup und Gegenstand-Fenster.
- **Gegenstands-Weitergabe innerhalb der Party** (`WeitergebenPopup.tsx`,
  `VerhandlungPopup.tsx` für `GEGENSTAND_WEITERGABE`, siehe „Zuletzt gebaut“
  unten und `docs/wiki/entities/gegenstand-transfer.md`): Backend-Import und
  `tsc -b` sauber, Zugriffsschutz-Whitelist ergänzt. **Nie im Browser
  angeklickt** — bitte als Spieler einen Gegenstand an ein Party-Mitglied
  anbieten und prüfen, ob das Annehmen/Ablehnen-Popup beim Empfänger kommt
  und der Besitz danach stimmt.

- **Shop-System komplett** (`frontend/src/haendler/`, siehe „Zuletzt gebaut“
  unten und `docs/api/haendler.md`): Übersicht, physisch/digital getrennte
  Shop-Seite, Seltenheitsrahmen, Verhandeln-Integration, Bestellungen,
  KI-Alltagsgegenstand-Erzeugung (Spieler fragt Verkäufer, KI schlägt Preis
  vor, SL-Popup entscheidet) und der SL-Sortiment-Editor (Ware
  hinzufügen/entfernen, Rabatt, Standort — `HaendlerBearbeiten.tsx`).
  Backend komplett per echtem E2E-Test gegen laufendes Backend + Neo4j +
  echten KI-Provider verifiziert (harmloser Wunsch UND Waffen-Ausschluss
  beide grün). **Frontend nie im Browser angeklickt**, nur `tsc -b`
  geprüft (`vite build` läuft, aber Optik/Bedienung ungetestet) —
  Seltenheitsrahmen-Effekte (Glitzern/Zacken/Wabern) sind reine
  Code-Vermutung, bitte am Spieltisch gegenprüfen.
- **Kampagnen-Export/Import** (`EinstellungenFenster.tsx`, Sektion
  „KAMPAGNE“, siehe „Zuletzt gebaut“ unten): Export-Knopf, Import-Upload.
  Backend-Logik komplett per echtem E2E-Testlauf gegen laufendes Backend +
  Neo4j verifiziert (Export → Import → alle Prüfungen bestanden). Nur die
  Frontend-Bedienung selbst ist ungetestet — nie im Browser angeklickt,
  nur `tsc -b` geprüft. Bitte einmal am Dev-Server exportieren und
  importieren, v.a. ob der Downloaddateiname stimmt und nach Import
  automatisch zur neuen Kampagne gewechselt wird.
- **Messenger-Mobil-Fixes** (`Messenger.tsx`/`messenger.css`, siehe „Zuletzt
  gebaut" unten): Hart-Scroll ans Ende, Tastatur-Sichtbarkeit via Visual
  Viewport API, dynamische Sprechblasen-Form — nur `tsc -b` geprüft, das
  Browser-Tool kann `localhost` nicht erreichen (Netzwerksperre), deshalb
  **kein DevTools-Mobil-Emulationstest möglich**, nur Code-Review. Bitte am
  echten Handy testen, v.a. ob der Composer bei geöffneter Tastatur wirklich
  sichtbar bleibt (`visualViewport`-Verhalten variiert je nach
  Android/iOS-Browser).
- **Wiki-Mobil-Drawer** (`WikiAnsicht.tsx`/`wiki.css`, siehe „Zuletzt gebaut"
  unten): Seitenbaum/Inhaltsverzeichnis als Slide-in mit Backdrop und
  Schließen-Knopf, Kachel-Raster der Ideenschmiede + Verweis-Auswähler mit
  größeren Touch-Zielen. Ebenfalls nur `tsc -b` geprüft, kein Browser-Test
  möglich (siehe oben).
- **KI-Bildgenerierung** (`KiBildPopup.tsx`): nie im Browser angeklickt, nur
  `tsc -b` geprüft. Popup öffnet sich an Person/Event/Ort/Fraktion/Gegenstand
  sowie am eigenen Spieler-Portrait. Cloud-Pfad (Gemini) UND lokaler Pfad
  (Fooocus) wurden je einmal echt getestet (siehe „Zuletzt gebaut") — die
  Optik/Bedienung im Popup selbst aber nicht.
- **Fooocus-Wrapper** (`C:\DEV\Fooocus\pnptool_server.py`): liegt außerhalb
  des Repos, kein Autostart. Muss manuell gestartet werden
  (`cd C:\DEV\Fooocus && .venv\Scripts\python.exe pnptool_server.py`), sonst
  schlägt der „lokal"-Provider im Popup fehl. Cloud-Provider funktioniert
  immer, auch ohne das.
- **Wiki-Import** (`WikiImportPopup.tsx`, Knopf „⇪✨" neben „+ Neue Seite" in
  der Wiki-Ansicht): nie im Browser angeklickt, nur `tsc -b` geprüft und ein
  Backend-only-E2E-Test (5 verschachtelte Entwürfe, Auto-Verknüpfung lief).
  Optik/Bedienung im Popup selbst ungetestet.
  - **PDF-Import ungetestet** — nur `.docx` real durchgespielt. PDFs liefern
    keine Formatvorlagen, die automatische Kapitel-Gliederung könnte deutlich
    schwächer ausfallen als bei Word-Dateien.
  - **60.000-Zeichen-Obergrenze** pro Dokument ist eine Schätzung, kein
    empirisch ermittelter Wert — bei Bedarf nachjustieren, falls größere
    Dokumente gebraucht werden oder die Grenze zu früh/spät greift.
- **SL-Beratungschat** (`BeratungPopup.tsx`, Knopf ⌬ Beratung in der
  Ideenschmiede): nie im Browser angeklickt, nur `tsc -b` + pytest +
  OpenAPI. Bitte ein Gespräch führen, prüfen dass ✨ KI unangetastet bleibt,
  und einmal „Entwurf anlegen“ — Kachel muss als Entwurf landen, nächster
  Chat darf sie nicht als Kanon kennen. Backend-Neustart nötig (Migration
  `007_ki_beratung.cypher`).
- **🔍-Prüfen-Knopf im RichTextEditor** (Personen/Orte/Events/Fraktionen/
  Gegenstände/Begleiter): nie im Browser angeklickt, nur `tsc -b` und
  Backend-Import geprüft. Siehe „Zuletzt gebaut" unten.
- **Auto-Verknüpfung: Sweep + Freitext-UI** (`app/ki/auto_verknuepfung.py` +
  neue Frontend-Popups, siehe „Zuletzt gebaut" unten): Backend per echtem
  E2E-Test gegen laufendes Backend + Neo4j verifiziert. Frontend (Sweep-
  Knopf in den Kampagnen-Einstellungen, ⧉✨-Knopf im `RichTextEditor`/
  Ideenschmiede) nie im Browser angeklickt, nur `tsc -b` und
  `vite build` geprüft.
- **Rüstungs-Reparatur-UI** (`RuestungReparatur.tsx` im Bearbeiten-Fenster
  einer Rüstung, `VerhandlungPopup.tsx` beim Spieler): nie im Browser
  angeklickt, nur `tsc -b` geprüft. Die Backend-Logik dahinter (Würfe,
  Materialverbrauch, Preisformel, Deckel, Annehmen/Ablehnen) wurde per
  echtem End-to-End-Skript gegen laufendes Backend + Neo4j durchgespielt
  und ist verifiziert — offen ist nur die Optik/Bedienung der beiden neuen
  Popups selbst (Layout, ob der Commlink-Stil passt, ob das Verhandlungs-
  Popup beim Spieler zuverlässig aufpoppt). Siehe „Zuletzt gebaut“ unten.
- **Häretiker-Flavor-Option** (Charaktererstellung, Charakterblatt,
  Kampfkarte, Probenrechner, Level-Up), siehe „Zuletzt gebaut“ unten und
  CLAUDE.md Punkt 14: Backend + Frontend komplett per echtem
  Backend-only-E2E-Test gegen laufendes Backend + Neo4j verifiziert
  (Häretiker-Weg-Karte, Katalog-Identität, Tooltip-Texte). Optik/Bedienung
  im Browser nie angeklickt, nur `tsc -b` geprüft — bitte einmal bei der
  Charaktererstellung „Häretiker“ statt „Magier“ wählen und prüfen, ob die
  Sphären-Namen (Chronos, Ehecatl, …) und „Glauben“/„Blasphemie“ überall
  im UI stimmig auftauchen (Charakterblatt, Kampfkarte, Probenrechner,
  Level-Up, Willenskraft-Rückfrage).

## Vor jedem Task: Wiki befragen

**`docs/wiki/index.md` zuerst lesen**, bevor Regeln oder Architektur-Entscheidungen neu ausgedacht werden — v.a. bei Regelfragen, weil sich NeotopiA laufend weiterentwickelt und das Excel oft nicht mehr der aktuelle Stand ist (siehe `docs/wiki/comparisons/regelwerk-excel-vs-aktuell.md`). Das Wiki hält bereits entschiedene Fragen, offene Baustellen und die Versionsgeschichte fest — Ziel ist, dieselbe Entscheidung nicht zweimal zu treffen (oder zu widersprechen). **Nach jeder inhaltlichen Änderung die passende Wiki-Seite nachziehen**, nicht nur CLAUDE.md.

## Was ist PnPTool

WebApp für Mark's Pen-and-Paper-Rollenspielrunden, Homebrew-System **"NeotopiA"** (WoD-artige Attribute, Shadowrun-Cyberware/Rigging, Mage-Sphären, Cyberpunk-Setting). Referenz: `docs/reference/Neotopia.xlsx`.

**Zwei Nutzerrollen:**
- **Spielleiter (GM)** — plant Kampagnen als Beziehungsgraph, sendet Live-Popups
- **Spieler** — interaktive Charakterbögen, Messenger, empfängt Popups

**Wichtige Dokumentation:**
- `docs/wiki/index.md` — **Projekt-Wiki**: Regeln inkl. Versionsgeschichte, Architektur, offene Fragen (siehe oben — zuerst hier nachschlagen)
- `docs/ui-konzept.md` — Leitbild fürs UI ("Commlink")
- `docs/theming.md` — Alle Farben als Tokens in `frontend/src/theme/`
- `docs/api/` — **Ausführliche API-Dokumentation** (Endpoints, Schemas, Logik)
- `~/.claude/plans/gut-pnp-steht-f-r-temporal-waterfall.md` — Architektur & Roadmap

## Tech-Stack (entschieden)

- **Backend**: FastAPI, neo4j async driver, JWT in httpOnly-Cookie, bcrypt direkt
- **Datenbank**: Neo4j 5 in Docker
- **Frontend**: React 19 + TypeScript + Vite, Cytoscape.js direkt (kein Wrapper)
- **Deployment**: Lokal Windows-Dev (`npm run dev`); produktiv auf bebop unter `pnptool.aurielmc.cloud` (seit 25.09.2026), Frontend-Image nginx + `vite build` (seit 03.10.2026)

## Projektstruktur

```
C:\DEV\PnPTool\
├── CLAUDE.md                 ← diese Datei
├── docs/
│   ├── api/                  ← API-Dokumentation (NEU 07.09.2026)
│   │   ├── README.md         — Übersicht, Konventionen
│   │   ├── mitteilungen.md   — Popups, WebSocket, Ausblenden
│   │   ├── kontakte.md       — Messenger, Stufen, Alias
│   │   ├── kampf.md          — Runden, Initiative
│   │   ├── ruestung.md       — Kästchen + Schadensreduktion (NEU 10.09.2026, Reduktion statt Durchlass 18.09.2026)
│   │   ├── rassen.md         — Baukasten, Balance, Freigabe (NEU 11.09.2026)
│   │   ├── party.md          — Gruppen, Mitgliedschaft, aktive Party (NEU 18.09.2026)
│   │   ├── spotify.md        — Playlist an Ort/Event, Musik folgt aktiver Party (NEU 19.09.2026)
│   │   ├── personen.md       — PCs/NPCs, Attribute, Cyberware
│   │   ├── wiki.md           — Seiten, Freigaben
│   │   ├── entitaeten.md     — Orte, Gegenstände, Fraktionen
│   │   ├── kampagnen.md      — Themes
│   │   └── auth.md           — Login, JWT
│   ├── ui-konzept.md
│   ├── theming.md
│   └── phase-5-messenger.md
├── backend/
│   ├── .venv/
│   ├── app/
│   │   ├── main.py
│   │   ├── auth/, campaigns/, entities/, graph/
│   │   ├── mitteilungen/     — Popups, WebSocket, Ausblenden
│   │   ├── kontakte/         — Messenger
│   │   ├── kampf/            — Rundenkampf
│   │   ├── wiki/             — Weltenbau
│   │   ├── party/            — Gruppen, Mitgliedschaft, aktive Party
│   │   ├── spotify/          — Musik: OAuth, Playlist-Suche, Wiedergabe
│   │   └── items/, traits/   — Gegenstände, Charakterwerte
│   └── scripts/create_gm.py
└── frontend/
    └── src/
        ├── theme/            — ALLE Farben hier, nirgends sonst!
        ├── mitteilungen/     — Popups, Blitz-Symbol
        ├── kontakte/         — Messenger (Persona-5-Stil)
        ├── kampf/            — Kampfmodus
        └── ...
```

## Wie man lokal startet

```powershell
# 1. Neo4j (läuft meist schon)
docker compose up -d neo4j

# 2. Backend (OHNE --reload, siehe Stolpersteine)
cd C:\DEV\PnPTool\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001

# 3. Frontend
cd C:\DEV\PnPTool\frontend
npm run dev
```

**Test-Login:** `sl` / `test-passwort-123`
**Testkampagne:** `71dc452c-6c45-4a18-aec5-24815d161053`

## Stand der Umsetzung (10.09.2026)

| Phase | Status | Beschreibung |
|-------|--------|--------------|
| 1 | ✅ | Grundgerüst, Docker, Auth |
| 2 | ✅ | CRUD, Cytoscape-Graph |
| 3 | ✅ | Charakterblatt (Attribute, Kästchen/Box-Tracks) |
| 4 | ✅ | Spieler-Zugang, Sichtbarkeit |
| 5 | ✅ | **Mitteilungen + Messenger fertig** |
| Wiki | ✅ | Seitenbaum, Freigaben, TipTap-Editor |
| Themes | ✅ | Zwei Themes, Token-basiert |
| Rüstung | ✅ | Kästchen + Schadensreduktion + Reparatur (Selbst/Händler), siehe `docs/api/ruestung.md` |
| Party | ✅ | Gruppen, Mitgliedschaft, aktive Party, siehe `docs/api/party.md` |
| Spotify | ✅ | Playlist an Ort/Event, Musik folgt aktiver Party, siehe `docs/api/spotify.md` |

**Zuletzt gebaut (11.10.2026 — KI-Charakter geht im Tutorial-Shop einkaufen, Mentor/Kontakte-Pipeline):**
- **Was:** Marks Wunsch: die KI-Charaktererstellung (Ideenschmiede ✨-Charakter
  + Massenidee, beide über `ki/routes.py::_idee_anlegen`) lässt das Freebee-
  Kapital nicht mehr ungenutzt liegen, sondern kauft sinnvoll aus dem
  bestehenden Tutorial-Shop-Sortiment (nie Neues erfinden, KI entscheidet
  selbst wieviel vom Budget sinnvoll ist — kein Zwang, alles auszugeben).
  Dazu die bisher fehlende Mentor/Kontakte-Pipeline (analog Kredithai):
  Mentor-Hintergrundpunkte erzeugen sofort einen vollen, KI-ausgearbeiteten
  NPC inkl. Einkauf (bestehenden `istMentor`-NPC wiederverwenden, sonst neu).
  Kontakte-Hintergrundpunkte legen dagegen nur N leere Platzhalter
  (`istBlankoKontakt`) in der Kontaktliste an — der Spieler tippt sie später
  im Spiel selbst an und beschreibt per Freitext, wen er braucht, statt alle
  Kontakte schon bei der Erstellung festzulegen (Marks Entscheidung). Beide
  Pipelines sind idempotent bei erneuter SL-Korrektur-Einreichung (legen nur
  Fehlendes nach, löschen nie).
- **Dateien:** `backend/app/haendler/ki_einkauf.py` (neu), `backend/app/
  hintergruende/{mentor.py (neu), spawn.py, repository.py}`, `backend/app/
  ki/routes.py` (Einkauf-Hook im charakter-Zweig), `backend/app/traits/
  routes.py` (Hook für Mentor/Kontakte-Rating nach Erstellung), `backend/app/
  kontakte/{routes.py, schemas.py, repository.py, security.py}` (neue Route
  `POST .../generieren`), `backend/app/entities/{schemas.py, repository.py}`
  (Felder `istMentor`, `istBlankoKontakt`), `frontend/src/kontakte/
  {KontakteAnsicht.tsx, api.ts, kontakte.css}` (Blanko-Kontakt-Kachel +
  Prompt-Popup).
- **Verifiziert:** neuer Test `test_ki_einkauf_mentor_kontakte.py` (Auswahl-
  Logik, No-Op-Pfade, Idempotenz — einzeln grün, in Kombination mit der
  Gesamtsuite gelegentlich die vorbestehende Neo4j/asyncio-Flakiness dieses
  Projekts unter Windows, siehe andere `test_*`-Dateien mit demselben
  `AttributeError`). Komplette Backend-Suite sonst unverändert grün,
  `test_zugriffsschutz.py` unverändert bei denselben 2 vorbestehenden
  Lücken (nicht von mir verursacht, vor dem Change per `git stash`
  gegengeprüft). `tsc -b` sauber. **Nie im Browser angeklickt, kein echter
  KI-Call getestet** — Mistral/Gemini brauchen eine laufende Kampagne mit
  API-Key.
- **Nicht dabei:** Rassen-Gratis-Erstkauf-Feature (`gratisErsterKaufTyp`)
  gilt beim KI-Einkauf nicht, nur beim echten Spieler-Kauf. Kein Digital-
  Bestellung-Pfad beim KI-Einkauf (Ware landet immer sofort im Inventar).

**Zuletzt gebaut (12.10.2026 — Mechanik-Hintergründe im SL-Baukasten sichtbar + abschaltbar):**
- **Was:** Mark schaute sich die Hintergründe-Verwaltung an und merkte an,
  dass Mentor/Kontakte/Schulden dort unsichtbar sind, weil sie Mechanik statt
  Katalogzeile sind — Wunsch: oben im Menü anzeigen, damit man weiß dass es
  sie gibt, mit Checkbox zum An-/Abschalten je Kampagne. Neue campaign-weite
  Einstellungen `mentorAktiv`/`kontakteAktiv`/`schuldenAktiv` (Default an,
  gleiches Muster wie `messengerAktiv` & Co.). `erstellung.py::regelwerk()`
  filtert deaktivierte Namen aus dem Hintergrund-Pool der Charaktererstellung
  und reicht `freebees.kreditErlaubt` durch (Schulden hängt am Kredit-Freebee,
  nicht am Pool); `erstellung.py::pruefe()` lehnt eine Einreichung serverseitig
  ab, die trotzdem Punkte auf einen deaktivierten Mechanik-Hintergrund legt
  oder den Kredit-Freebee bei abgeschalteten Schulden nutzt — Schutz gegen
  eine veraltete/manipulierte Anfrage, nicht nur Oberflächen-Kosmetik.
- **Dateien:** `backend/app/campaigns/repository.py` (3 neue
  `EINSTELLUNGEN_DEFAULTS`), `backend/app/hintergruende/seed.py` (neu:
  `SYSTEM_HINTERGRUENDE`-Metadaten), `backend/app/hintergruende/routes.py`
  (neu: `GET/PATCH .../hintergruende/system`), `backend/app/traits/
  {erstellung.py, routes.py}` (Einstellungen-Gates in `regelwerk()`/`pruefe()`),
  `frontend/src/hintergruende/{api.ts, HintergruendeVerwaltung.tsx,
  hintergruende.css (neu)}` (Checkbox-Block „Mechanik-Hintergründe“),
  `frontend/src/traits/{bogenApi.ts, Charaktererstellung.tsx}`
  (Kredit-Regler blendet sich aus, wenn `kreditErlaubt` falsch ist).
- **Verifiziert:** 7 neue Backend-Tests grün (Gates in `pruefe()`/`regelwerk()`,
  SYSTEM_HINTERGRUENDE-Konsistenz), komplette Suite sonst unverändert bei
  denselben 21 vorbestehenden Fehlschlägen (Achievements/Flora&Fauna/Shop/
  Zugriffsschutz, fehlende lokale Neo4j-Verbindung — nicht von mir
  verursacht). `tsc -b` sauber. **Nie im Browser angeklickt** — siehe „Offen“
  oben für die konkreten Klickschritte.

**Zuletzt gebaut (11.10.2026 — Tutorial-Shop-Auswahl zurück in die Kampagnen-Einstellungen):**
- **Was:** Mark meldete: Tutorial-Shop-Auswahl steckte als eigener
  Burgermenü-Punkt statt in den Kampagnenoptionen ("wie ausgemacht"), dort
  schien nichts auswählbar. Ursache 1 (echter Bug): Commit 5614883
  (10.10.2026) hat "Kampagnenmenü" als Burgermenü-Punkt missverstanden statt
  als Kampagnen-Einstellungen (⚙-Popup). Jetzt behoben: `TutorialShopVerwaltung`
  sitzt in `EinstellungenFenster.tsx`, Sektion „Tutorial-Shop“, kein eigener
  Bereich mehr. Ursache 2 (kein Bug): die Auswahlliste war leer, weil in
  Marks laufender Kampagne (`3f2b8734-...`) aktuell **kein einziger Ort**
  `istShop=true` hat — die Leer-Meldung "Noch kein Laden..." ist korrektes
  Verhalten, nicht die gemeldete Fehlfunktion. Erst einen Ort unter „Orte“
  zum Laden machen, dann erscheint er hier wählbar.
- **Dateien:** `App.tsx` (Bereich+Render+Import entfernt),
  `campaigns/EinstellungenFenster.tsx` (Sektion ergänzt),
  `haendler/OrtLadenFenster.tsx` + `TutorialShopVerwaltung.tsx` + `docs/api/haendler.md` (Hinweistexte korrigiert).
- **Verifiziert:** echter Browser-Klicktest gegen lokalen Dev-Server
  (Backend befristet gestartet, danach wieder beendet) + echte Neo4j-Daten —
  Burgermenü zeigt den Punkt nicht mehr, Einstellungen-Popup zeigt die neue
  Sektion korrekt inkl. Leer-Zustand. `tsc -b` sauber. Auswahl-Klick selbst
  (Zeile anklicken → Haken setzt sich) nicht gegen einen echten Laden
  getestet, um nicht in Marks laufender Kampagne einen Test-Ort anzulegen —
  Code ist unverändert zum bereits bestehenden `waehlen()`-Handler.

**Zuletzt gebaut (11.10.2026 — Shop-Sortiment: Ware-Auswahl mit Bild/Seltenheit/Steckbrief):**
- **Was:** Mark: das Vorlagen-Dropdown im Sortiment-Editor zeigte außer dem
  Namen nichts — keine Seltenheit, kein Steckbrief, Auswahl "fürs Sortiment"
  praktisch blind. Neues `VorlagenAuswahlPopup.tsx`: durchsuchbares Kachel-
  raster, wiederverwendet `.shop-ware`/`data-seltenheit` (derselbe
  Seltenheitsrahmen wie im Spieler-Shop) plus Typ-Symbol und
  `steckbriefKurz()` (dieselbe Kurzfassung wie auf der normalen
  Gegenstands-Kachel) direkt auf der Kachel. Ersetzt das `<select>` in
  `HaendlerBearbeiten.tsx` durch einen Knopf, der das Popup öffnet.
- **Dateien:** `haendler/VorlagenAuswahlPopup.tsx` (neu),
  `haendler/HaendlerBearbeiten.tsx`, `haendler/shop.css` (`.shop-ware-typ`/
  `.shop-ware-steckbrief`).
- **Verifiziert:** echter Browser-Klicktest live auf bebop (Tutorial-Shop,
  68 echte Vorlagen) — Suche filtert, alle Kacheln zeigen Typ+Steckbrief+
  Seltenheit korrekt (per DOM-Abfrage gegengeprüft, nicht nur Screenshot),
  Klick wählt aus und schließt das Popup, Preis-Feld + Hinzufügen-Knopf
  bleiben unverändert. Testauswahl am Ende bewusst NICHT abgeschickt, um
  Marks echtes Sortiment nicht zu verändern. `tsc -b` sauber.

**Zuletzt gebaut (11.10.2026 — Shop-Sortiment: Mehrfachauswahl statt Ein-Klick-Schließen):**
- **Was:** Mark direkt im Anschluss an die Ware-Auswahl: "ich klicke auf eine
  Sache und das Fenster geht wieder zu" — jeder Klick wählte genau EIN
  Gegenstand und schloss sofort, beim Sortiment-Aufbau mit vielen Gegenständen
  mühsam. `VorlagenAuswahlPopup` toggelt jetzt die Auswahl pro Klick (Neon-
  Outline + Haken-Marke, Popup bleibt offen, Auswahl übersteht auch
  Such-Wechsel dazwischen), ein optionaler gemeinsamer Preis gilt für den
  ganzen Schwung, "N Waren hinzufügen" schickt am Ende alles auf einmal ab.
- **Dateien:** `haendler/VorlagenAuswahlPopup.tsx` (Prop `onWaehlen` →
  `onHinzufuegen(ids[], preis?)`), `haendler/HaendlerBearbeiten.tsx`
  (`neueWareId`/`neuerPreis`-States raus, ein `vorlagenHinzufuegen`-Loop
  rein), `haendler/shop.css` (`[data-gewaehlt]`-Outline + Haken-Marke, bewusst
  `outline` statt `border`/`box-shadow`, damit es den Seltenheitsrahmen nicht
  überschreibt).
- **Verifiziert:** echter Browser-Klicktest live auf bebop gegen den
  Tutorial-Shop — zwei Gegenstände über zwei verschiedene Suchen hinweg
  ausgewählt (Auswahl blieb beim Suche-Wechsel erhalten), Knopf zählte
  korrekt auf "2 Waren hinzufügen" hoch, ein Abschicken hat beide wirklich
  ins Sortiment gelegt (API-Aufrufe real durchgelaufen) — danach bewusst
  wieder entfernt, um Marks echtes Sortiment nicht zu verändern. `tsc -b`
  sauber.

**Zuletzt gebaut (11.10.2026 — Tutorial-Shop-Sektion überlagerte sich im Einstellungen-Popup):**
- **Was:** Mark meldete nach dem obigen Fix: Tutorial-Shop-Sektion ist jetzt
  in den Einstellungen, aber überlagert sich mit der folgenden KI-Sektion
  (Screenshot zeigte Tabellenzeilen und KI-Dropdown übereinander). "Fix
  einprogrammiert" (keine echte Auswahl möglich) war dabei KEIN Bug — in der
  DB stand korrekt nur ein Ort als Laden, der bereits `istTutorialShop=true`
  hatte (Marks eigener Klick hatte funktioniert, nur gab's nichts zum
  Vergleichen).
- **Root Cause (echter Bug, per CDP live auf bebop verifiziert):** `.zf-seite`
  (gemeinsame Klasse mit `ZusatzfertigkeitenVerwaltung`/
  `HintergruendeVerwaltung`) setzt `min-height: 0` — nötig, wenn sie als
  GANZE Bereichsseite den vollen verfügbaren Platz ausfüllt und selbst
  schrumpfen/scrollen muss. Eingebettet zwischen vielen Settings-Abschnitten
  im `.fn-inhalt`-Flex-Stack sorgt genau dieses `min-height:0` dafür, dass
  der Flexbox-Shrink-Algorithmus die GANZE Sektion auf `offsetHeight: 0`
  zusammendrückt, sobald der Dialog nicht genug Platz hat — andere
  Geschwister (h4, Schalter) haben kein `min-height:0`, können also nicht
  schrumpfen, der ganze Druck landet auf `.zf-seite`. `overflow: visible`
  lässt den Inhalt (`scrollHeight` korrekt 171px) trotzdem sichtbar
  rendern — nur eben außerhalb seiner eigenen (kollabierten) Box, über dem
  nächsten Abschnitt liegend.
- **Fix:** `<TutorialShopVerwaltung>` in `EinstellungenFenster.tsx` in einen
  `<div style={{ flexShrink: 0 }}>`-Wrapper gepackt. Macht `.zf-seite` selbst
  zum Kind eines nicht-flexenden Divs, komplett raus aus der Shrink-Rechnung
  — ohne die geteilte `.zf-seite`-Klasse anzufassen (bleibt für ihren
  Vollbild-Einsatz unverändert).
- **Verifiziert:** Fix per `el.style.flexShrink='0'` LIVE im DOM auf
  `pnptool.aurielmc.cloud` getestet, bevor der Code geändert wurde
  (`offsetHeight` 0→171px). Danach Code gebaut, deployed, nochmal live
  gegen den echten Build bestätigt (`offsetHeight === scrollHeight === 171`,
  Screenshot sauber). Generelle Lektion: `min-height: 0` auf einer geteilten
  Komponenten-Klasse ist nicht automatisch sicher in jedem Einsatzkontext —
  bei neuer Einbettung in einen bestehenden Flex-Stack mit vielen
  Geschwistern immer `offsetHeight` der Sektion gegenprüfen, nicht nur
  `tsc -b`.

**Zuletzt gebaut (10.10.2026 — Rüstungs-Steckbrief: Reduktion + Kästchen):**
- **Was:** „Rüstungsbonus“ ist aus Steckbrief und Umbauen raus. Stattdessen
  zwei Zeilen: Reduktion und Kästchen.
- **Dateien:** CharacterSheetPanel, steckbrief.ts, GegenstandKachel.
- **Verifiziert:** `tsc -b`. **Im Browser eine Rüstung öffnen.**

**Zuletzt gebaut (10.10.2026 — Waffen-Schadensart default Tödlich):**
- **Was:** Waffen ohne gesetzte Art gelten als Tödlich. Schlag und Schwerheilbar
  setzt man extra. Dropdown ohne „offen“.
- **Dateien:** `waffenbonus.py`, `_create_data`, Repository-Lesen,
  CharacterSheetPanel, Steckbrief.
- **Verifiziert:** `test_waffenbonus.py`, `test_gegenstand_felder.py`. **Im
  Browser eine Pistole öffnen — Schadensart Tödlich.**

**Zuletzt gebaut (10.10.2026 — Waffenschaden einheitlich, Skala bis 12):**
- **Was:** Label „Schadensbonus“ ist überall „Schaden“. Steckbrief zeigt den
  Wert nur noch einmal. Maximum 12 (1–7 Handwaffe, 8–12 Schiffswaffe).
  KI-Schema-Feld heißt `schaden` (alter Schlüssel `schadensbonus` wird noch
  gelesen). Rüstungsbonus bleibt bei 7.
- **Dateien:** `items/waffenbonus.py`, CharacterSheetPanel, Begleiter,
  KI-Prompts, `docs/reference/Neotopia_Gegenstaende.md`.
- **Verifiziert:** `test_waffenbonus.py` + KI-Waffen-Tests. **Im Browser eine
  Waffe auf 12 stellen und den Steckbrief gegenlesen.**

**Zuletzt gebaut (10.10.2026 — KI-Waffen bekommen einen Schaden):**
- **Was:** Beratung/✨ und Shop-KI haben Waffen ohne `kraft`/`schaden` angelegt.
  Kachel und Kampfkarte zeigten dadurch 0. Schema verlangt jetzt `schaden`
  (1–12, Regelwerk, kein Würfelausdruck); beim Anlegen landen Wert, `schaden`
  und `istWaffe` auf der Waffe. Fehlende Angabe wird 1, nicht 0.
- **Dateien:** `items/waffenbonus.py`, `ki/routes.py`, `haendler/ki_vorschlag.py`,
  Import-Skript setzt `kraft=schaden`.
- **Verifiziert:** drei Tests in `test_ki_idee_typen.py`. Die sechs Live-Entwürfe
  sind direkt in Neo4j nachgezogen. **Im Browser die Kacheln gegenlesen.**

**Zuletzt gebaut (10.10.2026 — Schulden/Kredithai nach Kredit-Freebees):**
- **Was:** Kredit in der Erstellung erzeugt den Systemhintergrund Schulden.
  Bestehenden NPC mit `istKredithai` wiederverwenden, sonst Stub
  „Kredithai“ in der Ideenschmiede. Kanten `HAT_KREDITHAI`,
  `VERBINDUNG` typ Schuldet, `KENNT` mit zu. Rassen-Häkchen
  `kannKredithai`, NPC-Flag im Detail. KI-Füllung kommt mit der
  Kontakt-Pipeline — Erstellung wartet nicht auf LLM.
- **Dateien:** `backend/app/hintergruende/{kredithai,spawn,repository}.py`,
  `backend/app/traits/routes.py`, `frontend/src/rassen/RassenUebersicht.tsx`,
  `frontend/src/entities/NPCDetail.tsx`
- **Verifiziert:** `tests/test_kredithai.py`. Nicht im Browser geklickt.
- **Nicht dabei:** Mentor/Kontakte-Pipeline, Blatt-Button, Achievement-IDs.

**Zuletzt gebaut (10.10.2026 — Charakter-Bildergalerie):**
- **Was:** PC- und NPC-Detail zeigen dieselbe Galerie wie Orte und Fraktionen
  (mehrere Bilder, Primärbild = Anzeigebild auf der Kachel und im
  Spielerportrait). Ein weiteres Bild klaut das Anzeigebild nicht mehr.
  Spieler-Upload ersetzt nur das Primärbild, Extra-Bilder bleiben.
- **Dateien:** `frontend/src/entities/PCDetail.tsx`, `NPCDetail.tsx`,
  `BildGalerie.tsx`, `EntityManager.tsx`, `backend/app/entities/repository.py`,
  `backend/app/players/routes.py`, `backend/tests/test_charakter_galerie.py`
- **Verifiziert:** `tsc -b` und der Galerie-Test. Nicht im Browser geklickt.
- **Nicht dabei:** Gegenstände haben weiter nur ein Bild. Das eigene
  Portrait-Menü des Spielers zeigt weiter nur das Primärbild.

**Zuletzt gebaut (10.10.2026 — KI-Charakter folgt der Spieler-Erstellung):**
- **Was:** ✨-Charakter in der Ideenschmiede schreibt keine Roh-Ratings mehr.
  Dieselbe Prüfung wie ein Spieler: Rasse, Weg, Attribut-Zusatzpunkte nach
  Kontingent (höchstens 3, StartMax 4+Mod), genau ein Fertigkeitspaket,
  Hintergründe bis 5, Freebees inkl. Kredit/Eigenkapital innerhalb des
  Budgets — Geld und ein paar Details, nicht jedes Attribut auf 6.
  Regelwidrig einmal nachgebessert, sonst 422, kein Entwurf.
- **Dateien:** `backend/app/traits/erstellung.py`, `backend/app/ki/routes.py`,
  `backend/tests/test_ki_charakter_erstellung.py`, `backend/tests/test_ki_idee_typen.py`
- **Verifiziert:** die beiden Testdateien grün. Lokales uvicorn auf 8001
  lief noch ohne den Check (Start vor dem Commit, kein `--reload`) und
  wurde neu gestartet. Nicht im Browser geklickt.

**Zuletzt gebaut (10.10.2026 — Achievements: Backend + Frontend):**
- **Was:** Komplettes Feature aus dem Konzept (`docs/wiki/entities/
  achievements.md`) gebaut. 14 AUTO-Trigger (u. a. ERSTER_KILL, MOERDER,
  MEISTE_SCHADEN_GENOMMEN/VERTEILT, CHARAKTER_ERSTELLT, GEHEIMNISTRAEGER,
  parametrisierbares ERSTER_BESITZ_ZIEL/ERSTE_BESCHREIBUNG_ZIEL,
  ERSTER_CRITTER, ERSTE_DROHNE, ENDBOSS_BESIEGT, ERSTE_SITZUNG_UEBERLEBT),
  live aus dem Ereignisprotokoll berechnet, kein persistenter
  Vorschlags-Knoten. Mechanische Belohnung (EP oder Hintergrund, fest am
  Achievement hinterlegt) — einziger Weg, wie ein Hintergrund nach der
  Charaktererstellung noch steigt. `einzigartig`-Häkchen trennt
  campaign-weit einmalige Titel von pro-Person wiederholbaren, bei
  Rekord-Triggern wandert der Titel automatisch (alte Verleihung wird
  abgelöst, bleibt aber als Historie stehen). Spontane manuelle Vergabe
  mit optionalem ✨-KI-Text.
- **Dateien:** `backend/app/achievements/` (`schemas.py`, `repository.py`,
  `trigger.py`, `belohnung.py`, `routes.py`), Migration
  `012_achievements.cypher` (`Person.istEndboss`-Backfill),
  `entities/schemas.py`/`repository.py` (neues `istEndboss`-Feld).
  Frontend: `frontend/src/achievements/` — `AchievementVerwaltung.tsx`
  (SL: Katalog, Baukasten, Auto-Vorschläge, manuelle Vergabe),
  `MeineAchievements.tsx` (Spieler: Scroll-Popup, neuestes zuerst), beide
  über 🏆-Symbol in der Werkzeugleiste (`App.tsx`/`SpielerAnsicht.tsx`).
- **Verifiziert:** `backend/tests/test_achievements.py` (8 Tests, einzeln
  alle grün — derselbe vorbestehende Windows-Proactor-Loop-Flake wie bei
  `test_flora_fauna.py` trifft auch hier jeden zweiten Test im Verbund,
  Stolperstein 8/13), volle Backend-Suite sonst nur die vorbestehenden
  13 Fehlschläge, `tsc -b --force` sauber, Backend startet fehlerfrei gegen
  Neo4j (alle Routen im OpenAPI). **Nie im Browser angeklickt** — siehe
  „Offen" oben, Mark testet bewusst zuerst auf Andromeda.

**Zuletzt gebaut (10.10.2026 — Ideenschmiede: Entwürfe laden wieder):**
- **Was:** Live „Fehler beim Laden der Entwürfe“. Die Meldung kommt aus dem
  Catch-all in `IdeenschmiedeAnsicht`, nicht von `/entwuerfe` (die Route
  schluckt Fehler und liefert `[]`). Die Schmiede lädt parallel
  `GET /personen` — der knallte mit `ResponseValidationError` (28×
  `int_type`/`bool_type`, `input: None`) für `kapitalBasis`,
  `tutorialAusgegeben`, `gratisGegenstandErhalten`, `rassenFeatureGenutzt`.
- **Ursache:** Tutorial-Shop/Rassen-Features (10.10.) stehen in
  `PERSON_FIELDS` und `PersonResponse` als Pflicht-int/bool, fehlten aber in
  `_BOGEN_DEFAULTS`. Neo4j liefert für Altbestand `null`; Pydantic-Default
  greift nur, wenn der Key fehlt, nicht bei explizitem `None` (Stolperstein 9
  / 6-Schichten-Check, Schicht DEFAULTS).
- **Fix:** die vier Felder in `_BOGEN_DEFAULTS` (0 / False). Regression in
  `test_bogenfeld_defaults.py`, plus Netz dass jedes `int`/`bool` in
  `PersonResponse` aus `PERSON_FIELDS` einen Default hat (`ist*`-Konvention
  deckt `kapitalBasis`/`gratisGegenstandErhalten` nicht ab).
- **Verifiziert:** die fünf Defaults-Tests grün. Volle Suite: dieselben
  vorbestehenden Fehlschläge (asyncio/Neo4j-Stolperstein, Zugriffsschutz).
  **In der Schmiede gegenprüfen** — hart neu laden, Entwürfe müssen wieder
  erscheinen; NPCs/PCs ohne die neuen Properties ebenfalls.

**Zuletzt gebaut (09.10.2026 — Charaktererstellung speichert den Person-Schritt als Entwurf):**
- **Was:** Mark hat auf Andromeda Quills Konzept („der Held“) getippt, später
  am Handy denselben Assistenten weitergepflegt — der Text war weg. Ursache:
  der Person-Schritt (Name/Konzept/Alter/Ambition/Verlangen/Ziel) lebte nur
  im React-State. Autosave gab es für Wiki/Beschreibung, nicht für die
  Erstellung. Nginx-/Neo4j-Logs haben keinen Body, der Text war nicht
  rekonstruierbar.
- **Fix:** `useAutosave` schreibt dieselben Felder per bestehendem
  `PATCH .../personen/{id}/steckbrief` auf den Entwurfsknoten (1200ms +
  Flush beim Verlassen). Beim Öffnen hydratisiert der Assistent aus
  `GET .../bogen`. `SteckbriefUpdate` nimmt jetzt auch `name` und `alter`
  (`None` = unangetastet). Leerer Name wird nicht geschrieben. Der Rest
  des Assistenten (Weg/Rasse/Punkte) bleibt lokal bis „Charakter anlegen“.
  Keine Statusanzeige (still, wie Wiki-Autosave).
- **Verifiziert:** `pytest tests/test_steckbrief.py` 2/2, `tsc -b` sauber.
  Zugriffsschutz-Suite: dieselben vorbestehenden Fehlschläge, Steckbrief-
  Ausnahme unverändert. **Am Handy/PC gegenprüfen** — Person-Schritt
  tippen, Tab schließen oder Gerät wechseln, Assistent neu öffnen.

**Zuletzt gebaut (09.10.2026 — Android-Tastatur bleibt über dem Text):**
- **Was:** Mark: Tastatur klappt zu beim Markieren/Caret-Setzen/Autokorrektur,
  Text verschwindet unregelmäßig darunter. Der parallele Chat (Rahmen um
  langen Editor-Text, `097541f`) war ein anderes Thema und ist fertig.
- **Ursache:** PWA fullscreen ändert oft nur den Visual Viewport. Fenster
  blieben `94svh` hoch (unter der Tastatur), `body { overflow: hidden }`
  verhinderte das Nachschieben, und `.ProseMirror { overflow-y: auto }` plus
  `.fn-inhalt` war ein doppelter Scroll-Container — Android nimmt Caret-Tipp
  als Scroll und blendet die IME aus. Messenger hat bei jedem
  `visualViewport.scroll` `scrollIntoView` gemacht, das stiehlt den Fokus.
- **Fix:** `tastatur.ts` setzt `--vv-h`/`--vv-oben`/`--tastatur` und holt
  die Caret-Stelle nur ins Bild, wenn sie wirklich verdeckt ist (nicht bei
  laufender Markierung). Fenster folgt dem Visual Viewport. Viewport-Meta
  `interactive-widget=resizes-content`. Mobil kein intern scrollendes
  contenteditable (Desktop-Rahmen bleibt). Toolbar/Zoom `pointerdown`
  preventDefault. Messenger nutzt dieselben CSS-Vars.
- **Verifiziert:** `tsc --noEmit` sauber. **Am Handy gegenprüfen** — siehe
  „Offen“ oben.

**Zuletzt gebaut (10.10.2026 — Lebenspunkte-Grundwert pro Critter):**
- **Was:** Mark fiel auf, dass Critter (wie PCs/NPCs) standardmäßig 6
  Lebenspunkte haben — für eine Ratte oder einen Rattenschwarm viel zu
  viel, die sollen z.B. nur 2 haben (1 Grundwert + 1 durch
  Widerstandsfähigkeit). Nachträglich in den Optionen änderbar war der
  Wunsch, kein genereller Baukasten für alle Critter-Typen.
- **Neues Feld `Person.gesundheitGrundwert`** (analog `willenskraftBonus`):
  ersetzt für genau DIESE Person den bisher global fixen
  `GESUNDHEIT_GRUNDWERT = 6` (`traits/bogen.py`). Widerstandsfähigkeit zählt
  weiterhin unverändert obendrauf — nur der Sockel ist jetzt personenweise
  überschreibbar. Sentinel `-1` statt `None` als "kein Override": `update_
  node` filtert `None` beim PATCH generell als "Feld nicht anfassen" heraus
  (siehe Stolperstein beim Alias-Feld), ein Zurücksetzen auf den Standard
  wäre mit `None` als Default also unmöglich gewesen.
- **Frontend:** Zahleneingabe „Lebenspunkte-Grundwert“ im Critter-Fenster
  (`CritterFenster.tsx`, Abschnitt Verwaltung) — leer lassen = Standard (6),
  jede Zahl ≥0 überschreibt ihn. Kein eigener Katalog/Dropdown für
  Critter-Typen, bewusst ein einfaches Zahlenfeld.
- **Verifiziert:** `pytest tests/test_bogen.py` (5 neue Fälle: globaler
  Standard ohne Override, Sentinel -1 wie None behandelt, Rattenschwarm-
  Beispiel ergibt exakt 2, Grundwert 0 bleibt 0 und wird nicht ersetzt),
  volle Backend-Suite 539 passed (nur die 8 vorbestehenden, unabhängigen
  Fehlschläge — per `git stash`-Vergleich bestätigt identisch mit und ohne
  diese Änderung), `tsc -b` sauber. **Nie im Browser angeklickt** — siehe
  „Offen“ oben.
- Commit: `914b998`.

**Zuletzt gebaut (09.10.2026 — Vorgefertigte Charaktere als echtes Feld + PC↔NPC-Umwandlung):**
- **Was:** Mark wollte wissen, wie er einen Charakter als "vorgefertigt"
  markiert (bisher implizit: jeder abgeschlossene PC ohne Spieler), und kam
  dabei auf den Wunsch, nicht gewählte Vorgefertigte bei Bedarf zu einem
  NPC machen zu können (und umgekehrt) — ohne den Baustand zu verlieren.
  Teaser-Text für die Spieler-Auswahlkarte ist bewusst **kein** neues Feld:
  das bestehende `konzept` übernimmt diese Rolle, der Spieler passt es nach
  der Wahl selbst an (volle `description` geht ohnehin nie an die
  Auswahl-Route — Geheimnisse waren schon vorher sicher).
- **Neues Feld `Person.istVorgefertigt`** (analog `istHaendler`/`istKI`):
  SL setzt es per Checkbox im PC-Detail-Schnellzugriff. `GET
  /api/spieler/vorgefertigte` filtert jetzt zusätzlich darauf statt wie
  bisher automatisch jeden unclaimed PC zu zeigen. Migration
  `011_istvorgefertigt.cypher` markiert beim ersten Deploy alle
  Bestands-PCs, die die alte Regel erfüllt hätten, damit niemand aus der
  Auswahl verschwindet.
- **PC↔NPC-Umwandlung in-place** (`entities/repository.py::person_zu_npc`/
  `person_zu_pc`, neue Routen `POST .../personen/{id}/zu-npc`/`zu-pc`):
  PC und NPC sind derselbe `Person`-Knoten, `personType` kippt nur ein
  Filterfeld — Inventar, Charakterbogen, Beziehungen, Bilder bleiben
  unangetastet. PC→NPC setzt `istVorgefertigt=false` zurück und löst eine
  bestehende `SPIELT`-Kante (Spieler landet wieder im Ersteinstieg).
  NPC→PC verliert `istHaendler`/`istCritter`/`istKI`/`istPflanzenCritter`
  (ergeben an einem PC keinen Sinn; Mark: "ein NPC der mal Händler war
  seinen Händler Status verliert" — Sortiment bleibt dabei in der DB,
  nur das Flag kippt). Beide loggen `CharakterEntwicklung`
  (`ZU_NPC_GEMACHT`/`ZU_PC_GEMACHT`).
- **Frontend:** Checkbox + "⇄ Zu NPC machen" im PC-Detail-Schnellzugriff,
  "⇄ Zu PC machen" im NPC-Detail — je mit Commlink-`Bestaetigung`-Dialog
  (Marks Standardregel für destruktive/folgenreiche Aktionen).
- **Verifiziert:** echter E2E-Test gegen laufende Neo4j — Filter zeigt nur
  `istVorgefertigt=true`, PC→NPC setzt Flag zurück + Baustand bleibt
  (`konzept` als Stichprobe), NPC→PC in Gegenrichtung, ehemaliger Händler
  verliert `istHaendler`, falscher Ausgangstyp liefert `None` statt Crash;
  Migration separat getestet (Bestandsdaten werden markiert, idempotent,
  überschreibt keinen manuell gesetzten Wert erneut). Backend-Suite: die
  von dieser Änderung berührten 511 Tests grün (`tsc -b` sauber).
  **Hinweis:** beim Testlauf liefen parallel 6 unabhängige Fehlschläge aus
  einer zeitgleich laufenden zweiten Session (Umbau `zeigeInGraph` →
  `storyRelevant`, Migrationen 009/010 — nicht von dieser Änderung
  verursacht, per `git diff` auf die dortigen Dateien bestätigt). Eigene
  Migration von `009` auf `011_istvorgefertigt.cypher` umbenannt, weil
  `009`/`010` von der Parallel-Session zwischenzeitlich belegt wurden.
  **Nie im Browser angeklickt** — siehe „Offen“ oben.

**Zuletzt gebaut (04.–08.10.2026 — Urlaubs-Woche mit Chibi Neko auf bebop):**
- **Was:** 45 Commits auf `main`, HEAD `be2a6ff`. Gebaut und live geschaltet von Chibi Neko
  über Telegram, während Andromeda aus war. Windows-Klon hing bis 09.10. auf
  `19c78e9` und ist per Fast-Forward nachgezogen. Live-Frontend-Image vom
  08.10. 13:54 (letzter Commit), Backend-Image vom 07.10. 20:28 (letzter
  Backend-Commit war 18:00 — Kontakte/Ideenschmiede danach nur Frontend).
- **Inhalt (alles live, chronologisch):** Ort zum Laden + Shop-Regressionen;
  Zusatzfertigkeiten zwischen Fertigkeiten und Hexkraft/Sphäre/NeuroWeaving;
  Massen-KI als Hintergrund-Job, Anzahl-Feld-Clamp, Beratung-Prompt thematisch
  fokussiert; Begleiter-Label „KI“→„Æ“; Rucksack 🎒 im Burgermenü; Alias-Feld
  plus Anzeige „Alias aka echter Name“; Charaktererstellung überlagert
  Einfluss/Verwaltung nicht mehr; Flora & Fauna (Entität Gewächs, Kante
  `LEBT_IN`, eigener Burgermenü-Punkt mit Suche/Anlegen); Rassen-Baukasten
  Stale-Closure bei Modifikator-Klicks; Gegenstand-Anlegen mit Vorlage statt
  Platzhalter; Gegenstandstyp nachträglich nur SL; Popup schließt nicht mehr
  bei Textauswahl über den Rand; Gemini HTTP-503-Retry; Beratung
  Mistral-Fallback + Anbieter-Label; Kontakte: Messenger-Hinweis statt stillem
  Fehler + Suchfeld PC/NPC; Ideenschmiede-Geschichte-Entwurf speichert wirklich
  (Autosave). Rassen-Fairness (immer 24) steht extra im nächsten Block.
- **Doku:** Bis 09.10. war hier nur die Rassen-Fairness nachgetragen. Dieser
  Block schließt die Lücke. Keine offenen Feature-Branches, Working Tree sauber.

**Zuletzt gebaut (04.10.2026 — Rassen-Fairness: Nachteile geben jetzt einen Punkt zurück):**
- **Was:** Mark meldete einen vermuteten Logikfehler bei den Rassen ("ich
  glaube es wird nur der erste - Wert gerechnet, aber alle + Werte... Und
  das führt zu einem Ungleichgewicht"). Nachgerechnet: kein Rechenfehler
  (jeder Nachteil wurde schon immer korrekt summiert, 15/15 Tests grün),
  aber die Formel selbst war unfair — Nachteile brachten keine freien
  Punkte ein, also kamen Rassen mit Schwächen am Ende auf weniger
  Gesamtpunkte (24 − Σ Nachteile) als der Mensch (immer 24). Mark wollte
  stattdessen: "ein Minus Punkt gibt einen Punkt zurück, es soll also immer
  24 rauskommen". Neue Formel: Freie Punkte + Σ Vorteile − Σ Nachteile = 15
  (statt vorher ohne das Minus). Die fünf eingebauten Rassen wurden
  entsprechend neu balanciert: Ork 6/5/3→6/6/3, Elf/Zwerg 5/5/3→5/6/3, Troll
  5/4/3→5/6/3 — alle landen jetzt exakt bei 24. Die "Nachteile = aufgerundet
  halbe Vorteile"-Mindestregel bleibt (verhindert weiterhin ein reines
  Vorteils-Volk ohne erzählerische Schwäche, ist aber kein Budget-Mechanismus
  mehr, das erledigt die neue Formel von selbst).
- **Dateien:** `rassen/balance.py` (Formel + Docstring), `traits/erstellung.py`
  (RASSEN-Werte), `tests/test_rassen_balance.py`, `rassen/RassenUebersicht.tsx`
  (Hinweistext), `docs/api/rassen.md`, `docs/regeln-neotopia.md`.
- **Verifiziert:** `pytest tests/test_rassen_balance.py tests/test_rassen_grenzen.py`
  + volle Suite + `tsc -b`/`vite build`. Im Browser: Rassen-Baukasten zeigt
  alle fünf Rassen als "✓ ausgewogen" mit der neuen Bilanz; eine testweise
  angelegte Troll-Erstellung kommt in Summe auf 24 Attributpunkte.

**Zuletzt gebaut (10.10.2026 — Shops nur noch über den Ort):**
- **Was:** Mark: Shops nicht über NPCs anlegen. Laden, Ware, Spezialisierung,
  Vertriebsart und Tutorial-Flag hängen am Ort (`OrtLadenFenster`: Zum Laden
  machen, Haken Tutorial-Shop, Sortiment). Verkäufer-NPC ist optional und nur
  für Verhandeln/Kontakte. Kein Auto-Ort mehr aus `istHaendler`. NPC-Detail
  hat keinen „Zum Händler machen“-Knopf mehr.
- **Dateien:** `haendler/repository.py`, `haendler/OrtLadenFenster.tsx`,
  `NPCDetail.tsx`, `HaendlerBearbeiten.tsx` (Standort-Dropdown weg),
  `HaendlerEinstellungenFenster.tsx` gelöscht, `ki/routes.py`
  (`shop_id_von_gesicht`).
- **Verifiziert:** pytest shop/tutorial/massenidee + `tsc -b`.


**Ältere Einträge (vor 04.10.2026):** vollständiges Build-Log in
`docs/ENTWICKLUNGSHISTORIE.md`, Abschnitt „Build-Log-Archiv“ — chronologisch,
nichts gekürzt. Viele Themen stehen zusätzlich aktuell gehalten im Wiki (immer
zuerst `docs/wiki/index.md` prüfen, siehe oben).

## Wichtige Design-Entscheidungen

*(Details in `docs/api/` — hier nur die Kurzfassung)*

### Mitteilungen (`docs/api/mitteilungen.md`)
- **Kein Absender** — Ansagen kommen "aus der Spielwelt"
- **4 Arten:** TEXT, BILD, WARNUNG (Bildschirm pulsiert), NACHRICHT (Chat)
- **Ausblenden statt Löschen** — jeder räumt seine eigene Liste auf
- **WebSocket** mit Reconnect (Android schläfert Tabs ein)

### Kontakte/Messenger (`docs/api/kontakte.md`)
- **`chatOffen` getrennt von `stufe`** — Nummer haben ≠ kennen
- **Spieler sehen NPCs nur unter Alias** (kein echter Name)
- **Persona-5-Stil** — schräge Sprechblasen, Neon-Farben

### Kampf (`docs/api/kampf.md`)
- **Initiative vom Spieler eingeben** — physische Würfel
- **Reflex-Booster** — Zusatzaktion, Ampel, Paralyse
- **NPC-Namen verborgen** — Spieler sehen "Unbekannter Ork"
- **Waffen tragen eine Schadensart** — `schadenArt`: `schlag` / `schwer` /
  `aggraviert`, am Tisch Schlag / Tödlich / Schwerheilbar. Leer = noch nicht
  gesetzt, nichts wird geraten. Im Umbau wählbar, auf der Kachel sobald
  gesetzt.

### Rüstung (`docs/api/ruestung.md`)
- **Kästchen + Schadensreduktion statt flachem Bonus** — Rüstung nutzt sich ab
- **Reduktion: höher ist besser** (18.09.2026 gedreht — vorher "Durchlass",
  niedriger=besser, von Mark nach dem Praxistest als unintuitiv verworfen:
  *"Durchlass ist ein dummer Wert"*). Wie viel Schaden pro Treffer abgefangen
  wird; sinkt gestuft mit dem Kästchen-Anteil (>50% voll, >25% halb, sonst
  ein Viertel) statt einen eigenen "Aktuell"-Wert zu brauchen
- **Abstufen statt Blocken** — Schwerheilbar→Tödlich→Schlag, nur Schlag wird
  halbiert (unterste Stufe)
- **Kein separater Aktuell-Wert für die Reduktion mehr** — die effektive
  Reduktion wird aus dem Kästchen-Verhältnis berechnet. Das war zugleich der
  Fix für einen Bug (18.09.2026): der alte Durchlass-Aktuell-Wert zog beim
  nachträglichen Aktivieren über PATCH nicht mit, wodurch frische Rüstung
  fälschlich als zerschossen galt
- **Alles Getragene ist EIN Pool** — Kästchen summiert, Reduktion vom Teil
  mit der besten Basis. **Keine Körperzonen**, kein Zielen (zu kompliziert)
- **Beste Reduktion wird zuerst aufgebraucht**, Überlauf ins nächste. Killt
  nebenbei den "kugelsicheres Suspensorium"-Trick von selbst
- **Zerstörte Rüstung (0 Kästchen) fliegt aus der Ausrüstung** — landet im
  Mitgeführten (reparierbar, wie ausgebautes Chrom), Wiederanlegen gibt 409
- **Treffer hängt an der Person, nicht am Gegenstand** — welche Teile dran
  sind, ist Regelfrage, nicht Angabe des Aufrufers
- **Reparatur noch ohne Probe/Preis** — SL trägt das Ergebnis von Hand ein,
  bis Hardware-Skill-Check und Shop-System stehen

### Rassen (`docs/api/rassen.md`)
- **Katalog global, Freigabe je Kampagne** — der SL hakt an, was in dieser
  Runde wählbar ist; neu gebaute Rassen sind bewusst noch nicht freigegeben
- **Balance-Regel aus den Daten gefunden, nicht erfunden:** freie Punkte +
  positive Modifikatoren = 15, Nachteile = halbe Vorteile (aufgerundet).
  Alle fünf gewachsenen Rassen erfüllen sie exakt
- **Baukasten warnt, blockiert nicht** — ein übermächtiges NPC-Volk bleibt
  möglich
- **Nur Attribute** — Fertigkeitsboni o.ä. gäbe es nicht mehr nachrechenbar
- **Erstellungsgrenze ≠ Lebensmaximum:** `startmaxima` = 4+Mod (nur bei der
  Erstellung), `lebensmaxima` = 6+Mod (dauerhaft, als `maxOverride` am Blatt)
- **Rassen-Kennung ist eine UUID ohne Namen** — Lehre aus Stolperstein 6,
  damit Umbenennen im Baukasten nichts zerreisst

### Cyberware
- **`verbaut` statt `ausgeruestet`** — Chrom sitzt im Körper
- **Chirurgisch entfernen** — kein "Ablegen"-Button
- **Kein generisches Bonus-Feld** — Initiative-Bonus nur für Reflex-Booster

### Allgemein
- **Bestätigungsdialog** für destruktive Aktionen
- **Papierkorb** statt echtem Löschen (SL-sichtbar)
- **Keine harten Farbwerte** außerhalb `frontend/src/theme/`

## Bekannte Stolpersteine

1. **`uvicorn --reload` auf Windows** — Zombie-Prozesse. Beide PIDs killen, ohne `--reload` starten.
2. **Cytoscape + `text-align: center`** — Canvas verschoben. Fix: `textAlign: "left"` auf Container.
3. **Neue Pydantic-Felder + Bestandsdaten** — `coalesce`-Fallback in `_decode()` nicht vergessen!
4. **WebSocket nicht an `require_campaign_zugang`** — wirft HTTPException, Client sieht nur Abbruch.
5. **6-Schichten-Check bei neuen Feldern:** DB-Property → Repository FIELDS+DEFAULTS → Create-Schema → Update-Schema → Response-Schema → Frontend-Interface
6. **TraitDef-Umbenennen braucht eine Migration!** Die Kennung ist
   `ruleset:category:name` (`traits/seed.py`). Wer einen Wert umbenennt,
   ändert damit die Kennung — `MERGE` legt dann einen **neuen, leeren**
   Knoten an, während der alte samt aller Charakterwerte (`HAS_TRAIT`, dort
   sitzt das `rating`) stehen bleibt. Genau so entstand der Arete/Hexkraft-
   Doppelgänger (10.09.2026): Blatt zeigte die alten Punkte, Kampfkarte den
   neuen leeren Wert, und weil die alte Kategorie keine Magie-Kategorie mehr
   war, sah plötzlich jeder Charakter die Zeile. Vorlage für den Fix:
   `seed.py::_migriere_arete_zu_hexkraft` (Werte umhängen, alten Knoten erst
   löschen wenn nichts mehr dranhängt).
7. **Neo4j NIE mit `docker run` starten — sonst Datenverlust!** Das
   neo4j:5-Image deklariert `VOLUME /data`; ein `docker run` ohne explizites
   `-v` erzeugt jedes Mal ein **anonymes Volume** → DB startet leer → wirkt
   wie „Kampagne gelöscht". Die alten Daten liegen dann in verwaisten
   anonymen Volumes. Immer `docker compose up -d neo4j` nutzen (benanntes
   Volume `pnptool_neo4j_data`). Am 15.09.2026 behoben: aktuelle Daten aus
   dem anonymen Volume ins benannte Volume kopiert, Container über compose
   neu erstellt. Diagnose-Hinweis: `docker volume ls` zeigt anonyme
   Hash-Volumes als Verräter; ein Re-Start eines alten Containers
   (`docker start pnptool-neo4j-1`) endet mit Exit 3 (Server startet+stoppt
   sofort) — stattdessen `docker rm` + `docker compose up -d neo4j`.
8. **`tests/test_shop_am_ort.py` instabil im Verbund, isoliert stabil**
   (gefunden 10.10.2026, vorbestehend, siehe `docs/ENTWICKLUNGSHISTORIE.md`
   Stolperstein 13 für die volle Herleitung) — `asyncio.run()` pro Test +
   Modul-Singleton-Treiber. Ein Fehlschlag im vollen Lauf dieser Datei ist
   kein neuer Bug, Test isoliert laufen lassen.

## Git-Workflow

- Remote: `https://github.com/Auriel-McCloud/PnPTool.git`
- Branch: `main` (direkt committen)
- Commit-Messages: Deutsch, eine Zeile, fachliches Ergebnis
- Session-Start: `git log --oneline -5`, `git status`
- Session-Ende: committen + pushen (Mark arbeitet von PC und Handy)

## Server-Status

- **Neo4j:** Docker Compose, Container `pnptool-neo4j-1`, Port 7687 — benanntes Volume `pnptool_neo4j_data` (nie `docker run`, siehe Stolperstein 7)
- **Backend:** `127.0.0.1:8001` (Port 8001 wegen Zombie-Prozessen)
- **Frontend:** `localhost:5173`, Vite-Proxy → 8001


## Geplante Features — Status & Doku-Verweise

Ausführliche Herleitung/Historie jedes Punkts: `docs/ENTWICKLUNGSHISTORIE.md`,
Abschnitt „Geplante-Features-Archiv“ (nichts gekürzt, nur hierher verschoben).
Wo es bereits eine Wiki-Seite gibt, ist die die aktuellere Quelle (Stand wird
dort weitergepflegt, hier nicht mehr).

| # | Feature | Status | Doku |
|---|---|---|---|
| 1 | Shop-System + Händler-Spam | Kern+Sortiment+Verhandeln ✅ gebaut; Spam/Scammer/I.C.E.-Skalierung **offen** | `docs/api/haendler.md`, [[waehrung-und-preise]] |
| 2 | Augment-Differenzierung (Hexware/Bioware/Cyberware exklusiv) | ✅ fertig | [[cyberware-bioware]] |
| 3 | KI-Integration (NPC-Gen, Bild, Wiki-Import, Auto-Verknüpfung, Prüfung, Beratung, alle Welttypen) | ✅ größtenteils gebaut; Chatbots an Gegenständen **nicht umgesetzt**; Jev **geparkt** | [[ki-integration]], `docs/api/ki.md` |
| 4 | Spotify | ✅ fertig | [[spotify-anbindung]] |
| 5 | Deploy (Debian/nginx) | ✅ erledigt (bebop) | `docs/api/tech-stack` s.u. |
| 6 | Drei-Ebenen-Architektur (Regelsystem→Kampagne→Ideenschmiede) | ✅ fertig | [[architektur-drei-ebenen]] |
| 7 | Rüstungssystem inkl. Reparatur | ✅ fertig | `docs/api/ruestung.md`, [[ruestung-kaestchen-durchlass]] |
| 8 | KI+Critter als echte NPCs, Einfluss-System, Matrix-Attribut | ✅ Backend+Frontend fertig; KI-Auto-Steigerung **offen** (braucht Party-Besuchs-Log) | nur Archiv (noch keine eigene Wiki-Seite) |
| 9 | Decker/Neuroweaver 6-Skill-System | ✅ fertig | [[neuroweaving-decking]] |
| 10 | KI-Chatbots für Gegenstände (Decker-Deck, TTS) | reine Idee, **nicht begonnen** | nur Archiv |
| 11 | Charakterportrait im Spieler-Menü | ✅ MVP (Upload/Kamera/KI); Zeichentool **offen** | [[ki-integration]] (Bildgenerierung) |
| 12 | Steckbrief nachträglich bearbeiten | ✅ erledigt | — |
| 13 | Handy-Ansicht Story-Wiki + Ideenschmiede | ✅ gebaut | [[ingame-wiki-feature]], [[ui-konzept-commlink]] |
| 14 | Häretiker-Flavor (Magier-Reskin) | ✅ fertig | [[magie-hexkraft]] |
| 15 | Critter-Tamagotchi/Desktop-Pet | reine Idee, **explizit zuletzt** (Marks Vorgabe) | nur Archiv |
| 16 | Inventar-Transfer + neue Gegenstandstypen | Party-Weitergabe ✅; Rest (gleicher Ort, Geld, Credstick, Heiltrank, Granate) **offen**, Datenmodell nicht entschieden | [[gegenstand-transfer]] |
| 17 | Ereignisprotokoll / Sitzungs-Log | Backend+Hooks+SL-Zeitleiste ✅; Korrektur/Papierkorb-UI + NPC-Wissen + ein paar KI-Nebenpfade **offen** | [[ereignisprotokoll]], `docs/api/ereignisprotokoll.md` |

