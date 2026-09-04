"""Die Initiativliste darf Spielern keine echten NPC-Namen verraten.

Marks Vorgabe: *"die Spieler dürfen nur die Alias Namen der NPCs sehen nicht
ihre richtigen Namen!"*

Bewiesener Ausgangszustand (03.09.2026): `GET .../kampf` lieferte die Liste
ungefiltert an jeden mit Kampagnenzugang — ein Spieler las den echten Namen
eines NPC im Klartext.
"""

from app.kampf.sichtbarkeit import fuer_spieler


def t(**kwargs) -> dict:
    """Ein Teilnehmer mit sinnvollen Vorgaben."""
    basis = {
        "id": "t-1",
        "name": "Viktor Kane",
        "initiative": 7,
        "kampfart": "NAHKAMPF",
        "notiz": "",
        "erledigt": False,
        "personId": None,
        "personType": None,
        "begleiterId": None,
    }
    basis.update(kwargs)
    return basis


class TestEchteNamenBleibenGeheim:
    def test_npc_erscheint_unter_alias(self):
        liste = fuer_spieler(
            [t(personId="p-1", personType="NPC")],
            rassen={"p-1": "Ork"},
        )
        assert liste[0]["name"] == "Unbekannter Ork"
        assert "Viktor" not in liste[0]["name"]

    def test_npc_ohne_rasse_wird_unbekannte_person(self):
        liste = fuer_spieler([t(personId="p-1", personType="NPC")], rassen={"p-1": ""})
        assert liste[0]["name"] == "Unbekannte Person"

    def test_pcs_behalten_ihren_namen(self):
        # Die Mitspieler kennen einander — sonst wäre die Liste unbrauchbar.
        liste = fuer_spieler(
            [t(name="Ryu Tanaka", personId="p-2", personType="PC")],
            rassen={"p-2": "Mensch"},
        )
        assert liste[0]["name"] == "Ryu Tanaka"

    def test_freier_eintrag_bleibt_wie_eingetragen(self):
        # "Wachmann 1" hat der SL selbst getippt; das ist kein Geheimnis.
        liste = fuer_spieler([t(name="Wachmann 1")], rassen={})
        assert liste[0]["name"] == "Wachmann 1"

    def test_persoenlicher_alias_gewinnt_gegen_standard(self):
        # Später, wenn das Kontaktsystem steht: "der Schläger vom Hafen".
        liste = fuer_spieler(
            [t(personId="p-1", personType="NPC")],
            rassen={"p-1": "Ork"},
            aliase={"p-1": "Der Schläger"},
        )
        assert liste[0]["name"] == "Der Schläger"

    def test_notiz_wird_entfernt(self):
        # Die Notiz ist die Gedächtnisstütze der SL ("blutet, flieht bei 2 HP").
        liste = fuer_spieler([t(personId="p-1", personType="NPC", notiz="flieht bald")], rassen={"p-1": "Ork"})
        assert liste[0]["notiz"] == ""

    def test_notiz_am_eigenen_pc_bleibt(self):
        liste = fuer_spieler(
            [t(name="Ryu", personId="p-2", personType="PC", notiz="vergiftet")],
            rassen={},
            eigene_person_id="p-2",
        )
        assert liste[0]["notiz"] == "vergiftet"

    def test_reihenfolge_und_initiative_bleiben_erhalten(self):
        # Mark: "volle Liste wie jetzt" — nur die Namen sind geschützt.
        liste = fuer_spieler(
            [
                t(id="a", name="Ryu", initiative=9, personId="p-2", personType="PC"),
                t(id="b", name="Viktor Kane", initiative=7, personId="p-1", personType="NPC"),
            ],
            rassen={"p-1": "Ork"},
        )
        assert [x["id"] for x in liste] == ["a", "b"]
        assert [x["initiative"] for x in liste] == [9, 7]

    def test_die_urspruengliche_liste_bleibt_unveraendert(self):
        # Sonst verändert ein Spieleraufruf den Zustand für alle anderen.
        original = [t(personId="p-1", personType="NPC")]
        fuer_spieler(original, rassen={"p-1": "Ork"})
        assert original[0]["name"] == "Viktor Kane"

    def test_begleiter_eines_npc_bleibt_verdeckt(self):
        liste = fuer_spieler(
            [t(name="Kampfdrohne von Viktor", begleiterId="b-1")],
            rassen={},
            begleiter_besitzer={"b-1": "p-1"},
            npc_ids={"p-1"},
        )
        assert liste[0]["name"] == "Unbekannte Begleitung"

    def test_begleiter_eines_pc_bleibt_sichtbar(self):
        liste = fuer_spieler(
            [t(name="Rex", begleiterId="b-2")],
            rassen={},
            begleiter_besitzer={"b-2": "p-2"},
            npc_ids=set(),
        )
        assert liste[0]["name"] == "Rex"
