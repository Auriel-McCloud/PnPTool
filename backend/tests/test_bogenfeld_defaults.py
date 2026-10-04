"""Regressionstest für den Stolperstein 'fehlender Bogenfeld-Default':
ein neues Boolean-Feld in ORT_FIELDS/PERSON_FIELDS ohne Eintrag in
_BOGEN_DEFAULTS lässt GET-Listenrouten für Bestandsdaten mit einem
bool_type-Validierungsfehler abstürzen (siehe istShop, 04.10.2026 live
aufgetreten: Neo4j liefert None für Knoten ohne das Property, Pydantic
wendet den Feld-Default aber nur an, wenn der Key GANZ FEHLT, nicht wenn
er explizit None ist).
"""

from app.entities.repository import _BOGEN_DEFAULTS, _mit_defaults, ORT_FIELDS, PERSON_FIELDS


def test_istshop_hat_einen_default():
    """Direkter Regressionstest für den konkreten Vorfall (04.10.2026)."""
    assert "istShop" in _BOGEN_DEFAULTS
    assert _BOGEN_DEFAULTS["istShop"] is False


def test_mit_defaults_ersetzt_none_istshop_mit_false():
    roh = {"id": "o1", "name": "Hafen", "istShop": None}
    daten = _mit_defaults(roh)
    assert daten["istShop"] is False


def test_jedes_boolsche_feld_in_ort_und_person_hat_einen_bogen_default():
    """Breiterer Schutz: jedes Feld in ORT_FIELDS/PERSON_FIELDS, das mit
    'ist' beginnt (Namenskonvention für Boolean-Flags in diesem Projekt),
    muss einen Default in _BOGEN_DEFAULTS haben — sonst reisst ein
    Bestandsdatensatz ohne das Property die ganze Liste mit 500/422 runter."""
    fehlend = []
    for feld in {*ORT_FIELDS, *PERSON_FIELDS}:
        if feld.startswith("ist") and feld not in _BOGEN_DEFAULTS:
            fehlend.append(feld)
    assert not fehlend, f"Boolsche Felder ohne _BOGEN_DEFAULTS-Eintrag: {fehlend}"
