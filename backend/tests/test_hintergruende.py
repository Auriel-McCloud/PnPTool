"""Narrativer Hintergrund-Katalog: Seed ohne Mentor/Kontakte."""

from app.hintergruende.seed import NARRATIVE_SEED, SYSTEM_HINTERGRUENDE, SYSTEM_SCHLUESSEL


def test_seed_laesst_systemhintergruende_weg():
    namen = {eintrag["name"] for eintrag in NARRATIVE_SEED}
    assert "Mentor" not in namen
    assert "Kontakte" not in namen
    assert "Schulden" not in namen
    assert "Straßenruf" in namen
    assert "Ressourcen" in namen


def test_systemschluessel_sind_mentor_kontakte_schulden():
    assert SYSTEM_SCHLUESSEL == ("MENTOR", "KONTAKTE", "SCHULDEN")


def test_system_hintergruende_decken_alle_systemschluessel_ab():
    """Jeder SYSTEM_SCHLUESSEL braucht genau einen Metadaten-Eintrag mit
    Name, Beschreibung und einer gültigen Einstellung zum Umschalten."""
    schluessel = {eintrag["schluessel"] for eintrag in SYSTEM_HINTERGRUENDE}
    assert schluessel == set(SYSTEM_SCHLUESSEL)
    for eintrag in SYSTEM_HINTERGRUENDE:
        assert eintrag["name"]
        assert eintrag["beschreibung"]
        assert eintrag["einstellung"].endswith("Aktiv")
