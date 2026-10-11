"""Regressionstest: Ideenschmiede-Entwürfe (istEntwurf=true) dürfen nicht in
der normalen Gegenstände-Übersicht auftauchen.

Bug (gefunden 11.10.2026): beim Einbau von istEntwurf auf allen Entitäten
(c5b3c9b) wurde der Entwurf-Filter bei Person/Ort/Event/Fraktion/WikiSeite
eingebaut (siehe entities/routes.py::_aufbereiten, wiki/routes.py::seitenbaum,
test_ist_entwurf_filter.py), bei Gegenständen aber vergessen — list_all_items/
list_items gaben ungefiltert alles zurück, was filter_gegenstaende_for_viewer
durchliess (das filtert nur nach Sichtbarkeit, nicht nach Entwurf-Status).
Dadurch erschienen SL-seitig Ideenschmiede-Entwürfe in der normalen
Gegenstandsübersicht. get_item (Einzelabruf) filtert bewusst NICHT — die
Ideenschmiede lädt Entwürfe fürs Detail-Popup genau darüber.
"""

import asyncio

import pytest

from app.auth.dependencies import Viewer
from app.items import repository
from app.items.routes import list_all_items, list_items


def _item(id_, name, ist_entwurf):
    return {
        "id": id_,
        "name": name,
        "istEntwurf": ist_entwurf,
        "sichtbarkeit": "GM",
        "sichtbarFuer": [],
        "ownerId": None,
        "ownerName": None,
        "ownerPersonType": None,
    }


@pytest.fixture
def gm_viewer():
    return Viewer(role="GM", person_id=None)


def test_list_all_items_blendet_entwuerfe_aus(monkeypatch, gm_viewer):
    gegenstaende = [
        _item("1", "Entwurf-Schwert", True),
        _item("2", "Echtes-Schwert", False),
        _item("3", "Alt-Schwert", None),  # Bestandsdaten ohne das Feld
    ]

    async def fake_list_alle(_campaign_id):
        return gegenstaende

    monkeypatch.setattr(repository, "list_alle_gegenstaende", fake_list_alle)

    result = asyncio.run(list_all_items("test-campaign", viewer=gm_viewer))
    namen = [g["name"] for g in result]
    assert "Entwurf-Schwert" not in namen
    assert "Echtes-Schwert" in namen
    assert "Alt-Schwert" in namen


def test_list_items_blendet_entwuerfe_aus(monkeypatch, gm_viewer):
    gegenstaende = [
        _item("1", "Entwurf-Pistole", True),
        _item("2", "Echte-Pistole", False),
    ]

    async def fake_list(_campaign_id, _person_id):
        return gegenstaende

    monkeypatch.setattr(repository, "list_gegenstaende", fake_list)

    result = asyncio.run(list_items("test-campaign", "person-1", viewer=gm_viewer))
    namen = [g["name"] for g in result]
    assert "Entwurf-Pistole" not in namen
    assert "Echte-Pistole" in namen
