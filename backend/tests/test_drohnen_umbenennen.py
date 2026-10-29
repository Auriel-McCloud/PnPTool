"""29.10.2026, Mark: "ich hätte gerne das der Spieler seiner Drohne selbst
einen Namen geben kann, er kann sie gerne jeder zeit umbenennen, es ist ja
auch seine Drohne" — eigener Endpunkt `POST /drohnen/{id}/name`, weil
`PATCH /personen/{id}` (GM-exklusiv) dafür nicht in Frage kommt. Außerdem
deckt Mark denselben Wunsch fürs Umbenennen eines PCs/NPCs durch die SL ab
("bin mit dem Namen jetzt gefangen") — das läuft über das bestehende PATCH,
hier nur die Validierung gegen leere Namen.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from app.auth.dependencies import Viewer
from app.entities.routes import DrohneNameInput, drohne_name_setzen
from app.entities.schemas import PersonUpdate

GM = Viewer(role="GM", person_id=None)
RIGGER = Viewer(role="PLAYER", person_id="rigger-1")
FREMDER_SPIELER = Viewer(role="PLAYER", person_id="jemand-anders")


def _run(coro):
    return asyncio.run(coro)


def test_drohne_name_input_trimmt():
    assert DrohneNameInput(name="  Blinky  ").name == "Blinky"


def test_drohne_name_input_lehnt_leer_ab():
    with pytest.raises(ValidationError):
        DrohneNameInput(name="   ")


def test_person_update_name_trimmt():
    assert PersonUpdate(name="  Neo  ").name == "Neo"


def test_person_update_name_lehnt_leer_ab():
    with pytest.raises(ValidationError):
        PersonUpdate(name="   ")


def test_person_update_ohne_name_bleibt_unberuehrt():
    assert PersonUpdate().name is None


def _mocks(rigger_id):
    drohne = {"id": "drohne-1", "istDrohne": True, "name": "Alt"}
    get_node = AsyncMock(return_value=drohne)
    drohne_rigger = AsyncMock(return_value=rigger_id)
    update_node = AsyncMock(return_value={"id": "drohne-1", "name": "Neu"})
    return get_node, drohne_rigger, update_node


def test_gebundener_rigger_darf_umbenennen():
    get_node, drohne_rigger, update_node = _mocks("rigger-1")
    with patch("app.entities.routes.repository.get_node", get_node), \
         patch("app.entities.routes.repository.drohne_rigger", drohne_rigger), \
         patch("app.entities.routes.repository.update_node", update_node):
        ergebnis = _run(drohne_name_setzen("camp", "drohne-1", DrohneNameInput(name="Neu"), RIGGER))
    assert ergebnis == {"id": "drohne-1", "name": "Neu"}
    update_node.assert_awaited_once()


def test_gm_darf_immer_umbenennen():
    get_node, drohne_rigger, update_node = _mocks("rigger-1")
    with patch("app.entities.routes.repository.get_node", get_node), \
         patch("app.entities.routes.repository.drohne_rigger", drohne_rigger), \
         patch("app.entities.routes.repository.update_node", update_node):
        _run(drohne_name_setzen("camp", "drohne-1", DrohneNameInput(name="Neu"), GM))
    update_node.assert_awaited_once()


def test_fremder_spieler_darf_nicht_umbenennen():
    from fastapi import HTTPException

    get_node, drohne_rigger, update_node = _mocks("rigger-1")
    with patch("app.entities.routes.repository.get_node", get_node), \
         patch("app.entities.routes.repository.drohne_rigger", drohne_rigger), \
         patch("app.entities.routes.repository.update_node", update_node):
        with pytest.raises(HTTPException) as exc:
            _run(drohne_name_setzen("camp", "drohne-1", DrohneNameInput(name="Neu"), FREMDER_SPIELER))
    assert exc.value.status_code == 404
    update_node.assert_not_awaited()
