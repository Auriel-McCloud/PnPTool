# NeotopiA – Charakterblatt (Sheet 1: Charakterblatt)

Transkription des Excel-Sheets `Charakterblatt` (A1:N117) aus `Neotopia.xlsx` (Stand der Quelle: 29.08.2026). Diese Datei ersetzt das Sheet als Index-Quelle — bei Widersprüchen gilt weiterhin das Excel bzw. Mark.

## Kopfbereich
- Name / Konzept / Alter
- Rasse / Ambition / Verlangen
- Spieler / Ziel / Kapital-Schulden (¥)

## Attribute (6-Punkte-Skala, drei Spalten)

| Körperlich | Gesellschaftlich | Geistig |
|---|---|---|
| Körperkraft | Charisma | Intelligenz |
| Geschicklichkeit | Manipulation | Geistesschärfe |
| Widerstandsfähigkeit | Fassung | Entschlossenheit |

Jedes Attribut hat 6 Kästchen zum Ankreuzen.

## Ressourcen-Leisten (je 10 Kästchen, in 5+5 gruppiert)

- **Gesundheit** (links) / **I.C.E. (Cyber Wall)** (rechts)
- **Arete != NeuroWeaving** (links) / **Willenskraft** (rechts)

(Anm.: „Arete != NeuroWeaving" steht wörtlich so im Blatt — die beiden Wege schließen sich gegenseitig aus, siehe `Neotopia_Regeln.md`.)

## Fähigkeiten (Probe = Attribut + Fähigkeit), 5-Punkte-Skala, drei Spalten zu je 10

| Spalte 1 | Spalte 2 | Spalte 3 |
|---|---|---|
| Diebeshandwerk | Anführen | Ermitteln |
| Fahren | Ausflüchte | Finanzen |
| Handgemenge | Darbietung | Geisteswissenschaften |
| Handwerk | Einschüchtern | Medizin |
| Heimlichkeit | Etiketten | Naturwissenschaften |
| Nahkampf | Menschenkenntnis | Okkultismus |
| Schusswaffen | Szenenkenntnis | Politik |
| Sportlichkeit | Tierkunde | Technologie |
| Überleben | Überzeugen | Wahrnehmung |
| Riggen | Maker (Hardware) | Matrix |

30 Fähigkeiten gesamt (siehe auch `backend/app/traits/seed.py` sowie `Neotopia_Attribute_und_Fertigkeiten.md`/`Master/` für die Beschreibungstexte).

## NeuroWeaving (5-Punkte-Skala)

Brute Force · Schleichen · Daten Verarbeiten · Kompilieren

## Sphären (5-Punkte-Skala, drei Spalten)

| Spalte 1 | Spalte 2 | Spalte 3 |
|---|---|---|
| Korrespondenz | Leben | Ursprung |
| Entropie | Materie | Geister |
| Kräfte | Gedanken | Zeit |

## Cyber/Bio-Ware

Vier Körperregionen, jeweils 3 Implantat-Zeilen mit **Bonus** und **WVerlust** (je 5 Kästchen):
- Kopf, Arme (nebeneinander)
- Torso, Beine (nebeneinander)

## Ausrüstung

**Rüstung** (Bonus-Kästchen je Körperteil):
- Kopf: 2
- Torso: 4
- Beine: 2

**Waffen** (parallel dazu, bis zu 3 Slots): Schadens-Bonus (7 Kästchen) + Schadensart-Feld je Slot.

## Gegenstände

- **Am Körper:** 4 Freitextzeilen
- **Im Versteck:** 4 Freitextzeilen
- **Notizen:** Freitextfeld
- **Portrait:** Bildfeld

## Mitgeführte Drohne/Fahrzeug/Sprite/Geist (unterer Blattbereich, Zeile 96–117)

Eine eingebettete Kurzversion des Drohnen/Fahrzeug-Blatts (siehe `Neotopia_Drohnen_Fahrzeuge.md`) direkt auf dem Charakterblatt:
- Beziehung (Freitext)
- Stufe: 15 Kästchen in drei 5er-Gruppen
- Widerstand, Angriff, Agilität: je 5 Kästchen
- Fähigkeiten: 4 Zeilen à 5 Kästchen (frei benennbar)
- Gegenstand: Schadens-Bonus (7 Kästchen) + Schadensart
