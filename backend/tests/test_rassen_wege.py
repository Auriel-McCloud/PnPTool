"""Weg-Sperre an der Rasse (20.11.2026): leere Liste = alle Wege, nur einer = automatisch."""

from app.traits import erstellung

ALLE = ["KEINER", "MAGIER", "HAERETIKER", "NEUROWEAVER"]


def test_leere_liste_heisst_alle_wege():
    assert erstellung.erlaubte_wege({}) == ALLE
    assert erstellung.erlaubte_wege({"erlaubteWege": []}) == ALLE
    assert erstellung.erlaubte_wege(None) == ALLE


def test_reihenfolge_wie_wege_und_unbekanntes_faellt_raus():
    assert erstellung.erlaubte_wege({"erlaubteWege": ["NEUROWEAVER", "FOO", "MAGIER"]}) == ["MAGIER", "NEUROWEAVER"]


def test_weg_fuer_rasse_nimmt_ersten_erlaubten():
    nur_magier = {"erlaubteWege": ["MAGIER"]}
    assert erstellung.weg_fuer_rasse("KEINER", nur_magier) == "MAGIER"
    assert erstellung.weg_fuer_rasse("MAGIER", nur_magier) == "MAGIER"
    assert erstellung.weg_fuer_rasse("NEUROWEAVER", {}) == "NEUROWEAVER"


def test_weg_fehler_unterscheidet_haeretiker_von_magier():
    rassen = {"Quill": {"erlaubteWege": ["MAGIER"]}, "Mensch": {}}
    assert erstellung.weg_fehler("MAGIER", "Quill", rassen) is None
    fehler = erstellung.weg_fehler("HAERETIKER", "Quill", rassen)
    assert fehler and "Häretiker" in fehler and "Magier" in fehler
    assert erstellung.weg_fehler("NEUROWEAVER", "Mensch", rassen) is None
    # Unbekannte Rasse meldet pruefe() selbst.
    assert erstellung.weg_fehler("MAGIER", "Gibtsnicht", rassen) is None


def test_regelwerk_schreibt_erlaubte_wege_aus():
    rassen = {
        "Quill": {"modifikatoren": {}, "freiePunkte": [7, 5, 3], "beschreibung": "", "erlaubteWege": ["NEUROWEAVER"]},
        "Mensch": {"modifikatoren": {}, "freiePunkte": [7, 5, 3], "beschreibung": ""},
    }
    regeln = erstellung.regelwerk(rassen)
    nach_name = {r["name"]: r for r in regeln["rassen"]}
    assert nach_name["Quill"]["erlaubteWege"] == ["NEUROWEAVER"]
    assert nach_name["Mensch"]["erlaubteWege"] == ALLE


def test_ki_konzept_text_nennt_gesperrte_wege():
    rassen = {"Quill": {"modifikatoren": {}, "freiePunkte": [7, 5, 3], "erlaubteWege": ["MAGIER"]}}
    assert "Weg nur: MAGIER" in erstellung.ki_konzept_text(rassen)
