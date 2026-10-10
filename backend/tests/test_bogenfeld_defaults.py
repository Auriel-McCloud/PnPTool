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


def test_mit_defaults_ersetzt_none_tutorial_shop_felder():
    """Bestands-Personen ohne Tutorial-/Rassenfeature-Properties (None aus
    Neo4j) dürfen GET /personen nicht mit int_type/bool_type reissen.

    Live 10.10.2026: die Ideenschmiede zeigte „Fehler beim Laden der Entwürfe“,
    weil sie Personen mitlädt und PersonResponse kapitalBasis,
    tutorialAusgegeben, gratisGegenstandErhalten, rassenFeatureGenutzt als
    int/bool verlangt — Pydantic-Default greift nicht bei explizitem None.
    """
    from app.entities.schemas import PersonResponse

    roh = {
        "id": "p1",
        "name": "Altbestand",
        "personType": "NPC",
        "description": "",
        "notes": "",
        "sichtbarkeit": "GM",
        "sichtbarFuer": [],
        "notizenSichtbarkeit": "GM",
        "notizenSichtbarFuer": [],
        "kapitalBasis": None,
        "tutorialAusgegeben": None,
        "gratisGegenstandErhalten": None,
        "rassenFeatureGenutzt": None,
    }
    daten = _mit_defaults(roh)
    assert daten["kapitalBasis"] == 0
    assert daten["tutorialAusgegeben"] == 0
    assert daten["gratisGegenstandErhalten"] is False
    assert daten["rassenFeatureGenutzt"] is False
    PersonResponse.model_validate(daten)


def test_person_response_int_und_bool_felder_haben_bogen_defaults():
    """Namenskonvention 'ist*' deckt kapitalBasis/tutorialAusgegeben/
    gratisGegenstandErhalten/rassenFeatureGenutzt nicht ab — jedes int/bool
    in PersonResponse, das aus PERSON_FIELDS kommt, braucht denselben Netz."""
    from app.entities.schemas import PersonResponse

    fehlend = []
    person_felder = set(PERSON_FIELDS)
    for name, info in PersonResponse.model_fields.items():
        if name not in person_felder:
            continue
        if info.annotation in (int, bool) and name not in _BOGEN_DEFAULTS:
            fehlend.append(name)
    assert not fehlend, f"PersonResponse int/bool ohne _BOGEN_DEFAULTS: {fehlend}"
