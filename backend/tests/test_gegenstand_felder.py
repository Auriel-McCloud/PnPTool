"""Beim Anlegen eines Gegenstands darf kein Feld still verlorengehen.

Gefunden am 03.09.2026: `_create_data` in `app/items/routes.py` zählt die
Felder **einzeln** auf. `initiativeBonus` fehlte dort — der Wert kam nie in
der Datenbank an, obwohl Schema, Repository und Cypher korrekt waren. Ein
Reflex-Booster erhöhte die Initiative also nicht.

Dieselbe Lücke betraf `wVerlust`, `koerperzone`, `riggerBonus` und ein Dutzend
weitere: sie liessen sich nur per PATCH nachtragen.

Dieser Test vergleicht das Schema mit der Übergabe und schlägt an, sobald ein
neues Feld vergessen wird.
"""

from app.items.routes import _create_data
from app.items.schemas import GegenstandCreate

# Felder, die _create_data bewusst NICHT durchreicht, mit Begründung.
BEWUSST_AUSGELASSEN = {
    # Wird aus der Rolle des Aufrufers bestimmt, nicht aus dem Body.
    "istVorlage",
    # Werden von der Route aus Besitzer und Sichtbarkeitsregeln berechnet.
    "sichtbarkeit",
    "sichtbarFuer",
    # Der Besitzer steckt im Pfad, nicht im Datensatz.
    "besitzerId",
    # Ergibt sich aus dem Typ, wenn nichts anderes angegeben ist.
    "istBehaelter",
}


def test_create_data_reicht_jedes_schemafeld_durch():
    body = GegenstandCreate(name="Prüfstück")
    daten = _create_data(body, ist_vorlage=False, sichtbarkeit="GM", sichtbar_fuer=[])

    schemafelder = set(GegenstandCreate.model_fields)
    uebergeben = set(daten)
    fehlend = schemafelder - uebergeben - BEWUSST_AUSGELASSEN

    assert not fehlend, (
        "Diese Felder gehen beim Anlegen verloren und lassen sich nur per "
        f"PATCH nachtragen: {sorted(fehlend)}"
    )


def test_initiative_bonus_kommt_an():
    # Der konkrete Fall, der den Fehler aufgedeckt hat.
    body = GegenstandCreate(name="Reflex Booster", initiativeBonus=3)
    daten = _create_data(body, ist_vorlage=False, sichtbarkeit="GM", sichtbar_fuer=[])
    assert daten["initiativeBonus"] == 3


def test_chromwerte_kommen_an():
    body = GegenstandCreate(name="Chrom", wVerlust=0.67, koerperzone="Kopf", slot=2)
    daten = _create_data(body, ist_vorlage=False, sichtbarkeit="GM", sichtbar_fuer=[])
    assert daten["wVerlust"] == 0.67
    assert daten["koerperzone"] == "Kopf"
    assert daten["slot"] == 2
