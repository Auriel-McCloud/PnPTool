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


def test_notizen_aus_der_ki_antwort_landen_im_notes_feld():
    """Details, die nicht in die knappe beschreibung passen, gehen ins SL-Notizfeld."""
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(
                    return_value={
                        "name": "Hafen",
                        "beschreibung": "nass",
                        "notizen": "Hier stehen alle Details aus dem Gespräch.",
                    }
                ),
            ),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "o1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            await _idee_anlegen("c1", "ort", "ein Hafen")
            daten = create.await_args.args[3]
            assert daten["notes"] == "Hier stehen alle Details aus dem Gespräch."

    _run(run())


def test_fehlende_notizen_in_der_antwort_brechen_nichts():
    """Ältere/gemockte Antworten ohne notizen-Feld bleiben gültig (leerer String)."""
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
            await _idee_anlegen("c1", "ort", "ein Hafen")
            daten = create.await_args.args[3]
            assert daten["notes"] == ""

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


def test_idee_charakter_lehnt_regelwidrige_bogenwerte_ab():
    from fastapi import HTTPException

    from tests.test_erstellung import KATALOG, grundgeruest

    async def run():
        daten = {
            **grundgeruest(attributPunkte={
                **grundgeruest()["attributPunkte"],
                "Körperkraft": 10,
            }),
            "name": "Kira",
            "beschreibung": "x",
            "notizen": "",
            "konzept": "Fixer",
        }
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.generiere_json", AsyncMock(return_value=daten)),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch("app.ki.routes.rassen_repository.liste_fuer_kampagne", AsyncMock(return_value=[])),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.create_node", AsyncMock()) as create,
        ):
            with pytest.raises(HTTPException) as exc:
                await _idee_anlegen("c1", "charakter", "eine Kira")
            assert exc.value.status_code == 422
            assert create.await_count == 0

    _run(run())


def test_idee_charakter_schreibt_endwerte_aus_der_erstellung():
    from tests.test_erstellung import KATALOG, grundgeruest

    async def run():
        daten = {
            **grundgeruest(freebeeKredit=1, freebeePunkte={"Etiketten": 1}),
            "name": "Kira",
            "beschreibung": "x",
            "notizen": "",
            "konzept": "Fixer",
        }
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.generiere_json", AsyncMock(return_value=daten)),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch("app.ki.routes.rassen_repository.liste_fuer_kampagne", AsyncMock(return_value=[])),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "p1"})) as create,
            patch("app.ki.routes.set_ratings_bulk", AsyncMock()) as bulk,
            patch("app.ki.routes.setze_maxima_bulk", AsyncMock()),
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await _idee_anlegen("c1", "charakter", "eine Kira")
            assert ergebnis["typ"] == "charakter"
            werte = bulk.await_args.args[2]
            assert werte["Körperkraft"] == 4
            person = create.await_args.args[3]
            assert person["erstellungAbgeschlossen"] is True

    _run(run())


def test_idee_charakter_bessert_regelwidrige_antwort_nach():
    from tests.test_erstellung import KATALOG, grundgeruest

    async def run():
        illegal = {
            **grundgeruest(attributPunkte={
                **grundgeruest()["attributPunkte"],
                "Körperkraft": 10,
            }),
            "name": "Kira",
            "beschreibung": "x",
            "notizen": "",
            "konzept": "Fixer",
        }
        legal = {
            **grundgeruest(freebeeKredit=2, freebeeEigenkapital=1),
            "name": "Kira",
            "beschreibung": "x",
            "notizen": "",
            "konzept": "Fixer",
        }
        ki = AsyncMock(side_effect=[illegal, legal])
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.generiere_json", ki),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch("app.ki.routes.rassen_repository.liste_fuer_kampagne", AsyncMock(return_value=[])),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "p1"})) as create,
            patch("app.ki.routes.set_ratings_bulk", AsyncMock()) as bulk,
            patch("app.ki.routes.setze_maxima_bulk", AsyncMock()),
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await _idee_anlegen("c1", "charakter", "eine Kira")
            assert ergebnis["typ"] == "charakter"
            assert ki.await_count == 2
            assert "Körperkraft" in ki.await_args.args[0]
            assert bulk.await_args.args[2]["Körperkraft"] == 4
            person = create.await_args.args[3]
            assert person["kapital"] == 40_000
            assert person["schulden"] == 20_000

    _run(run())
