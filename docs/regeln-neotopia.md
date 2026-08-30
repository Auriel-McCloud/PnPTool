# NeotopiA — Regeln, soweit fürs Werkzeug relevant

Aus `docs/reference/Neotopia.xlsx` herausgezogen (Blätter *Charakterblatt* und *Regeln*). Die Tabelle bleibt die Quelle der Wahrheit; dies hier ist die lesbare Fassung für die Umsetzung. **Bei Widersprüchen gilt die Tabelle bzw. Mark.**

**Herkunft der Regeln:** NeotopiA lehnt sich an die World of Darkness an — Mark nennt *Hunter V5* und *Vampire V5* als nächste Verwandte. Das **Magiesystem stammt aus Mage M20** (Sphärenbeschreibungen decken sich), ist aber an Shadowrun angepasst worden. **Marks Änderungen stehen im Excel und haben Vorrang vor dem Originalregelwerk.** Das M20-Grundregelwerk liegt als gekauftes PDF lokal im Projektordner zum Nachschlagen; es ist bewusst von der Versionierung ausgenommen (Urheberrecht, und 123 MB nimmt GitHub ohnehin nicht an).

## Würfelsystem

- Pool aus zehnseitigen Würfeln. **1–5 Misserfolg, 6–10 Erfolg.**
- **Kritisch:** zwei Zehnen zählen wie vier Erfolge, drei wie sechs — jede weitere Zehn verdoppelt entsprechend.
- **Patzer:** die Hälfte der Würfel zeigt 1.
- Es gibt keine Zahlenwerte: *alle* Werte sind Würfel, gezählt wird das Ergebnis.
- **Probe = Attribut + Fähigkeit.** Attribut + Attribut kommt selten vor.

## Attribute (Maximum 6)

| Körperlich | Gesellschaftlich | Geistig |
|---|---|---|
| Körperkraft | Charisma | Intelligenz |
| Geschicklichkeit | Manipulation | Geistesschärfe |
| Widerstandsfähigkeit | Fassung | Entschlossenheit |

## Abgeleitete Werte — nicht frei gesetzt

- **Gesundheit = 5 + Widerstandsfähigkeit**
- **Willenskraft = Entschlossenheit + Fassung**
- **Initiative = Geistesschärfe + Geschicklichkeit + Cyberware-Modifikator**

Auf dem Blatt sind Gesundheit, I.C.E., Arete/NeuroWeaving und Willenskraft **Kästchenreihen** (10 Kästchen, 5+5), keine Punktereihen. Der abgeleitete Wert bestimmt, wie viele davon zählen; abgehakt wird Schaden bzw. Verbrauch.

## Fähigkeiten (Maximum 5)

Dreißig Stück in drei Spalten, siehe `backend/app/traits/seed.py`. Riggen, Maker (Hardware) und Matrix gehören dazu.

## Die zwei besonderen Wege

**Auf dem Blatt steht ausdrücklich „Arete != NeuroWeaving"** — die beiden schließen sich aus. Wer keines von beidem gewählt hat, sieht weder Sphären noch NeuroWeaving-Fähigkeiten.

### Magie (Arete + Sphären)

- **Arete** ist der Magiewert. Ein *kontrollierter* Zauber würfelt nur den Arete-Wert.
- **Wilde Magie:** Bonuswürfel bis zur Höhe der Willenskraft dazunehmen; dafür muss vorher ein **Zielwert** festgelegt werden. Wird er unterschritten, ist die Probe gescheitert.
- Nach einem gelungenen wilden Zauber: **Willenskraftwurf gegen die Zahl der Erfolge**. Die Differenz geht als Schaden auf die Lebenspunkte. Entfällt, wenn die Erfolge genau dem Zielwert entsprechen.
- Kritische Treffer zählen beim Zielwert **nicht** als zusätzliche Erfolge — dort zählen nur Nettoerfolge.
- **Sphären beschreiben, was möglich ist, und geben keine Bonuswürfel.** Stufen: 1 wahrnehmbar · 2 bis ~50 cm³ · 3 bis ~4 m³ · 4 bis Hausgröße · 5 alles.
- Sphären: Korrespondenz, Entropie, Kräfte, Leben, Materie, Gedanken, Ursprung, Geister, Zeit. *Schaden durch Kräfte ist automatisch +1.*

### NeuroWeaving (Technomancer)

- Gleiche Grundregeln wie Arete, auch beim Willenskrafteinsatz und seinen Folgen.
- **Aber:** die NeuroWeaving-Fähigkeiten **geben Bonuswürfel** (anders als Sphären) und wirken nicht als Begrenzung.
- Ein Technomancer darf NeuroWeaving-Fertigkeiten auch nutzen, in denen er keine Punkte hat.
- Seine Verteidigung bestimmt sich über die Willenskraft.
- Fähigkeiten: Brute Force, Schleichen, Daten Verarbeiten, Kompilieren.

## Schadensarten

Drei Arten, wie in der World of Darkness — auf dem Blatt in dieselbe Kästchenreihe eingetragen:

| Zeichen | Art | Bedeutung |
|---|---|---|
| `/` | Schlagschaden | heilt schnell |
| `X` | schwerer Schaden | heilt langsam |
| durchgestrichenes `X` | aggravierter Schaden | heilt kaum |

**Schwererer Schaden steht links.** Beim Eintragen von Hand füllt man von links auf und ersetzt leichteren durch schwereren; die Anzeige hält sich daran und sortiert aggraviert, dann schwer, dann Schlag. Übersteigt die Summe die Gesundheit, wird beim leichtesten gekürzt.

Im Werkzeug schaltet ein Klick auf ein Kästchen weiter: unbeschädigt → `/` → `X` → durchgestrichen → wieder frei. Die Zeichen sind in CSS gezeichnet, nicht getippt — für aggravierten Schaden gibt es kein passendes Schriftzeichen.

## Matrix-Verteidigung (I.C.E. / Cyber Wall)

**Wer kein Technomancer ist, bezieht den Wert vom Commlink.** Ohne Commlink ist er 0 — dann ist man aber auch **offline und schlicht nicht angreifbar**. Der Unterschied zwischen „ungeschützt" und „nicht erreichbar" liegt also nicht im Wert, sondern darin, ob überhaupt ein Gerät dabei ist. Ein Commlink im Versteck schützt niemanden; es zählt nur, was ausgerüstet oder mitgeführt wird. Bei mehreren Geräten gilt der beste Wert, nicht die Summe.

**Cyberdecks addieren ihren Bonus obendrauf** (im Regelwerk als „Cywall+1" bis „Cywall+4" notiert). Mehrere Decks werden summiert — anders als Commlinks, weil es Zusatzausrüstung ist und kein Zugangsgerät. **Ein Deck allein nützt nichts:** ohne Commlink besteht keine Verbindung, die es verstärken könnte.

Commlink-Preis: 200 ¥ je Cyberwall-Punkt bis 5, darüber 500 ¥ je Punkt.

| Commlink | I.C.E. | Preis | | Cyberdeck | B/S/D/K | Bonus |
|---|---|---|---|---|---|---|
| Meta Link | 1 | 100 ¥ | | Aztechnology Tlaloc | 4/4/3/5 | +1 |
| Sony Emperer | 2 | 700 ¥ | | Tachikoma Prime | 5/3/4/4 | +2 |
| Renraku Sensei | 3 | 1.000 ¥ | | Hosaka Ghost | 4/5/4/5 | +3 |
| Erika Elite | 4 | 2.500 ¥ | | Ono-Sendai Cyberspace VII | 5/5/5/5 | +4 |
| Hermes Ikon | 5 | 5.000 ¥ | | | | |
| Transs Avalon | 6 | 8.000 ¥ | | | | |

Diese Geräte liegen in der Testkampagne als Vorlagen bereit.

**Technomancer: Fassung + Geistesschärfe.** Er trägt seine Abwehr in sich und braucht kein Gerät, ist also nie offline.

> ⚠️ **Weicht bewusst vom Regelblatt ab.** Dort steht in Zeile 99 „Die Verteidigungsfähigkeit eines Technomancers wird über seine Willenskraft bestimmt". Mark hat das am 29.08.2026 geändert: Die Willenskraft wird beim NeuroWeaving verbraucht, dieselbe Größe als Verteidigung hätte ihn nach jeder Aktion verwundbar gemacht. Fassung + Geistesschärfe bleibt stabil. **Das Excel ist an dieser Stelle noch nicht nachgezogen.**

## Kampf

- **Initiative:** Matrixnutzer vor Nahkämpfern vor Fernkämpfern. In umgekehrter Reihenfolge sagen alle an, was sie vorhaben — die schnellste Person kann dadurch reagieren; gewürfelt wird dann in der richtigen Reihenfolge.
- **Parieren:** Geschicklichkeit + Waffenfertigkeit. Gegen Fernkampf nur mit Cyberware oder Magie. Jede weitere Nutzung in derselben Runde gibt kumulativ −1.
- **Schaden Fernkampf:** Waffenschaden + Nettoerfolge gegen Rüstungsbonus.
- **Schaden Nahkampf:** Waffenschaden + Stärke + Nettoerfolge gegen Rüstungsbonus.
- Rüstungsboni werden addiert. Ab Rüstungswert 3 gibt es −1 auf Geschicklichkeit, ab 4 entsprechend −2.

## Charaktererstellung

1. **Alle Attribute starten auf 1**, verändert durch die Rasse.
2. **Rassen** mit Startmaximum und freien Punkten für die drei Attributspalten (frei zuordenbar, welche Spalte welche Zahl bekommt):

| Rasse | Frei | Startmax | Anpassungen |
|---|---|---|---|
| Mensch | 7 / 5 / 3 | 4 / 4 / 4 | — |
| Ork | 6 / 5 / 3 | 3 / 5 / 4 | Intelligenz −1, Körperkraft +1 |
| Elf | 5 / 5 / 3 | 3 / 5 / 5 | Widerstandsfähigkeit −1, Charisma +1, Geschicklichkeit +1 |
| Zwerg | 5 / 5 / 3 | 3 / 5 / 5 | Charisma −1, Widerstandsfähigkeit +1, Fassung +1 |
| Troll | 5 / 4 / 3 | 6 / 5 / 3 | Körperkraft +2, Widerstandsfähigkeit +1, Geistesschärfe −1, Geschicklichkeit −1 |

3. **Fähigkeiten** — eines von drei Paketen:
   - *Profi*: 1×4, 3×3, 3×2, 1×1 (8 Fähigkeiten)
   - *Ausgeglichen*: 3×3, 5×2, 7×1 (15 Fähigkeiten)
   - *Jack of all Trades*: 1×3, 8×2, 10×1 (19 Fähigkeiten)
   - Arete, Sphären und NeuroWeaving zählen als Fähigkeit, werden aber normalerweise ohne Attribut gewürfelt.
4. **Startkapital 10.000 ¥.**
5. **15 Freebees**, Kosten: Attribut / Arete / NeuroWeaving **5** (darf das Startmaximum übersteigen), Fertigkeit **2** (höchstens +1), Willenskraft **1**, Kredit 10.000 ¥ = 1, Eigenkapital 10.000 ¥ = 2.
   *Das Startmaximum gilt nicht für Freebees.*

> **Beim Umsetzen abgeleitet:** die Startmaximum-Spalte der Tabelle ist durchgehend
> **4 + Anpassung** — ohne Anpassung 4, bei +1 dann 5, bei +2 dann 6, bei −1 dann 3.
> Deshalb steht im Code (`backend/app/traits/erstellung.py`) nur die Grundzahl 4 und
> wird mit dem Rassenmodifikator verrechnet, statt die Tabelle doppelt zu führen.

### Hintergründe — **nicht aus dem Regelwerk**

Im Excel kommen Hintergründe nicht vor. Mark wollte sie ("bis zu 5 Punkte als Freebees"),
die Liste selbst ist deshalb ein Vorschlag fürs Setting und steht zum Umbau frei
(`HINTERGRUENDE` in `erstellung.py`): Kontakte, Ressourcen, Straßenruf, Verbündete,
Mentor, Unterschlupf, Schwarzmarkt, Konzernzugang, Ausrüstung, Geheimwissen.

Ebenfalls gesetzt, aber nicht belegt: **1 Freebee je Hintergrundpunkt**, höchstens
5 Punkte insgesamt und 5 auf einen einzelnen.

### Kopfzeile des Blatts

Aus dem Charakterblatt-Sheet (Zeilen 3-7), reiner Text ohne Regelwirkung:
**Konzept · Alter · Ambition · Verlangen · Ziel · Kapital/Schulden.**

## Erfahrung ausgeben — **nicht aus dem Regelwerk**

Das Excel beschreibt die Erstellung, sagt aber nichts über spätere Steigerungen.
Die Preise in `backend/app/traits/erfahrung.py` sind deshalb ein Vorschlag, angelehnt
an die World of Darkness (Preis = aktueller Wert × Faktor, der fünfte Punkt kostet
mehr als der zweite) und an das Freebee-Verhältnis der Erstellung:

| Was | Faktor | Erster Punkt (von 0) |
|---|---|---|
| Attribut | × 4 | — (steht nie auf 0) |
| Fertigkeit | × 2 | 3 |
| Sphäre | × 5 | 7 |
| NeuroWeaving | × 5 | 7 |
| Arete | × 8 | 10 |
| Hintergrund | × 3 | 3 |
| Willenskraft | × 1 | — |

## Cyber-/Bioware

**WVerlust = Willenskraftverlust.** Je nach Preis pro Bonuspunkt:

| Preis je Bonus | Willenskraftverlust |
|---|---|
| 500 ¥ | Bonus × 2 (abgerundet) |
| 2.000 ¥ | Bonus |
| 5.000 ¥ | Bonus ÷ 2 (abgerundet) |
| 10.000 ¥ | Bonus ÷ 3 (abgerundet) |
| 20.000 ¥ | Bonus ÷ 4 (abgerundet) |

Prothese 10.000 ¥ (Verlust 2), Prothesen-Gadget 5.000 ¥. Körperzonen: Kopf, Arme, Torso, Beine — je drei Plätze mit Bonus und Verlust.

## Drohnen und Fahrzeuge

- Beim Kauf wird die **Stufe** festgelegt und frei auf Werte und Fertigkeiten verteilt.
- Gesundheit = Stufe · Widerstand = Schadensreduktion · Angriff = Treffen und Schaden · Agilität = Geschwindigkeit.
- Beim **Riggen** nutzt man die eigenen Werte, aber höchstens bis zur Stufe der Drohne.
- Preise: Fahrzeug Stufe × 5.000 ¥ (ab 5 × 20.000, ab 10 × 40.000), Drohne Stufe × 500 ¥ (ab 5 × 1.000, ab 10 × 5.000).

## Geld

NuYen (¥) ist Weltwährung, 1 ¥ = 1 €. Preise für Ungelistetes: recherchieren oder Spielleitung fragen.

## Willenskraft

- Wird **ausgegeben, um Erfolge zu erzwingen**.
- Wer sie ausgegeben hat, kann sie nicht mehr in **wilde Magie** oder
  NeuroWeaving stecken — es zählt der Rest, nicht der Gesamtwert.
- **Zurück kommt sie** durch **Schlaf**, oder wenn der Charakter seiner
  **Ambition** oder seinem **Verlangen** entsprechend handelt, oder ein **Ziel**
  erreicht. Eintragen tut das die Spielleitung — der Spieler verbraucht sie
  selbst, stellt sie aber nicht wieder her.

## Offen / noch zu klären

- Ob „Magier" und „Technomancer" eigene Charaktertypen sind — **entschieden:** eigenes Feld `weg`, nicht aus Arete > 0 abgeleitet, sonst wäre ein frisch erstellter Magier mit Arete 0 keiner.
- Rüstungsmaxima je Zone (Kopf 2, Torso 4, Beine 2 laut Blatt) — ob das feste Grenzen sind oder nur die Vorlage.
- **Sphären beim Freebee-Kauf**: Zeile 39 nennt nur „Attribut / Arete NeuroWeaving 5", Zeile 27 stellt Sphären
  aber zu den Fertigkeiten. Umgesetzt ist vorerst der Fertigkeitspreis (2, höchstens +1).
- **Hintergründe und Erfahrungspreise** — siehe oben, beides erfunden statt belegt.
