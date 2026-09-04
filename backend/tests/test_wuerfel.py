"""Das NeotopiA-Würfelsystem.

Regelblatt (`docs/regeln-neotopia.md`, Zeilen 9-12):

* Pool aus zehnseitigen Würfeln, **1-5 Misserfolg, 6-10 Erfolg**.
* **Kritisch:** zwei Zehnen zählen wie vier Erfolge, drei wie sechs — jede
  weitere Zehn verdoppelt entsprechend.
* **Patzer:** die Hälfte der Würfel zeigt 1.

Marks Formulierung im Auftrag: *"alles über 5 ist ein Erfolg, Doppel 10 zählt
als 4 Erfolge"* — deckungsgleich.
"""

import pytest

from app.wuerfel.logic import (
    ist_patzer,
    werte_wurf,
    zaehle_erfolge,
)


class TestErfolgeZaehlen:
    def test_sechs_bis_zehn_sind_erfolge(self):
        assert zaehle_erfolge([6, 7, 8, 9]) == 4

    def test_eins_bis_fuenf_sind_misserfolge(self):
        assert zaehle_erfolge([1, 2, 3, 4, 5]) == 0

    def test_fuenf_ist_noch_kein_erfolg(self):
        # "alles über 5" — die 5 selbst zählt nicht.
        assert zaehle_erfolge([5]) == 0

    def test_leerer_pool_gibt_null(self):
        assert zaehle_erfolge([]) == 0


class TestZehnen:
    def test_eine_zehn_ist_ein_erfolg(self):
        assert zaehle_erfolge([10]) == 1

    def test_zwei_zehnen_zaehlen_wie_vier(self):
        # Marks Regel: "Doppel 10 zählt als 4 Erfolge".
        assert zaehle_erfolge([10, 10]) == 4

    def test_drei_zehnen_zaehlen_wie_sechs(self):
        assert zaehle_erfolge([10, 10, 10]) == 6

    def test_vier_zehnen_zaehlen_wie_acht(self):
        # "jede weitere Zehn verdoppelt entsprechend" — 4 Zehnen = 8.
        assert zaehle_erfolge([10, 10, 10, 10]) == 8

    def test_zehnen_und_normale_erfolge_addieren_sich(self):
        # 2 Zehnen = 4, plus zwei einfache Erfolge = 6.
        assert zaehle_erfolge([10, 10, 7, 8]) == 6

    def test_zwei_zehnen_neben_misserfolgen(self):
        assert zaehle_erfolge([10, 10, 1, 2, 3]) == 4


class TestPatzer:
    def test_haelfte_einsen_ist_patzer(self):
        assert ist_patzer([1, 1, 5, 4]) is True

    def test_weniger_als_die_haelfte_ist_kein_patzer(self):
        assert ist_patzer([1, 5, 4, 6]) is False

    def test_mehr_als_die_haelfte_ist_patzer(self):
        assert ist_patzer([1, 1, 1, 4]) is True

    def test_ungerader_pool_braucht_aufgerundete_haelfte(self):
        # 5 Würfel: 3 Einsen sind die Hälfte oder mehr.
        assert ist_patzer([1, 1, 1, 5, 6]) is True
        assert ist_patzer([1, 1, 5, 5, 6]) is False

    def test_leerer_pool_ist_kein_patzer(self):
        assert ist_patzer([]) is False


class TestWurfAuswerten:
    def test_wurf_liefert_augen_und_erfolge(self):
        ergebnis = werte_wurf([10, 10, 6, 2])
        assert ergebnis["augen"] == [10, 10, 6, 2]
        assert ergebnis["erfolge"] == 5
        assert ergebnis["patzer"] is False

    def test_wurf_meldet_patzer(self):
        ergebnis = werte_wurf([1, 1, 3, 4])
        assert ergebnis["erfolge"] == 0
        assert ergebnis["patzer"] is True

    def test_augen_bleiben_in_wurfreihenfolge(self):
        # Für die Anzeige am Tisch: man will sehen, was gefallen ist.
        ergebnis = werte_wurf([3, 10, 7])
        assert ergebnis["augen"] == [3, 10, 7]


class TestWuerfeln:
    def test_pool_bestimmt_die_anzahl_der_augen(self):
        from app.wuerfel.logic import wuerfle

        ergebnis = wuerfle(7)
        assert len(ergebnis["augen"]) == 7

    def test_alle_augen_liegen_zwischen_eins_und_zehn(self):
        from app.wuerfel.logic import wuerfle

        for _ in range(50):
            ergebnis = wuerfle(10)
            assert all(1 <= a <= 10 for a in ergebnis["augen"])

    def test_pool_null_wuerfelt_nicht(self):
        from app.wuerfel.logic import wuerfle

        ergebnis = wuerfle(0)
        assert ergebnis["augen"] == []
        assert ergebnis["erfolge"] == 0

    def test_negativer_pool_wuerfelt_nicht(self):
        from app.wuerfel.logic import wuerfle

        assert wuerfle(-3)["augen"] == []

    def test_pool_ist_nach_oben_begrenzt(self):
        # Schutz vor einem Tippfehler wie 99999, der den Server beschäftigt.
        from app.wuerfel.logic import MAX_POOL, wuerfle

        with pytest.raises(ValueError):
            wuerfle(MAX_POOL + 1)
