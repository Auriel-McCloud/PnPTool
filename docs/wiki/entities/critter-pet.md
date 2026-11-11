---
title: Critter-Pet (Tamagotchi)
created: 2026-11-11
updated: 2026-11-11
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

## Noch offen

- Häufchen entfernen: wegklicken/wischen, nach Zeit, oder nur durch den Besitzer?
- Drag and Drop/Werfen zusätzlich zum Streicheln: ja oder nein?
- Woher das Sprite eines Critters kommt (fest im Code je Art vs. SL wählt
  aus einer Liste) — erst relevant, wenn die zweite Art kommt.

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
