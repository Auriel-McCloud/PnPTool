"""Spieler-Notizen: privates Pad, nur der eigene Zugang sieht sie."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.main import app


def _run(coro):
    return asyncio.run(coro)


def test_leerer_titel_wird_abgelehnt():
    from app.spielernotizen.schemas import SpielerNotizCreate

    with pytest.raises(ValidationError):
        SpielerNotizCreate(titel="   ")


def test_notizen_routen_sind_registriert():
    pfade = app.openapi()["paths"]
    assert "/api/spieler/notizen" in pfade
    assert "get" in pfade["/api/spieler/notizen"]
    assert "post" in pfade["/api/spieler/notizen"]
    assert "patch" in pfade["/api/spieler/notizen/{notiz_id}"]
    assert "delete" in pfade["/api/spieler/notizen/{notiz_id}"]


SPIELER = {
    "id": "s1",
    "campaignId": "c1",
    "benutzername": "aria",
    "campaignName": "Test",
    "personId": "p1",
    "personName": "Aria",
}


def test_liste_fragt_nur_den_eigenen_zugang():
    from app.spielernotizen import routes

    eigene = [{"id": "n1", "titel": "Bar", "inhalt": "", "erstelltAm": "t", "geaendertAm": "t"}]
    with patch("app.spielernotizen.routes.repository.liste", AsyncMock(return_value=eigene)) as liste:
        ergebnis = _run(routes.liste(spieler=SPIELER))
    liste.assert_awaited_once_with("s1", "c1")
    assert ergebnis[0]["titel"] == "Bar"


def test_fremde_notiz_ist_404():
    from app.spielernotizen import routes
    from app.spielernotizen.schemas import SpielerNotizUpdate

    with patch("app.spielernotizen.routes.repository.aendern", AsyncMock(return_value=None)):
        with pytest.raises(HTTPException) as fehler:
            _run(routes.aendern("fehlt", SpielerNotizUpdate(titel="x"), spieler=SPIELER))
    assert fehler.value.status_code == 404


def test_export_weissliste_kennt_spielernotiz():
    from app.campaigns.export_import import KNOWN_LABELS, KNOWN_REL_TYPES

    assert "SpielerNotiz" in KNOWN_LABELS
    assert "HAT_NOTIZ" in KNOWN_REL_TYPES
