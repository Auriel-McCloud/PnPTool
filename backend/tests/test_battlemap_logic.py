"""Wer darf welchen Token schieben — ohne Datenbank."""

from app.battlemap.logic import darf_schieben, token_stand


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


class TestTokenStand:
    def test_nimmt_neuen_teilnehmer_mit_portrait(self):
        stand = token_stand(
            {
                "amZug": "t1",
                "battlemapId": "k1",
                "teilnehmer": [
                    {
                        "id": "t1",
                        "name": "Ada",
                        "bildUrl": "/a.png",
                        "hexQ": 0,
                        "hexR": 1,
                        "istGross": False,
                        "personId": "p1",
                        "personType": "PC",
                        "besitzerId": None,
                    },
                    {"id": "t2", "name": "Ada extra", "zusatzzug": True, "hexQ": 0, "hexR": 1},
                ],
            }
        )
        assert stand["amZug"] == "t1"
        assert stand["battlemapId"] == "k1"
        assert [t["id"] for t in stand["teilnehmer"]] == ["t1"]
        assert stand["teilnehmer"][0]["name"] == "Ada"
        assert stand["teilnehmer"][0]["bildUrl"] == "/a.png"
        assert stand["teilnehmer"][0]["hexR"] == 1

    def test_kampf_ende_leert_die_liste(self):
        stand = token_stand({"amZug": None, "battlemapId": None, "teilnehmer": []})
        assert stand["teilnehmer"] == []
        assert stand["battlemapId"] is None
