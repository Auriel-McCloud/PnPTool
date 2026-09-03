"""Tests für die Fachlogik der SL-Mitteilungen (Push-Popups).

Reine Unit-Tests ohne Datenbank und ohne WebSocket — dieselbe Bauart wie
test_visibility.py und test_wiki.py.
"""

import pytest

from app.mitteilungen.logic import (
    darf_empfangen,
    empfaenger_aufloesen,
    ist_ungelesen,
    zaehle_ungelesen,
)


def m(**ueber):
    """Eine Mitteilung mit vernünftigen Vorgaben."""
    basis = {
        "id": "mit-1",
        "art": "TEXT",
        "inhalt": "Würfelt für Initiative!",
        "anAlle": True,
        "empfaengerIds": [],
        "gelesenVon": [],
        "erstelltAm": "2026-09-03T20:00:00Z",
    }
    basis.update(ueber)
    return basis


class TestEmpfaengerAufloesen:
    """Wer bekommt die Mitteilung tatsächlich?"""

    def test_an_alle_trifft_jeden_spielercharakter(self):
        pcs = ["pc-1", "pc-2", "pc-3"]
        assert empfaenger_aufloesen(an_alle=True, empfaenger_ids=[], alle_pc_ids=pcs) == pcs

    def test_an_einzelne_trifft_nur_die_genannten(self):
        pcs = ["pc-1", "pc-2", "pc-3"]
        assert empfaenger_aufloesen(False, ["pc-2"], pcs) == ["pc-2"]

    def test_unbekannte_empfaenger_werden_verworfen(self):
        # Eine Person-ID aus einer anderen Kampagne darf nicht durchrutschen.
        assert empfaenger_aufloesen(False, ["pc-1", "fremd"], ["pc-1", "pc-2"]) == ["pc-1"]

    def test_reihenfolge_und_doppelte(self):
        assert empfaenger_aufloesen(False, ["pc-2", "pc-2", "pc-1"], ["pc-1", "pc-2"]) == ["pc-2", "pc-1"]

    def test_an_alle_ignoriert_eine_mitgegebene_liste(self):
        # anAlle gewinnt: sonst wäre unklar, was gilt.
        assert empfaenger_aufloesen(True, ["pc-1"], ["pc-1", "pc-2"]) == ["pc-1", "pc-2"]

    def test_leere_auswahl_trifft_niemanden(self):
        assert empfaenger_aufloesen(False, [], ["pc-1"]) == []


class TestDarfEmpfangen:
    def test_sl_sieht_alles(self):
        assert darf_empfangen(m(anAlle=False, empfaengerIds=["pc-9"]), "GM", None) is True

    def test_an_alle_erreicht_jeden_spieler(self):
        assert darf_empfangen(m(anAlle=True), "PLAYER", "pc-1") is True

    def test_gerichtete_mitteilung_nur_beim_empfaenger(self):
        nachricht = m(anAlle=False, empfaengerIds=["pc-1"])
        assert darf_empfangen(nachricht, "PLAYER", "pc-1") is True
        assert darf_empfangen(nachricht, "PLAYER", "pc-2") is False

    def test_spieler_ohne_charakter_bekommt_nur_rundrufe(self):
        assert darf_empfangen(m(anAlle=True), "PLAYER", None) is True
        assert darf_empfangen(m(anAlle=False, empfaengerIds=["pc-1"]), "PLAYER", None) is False


class TestUngelesen:
    def test_frische_mitteilung_ist_ungelesen(self):
        assert ist_ungelesen(m(), "pc-1") is True

    def test_nach_dem_lesen_nicht_mehr(self):
        assert ist_ungelesen(m(gelesenVon=["pc-1"]), "pc-1") is False

    def test_gelesen_gilt_pro_person(self):
        nachricht = m(gelesenVon=["pc-1"])
        assert ist_ungelesen(nachricht, "pc-2") is True

    def test_zaehler_nur_fuer_eigene_ungelesene(self):
        liste = [
            m(id="a"),
            m(id="b", gelesenVon=["pc-1"]),
            m(id="c", anAlle=False, empfaengerIds=["pc-2"]),
            m(id="d"),
        ]
        # pc-1: a und d offen, b gelesen, c nicht für ihn
        assert zaehle_ungelesen(liste, "PLAYER", "pc-1") == 2

    def test_zaehler_leer_ohne_mitteilungen(self):
        assert zaehle_ungelesen([], "PLAYER", "pc-1") == 0


class TestArt:
    """Text jetzt, Bild später — die Art muss von Anfang an mitgeführt werden."""

    def test_text_ist_die_voreinstellung(self):
        assert m()["art"] == "TEXT"

    def test_bild_wird_als_art_akzeptiert(self):
        nachricht = m(art="BILD", inhalt="", bildUrl="/uploads/x/bild.png")
        assert darf_empfangen(nachricht, "PLAYER", "pc-1") is True


class TestSchemaPruefung:
    """Der Schemavertrag ist die Stelle, an der Unsinn abgefangen wird."""

    def test_textmitteilung_ohne_text_wird_abgelehnt(self):
        from pydantic import ValidationError

        from app.mitteilungen.schemas import MitteilungCreate

        with pytest.raises(ValidationError):
            MitteilungCreate(art="TEXT", inhalt="   ", anAlle=True)

    def test_bildmitteilung_ohne_bild_wird_abgelehnt(self):
        from pydantic import ValidationError

        from app.mitteilungen.schemas import MitteilungCreate

        with pytest.raises(ValidationError):
            MitteilungCreate(art="BILD", bildUrl="", anAlle=True)

    def test_bildmitteilung_braucht_keinen_text(self):
        from app.mitteilungen.schemas import MitteilungCreate

        # Ein Bild spricht fuer sich; die Bildunterschrift ist freiwillig.
        m = MitteilungCreate(art="BILD", bildUrl="/uploads/x/npc.png", anAlle=True)
        assert m.inhalt == ""

    def test_gerichtete_mitteilung_ohne_empfaenger_wird_abgelehnt(self):
        from pydantic import ValidationError

        from app.mitteilungen.schemas import MitteilungCreate

        with pytest.raises(ValidationError):
            MitteilungCreate(art="TEXT", inhalt="hallo", anAlle=False, empfaengerIds=[])
