"""Reine Hex-Regeln der Battlemap, ohne Datenbank."""

from app.battlemap.hex import (
    distanz,
    drop_frei,
    nachbarn,
    naechster_freier,
    reichweite,
    spawn_platz,
    y_felder,
)


class TestDistanz:
    def test_gleiches_feld_ist_null(self):
        assert distanz(0, 0, 0, 0) == 0

    def test_nachbar_ist_eins(self):
        assert distanz(0, 0, 1, 0) == 1

    def test_zwei_schritte(self):
        assert distanz(0, 0, 2, -1) == 2


class TestNachbarn:
    def test_sechs_nachbarn(self):
        assert len(nachbarn(0, 0)) == 6

    def test_jeder_nachbar_hat_distanz_eins(self):
        for q, r in nachbarn(3, -2):
            assert distanz(3, -2, q, r) == 1


class TestYFelder:
    def test_normal_ist_ein_feld(self):
        assert y_felder(4, 1, gross=False) == {(4, 1)}

    def test_gross_sind_drei_felder(self):
        felder = y_felder(0, 0, gross=True, drehung=0)
        assert len(felder) == 3
        assert (0, 0) in felder

    def test_gross_haengt_zusammen(self):
        felder = list(y_felder(0, 0, gross=True, drehung=0))
        a, b, c = felder
        assert distanz(*a, *b) == 1
        assert distanz(*a, *c) == 1 or distanz(*b, *c) == 1


class TestReichweite:
    def test_laufen_ist_drei_plus_sportlichkeit(self):
        assert reichweite(sportlichkeit=2, fliegen=None) == 5

    def test_drohne_ist_drei_plus_fliegen_mal_zwei(self):
        assert reichweite(sportlichkeit=0, fliegen=3) == 9

    def test_fliegen_null_bleibt_drei(self):
        assert reichweite(sportlichkeit=0, fliegen=0) == 3


class TestNaechsterFreier:
    def test_start_frei_nimmt_start(self):
        assert naechster_freier(2, 3, belegt=set()) == (2, 3)

    def test_start_belegt_nimmt_nachbarn(self):
        frei = naechster_freier(0, 0, belegt={(0, 0)})
        assert frei in nachbarn(0, 0)

    def test_ring_voll_geht_weiter(self):
        ring = {(0, 0), *nachbarn(0, 0)}
        frei = naechster_freier(0, 0, belegt=ring)
        assert frei is not None
        assert frei not in ring
        assert distanz(0, 0, *frei) == 2


class TestDropFrei:
    def test_leeres_feld_ist_frei(self):
        assert drop_frei(1, 1, gross=False, eigene_id="a", belegt={}) is True

    def test_fremdes_feld_ist_gesperrt(self):
        assert drop_frei(1, 1, gross=False, eigene_id="a", belegt={(1, 1): "b"}) is False

    def test_eigenes_feld_bleibt_frei(self):
        assert drop_frei(1, 1, gross=False, eigene_id="a", belegt={(1, 1): "a"}) is True

    def test_gross_braucht_drei_freie(self):
        y = y_felder(0, 0, gross=True, drehung=0)
        eines = next(p for p in y if p != (0, 0))
        assert drop_frei(0, 0, gross=True, drehung=0, eigene_id="a", belegt={eines: "b"}) is False


class TestSpawnPlatz:
    def test_nimmt_das_startfeld(self):
        assert spawn_platz(5, 5, gross=False, belegt={}) == (5, 5, 0)

    def test_weicht_auf_nachbarn_aus(self):
        q, r, _dreh = spawn_platz(0, 0, gross=False, belegt={(0, 0): "x"})
        assert (q, r) in nachbarn(0, 0)
