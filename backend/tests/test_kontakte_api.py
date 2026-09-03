"""API-nahe Vertragstests für Kontakte und Messenger."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Viewer
from app.kontakte.routes import require_messenger_active
from app.kontakte.schemas import KontaktResponse, NachrichtCreate
from app.kontakte.security import kontakt_fuer_viewer


class _SettingsRepo:
    get_einstellungen = AsyncMock(return_value={"messengerAktiv": False})


def test_spielerantwort_uebertraegt_echten_namen_nicht_ohne_freigabe():
    roh = {
        "id": "r-1",
        "pcId": "pc-1",
        "npcId": "npc-1",
        "npcName": "Mara Voss",
        "npcAlias": "Die Rote",
        "npcRasse": "Mensch",
        "npcBildUrl": "silhouette.png",
        "npcDescription": "Eine rote Jacke.",
        "alias": "Die Rote",
        "persoenlicherAlias": "",
        "persoenlicheNotizen": "",
        "stufe": "GESEHEN",
        "echterNameBekannt": False,
        "kontaktAnfrageStatus": "KEINE",
    }

    antwort = kontakt_fuer_viewer(roh, Viewer(role="PLAYER", person_id="pc-1"))

    assert isinstance(antwort, KontaktResponse)
    assert antwort.echterName is None
    assert "npcName" not in antwort.model_dump()
    assert antwort.alias == "Die Rote"


def test_spielerantwort_darf_echten_namen_nach_freigabe_enthalten():
    roh = {
        "id": "r-1",
        "pcId": "pc-1",
        "npcId": "npc-1",
        "npcName": "Mara Voss",
        "npcAlias": "Die Rote",
        "npcRasse": "Mensch",
        "npcBildUrl": "",
        "npcDescription": "",
        "alias": "",
        "persoenlicherAlias": "",
        "persoenlicheNotizen": "",
        "stufe": "GESPROCHEN",
        "echterNameBekannt": True,
        "kontaktAnfrageStatus": "KEINE",
    }

    antwort = kontakt_fuer_viewer(roh, Viewer(role="PLAYER", person_id="pc-1"))

    assert antwort.echterName == "Mara Voss"
    assert antwort.alias == "Die Rote"


def test_nachricht_eingabe_akzeptiert_unicode_emoji():
    nachricht = NachrichtCreate(inhalt="Bis später! 👩🏽‍🚀")

    assert "👩🏽‍🚀" in nachricht.inhalt


def test_messenger_ist_bei_deaktivierter_kampagnenoption_gesperrt(monkeypatch):
    from app.kontakte import routes

    monkeypatch.setattr(routes, "get_einstellungen", AsyncMock(return_value={"messengerAktiv": False}))

    with pytest.raises(HTTPException) as fehler:
        asyncio.run(require_messenger_active("kampagne-1", Viewer(role="PLAYER", person_id="pc-1")))

    assert fehler.value.status_code == 403
    assert "Messenger" in str(fehler.value.detail)


def test_messenger_dependency_laesst_aktive_kampagne_durch(monkeypatch):
    from app.kontakte import routes

    monkeypatch.setattr(routes, "get_einstellungen", AsyncMock(return_value={"messengerAktiv": True}))
    viewer = Viewer(role="PLAYER", person_id="pc-1")

    assert asyncio.run(require_messenger_active("kampagne-1", viewer)) == viewer
