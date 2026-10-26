"""Bugfix 26.10.2026 (Mark: "ich habe auch nicht die Möglichkeit Waffen
auszurüsten"): der gebundene Rigger durfte Gegenstände seiner eigenen
Drohne/seines eigenen Fahrzeugs nicht umlegen — `ablage_aendern` kannte nur
"ist das dein eigener Charakter", nie "ist das deine eigene Drohne". Siehe
`items/routes.py::ablage_aendern`.

Kein echtes Neo4j, gleiches Muster wie `test_ereignisprotokoll_hooks.py`.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Viewer
from app.items.routes import ablage_aendern
from app.items.schemas import AblageRequest

RIGGER = Viewer(role="PLAYER", person_id="rigger-1")
FREMDER = Viewer(role="PLAYER", person_id="jemand-anders")


def _run(coro):
    return asyncio.run(coro)


def _mocks(besitzer: str | None, besitzer_person: dict | None, rigger_id: str | None):
    return (
        patch("app.items.routes.repository.get_owner_person_id", AsyncMock(return_value=besitzer)),
        patch("app.items.routes.get_node", AsyncMock(return_value=besitzer_person)),
        patch("app.items.routes.drohne_rigger", AsyncMock(return_value=rigger_id)),
    )


def test_fremder_spieler_bekommt_404():
    p1, p2, p3 = _mocks("drohne-1", {"istDrohne": True}, "rigger-1")
    with p1, p2, p3:
        with pytest.raises(HTTPException) as exc:
            _run(ablage_aendern("camp", "item-1", AblageRequest(ablage="RUCKSACK"), FREMDER))
    assert exc.value.status_code == 404


def test_rigger_darf_item_seiner_drohne_umlegen():
    item = {
        "id": "item-1",
        "typ": "Waffe",
        "istNatuerlich": False,
        "verbaut": False,
        "koerperzone": "",
        "slot": None,
        "ruestungKaestchenMax": 0,
        "ruestungKaestchenAktuell": 0,
    }
    p1, p2, p3 = _mocks("drohne-1", {"istDrohne": True}, "rigger-1")
    with (
        p1,
        p2,
        p3,
        patch("app.items.routes.repository.get_gegenstand", AsyncMock(return_value=item)),
        patch("app.items.routes.repository.set_ablage", AsyncMock(return_value={**item, "ablage": "RUCKSACK"})) as set_ablage,
    ):
        ergebnis = _run(ablage_aendern("camp", "item-1", AblageRequest(ablage="RUCKSACK"), RIGGER))
    set_ablage.assert_called_once()
    assert ergebnis["ablage"] == "RUCKSACK"


def test_unverbundener_spieler_sieht_fremde_drohne_nicht():
    """Drohne existiert, aber der anfragende Spieler ist nicht ihr Rigger."""
    p1, p2, p3 = _mocks("drohne-1", {"istDrohne": True}, "rigger-1")
    with p1, p2, p3:
        with pytest.raises(HTTPException) as exc:
            _run(ablage_aendern("camp", "item-1", AblageRequest(ablage="RUCKSACK"), FREMDER))
    assert exc.value.status_code == 404


def test_eigener_charakter_bleibt_unveraendert_erlaubt():
    """Gegenprobe: der bestehende Weg (eigener Charakter) funktioniert
    weiterhin, ohne dass die Drohnen-Erweiterung ihn stört."""
    item = {
        "id": "item-1",
        "typ": "Waffe",
        "istNatuerlich": False,
        "verbaut": False,
        "koerperzone": "",
        "slot": None,
        "ruestungKaestchenMax": 0,
        "ruestungKaestchenAktuell": 0,
    }
    with (
        patch("app.items.routes.repository.get_owner_person_id", AsyncMock(return_value="rigger-1")),
        patch("app.items.routes.get_node", AsyncMock()) as get_node,
        patch("app.items.routes.drohne_rigger", AsyncMock()) as drohne_rigger,
        patch("app.items.routes.repository.get_gegenstand", AsyncMock(return_value=item)),
        patch("app.items.routes.repository.set_ablage", AsyncMock(return_value={**item, "ablage": "RUCKSACK"})),
    ):
        ergebnis = _run(ablage_aendern("camp", "item-1", AblageRequest(ablage="RUCKSACK"), RIGGER))
    get_node.assert_not_called()
    drohne_rigger.assert_not_called()
    assert ergebnis["ablage"] == "RUCKSACK"
