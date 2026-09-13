"""Test: istEntwurf-Filter in Entitäten-Listen."""
import asyncio
import pytest
from app.entities.routes import _aufbereiten
from app.auth.dependencies import Viewer


class TestIstEntwurfFilter:
    @pytest.fixture
    def gm_viewer(self):
        return Viewer(role="GM", person_id=None)

    @pytest.fixture
    def orte_mit_entwurf(self):
        return [
            {"id": "1", "name": "Entwurf-Ort", "istEntwurf": True, "sichtbarkeit": "GM", "sichtbarFuer": []},
            {"id": "2", "name": "Echter-Ort", "istEntwurf": False, "sichtbarkeit": "GM", "sichtbarFuer": []},
            {"id": "3", "name": "Alter-Ort", "sichtbarkeit": "GM", "sichtbarFuer": []},  # kein istEntwurf-Feld
        ]

    def test_entwuerfe_werden_standardmaessig_ausgeblendet(self, orte_mit_entwurf, gm_viewer):
        """Normale Liste zeigt nur Nicht-Entwürfe."""
        async def run():
            return await _aufbereiten(
                orte_mit_entwurf,
                "test-campaign",
                gm_viewer,
                namensfeld="name",
                suche=None,
                sortierung=None,
            )
        result = asyncio.run(run())
        namen = [o["name"] for o in result]
        assert "Entwurf-Ort" not in namen
        assert "Echter-Ort" in namen
        assert "Alter-Ort" in namen  # Legacy ohne Feld = kein Entwurf

    def test_nur_entwuerfe_zeigt_nur_entwuerfe(self, orte_mit_entwurf, gm_viewer):
        """Mit nur_entwuerfe=True kommen nur Entwürfe."""
        async def run():
            return await _aufbereiten(
                orte_mit_entwurf,
                "test-campaign",
                gm_viewer,
                namensfeld="name",
                suche=None,
                sortierung=None,
                nur_entwuerfe=True,
            )
        result = asyncio.run(run())
        namen = [o["name"] for o in result]
        assert namen == ["Entwurf-Ort"]
