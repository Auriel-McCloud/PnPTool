"""Auto-Hooks ins Ereignisprotokoll — ohne Neo4j, nur ob die Fachstellen rufen.

Die Writer selbst leben in app/ereignisprotokoll/repository.py (Commit 233c939).
Hier geht es um die Verdrahtung: Kauf, Weitergabe, Reparatur, Aufenthalt, KI.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.verhandlung import logic

_APP = Path(__file__).resolve().parents[1] / "app"


def _run(coro):
    return asyncio.run(coro)


def test_shop_kauf_loggt_gegenstand_und_geld():
    """Angenommener Shop-Kauf muss GEKAUFT + HANDEL mit gemeinsamer handelId schreiben."""

    async def run():
        with (
            patch("app.verhandlung.logic.entities_repository") as ent,
            patch("app.verhandlung.logic.items_repository") as items,
            patch("app.verhandlung.logic.haendler_repository") as haendler,
            patch("app.verhandlung.logic.hooks") as hooks,
        ):
            ent.get_node = AsyncMock(return_value={"kapital": 500})
            ent.update_node = AsyncMock()
            items.get_gegenstand = AsyncMock(return_value={"istVorlage": False, "id": "g1"})
            items.transfer_owner = AsyncMock(return_value={"id": "g1"})
            items.get_owner_id = AsyncMock(return_value="haendler-1")
            haendler.verkauft_entfernen = AsyncMock()
            hooks.handel = AsyncMock()
            verhandlung = {
                "empfaengerPersonId": "kaeufer-1",
                "gesamtbetrag": 120,
                "kontext": {"haendlerId": "haendler-1", "gegenstandId": "g1"},
            }
            await logic._ausfuehren_shop_kauf("kampagne-1", verhandlung)
            hooks.handel.assert_awaited_once()
            kw = hooks.handel.await_args.kwargs
            assert kw["gegenstand_id"] == "g1"
            assert kw["neuer_besitzer_id"] == "kaeufer-1"
            assert kw["betrag"] == 120
            assert kw["von_person_id"] == "haendler-1"

    _run(run())


def test_weitergabe_loggt_gegenstandsbewegung():
    async def run():
        with (
            patch("app.verhandlung.logic.items_repository") as items,
            patch("app.verhandlung.logic.hooks") as hooks,
        ):
            items.get_gegenstand = AsyncMock(return_value={"id": "g1"})
            items.get_owner_id = AsyncMock(return_value="absender-1")
            items.transfer_owner = AsyncMock(return_value={"id": "g1"})
            hooks.gegenstand = AsyncMock()
            verhandlung = {
                "empfaengerPersonId": "empfaenger-1",
                "kontext": {"gegenstandId": "g1", "absenderPersonId": "absender-1"},
            }
            await logic._ausfuehren_gegenstand_weitergabe("kampagne-1", verhandlung)
            hooks.gegenstand.assert_awaited_once()
            kw = hooks.gegenstand.await_args.kwargs
            assert kw["art"] == "WEITERGEGEBEN"
            assert kw["alter_besitzer_id"] == "absender-1"
            assert kw["neuer_besitzer_id"] == "empfaenger-1"
            assert kw["gegenstand_id"] == "g1"

    _run(run())


def test_ruestungsreparatur_loggt_reparatur_und_ausgabe():
    async def run():
        with (
            patch("app.verhandlung.logic.entities_repository") as ent,
            patch("app.verhandlung.logic.items_repository") as items,
            patch("app.verhandlung.logic.repariere", return_value={"kaestchenNeu": 4}),
            patch("app.verhandlung.logic.hooks") as hooks,
        ):
            ent.get_node = AsyncMock(return_value={"kapital": 800})
            ent.update_node = AsyncMock()
            items.get_gegenstand = AsyncMock(
                return_value={
                    "typ": "Rüstung",
                    "ruestungKaestchenAktuell": 2,
                    "ruestungKaestchenMax": 6,
                }
            )
            items.update_gegenstand = AsyncMock(return_value={"id": "ruestung-1"})
            hooks.gegenstand = AsyncMock()
            hooks.geld = AsyncMock()
            verhandlung = {
                "empfaengerPersonId": "pc-1",
                "gesamtbetrag": 50,
                "kontext": {"gegenstandId": "ruestung-1", "kaestchen": 2},
            }
            await logic._ausfuehren_ruestung_reparatur("kampagne-1", verhandlung)
            hooks.gegenstand.assert_awaited_once()
            assert hooks.gegenstand.await_args.kwargs["art"] == "REPARIERT"
            hooks.geld.assert_awaited_once()
            assert hooks.geld.await_args.kwargs["art"] == "AUSGABE"
            assert hooks.geld.await_args.kwargs["betrag"] == 50

    _run(run())


def test_fachstellen_rufen_die_hooks():
    """Regression: die Verdrahtung darf nicht lautlos aus den Fachmodulen fallen."""
    erwartet = {
        "ki/routes.py": "hooks.ki",
        "ki/wiki_pruefung.py": "hooks.ki",
        "ki/auto_verknuepfung.py": "hooks.ki",
        "haendler/routes.py": "hooks.handel",
        "items/routes.py": "hooks.gegenstand",
        "party/repository.py": "hooks.aufenthalt",
        "traits/routes.py": "hooks.kampf_treffer",
        "entities/routes.py": "hooks.charakterentwicklung",
        "verhandlung/routes.py": "hooks.verhandlungsausgang",
        "verhandlung/logic.py": "hooks.handel",
    }
    for rel, nadel in erwartet.items():
        text = (_APP / rel).read_text(encoding="utf-8")
        assert nadel in text, f"{rel} ruft {nadel} nicht"
