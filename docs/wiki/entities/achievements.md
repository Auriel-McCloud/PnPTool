---
title: Achievements
created: 2026-09-27
updated: 2026-10-10
type: entität
tags: [ereignisprotokoll, ki-integration, datenmodell, ui, kampf, erfahrung, backend, frontend]
sources: [../../../CLAUDE.md, ereignisprotokoll.md, concepts/erfahrung-und-steigern.md]
status: gebaut
---

# Achievements

**Status: Backend + Frontend gebaut (10.10.2026), `tsc -b` sauber, eigene
Backend-Tests grün. Browser-Klicktest am Spieltisch noch offen.** Modul
`backend/app/achievements/` (`schemas.py`, `repository.py`, `trigger.py`,
`belohnung.py`, `routes.py`), Router in `app/main.py`. Frontend:
`frontend/src/achievements/` (`AchievementVerwaltung.tsx` für die SL,
`MeineAchievements.tsx` für Spieler, beide über das 🏆-Symbol in der
Werkzeugleiste erreichbar).
Auslöser: beim Durchsprechen des Ereignisprotokolls kam Mark
selbst auf Achievements zurück, mit einer Liste von Beispielen und dem
ausdrücklichen Wunsch nach **beidem**: automatischer Erkennung aus dem Log
UND spontaner Vergabe von Hand.

## Marks Beispiele (27.09.2026)

*"First Blood" / "erster Kill", "hat den meisten Schaden genommen", "hat den
meisten Schaden verteilt", "erster gekaufter Gegenstand außerhalb der
Charaktererstellung", "Hello World", "erste Verhandlung"*

Diese Beispiele zerfallen bei genauerem Hinsehen in **zwei fachlich
unterschiedliche Sorten**, die das Datenmodell auch unterschiedlich
behandeln muss:

- **Meilenstein** — einmal erreicht, für immer wahr ("erster Kill",
  "Hello World", "erste Verhandlung", "erster Kauf").
- **Rekord** — kann den Träger wechseln, weil morgen jemand anderes den Wert
  übertrifft ("meisten Schaden genommen/verteilt").

## Das `einzigartig`-Häkchen (Marks Lösung)

Mark, nach Rückfrage: *"nur einmal pro Kampagne, aber jeder könnte ein
'Mörder'-Achievement erhalten, ein 'First Kill' bekommt nur der mit dem
First Kill — wir machen einfach wieder ein 'einzigartiges Achievement'
Häkchen für einzigartige pro Kampagne, und den Rest kann jeder erhalten."*

**Wiederverwendet ein bestehendes Projektkonzept 1:1**, statt etwas Neues zu
erfinden: `Gegenstand.einzigartig` unterscheidet schon länger Unikat
(genau ein Exemplar, Besitzer kann wechseln) von Vorlage (beliebig oft
kopierbar) — siehe [[../concepts/waehrung-und-preise]]. Bei Achievements
bedeutet dasselbe Häkchen:

- **`einzigartig: false`** — jede Person kann es unabhängig erhalten
  ("Mörder": jeder, der irgendwann einen Kill hat, bekommt sein eigenes).
- **`einzigartig: true`** — höchstens EIN Träger campaign-weit gleichzeitig
  ("First Kill": nur wer zuerst tötet).

**Kein zusätzliches Feld für "kann der Träger wechseln?" nötig** — das
ergibt sich automatisch aus der Auslöseart: Ein Meilenstein-Trigger wie
"war die erste Person, die X getan hat" kann nach der ersten Vergabe
logisch nie wieder zutreffen (es gab ja schon einen Ersten) — der Träger
bleibt also für immer derselbe, ganz ohne Sonderregel. Ein Rekord-Trigger
wie "höchster je verursachter Schaden in einem Treffer" kann dagegen bei
jedem neuen `KampfLogEintrag` erneut geprüft werden und den Titel weiterreichen
— genau wie ein einzigartiger Gegenstand per `GegenstandsBewegung` den
Besitzer wechselt (siehe [[ereignisprotokoll]]). Dieselbe Grundidee wird
hier für Achievements wiederverwendet.

## Datenmodell

```cypher
(:Achievement {
  id: uuid,
  campaignId: uuid,
  name: string,
  beschreibung: string,     # was das Achievement bedeutet, Kurzfassung
  icon: string,             # optional, Symbol/Emoji
  art: "AUTO" | "MANUELL",  # automatisch erkannt oder nur von Hand vergebbar
  auslöseArt: string | null, # nur bei AUTO, siehe Trigger-Katalog unten
  einzigartig: bool,         # s.o. — analog Gegenstand.einzigartig

  # Mechanische Wirkung (10.10.2026, Mark: "Achievements sollen was bringen,
  # nicht nur kosmetisch sein") — fest am Achievement hinterlegt, nicht frei
  # wählbar bei der einzelnen Vergabe. Wiederverwendet den bestehenden
  # Hintergrund-Katalog statt etwas Neues zu erfinden: Hintergrund lässt sich
  # nach der Erstellung bisher GAR NICHT mehr steigern (LevelUp.tsx lässt die
  # Kategorie bewusst aus — "das kann nur noch die SL vergeben"). Ein
  # Achievement mit belohnungsArt=HINTERGRUND ist damit der erste und einzige
  # Weg, wie ein Spieler nach der Erstellung noch Hintergrundpunkte bekommt.
  belohnungsArt: "KEINE" | "EP" | "HINTERGRUND",
  belohnungsMenge: int,              # nur relevant wenn belohnungsArt != KEINE
  belohnungsHintergrund: string | null, # nur bei HINTERGRUND: welcher Name
                                         # aus HINTERGRUENDE (erstellung.py),
                                         # z.B. "Mörder" -> immer "Ruf"

  # Ziel-Parametrisierung (10.10.2026) — macht EINEN Trigger-Typ für beliebig
  # viele konkrete Gegenstände wiederverwendbar, statt für jeden Gegenstand
  # (Beta-Isotop, farbiger Ki-Kristall, ...) einen eigenen auslöseArt-Wert
  # hart in den Code zu schreiben. Die SL wählt den Zielgegenstand beim
  # Anlegen des Achievements aus dem bestehenden Gegenstands-Katalog.
  zielGegenstandId: string | null   # nur bei ERSTER_BESITZ_ZIEL /
                                     # ERSTE_BESCHREIBUNG_ZIEL
})

(:AchievementVerleihung {
  ...Basis (aus ereignisprotokoll.md: zeitpunkt, ingameZeitpunkt, sitzungId,
            slNotiz, geloescht, campaignId),
  text: string,       # personalisierter Achievement-Text (KI oder SL-Freitext)
  abgeloest: bool      # nur relevant bei einzigartig=true + Rekord-Auslöser:
                        # wurde der Titel später an jemand anderen weitergegeben?
})-[:PERSON]->(:Person)
  -[:ACHIEVEMENT]->(:Achievement)
```

**Aktueller Träger eines einzigartigen Achievements** = die neueste
`AchievementVerleihung` mit `abgeloest: false`. Ältere Verleihungen bleiben
stehen (Papierkorb-Prinzip, kein Löschen) — damit lässt sich später auch
"wer hatte den Rekord vor Fred" beantworten.

## Trigger-Katalog (Beispiele, fest im Code, erweiterbar)

Ein AUTO-Achievement braucht eine feste `auslöseArt` aus einem Code-Katalog
(analog zu `GEGENSTAND_TYPEN` — kein Freitext, den die KI erfinden könnte).
Erste Belegung, direkt an Marks Beispielen:

| `auslöseArt` | Prüft gegen | `einzigartig` empfohlen | Beispiel |
|---|---|---|---|
| `ERSTER_KILL` | erster `KampfLogEintrag` mit `art: "TOD"` campaign-weit, Angreifer wird Träger | `true` | "First Blood" |
| `MOERDER` | pro Person: hat sie irgendwann einen `KampfLogEintrag` mit `art: "TOD"` als Angreifer? | `false` | "Mörder" — jeder kriegt seins |
| `MEISTE_SCHADEN_GENOMMEN` | höchster `hpMenge`-Wert über alle `KampfLogEintrag` mit dieser Person als `ZIEL` | `true` (Rekord, wandert) | "hat den meisten Schaden genommen" |
| `MEISTE_SCHADEN_VERTEILT` | höchster `hpMenge`-Wert über alle `KampfLogEintrag` mit dieser Person als `ANGREIFER` | `true` (Rekord, wandert) | "hat den meisten Schaden verteilt" |
| `ERSTER_KAUF` | pro Person: erste `GegenstandsBewegung` mit `art: "GEKAUFT"` und dieser Person als `NEUER_BESITZER` | `false` | "erster gekaufter Gegenstand außerhalb der Erstellung" |
| `ERSTE_VERHANDLUNG` | pro Person: erster `VerhandlungsAusgang` mit dieser Person beteiligt | `false` | "erste Verhandlung" |
| `CHARAKTER_ERSTELLT` | `Person.erstellungAbgeschlossen` wechselt von `false` auf `true` | `false` | "Hello World" |
| `GEHEIMNISTRAEGER` | `sichtbarkeit` einer Beschreibung/Notiz wechselt auf `SPEZIFISCH` mit genau EINER Person in `sichtbarFuer` | `false` | "Du weißt etwas, das sonst keiner weiß" |
| `ERSTER_BESITZ_ZIEL` | pro Person: erste `GegenstandsBewegung` mit dieser Person als `NEUER_BESITZER`, Gegenstand = `Achievement.zielGegenstandId` | `false` (meist pro Fund wiederholbar) | "Du hältst ein β⁺-Isotop in den Händen" |
| `ERSTE_BESCHREIBUNG_ZIEL` | Beschreibung des Gegenstands `Achievement.zielGegenstandId` wechselt für diese Person von gesperrt auf sichtbar (`sichtbarkeit`/`entities/visibility.py::is_visible_to` erstmals `true`) | `false` | "Du hast herausgefunden, was der grüne Ki-Kristall ist" |
| `ERSTER_CRITTER` | pro Person: erste `BEGLEITET`-Kante von einem `Person{istCritter:true}` auf diese Person | `false` | "Du besitzt jetzt ein Haustier" |
| `ERSTE_DROHNE` | pro Person: erster `Begleiter{art:"BEGLEITER"}` mit `besitzerId` = diese Person | `false` | "Du bist jetzt eine Drohne" |
| `ENDBOSS_BESIEGT` | `KampfLogEintrag` mit `art:"TOD"`, Ziel = `Person{istEndboss:true}`, Angreifer wird Träger | `true` | "You Killed the Big Bad Guy" |
| `ERSTE_SITZUNG_UEBERLEBT` | beim Anlegen der ZWEITEN `Sitzung` einer Kampagne: alle PCs ohne `KampfLogEintrag{art:"TOD"}` als Ziel während der ersten Sitzung | `false` | "Du hast dein erstes Abenteuer überstanden" |

**Warum `CHARAKTER_ERSTELLT` funktioniert, obwohl die Charaktererstellung
selbst NICHT geloggt wird** (siehe [[ereignisprotokoll]], Marks
Entscheidung): der Trigger hängt nicht an einem Log-Eintrag, sondern direkt
am bestehenden `Person.erstellungAbgeschlossen`-Feld — kein neuer Code-Pfad
nötig, nur eine Prüfung an der Stelle, wo dieses Feld schon auf `true`
gesetzt wird (`traits/erstellung.py`).

**Neues Personen-Flag für `ENDBOSS_BESIEGT`:** `Person.istEndboss: bool`
(Default `false`), analog zu `istCritter`/`istKI` — ein NPC, den die SL als
Endgegner markiert. Reines Markierungsfeld, kein eigener Knotentyp nötig.

**`ERSTE_SITZUNG_UEBERLEBT` braucht keinen "Sitzung beenden"-Knopf:** da es
im Tool kein explizites Sitzungsende gibt (nur "zuletzt angelegte Sitzung =
aktiv", siehe [[ereignisprotokoll]]), prüft der Trigger rückwirkend beim
**Anlegen der zweiten Sitzung** einer Kampagne, welche PCs während der
ersten Sitzung keinen Tod erlitten haben. Mark bestätigt diesen
Kompromiss statt eines größeren Umbaus.

Weitere `auslöseArt`-Werte lassen sich später ergänzen, ohne das Schema
anzufassen (genau wie neue `VerhandlungsArt`-Einträge in `verhandlung/logic.py`).

## Mechanische Belohnung: EP oder Hintergrund (10.10.2026)

Mark: *"ein Achievement der Spieler einen XP bringt... Backgrounds lassen
sich nicht durch XP steigern, also könnte man Backgrounds, und
Background-Punkte durch Achievements erhalten"* — Achievements sind damit
**nicht rein kosmetisch**, sondern können echte Spielmechanik auslösen.

- **`belohnungsArt: "EP"`** — bei Vergabe wird `Person.erfahrung` um
  `belohnungsMenge` erhöht, exakt wie eine manuelle EP-Vergabe durch die SL
  (`traits/erfahrung.py`-Infrastruktur, kein neuer Zahlenweg).
- **`belohnungsArt: "HINTERGRUND"`** — bei Vergabe wird der in
  `belohnungsHintergrund` festgelegte Hintergrund (z. B. "Ruf") um
  `belohnungsMenge` erhöht, gedeckelt auf `HINTERGRUND_MAX` (5). **Das ist
  der einzige Weg, wie ein Hintergrund nach der Charaktererstellung noch
  steigt** — `LevelUp.tsx` schließt `Hintergrund` bewusst aus der
  Spieler-Steigerung aus (siehe [[../concepts/erfahrung-und-steigern]]).
- **`belohnungsArt: "KEINE"`** — rein kosmetisch, z. B. für Flavor-Trophäen
  wie "Hello World".
- **Welcher Hintergrund, ist fest am Achievement hinterlegt**, nicht frei
  wählbar bei der einzelnen Vergabe (Mark: "Mörder" gibt immer "Ruf") — so
  bleibt die KI-Textgenerierung thematisch konsistent mit der Belohnung.

**Bewusst nicht automatisch für "alle erfahren etwas" gebaut:** eine
campaign-weite Enthüllung (z. B. eine Wiki-Seite wird für alle freigegeben)
bekommt **keinen eigenen AUTO-Trigger** — es gibt keine einzelne Person, die
das "tut". Bleibt `MANUELL`: die SL vergibt es spontan an eine, mehrere
oder alle Personen, wenn sie eine Beschreibung campaign-weit freigibt.

## Erkennungs-Pipeline (kein zusätzlicher Warteschlangen-Knoten nötig)

**Bewusst KEIN persistenter "Vorschlag"-Knoten** — anders als z. B. ein
Mitteilungs-Popup, ist ein Achievement-Trigger jederzeit aus dem
bestehenden Log **neu berechenbar** ("hat diese Person schon einen Kill,
und existiert noch keine `ERSTER_KILL`/`MOERDER`-Verleihung an sie?"). Das
spart einen weiteren Knotentyp und folgt demselben Muster wie der
bestehende KI-Sortiment-Vorschlag (`GET .../ki-vorschlaege` — live
berechnet, nichts gespeichert, bis der SL bestätigt):

- **`GET .../achievements/vorschlaege`** — durchläuft alle `AUTO`-Achievements
  der Kampagne, prüft pro `auslöseArt` gegen den aktuellen Log-Stand, filtert
  bereits verliehene (nicht abgelöste) Fälle heraus. Liefert eine Liste
  offener Vorschläge (Person + Achievement + auslösender Log-Eintrag als
  Kontext).
- **`POST .../achievements/vorschlaege/{...}/anwenden`** — SL bestätigt EINEN
  Vorschlag. Erst hier generiert die KI den personalisierten Text (siehe
  unten), danach entsteht die `AchievementVerleihung`. Bei einem
  Rekord-Auslöser (`einzigartig: true` + `MEISTE_SCHADEN_*`) wird die
  bisherige Trägerin zuerst auf `abgeloest: true` gesetzt.
- Kein automatischer Hintergrundlauf (Mark ist kostenbewusst, wie beim
  Wiki-Rechtschreib-Sweep) — der SL öffnet die Vorschlagsliste gezielt,
  z. B. am Ende einer Sitzung.

## KI-Text, thematisch auf die letzten Ereignisse bezogen

Mark: *"dann wieder von Mistral oder Gemini genauso einen Achievement-Text
bekommen wie bei der Charaktererschaffung, aber thematisch auf die letzten
Ereignisse, den Ort und das Event bezogen."*

Wiederverwendet die bestehende Infrastruktur (`app/ki/kontext.py::sammle_kontext`,
dieselbe wie beim NPC-Generator/der Ideenschmiede), erweitert um den
**auslösenden Log-Eintrag als Zusatzkontext**: bei `ERSTER_KILL` z. B. der
`KampfLogEintrag` selbst (welche Person, welcher Gegner, `hpArt`/`hpMenge`)
plus — sofern zum Zeitpunkt ein `Aufenthalt`-Eintrag existiert (siehe
[[ereignisprotokoll]]) — Ort/Event, an dem es passierte. Die KI bekommt
damit "wer, was, wo, im Rahmen welcher Sitzung" statt nur einen nackten
Achievement-Namen — Ergebnis ist ein Text wie *"Im Schatten der Docks von
Omikron² Eridiani zog Ryu zum ersten Mal wirklich Blut..."* statt einer
generischen Trophäenbeschreibung. Genau wie beim ✨-KI-Knopf überall sonst:
**Vorschau vor dem Speichern**, SL kann den Text noch anpassen, bevor die
`AchievementVerleihung` entsteht.

## Spontane Vergabe (Mark: "spontan selbst einen erzeugen und zuweisen")

Zweiter, unabhängiger Weg — jederzeit, ohne Bezug zu einem Auto-Trigger:

- **Neues Achievement anlegen**: eigenes Baukasten-Popup (Commlink-Stil,
  analog zum Rassen-Baukasten — siehe [[rassen-baukasten-feature]]), Felder
  Name/Beschreibung/Icon/`einzigartig`-Häkchen, `art: "MANUELL"`, plus die
  Belohnungsfelder (`belohnungsArt`, `belohnungsMenge`,
  `belohnungsHintergrund` per Dropdown aus dem Hintergrund-Katalog).
  Bei `art: "AUTO"` zusätzlich `auslöseArt`-Dropdown aus dem Code-Katalog
  oben, bei `ERSTER_BESITZ_ZIEL`/`ERSTE_BESCHREIBUNG_ZIEL` ein weiteres
  Dropdown zur Auswahl des Zielgegenstands aus dem bestehenden Katalog.
- **Direkt einer Person zuweisen**: Auswahl-Popup (Person + Achievement aus
  dem Katalog), optionaler ✨-KI-Knopf für den Text (derselbe Mechanismus
  wie oben, nur ohne automatischen Auslöser-Kontext — nur allgemeiner
  Kampagnenkontext), oder komplett freier SL-Text.
- Ein bereits bestehendes `MANUELL`-Achievement lässt sich jederzeit erneut
  vergeben (an eine andere Person, oder — falls nicht `einzigartig` — an
  mehrere).

## UI (27.09.2026, Marks Vorgabe)

**Pokal-Symbol 🏆 in der oberen Werkzeugleiste** (`cl-leiste-werkzeuge` in
`frontend/src/shell/CommlinkShell.tsx` — derselbe Slot, in dem heute schon
`ErklaerungSchalter`/`ThemeSchalter` sitzen), sichtbar für SL **und**
Spieler gleichermaßen. Kein neuer Burgermenü-Eintrag in der
Symbolspalte/`BEREICHE` — Mark wollte es bewusst als Kopfzeilen-Symbol,
nicht als eigenen Bereich.

**Klick-Verhalten unterscheidet sich nach Rolle:**

- **Spieler** — öffnet ein scrollbares Popup mit den **eigenen** erhaltenen
  Achievements, **neuestes zuerst** (sortiert nach
  `AchievementVerleihung.zeitpunkt` absteigend). Jeder Eintrag lässt sich
  erneut antippen/öffnen, um den vollen (KI- oder SL-)Text nochmal zu lesen
  — nicht nur eine einmalige Toast-Meldung.
- **SL** — öffnet stattdessen ein volles Fenster im Burgermenü-Stil (Mark:
  *"für den SL sollte es ein Burgermenü sein, damit man sich mit dem
  Entwerfen leichter tut"*) — die eigentliche Verwaltungsoberfläche: Katalog
  aller `Achievement`-Definitionen, "+ Neu anlegen"-Baukasten (siehe oben),
  Liste offener Auto-Trigger-Vorschläge zum Bestätigen, manuelle Vergabe an
  eine Person. Analog zum bestehenden Rassen-Baukasten-Fenster, nur über das
  Pokal-Symbol statt einen Symbolspalten-Eintrag erreicht.

**Automatisches Aufpoppen neuer Achievements** — sobald eine
`AchievementVerleihung` entsteht, bekommt die betroffene Person automatisch
ein Popup zu sehen (analog zum bestehenden Mitteilungs-Live-Kanal, siehe
[[mitteilungen-system]]), **außer während eines laufenden Kampfs**:

> Mark: *"wenn es nicht gerade den Kampf ist sollten neue Achievements als
> Popup aufpoppen, die man während dem Kampf erhält sollten nach dem Kampf
> aufpoppen"*

Technisch: beim Entstehen einer Verleihung wird geprüft, ob gerade ein
`Kampf` für die Kampagne läuft (`backend/app/kampf/repository.py::hole`).
Läuft keiner → sofortiger Live-Push, wie eine normale Mitteilung. Läuft
einer → die Verleihung wird zurückgehalten (kein Push), bis der Kampf endet
(`DELETE .../kampf`, `backend/app/kampf/routes.py::beende`) — dort werden
dann alle in der Zwischenzeit entstandenen, noch nicht zugestellten
Verleihungen an ihre jeweiligen Empfänger nachgeliefert. Passt inhaltlich
gut zusammen: gerade Kampf-Achievements (`ERSTER_KILL`,
`MEISTE_SCHADEN_*`) entstehen naturgemäß oft mitten im Gefecht — ein Popup
mittendrin würde vom eigentlichen Kampfgeschehen ablenken.

## Offene Fragen (bewusst nicht Teil dieser Runde)

- Weitere `auslöseArt`-Werte über die zwölf oben hinaus (Mark hatte auch
  Kampagnen-Enden im Blick, o. Ä.) — Katalog ist bewusst offen erweiterbar,
  keine abschließende Liste.
- `ERSTE_BESCHREIBUNG_ZIEL` braucht beim Bauen eine Entscheidung, welche
  konkrete Sichtbarkeits-Prüfung genau als "wechselt auf sichtbar" zählt
  (Gegenstands-`sichtbarkeit` direkt, oder zusätzlich über die geplante
  [[spieler-lexikon]]-Entdeckungskette) — zum Zeitpunkt dieser Runde ist das
  Lexikon-Feature selbst noch nicht gebaut.

## Siehe auch

- [[ereignisprotokoll]] — Basis-Log-Kategorien, die die AUTO-Trigger auswerten
- [[../concepts/waehrung-und-preise]] — `Gegenstand.einzigartig`, Vorbild fürs Achievement-Häkchen
- [[../concepts/erfahrung-und-steigern]] — EP-Vergabe, Hintergrund-Steigerungssperre nach der Erstellung
- [[rassen-baukasten-feature]] — Vorbild für den Achievement-Baukasten (Katalog + Freigabe-Popup-Stil)
- [[ki-integration]] — KI-Text-Infrastruktur (`sammle_kontext`, ✨-Knopf-Muster)
- [[mitteilungen-system]] — Live-Push-Mechanismus, den das Achievement-Popup wiederverwendet
- [[../../api/kampf.md]] — `Kampf`-Zustand, entscheidet ob ein Popup sofort oder erst nach Kampfende kommt
- [[../../../CLAUDE.md]] — Punkt 17 unter "Geplante Features"
