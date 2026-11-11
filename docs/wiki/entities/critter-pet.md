---
title: Critter-Pet (Tamagotchi)
created: 2026-11-11
updated: 2026-11-11
type: entität
tags: [ui, frontend, backend, datenmodell]
sources: [../../ENTWICKLUNGSHISTORIE.md, gespräch 2026-11-11]
status: offen
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
