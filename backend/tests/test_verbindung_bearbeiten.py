"""Verbindung nachträglich ändern: Typ, Beschreibung, Sichtbarkeit."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.main import app


def _run(coro):
    return asyncio.run(coro)


def test_patch_verbindung_ist_registriert():
    pfad = "/api/campaigns/{campaign_id}/verbindungen/{edge_id}"
    methoden = app.openapi()["paths"][pfad]
    assert "patch" in methoden


def test_leerer_typ_wird_abgelehnt():
    from app.entities.schemas import VerbindungUpdate

    with pytest.raises(ValidationError):
        VerbindungUpdate(typ="   ")


def test_update_verbindung_schreibt_typ_und_sichtbarkeit():
    from app.entities import routes
    from app.entities.schemas import VerbindungUpdate

    aktualisiert = {
        "id": "e1",
        "vonKind": "Person",
        "vonId": "a",
        "zuKind": "Fraktion",
        "zuId": "b",
        "typ": "Freund",
        "beschreibung": "Tippfehler weg",
        "seit": "",
        "bis": "",
        "sichtbarkeit": "ALLE",
        "sichtbarFuer": [],
    }
    body = VerbindungUpdate(typ="Freund", beschreibung="Tippfehler weg", sichtbarkeit="ALLE")

    async def run():
        with patch(
            "app.entities.routes.repository.update_verbindung", AsyncMock(return_value=aktualisiert)
        ) as upd:
            ergebnis = await routes.update_verbindung("c1", "e1", body)
        upd.assert_awaited_once_with("c1", "e1", body.model_dump())
        assert ergebnis["typ"] == "Freund"
        assert ergebnis["sichtbarkeit"] == "ALLE"

    _run(run())


def test_update_verbindung_fehlt_ist_404():
    from app.entities import routes
    from app.entities.schemas import VerbindungUpdate

    async def run():
        with patch("app.entities.routes.repository.update_verbindung", AsyncMock(return_value=None)):
            with pytest.raises(HTTPException) as fehler:
                await routes.update_verbindung("c1", "fehlt", VerbindungUpdate(typ="x"))
        assert fehler.value.status_code == 404

    _run(run())
