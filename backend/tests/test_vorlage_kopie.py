"""Besitz-Reiter: Kopie einer Vorlage, ohne sie selbst zu vergeben.

Neue Vorlagen sind standardmäßig einzigartig. Ohne ausdrückliches `kopie`
übergibt die Route dann das Stück selbst und die Vorlage ist weg. Der
Knopf „Kopie erstellen“ setzt das Flag — die Vorlage bleibt.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from app.items.routes import zuweisen
from app.items.schemas import ZuweisenRequest


def _run(coro):
    return asyncio.run(coro)


def _vorlage(*, einzigartig: bool, story: bool) -> dict:
    return {
        "id": "g1",
        "istVorlage": True,
        "einzigartig": einzigartig,
        "storyRelevant": story,
        "name": "Klinge",
    }


def _aufruf(vorlage: dict, kopie: bool):
    with (
        patch("app.items.routes.repository.get_gegenstand", AsyncMock(return_value=vorlage)),
        patch("app.items.routes.get_node", AsyncMock(return_value={"id": "p1", "personType": "PC"})),
        patch("app.items.routes.repository.assign_copy", AsyncMock(return_value={"id": "kopie"})) as kopieren,
        patch("app.items.routes.repository.assign_owner", AsyncMock(return_value={"id": "g1"})) as uebergeben,
    ):
        ergebnis = _run(zuweisen("c1", "g1", ZuweisenRequest(zielPersonId="p1", kopie=kopie)))
    return ergebnis, kopieren, uebergeben


def test_einzigartige_vorlage_bleibt_wenn_kopie_gesetzt():
    ergebnis, kopieren, uebergeben = _aufruf(_vorlage(einzigartig=True, story=False), kopie=True)
    kopieren.assert_awaited_once()
    uebergeben.assert_not_awaited()
    assert ergebnis["id"] == "kopie"


def test_story_vorlage_bleibt_wenn_kopie_gesetzt():
    _, kopieren, uebergeben = _aufruf(_vorlage(einzigartig=False, story=True), kopie=True)
    kopieren.assert_awaited_once()
    uebergeben.assert_not_awaited()


def test_einzigartige_vorlage_wird_ohne_flag_selbst_uebergeben():
    _, kopieren, uebergeben = _aufruf(_vorlage(einzigartig=True, story=False), kopie=False)
    uebergeben.assert_awaited_once()
    kopieren.assert_not_awaited()


def test_gewoehnliche_vorlage_wird_auch_ohne_flag_kopiert():
    _, kopieren, uebergeben = _aufruf(_vorlage(einzigartig=False, story=False), kopie=False)
    kopieren.assert_awaited_once()
    uebergeben.assert_not_awaited()
