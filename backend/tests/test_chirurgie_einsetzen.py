"""Chrom einsetzen darf nicht an einem kaputten get_node-Aufruf scheitern.

Bug: der Weg-Check in chirurgie_durchfuehren rief get_node(campaign_id,
besitzer_id) auf. Die echte Signatur ist (label, fields, campaign_id,
node_id) — Python meldet dann genau „missing 2 required positional
arguments: 'campaign_id' and 'node_id'“. Jeder Einbau knallte, nicht nur
der Magier-/Neuroweaver-Sonderfall.
"""

import asyncio

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Viewer
from app.items import repository
from app.items.routes import ChirurgieRequest, chirurgie_durchfuehren
import app.items.routes as routes


def _item(**kwargs):
    basis = {
        "id": "item-1",
        "name": "Reflexbooster",
        "typ": "Cyberware",
        "verbaut": False,
        "koerperzone": "",
        "slot": None,
    }
    basis.update(kwargs)
    return basis


def _patch(monkeypatch, *, weg="KEINER", typ="Cyberware"):
    aufrufe = []

    async def fake_get_gegenstand(_campaign_id, _item_id):
        return _item(typ=typ)

    async def fake_owner(_campaign_id, _item_id):
        return "person-1"

    async def fake_get_node(label, fields, campaign_id, node_id):
        aufrufe.append((label, fields, campaign_id, node_id))
        return {"weg": weg}

    async def fake_setze_verbaut(_campaign_id, _item_id, verbaut):
        return _item(typ=typ, verbaut=verbaut)

    monkeypatch.setattr(repository, "get_gegenstand", fake_get_gegenstand)
    monkeypatch.setattr(repository, "get_owner_person_id", fake_owner)
    monkeypatch.setattr(routes, "get_node", fake_get_node)
    monkeypatch.setattr(repository, "setze_verbaut", fake_setze_verbaut)
    return aufrufe


def _einsetzen(typ="Cyberware"):
    return asyncio.run(
        chirurgie_durchfuehren(
            "camp-1",
            "item-1",
            ChirurgieRequest(einsetzen=True),
            viewer=Viewer(role="PLAYER", person_id="person-1"),
        )
    )


def test_cyberware_einsetzen_laedt_die_person_vollstaendig(monkeypatch):
    aufrufe = _patch(monkeypatch)
    ergebnis = _einsetzen()
    assert ergebnis["verbaut"] is True
    assert aufrufe == [("Person", routes.PERSON_FIELDS, "camp-1", "person-1")]


def test_magier_darf_keine_bioware_einsetzen(monkeypatch):
    _patch(monkeypatch, weg="MAGIER", typ="Bioware")
    with pytest.raises(HTTPException) as fehler:
        _einsetzen("Bioware")
    assert fehler.value.status_code == 409
    assert "Bioware" in fehler.value.detail


def test_neuroweaver_darf_keine_hexware_einsetzen(monkeypatch):
    _patch(monkeypatch, weg="NEUROWEAVER", typ="Hexware")
    with pytest.raises(HTTPException) as fehler:
        _einsetzen("Hexware")
    assert fehler.value.status_code == 409
    assert "Hexware" in fehler.value.detail


def test_magier_darf_cyberware_einsetzen(monkeypatch):
    _patch(monkeypatch, weg="MAGIER", typ="Cyberware")
    ergebnis = _einsetzen("Cyberware")
    assert ergebnis["verbaut"] is True
