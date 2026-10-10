"""Narrativer Hintergrund-Katalog: Seed ohne Mentor/Kontakte."""

from app.hintergruende.seed import NARRATIVE_SEED, SYSTEM_SCHLUESSEL


def test_seed_laesst_systemhintergruende_weg():
    namen = {eintrag["name"] for eintrag in NARRATIVE_SEED}
    assert "Mentor" not in namen
    assert "Kontakte" not in namen
    assert "Schulden" not in namen
    assert "Straßenruf" in namen
    assert "Ressourcen" in namen


def test_systemschluessel_sind_mentor_kontakte_schulden():
    assert SYSTEM_SCHLUESSEL == ("MENTOR", "KONTAKTE", "SCHULDEN")
