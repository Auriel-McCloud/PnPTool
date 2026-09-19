---
title: UI-Konzept — Das Commlink
created: 2026-09-18
updated: 2026-09-19
type: entität
tags: [ui, frontend]
sources: [../../ui-konzept.md, ../../../frontend/src/shell/CommlinkShell.tsx, ../../../frontend/src/shell/commlink.css]
status: teilweise-umgesetzt
---

# UI-Konzept — Das Commlink

Festgehalten 28.08.2026. Leitbild: Oberfläche soll sich wie ein **Commlink**
(Zukunfts-Smartphone der Spielwelt) anfühlen, nicht wie ein Verwaltungswerkzeug.
Zielgerät: **Tablet**, Touch als Normalfall.

## Kernprinzipien

- **Kein Scrollen auf Übersichtsseiten** (Marks weitreichendste Vorgabe) —
  feste Höhe, Raster mit fester Kachelzahl, Blättern statt Scrollen. Scrollen
  bleibt nur in Popups/Fenstern erlaubt.
- **Fenster statt Inline-Akkordeons** — ein Gegenstand öffnet sich als eigenes
  fokussiertes Fenster; Position wechselt bewusst (nicht immer zentriert),
  abgeleitet aus einer Streufunktion über die Item-ID (dasselbe Fenster immer
  an derselben Stelle, verschiedene Fenster an verschiedenen).
- **Eine Hülle für beide Rollen** (SL/Spieler) — SL bekommt mehr Bereiche/Felder,
  Spieler die schlanke Ansicht. Einmal bauen, zweimal nutzen.
- **Neonfarben tragen Bedeutung, nicht Dekoration** — Magenta „SL-geheim",
  Cyan „aktiv/Fokus" (siehe [[theming-system]]).
- **`prefers-reduced-motion` wird respektiert** — inkl. Flackern-Effekt.

## Navigation (nach Marks Rückmeldung überarbeitet)

Ab 600px: schmale Symbolspalte (60px), angetippt fährt nur der eine Eintrag
heraus (nicht das ganze Menü), zweites Antippen wechselt den Bereich. Unter
600px: Schublade hinter ☰. Bereichswechsel ist **inszeniert**: Name löst sich
aus dem Menü, fliegt nach oben, Leuchtbalken fährt herab.

## Stand der Umsetzung (Auszug, siehe `docs/ui-konzept.md` für Details)

**Gebaut:** Commlink-Hülle (28.08.2026), Navigation-Überarbeitung, Fenstersystem
(29.08.2026), Kampfmodus (30.08.2026), Tooltip-System (30.08.2026, Schieberegler
+ `Erklaerung`-Knoten je Regelwerk).

**Noch nicht gebaut:** feinerer Bereichsschnitt (PCs/NPCs/Orte/Events aus
`EntityManager` „Welt" heraustrennen), SL-Popup-Symbol ist angelegt aber
deaktiviert.

## Kampagnenweite Einstellungen — ein Ort, nicht zwei

`EinstellungenFenster.tsx` ist die **einzige** Stelle für Regel-Schalter, die
für die ganze Kampagne gelten (digitales Würfeln, Gewicht/Traglast-Anzeige,
Messenger an/aus). Über die Werkzeugleiste erreichbar (`App.tsx`,
`einstellungenOffen`-State), unabhängig vom Bereichsmenü links.

**18.09.2026 aufgeräumt:** Der „Zugang"-Bereich (`SpielerVerwaltung.tsx`,
`bereich === "zugang"` in `App.tsx`) hatte einen eigenen, redundanten
„Spielregeln"-Abschnitt mit demselben Gewicht/Traglast-Schalter — eine der
ersten Baustellen des Projekts, nie aufgeräumt. Der Zugang-Bereich ist jetzt
wieder rein das, was der Name sagt: Spielerzugänge anlegen und Charakteren
zuordnen. Kampagnenweite Regeln gehören ins Einstellungen-Fenster, nicht in
einen thematisch anderen Bereich.

## Das Gerät blutet mit (Verwundungsanzeige)

`frontend/src/shell/Verwundung.tsx` + `verwundung.css` — Marks Bild: nicht
nur der Charakterbogen zeigt niedrige Gesundheit, das ganze Gerät soll es
spüren lassen. Ein Schein vom unteren Bildschirmrand her, dessen Höhe und
Deckkraft mit dem Schaden wachsen; bleibt nur noch wenig Gesundheit, pulst
er im Herzschlag-Rhythmus (zwei Stöße, dann Pause — kein gleichmäßiges
Auf/Ab). Nimmt keine Eingaben an, respektiert `prefers-reduced-motion`.
Nur in der Spieler-Ansicht (`SpielerAnsicht.tsx`), nicht bei der SL.

**19.09.2026, nach dem ersten Praxistest kalibriert** (Mark: der Effekt
beginne „erst sehr spät" und sei „sehr dezent"):

- **Sichtbarkeitsschwelle eingeführt:** vorher leuchtete der Schein schon
  beim allerersten Kratzer messbar, aber kaum wahrnehmbar. Jetzt bleibt bis
  zur **Hälfte der maximalen Gesundheit** komplett Ruhe — ein Kratzer soll
  nicht schon leuchten — und erst danach beginnt der Effekt.
- **Wurzel-Kurve statt linear:** nach der Schwelle steigt die Intensität mit
  `Math.pow(anteil, 0.6)` statt 1:1 mit dem Schaden — dieselbe Restspanne an
  Gesundheit wirkt dadurch in der zweiten Hälfte deutlich schneller
  bedrohlich als vorher.
- **Herzschlag relativ statt absolut:** vorher eine feste Schwelle „≤2
  Kästchen übrig", die bei hoher maximaler Gesundheit (z.B. mit
  Chrom-Bonus, bis 18 Kästchen) fast nie ausgelöst hat. Jetzt **ab 75%
  Schaden relativ zum Maximum** — skaliert mit jedem Charakter mit.
- CSS-Verlauf (`verwundung.css`) parallel intensiviert: höhere
  Ziel-Deckkraft (0.75 statt 0.55) und ein kompakterer Übergang, damit die
  spätere Startschwelle nicht durch einen zu sanften Anstieg wieder verpufft.

## Das Gerät stört mit (Neonflackern)

`frontend/src/shell/CommlinkShell.tsx` (`Stoerung`-Komponente) +
`commlink.css` (`.cl-stoerung`). Seltener Störeffekt (alle 5–10 Minuten,
zufällig) — Marks Ausgangsbild: eine Neonröhre oder ein gestörter alter
Fernseher.

**19.09.2026, nach dem ersten Praxistest verstärkt** (Mark: „das Flackern
ist zu kurz", gewünschtes Bild: *"wie bei einem alten Fernseher wo das
Bild kurzzeitig mit schwarz-weißen Ameisenkrieg-Flecken übersäht ist, aber
das Bild drunter noch verzerrt durchscheint"*):

- **Dauer mehr als verdreifacht:** 0,45s → 1,6s (`STOERUNG_MS` in
  `CommlinkShell.tsx`).
- **Optik komplett neu, drei übereinanderliegende Schichten statt nur
  Farbtönung:**
  1. `.cl-stoerung` selbst — der bisherige Neon-Tint + Vignette
     (`cl-flackern`), jetzt über 8 statt 3 Schübe verteilt
  2. `::before` — echtes Schwarz-Weiß-Bildrauschen ("Ameisenkrieg") aus
     einem SVG-`feTurbulence`-Filter (Graustufen, Kontrast hochgezogen),
     per `mix-blend-mode: overlay` über den Inhalt gelegt statt ihn zu
     ersetzen, mit leichter Verschiebung zwischen den Schüben
     (`cl-rauschen`)
  3. `::after` — `backdrop-filter` (Blur + Kontrast + Sättigung runter +
     Hue-Shift) verzerrt das Bild darunter sichtbar, ohne es zu verdecken
     — genau der gewünschte "durchscheint"-Effekt (`cl-verzerrung`)
- **`steps(1, end)` statt weichem Fade:** harte Sprünge wirken wie echte
  Empfangsaussetzer statt ein Ein-/Ausblenden. Mehrere kurze Schübe über
  die 1,6s verteilt statt ein einzelner Blitz.
- `prefers-reduced-motion` und die zufällige Taktung unverändert
  respektiert.

## Siehe auch

- [[theming-system]] — technische Umsetzung der Farbwelt
- [[mitteilungen-system]] — SL-Popup-Symbol (angelegt, noch deaktiviert)
- [[architektur-drei-ebenen]] — „Schmiede"-Tab in derselben Shell
