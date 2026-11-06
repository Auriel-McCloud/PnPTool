"""`_karte_fuer`: Fog-of-War-Schalter und Matrix-Hot-Live-Sicht (06.11.2026).

Reine Logik, keine DB: `_karte_fuer` nimmt fertige Dicts entgegen, die
DB-Aufrufe (fogOfWar-Einstellung, matrixLiveSicht) sitzen in separaten,
async Helferfunktionen, die hier nicht gebraucht werden.
"""

from app.kampf.routes import _karte_fuer


def token(tid, q, r, **extra):
    basis = {
        "id": tid,
        "name": tid,
        "hexQ": q,
        "hexR": r,
        "personId": tid,
        "personType": "PC",
        "besitzerId": None,
        "blickrichtung": 0,
        "versteckt": False,
        "rundumsicht": False,
        "bildUrl": "",
        "istGross": False,
    }
    basis.update(extra)
    return basis


def kampf_mit(teilnehmer: list[dict]) -> dict:
    return {"teilnehmer": teilnehmer, "_hotDrohnen": [], "_waende": []}


class TestFogAus:
    """Fog of War aus: Wahrheit statt Erinnerung, Versteckt bleibt wirksam."""

    def test_fog_aus_zeigt_hinten_live(self):
        a = token("a", 0, 0, blickrichtung=0)
        hinten = token("h", -2, 0, personType="NPC")
        kampf = kampf_mit([a, hinten])
        gesehen = _karte_fuer(kampf, {}, "PLAYER", "a", frozenset(), False)
        ziel = next(t for t in gesehen if t["id"] == "h")
        assert ziel["hexQ"] == -2

    def test_fog_aus_versteckt_bleibt_verborgen(self):
        a = token("a", 0, 0)
        b = token("b", 2, 0, versteckt=True, personId="b")
        kampf = kampf_mit([a, b])
        gesehen = _karte_fuer(kampf, {}, "PLAYER", "a", frozenset(), False)
        assert [t["id"] for t in gesehen] == ["a"]

    def test_fog_an_zeigt_hinten_als_erinnerung(self):
        a = token("a", 0, 0, blickrichtung=0)
        hinten = token("h", -2, 0, personType="NPC")
        kampf = kampf_mit([a, hinten])
        gesehen = _karte_fuer(kampf, {}, "PLAYER", "a", frozenset(), True)
        assert [t["id"] for t in gesehen] == ["a"]

    def test_gm_sieht_immer_wahrheit_unabhaengig_vom_schalter(self):
        a = token("a", 0, 0)
        b = token("b", -4, 0, versteckt=True, personId="b")
        kampf = kampf_mit([a, b])
        gesehen = _karte_fuer(kampf, {}, "GM", None, frozenset(), False)
        assert {t["id"] for t in gesehen} == {"a", "b"}


class TestHotLiveSicht:
    def test_live_sicht_zeigt_alles_auch_versteckte(self):
        a = token("a", 0, 0)
        b = token("b", -4, 0, versteckt=True, personId="b")
        kampf = kampf_mit([a, b])
        gesehen = _karte_fuer(kampf, {}, "PLAYER", "a", frozenset({"a"}), False)
        assert {t["id"] for t in gesehen} == {"a", "b"}

    def test_live_sicht_nur_fuer_den_berechtigten(self):
        a = token("a", 0, 0)
        b = token("b", -4, 0, personType="NPC")
        kampf = kampf_mit([a, b])
        gesehen = _karte_fuer(kampf, {}, "PLAYER", "b", frozenset({"a"}), False)
        # "b" selbst hat keine Live-Sicht -> normaler Fog-aus-Pfad, kein eigenes Auge auf b -> alles (kein Standpunkt)
        assert {t["id"] for t in gesehen} == {"a", "b"}
