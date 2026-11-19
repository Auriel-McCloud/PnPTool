---
title: Critter-Pet (Tamagotchi)
created: 2026-11-11
updated: 2026-11-19
type: entität
tags: [ui, frontend, backend, datenmodell]
sources: [../../ENTWICKLUNGSHISTORIE.md, gespräch 2026-11-11, gespräch 2026-11-18 (Tierladen)]
status: teilweise-umgesetzt
---

# Critter-Pet (Tamagotchi)

Ein Critter eines Spielers lebt als animiertes Pet-Overlay in der offenen
PnPTool-Webapp und kann auf die Bildschirme anderer Spieler wandern.
Herkunft: Planpunkt 15 in `CLAUDE.md`, erste Skizze 24.09.2026 in
`docs/ENTWICKLUNGSHISTORIE.md` (Punkt 15). Verwandt: [[concepts/augments-ausruestung]]
(Ki-Tama-Critter „heilt mit wie ein Pet“), [[entities/mitteilungen-system]]
(WebSocket-Infrastruktur), [[entities/achievements]] (`ERSTER_CRITTER`).

## Skizze 24.09.2026 (unverändert übernommen)

- Bedürfnisse: füttern (Tierfutter im Shop kaufen/verbrauchen), baden/pflegen.
  Vernachlässigt verliert das Tier Lebenspunkte.
- Persönlichkeit: stellt beim Herumlaufen Chaos an (Dinge „kaputt machen“,
  Häufchen) — reiner Flavor, keine Spielmechanik-Folge.
- Wandern: zwischen den offenen PnPTool-Sitzungen der Spieler einer Party;
  läuft bei einem Client rechts raus, taucht beim nächsten links auf.
- **Entschieden (24.09.):** Weg 1 — DOM-Overlay nur innerhalb der
  Webapp/PWA, kein natives Android-Overlay. Server hält Zustand (Position,
  aktueller Client, Bedürfnisse), Sync per WebSocket wie Mitteilungen.
- Damals: „explizit ganz zum Schluss“ als Bonus-Feature.

## Nachschärfung 11.11.2026

- Pet ist **an einen Critter gekoppelt** (bestehender `Person{istCritter}`
  mit `BEGLEITET`-Kante zum Besitzer).
- Wandert vom Besitzer auf das Display **anderer Leute** (Wortlaut Mark;
  ob nur Party oder alle Verbundenen: siehe offene Achsen).
- Erstes Pet: kleiner roter Drache im Stil von Mushu (Mulan). Pixel-Art ist
  okay, solange es süß aussieht. **Mehr Animationen** als nur Laufen.
- Prototyp-Sprite 11.11.: prozedural per Python/Pillow (48×40 px, Idle +
  Laufen, Auto-Outline) — eigene Figur, nur Mushu-inspiriert, kein
  Disney-Asset.

## Entscheidungen 11.11.2026 (Antwort auf die offenen Achsen)

- **Wanderziel:** nur zu **eingeloggten Party-Mitgliedern**. Serverseitig
  getrackt: läuft bei einem Tablet am Rand raus, taucht bei einem anderen
  rein — nicht zwingend in derselben Sekunde. **Nicht bei der SL.**
- **Tamagotchi-Mechanik:** vorerst **nur herumlaufen**, keine Bedürfnisse.
  Später denkbar: wird unglücklich, Futter im Shop; im Kampf verletztes Pet
  heilt mit Futter oder braucht Medizin. (Skizze 24.09. „LP-Verlust bei
  Vernachlässigung“ damit vorerst nicht umgesetzt.)
- **Andere Spieler** dürfen interagieren: **Streicheln** (Marks Favorit);
  Hochheben per Drag and Drop und aus dem Bild werfen nur als verworfene/
  unsichere Alternative erwähnt — offen, ob zusätzlich.
- **Häufchen:** macht er auch bei den anderen auf den Bildschirm, und es
  **bleibt liegen, wenn er geht** (persistent, also serverseitig je Client/
  Spieler gespeichert). Wie es wieder weggeht: offen.
- **Animationen:** Idle, Laufen, Schlafen, Essen, Feuer-Rülpser, Freuen/
  Hüpfen, Hunger/traurig, Häufchen — alle gewünscht. Zusätzlich: **klettert
  am Rand von Popups hoch und stellt/legt sich oben drauf.**
- **Sprites:** später mehr Arten; **jeder Critter kann sein eigenes Sprite
  bekommen.**
- **Optik:** länglicher, wie ein **chinesischer Drache** (statt kompaktem
  Chibi-Mushu).
- **Design festgelegt (11.11.2026):** Design 2 (chinesischer Drache, gelbe
  Rückenzacken, Geweih-Hörner, Schnurrhaare, Flammenquaste), Körper etwas
  dünner, **Beine unverändert kurz**. Verworfen: Brik-Mushu-Vorlage
  („schräg“) und lange dünne Beine („schrecklich“). Generator + GIFs:
  `docs/assets/critter-pet/drache_final.py` (`python drache_final.py <ziel>`),
  `final_idle.gif`, `final_lauf.gif`.

## Gebaut 11.11.2026 (erste Ausbaustufe)

- SL: `CritterFenster` → „Pet auf den Tablets“ (aus / Kleiner Drache),
  gespeichert als `petArt` am Critter. API `docs/api/pets.md`.
- Server (`backend/app/pets/motor.py`) weiß, auf welchem Tablet das Pet ist;
  Tablet meldet „raus“ am Rand → 3–12 s Pause → nächstes eingeloggtes
  Party-Mitglied (bevorzugt ein anderes), Gegenseite rein. Nie bei der SL.
  Pet existiert nur, solange der Besitzer verbunden ist (Annahme: es ist sein
  Tier, ohne ihn geht es nicht auf Wanderschaft).
- Tablet: läuft unten über den Bildschirm, Pausen, bleibt 40–120 s, dann
  raus. Unter den Fenstern (verdeckt nie einen Dialog). Verbindet nur bei
  sichtbarem Tab.
- Streicheln (antippen): Freuden-Hüpfer + Herzen, nur auf diesem Tablet.
- Häufchen: höchstens eins pro Besuch (20 % je Pause), bleibt liegen
  (`PetHaeufchen`-Knoten je Bildschirm, max. 12, ältestes fällt weg).
  **Annahme:** Antippen wischt es weg — Mark hat die Frage nicht beantwortet.
- Animationen bisher: Idle, Laufen, Freuen. Sprites aus
  `docs/assets/critter-pet/sprites_exportieren.py` → `frontend/public/pets/drache/`.
- **Noch nicht gebaut:** Schlafen, Essen, Feuer-Rülpser, Traurig/Hunger,
  Popups hochklettern und drauflegen, Hochheben/Werfen, Bedürfnisse.
- **Nachbesserung nach Marks Tablet-Test (11.11.):** Pet zeigte ein Kästchen
  (globale Button-Optik) → jetzt `div`. Laufen zuckte und wirkte rückwärts →
  24 Frames, kleinere Welle, Welle läuft Kopf → Schwanz.
- **Zweite Nachbesserung (11.11.):** auch das wirkte „wie ein Tornado im
  eigenen Fenster“. **Regel (Mark):** die Figur bewegt sich in ihrem Rahmen
  nicht fort, nur der Rahmen wandert über den Schirm; die Figur macht dazu
  die Laufbewegung. Körperform steht still, nur Beine tapsen, leichtes Wippen.
  Mark: „jetzt schaut es wie gehen aus“. Danach 32 statt 16 Frames (35 ms,
  gleicher Takt), weil es noch zuckelig wirkte.
- **Klettern und Springen (11.11., gebaut):** Mark: „nicht nur unten am Rand
  rumlaufen, sondern auch wo rauf klettern oder springen“. Springt auf
  niedrige Popups, klettert an höheren seitlich hoch und steigt drauf,
  läuft oben herum, schläft dort einmal pro Besuch (Zzz), springt wieder
  runter. Klettert auch am Bildschirmrand hoch, hängt kurz, springt ab.
  Popup zu → fällt runter. Raus zum nächsten Tablet nur über den Boden.
  Dafür liegt die Pet-Ebene jetzt **über** den Fenstern (z-index 210), unter
  Ansagen/Verhandlungen/Bestätigungen. Logik: `frontend/src/pets/bewegung.ts`.
  Erledigt damit aus der Animationsliste: Schlafen, Popups hochklettern und
  drauflegen. Offen: Essen, Feuer-Rülpser, Traurig/Hunger.
- **Übergänge, mühsames Klettern, Wörter/Linien/Kästchen (11.11., gebaut):**
  Mark wollte eine Übergangs-Animation, anstrengenderes Klettern und dass er
  „auf Wörtern, Linien, Punkten, Kästchen usw.“ herumläuft. Er hüpft jetzt
  zwischen Textzeilen, Knöpfen, Feldern, Bildern, Linien, Punkte-Reihen,
  Kacheln/Karten und Popups; nur was wirklich sichtbar oben liegt, bei
  offenem Popup nur darin. Weggescrollt/verdeckt → er fällt. Übergänge:
  an die Wand drehen, über die Kante hochziehen, aus der Wand ausdrehen,
  Landung einfedern. Klettern: Klimmzüge mit Nachgreifen, Rast mit Wackeln
  und Schweißtropfen, manchmal abrutschen.
- **Feuerniesen, Brandflecken, Häufchen auf Flächen (11.11., gebaut):** Mark:
  „ab und zu Feuer niesen, dann Stellen verbrennen, über die man wischen muss,
  damit sie wieder sauber werden“. Anlauf, Hatschi, Feuerstoß; 1–2
  Brandflecken, die liegen bleiben wie Häufchen (auch nach dem Weiterziehen)
  und nur durch Reiben weggehen. Häufchen macht er jetzt auch oben auf Text
  und Kästchen — die Position ist eine Bildschirmstelle, beim Scrollen bleibt
  das Häufchen also am Bildschirm, nicht am Wort.
- **Nachschärfung 11.11.:** Feuerstoß etwa doppelt so lang, Brandfleck etwa
  doppelt so groß. Schlafen bis zu 5 Minuten (Mark: „man kann ihn ja
  aufwecken, wenn man ihn antippt“) — Antippen weckt ihn.
- **Packen und Werfen (11.11., gebaut):** Mark: „antippen und 3 Sekunden
  drauf bleiben, dann nehmen und verschieben, und idealerweise aus dem
  Bildschirm rauswerfen, damit er zu wem anderen geht“. Damit ist die
  offene Frage „Hochheben/Werfen zusätzlich zum Streicheln“ entschieden:
  ja, beides. Kurz antippen streichelt, 3 s halten packt ihn; loslassen
  lässt ihn mit Schwung fliegen; seitlich raus = er wandert zum nächsten
  Tablet.

## Häufchen am Element, Ruß am Display (11.11.2026, gebaut)

Mark: Häufchen sollen nicht an der Bildschirmposition kleben, sondern „am
HTML-Element hängen … und runterfallen, wenn man die Seite wechselt“;
Brandflecken „könnten ja am Display sein und sich deswegen nicht bewegen“
und sollen so aussehen.

- Häufchen scrollen/wandern mit ihrem Element; verschwindet es, fallen sie
  auf den Boden, und diese Lage wird gespeichert.
- Brandflecken bleiben fix am Bildschirm und sehen jetzt aus wie Ruß auf der
  Glasscheibe (Inhalt dahinter verschwommen, Glanz). Wegwischen wie bisher.
- Ersetzt die frühere Entscheidung „Spurenposition als Bildschirmanteil,
  wandert beim Scrollen nicht mit“ — für Häufchen.

## Burgermenü-Ausflug (11.11.2026, gebaut)

Mark: „es wäre genial, wenn er auf der linken Seite nicht am Bildschirmrand,
sondern am Burgermenü außen raufklettert, zu einem Menüpunkt, den aufklappen
kann, um sich dann darauf zu setzen oder zu legen, vielleicht um darauf zu
schlafen — oder später etwas zu fressen“.

- Nur ab Tablet-Breite (Symbolspalte sichtbar) und ohne offenes Popup; am
  Handy bleibt der linke Bildschirmrand.
- Das Herausziehen ist rein optisch (wie das erste Antippen eines
  Eintrags); der Bereich wird nicht gewechselt, das Antippen des Spielers
  funktioniert unverändert.
- Auf dem Eintrag schläft er meist (bis 5 min) oder sitzt; Antippen weckt
  ihn, dann springt er bald runter und der Eintrag klappt zu.
- **Idee für später:** auf einem bestimmten Menüpunkt fressen (z. B. Shop
  oder Inventar) — hängt am Futter-/Hunger-Thema, noch offen.

## Bärbel, die fliegende Bibel (11.11.2026, gebaut)

Idee von Marks Frau: ihr Charakter hat eine Bibel namens Bärbel, die mit ihr
spricht — zugleich Zauberbuch. Pixel-Buch mit „BÄRBEL“ auf dem Titel.

- **Datenmodell (mit Mark abgestimmt):** Bärbel ist ein **Gegenstand**, kein
  Critter. `petArt` gibt es jetzt auch am `Gegenstand` (SL: Item-Bearbeitung →
  „Pet auf den Tablets“). Besitzer = wer ihn per `BESITZT` hat; Ausrüsten
  nicht nötig („Bärbel lässt sich nicht einsperren“). Ausnahme: liegt sie
  (auch verschachtelt) in einer verschlossenen Kiste, „wurde sie gegen ihren
  Willen eingesperrt“ und fliegt nicht; weggeworfen ebenso nicht. Wechselt
  der Besitzer, fliegt sie beim neuen.
- **Wandern:** wie der Drache zu den eingeloggten Party-Mitgliedern, aber
  sie kommt **nie unten** von der Seite, sondern in irgendeiner Höhe oder
  von oben, und fliegt auch so raus (links/rechts/oben).
- **Aussehen:** drei Gestalten, zwischen denen sie sich ab und zu in einer
  violetten Zauberwolke verwandelt (Marks Wunsch „alle drei super“):
  1 klassisch (braunes Leder, Goldkreuz), 2 Grimoire (violett, Auge — blinzelt
  nur manchmal und schaut sich um), 3 rot mit Kulleraugen (blinzelt oft).
- **Bewegung** (`frontend/src/pets/flug.ts`, gleiche Schnittstelle
  `PetSteuerung` wie `PetBewegung`): zugeklappt langsam schweben, aufgeklappt
  wie ein Vogel flattern (Deckel = Flügel, Abschlag schnell), dazwischen
  auf-/zuklappen; landet zugeklappt auf Text/Kästchen und ruht, Fläche weg →
  flattert weg. Antippen = Freuen (Hüpfer, Herzen); 3 s halten = packen
  (flattert panisch), Wurf mit Luftwiderstand, fängt sich wieder oder fliegt
  raus.
- **Spur:** statt Häufchen verliert sie beim Flattern Seiten (`art: seite`),
  die zu Boden segeln und dort zerknittert liegen; antippen = aufheben.
- Sprites prozedural: `docs/assets/critter-pet/baerbel_design.py` (Figur),
  `baerbel_exportieren.py` → `frontend/public/pets/baerbel/`.

**Nachbesserung 11.11.:** Verwandlungswolke intensiver, länger (≈2,2 s) und wabernd, auf größerer Leinwand über dem Buch (Marks Wunsch nach dem ersten Test: „funktioniert mega cool“).

**Nachbesserung 11.11.:** Seiten bleiben öfter (70 % je überquerter Kante) auf Wörtern/Kästchen liegen und fallen erst beim Bereichswechsel zu Boden (Mark: „erst zu Boden fallen, wenn man die Seite wechselt“).

**Gebaut 11.11.:** Tentakelmonster will raus (Spalt mit glühenden Augen, Tentakel klatscht aufs Display → feuchter Schleimfleck `schleim`, wegwischen) und Blitz-Zauber (Buch leuchtet auf, Blitz schlägt im Bild ein → Brandfleck wie beim Drachen).

**Gebaut 11.11. (Interaktion):** Der Drache frisst Bärbels Seiten, wenn er daran vorbeikommt (läuft auch gezielt hin); Bärbels Tentakel zieht Häufchen ins Buch. Blitz variiert: Einzel-, Gabel-, Kettenblitz, trifft oft Wörter/Kästchen. Direkte Begegnung (11.11., gebaut): auf demselben Bildschirm niest der Drache Bärbel an (sie verwandelt sich), ihr Blitz verkohlt ihn, die Tentakel schleimt ihn voll.

**Gebaut 11.11. (Vorlesen):** Etwa alle 15 Minuten Anwesenheit (nicht Wanduhr, nicht im Kampf) schlägt sie sich groß auf und zeigt ein KI-Bibelzitat zur Lage (Ort, Anwesende, Events am Ort). Bleibt bis zum Antippen. Glitzerwolke nicht gebaut — die Tafel ist die lesbare Fläche.

**Nachbesserung 12.11. (Vorlesen):** Mark war mit Tafel daneben und frechen Sprüchen unzufrieden: „das Buch so groß wird und sich aufschlägt, dass man den Text im Buch lesen kann“, „höchstens umformulierte Bibelverse, gerne auch aus dem Alten Testament“, Schrift „elegant oder alt“. Jetzt: Bärbel fliegt zur Mitte, wächst als großes Buch in ihrer aktuellen Gestalt (Farben, Kreuz/Auge/Kulleraugen auf dem Deckel), der Deckel schwingt auf, der Vers steht auf den Seiten und erscheint Wort für Wort wie Tinte (Fraktur-Initiale und -Stelle, Fließtext in alter Druckschrift). Kein Kommentar mehr, nur Stelle + Vers. Antippen klappt zu und lässt sie wieder klein weiterfliegen. Ersetzt die Tafel aus dem 11.11.

**Nachbesserung 12.11. (Vorlesen):** Abstand jetzt zufällig 15–45 Minuten (Mark nach dem Test). Mark hatte zweimal dasselbe Zitat: bei gleicher Lage wählte die KI denselben Vers (bzw. der Notfall-Vers war je Kampagne fest). Jetzt merkt sie sich die letzten Stellen, die KI bekommt ein zufälliges Leitbild und darf sie nicht wiederholen; eine Wiederholung wird durch einen anderen festen Vers ersetzt.

**Noch offen (Ideen von Mark):** weitere Monster (Klauen), Feuerbälle. Fledermäuse: gebaut 18.11., siehe Abschnitt „Bärbel niest Fledermäuse aus“.

## Wolkenlauf des Drachen (12.11.2026, gebaut)

Mark: „am Tablet ist das Charakterblatt vor allem in der oberen Hälfte, der Babydrache kommt dort nicht wirklich hin … chinesische Drachen erzeugen kleine Wolken unter ihren Klauen und laufen darüber durch die Luft — damit er auf relativ leeren Bildschirmen rauf zu Sachen kommt.“

- Er ruft eine Glückswolke unter die Füße (kurz geduckt), läuft dann im Bogen durch die Luft zu einer Fläche, die er per Sprung nicht erreicht — bevorzugt oben am Bildschirm. Ist es zu steil, holt er seitlich aus und dreht im Bogen zurück.
- Unter jedem Schritt puffen abwechselnd unter Vorder- und Hinterpfote Wölkchen auf, die hinter ihm zerfasern. Die Nase folgt der Steigung.
- Verschwindet das Ziel (Popup zu, weggescrollt), fällt er runter. Packen geht auch in der Luft.
- **Annahme:** Häufigkeit etwa 30 % der Entscheidungen am Boden, 22 % auf Flächen; Tempo 85 px/s.

## Ruß abschütteln (12.11.2026, gebaut)

Mark: „Wenn der Drache verkohlt wurde, färbt er sich danach einfach wieder normal … cooler, wenn er sich irgendwann schütteln würde und der Ruß abfallen und zu Boden fallen würde.“

- Nach Bärbels Blitz zuckt er wie bisher kurz, bleibt danach aber schwarz verrußt und macht normal weiter.
- Nach 7–20 Sekunden (spätestens bevor er zum nächsten Tablet geht) bleibt er stehen und schüttelt sich wie ein nasser Hund; dabei verschwindet der Ruß, Flocken (ab und zu ein Glutfunke) fliegen ab und rieseln zum unteren Bildschirmrand.
- **Annahme:** Die Flocken bleiben etwa 5 Sekunden liegen und verblassen dann — keine dauerhafte Spur zum Wegwischen.

## Eisdrache und Blitzdrache (12.11.2026, gebaut)

Mark: „Ich habe einen Critter gemacht, der Wolke Salamander heißt, der ist in Wahrheit das Gleiche wie unser Babydrache, nur dass er silberblau ist“ — er spuckt Eis oder Blitze statt Feuer. Aus dem Entwurf (zwei Farbvarianten × zwei Atem): „Warum machst du nicht beide? Der blauere ist Eis und der silberne Blitz.“

- Zwei neue Pet-Arten am Critter: **Kleiner Eisdrache** (blauer Körper, silberner Bauch und Mähne) und **Kleiner Blitzdrache** (silberner Körper, blaue Mähne). Gleiche Figur, gleiche Animationen und gleiches Verhalten wie der Drache (Wolkenlauf, Ruß abschütteln, Fressen, Bärbel zielt auf ihn).
- Eisdrache niest einen Frostkegel mit Eiskristallen, der in Schneeflocken zerfällt; danach liegt **Raureif** auf dem Display (Eisblumen, dahinter milchig) — wegwischen wie Ruß.
- Blitzdrache niest eine zackige, verästelte Entladung; sie hinterlässt Brandflecken wie das Feuer.
- Treffen: Blitz verrußt einen anderen Drachen (wie Bärbels Blitz, dann Abschütteln), Eis lässt ihn kurz bereift bibbern; Bärbel erschrickt und verwandelt sich bei Feuer, Eis und Blitz.
- **Annahme:** Namen „Kleiner Eisdrache“/„Kleiner Blitzdrache“; Raureif bleibt liegen, bis er weggewischt wird (taut nicht von selbst); Eis-Bibbern dauert 3,5 s.

## Abdrehen und Kampfpause (11.11.2026, gebaut)

Mark: Schalter zum Abdrehen in den Kampagnenoptionen („Desktop-Pets aktiv“, Default an) und im Kampf grundsätzlich keine Pets — sie verschwinden beim Kampfbeginn und kommen nach dem Kampf beim Besitzer wieder. Spuren bleiben gespeichert. Mark hat nachgezogen: im Kampf und bei abgedrehten Pets werden sie ausgeblendet und danach wieder eingeblendet, nicht gelöscht.

## Nebenbei gefunden 11.11.2026

Der Spieler sah seinen Critter gar nicht im Begleiter-Bereich (der las nur
Sprite/Geist-Begleiter). Behoben: eigene Critter erscheinen dort als Kachel
mit lesbarem Charakterblatt (`GET …/critter/meine`, CLAUDE.md).
12.11.2026: nur noch Critter mit `BEGLEITET`-Kante — Ki-Tama-Beschwörungen
erscheinen dort nicht (Mark), sie stehen im Kampf unter „Deine Beschwörungen“.

## Wachsen und neue Fähigkeiten (Idee 12.11.2026, offen)

Mark: „Ich würde sie wirklich gerne mehr zu Tamagotchi-artigen Pets machen. Ich würde sie gerne wachsen lassen, mit jeder Session könnten sie ein wenig größer und eleganter werden, also zumindest die Drachen. Bärbel könnte mehr Fähigkeiten bekommen.“ — vorerst nur notiert, Besprechung später.

Skizze (Neko, noch nichts entschieden):
- **Drachen wachsen in Stufen.** Die Figur ist prozedural (`drache_final.py`), Wachstum ist ein Parameter-Satz je Stufe: Körperlänge (Wirbelzahl), Dicke, Kopf-zu-Körper-Verhältnis (Baby groß, später kleiner), Hornlänge/-verzweigung, Mähne, Schnurrhaare, Beinlänge, Schwanzquaste. Alle Animationen und Atem-Sheets je Stufe neu exportieren — billig, gilt automatisch für Drache, Eis- und Blitzdrache.
- Realistisch klar unterscheidbar: **5–6 Stufen** (Schlüpfling → Baby (heute) → Jungtier → Halbstark → Jungdrache → ausgewachsen/ehrwürdig). Mehr Stufen gehen technisch, die Sprünge werden aber unsichtbar klein; Alternative: stufenloser Wachstumswert, gerendert in ~6–8 Zwischenstufen.
- **Größengrenze:** heute 84×44 Sprite-Pixel, am Tablet ×2. Der Bildschirm (Handy!) begrenzt; „größer“ eher ~1,6–2× Baby-Länge, Rest über Eleganz (schlanker, länger, wallende Mähne) statt Masse.
- **Technik:** Maße stehen heute fest in `SPRITE` (`PetOverlay.tsx`); Wachstum braucht `sprite.json` je Stufe (Maul, Füße, Breite) und Masse je Art+Stufe. Klettern/Wolkenlauf/Treffer rechnen schon aus `Masse`.
- **Bärbel:** statt Wachstum neue Fähigkeiten freischalten (sie hat schon: 3 Gestalten/Verwandlung, Blitz, Tentakelmonster, Seiten verlieren, Vorlesen). Jede neue Fähigkeit ist eigenes Design + Code — teurer als eine Drachenstufe, etwa eine je Ausbaurunde.

Offene Achsen:
- **Auslöser fürs Wachsen:** automatisch je gespielter Sitzung (Sitzungen gibt es schon, siehe Ereignisprotokoll/Achievements), SL-Knopf „wachsen lassen“, oder Tamagotchi-Pflege (gestreichelt/gefüttert) — oder Mischung (Pflege nötig, sonst kein Wachstum).
- **Datenmodell:** Stufe/Wachstumswert am Critter-Knoten (`petStufe`?) — je Critter eigenständig. Kann die SL zurücksetzen/korrigieren?
- **Wie viele Stufen** und Endstufe: hört es auf („wer soweit kommt…“) oder gibt es eine Endform?
- **Hat Wachstum Spielwirkung** am Critter (Werte) oder ist es reiner Flavor?
- **Bärbel:** welche Fähigkeiten in welcher Reihenfolge, auch freigeschaltet je Sitzung?

### Marks Antworten 12.11.2026

- **Stufen:** 5–6 deutlich sichtbare Stufen, dazwischen jeweils eine Zwischenstufe, in der kaum etwas passiert → etwa **12 Schritte**, ausgewachsen nach **10–12 Sitzungen**.
- **Auslöser (Mischung):** Er wächst nur, wenn er in der Sitzung **gefüttert und gestreichelt** wurde. Zusätzlich die Idee, das Wachstum an die **Erfahrungspunkte des Critters** zu koppeln, an dem das Pet hängt.
- **Ende/Neustart:** Ausgewachsen hört es optisch auf. Wird die Pet-Art an einen **neuen Critter** gehängt, fängt sie dort wieder klein an → Stufe gehört zum Critter, nicht zur Pet-Art.
- **Spielwirkung andersherum:** Das Wachstum gibt keine Werte. Umgekehrt soll der **Critter mit der Gruppe EP bekommen** (er hängt an einem Spieler): bekommt die Kampagne EP, bekommt er auch welche. Mark will das noch testen.
  - Code-Stand 12.11. (Neko): `kampagnenEP` fließt in `bogen_uebersicht` bei **jeder** Person ein, auch beim Critter (keine Ausnahme für `istCritter`) — er sollte die Gruppen-EP also schon haben. Am Spieltisch gegenprüfen.
  - Falle fürs Koppeln: `kampagnenEP` ist ein Kampagnen-Gesamtwert. Ein neu angelegter Critter „hat“ sofort alle bisherigen Gruppen-EP — fürs Wachstum zählen also nur EP **seit der Bindung** (Startwert beim Setzen der Pet-Art merken), sonst wäre er sofort ausgewachsen.
- **Bärbel — Fähigkeiten:** so viele, wie uns einfallen. Ideen: weitere Monster (Fledermäuse; schon notiert: Klauen), **andere Kreaturen ausspucken**, **Eis- und Feuerzauber** lernen.
- **Bärbel — Vorlesen (wichtig!):** Für die **Bibelzitate kehrt Bärbel immer zu ihrem Besitzer zurück** und liest dort vor (heute liest sie auf dem Tablet, auf dem sie gerade ist — `motor.py::_petmotor_lesen_takt` sendet an `pet.wirt`). Den **anderen** zeigt sie später andere Texte: **Kochrezepte**, **DIY-Anleitungen für irgendeinen Blödsinn**, **Wettervorhersage für irgendein Land an irgendeinem Tag**.

Noch offen:
- Wie genau Pflege und EP zusammenspielen: Pflege als Bedingung und EP als Maß (z. B. Stufe nur bei Pflege, Tempo nach EP)? Oder eins von beiden?
- **Füttern gibt es noch nicht** (heute frisst der Drache nur Bärbels Seiten): Womit wird gefüttert (Tierfutter-Gegenstand aus dem Shop, Futter-Knopf, Antippen mit Futter)? Wer darf füttern/streicheln, damit es zählt (nur Besitzer oder jeder)?
- Was zählt als „in der Sitzung“ (laufende Sitzung aus dem Ereignisprotokoll)?
- Reihenfolge der Bärbel-Fähigkeiten, und ob sie auch je Sitzung freigeschaltet werden.

### Marks Entscheidung 12.11.2026 (Abend): EP = Wachstum, Futter = Heilung

- **Wachstum hängt an den EP** des Critters (nur EP seit der Bindung, siehe Falle oben). Pflege ist damit keine Wachstumsbedingung mehr (Neko-Lesart, von Mark noch zu bestätigen).
- **Füttern heilt:** Der Critter kämpft mit, Futter gibt ihm Lebenspunkte zurück.
- **Futter ist ein Verbrauchsgegenstand**, den Mark selbst anlegt (Typ `Verbrauchsgegenstand`, stapelbar, 1 Stück je Mahlzeit).
- **Bedienidee Mark:** Den Critter im Inventar in die Nähe des Futters heben, dann fängt er an zu fressen. Neko: passt zur vorhandenen Mechanik — das Pet lässt sich schon packen (3 s halten) und werfen, und der Drache hat einen Fressen-Zustand (Bärbels Seiten). Ablegen über der Futter-Kachel = fressen. Zusätzlich Rückweg nötig, wenn das Pet gerade bei einem anderen Spieler ist: z. B. Knopf „Füttern“ am Futter ruft es heim, es läuft hin und frisst.

Nachschärfung Mark (gleicher Abend):
- **Futternapf statt Heimruf:** „Füttern“ am Futter legt einen **Napf** auf den Bildschirm, der dort liegen bleibt (wie Häufchen/Seiten), bis der Drache vorbeikommt und ihn leer frisst. Das Pet wird nicht herbeigerufen.
- **Heilung nur Schlagschaden.** Schwerer/aggravierter Schaden heilt der Critter wie die Spieler über die Rast. Code-Stand: `personen_rasten` nimmt per `_mit_gebundenen_crittern` alle über `BEGLEITET` an den Besitzer gebundenen Critter automatisch mit (seit 30.10. für Ki-Tama-Pets).
- **Wachstum: alle 5 EP ein Schritt** (vorläufig — Mark kann noch nicht einschätzen, ob das viel ist; als Kampagnen-Einstellung verstellbar machen). Live-Stand 12.11.: `kampagnenEP` = 0, keine Sitzungen protokolliert — kein Erfahrungswert. 12 Schritte × 5 = 60 EP.
- **Füttern und Streicheln darf jeder am Tisch.**
- **Zutraulichkeits-Meter (Idee):** Wert je Spieler und Critter, Streicheln +1, Füttern +5. Wirkung noch offen.

Noch offen:
- ~~Wie viele Schlagschaden-Kästchen heilt ein Futter?~~ Entschieden 12.11.: **3 Schlagschaden** je Futter.
- ~~Zutraulichkeit: Datenmodell, Spam-Schutz~~ Entschieden 12.11.: Kante Spieler-PC → Critter mit `wert` (je Spieler und Critter eigener Wert); Streicheln zählt höchstens +1 alle 5 Minuten je Spieler, Füttern (+5) zählt immer.
- Zutraulichkeit — Wirkung (später): Ideen Neko: wandert öfter zu Lieblingen, faucht/niest bei Fremden, rollt sich bei Lieblingen zum Schlafen ein. Idee Mark: ab hoher Zuneigung findet das Pet Dinge und bringt Geschenke. Der Wert muss **nicht sichtbar** sein.

## Noch offen

- Wachsen/Fähigkeiten freischalten — siehe Abschnitt oben (Antworten 12.11., Rest offen).
- Bärbel liest Bibelzitate nur beim Besitzer — **gebaut 12.11.** (fliegt dafür heim, siehe CLAUDE.md). Anderen Rezepte/DIY/Wetter: noch nicht gebaut.

### Weitere Ideen Mark 12.11.2026 (Abend)

- **Bärbel als Critter?** Bärbel ist ein Gegenstand und bekommt keine EP. Mark fragt seine Spieler und bereitet einen Bärbel-Critter vor — wird spontan entschieden.
  - **19.11.2026 gebaut:** Mark konnte Bärbel am Critter nicht auswählen. Jetzt steht „Bärbel (fliegendes Buch)“ in der Pet-Auswahl am Critter UND am Gegenstand. Am Critter ist der Besitzer der begleitete Spielercharakter; sie wächst dort nicht (keine Bärbel-Stufen), verhält sich sonst gleich. Ob die Gegenstands-Bärbel danach abgeschaltet wird, entscheidet Mark (sonst fliegen zwei Bärbels).
- **Nachrichten an Vertraute:** Hat ein anderer Spieler als der Besitzer **50 Zutraulichkeit** zu Bärbel, bekommt er manchmal auch Nachrichten von ihr (eher keine Bibelverse; was genau, später).
- **Drachen lernen mit dem Wachstum** (Fähigkeiten statt alles von Anfang an):
  - **Phase 1 — Ei:** schlüpft nach **5–10 Mal Antippen**.
  - **Phase 2 — Baby:** läuft nur unten herum, will Futter, macht Häufchen.
  - **Nach 3 EP:** wird zum heutigen Drachen — kann klettern, niesen, evtl. hüpfen.
  - **Später:** Fliegen/Wolkenlauf und das Öffnen des Burgermenüs. Weitere Fähigkeiten folgen, wenn sie uns einfallen.
  - Offen: welche Fähigkeit bei welcher Stufe/EP-Schwelle; zählt jedes Antippen (auch Fremde) fürs Schlüpfen; Ei-/Baby-Sprites neu zeichnen.

## Gebaut 12.11.2026: Ei, Schlüpfen, Baby

Entwurf von Mark abgenommen („Perfekt!!!“). Technik siehe CLAUDE.md.
- Neuer Drache an einem Critter = **Ei** (Schuppenmuster in der Drachenfarbe). Liegt beim Besitzer unten, wandert nicht, wackelt ab und zu. **Jeder** darf tippen; nötig sind zufällig **5–10 Tipps**, jeder Tipp lässt es hopsen, Risse wachsen (0–4).
- **Schlüpfen:** Kappe hüpft hoch, dreht sich, landet als **Hütchen** auf dem Kopf; das Baby trägt es, bis es zum ersten Mal frisst oder schläft (Annahme Neko).
- **Baby:** halb so lang, großer Kopf, Kulleraugen, Hornstummel. Läuft nur unten, frisst Seiten, macht Häufchen, schläft auch am Boden. Kein Klettern, Niesen, Hüpfen, Wolkenlauf, Burgermenü.
- **Wachstum:** EP des Critters ab dem Schlüpfen. Ab **3 EP** der heutige Drache (klettern, niesen, hüpfen); **Burgermenü ab 8 EP, Wolkenlauf ab 13 EP** (Mark, 12.11.).
- Bestandsdrachen (vor dem 12.11. gesetzt) bleiben groß und können alles. Ei neu starten: Pet-Art am Critter abwählen und neu wählen.
- ~~Noch nicht gebaut: weitere sichtbare Wachstumsstufen (5–6 Stufen, alle 5 EP)~~ — gebaut 13.11.2026, siehe unten. Offen: SL-Korrektur der Stufe.

## Gebaut 12.11.2026: Futternapf, Heilung, Zutraulichkeit

- **Tierfutter:** Verbrauchsgegenstand, den die SL im Bearbeiten-Formular als **„Tierfutter“** ankreuzt (Flag `istTierfutter`, Annahme Neko — Mark legt das Futter selbst an).
- **Füttern:** Knopf „Füttern“ im Inventar (nur Spieler, eigenes Futter, 1 Stück). Dafür steht ein **Napf** unten auf dem eigenen Bildschirm, bis ein Drache vorbeikommt — er riecht ihn über den ganzen Schirm und läuft fast immer hin. Antippen räumt ihn nicht weg. Auch das Baby frisst.
- **Leer gefressen:** Critter heilt **3 Schlagschaden**; der Fütternde bekommt **+5 Zutraulichkeit**.
- **Streicheln:** +1 Zutraulichkeit, höchstens alle 5 Minuten je Spieler (auch bei Bärbel). Der Wert ist unsichtbar; Wirkung (Geschenke, Bärbel-Nachrichten ab 50, …) noch offen.

- Häufchen entfernen: wegklicken/wischen, nach Zeit, oder nur durch den Besitzer?
- ~~Drag and Drop/Werfen zusätzlich zum Streicheln: ja oder nein?~~ Entschieden 11.11.: ja (3 s halten, siehe oben).
- ~~Woher das Sprite eines Critters kommt~~ — feste Arten im Code, SL wählt
  aus der Liste (Critter: Tiere, Gegenstand: Bärbel).

## Entwurf 13.11.2026: Stufen 3–6 und Einkringeln (abgenommen und gebaut, siehe nächster Abschnitt)

Mark: „entwirf mir die restlichen Altersstufen … sie sollten immer größer, eleganter und wie chinesische Drachen aussehen, ich hätte dann auch gerne, dass sie sich zum Schlafen einkringeln können.“

- Generator: `docs/assets/critter-pet/drache_stufen.py` (`python drache_stufen.py <ziel>` malt die Vorschau-Tafeln), Tafel: `docs/assets/critter-pet/stufen_entwurf.png`. Eine Figur, je Stufe ein Parameter-Satz (`STUFEN`) — gilt für Drache, Eis- und Blitzdrache.
- **Stufen (Arbeitsnamen):** 1 Schlüpfling und 2 heutiger Drache unverändert; neu 3 Halbstarker, 4 Jungdrache, 5 Drache, 6 Ehrwürdiger Drache. Sprite-Breite 84 → 102 → 116 → 132 → 149 px (inkl. Schnurrhaare und Schwanzflamme), Höhe 44 → 42 → 48 → 52 → 60.
- **Was wächst:** Körper länger und im Verhältnis schlanker, Körperbögen höher, Schwanz steigt nach hinten an, Hals länger mit S-Schwung, Geweih länger und verzweigter (1 → 3 Enden), Kopfmähne lang und wallend, Schnurrhaare im S-Bogen, Schwanzflamme mehrzüngig. Ab Stufe 4: Bauchplatten, Flammen an den Fersen, Flammenbraue, Pfoten mit Schenkel. Ab Stufe 5: Fangzahn, feinerer Schwanz. Beine bleiben kurz (Marks Grenze vom 11.11.).
- **Einkringeln:** gestapelte Spirale wie ein aufgerolltes Tau — Brust außen unten, Schwanz innen oben, die Schwanzflamme steht in der Mitte hoch wie eine Kerze, Kopf liegt vorn am Boden, Schnurrhaare hängen. Für alle sechs Stufen entworfen (Schlüpfling = kleiner Kringel). Übergang: legt sich hin, rollt sich vom Schwanz her ein; schlafend atmet er.
- **Offen (Mark):** Aussehen abnehmen; Größe am Handy (Stufe 6 = 149 px × 1,5 ≈ 224 px Breite); EP-Schwellen je Stufe; ob die 12 Schritte echte Zwischenformen bekommen (Parameter lassen sich zwischen zwei Stufen überblenden); ob jede Stufe eine neue Fähigkeit bringt.

## Gebaut 13.11.2026: große Stufen und Schlafkringel

Mark zum Entwurf: „die sind perfekt! bitte bau das ein!“

- **Stufen:** nach Schlüpfling und jungem Drachen kommen Halbstarker, Jungdrache, Drache und Ehrwürdiger Drache (`halbstark`, `jungdrache`, `gross`, `ehrwuerdig`) — für Drache, Eis- und Blitzdrache. Sprite-Breite 100 / 116 / 132 / 148 px (junger Drache 84).
- **Wann:** Wachstum in Schritten, ein Schritt kostet so viele EP des Critters, wie in den Kampagnen-Einstellungen unter „Drachen-Wachstum: EP je Schritt“ steht (Mark, 12.11.: 5, vorläufig). **Annahme Neko:** alle 3 Schritte eine neue Gestalt → 15, 30, 45, 60 EP seit dem Schlüpfen; nach 12 Schritten ausgewachsen. Die Zwischenschritte haben keine eigene Gestalt.
- **Fähigkeiten:** unverändert (klettern/niesen/hüpfen ab 3 EP, Burgermenü ab 8, Wolkenlauf ab 13) — die großen Stufen können alles. **Annahme Neko:** der Atem (Feuer/Eis/Blitz) wird mit jeder Stufe etwas größer (×1,15 bis ×1,6).
- **Einkringeln:** jeder Drache — auch Schlüpfling, junger Drache und Bestandsdrachen — legt sich zum Schlafen hin, rollt sich vom Schwanz her ein und schläft als Kringel; Zzz steigt erst dann auf. Antippen oder Ausschlafen rollt ihn wieder aus (dieselbe Bewegung rückwärts, etwas schneller), geweckt freut er sich.
- Bestandsdrachen ohne Stufe bleiben der junge Drache und wachsen nicht (wie bisher; Ei neu starten = Pet-Art ab- und wieder anwählen).
- Technik: CLAUDE.md, Abschnitt 13.11.2026.
- **Noch offen:** neue Fähigkeit je großer Stufe (Ideen siehe „Fähigkeiten der großen Drachen“ unten).
- **SL-Knöpfe (13.11.2026, gebaut):** Mark: „ja ein SL-Knopf wäre auch gut! vor allem auch um alles sauber zu machen!“
  - **Wachstum einstellen:** im Critter-Fenster unter „Pet auf den Tablets“ gibt es bei Drachen die Auswahl „Wachstum“ (Ei, Schlüpfling, alle 13 Schritte). Die Wahl setzt ihn auf diese Stufe; danach wächst er mit seinen EP normal weiter. Kein neues Datenfeld — es wird nur der Startwert der EP-Zählung verschoben. Ein Bestandsdrache (steht als „Junger Drache (wächst nicht)“ da) wächst ab der ersten Wahl mit.
  - **Alles sauber machen:** Knopf in den Kampagnen-Einstellungen mit Rückfrage. Räumt Häufchen, Brandflecken, Raureif, Schleim und Bärbels Seiten von allen Spieler-Tablets. **Annahme Neko:** Futternäpfe bleiben stehen (sie haben ein Stück Futter gekostet); „sauber machen“ meint die Spuren, nicht ein Zurücksetzen der Drachen.
- **Zwischenformen (13.11.2026, gebaut):** Mark: „ja das klingt gut, bitte mach Zwischenformen.“ Jeder der 12 Wachstumsschritte hat jetzt eine eigene Form: zwischen zwei Gestalten liegen zwei Zwischenformen, in denen er nur ein Stück länger und eleganter wird (Länge, Bögen, Hals, Geweih, Mähne, Schnurrhaare, Schwanzflamme je ein Drittel des Wegs). Neue Merkmale (Bauchplatten, Fersenflammen, Geweih-Enden, Fangzahn) kommen erst mit der nächsten Gestalt. Mit 5 EP je Schritt ändert sich also alle 5 EP etwas. Beim Wachsen freut er sich an Ort und Stelle. Tafel aller 13 Schritte: `docs/assets/critter-pet/schritte_tafel.png`.

## Fähigkeiten der großen Drachen (Ideen 13.11.2026, offen)

Mark: „vielleicht könnte er auch Feuerbälle schießen, die weiter fliegen“, „was ist denn eine Drachenperle? das klingt gut!“, „hast du noch Ideen für Fähigkeiten?“ — noch nichts gebaut, Zuordnung zu den Stufen offen.

- **Feuerball — gebaut 13.11.2026, siehe Abschnitt „Feuerball“ unten.** Ursprüngliche Idee Mark: fliegt weit über den Bildschirm statt nur vor dem Maul zu lodern; Eisdrache Eisball, Blitzdrache Kugelblitz. Einschlag = größerer Fleck. Offen: prallt er an Wörtern/Kästchen ab oder fliegt er bis zum Rand; fliegt er manchmal zum Nachbar-Tablet weiter.
- **Drachenperle — gebaut 13.11.2026, siehe Abschnitt „Drachenperle“ unten.** Ursprünglicher Vorschlag: die leuchtende Perle der chinesischen Drachen (Weisheit, Glück, Donner/Mond), der sie nachjagen. Für den Ehrwürdigen: schwebt vor ihm, er jagt und jongliert sie, Spieler können sie wegschnippen, im Schlaf liegt sie leuchtend in der Mitte des Kringels. Keine Spielwerte (Wachstum gibt keine Werte).
- **Weitere Vorschläge Neko:** Regen machen (chinesische Drachen bringen Regen: Wolke wäscht Flecken vom Bildschirm; Eisdrache Schnee, Blitzdrache Gewitter); frei durch die Luft schlängeln statt nur Wolkenlauf; Brüllen (Schirm wackelt, Häufchen fliegen weg, andere Pets erschrecken); um ein Popup oder Portrait wickeln; Schatz horten (sammelt Seiten und Krümel auf einen Haufen); Geschenke bringen bei hoher Zutraulichkeit (Marks Idee vom 12.11.); kleinere Pets reiten auf ihm.
- **Vorschlag Reihenfolge (Neko, nicht entschieden):** Halbstarker Feuerball → Jungdrache Regen → Drache frei fliegen und Brüllen → Ehrwürdiger Drachenperle.

## Drachenperle (13.11.2026, gebaut)

Mark: „Mach so eine Drachenperle! Aber vielleicht, dass sie nicht immer da ist … Vielleicht kann man die Drachenperle auch aus dem Bildschirm werfen, weil sie ein Objekt ist, und dann geht er sie auf anderen Tablets suchen und bringt sie zurück … (ohne dass er weiß, auf welchem es liegt) … so als Minispiel.“

- **Wer:** nur der Ehrwürdige Drache (alle drei Farben, dieselbe Perle).
- **Nicht immer da:** frühestens 15–45 s nach der Ankunft auf einem Tablet holt er sie manchmal hervor (leuchtet vor seinem Maul auf). Sie bleibt 1–2,5 Minuten, dann verschluckt er sie wieder und wartet 3–8 Minuten. Bevor er weiterzieht, steckt er sie ein.
- **Ein Ding auf dem Schirm:** sie liegt leuchtend am Boden. Antippen lässt sie hüpfen, packen und loslassen wirft sie; sie prallt am Rand ab und rollt aus. Der Drache stupst sie selbst ab und zu mit der Nase an.
- **Hinauswerfen:** mit Schwung über den linken oder rechten Rand — sie landet auf einem zufälligen anderen Tablet der Party (fliegt dort herein). Ist sonst niemand eingeloggt, kommt sie zurück.
- **Suchen:** der Drache erschrickt („!“), rennt hinaus und sucht ein Tablet nach dem anderen ab, keins doppelt. Wo sie nicht liegt, läuft er in die Mitte, schaut sich um („?“) und rennt weiter. Der Server verrät dem Tablet nie, wo die Perle liegt, und wählt das nächste Tablet zufällig.
- **Finden und Zurückbringen:** „!“, er hebt sie auf, trägt sie vor dem Maul und bringt sie dem, der sie hinausgeworfen hat (ist der weg: dem Besitzer). Dort legt er sie stolz ab.
- **Weiterwerfen:** wer die Perle bei sich liegen hat, darf sie auch weiterwerfen — der Drache muss weitersuchen; zurückgebracht wird sie trotzdem dem ersten Werfer.
- **Tablet aus:** geht das Tablet aus, auf dem die Perle liegt, kullert sie auf ein anderes Tablet der Party weiter — sonst fände er sie nie. Gibt es den Drachen nicht mehr (oder stellt die SL ihn jünger), verschwindet die Perle.
- **Annahmen Neko:** alle Zeiten oben; beim Suchen und Tragen läuft er 2,4-mal so schnell; die Perle ist für alle drei Drachenfarben gleich; „Alles sauber machen“ räumt sie mit weg; keine Spielwerte.
- **Perle im Schlafkringel (gebaut 13.11.2026, Mark: „die Perle mit Schlafkringel“):** liegt die Perle draußen, legt er sich ab und zu zu ihr und kringelt sich um sie — sie rollt beim Einkringeln in die Mulde in der Mitte und leuchtet dort, bis er aufwacht; dann kullert sie wieder heraus. Im Kringel kann man sie nicht greifen, Antippen weckt den Drachen.
- **Noch offen:** Belohnung fürs Zurückbringen (Herzen, Zutraulichkeit); Perle dem schlafenden Drachen stehlen.

## Feuerball (13.11.2026, gebaut)

Mark: „vielleicht könnte er auch Feuerbälle schießen, die weiter fliegen“, dann „ein Go für alles“.

- **Wer:** ab dem Halbstarken (Schritt 3), alle drei Farben: Feuerball, Eisball (Eisdrache), Kugelblitz (Blitzdrache). Bestandsdrachen ohne Wachstum nicht.
- **Wann:** etwa jedes zweite Niesen wird ein Ball statt des Feuerstoßes; er dreht sich dafür meist dorthin, wo mehr Platz ist.
- **Flug:** im flachen Bogen weit über den Schirm, schlägt unten ein und hinterlässt einen großen Fleck (`krater`, beim Eisdrachen `eiskrater`) — Wegwischen wie Brandfleck und Raureif, braucht nur mehr Reiben. Der Einschlag trifft andere Pets wie der Atem.
- **Aufs Nachbar-Tablet:** fliegt er über den Seitenrand hinaus, kommt er auf einem zufälligen anderen Tablet der Party von der Gegenseite herein und schlägt dort ein. Ist sonst niemand da, verpufft er. Höchstens alle 4 s je Drache.
- **Annahmen Neko:** jedes zweite Niesen; Flugweite und -höhe; prallt nicht an Wörtern oder Kästchen ab; der Ball wächst mit dem Atem der Stufe.

## KI-Begleiter als Pet (13.11.2026, gebaut)

Mark zu den Entwürfen: „Ich mag A Datenwolke und B Lichtkern! Es kann gerne zwischen den 2 Gestalten wechseln und auch verschiedene Farben und Gestalten annehmen. Bitte bau die KI … ein Go für alles.“

- **Pet-Art `ki`**, wählbar am Critter („KI (Datenwolke / Lichtkern)“). Keine Sprites: ein Schwarm aus Teilchen auf einer kleinen Leinwand (`frontend/src/pets/ki.ts`, `KiFigur.tsx`), das Leuchten macht ein CSS-Filter in ihrer Farbe.
- **Zwei Grundformen:** Datenwolke (Schwarm mit dichtem Kern und Augen, später Datennetz, Nullen und Einsen, Umlaufbahn) und Lichtkern (pulsierende Kugel mit Strahlen, später Ringe und Trabanten). Sie wechselt von selbst; die Teilchen fließen von einem Platz zum anderen.
- **Gestalten:** Katze, Totenkopf, Herz, Schlüssel, Pfeil, Warnung, Stern, Blitz, Smiley — aus der Wolke als gefüllte Punktform, aus dem Lichtkern als Umriss aus Licht. Jede Gestalt bringt eine Farbe mit.
- **Farben:** Cyan (Start), Magenta, Grün, Bernstein, Violett, Rot; sie wechselt von selbst und behält die Farbe der letzten Gestalt.
- **Wachstum:** wie die Drachen 12 Schritte mit den EP ihres Critters (`petWachstumEp`), ohne Ei: Funke → Keim → Geist → Wesen → Entität, alle 3 Schritte eine neue Gestalt, dazwischen wird sie mit jedem Schritt größer und dichter. Die SL stellt die Stufe im Critter-Fenster ein.
- **Was sie kann, wächst mit:** Funke schwebt und pulsiert · Keim wechselt Wolke/Lichtkern, blinzelt, wird beim Antippen ein Herz, schläft (Standby) · Geist nimmt Farben und Gestalten an · Wesen liest Daten (schwebt über eine Zeile, ein Lichtstrich fährt darüber, Pixel strömen in sie hinein) · Entität hat Umlaufbahn und drei Ringe und zeigt Gestalten öfter.
- **Anfassen:** Antippen = sie freut sich. Ziehen = sie kommt mit; mit Schwung über den Seitenrand geworfen fliegt sie zum nächsten Tablet. Feuer, Eis und Blitz der anderen Pets geben ihr eine Bildstörung.
- **Hinterlässt nichts** — keine Spuren, also nichts zum Saubermachen.
- **Annahmen Neko:** hängt an einem Critter und wächst mit dessen EP (wie der Drache); Stufennamen; Startfarbe Cyan; welche Fähigkeit mit welcher Stufe kommt; Besuchsdauer 1–2,5 Minuten; Glitch-Geist (Entwurf C) nicht gebaut.
- **Offen:** eine feste Lieblingsfarbe je KI; eigene Gestalten nach Wunsch des Spielers; KI an einem Gegenstand statt Critter (→ 15.11. gebaut, siehe unten).

### KI am Gegenstand (15.11.2026, gebaut)

Mark: „Und dann wollte ich noch, dass ein Spieler eine KI als Begleiter hat, ich dachte mir, dass wir die an einen Gegenstand koppeln könnten, und wir in dem Gegenstand für den Spieler einen aktivieren/deaktivieren-Button … da geht es aber eigentlich nur um das Desktop-Pet.“

- **Datenmodell (Rückfrage beantwortet):** die KI bleibt ein eigener Begleiter — KI-Person (`istKI`) mit Blatt aus der Begleiter-Verwaltung, wächst mit ihren EP. Die SL koppelt sie im Bearbeiten-Formular des Gegenstands (unter „Pet auf den Tablets“, Feld „KI-Begleiter“). Am Gegenstand: `kiPersonId` und `kiAktiv`.
- **Schalter:** der Besitzer sieht im Gegenstandfenster „KI aktivieren/deaktivieren“; er schaltet nur das Desktop-Pet. Die SL hat dasselbe als Häkchen „KI wach“ im Formular, dazu die Wachstumsstufe.
- **Wann sie fliegt:** wie Bärbel — beim Besitzer des Gegenstands und seiner Party, nicht weggeworfen, nicht in einer verschlossenen Kiste, und nur wenn wach. Neu gekoppelt ist sie wach; eine KI ohne Pet-Art wird beim Koppeln zur KI-Pet-Art (Funke).
- **Annahmen Neko:** Ausrüsten nicht nötig (wie Bärbel); Startzustand wach; die KI am Critter (13.11.) bleibt daneben möglich.
- Im Kampf ist sie wie jeder Begleiter freisetzbar (siehe [[concepts/kampf-und-initiative]]), unabhängig vom Schalter.
- **Bestands-NPCs als KI (15.11.):** Mark hatte KIs als normale NPCs angelegt. Es gibt (noch) keinen KI-Schalter im NPC-Detail; auf seinen Wunsch wurde nur **Babybell** live per Einmal-Update auf `istKI = true` gestellt (Babel bewusst nicht). Weitere NPCs gleich so umstellen oder ein Häkchen bauen, wenn er es braucht.

### Entwurf 13.11.2026 (Auswahl getroffen: A und B)

Mark: „Einer meiner Spieler hat eine eigene KI, und ich dachte mir, wir könnten sie als Datenwolke oder cooles, Licht pulsierendes, manchmal verschiedene Formen oder Gestalten annehmendes Wesen machen … Die KI wäre auch ein Begleiter, der wachsen kann.“

Drei Entwürfe, je fünf Wachstumsstufen (Funke, Keim, Geist, Wesen, Entität — Arbeitstitel), Generator `docs/assets/critter-pet/ki_entwurf.py`, Tafeln `ki_entwurf_wachstum.png` und `ki_entwurf_gestalten.png`:

- **A Datenwolke:** Schwarm aus Datenpunkten mit dichtem Kern und Augen; wächst zu Wolke mit Netz, Nullen/Einsen und Umlaufbahn. Gestalten: die Punkte lösen sich und formen das Bild.
- **B Lichtkern:** pulsierende Kugel mit Strahlen; bekommt Ringe und Trabanten. Gestalten: zeichnet Umrisse aus Licht.
- **C Glitch-Geist:** Hologramm-Gestalt aus Bildzeilen mit Visier, verrutschten Zeilen und Farbsaum; bekommt Hände, Reif, Splitter. Gestalten: flackert zur Form um.
- Gestalten im Entwurf: Katze, Totenkopf, Herz, Schlüssel, Pfeil, Warnung. Farbe als Palette frei wählbar (Cyan, Magenta, Grün, Bernstein gezeigt). Leuchten kommt im Tool aus einem CSS-Filter, nicht aus dem Sprite.

Marks Wahl: A und B, Wechsel zwischen beiden, dazu Farben und Gestalten. C nicht gebaut. Die übrigen Achsen (woran sie hängt, was sie tut) hat Neko als Annahme gebaut, siehe oben.

## Mongo und Tummy-Acher (15.11.2026, Grundausstattung gebaut)

### Gebaut 15.11.2026 (Mark: „Fang gut bauen an!“)

- Alle drei Farben je Pet als eigene Art am Critter: Mongo Dschungel/Wüste/Bonbon, Tummy-Acher Fleisch/Rosa/Lila.
- Ei (antippen wie beim Drachen) + 6 Schritte. **Annahme Neko:** gleich schnell ausgewachsen wie der Drache — bei „EP je Schritt“ 5 alle 12 EP ein Schritt, groß bei 60 EP.
- Können vorerst, was der Drache ohne Atem kann: Küken nur am Boden, fressen, Häufchen; ab Schritt 2 klettern und springen, ab 3 aufs Burgermenü; schlafen, streicheln, packen/werfen, Ruß abschütteln. Animationen: stehen, laufen (Mongo gebückt), freuen, springen, fressen (Mongo senkt den Kopf, Tummy mampft), hinlegen/schlafen.
- **Futter lässt wachsen** (Mark: „über XP und Futter“): ein leer gefressener Napf zählt wie 1 EP — Kampagnen-Einstellung „Pet-Wachstum: EP je Futter“. **Annahme Neko:** gilt für alle wachsenden Pets, nicht nur den Tummy-Acher (0 stellt es ab).
- **KI-Futter:** im Bearbeiten-Formular beim Häkchen „Futter“ die Auswahl „für Tiere (Napf) / für KI (Datenpaket)“. Das Datenpaket schwebt leuchtend auf dem Bildschirm, die KI fliegt hin und saugt es ein; heilt, macht zutraulich, lässt wachsen wie der Napf. Tiere fressen kein Datenpaket, die KI keinen Napf.
- **Noch nicht gebaut** (entschieden, nächste Stufen): Mongo jagt/scheucht andere Pets, rennt schnell und springt weit, kreischt mit Bildschirmwackeln, faucht fremde Finger an, versteckt sich hinter Objekten, zieht Pets aus dem Bildschirm. Tummy-Acher frisst alle Spuren (auch die Perle), Näpfe anderer, knabbert Knöpfe/Wörter an, verschluckt Pets kurz, Gummiball beim Werfen, frisst Feuerbälle/Blitze, plumpst platt und ploppt rund, Mongo beißt rein und er rollt weg, leckt Ruß und Schleim vom Bildschirm.

### Tummy-Acher frisst Punkte (16.11.2026, gebaut)

Mark: „er könnte ja auch die Punkte der Fertigkeiten und Attribute der Spieler fressen, die Frage ist wie sie die wieder bekommen, vielleicht wenn man ihn streichelt?“ — entschieden: **nur Optik** (der Wert bleibt gleich), zurück **durch Streicheln**.

- Ab Schritt 2 (springen) hüpft er gern auf Punktereihen im Charakterbogen und mampft gefüllte Punkte weg; sie fliegen ins Maul, an ihrer Stelle ist eine Lücke. Der Wert ändert sich nicht und lässt sich weiter anklicken.
- Höchstens 12 Punkte im Bauch (Annahme Neko). Er behält sie auch, wenn er weiterzieht — erst Streicheln bringt sie zurück: er rülpst, die Punkte fliegen im Bogen an ihren Platz. Neu laden bringt sie ebenfalls zurück.

### Idee und Entwurf (15.11.2026)

Mark: „Ich hätte gerne 2 Pets aus Dungeon Crawler Carl, und zwar einen Mongoliensis, der klein wie ein seltsames Hühnchen und groß wie ein ausgewachsener gefiederter Raptor aussieht, und dann einen Tummy-Acher, eine runde tollpatschige Fleischkugel auf 2 Beinen, die alles frisst und fast unzerstörbar ist, und aus irgendeinem Grund sehr niedlich ist.“ Er will beide vor dem Android-Desktop-Pet bauen.

- **Mongo (Mongoliensis):** wächst vom komischen Küken zum gefiederten Raptor.
- **Tummy-Acher:** runde Fleischkugel auf zwei Beinen, tollpatschig, frisst alles, fast unzerstörbar, niedlich.
- Eigene Figuren, nur von den Büchern inspiriert (wie beim Mushu-Drachen).
- **Entscheidungen 15.11.2026 (Mark):**
  - Mongo: **Ei + 6 Schritte** bis groß. Tummy-Acher „theoretisch auch“: ebenfalls Ei + 6 Schritte.
  - Mongo kann: andere Pets jagen und scheuchen, schnell rennen und weite Raptor-Sprünge, kreischen (Bildschirm wackelt), fremde Finger anfauchen (beschützt seinen Besitzer) — alles gewünscht. Neu dazu: **versteckt sich hinter Objekten** und **zieht andere Pets aus dem Bildschirm** (sie wandern dann weiter).
  - Tummy-Acher frisst: alle Spuren (Häufchen, Seiten, Ruß, auch die Perle), Näpfe auch anderer Pets, knabbert Knöpfe/Wörter an (kurz weg, dann wieder da), verschluckt andere Pets kurz und spuckt sie wieder aus. Unzerstörbar: springt geworfen wie ein Gummiball, frisst Feuerbälle/Blitze, plumpst flach und ploppt wieder rund, Mongo beißt rein und er rollt kichernd weg — alles gewünscht („Jaaah … klingt super“). Neu dazu: **leckt die Bildschirme frei von Ruß und Schleim**.
  - Tummy-Acher wächst **über EP und über Futter**.
  - Neu: **Spezialfutter für das KI-Pet** (heute frisst nur der Drache aus dem Napf).
- **Damals offen, am 15.11. entschieden** (Mark: „Fang gut bauen an!“ auf Nekos Vorschläge): Futter-Wachstum als Kampagnen-Einstellung „EP je Futter“ (Start 1); KI-Futter als Auswahl „für Tiere/für KI“ am Futter, wirkt wie Tierfutter; alle Farben als eigene Arten; hängen am Critter wie der Drache.
  - Design: Entwurfstafeln `docs/assets/critter-pet/mongo_entwurf.png` und `tummy_entwurf.png` (Generator `dcc_entwurf.py`), je drei Farbvarianten (Mongo: Dschungel, Wüste, Bonbon; Tummy-Acher: Rosa, Pfirsich, Lila), Ei + 6 Schritte plus Kreischen bzw. Mampf/Platt. Mark wählt.
  - Nachschärfung 15.11. (Mark mit Velociraptor-Referenzbild): „Schwanz dünner und länger, ganz ausgewachsen ein wenig mehr wie auf dem Bild“. Umgesetzt: Schwanz fast doppelt so lang, dünn zulaufend, waagrecht steif mit Federsaum statt Fächer; Rücken dunkel, Bauch nur noch schmaler Streifen; längere Schnauze und Beine; gefaltete Flügelfedern mit Krallen; Kamm liegt beim Großen nach hinten. Küken-Stufen fast unverändert.
  - Nachschärfung 15.11.: Mark „Hals noch länger und dünner, dann passt es“. Hals beim Großen gut 50 % länger und deutlich schmaler (`hl` 13 → 20, Halsdicke ~0,5 statt 0,62). Damit ist die Mongo-Figur für Mark abgenommen.
  - Nachschärfung 15.11.: „Wenn er läuft, etwas gebückter, damit er gefährlicher aussieht.“ Pose `laufen` in `dcc_entwurf.py`: Rumpf nach vorn gekippt, Hüfte tiefer (Knie gebeugt), S-Hals mit vorgestrecktem tiefem Kopf, Schrittweite wächst mit. Gebückt skaliert mit dem Wachstum — das Küken watschelt aufrecht (Annahme Neko). Stehen unverändert. Tafel `mongo_laufen_entwurf.png`.
  - Nachschärfung 15.11.: Kante/Höcker am Rücken vor dem Schwanz auf der Jagd „schaut falsch aus“. Schwanz läuft beim Laufen genau in Verlängerung des Rumpfs (gerade Rückenlinie), Schwanzansatz so dick wie die Hüfte.
  - Nachschärfung 15.11. Tummy-Acher („fast perfekt“): Zahn wirkte aufgeklebt. Jetzt rechts der Mitte, wächst von der Unterkieferkante hoch, mit Schattenseite; Zunge nach links verschoben.
  - 15.11.: Mark „die gefallen mir sehr gut!!“ — beide Figuren abgenommen. Letzte Korrektur: bei Schritt 2 und 4 war der Zahn zu hoch; Zahnhöhe jetzt höchstens 60 % der Mundhöhe.
  - Nachschärfung 15.11. (Mark mit Buchcover): Tummy-Acher „mehr wie ein seltsamer Fleischklops … mit Zahn und Dellen“, süß ja, aber seltsam. Umgesetzt: klumpiger Körper aus Beulen, Dellen und Sprenkel, ungleich große Glubschaugen mit blauer Iris über dem Umriss, breites Grinsen mit einem Zahn, keine Arme mehr, Haarbüschel weg. Farben jetzt A Fleisch (wie Cover), B Rosa, C Lila (Pfirsich entfällt, war fast wie Fleisch).

## Vampir-Fledermaus (Idee 17.11.2026, offen)

Mark: „eine süße Fledermaus, die ab Stufe 3 auch zu einem Vampir werden kann, wir brauchen aber auf jeden Fall einen Vampir-Mann und eine Vampir-Frau; mit Stufe 4 wäre die dann ein junger Teenager, 5 dann schon so 18, ein wenig sexy oder elegant, und [6] wäre dann halt der ausgewachsene elegante Vampir mit viel Charme und Sexappeal.“

Skizze (Neko, nichts entschieden):
- **Stufen:** 1 Baby-Fledermaus · 2 Fledermaus · 3 Vampir-Kind (Chibi mit Umhang) · 4 Teenager · 5 junger Erwachsener (~18, elegant) · 6 ausgewachsener Vampir mit Charme. Wachstum wie die anderen Pets über die Critter-EP (12 Schritte, Zwischenformen).
- **Rahmen Optik:** Stufe 3–4 niedlich/frech bzw. düster-melancholischer Teen, nichts Anzügliches; Eleganz, Charme und Sexappeal erst ab Stufe 5 (erwachsen).
- **Verhaltensideen:** hängt kopfüber an Popup-Kanten und Menüpunkten und schläft so (bzw. im Sarg ab Stufe 3); verwandelt sich zum Wandern in eine Fledermaus mit Rauchwölkchen; Umhang-Schwung; Kusshand/Herzen beim Streicheln, hypnotisiert andere Pets; Futter als Blutkonserve oder Tomatensaft; Spur: Blutstropfen oder Fledermaus-Guano.
- **Technik:** erste menschenähnliche Pixel-Figur — Laufzyklus und Proportionen (Kopf groß → klein) sind aufwändiger als bei den Tieren; Entwurfstafel zuerst.

Offene Achsen (Formular vom 17.11. ohne Antwort abgelaufen):
- ~~Weggabelung Stufe 3~~ **Entschieden 17.11. (Mark):** „Sie bleibt eine Fledermaus, sie kann sich aber in einen Vampir verwandeln, wenn sie möchte.“ → Grundgestalt ist immer die Fledermaus; ab Stufe 3 verwandelt sie sich von selbst ab und zu in die Vampirgestalt ihrer Stufe und zurück (wie Bärbels Gestaltwechsel). Lesart Neko: die Stufen 3–6 beschreiben die Vampirgestalt; die Fledermaus wächst mit.
- **Mann/Frau:** zwei eigene Pet-Arten (wie Drachenfarben) · SL wählt bei der Verwandlung · Zufall.
- **Start:** schlafende Baby-Fledermaus kopfüber, 5–10× antippen weckt sie · Ei · gleich wach.
- **Fortbewegung Vampir:** laufen + zum Wandern/Klettern Fledermaus-Verwandlung · schweben · nur laufen/springen.
  Neko: durch die Entscheidung oben naheliegend — als Fledermaus fliegt/wandert sie, als Vampir läuft sie. Noch offen: wann/wie oft sie sich verwandelt (zufällig, beim Streicheln, nachts …).
- **Stufenfolge:** wie oben · oder Stufe 3 noch Fledermaus mit Umhang, Vampir-Kind entfällt.

### Marks Entscheidungen 17.11.2026 (zweite Antwort)

- **Mann/Frau:** zwei eigene Pet-Arten — Fledermaus M und Fledermaus W. Die SL wählt beim Setzen am Critter.
- **Verwandeln nach Zutraulichkeit:** bei hoher Zutraulichkeit verwandelt sie sich öfter in den Vampir und bleibt länger in der Gestalt. Lesart Neko: zählt die Zutraulichkeit des Spielers, auf dessen Tablet sie gerade ist (Wert je Spieler und Critter, unsichtbar).
- **Start:** Ei wie beim Drachen. **Kopfüber hängen ist wichtig** (Mark) — Kernverhalten der Fledermaus (an Popup-Kanten, Menüpunkten, oben am Bildschirm).
- **Bärbel will die Fledermaus fressen:** Bärbel spuckt laut Ideenliste manchmal Fledermäuse aus (noch nicht gebaut). Neu: trifft Bärbel die Fledermaus-Pets, will sie sie unbedingt fressen (jagt sie, schnappt mit dem Deckel, Tentakel greift). Ausgang (entkommt sie immer, verschluckt und wieder ausgespuckt?) offen.
- Noch offen: Entwurfstafel (Fledermaus-Stufen + Vampirgestalten M/W je Stufe); was die Vampirgestalt tut; Futter und Spur.

### Entwurf 17.11.2026 (Mark: „Das klingt perfekt und lustig! Machen wir das“)

Mark hat das Bärbel-Duell abgenommen: meist entkommt die Fledermaus knapp, ab und zu verschluckt Bärbel sie, rülpst und spuckt sie zerzaust wieder aus.

- Generator `docs/assets/critter-pet/vampir_entwurf.py` (`python vampir_entwurf.py <ziel>`), Tafeln `fledermaus_entwurf.png` und `vampir_entwurf.png`.
- **Fledermaus M** (schiefergrau-violett) und **W** (lila, Wimpern, Locke im Büschel): Ei + 6 Stufen, Flügel angelegt; ab Stufe 3 rote Augen und Fangzähnchen, ab 4 Fellkrause, ab 5 längere Fänge. Dazu Flugpose und kopfüber an einer Kante.
- **Vampirgestalt M:** 3 Kind (Stehkragen-Umhang, Fliege) · 4 Teen (Emo-Pony, offene Jacke, Shirt mit Fledermaus-Logo, kurzer Umhang) · 5 ~18 (offenes weißes Hemd, Weste, lose Strähne, Schmunzeln mit Fang) · 6 erwachsen (Frack, rote Weste, Halstuch mit Rubin, hoher Kragen, graue Schläfen).
- **Vampirgestalt W:** 3 Kind (Zöpfe, Kleidchen mit Bubikragen) · 4 Teen (gerader Pony, knielanges Kleid, Ringelstrümpfe, Stiefel) · 5 ~18 (schulterfreies Kleid, Samtband, rote Lippen) · 6 erwachsen (bodenlanges Abendkleid mit Schlitz, Opernhandschuhe, Rose im Haar, hoher Kragen).
- Größe: Vampir 38 → 70 px hoch (Drache Stufe 6: 60 px); am Handy ×1,5.
- Mark: „Das find ich super!“ — Aussehen abgenommen. Nachschärfung: „Der Mann müsste sich vielleicht noch manchmal einen Zylinder aufsetzen und vielleicht einen eleganten Gehstock haben.“ Entworfen für den erwachsenen Vampir M (Spalte „6 Zylinder+Stock“): Zylinder leicht schräg mit rotem Band, schwarzer Gehstock mit Silberknauf. **Annahme Neko:** Zylinder nur ab und zu (holt ihn hervor, setzt ihn auf, lüftet ihn zum Gruß), Gehstock nur beim Erwachsenen; ob schon der 18-Jährige Hut/Stock bekommt, offen.
- Nachschärfung Mark: Stock „schaut nicht elegant aus, wenn er so schräg wegsteht, er müsste den Arm ausstrecken und sich ein wenig draufstützen“. Jetzt: Arm seitlich ausgestreckt über dem roten Umhangfutter, Hand ruht auf dem Silberknauf, Stock steht fast senkrecht.
- Nachschärfung Mark („Sehr gut“): Arm eine Spur kürzer, Knauf als silberner Totenkopf (Hand liegt auf dem Schädeldach). Danach Totenkopf eine Spur kleiner (7 → 5 px breit).
- Offen: Verwandlungseffekt (Rauch mit Mini-Fledermäusen); Animationen.

### Gebaut 17.11.2026 (Mark: „Sehr gut! Bitte setz das um“)

- Zwei Pet-Arten am Critter: **Vampir-Fledermaus (Mann)** und **(Frau)**. Ei (5–10× antippen) + 6 Schritte wie Mongo; Futter aus dem Napf heilt und lässt wachsen. SL-Stufennamen: Fledermäuschen, Fledermaus, Vampir: Kind, Teen, ~18, erwachsen.
- **Fledermaus:** fliegt herein (in irgendeiner Höhe oder von oben), **hängt kopfüber** unter Knöpfen, Textzeilen, Kacheln, Popups oder oben am Bildschirmrand und pendelt leicht; döst 8–25 s oder schläft (Zzz) bis 3 Minuten. Antippen weckt sie bzw. sie freut sich (Herzen, Wackeln). Lässt beim Hängen manchmal ein Häufchen fallen (höchstens eins je Besuch). Verschwindet die Kante, fliegt sie los. Napf: landet daneben und frisst.
- **Vampir (ab Schritt 3):** landet auf dem Boden oder einer breiten Fläche, verwandelt sich in einer Rauchwolke mit kleinen Fledermäusen, läuft dort herum, wirft beim Streicheln eine **Kusshand**; danach wieder Rauchwolke und als Fledermaus weiter. Der erwachsene Mann setzt sich manchmal den **Zylinder** auf (kleine Wolke am Kopf), lüftet ihn zum Gruß und nimmt ihn vor der Rückverwandlung wieder ab; den **Gehstock** hat er immer.
- **Zutraulichkeit:** Das Tablet bekommt die Zutraulichkeit seines Spielers zum Pet. Je höher, desto öfter wird sie zum Vampir (12 % → 50 % der Entscheidungen) und desto länger bleibt sie es (15–30 s → bis dreimal so lang). **Annahme Neko:** volle Wirkung ab 40 Zutraulichkeit.
- **Bärbel will sie fressen:** sieht Bärbel eine Fledermaus, klappt sie auf und jagt hinterher; die Fledermaus flieht (ein Vampir verwandelt sich vor Schreck zurück). Kommt Bärbel nah, schnappt sie zu — meist daneben, ab und zu (**Annahme: 35 %**) sitzt es: die Fledermaus ist im Buch, das Buch beult und wackelt 2,6 s, dann rülpst Bärbel (eine Seite fliegt raus) und spuckt sie zerzaust mit Kringelaugen aus; sie taumelt und fliegt weiter. Jagd höchstens alle 35–90 s, je 8 s.
- Packen (3 s) und Werfen wie bei allen Pets; ein Vampir wird dabei sofort wieder zur Fledermaus. Feuer/Eis/Blitz anderer Pets lassen sie fliehen.
- **Annahmen Neko:** Pausen, Dauern und Wahrscheinlichkeiten oben; Vampir-Laufen von vorn (Gehbewegung im Stand, der Rahmen wandert); Rauch dunkelviolett; Zylinder/Lüften und Gehstock nur beim erwachsenen Mann — **von Mark bestätigt 17.11.** („Den hat nur der Erwachsene!“).
- Noch offen: was der Vampir sonst noch tun könnte. (Bärbel niest selbst Fledermäuse aus: gebaut 18.11., eigener Abschnitt.)

## KI-Reinigungslaser (18.11.2026, gebaut)

Mark: „ein Reinigungslaser! Ein Strahl, der an einem Punkt beginnt und dann immer schneller wird, bis er wie ein Fächer aussieht, der dann allen Schmutz der anderen Pets wegbrennen kann.“

Skizze Neko (nichts entschieden): Die KI schwebt zum Schmutz, der Kern lädt sich auf, ein dünner Strahl in ihrer Farbe trifft einen Punkt am Boden, pendelt immer schneller, bis er als flimmernder Fächer steht. Alles im Fächer verdampft mit Funken und Rauchwölkchen. Passt zu „hinterlässt nichts“: die KI ist die Putzkraft der Pet-Bande.

Offene Fragen (am 18.11. gestellt, Vorschlag zuerst):
- Ab welcher Stufe? Vorschlag: ab Wesen, Entität mit breiterem Fächer. Alternativen: erst Entität, schon Geist.
- Was brennt weg? Vorschlag: alle Spuren (Häufchen, Brandflecken, Krater, Raureif, Schleim, Seiten); Näpfe, Perle und Datenpakete bleiben.
- Anderes Pet im Fächer? Vorschlag: verrußt wie nach Bärbels Blitz und schüttelt sich ab. Alternativen: flüchtet; nichts.
- Auslöser? Vorschlag: von selbst ab 3 Spuren auf dem Schirm, höchstens alle 2 Minuten. Alternativen: bei jeder Spur; nur auf Antippen des Besitzers.

**Mark 18.11.:** „am Anfang nur kleine Dinge wegbrennen wie Kot oder Seiten, später dann Schleim und danach Brandflecken; er könnte auch lernen, den Tummy zu jagen und die Punkte zurückzuholen.“

Vorschlag Neko dazu (offen):
- Geist: dünner Punktstrahl, nur Häufchen und Seiten · Wesen: Strahl pendelt, dazu Schleim und Raureif · Entität: voller Fächer, dazu Brandflecken und Krater. Raureif und Krater hat Neko zugeordnet.
- Tummy-Jagd ab Entität: hat der Tummy-Acher Punkte im Bauch, jagt die KI ihn und kitzelt ihn mit dem Strahl; er hickst, rülpst, die Punkte fliegen zurück (wie beim Streicheln, `punkte.ts::ausspucken`).

**Entschieden 18.11. (Mark):**
- Feuert von selbst, fliegt dafür zum Schmutz hin.
- Räumt alles auf, es bleiben keine Spuren übrig. **Lesart Neko:** sie putzt den Schirm komplett, soweit ihre Stufe die Spurart schon kann; Näpfe, Perle, Datenpakete sind keine Spuren.
- Ab 3 Spuren auf dem Schirm schaltet sie in den Putzmodus: rotes **!** über dem Kopf.
- Ab 10 Spuren ist sie wütend: drei blinkende **!** und das Anime-Zornader-Symbol (💢, rote gebogene Linien in Kreuzform).
- Offen: anderes Pet im Fächer; Stufenzuordnung (Vorschlag oben) bestätigen.

**Entschieden 18.11. (Mark), zweite Runde:**
- Anderes Pet im Fächer wird verrußt und schüttelt sich ab.
- Wütend (ab 10 Spuren) jagt sie nach dem Saubermachen einen **Schuldigen**: erst sauber machen, dann jagen. Die Wut (drei !, 💢) bleibt, bis sie einen gefunden hat, auch über die Tablet-Grenzen hinaus.
- Vorschlag Neko (offen): Schuldig ist das Pet mit den meisten weggeputzten Spuren (`petId` an der Spur); ist es nicht da, fliegt sie zu dem Tablet, auf dem es gerade ist (wie die Perlen-Suche). Gefunden → Laser, verrußt, Wut weg. Ist es nirgends wach, nimmt sie den Nächstschuldigen.
- Stufenzuordnung: Mark hat nicht widersprochen, gilt als Annahme.

### Gebaut 18.11.2026 (Mark: „bau“)

- **Was sie kann (Stufe):** Geist: dünner Punktstrahl, der nur zittert — Häufchen, Seiten · Wesen: Strahl pendelt — dazu Schleim, Raureif · Entität: voller Fächer — dazu Brandflecken, Krater (`laser.ts::LASER_ARTEN`).
- **Putzmodus:** ab 3 Spuren auf dem Schirm (und mindestens einer, die sie schon kann) rotes **!** über dem Kopf. Sie fliegt über die nächste Spur, lädt den Kern auf, Strahl auf den Punkt, pendelt immer schneller, bis er als Fächer steht. Alles im Strahl verdampft (Lichtblitz, Funken, Rauch) und verschwindet wie weggewischt. Danach die nächste, bis keine Spur mehr übrig ist, die sie kann.
- **Wütend:** ab 10 Spuren drei blinkende **!**, pochende Zornader (💢, vier gebogene Stücke) und sie wird rot. Erst sauber machen, dann jagen: Schuldiger ist, wessen Spuren am meisten lagen (`petId` an der Spur). Ist er auf dem Schirm, fliegt sie hinterher und schießt; ist er auf einem anderen Tablet, schaut sie sich kurz um und fliegt los — der Server schickt sie direkt dorthin (`Pet.jagd`, `_jagd_ziel`, Meldung `jagd`). Die Wut bleibt über Tablets hinweg, bis sie einen Schuldigen erwischt hat; dann wird sie wieder ihre Farbe und zeigt kurz ein Smiley. Ist keiner online, bleibt sie wütend und zieht normal weiter.
- **Pets im Strahl** verrußen wie nach Bärbels Blitz (Drache, Mongo, Tummy schütteln sich ab; Bärbel und die Fledermaus erschrecken, eine andere KI bekommt eine Bildstörung).
- **Tummy-Acher kitzeln (Entität):** hat er Punkte im Bauch, fliegt sie hin und kitzelt ihn mit einem dünnen Strahl; er rülpst, die Punkte fliegen zurück (wie Streicheln, ohne Zutraulichkeit). Höchstens alle 8–14 s.
- Angetippt oder gepackt bricht der Schuss ab; danach macht sie mit dem Putzen weiter.
- **Annahmen Neko:** Schusslänge ~3 s (Jagd kürzer), Abstand über der Spur, Fächerbreite je Stufe, höchstens 40 Schüsse je Putzrunde, Zeichen wachsen mit ihr; Schuldige ohne Spur-Verursacher (Datenpaket, Napf) zählen nicht; sie putzt keine Spuren, die ihre Stufe noch nicht kann, auch wenn sie wütend ist.

## KI-Traktorstrahl und Pixelherz (19.11.2026, gebaut)

Mark: „Ich hab jetzt die KI aktiviert, das kleine Pünktchen. Wenn man es antippt, wäre cool, wenn ein pixeliges Herz aufsteigt, und scheinbar hat es in der Form noch keinen Laser, was mich auf die Idee gebracht hat, wir machen etwas, das langsamer ist: wir geben ihm einen Traktorstrahl, so blaue Partikel, die z. B. zum Kot fliegen, ihn aufheben, dann bringt er ihn zum Rand und schmeißt ihn aus dem Bildschirm raus, wo er dann verschwindet.“

- **Ablauf:** Liegt ein Häufchen oder eine Seite herum, schwebt sie ein Stück darüber. Ein blauer Lichtkegel mit wandernden Ringen geht an, blaue Pixel-Teilchen schlängeln hinüber und flirren um das Ding. Nach ~1,4 s hebt es ab und hängt unter ihr; sie trägt es langsam zum näheren Seitenrand und steigt dabei etwas, das Ding pendelt am Strahl. Am Rand ein Schwung — es fliegt kreiselnd aus dem Bildschirm und ist weg (Server `wegmachen`). Danach freut sie sich.
- **Herz:** Antippen lässt bei jeder Stufe ein pinkes Pixelherz über ihr aufsteigen (zusätzlich zur Herz-Gestalt ab Keim).
- **Abbruch:** Antippen oder Ziehen beendet den Strahl. Hängt das Ding schon in der Luft, fällt es nach unten aus dem Bild und ist auch weg. Nimmt jemand anderes es vorher (weggewischt, verbrannt, gefressen), lässt sie es.
- **Nachbesserung 19.11. (Mark: „Traktorstrahl ein wenig weiter runter, so dass sich das Häufchen im Strahl befindet, und cooler, wenn es da bleibt, wenn man ihn unterbricht“):** Der Kegel reicht jetzt ein Stück über das Ding hinaus und ist breiter, es hängt mitten im Strahl. Unterbrochen fällt es von dort hinunter (eine Seite segelt und kann auf einer Kante liegen bleiben) und **bleibt liegen**, wo es landet; danach macht sie 4–9 s Pause, bevor sie es wieder holt.
- **Annahmen Neko:** nur Funke und Keim (ab Geist übernimmt der Laser); nur Häufchen und Seiten; schon ab einer Spur, kein Putzmodus-„!“; 4–9 s Pause zwischen zwei Würfen; Tragetempo 70 % ihres Flugtempos; Herz bei allen Stufen; Teilchen immer blau, unabhängig von ihrer Farbe. Konstanten in `frontend/src/pets/traktor.ts`.

## Fledermäuse trinken Punkte (18.11.2026, gebaut)

Mark: „Die könnten die Fähigkeits- und Attributpunkte austrinken! So anstelle von Blut, und die füllen sich dann nur ganz langsam wieder auf, das könnte fast 10–15 Minuten dauern, bis die wieder ganz voll sind.“

Vorschlag Neko (offen):
- Nur Optik wie beim Tummy-Acher, der Wert bleibt gleich.
- Fledermaus hängt kopfüber unter einer Punktereihe und saugt; die Punkte werden ausgehöhlt (Umriss bleibt) statt verschwinden.
- Rückkehr: Punkt für Punkt, gestaffelt, bis alles nach 10–15 Minuten wieder voll ist; neu laden füllt sofort. Höchstens 6 Punkte je Besuch.
- Vampirgestalt trinkt auch (beugt sich elegant über die Reihe, beißt zu).
- Die KI holt getrunkene Punkte nicht zurück — die kommen ja von selbst.

**Mark 18.11.:** „Ja passt super“ zum Vorschlag, dazu: „wie eine Fruitbat in die Kugel beißen und sie dann austrinken“.

### Gebaut 18.11.2026

- Die Fledermaus (alle Stufen) schwebt flatternd seitlich an einem gefüllten Punkt im Charakterbogen, schräg zur Kugel geneigt, beißt hinein (Kugel zuckt) und trinkt sie aus: die Füllung sinkt von oben, der Ring bleibt, Tropfen in der Punktfarbe fliegen ins Maul. Die Kugel liegt dabei vor ihrem Maul (über der Pet-Ebene). Danach trinkt sie oft den Nachbarn in derselben Reihe, sonst fliegt sie satt mit einer Freudenrolle weg.
- Nur Optik (`punkte.ts`: `punktAnbeissen`/`punktTrinken`/`punktNachfuellen`, Klasse `pet-punkt-getrunken`, Füllstand `--pet-pegel`). Jeder ausgetrunkene Punkt läuft in 10–15 Minuten langsam wieder voll; neu laden füllt sofort. Der Tummy-Acher frisst keine angetrunkenen Punkte.
- Als Vampir wird sie bei Durst kurz wieder zur Fledermaus und trinkt dann (Abweichung vom Vorschlag „beugt sich über die Reihe“: dafür gäbe es keine Pose; Mark wollte ohnehin den Fruitbat-Biss).
- **Annahmen Neko:** höchstens 6 Punkte je Besuch, ein Punkt dauert ~2 s (**Mark 18.11.: zu schnell → jetzt 5–6 s je Punkt**), Durst frühestens 5–17 s nach der Ankunft und nach dem Trinken 25–60 s Pause; Abbruch (gepackt, Bärbel, Feuer) lässt den Punkt ab seinem Stand nachlaufen.

## Bärbel niest Fledermäuse aus (18.11.2026, gebaut)

Mark: „kannst du bitte für Bärbel die Animation machen, bei der sie Fledermäuse ausniest, es wäre toll, wenn die Fledermäuse wie die Perle da bleiben würden und durch die Gegend flattern und sich kopfüber auf HTML-Items hängen, und Bärbel dann versucht, sie mit dem Tentakel wieder einzufangen oder mit Blitzen zu vernichten, und sie jagt … Andere Pets könnten sie eventuell auch jagen, das könnten wir später noch einführen; vielleicht erscheinen zufällig zwischen 2 und 5 Fledermäuse.“ (Erfüllt die alte Ideenliste „weitere Monster: Fledermäuse“.)

- **Niesen:** Bärbel holt zugeklappt Luft (bläht sich, kippt nach hinten, zittert), dann Hatschi: der Deckel fliegt auf, kleine violette Wolke, Rückstoß nach oben, und **2–5 kleine Fledermäuse** prusten in alle Richtungen heraus.
- **Die Flattermäuse** bleiben als Spur (`flattermaus`) auf dem Tablet, auf dem sie geniest hat — auch nach Neuladen, bis Bärbel sie erwischt. Sie flattern im Zickzack herum (ein paar Schlenker), hängen sich **kopfüber** unter Knöpfe, Textzeilen, Kacheln, Popups oder oben an den Bildschirmrand, pendeln dort 6–25 s und ziehen weiter. Verschwindet die Kante, flattern sie los. Aussehen: die Baby-Fledermaus, kleiner (×0,6) und mit violettem Zauberschein.
- **Bärbel jagt sie:** hängt eine still, fliegt Bärbel hin und das Tentakelmonster packt sie und zieht sie zurück ins Buch. Fliegt sie, jagt Bärbel hinterher und schleudert aus etwa 300 px den Blitz (der Strahl folgt ihr beim Aufladen; ein Gabelblitz nimmt eine zweite Maus mit). Getroffen wird sie schwarz, trudelt runter und verpufft. Erwischt → kleiner Freudenhüpfer.
- **Ausweichen:** in etwa einem Drittel der Versuche merkt die Maus es und haut im letzten Moment ab — Tentakel klatscht ins Leere (Schleim), Blitz schlägt daneben ein (Brandfleck).
- **Antippen** scheucht eine Maus auf (sie fliegt weit weg); wegmachen kann sie nur Bärbel. SL „Alles sauber machen“ räumt sie mit weg.
- **Annahmen Neko:** Niesen frühestens 20–60 s nach der Ankunft, danach 100–220 s Pause, nicht mehr ab 6 Mäusen im Bild; Jagdversuch alle 7–16 s, solange Mäuse da sind (nach dem Niesen erst 12–22 s flattern lassen); Ausweich-Chance 35 %; Tentakel bei hängender Maus 60 %, sonst Jagd mit Blitz; sie bleiben auf ihrem Tablet und wandern nicht mit (anders als die Perle); Feuer, Eis, Laser und die anderen Pets beachten sie noch nicht.
- **Noch offen (Mark: „später“):** andere Pets jagen sie auch (z. B. Drache, Mongo, Vampir-Fledermaus).

## Tierladen: Pet kaufen (gebaut 18.11.2026)

Mark: „wie aufwändig wäre ein Petshop bei dem sich meine Spieler ein Pet
kaufen könnten?“ — ein Laden, der Tiere UND Tiernahrung verkauft, wie das
„in echt auch wäre“.

**Entschieden (Mark, 18.11.):**
- Die SL baut den Critter **fertig** (Begleiter-Verwaltung, volles Blatt,
  Pet-Art, alles wie heute) — der Spieler baut sich nichts selbst
  zusammen, er kauft ein fertiges Stück.
- Käufer bekommt einen **vollwertigen Begleiter** (eigenes Blatt,
  Kampfteilnahme — wie ein normaler Critter heute schon kann).
- Im Laden ein **eigener Reiter „Pets“** neben der normalen Warenliste
  (Tiernahrung bleibt ganz normal `istTierfutter`-Ware in der Liste).
- **Limit 1 Begleiter pro Spieler — nur beim Kauf.** Die SL darf als SL
  weiterhin beliebig viele Critter manuell zuweisen (Begleiter-Verwaltung,
  unverändert). Der Shop-Kauf-Knopf prüft dagegen: hat der Käufer schon
  **irgendeinen** `BEGLEITET`-Critter (egal ob SL-zugewiesen oder gekauft),
  verweigert der Verkäufer den Verkauf — nicht nur „schon eins gekauft“.
- Reiter nur sichtbar, wenn Pets im Angebot sind **und** der Spieler noch
  keinen Begleiter hat. Kein eigener Ortstyp — derselbe Laden führt Tiere
  und Tiernahrung zusammen.

**Gebaut 18.11.2026:**
- Ein zum Verkauf stehender Critter ist ein normaler `Person{istCritter}`
  OHNE `BEGLEITET`-Kante, gelistet über dieselbe `Ort-[:VERKAUFT]->`-Kante
  wie eine Unikat-Ware (Bärbel-Muster), nur das Ziel ist der Critter statt
  ein `Gegenstand`. Preis direkt auf der Kante (`haendler/repository.py::
  pets_sortiment`/`pet_verkaufen`/`pet_aus_sortiment_entfernen`/
  `pet_regal_raeumen`).
- SL-Seite: `HaendlerBearbeiten.tsx`, Abschnitt „Pets im Angebot“ +
  `PetAnbietenPopup.tsx` (Picker aus besitzerlosen Crittern via
  `entitiesApi.listCritter`, kein neuer Lookup-Endpunkt).
- Kauf: `POST .../haendler/{id}/pets/kaufen` (`haendler/routes.py::
  pet_kaufen`) — 1-Begleiter-Limit über `entities_repository.
  critter_von_besitzer`, danach `haendler/uebergabe.py::critter_uebergeben`
  (→ `critter_besitzer_setzen`, erzeugt `BEGLEITET` statt `BESITZT`).
  Guthaben-/Tutorial-Buchung identisch zum Item-Kauf.
- Frontend-Reiter: `ShopSeite.tsx` (Zustand `ansicht`), sichtbar nur wenn
  `pets.length > 0 && meineCritter.length === 0` (`entitiesApi.
  meineCritter`) — Kachel/Popup in `ShopPet.tsx`. Nur im normalen Shop,
  NICHT im Tutorial-Shop (kein Freebee-Kauf).

**Offen/Annahmen Neko:**
- Ein Critter kann aktuell technisch an mehreren Läden gleichzeitig zum
  Verkauf stehen (keine Sperre) — bewusst nicht verhindert, SL-Entscheidung.
- Das 1-Begleiter-Limit zählt nur `Person{istCritter}` mit `BEGLEITET`,
  nicht Bärbel/KI-Begleiter am Gegenstand.

## Offene Achsen (Stand vor 11.11.-Antwort)

- Wanderziel: nur Party-Mitglieder (Skizze 24.09.) oder alle eingeloggten
  Spieler der Kampagne? Sieht die SL das Pet auch?
- Sprite-Zuordnung: ein Sprite-Set pro Critter (SL wählt/lädt hoch) oder
  feste Pet-Arten im Code (Drache, …)?
- Animationsliste (Vorschlag): Idle, Laufen, Schlafen, Essen, Feuer-Rülpser,
  Freuen/Hüpfen, Traurig/Hunger, Häufchen.
- Tamagotchi-Mechanik: Bedürfnisse aus der Skizze 24.09. (Hunger/Pflege,
  LP-Verlust) übernehmen oder vorerst nur Flavor ohne LP-Folge?
- Interaktion der anderen Spieler: dürfen sie das fremde Pet streicheln/
  füttern/zurückschicken?
