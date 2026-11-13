---
title: Critter-Pet (Tamagotchi)
created: 2026-11-11
updated: 2026-11-13
type: entität
tags: [ui, frontend, backend, datenmodell]
sources: [../../ENTWICKLUNGSHISTORIE.md, gespräch 2026-11-11]
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

**Noch offen (Ideen von Mark):** weitere Monster (Klauen, Fledermäuse), Feuerbälle.

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
- **Offen:** eine feste Lieblingsfarbe je KI; eigene Gestalten nach Wunsch des Spielers; KI an einem Gegenstand statt Critter.

### Entwurf 13.11.2026 (Auswahl getroffen: A und B)

Mark: „Einer meiner Spieler hat eine eigene KI, und ich dachte mir, wir könnten sie als Datenwolke oder cooles, Licht pulsierendes, manchmal verschiedene Formen oder Gestalten annehmendes Wesen machen … Die KI wäre auch ein Begleiter, der wachsen kann.“

Drei Entwürfe, je fünf Wachstumsstufen (Funke, Keim, Geist, Wesen, Entität — Arbeitstitel), Generator `docs/assets/critter-pet/ki_entwurf.py`, Tafeln `ki_entwurf_wachstum.png` und `ki_entwurf_gestalten.png`:

- **A Datenwolke:** Schwarm aus Datenpunkten mit dichtem Kern und Augen; wächst zu Wolke mit Netz, Nullen/Einsen und Umlaufbahn. Gestalten: die Punkte lösen sich und formen das Bild.
- **B Lichtkern:** pulsierende Kugel mit Strahlen; bekommt Ringe und Trabanten. Gestalten: zeichnet Umrisse aus Licht.
- **C Glitch-Geist:** Hologramm-Gestalt aus Bildzeilen mit Visier, verrutschten Zeilen und Farbsaum; bekommt Hände, Reif, Splitter. Gestalten: flackert zur Form um.
- Gestalten im Entwurf: Katze, Totenkopf, Herz, Schlüssel, Pfeil, Warnung. Farbe als Palette frei wählbar (Cyan, Magenta, Grün, Bernstein gezeigt). Leuchten kommt im Tool aus einem CSS-Filter, nicht aus dem Sprite.

Marks Wahl: A und B, Wechsel zwischen beiden, dazu Farben und Gestalten. C nicht gebaut. Die übrigen Achsen (woran sie hängt, was sie tut) hat Neko als Annahme gebaut, siehe oben.

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
