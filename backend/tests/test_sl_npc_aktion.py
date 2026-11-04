"""Booster und Hot: die SL handelt für NPCs, nie für Spielercharaktere."""

from app.kampf.initiative import (
    FEHLER_KEINE_PERSON,
    FEHLER_KEIN_CHARAKTER,
    FEHLER_NUR_SPIELER,
    FEHLER_UNBEKANNT,
    person_fehler_http,
    waehle_person,
)


def test_spieler_handelt_immer_fuer_sich():
    person, fehler = waehle_person("PLAYER", "pc-1", "npc-9", "NPC", schreiben=True)
    assert person == "pc-1"
    assert fehler is None


def test_spieler_ohne_charakter():
    person, fehler = waehle_person("PLAYER", None, None, None, schreiben=False)
    assert person is None
    assert fehler == FEHLER_KEIN_CHARAKTER


def test_sl_lesen_ohne_ziel_ist_leer():
    person, fehler = waehle_person("GM", None, None, None, schreiben=False)
    assert person is None
    assert fehler is None


def test_sl_schreiben_ohne_ziel():
    _, fehler = waehle_person("GM", None, None, None, schreiben=True)
    assert fehler == FEHLER_KEINE_PERSON


def test_sl_steuert_npc():
    person, fehler = waehle_person("GM", None, "npc-1", "NPC", schreiben=True)
    assert person == "npc-1"
    assert fehler is None


def test_sl_steuert_drohne_und_critter():
    # Technisch personType NPC, die SL würfelt und handelt sie.
    for typ in ("NPC", ""):
        person, fehler = waehle_person("GM", None, "d-1", typ, schreiben=True)
        assert person == "d-1"
        assert fehler is None


def test_sl_darf_pc_nicht_zuenden():
    _, fehler = waehle_person("GM", None, "pc-1", "PC", schreiben=True)
    assert fehler == FEHLER_NUR_SPIELER


def test_sl_unbekannte_person():
    _, fehler = waehle_person("GM", None, "weg", None, schreiben=False)
    assert fehler == FEHLER_UNBEKANNT


def test_fehler_werden_zu_http():
    assert person_fehler_http(FEHLER_NUR_SPIELER) == (403, "Spielercharaktere entscheiden das selbst")
    assert person_fehler_http(FEHLER_UNBEKANNT)[0] == 404
