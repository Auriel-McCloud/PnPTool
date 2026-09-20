# NeotopiA – Charaktererschaffung

Transkription des Abschnitts „Charaktererstellung" aus dem Excel-Sheet `Regeln` (Zeilen 1–45) aus `Neotopia.xlsx` (Stand der Quelle: 29.08.2026). Für die generellen Spielregeln siehe `Neotopia_Regeln.md`, für Gegenstände/Preise `Neotopia_Gegenstaende.md`.

## Attribute verteilen

Jeder Charakter startet mit 1 Punkt in allen Attributen, modifiziert durch die Rasseneigenschaften unten.

### Rassentabelle

**Mensch**

| StartMax | Freie Punkte | Modifikator |
|---|---|---|
| 4 | 7 | frei |
| 4 | 5 | frei |
| 4 | 3 | frei |

**Ork**

| StartMax | Freie Punkte | Modifikator |
|---|---|---|
| 3 | 6 | Intelligenz −1 (0) |
| 5 | 5 | Körperkraft +1 (2) |
| 4 | 3 | frei |

**Elf**

| StartMax | Freie Punkte | Modifikator |
|---|---|---|
| 3 | 5 | Widerstandsfähigkeit −1 (0) |
| 5 | 5 | Charisma +1 (2) |
| 5 | 3 | Geschicklichkeit +1 (2) |

**Zwerg**

| StartMax | Freie Punkte | Modifikator |
|---|---|---|
| 3 | 5 | Charisma −1 (0) |
| 5 | 5 | Widerstandsfähigkeit +1 (2) |
| 5 | 3 | Fassung +1 (2) |

**Troll**

| StartMax | Freie Punkte | Modifikator |
|---|---|---|
| 6 | 5 | Körperkraft +2 (3) |
| 5 | 4 | Widerstandsfähigkeit +1 (2) |
| 3 | 3 | Geistesschärfe −1 (0) |
| 3 | — | Geschicklichkeit −1 (0) |

*Troll hat als einzige Rasse vier Modifikator-Zeilen (zwei Boni, zwei Mali); die vierte Zeile hat im Original keine eigenen freien Punkte (nur Bindestriche im Excel).*

> **Anmerkung zur Transkription:** Das Excel ordnet die drei (bzw. bei Troll vier) Zeilen pro Rasse nicht explizit den Attributgruppen Körperlich/Gesellschaftlich/Geistig zu — die Zuordnung ergibt sich implizit aus dem im Modifikator genannten Attribut. Bei Unklarheiten zählt das Excel bzw. Mark.

### Regeln zur Verteilung

- Die mittlere Spalte ("Freie Punkte") gibt an, wie viele Punkte frei auf die drei Attribut-Spalten Körperlich – Gesellschaftlich – Geistig verteilt werden dürfen.
- Dabei ist frei wählbar, welcher der drei Werte welcher Spalte zugeordnet wird.
  *Beispiel: Der Mensch kann 7 entweder auf Körperliche, Gesellschaftliche oder Geistige Attribute verteilen; dann bleiben noch 5 und 3 für die beiden anderen.*
- Der StartMax-Wert gilt **nicht** für Freebees (Freebees können ihn übersteigen).

## Fertigkeiten

Arete, Sphären bzw. NeuroWeaving zählen als Fähigkeit, werden aber im Normalfall ohne Attribut gewürfelt.

Drei Pakete zur Wahl:

| Paket | Verteilung | Anzahl Fähigkeiten |
|---|---|---|
| Profi | 1 Wert auf 4, 3 Werte auf 3, 3 Werte auf 2, 1 Wert auf 1 | 8 |
| Ausgeglichen | 3 Werte auf 3, 5 Werte auf 2, 7 Werte auf 1 | 15 |
| Jack of all Trades | 1 Wert auf 3, 8 Werte auf 2, 10 Werte auf 1 | 19 |

## Abgeleitete Werte

- **Gesundheit** = 5 + Widerstandskraft
  *(Hinweis: Laut `../regeln-neotopia.md` hat Mark das am 10.09. auf „6 + Widerstandsfähigkeit" erhöht. Im Excel selbst — Stand 29.08. — steht noch die alte Formel mit 5. Das Excel ist hier veraltet, die neuere Regel in `regeln-neotopia.md` hat Vorrang.)*
- **Willenskraft** = Entschlossenheit + Fassung

## Kapital

- **Startkapital:** 10.000 ¥

## Freebees

- **Freebees gesamt:** 15
- **Kosten:**

| Freebee-Kauf | Kosten |
|---|---|
| Attribut / Arete / NeuroWeaving | 5 Punkte (kann StartMax übersteigen) |
| Fertigkeit | 2 Punkte (max. +1) — Fertigkeitsmaximum selbst am 20.09.2026 von 5 auf 6 angehoben, siehe `docs/regeln-neotopia.md` |
| Willenskraft | 1 Punkt |
| Kredit 10.000¥ | 1 Punkt |
| Eigenkapital 10.000¥ | 2 Punkte |

## Hinweise zu Magie/Sphären (im Erschaffungs-Block ebenfalls vermerkt)

- Sphärenstufen: 1 wahrnehmbar · 2 Manipulation bis ~50 cm³ · 3 bis ~4 m³ · 4 bis Hausgröße · 5 „Nach meiner Größe beurteilst du mich, tust du das?"
- NeuroWeaving-Fähigkeiten geben Bonuswürfel und gelten **nicht** als Limitierung wie bei Sphären.
