"""KI-Idee und Beratung-Entwurf: alle anlegbaren Welttypen."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from app.ki.auto_verknuepfung import BeziehungAnwendenErgebnis
from app.ki.routes import BeratungEntwurfInput, KiIdeeInput, _idee_anlegen

WELTTYPEN = ("story", "charakter", "gegenstand", "ort", "event", "fraktion", "verbindung")


def _run(coro):
    return asyncio.run(coro)


def test_idee_und_beratung_erlauben_dieselben_welttypen():
    for typ in WELTTYPEN:
        KiIdeeInput(typ=typ, prompt="x")
        BeratungEntwurfInput(typ=typ)


def test_unbekannter_idee_typ_wird_abgelehnt():
    with pytest.raises(ValidationError):
        KiIdeeInput(typ="rasse", prompt="x")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        BeratungEntwurfInput(typ="begleiter")  # type: ignore[arg-type]


def test_ort_wird_als_ort_angelegt_nicht_als_charakter():
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(return_value={"name": "Hafen", "beschreibung": "nass"}),
            ),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "o1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await _idee_anlegen("c1", "ort", "ein Hafen")
            assert ergebnis["typ"] == "ort"
            assert create.await_args.args[0] == "Ort"

    _run(run())


def test_fraktion_bekommt_ziele_und_ressourcen():
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(
                    return_value={
                        "name": "Chrysalis",
                        "beschreibung": "Konzern",
                        "ziele": [{"titel": "Markt", "beschreibung": "kaufen"}],
                        "ressourcen": [{"titel": "Kapital", "beschreibung": "viel"}],
                    }
                ),
            ),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "f1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await _idee_anlegen("c1", "fraktion", "ein Konzern")
            assert ergebnis["typ"] == "fraktion"
            assert create.await_args.args[0] == "Fraktion"
            daten = create.await_args.args[3]
            assert daten["ziele"][0]["titel"] == "Markt"
            assert daten["ressourcen"][0]["titel"] == "Kapital"

    _run(run())


def test_verbindung_nutzt_beziehung_anwenden():
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="Fred (Person)")),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(
                    return_value={
                        "vonName": "Fred",
                        "vonTyp": "Person",
                        "zuName": "Hafen",
                        "zuTyp": "Ort",
                        "typ": "hält sich auf",
                        "beschreibung": "stammt von dort",
                    }
                ),
            ),
            patch("app.ki.routes.verknuepfung_beziehung_anwenden", AsyncMock()) as anwenden,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            anwenden.return_value = BeziehungAnwendenErgebnis(
                verbindungId="v1",
                zielId1="p1",
                zielId2="o1",
                neuAngelegt1=False,
                neuAngelegt2=True,
            )
            ergebnis = await _idee_anlegen("c1", "verbindung", "Fred und der Hafen")
            assert ergebnis["typ"] == "verbindung"
            assert ergebnis["id"] == "v1"
            assert anwenden.await_count == 1

    _run(run())
