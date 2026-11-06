"""Wer darf welchen Token schieben — ohne Datenbank."""

from app.battlemap.logic import darf_schieben


class TestDarfSchieben:
    def test_sl_darf_jeden(self):
        assert darf_schieben(rolle="GM", person_id=None, token_person_id="a", besitzer_id=None, am_zug=True) is True

    def test_sl_auch_wenn_nicht_dran(self):
        assert darf_schieben(rolle="GM", person_id=None, token_person_id="a", besitzer_id=None, am_zug=False) is True

    def test_spieler_eigenen_wenn_dran(self):
        assert darf_schieben(rolle="PLAYER", person_id="a", token_person_id="a", besitzer_id=None, am_zug=True) is True

    def test_spieler_eigenen_nicht_ausserhalb_zug(self):
        assert darf_schieben(rolle="PLAYER", person_id="a", token_person_id="a", besitzer_id=None, am_zug=False) is False

    def test_spieler_fremde_nicht(self):
        assert darf_schieben(rolle="PLAYER", person_id="a", token_person_id="b", besitzer_id=None, am_zug=True) is False

    def test_spieler_eigene_drohne_wenn_dran(self):
        assert darf_schieben(rolle="PLAYER", person_id="a", token_person_id="drohne", besitzer_id="a", am_zug=True) is True

    def test_spieler_fremde_drohne_nicht(self):
        assert darf_schieben(rolle="PLAYER", person_id="a", token_person_id="drohne", besitzer_id="b", am_zug=True) is False
