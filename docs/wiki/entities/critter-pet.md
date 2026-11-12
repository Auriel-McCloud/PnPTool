---
title: Critter-Pet (Tamagotchi)
created: 2026-11-11
updated: 2026-11-12
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

- Häufchen entfernen: wegklicken/wischen, nach Zeit, oder nur durch den Besitzer?
- ~~Drag and Drop/Werfen zusätzlich zum Streicheln: ja oder nein?~~ Entschieden 11.11.: ja (3 s halten, siehe oben).
- ~~Woher das Sprite eines Critters kommt~~ — feste Arten im Code, SL wählt
  aus der Liste (Critter: Tiere, Gegenstand: Bärbel).

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
