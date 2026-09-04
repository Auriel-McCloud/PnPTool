"""Der echte NPC-Name darf einen Spieler nie erreichen.

Ergänzt `test_kontakte_api.py` um die Fälle, die beim Bauen der API dazukamen:
Beschreibung erst ab GESPROCHEN, Chat erst ab KONTAKT_AUSGETAUSCHT, und ein
Spieler sieht nur seine eigenen Kontakte.
"""

from app.auth.dependencies import Viewer
from app.kontakte.security import darf_kontakt_sehen, kontakt_fuer_gm, kontakt_fuer_viewer


def roh(**kwargs) -> dict:
    basis = {
        "id": "r-1",
        "pcId": "pc-1",
        "pcName": "Ryu",
        "npcId": "npc-1",
        "npcName": "Viktor Kane",
        "npcAlias": "",
        "npcRasse": "Ork",
        "npcBildUrl": "",
        "npcDescription": "Trägt eine rote Jacke.",
        "alias": "",
        "persoenlicherAlias": "",
        "persoenlicheNotizen": "",
        "stufe": "GESEHEN",
        "echterNameBekannt": False,
        "kontaktAnfrageStatus": "KEINE",
        "ungelesen": 0,
    }
    basis.update(kwargs)
    return basis


SPIELER = Viewer(role="PLAYER", person_id="pc-1")


class TestEchterName:
    def test_ohne_freigabe_kein_name_im_ganzen_datensatz(self):
        # Nicht nur `echterName is None` — der Name darf in KEINEM Feld
        # auftauchen, auch nicht versehentlich im Alias.
        antwort = kontakt_fuer_viewer(roh(), SPIELER)
        assert "Viktor" not in str(antwort.model_dump())

    def test_alias_faellt_auf_die_rasse_zurueck(self):
        assert kontakt_fuer_viewer(roh(), SPIELER).alias == "Unbekannter Ork"

    def test_npc_standardalias_schlaegt_die_rasse(self):
        antwort = kontakt_fuer_viewer(roh(npcAlias="Der Schläger"), SPIELER)
        assert antwort.alias == "Der Schläger"

    def test_persoenlicher_alias_schlaegt_alles(self):
        antwort = kontakt_fuer_viewer(
            roh(npcAlias="Der Schläger", persoenlicherAlias="Rote Jacke"), SPIELER
        )
        assert antwort.alias == "Rote Jacke"

    def test_alias_bleibt_auch_nach_der_namensfreigabe(self):
        # Spec: "Der persönliche Alias bleibt auch nach Bekanntwerden des
        # echten Namens erhalten."
        antwort = kontakt_fuer_viewer(
            roh(persoenlicherAlias="Rote Jacke", echterNameBekannt=True), SPIELER
        )
        assert antwort.alias == "Rote Jacke"
        assert antwort.echterName == "Viktor Kane"


class TestBeschreibung:
    def test_erst_ab_gesprochen(self):
        # Wer jemanden nur gesehen hat, weiss nichts über ihn.
        assert kontakt_fuer_viewer(roh(stufe="GESEHEN"), SPIELER).beschreibung == ""

    def test_ab_gesprochen_sichtbar(self):
        antwort = kontakt_fuer_viewer(roh(stufe="GESPROCHEN"), SPIELER)
        assert "rote Jacke" in antwort.beschreibung


class TestChat:
    def test_chat_zu_bei_gesehen(self):
        assert kontakt_fuer_viewer(roh(stufe="GESEHEN"), SPIELER).chatOffen is False

    def test_chat_zu_bei_gesprochen(self):
        # Reden reicht nicht — es braucht die angenommene Kontaktanfrage.
        assert kontakt_fuer_viewer(roh(stufe="GESPROCHEN"), SPIELER).chatOffen is False

    def test_chat_offen_nach_kontaktaustausch(self):
        antwort = kontakt_fuer_viewer(roh(stufe="KONTAKT_AUSGETAUSCHT"), SPIELER)
        assert antwort.chatOffen is True


class TestWerDarfSehen:
    def test_eigener_kontakt_ja(self):
        assert darf_kontakt_sehen(roh(pcId="pc-1"), SPIELER) is True

    def test_fremder_kontakt_nein(self):
        assert darf_kontakt_sehen(roh(pcId="pc-2"), SPIELER) is False

    def test_sl_sieht_alles(self):
        assert darf_kontakt_sehen(roh(pcId="pc-9"), Viewer(role="GM")) is True

    def test_spieler_ohne_charakter_sieht_nichts(self):
        assert darf_kontakt_sehen(roh(), Viewer(role="PLAYER", person_id=None)) is False


class TestSlAnsicht:
    def test_sl_sieht_den_echten_namen_immer(self):
        antwort = kontakt_fuer_gm(roh(echterNameBekannt=False))
        assert antwort.echterName == "Viktor Kane"
        assert antwort.npcName == "Viktor Kane"

    def test_sl_sieht_die_beschreibung_auch_bei_gesehen(self):
        antwort = kontakt_fuer_gm(roh(stufe="GESEHEN"))
        assert "rote Jacke" in antwort.beschreibung
