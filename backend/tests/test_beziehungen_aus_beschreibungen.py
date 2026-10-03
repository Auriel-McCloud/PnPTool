"""Beziehungen aus Beschreibungen: Vorschläge aus Beschreibung+Notizen ALLER
Entitäten einer Kampagne, ohne Wiki-Seitenbezug (03.10.2026, Marks Wunsch).
"""

import asyncio
from unittest.mock import AsyncMock, patch

from app.ki.auto_verknuepfung import BeziehungsVorschlag, beziehungsvorschlaege_aus_beschreibungen


def _run(coro):
    return asyncio.run(coro)


def test_weniger_als_zwei_entitaeten_mit_text_ruft_die_ki_nicht():
    async def run():
        with (
            patch(
                "app.ki.auto_verknuepfung.sammle_entitaeten_mit_text",
                AsyncMock(return_value=[{"id": "p1", "kind": "Person", "name": "Kez", "text": "Fixer"}]),
            ),
            patch("app.ki.auto_verknuepfung.generiere_json", AsyncMock()) as ki,
        ):
            ergebnis = await beziehungsvorschlaege_aus_beschreibungen("c1")
            assert ergebnis.beziehungen == []
            ki.assert_not_called()

    _run(run())


def test_erkannte_beziehung_wird_mit_zielid_zurueckgegeben():
    async def run():
        entitaeten = [
            {"id": "p1", "kind": "Person", "name": "Kez", "text": "Beschreibung: schuldet dem Zaibatsu Geld"},
            {"id": "f1", "kind": "Fraktion", "name": "Zaibatsu", "text": "Beschreibung: mächtiger Konzern"},
        ]
        with (
            patch("app.ki.auto_verknuepfung.sammle_entitaeten_mit_text", AsyncMock(return_value=entitaeten)),
            patch("app.ki.auto_verknuepfung.list_entitaets_verbindungen", AsyncMock(return_value=[])),
            patch("app.ki.auto_verknuepfung.sammle_verbindungstypen_text", AsyncMock(return_value="(noch keine)")),
            patch(
                "app.ki.auto_verknuepfung.generiere_json",
                AsyncMock(
                    return_value={
                        "beziehungen": [
                            {
                                "typ1": "Person",
                                "name1": "Kez",
                                "typ2": "Fraktion",
                                "name2": "Zaibatsu",
                                "beziehungstyp": "Schulden bei",
                                "beschreibung": "",
                            }
                        ]
                    }
                ),
            ),
            patch("app.ki.auto_verknuepfung.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await beziehungsvorschlaege_aus_beschreibungen("c1")
            assert len(ergebnis.beziehungen) == 1
            v = ergebnis.beziehungen[0]
            assert v.zielId1 == "p1"
            assert v.zielId2 == "f1"
            assert v.beziehungstyp == "Schulden bei"

    _run(run())


def test_bereits_bestehende_verbindung_wird_nicht_erneut_vorgeschlagen():
    """Dedup gegen den echten Graphen — unabhängig davon, in welcher Richtung
    die KI die Beziehung nennt (A-kennt-B == B-kennt-A)."""

    async def run():
        entitaeten = [
            {"id": "p1", "kind": "Person", "name": "Kez", "text": "Beschreibung: kennt Mira"},
            {"id": "p2", "kind": "Person", "name": "Mira", "text": "Beschreibung: kennt Kez"},
        ]
        bestehend = [{"vonId": "p2", "zuId": "p1", "typ": "kennt"}]
        with (
            patch("app.ki.auto_verknuepfung.sammle_entitaeten_mit_text", AsyncMock(return_value=entitaeten)),
            patch("app.ki.auto_verknuepfung.list_entitaets_verbindungen", AsyncMock(return_value=bestehend)),
            patch("app.ki.auto_verknuepfung.sammle_verbindungstypen_text", AsyncMock(return_value="kennt")),
            patch(
                "app.ki.auto_verknuepfung.generiere_json",
                AsyncMock(
                    return_value={
                        "beziehungen": [
                            {
                                "typ1": "Person",
                                "name1": "Kez",
                                "typ2": "Person",
                                "name2": "Mira",
                                "beziehungstyp": "kennt",
                                "beschreibung": "",
                            }
                        ]
                    }
                ),
            ),
            patch("app.ki.auto_verknuepfung.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await beziehungsvorschlaege_aus_beschreibungen("c1")
            assert ergebnis.beziehungen == []

    _run(run())


def test_beziehungsvorschlag_enthaelt_alle_felder():
    """Reine Datenklassenprobe — Regression falls das Schema je abweicht."""
    v = BeziehungsVorschlag(
        typ1="Person", name1="A", zielId1="1", typ2="Ort", name2="B", zielId2="2",
        beziehungstyp="lebt in", beschreibung="",
    )
    assert v.zielId1 == "1" and v.zielId2 == "2"
