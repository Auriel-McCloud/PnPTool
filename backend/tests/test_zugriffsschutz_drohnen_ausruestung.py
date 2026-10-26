"""Bugfix 26.10.2026 (Mark: "ich habe auch nicht die Möglichkeit Waffen
auszurüsten", dann "es müsste die Möglichkeit geben, etwas aus dem
Inventar des Riggers auszurüsten bzw. zu übergeben"): der gebundene Rigger
durfte Gegenstände seiner eigenen Drohne/seines eigenen Fahrzeugs weder
umlegen (`ablage_aendern`) noch zwischen sich und ihr übergeben
(`besitzer_wechseln`) — beide Routen kannten nur "ist das dein eigener
Charakter", nie "ist das deine eigene Drohne". Siehe
`items/routes.py::_eigener_kreis`.

Kein echtes Neo4j, gleiches Muster wie `test_ereignisprotokoll_hooks.py`.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Viewer
from app.items.routes import ablage_aendern, besitzer_wechseln
from app.items.schemas import AblageRequest, ZuweisenRequest

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


def test_natuerliche_ruestung_kann_nicht_uebertragen_werden():
    """Auch die SL darf die Außenhülle nicht per Besitzerwechsel von der
    Drohne losreissen — das ist kein normaler Gegenstand."""
    GM = Viewer(role="GM", person_id=None)
    aussenhuelle = {**_WAFFE, "istNatuerlich": True}
    with patch("app.items.routes.repository.get_gegenstand", AsyncMock(return_value=aussenhuelle)):
        with pytest.raises(HTTPException) as exc:
            _run(besitzer_wechseln("camp", "item-1", ZuweisenRequest(zielPersonId="irgendwer"), GM))
    assert exc.value.status_code == 409

_WAFFE = {
    "id": "item-1",
    "sichtbarkeit": "GM",
    "sichtbarFuer": [],
}
_DROHNE_PERSON = {"istDrohne": True, "personType": "NPC"}


def test_rigger_darf_eigenen_gegenstand_an_eigene_drohne_uebergeben():
    with (
        patch("app.items.routes.repository.get_gegenstand", AsyncMock(return_value=_WAFFE)),
        patch("app.items.routes.get_node", AsyncMock(return_value=_DROHNE_PERSON)),
        patch("app.items.routes.repository.get_owner_id", AsyncMock(return_value="rigger-1")),
        patch("app.items.routes.drohne_rigger", AsyncMock(return_value="rigger-1")),
        patch(
            "app.items.routes.repository.transfer_owner",
            AsyncMock(return_value={**_WAFFE, "besitzerId": "drohne-1"}),
        ) as transfer_owner,
        patch("app.items.routes.hooks.gegenstand", AsyncMock()),
    ):
        ergebnis = _run(
            besitzer_wechseln("camp", "item-1", ZuweisenRequest(zielPersonId="drohne-1"), RIGGER)
        )
    transfer_owner.assert_called_once_with("camp", "item-1", "drohne-1")
    assert ergebnis["besitzerId"] == "drohne-1"


def test_rigger_darf_nicht_fremde_gegenstaende_verschieben():
    """Der Gegenstand gehört jemand anderem — auch wenn das Ziel die eigene
    Drohne ist, darf der Rigger ihn nicht an sich reissen."""
    with (
        patch("app.items.routes.repository.get_gegenstand", AsyncMock(return_value=_WAFFE)),
        patch("app.items.routes.get_node", AsyncMock(return_value=_DROHNE_PERSON)),
        patch("app.items.routes.repository.get_owner_id", AsyncMock(return_value="jemand-anders")),
        patch("app.items.routes.drohne_rigger", AsyncMock(return_value="rigger-1")),
    ):
        with pytest.raises(HTTPException) as exc:
            _run(besitzer_wechseln("camp", "item-1", ZuweisenRequest(zielPersonId="drohne-1"), RIGGER))
    assert exc.value.status_code == 404


def test_rigger_darf_nicht_an_fremde_drohne_uebergeben():
    """Eigener Gegenstand, aber das Ziel ist die Drohne eines anderen Riggers."""
    with (
        patch("app.items.routes.repository.get_gegenstand", AsyncMock(return_value=_WAFFE)),
        patch("app.items.routes.get_node", AsyncMock(return_value=_DROHNE_PERSON)),
        patch("app.items.routes.repository.get_owner_id", AsyncMock(return_value="rigger-1")),
        patch("app.items.routes.drohne_rigger", AsyncMock(return_value="anderer-rigger")),
    ):
        with pytest.raises(HTTPException) as exc:
            _run(
                besitzer_wechseln(
                    "camp", "item-1", ZuweisenRequest(zielPersonId="fremde-drohne"), RIGGER
                )
            )
    assert exc.value.status_code == 404


def test_gm_darf_weiterhin_beliebig_uebergeben():
    """Gegenprobe: die SL bleibt von der neuen Einschränkung unberührt."""
    GM = Viewer(role="GM", person_id=None)
    with (
        patch("app.items.routes.repository.get_gegenstand", AsyncMock(return_value=_WAFFE)),
        patch("app.items.routes.get_node", AsyncMock(return_value=_DROHNE_PERSON)) as get_node,
        patch("app.items.routes.repository.get_owner_id", AsyncMock(return_value="jemand-anders")),
        patch("app.items.routes.drohne_rigger", AsyncMock()) as drohne_rigger,
        patch(
            "app.items.routes.repository.transfer_owner",
            AsyncMock(return_value={**_WAFFE, "besitzerId": "drohne-1"}),
        ),
        patch("app.items.routes.hooks.gegenstand", AsyncMock()),
    ):
        ergebnis = _run(
            besitzer_wechseln("camp", "item-1", ZuweisenRequest(zielPersonId="drohne-1"), GM)
        )
    drohne_rigger.assert_not_called()
    assert ergebnis["besitzerId"] == "drohne-1"
