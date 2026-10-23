"""Überblick für die vorgefertigte Charakterwahl — ohne Datenbank.

Der Spieler soll vor dem dauerhaften Übernehmen sehen, wohin die Punkte
gefallen sind: drei Spalten wie auf dem Papierblatt, nicht der volle Bogen.
Sphären und NeuroWeaving gehören nicht in diese drei Spalten — sonst wirkt
ein Magier geistig, nur weil er zaubert.
"""

from app.players.auswahl_steckbrief import spalten_summen
from app.players.schemas import VorgefertigterCharakter
from app.traits.seed import NEOTOPIA_TRAITS


def test_attribute_landen_in_ihrer_spalte():
    summen = spalten_summen(
        [
            {"name": "Körperkraft", "category": "AttributKörperlich", "rating": 4},
            {"name": "Charisma", "category": "AttributGesellschaftlich", "rating": 2},
            {"name": "Intelligenz", "category": "AttributGeistig", "rating": 5},
        ]
    )
    assert summen["attribute"] == {"koerperlich": 4, "gesellschaftlich": 2, "geistig": 5}


def test_fertigkeiten_folgen_den_drei_blattspalten():
    summen = spalten_summen(
        [
            {"name": "Schusswaffen", "category": "Fertigkeit", "rating": 4},
            {"name": "Etiketten", "category": "Fertigkeit", "rating": 3},
            {"name": "Wahrnehmung", "category": "Fertigkeit", "rating": 2},
        ]
    )
    assert summen["fertigkeiten"] == {"koerperlich": 4, "gesellschaftlich": 3, "geistig": 2}


def test_sphaeren_und_neuroweaving_bleiben_ausserhalb_der_spalten():
    summen = spalten_summen(
        [
            {"name": "Kräfte", "category": "Sphäre", "rating": 3},
            {"name": "Leben", "category": "Sphäre", "rating": 2},
            {"name": "Brute Force", "category": "NeuroWeaving", "rating": 4},
            {"name": "NeuroWeaving", "category": "NeuroWeavingWert", "rating": 1},
            {"name": "Ermitteln", "category": "Fertigkeit", "rating": 2},
        ]
    )
    assert summen["fertigkeiten"]["geistig"] == 2
    assert summen["sphaeren"] == 5
    assert summen["neuroweaving"] == 4


def test_null_und_fremde_werte_zaehlen_nicht():
    summen = spalten_summen(
        [
            {"name": "Körperkraft", "category": "AttributKörperlich", "rating": 0},
            {"name": "Kontakte", "category": "Hintergrund", "rating": 3},
            {"name": None, "category": None, "rating": None},
        ]
    )
    assert summen["attribute"] == {"koerperlich": 0, "gesellschaftlich": 0, "geistig": 0}
    assert summen["fertigkeiten"] == {"koerperlich": 0, "gesellschaftlich": 0, "geistig": 0}
    assert summen["sphaeren"] == 0
    assert summen["neuroweaving"] == 0


def test_ueberblick_passt_in_die_auswahl_antwort():
    summen = spalten_summen(
        [{"name": "Körperkraft", "category": "AttributKörperlich", "rating": 3}]
    )
    modell = VorgefertigterCharakter(
        id="p1",
        name="Nyx",
        konzept="Abgehalfterter Konzernanwalt mit Zugang",
        ambition="Den alten Ausweis zurück",
        ziel="Heute Nacht ins Archiv",
        **summen,
    )
    assert modell.attribute.koerperlich == 3
    assert modell.konzept == "Abgehalfterter Konzernanwalt mit Zugang"
    assert modell.ambition == "Den alten Ausweis zurück"
    assert modell.ziel == "Heute Nacht ins Archiv"


def test_jede_kernfertigkeit_hat_genau_eine_spalte():
    fertigkeiten = [name for name, kategorie, _, _ in NEOTOPIA_TRAITS if kategorie == "Fertigkeit"]
    assert len(fertigkeiten) == 30
    spalten = []
    for name in fertigkeiten:
        summen = spalten_summen([{"name": name, "category": "Fertigkeit", "rating": 1}])
        getroffen = [spalte for spalte, wert in summen["fertigkeiten"].items() if wert == 1]
        assert getroffen == [getroffen[0]], name
        spalten.append(getroffen[0])
    assert spalten.count("koerperlich") == 10
    assert spalten.count("gesellschaftlich") == 10
    assert spalten.count("geistig") == 10
