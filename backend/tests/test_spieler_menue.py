"""Spieler-Burgermenü: Layout hängt am eigenen Zugang, nicht am Charakter."""

import asyncio
from unittest.mock import AsyncMock, patch

from app.main import app

SPIELER = {
    "id": "s1",
    "campaignId": "c1",
    "benutzername": "aria",
    "campaignName": "Test",
    "personId": "p1",
    "personName": "Aria",
}


def _run(coro):
    return asyncio.run(coro)


def test_spieler_menue_ist_lesbar_und_schreibbar():
    pfade = app.openapi()["paths"]
    assert "/api/spieler/menue" in pfade
    assert "get" in pfade["/api/spieler/menue"]
    assert "patch" in pfade["/api/spieler/menue"]


def test_lesen_holt_das_layout_des_eigenen_zugangs():
    from app.players import routes

    erwartet = {
        "pc": {"ordnung": ["blatt"], "ausgeblendet": ["wiki"]},
        "tablet": {"ordnung": [], "ausgeblendet": []},
    }
    with patch(
        "app.players.routes.repository.get_menue_layouts",
        AsyncMock(return_value=erwartet),
    ) as holen:
        ergebnis = _run(routes.menue_lesen(spieler=SPIELER))
    holen.assert_awaited_once_with("s1")
    assert ergebnis.pc.ausgeblendet == ["wiki"]


def test_schreiben_speichert_am_eigenen_zugang():
    from app.auth.routes import MenueLayouts, MenueSlot
    from app.players import routes

    body = MenueLayouts(
        pc=MenueSlot(ordnung=["kampf", "blatt"], ausgeblendet=["shop"]),
        tablet=MenueSlot(),
    )
    with patch(
        "app.players.routes.repository.set_menue_layouts",
        AsyncMock(return_value=body.model_dump()),
    ) as schreiben:
        ergebnis = _run(routes.menue_schreiben(body, spieler=SPIELER))
    schreiben.assert_awaited_once_with("s1", body.model_dump())
    assert ergebnis.pc.ordnung == ["kampf", "blatt"]
