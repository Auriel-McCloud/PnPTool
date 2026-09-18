# NeotopiA – Referenz-Index (`docs/reference/`)

Dieser Ordner enthält das Rohmaterial und die aufbereiteten Regeltexte für NeotopiA.
**`Neotopia.xlsx` selbst wird nicht indiziert** — der komplette Inhalt der drei Excel-Sheets ist unten vollständig in Markdown transkribiert (Stand der xlsx: 29.08.2026).

## Aus Neotopia.xlsx transkribiert (Sheets: Charakterblatt, DrohneFahrzeug, Regeln)

| Datei | Inhalt |
|---|---|
| [`Neotopia_Charakterblatt.md`](./Neotopia_Charakterblatt.md) | Sheet 1 „Charakterblatt": Felder, Attribute, Fähigkeiten, Sphären/NeuroWeaving, Cyberware-Slots, Ausrüstung, eingebettetes Drohnen-Mini-Blatt |
| [`Neotopia_Drohnen_Fahrzeuge.md`](./Neotopia_Drohnen_Fahrzeuge.md) | Sheet 2 „DrohneFahrzeug": 4 wiederholte Blöcke für Drohnen/Fahrzeuge/Sprites/Geister |
| [`Neotopia_Charaktererschaffung.md`](./Neotopia_Charaktererschaffung.md) | Sheet 3 „Regeln", Zeilen 1–45: Rassen, Attributverteilung, Fertigkeitspakete, Freebees, Startkapital |
| [`Neotopia_Regeln.md`](./Neotopia_Regeln.md) | Sheet 3 „Regeln", Zeilen 47–108: Würfelsystem, Kampf, Magie/Arete, Sphären, NeuroWeaving, Riggen/Decking |
| [`Neotopia_Gegenstaende.md`](./Neotopia_Gegenstaende.md) | Sheet 3 „Regeln", Zeilen 109–447: Preise, Rüstung, Waffen, Technik, Drogen, SL-Ideen-Gadgets — **inkl. 2 versteckter Easter Eggs** (🥚 markiert) |

## Bereits vorhandene aufbereitete Texte

| Datei/Ordner | Inhalt |
|---|---|
| `Neotopia_Attribute_und_Fertigkeiten.md` | Fertige Tooltip-Texte für Attribute (Kurz- + Langbeschreibung), fürs Charakterblatt-UI |
| `Master/` | Finale Tooltip-Texte für alle Fertigkeiten + Sphären (eine .md pro Eintrag) — aktueller Stand |
| `Fertigkeiten/` | Rohtext-Entwürfe der Fertigkeiten-Tooltips (Vorstufe zu `Master/`) |
| `Sphären/` | Rohtext-Quellen der Sphären-Beschreibungen (Vorstufe zu `Master/`, aus M20 adaptiert) |
| `spähren.txt` | Volltext-Rohmaterial zu den Sphären aus dem Mage-M20-Regelwerk |
| `Regel Details - infotipp optionen.txt` | Attributsskala-Legende + Vorlagen für Ambition/Verlangen (aus Hunter/Vampire V5) |
| `hintergründe.txt` | Hintergründe/Merit-ähnliche Vorlagen (aus M20) |
| `gemini-code-1789580200097.md` | Alternativer Tooltip-Entwurf (von Gemini) für Attribute |

## Quelle & Vorrang

`Neotopia.xlsx` bleibt die kanonische Rohdaten-Quelle (3 Sheets: Charakterblatt, DrohneFahrzeug, Regeln). Bei Widersprüchen zwischen Excel und den Markdown-Dateien hier gilt das Excel bzw. Mark — bei Änderungen im Excel bitte die betroffene .md-Datei nachziehen.

Siehe auch [`../regeln-neotopia.md`](../regeln-neotopia.md) — die für die Tool-Implementierung aufbereitete, geglättete Regelversion (mit Formelkorrekturen, z. B. der neueren Gesundheits-Formel).
