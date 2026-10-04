"""Massen-KI-Anlage: N unterschiedliche Entwürfe aus einem Wunsch, optional
mit Ziel-Verknüpfung (Sortiment für Gegenstände, Beziehungskante für
Charakter/Ort). Siehe app/ki/routes.py::_massen_anlegen.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.ki.auto_verknuepfung import BeziehungAnwendenErgebnis
from app.ki.routes import (
    MassenIdeeInput,
    _massen_anlegen,
    _massen_zusatz,
)


def _run(coro):
    return asyncio.run(coro)


def _idee_side_effect(typ_namen: list[str]):
    """Baut einen AsyncMock-side_effect, der nacheinander {typ,id,name} für
    jeden angegebenen Namen liefert — wie _idee_anlegen es zurückgäbe."""
    ergebnisse = [{"typ": "ort", "id": f"id-{i}", "name": name} for i, name in enumerate(typ_namen)]

    async def seite(*_args, **_kwargs):
        return ergebnisse.pop(0)

    return seite


def test_massenidee_erlaubt_nur_die_drei_v1_typen():
    MassenIdeeInput(typ="gegenstand", prompt="x")
    MassenIdeeInput(typ="charakter", prompt="x")
    MassenIdeeInput(typ="ort", prompt="x")
    with pytest.raises(Exception):
        MassenIdeeInput(typ="story", prompt="x")  # type: ignore[arg-type]


def test_anzahl_wird_auf_1_bis_12_geklemmt():
    async def run():
        with (
            patch("app.ki.routes._idee_anlegen", AsyncMock(side_effect=_idee_side_effect([f"Ort {i}" for i in range(12)]))) as idee,
        ):
            ergebnis = await _massen_anlegen("c1", "ort", "irgendwas", 99, None, None, None)
            assert idee.await_count == 12
            assert len(ergebnis.eintraege) == 12

    _run(run())

    async def run_min():
        with (
            patch("app.ki.routes._idee_anlegen", AsyncMock(side_effect=_idee_side_effect(["Nur einer"]))) as idee,
        ):
            ergebnis = await _massen_anlegen("c1", "ort", "irgendwas", 0, None, None, None)
            assert idee.await_count == 1
            assert len(ergebnis.eintraege) == 1

    _run(run_min())


def test_jeder_eintrag_bekommt_wachsende_bereits_erzeugt_liste():
    namen = ["Hafenviertel", "Rotlichtviertel", "Industriering"]

    async def run():
        with (
            patch("app.ki.routes._idee_anlegen", AsyncMock(side_effect=_idee_side_effect(namen))) as idee,
        ):
            await _massen_anlegen("c1", "ort", "Stadtteile von Babel", 3, None, None, None)
            prompts = [call.args[2] for call in idee.await_args_list]
            # Erster Aufruf kennt noch keine Vorgänger.
            assert "Bereits in dieser Serie erzeugt" not in prompts[0]
            # Zweiter kennt den ersten Namen, dritter beide.
            assert "Hafenviertel" in prompts[1]
            assert "Hafenviertel" in prompts[2] and "Rotlichtviertel" in prompts[2]

    _run(run())


def test_ohne_ziel_wird_nichts_verknuepft():
    async def run():
        with patch("app.ki.routes._idee_anlegen", AsyncMock(side_effect=_idee_side_effect(["A", "B"]))):
            ergebnis = await _massen_anlegen("c1", "ort", "x", 2, None, None, None)
            assert all(e.verknuepft is False for e in ergebnis.eintraege)

    _run(run())


def test_unbekanntes_ziel_gibt_404():
    from fastapi import HTTPException

    async def run():
        with (
            patch("app.ki.routes._idee_anlegen", AsyncMock()),
            patch("app.ki.routes.get_node", AsyncMock(return_value=None)),
        ):
            with pytest.raises(HTTPException) as exc:
                await _massen_anlegen("c1", "ort", "x", 2, "Ort", "o-unbekannt", None)
            assert exc.value.status_code == 404

    _run(run())


def test_gegenstaende_landen_im_sortiment_eines_haendlers():
    async def run():
        with (
            patch(
                "app.ki.routes._idee_anlegen",
                AsyncMock(
                    side_effect=[
                        {"typ": "gegenstand", "id": "g1", "name": "Panzerjacke", "preis": 500},
                        {"typ": "gegenstand", "id": "g2", "name": "Thermovisor", "preis": 800},
                    ]
                ),
            ),
            patch(
                "app.ki.routes.get_node",
                AsyncMock(return_value={"id": "h1", "name": "Chrom-Charlie", "istHaendler": True, "personType": "NPC"}),
            ),
            patch("app.ki.routes.haendler_repository.verkauft_hinzufuegen", AsyncMock(return_value=True)) as verkauft,
        ):
            ergebnis = await _massen_anlegen("c1", "gegenstand", "Waren für Chrom-Charlie", 2, "Person", "h1", None)
            assert verkauft.await_count == 2
            verkauft.assert_any_await("c1", "h1", "g1", 500)
            assert all(e.verknuepft for e in ergebnis.eintraege)

    _run(run())


def test_gegenstaende_an_normale_person_werden_zugewiesen_nicht_verkauft():
    async def run():
        with (
            patch(
                "app.ki.routes._idee_anlegen",
                AsyncMock(return_value={"typ": "gegenstand", "id": "g1", "name": "Taschenmesser", "preis": 20}),
            ),
            patch(
                "app.ki.routes.get_node",
                AsyncMock(return_value={"id": "p1", "name": "Rollo", "istHaendler": False, "personType": "NPC"}),
            ),
            patch("app.ki.routes.haendler_repository.verkauft_hinzufuegen", AsyncMock()) as verkauft,
            patch("app.ki.routes.assign_copy", AsyncMock(return_value={"id": "g1-kopie"})) as kopie,
        ):
            ergebnis = await _massen_anlegen("c1", "gegenstand", "ein paar Sachen für Rollo", 1, "Person", "p1", None)
            verkauft.assert_not_awaited()
            assert kopie.await_count == 1
            assert ergebnis.eintraege[0].verknuepft is True

    _run(run())


def test_charaktere_bekommen_beziehungskante_zum_ziel_ort():
    async def run():
        with (
            patch(
                "app.ki.routes._idee_anlegen",
                AsyncMock(
                    side_effect=[
                        {"typ": "charakter", "id": "p1", "name": "Nyx"},
                        {"typ": "charakter", "id": "p2", "name": "Switchblade"},
                    ]
                ),
            ),
            patch(
                "app.ki.routes.get_node",
                AsyncMock(return_value={"id": "o1", "name": "Bar Lumen", "istEntwurf": False}),
            ),
            patch("app.ki.routes.verknuepfung_beziehung_anwenden", AsyncMock()) as anwenden,
        ):
            anwenden.return_value = BeziehungAnwendenErgebnis(
                verbindungId="v1", zielId1="p1", zielId2="o1", neuAngelegt1=False, neuAngelegt2=False
            )
            ergebnis = await _massen_anlegen(
                "c1", "charakter", "ein paar NPCs in einer Bar", 2, "Ort", "o1", "ist Stammgast in"
            )
            assert anwenden.await_count == 2
            erste_eingabe = anwenden.await_args_list[0].args[1]
            assert erste_eingabe.typ1 == "Person"
            assert erste_eingabe.zielId1 == "p1"
            assert erste_eingabe.typ2 == "Ort"
            assert erste_eingabe.zielId2 == "o1"
            assert erste_eingabe.beziehungstyp == "ist Stammgast in"
            assert all(e.verknuepft for e in ergebnis.eintraege)

    _run(run())


def test_default_beziehungstyp_greift_ohne_eigene_angabe():
    async def run():
        with (
            patch(
                "app.ki.routes._idee_anlegen",
                AsyncMock(return_value={"typ": "ort", "id": "o2", "name": "Chrom-Markt"}),
            ),
            patch(
                "app.ki.routes.get_node",
                AsyncMock(return_value={"id": "f1", "name": "Chrysalis-Konzern"}),
            ),
            patch("app.ki.routes.verknuepfung_beziehung_anwenden", AsyncMock()) as anwenden,
        ):
            anwenden.return_value = BeziehungAnwendenErgebnis(
                verbindungId="v2", zielId1="o2", zielId2="f1", neuAngelegt1=False, neuAngelegt2=False
            )
            await _massen_anlegen("c1", "ort", "Stadtteile unter Konzernkontrolle", 1, "Fraktion", "f1", None)
            eingabe = anwenden.await_args_list[0].args[1]
            assert eingabe.beziehungstyp == "wird kontrolliert von"

    _run(run())
