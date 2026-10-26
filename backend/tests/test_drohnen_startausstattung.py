"""Drohnen/Fahrzeuge bekommen bei der Erstellung automatisch ihre
Grundausstattung (26.10.2026, Mark nach dem ersten Spieltisch-Test):
3 Lebenspunkte-Basiswert + eine Außenhülle-Rüstung nach dem Natürliche-
Rüstung-Prinzip. Siehe `entities/routes.py::_drohnen_startausstattung`.

Kein echtes Neo4j, gleiches Muster wie `test_ereignisprotokoll_hooks.py`:
`asyncio.run()` + `unittest.mock.patch` auf die Repository-Funktionen.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from app.entities.routes import _drohnen_startausstattung


def _run(coro):
    return asyncio.run(coro)


def test_setzt_gesundheitgrundwert_auf_drei_ohne_override():
    person = {"id": "drohne-1", "gesundheitGrundwert": -1}
    with (
        patch("app.entities.routes.repository.update_node", AsyncMock(return_value={**person, "gesundheitGrundwert": 3})) as update,
        patch("app.entities.routes.items_repository.create_gegenstand", AsyncMock(return_value={"id": "item-1"})),
    ):
        ergebnis = _run(_drohnen_startausstattung("camp", person))
    update.assert_called_once()
    assert update.call_args[0][4] == {"gesundheitGrundwert": 3}
    assert ergebnis["gesundheitGrundwert"] == 3


def test_laesst_explizit_gesetzten_grundwert_unangetastet():
    person = {"id": "drohne-2", "gesundheitGrundwert": 10}
    with (
        patch("app.entities.routes.repository.update_node", AsyncMock()) as update,
        patch("app.entities.routes.items_repository.create_gegenstand", AsyncMock(return_value={"id": "item-1"})),
    ):
        ergebnis = _run(_drohnen_startausstattung("camp", person))
    update.assert_not_called()
    assert ergebnis["gesundheitGrundwert"] == 10


def test_erzeugt_natuerliches_aussenhuelle_item_ausgeruestet():
    person = {"id": "drohne-3", "gesundheitGrundwert": -1}
    with (
        patch("app.entities.routes.repository.update_node", AsyncMock(return_value=person)),
        patch("app.entities.routes.items_repository.create_gegenstand", AsyncMock(return_value={"id": "item-1"})) as create,
    ):
        _run(_drohnen_startausstattung("camp", person))
    create.assert_called_once()
    campaign_id, owner_id, data = create.call_args[0]
    assert campaign_id == "camp"
    assert owner_id == "drohne-3"
    assert data["istNatuerlich"] is True
    assert data["ablage"] == "AUSGERUESTET"
    assert data["name"] == "Außenhülle"
    assert data["sichtbarkeit"] == "GM"
