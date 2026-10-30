"""Bugfix 26.10.2026 (Mark): Charakterblatt-Reiter einer Drohne/eines
Fahrzeugs blieb fuer den gebundenen Rigger ewig bei "Lade Charakterblatt…"
stehen — `traits/routes.py` kannte bislang nur `person_id == viewer.person_id`
als Spieler-Erlaubnis, eine Drohne ist aber ein EIGENER Person-Knoten, nie
identisch mit dem des Riggers. Siehe `traits/routes.py::_darf_person_sehen`.

Bugfix 30.10.2026 (Mark): derselbe Fehler bei Beschwörungs-Crittern — das
"Beschworener Critter"-Fenster hing nach dem Beschwören ewig bei "Lade
Kampfwerte…", weil `_darf_person_sehen` das `istCritter`-Band nicht kannte.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from app.auth.dependencies import Viewer
from app.traits.routes import _darf_person_sehen

GM = Viewer(role="GM", person_id=None)
SPIELER = Viewer(role="PLAYER", person_id="rigger-1")
FREMDER_SPIELER = Viewer(role="PLAYER", person_id="jemand-anders")


def _run(coro):
    return asyncio.run(coro)


def test_gm_darf_immer():
    assert _run(_darf_person_sehen("camp", "irgendwer", {}, GM)) is True


def test_spieler_darf_eigenen_charakter():
    assert _run(_darf_person_sehen("camp", "rigger-1", {}, SPIELER)) is True


def test_spieler_ohne_bindung_an_fremde_person_nicht():
    # Kein istDrohne/istFahrzeug -> kein BEGLEITET-Lookup noetig, sofort False.
    with patch("app.traits.routes.drohne_rigger", AsyncMock()) as rigger_lookup:
        erlaubt = _run(_darf_person_sehen("camp", "irgendwer", {}, FREMDER_SPIELER))
    assert erlaubt is False
    rigger_lookup.assert_not_called()


def test_gebundener_rigger_darf_seine_drohne_sehen():
    with patch("app.traits.routes.drohne_rigger", AsyncMock(return_value="rigger-1")):
        erlaubt = _run(_darf_person_sehen("camp", "drohne-1", {"istDrohne": True}, SPIELER))
    assert erlaubt is True


def test_gebundener_rigger_darf_sein_fahrzeug_sehen():
    with patch("app.traits.routes.drohne_rigger", AsyncMock(return_value="rigger-1")):
        erlaubt = _run(_darf_person_sehen("camp", "fahrzeug-1", {"istFahrzeug": True}, SPIELER))
    assert erlaubt is True


def test_fremder_spieler_sieht_nicht_die_drohne_eines_anderen():
    with patch("app.traits.routes.drohne_rigger", AsyncMock(return_value="rigger-1")):
        erlaubt = _run(_darf_person_sehen("camp", "drohne-1", {"istDrohne": True}, FREMDER_SPIELER))
    assert erlaubt is False


def test_unverbundene_drohne_bleibt_gesperrt():
    with patch("app.traits.routes.drohne_rigger", AsyncMock(return_value=None)):
        erlaubt = _run(_darf_person_sehen("camp", "drohne-1", {"istDrohne": True}, SPIELER))
    assert erlaubt is False


def test_beschwoerer_darf_seinen_critter_sehen():
    with patch("app.traits.routes.critter_besitzer", AsyncMock(return_value="rigger-1")):
        erlaubt = _run(_darf_person_sehen("camp", "critter-1", {"istCritter": True}, SPIELER))
    assert erlaubt is True


def test_fremder_spieler_sieht_nicht_den_critter_eines_anderen():
    with patch("app.traits.routes.critter_besitzer", AsyncMock(return_value="rigger-1")):
        erlaubt = _run(_darf_person_sehen("camp", "critter-1", {"istCritter": True}, FREMDER_SPIELER))
    assert erlaubt is False


def test_unverbundener_critter_bleibt_gesperrt():
    with patch("app.traits.routes.critter_besitzer", AsyncMock(return_value=None)):
        erlaubt = _run(_darf_person_sehen("camp", "critter-1", {"istCritter": True}, SPIELER))
    assert erlaubt is False
