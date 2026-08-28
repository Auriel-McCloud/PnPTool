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

## Offen

- **Farbwelt und Typografie** — noch nicht entschieden.
- Welche Symbole genau in die obere Leiste gehören (über SL-Popups und Tooltip-Schalter hinaus).
- Ob "Notizen" spielereigene Notizen meint oder die bestehenden SL-Notizfelder.
- "Kontakte" ist vermutlich die Spielersicht auf Personen — Verhältnis zu den SL-Bereichen PCs/NPCs noch zu klären.
- Ob die Störeffekte abschaltbar sein sollen (Empfehlung: ja, mindestens für längere Sitzungen).
- Der **Regeln-Bereich** ist weiterhin ein komplett neuer Inhaltstyp (siehe Plandatei): vermutlich eine Rich-Text-Seite pro Kampagne, campaign-weit statt an eine Entität gebunden.

## Verhältnis zum früheren Vorbehalt

Die Plandatei `C:\Users\Mark\.claude\plans\gut-pnp-steht-f-r-temporal-waterfall.md` hatte den Umbau verschoben, weil *"der Funktionsumfang pro Entität noch spürbar wächst"*. Bewusste Differenzierung dazu:
- **Fenster statt Akkordeon** ist robust gegen dieses Argument — je mehr Felder eine Entität bekommt, desto mehr lohnt sich das Fenster.
- **Bereichs-Navigation** ebenfalls: dass ein Charakterbogen später mehr Felder hat, ändert nichts daran, dass Orte und Gegenstände eigene Bereiche sind.
- **Das Innere des Charakterbogens** ist das, was tatsächlich noch wächst (Box-Tracks, Cyberware, Begleiter-Blätter). Dort weiterhin zurückhalten und nicht durchdesignen.
