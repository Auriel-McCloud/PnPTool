# UI-Konzept: das Commlink

Festgehalten am 28.08.2026 im Gespräch mit Mark. Grundlage für den UI-Umbau, der den bisherigen Listen-Charakter ablöst. Auslöser war sein Urteil zur fertigen SL-Vorschau: *"technisch tut es was es soll, optisch noch weit weg — keine Popups, viel zu viel Listen-Charakter."*

## Leitbild

Die Oberfläche soll sich anfühlen wie ein **Commlink** — ein Zukunfts-Handy aus der Spielwelt — und nicht wie ein Verwaltungswerkzeug. Cyberpunk, künstlerisch, immersiv. Marks Formulierung: Navigation *"weniger wie zwischen Webseiten springen, mehr wie durch einen Apple-Fatclient"*, also flüssige Übergänge statt Seitenwechsel-Gefühl.

**Zielgerät ist das Tablet.** Touch-Bedienung ist der Normalfall, nicht die Ausnahme — Trefferflächen, Abstände und Gesten entsprechend auslegen. Handy und PC müssen mitgehen, geben aber nicht den Takt vor.

## Aufbau

- **Links: Bereichswechsel.** Charakterblatt, Gegenstände, Kontakte, Graph, Notizen, Kampfmodus, Regeln — Liste noch nicht abschließend.
- **Oben: Werkzeugleiste.** Symbole für SL-Popups, den Tooltip-Schalter (siehe unten) und weitere Funktionen, die noch zu definieren sind.
- **Fenster** statt Inline-Akkordeons: ein Gegenstand öffnet sich als eigenes, fokussiertes Fenster. Auf allen Geräten echte Fenster; am Handy bildschirmfüllend mit Griff oben mittig. **Position wechselt bewusst** — mal weiter oben, unten, rechts oder links statt immer starr zentriert.
- **Störeffekte**: gelegentliches Flackern wie bei einer Neonröhre oder einem gestörten Fernseher, etwa alle 5 bis zufällig 10 Minuten. Bewusst selten, als Würze.
- **Neonröhren als Feldbegrenzung**: leuchtende Ränder um Eingabeflächen. Bewusst in CSS statt als animierte Bilddateien — passt sich jeder Feldgröße an, bleibt auf hochauflösenden Displays scharf und ist umfärbbar (Magenta trägt die Bedeutung "SL-geheim"). Nur auf aktiven Flächen, nicht auf jedem Listeneintrag, sonst flimmert die Seite.

## Leitprinzip: kein Scrollen

Marks Vorgabe: *"der Plan ist, dass man niemals scrollen muss, maximal in Pop-ups, aber die Übersichtsseiten sollten immer statisch sein."*

Das ist die weitreichendste Entscheidung des ganzen Konzepts und erklärt auch das Urteil "zu viel Listen-Charakter": Eine scrollende Liste ist das Gegenteil eines Geräte-Displays. Konsequenzen, die daran hängen:

- Übersichten brauchen eine **feste Höhe** und müssen sich einteilen — Raster mit fester Kachelzahl, Blättern statt Scrollen, oder Suche/Filter als primärer Zugang statt einer langen Liste.
- Bei den derzeitigen Testdaten (2 Personen, 7 Gegenstände) passt alles auf einen Bildschirm; das täuscht. Bei 40 NPCs oder 60 Gegenständen trägt das nicht mehr.
- **Mark hat die Schwachstelle selbst benannt**: *"höchstens bei den Gegenständen müssen wir uns was überlegen."* Genau dort ist zuerst zu entscheiden — vermutlich in Verbindung mit der schon notierten Vision zu Suche und Kategorisierung (siehe CLAUDE.md, Abschnitt "Vision — Party/Gruppen, Suche & Kategorisierung").
- Scrollen bleibt erlaubt in Popups/Fenstern. Das macht das Fenstersystem umso wichtiger: lange Inhalte gehören dorthin, nicht auf die Übersichtsseite.

## Zwei Rollen, eine Hülle

Mark beschrieb überwiegend das **Spieler-Interface**, das es noch gar nicht gibt — ohne den Spieler-Login aus Phase 4 kann es niemand öffnen. Was ihn heute stört, ist das **SL-Werkzeug**, das er täglich benutzt und das *"noch mehr Felder braucht"*.

**Entschieden:** Navigation, Fenstersystem und Ästhetik werden als **eine gemeinsame Hülle** gebaut, die beide Rollen füllen. Der SL bekommt mehr Bereiche und Felder, der Spieler die schlanke Commlink-Ansicht. Einmal bauen, zweimal nutzen — und die Spielwelt fühlt sich für beide gleich an.

**Reihenfolge:** die Hülle entsteht zuerst um das SL-Werkzeug herum, weil Mark das sofort benutzen und beurteilen kann. Wenn Phase 4 kommt, bekommt der Spieler dieselbe Hülle mit weniger Bereichen.

## Bereichsschnitt

**Spielercharaktere und NPCs getrennt** (nicht ein gemeinsamer Bereich "Personen" mit Filter). Begründung: sobald viele NPCs existieren, gehen die wenigen PCs sonst darin unter.

## Kampfmodus

Eine Mischung aus dreierlei — nicht nur Initiative-Verwaltung:
- **Initiative und Reihenfolge**: wer ist wann dran, Runden zählen, aktueller Zug hervorgehoben.
- **Verdichtete Kampfwerte**: Leben, Waffen, Attacken und genau die Fähigkeiten, die im Kampf gebraucht werden — auf einen Blick statt über den ganzen Charakterbogen verteilt.
- Setzt teilweise auf noch fehlende Phase-3-Teile auf (Box-Tracks für Gesundheit/Willenskraft, Waffenwerte am Charakter).

## Tooltips (Querschnitts-Feature)

Neben **jedem Fachbegriff** soll sich eine Erklärung einblenden lassen, was der Begriff bedeutet bzw. bewirkt — ebenfalls als Popup. Weil das sonst überall zugleich auftaucht, gehört ein **Schieberegler in die obere Leiste**, der die Tooltip-Funktion als Ganzes an- und abschaltet.

Das ist kein Kampfmodus-Feature, sondern zieht sich durch die gesamte Oberfläche: Attribute, Fertigkeiten, Gegenstandstypen, Regelbegriffe. Braucht also einen zentralen Mechanismus (Begriff → Erklärung) statt verstreuter Einzeltexte, und eine Quelle für die Texte — vermutlich am `TraitDef`-Katalog bzw. am kommenden Regeln-Bereich.

## Stand der Umsetzung

**Gebaut (28.08.2026) — Schritt 1: die Hülle.**
- `frontend/src/index.css` ist jetzt das Commlink-Fundament: dunkle Flächen, CSS-Variablen für Farben/Maße, dunkle Formularelemente, Touch-Mindestgröße 44px. Ersetzt das Vite-Startertheme.
- `frontend/src/shell/CommlinkShell.tsx` + `commlink.css`: Bereichsmenü links, Werkzeugleiste oben, Aufblenden beim Bereichswechsel, Neonflackern. Bewusst **inhaltsfrei** — sie weiß nichts über Kampagnen oder Personen und kann deshalb später unverändert die Spieler-Ansicht tragen.
- Die bestehenden Ansichten wurden auf die Variablen umgestellt; hartkodierte Hellwerte sind raus.

**Navigation (nach Marks Rückmeldung überarbeitet).** Erst lag die Schwelle bei 900px, wodurch das Tablet im Hochformat dieselbe Burger-Schublade bekam wie das Handy — für ein Gerät, an dem man ständig zwischen Bereichen wechselt, falsch. Jetzt:
- **Ab 600px** eine schmale Symbolspalte (60px), die dauerhaft stehen bleibt. **Angetippt fährt nur der eine betroffene Eintrag heraus** und zeigt seinen Namen — nicht das ganze Menü. Erst das zweite Antippen wechselt den Bereich. Grund (Marks Rückmeldung): in der Spalte sieht man nur Zeichen, man weiß also gar nicht, was man anklickt; das ganze Menü auszufahren verdeckte zudem den Inhalt und beantwortete die Frage trotzdem nicht.
- Der vorgefahrene Eintrag ist **in der Leitfarbe seines Bereichs umrandet** und glüht darin — **dieselbe Farbe, die anschließend nach oben fliegt**. Umgesetzt über eine CSS-Variable `--ton` am Eintrag; die Bereichsfarbe steht in `App.tsx` an jedem Eintrag.
- *Zwei Fallstricke dabei, beide behoben:* (a) die globale `button:hover`-Regel aus `index.css` färbte alle vier Ränder cyan und überstimmte den Ton — die Menüregel setzte nur den linken Rand. (b) Damit ein Eintrag über die schmale Spalte hinausragen kann, braucht sie `overflow: visible`; dadurch standen aber auch die unsichtbaren Beschriftungen und die "bald"-Marken über dem Inhalt. Jetzt beschneiden sich die Zeilen einzeln, und nur der vorgefahrene Eintrag darf herausragen.
- **Unter 600px** (Handy) bleibt es bei der Schublade hinter dem ☰; dort war es laut Mark passend.

**Der Bereichswechsel ist inszeniert**, wie von Mark beschrieben: der angetippte Name löst sich aus dem Menü, fliegt nach oben und wird zur Überschrift, während ein Leuchtbalken herabfährt, die alte Seite auslöscht und die neue freilegt. Umgesetzt als fliegender Klon (Start- und Zielkoordinaten werden vor dem Umschalten gemessen) plus Balken-Animation; der Inhalt wechselt auf halbem Weg, verdeckt vom Balken. Zeiten stehen als Konstanten in `CommlinkShell.tsx` und müssen zu denen in `commlink.css` passen.

*Fallstrick dabei, bereits behoben:* eine CSS-Animation ohne `animation-fill-mode: forwards` springt am Ende in den Ausgangszustand zurück — der Balken blieb dadurch quer über dem Inhalt liegen. Jetzt zusätzlich per Zeitgeber aus dem Baum entfernt.

**Farbwelt: Neon auf Schwarz.** Grund `#08080d`, Cyan `#00e5ff` als Aktiv-/Fokusfarbe, Magenta `#ff2d95` als Signal. Bewusste Regel: **die Neonfarben tragen Bedeutung statt Dekoration** — Magenta heißt durchgehend "SL-geheim", Cyan "aktiv/Fokus". Flächiges Neon ermüdet bei langen Sitzungen am Tablet, deshalb sind die Flächen selbst gedeckt und nur Ränder, Text und Zustände leuchten.

**Bewegung respektiert `prefers-reduced-motion`** — inklusive Flackern. Für lichtempfindliche Menschen ist Geflacker keine Stimmung, sondern ein Problem.

**Achtung Cytoscape:** der Graph zeichnet auf Canvas und kennt keine CSS-Variablen. `CampaignGraphView.tsx` spiegelt die Farbwerte deshalb von Hand (`KIND_COLOR`, `FARBE_*`) — bei Themeänderungen dort mitziehen.

**Noch nicht gebaut — Schritt 2 und später:**
- Der feinere Bereichsschnitt. `EntityManager` hält Personen, Orte, Events und Verbindungen weiterhin in einer Ansicht namens "Welt"; PCs/NPCs/Orte/Events getrennt erfordert, diese Komponente zu zerlegen.
- Das **Fenstersystem** (Gegenstand als fokussiertes Fenster statt Inline-Akkordeon) — das ist der eigentliche Kern gegen den Listen-Charakter und der größte verbleibende Brocken. Damit erledigt sich auch der vertagte Breite-Bug.
- Kampfmodus, Regeln, Notizen sind im Menü als "bald" sichtbar, aber leer.
- **Tooltip-System: gebaut** (30.08.2026). Schieberegler links in der oberen Leiste, Zeichen neben jedem Wert des Charakterblatts, Erklärungen liegen als `Erklaerung`-Knoten je Regelwerk. Die Spielleitung schreibt sie direkt im Fenster. Noch offen: dieselben Zeichen bei Gegenstandstypen und im kommenden Regeln-Bereich, und die Texte selbst (kommen aus dem überarbeiteten Fremdmaterial).
- SL-Popups: das Symbol ist oben angelegt, aber deaktiviert.

## Offen

- **Typografie**: aktuell System-Schriften mit Versalien und weiter Laufweite für Navigation und Überschriften, Monospace für die Marke. Bewusst keine Webfonts (Ladezeit, Offline, keine Fremdanfragen) — falls doch eine markantere Schrift gewünscht ist, wäre sie lokal einzubinden.
- Welche Symbole genau in die obere Leiste gehören (über SL-Popups und Tooltip-Schalter hinaus).
- Ob "Notizen" spielereigene Notizen meint oder die bestehenden SL-Notizfelder.
- "Kontakte" ist vermutlich die Spielersicht auf Personen — Verhältnis zu den SL-Bereichen PCs/NPCs noch zu klären.
- Ob die Störeffekte abschaltbar sein sollen (Empfehlung: ja, mindestens für längere Sitzungen).
- Der **Regeln-Bereich** ist weiterhin ein komplett neuer Inhaltstyp (siehe Plandatei): vermutlich eine Rich-Text-Seite pro Kampagne, campaign-weit statt an eine Entität gebunden.

## Fenstersystem und "nie scrollen" (gebaut 29.08.2026)

**Fenster** (`frontend/src/shell/Fenster.tsx` + `fenster.css`): eigenständig und inhaltsfrei, damit später auch SL-Popups und der Shop darauf aufsetzen können.
- **Lage aus der Kennung abgeleitet** (kleine Streufunktion über die Item-ID): dasselbe Fenster geht immer an derselben Stelle auf, verschiedene Fenster an verschiedenen — Marks Wunsch "nicht zwingend immer in der Mitte", ohne dass etwas bei jedem Öffnen umherspringt. Bereich 36–64 %, also deutlich aus der Mitte, aber nie am Rand klebend.
- Am Handy bildschirmfüllend von unten, mit Griff oben mittig; darüber ein freistehendes Fenster mit Neonrahmen im Ton des Bereichs.
- Schließt per ✕, Escape und Klick auf den Hintergrund. Der Hintergrund wird währenddessen am Scrollen gehindert.
- **Der Detailbereich eines Gegenstands liegt jetzt hier** statt inline aufzuklappen. Damit erledigt sich auch der alte, bewusst vertagte Breite-Bug: das Akkordeon riss die Karte bei langen Inhalten auf, ein Fenster hat feste Maße.
- `GegenstandRow` hat dafür zwei Darstellungen (`kachel`) bei **einem** gemeinsamen Fenster — im Charakterblatt bleibt die kompakte Zeile, in der Übersicht die Kachel.

**"Nie scrollen" ist jetzt echt umgesetzt** — aber bewusst **bereichsweise**:
- `.cl-shell` hat feste Höhe (`100svh`) statt `min-height`; nur so hat ein Bereich eine ausmessbare Fläche.
- Die Hülle nimmt ein `statisch`-Flag. Gesetzte Bereiche bekommen `overflow: hidden` und teilen sich selbst ein, alle anderen scrollen weiter wie bisher. **Nur für Ansichten setzen, die dafür gebaut sind** — sonst wird Inhalt unerreichbar abgeschnitten. Derzeit einzig die Gegenstände-Übersicht.
- Die Gegenstände-Übersicht **misst ihre Fläche aus** (`useProSeite` mit `ResizeObserver`) und rechnet daraus, wie viele Kacheln hineinpassen; der Rest wird geblättert. Passt sich damit Hoch- und Querformat am Tablet gleichermaßen an, statt auf eine geratene Kachelzahl zu setzen.
- Dazu Suche (Name, Typ **und Besitzer** — "alle Waffen von Kira" ist die häufigere Frage als der exakte Name) und ein Besitzerfilter. Das Anlegen-Formular ist hinter "+ Neu" eingeklappt, damit es keine feste Höhe kostet.
- Verifiziert auf Tablet (768×1024) und Handy (412×915): `document.body.scrollHeight` entspricht exakt der Bildschirmhöhe, der Inhaltsbereich hat keinen Überlauf.

**Der Graph füllt inzwischen ebenfalls die Fläche** statt einer starren Höhe von 520px und ist damit der zweite statische Bereich. Cytoscape braucht dafür einen `ResizeObserver` am Container — ein `window`-resize-Listener allein genügt nicht, weil sich die Zeichenfläche auch ohne Fensteränderung verschiebt (Bereichswechsel, ausfahrendes Menü).

**Noch offen:** der Bereich "Welt" scrollt weiterhin — er muss sich erst selbst einteilen, bevor er `statisch` bekommen kann. Dieselbe Frage wie bei den Gegenständen: Kacheln oder Tabelle, Blättern, Suche. Bewusst nicht blind nach demselben Muster gebaut, solange das Kachel-Konzept nicht bestätigt ist.

## Spieler-Ansicht: geplanter Umbau (29.08.2026, noch nicht gebaut)

Marks Vorgaben nach dem ersten Blick aufs Tablet. Die derzeitige Spieler-Ansicht (Kontakte/Inventar/Orte/Beziehungen) ist ein Zwischenstand und wird davon weitgehend abgelöst.

- **Das Hauptfenster ist das eigene Charakterblatt**, nicht eine Liste. Es öffnet als Erstes.
- **Nur lesend**: keine Punkte hinzufügen oder abziehen. Werte ändert die Spielleitung bzw. später der Level-Up-Modus.
- **Das Charakterblatt richtet sich dynamisch nach dem Charakter** — wer keine Sphären hat, sieht keine Sphären-Abschnitte, wer Drohnen führt, bekommt die entsprechenden Teile. Der Aufbau folgt also den gesetzten Werten, nicht einer festen Maske.
- **Fremde Charakterblätter sind tabu** — weder von anderen Spielern noch von NPCs. (Serverseitig steht das noch aus: `GET /personen/{id}/werte` ist bislang ungefiltert, siehe CLAUDE.md.)
- **Kontakte wie ein Telefonbuch**: eigenes Menü, Namensliste, nicht die jetzige Kartenansicht.
- **Popups gehen animiert auf, und zwar von der Stelle, auf die getippt wurde.** Das jetzige Fenster erscheint schlicht — die Streuung der Position steht schon, die Herkunftsanimation fehlt.
- **SL-Benachrichtigungen kommen aus einem Blitz-Symbol rechts** in der oberen Leiste und klappen von dort auf. Entspricht der schon länger notierten Phase-5-Idee (Symbol oben rechts als Ursprung), jetzt konkret als Blitz und rechtsbündig.

Technisch vorbereitet ist dafür bereits: das Fenstersystem (`shell/Fenster.tsx`) muss einen Ursprungspunkt entgegennehmen und `transform-origin` daraus setzen; die Werte-Route braucht eine Sichtbarkeitsprüfung; das Charakterblatt braucht eine lesende Variante ohne Bedienelemente.

## Charakterblatt (gebaut 29.08.2026)

Das **Hauptfenster des Spielers** — erster Bereich, Startansicht. `traits/Charakterblatt.tsx`, Daten aus `GET .../personen/{id}/bogen`.

- **Nur lesend.** `DotPool` ohne `onChange` zeigt Punkte, ohne sie ändern zu lassen. Werte setzt die Spielleitung, später der Level-Up-Modus.
- **Dynamisch nach Weg:** der Katalog kommt bereits gefiltert vom Server. Ein Magier sieht Arete und Sphären, ein Technomancer NeuroWeaving, wer keinen Weg hat weder noch — und zwar nicht ausgeblendet, sondern gar nicht erst geliefert.
- **Kästchenreihen** (`traits/Kaestchen.tsx`) für Gesundheit, Willenskraft und I.C.E., wie auf dem Papierblatt in Fünfergruppen. Abgehakt wird durchgestrichen statt gefüllt, wie mit dem Stift. Kästchen jenseits des Maximums bleiben angedeutet stehen — man sieht, wie viel Luft nach oben wäre.
- **Offline ist ein eigener Zustand**, nicht Wert 0: ohne Commlink erscheint statt der Reihe der Hinweis „nicht erreichbar, aber auch nicht angreifbar".
- **Farbe je Wertegruppe** (`--cb-ton`): Körperlich rot, Gesellschaftlich bernstein, Geistig blau, Arete und Sphären violett, Fähigkeiten cyan. Die Punkte nehmen den Ton ihrer Gruppe auf.
- **Drei Spalten, spaltenweise gefüllt** — wie auf dem Papierblatt, wo die Fähigkeiten thematisch nach Spalten gruppiert sind (körperlich, gesellschaftlich, geistig, passend zu den Attributen darüber). Zeilenweise gefüllt ginge diese Zuordnung verloren.
- **Die drei Spalten bleiben bis zum Tablet im Hochformat erhalten** (~800px) und darunter. Statt umzubrechen wird enger gesetzt: kleinere Punkte (`--dot-groesse`), kleinere Schrift, weniger Spaltenabstand. Erst auf Handybreite (unter 560px) fällt es auf eine Spalte.

> Beim ersten Versuch lag die Umbruchgrenze bei 900px — das Tablet im Hochformat fiel damit auf zwei Spalten. **Layout immer im Hochformat prüfen**, das ist Marks eigentliches Format; im Querformat fällt so etwas nicht auf.

**Vorbereitet, aber noch ohne Wirkung:** `onWertGewaehlt` — antippen einer Fähigkeit meldet Name, Wert und Kategorie nach oben. Daran hängt später die Probenrechnung (Fertigkeit → Attribut wählen → Würfelpool).

## Verhältnis zum früheren Vorbehalt

Die Plandatei `C:\Users\Mark\.claude\plans\gut-pnp-steht-f-r-temporal-waterfall.md` hatte den Umbau verschoben, weil *"der Funktionsumfang pro Entität noch spürbar wächst"*. Bewusste Differenzierung dazu:
- **Fenster statt Akkordeon** ist robust gegen dieses Argument — je mehr Felder eine Entität bekommt, desto mehr lohnt sich das Fenster.
- **Bereichs-Navigation** ebenfalls: dass ein Charakterbogen später mehr Felder hat, ändert nichts daran, dass Orte und Gegenstände eigene Bereiche sind.
- **Das Innere des Charakterbogens** ist das, was tatsächlich noch wächst (Box-Tracks, Cyberware, Begleiter-Blätter). Dort weiterhin zurückhalten und nicht durchdesignen.

## Fächer statt Reiter (30.08.2026)

Marks Bild fürs Inventar: *"man kann ja nicht so viel direkt am Körper tragen…
ich frage mich ob es gut wäre wenn man die Ausrüstung sehen würde und man dort
den Behälter auswählen kann, dass man Rucksack als Popup bekommt, das gibt dann
auch die Illusion dass man auf den Rucksack nicht so schnell zugreifen kann wie
auf direkt Ausgerüstetes."*

- **Die Hauptansicht zeigt nur, was am Körper ist.** Sie scrollt nicht, das
  Raster wird ausgemessen und geblättert.
- **Alles andere sind Fächer** in einer Leiste am unteren Rand: der getragene
  Behälter, jedes eigene Fahrzeug, jeder Lagerort, und was andere haben. Ein
  Fach geht als Fenster auf — das Aufmachen *ist* die Handlung und trägt
  zugleich die Aussage, dass man da nicht so schnell drankommt.
- **Ein Fahrzeug ist auch dann ein Fach, wenn nichts darin liegt.** Man will
  nachsehen können, statt zu rätseln, ob das Auto weg ist. Im Fenster steht
  es selbst zuoberst, darunter sein Inhalt.
- **Fenster in Fenstern sind erwünscht** (Marks Wort: sieht cyberpunkig aus).
  Kachel im Fach → Gegenstandsfenster über dem Fachfenster.

**Scrollen: die Regel ist geschärft.** *"Ich habe die Idee, dass das Scrollen in
Popups ok ist, da das die Illusion des Screens nicht bricht, ich will nur in der
Hauptansicht kein Scrollen."* Damit gilt: Hauptansichten teilen sich die Fläche
ein und blättern; in Fenstern ist Scrollen ausdrücklich erlaubt.
