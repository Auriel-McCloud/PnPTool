"""Narrativer Hintergrund-Katalog: Seed ohne Mentor/Kontakte."""

from app.hintergruende.seed import NARRATIVE_SEED, SYSTEM_SCHLUESSEL


def test_seed_laesst_mentor_und_kontakte_weg():
    namen = {eintrag["name"] for eintrag in NARRATIVE_SEED}
    assert "Mentor" not in namen
    assert "Kontakte" not in namen
    assert "Straßenruf" in namen
    assert "Ressourcen" in namen


def test_systemschluessel_sind_mentor_und_kontakte():
    assert SYSTEM_SCHLUESSEL == ("MENTOR", "KONTAKTE")
