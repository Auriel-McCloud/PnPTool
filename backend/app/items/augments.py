"""Waffen-/Rüstungs-/Drohnen-Augments: montierbare Verbesserungen mit
eigenen Slots statt Körperzonen (29.10.2026, im Chat mit Mark entschieden —
siehe docs/wiki/concepts/augments-ausruestung.md für die volle Herleitung).

Ersetzt den alten, nie gebauten Plan "eigenes Körperzonen-Schema für
Drohnen-Augments" (28.10.2026) komplett: Waffen, Rüstung UND Drohnen/
Fahrzeuge tragen stattdessen alle nur ein `upgradeSlots`-Feld (0-6, SL legt
es pro Stück/pro Drohne individuell fest — "variabel halten", Mark).

Ein Augment ist selbst ein Gegenstand (`istAugment=true`) mit einem eigenen
`traitBoni`-Feld (wiederverwendet, exakt wie bei jedem anderen Gegenstand —
"frei einstellbar, genau wie traitBoni heute", Mark). Montiert wie
Cyberware: physisch, abbaubar, kein Verbrauch. Das Ziel ist aber kein
Körperteil, sondern ein ANDERER Gegenstand (Waffe/Rüstung) ODER eine
Drohne/ein Fahrzeug (Person-Knoten) — die Montage-Kante
(`items/repository.py::MONTIERT_AN`) zeigt deshalb auf einen Knoten
beliebigen Typs, nicht nur auf Gegenstände.

Montieren UND Demontieren brauchen je eine selbstberichtete Maker- oder
Handwerk-Probe (frei wählbar, wie bei der Werkbank-Reparatur). Ein Patzer
beschädigt das Augment (`defekt=true`) statt die Montage einfach nur
scheitern zu lassen — dieselbe Material-Reparatur wie der Rest der
Werkbank (`kampf/ruestung.py::reparatur_benoetigte_erfolge`/
`reparatur_heilung_material`) repariert es wieder, nur mit dem
AUGMENT-LEVEL statt "fehlenden Kästchen" als Zielgröße: wer die Formel
also einmal versteht, versteht beide Reparaturwege.
"""


def augment_level(trait_boni: dict[str, int]) -> int:
    """Wie "mächtig" ein Augment ist — Summe seiner Bonuspunkte.

    Bestimmt sowohl die Montage-Probe-Schwierigkeit (`benoetigte_erfolge_montage`)
    als auch, wie viel Material eine Reparatur nach einem Patzer braucht
    (`kampf/ruestung.py::reparatur_heilung_material`, mit `level` als
    "fehlende Kästchen" aufgerufen).
    """
    return max(0, sum(int(v) for v in trait_boni.values()))


def benoetigte_erfolge_montage(level: int) -> int:
    """Montieren UND Demontieren verlangen dieselbe Schwelle: Level + 1 —
    je stärker das Augment, desto schwieriger ein- oder auszubauen (Mark,
    29.10.2026). Gegenstück zur Reparatur-Formel unten, die bewusst leichter
    ist (Level − 1, Minimum 1, siehe `kampf/ruestung.py::
    reparatur_benoetigte_erfolge` — dieselbe Funktion, hier mit `level`
    statt Materialmenge aufgerufen).
    """
    return max(0, level) + 1


def waffentyp_passt(augment_waffentyp: str, ziel_kampf_fertigkeit: str) -> bool:
    """Ob dieses Augment an diesem Ziel montierbar ist.

    Ein leerer `augment_waffentyp` passt auf ALLES — Waffen jeden Typs,
    Rüstung UND Drohne/Fahrzeug (die beide kein `kampfFertigkeit`-Feld
    haben, `ziel_kampf_fertigkeit` kommt dort leer an). Ein gesetzter
    Waffentyp (Schusswaffen/Nahkampf/Handgemenge, dieselben drei Werte wie
    `items/waffenbonus.py::KampfFertigkeit`) grenzt auf genau diesen
    Waffentyp ein — Rüstung und Drohnen/Fahrzeuge fallen dann automatisch
    heraus, ohne eigene Sonderfall-Prüfung.
    """
    return not augment_waffentyp or augment_waffentyp == ziel_kampf_fertigkeit


# Welche Gegenstands-Typen Augments tragen können (ausserdem Drohnen/
# Fahrzeuge, aber das sind Person-Knoten, siehe Moduldocstring oben).
AUGMENT_TRAEGER_TYPEN = {"Waffe", "Rüstung", "Cyberdeck", "Riggerkonsole"}
