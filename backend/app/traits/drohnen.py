"""Riggerkonsole & aktive Slots (25.10.2026).

Siehe docs/wiki/concepts/drohnen-fahrzeuge.md. Eine Riggerkonsole
(`app/items/schemas.py::maxDrohnen`) begrenzt, wie viele Drohnen/Fahrzeuge
ihr Besitzer gleichzeitig aktiv verbunden haben kann. Reine Zählregel — wer
schon verbunden ist, bleibt verbunden, auch wenn die Konsole später
ausgetauscht wird und der neue Deckel niedriger ausfällt (kein nachträgliches
Zwangs-Deaktivieren, siehe `kann_aktivieren`).
"""


def kann_aktivieren(aktuell_aktive: int, max_drohnen: int) -> bool:
    """Darf eine weitere Drohne/ein weiteres Fahrzeug aktiviert werden?

    `aktuell_aktive` zählt NICHT die Drohne, die gerade aktiviert werden
    soll (die ist ja noch inaktiv) — ein Aufrufer mit z.B. 2 von 2 aktiven
    Slots bekommt hier `False`, mit 1 von 2 `True`.
    """
    return max(0, aktuell_aktive) < max(0, max_drohnen)


def kann_bezahlen(preis: int, rigger_kapital: int) -> bool:
    """Reicht das Kapital DES RIGGERS für einen Nuyen-Punktkauf an seiner
    Drohne/seinem Fahrzeug?

    Mark, 25.10.2026 (offene Frage aus Phase 2 beantwortet): "Der Rigger
    zahlt es aus seinem Kapitel, die Drohne hat keins!" — es gibt also KEIN
    eigenes Kapital-Feld am Drohnen-/Fahrzeug-Knoten, jeder Kauf zieht
    ausschließlich von `kapitalBasis` des Rigger-Person-Knotens ab. Eigene,
    benannte Funktion statt eines Inline-Vergleichs im Routenhandler, damit
    diese Entscheidung im Code sichtbar und einzeln testbar bleibt.
    """
    return max(0, preis) <= max(0, rigger_kapital)


# Eine Drohne riggt sich nicht selbst — die Fertigkeit "Riggen" beschreibt,
# wie ein MENSCH eine Drohne fernsteuert, nicht wie eine Drohne sich selbst
# steuert. Mark, 26.10.2026: komplett aus der Drohnen-Umbauen-Liste streichen
# (anders als die übrige volle Fertigkeitenliste, siehe
# docs/wiki/concepts/drohnen-fahrzeuge.md "Fertigkeiten" — das bleibt ein
# bewusster EINZELFALL-Ausschluss, kein genereller Kategorie-Filter).
DROHNE_GESPERRTE_FERTIGKEITEN = {"Riggen"}

# Fertigkeiten, die beim Drohnen-Umbau standardmässig OBEN/hervorgehoben
# stehen (Mark, 26.10.2026) — alle übrigen (inkl. campaign-eigener
# Zusatzfertigkeiten) landen hinter einem "weitere Fertigkeiten"-Umschalter,
# für den seltenen Sonderbau. "Sportlichkeit" heisst an der Drohne nur ANDERS
# BESCHRIFTET "Ausweichen" (Mark: nur bei Drohnen, bei Menschen bleibt der
# Name) — das ist reine Anzeige im Frontend, die gespeicherte Fertigkeit
# bleibt "Sportlichkeit".
DROHNE_WICHTIGE_FERTIGKEITEN = ["Schusswaffen", "Nahkampf", "Wahrnehmung", "Sportlichkeit"]

# Reine Anzeige-Umbenennung nur am Drohnen-/Fahrzeug-Blatt, siehe oben.
DROHNE_FERTIGKEIT_LABEL = {"Sportlichkeit": "Ausweichen"}

# Maschinenteil-Qualitätsstufen (26.10.2026, Material statt Nuyen beim
# Drohnen-Umbau): minderwertig taugt nur für Reparatur (nicht hier),
# normal deckt Fertigkeiten/Zusatzfertigkeiten, hochwertig zusätzlich
# Attribute — docs/wiki/concepts/drohnen-fahrzeuge.md, Abschnitt "Reparatur".
_MASCHINENTEIL_KATEGORIEN = {
    "hochwertig": {"AttributDrohne", "AttributDrohneAussenhuelle", "Fertigkeit", "Zusatzfertigkeit"},
    "normal": {"Fertigkeit", "Zusatzfertigkeit"},
    "minderwertig": set(),
}


def maschinenteil_reicht(qualitaet: str, category: str) -> bool:
    """Deckt diese Maschinenteil-Qualität einen Steigerungskauf dieser
    Kategorie ab? Höhere Stufe deckt alles, was eine niedrigere auch deckt."""
    return category in _MASCHINENTEIL_KATEGORIEN.get(qualitaet, set())


def benoetigte_erfolge_maker_probe(aktueller_wert: int) -> int:
    """Wie viele Erfolge die Maker-Probe für einen Material-Umbau braucht.

    Mark, 26.10.2026: "die Anzahl der Erfolge die er benötigt ist die
    Anzahl der vorhandenen Punkte in dem Skill/Attribut +1" — ein frischer
    Punkt (aktuell 0) braucht nur 1 Erfolg, ein schon hoher Wert entsprechend
    mehr. Gilt nur für den Material-Pfad (Maker baut/modifiziert); der
    ¥-Pfad (Auftrag an einen Profi) würfelt nicht.
    """
    return max(0, aktueller_wert) + 1
