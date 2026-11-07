"""Letzte Sicht: Halbkreis, Gedächtnis, Versteckt, Rundumsicht."""

from app.battlemap.sicht import aktualisiere, ansicht, ansicht_waende, blockiert, ping, sektor, start_speicher, vorderkegel, zentrum
from app.campaigns.repository import EINSTELLUNGEN_DEFAULTS


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


class TestRichtung:
    def test_osten_ist_null(self):
        assert sektor(0, 0, 3, 0) == 0

    def test_gleiches_feld_hat_keine_richtung(self):
        assert sektor(1, 1, 1, 1) is None

    def test_vorderkegel_drei_von_sechs(self):
        assert vorderkegel(0) == {5, 0, 1}


class TestGedaechtnis:
    def test_start_kennt_alle(self):
        speicher = start_speicher([token("a", 0, 0), token("b", 0, -3, personType="NPC")])
        assert "b" in speicher["a"]

    def test_hinten_friert(self):
        a = token("a", 0, 0, blickrichtung=0)
        b = token("b", 0, -3, personType="NPC")
        speicher = start_speicher([a, b])
        b["hexQ"], b["hexR"] = 0, -6
        speicher = aktualisiere([a, b], speicher)
        gesehen = ansicht([a, b], speicher, rolle="PLAYER", person_id="a")
        geist = next(t for t in gesehen if t["id"] == "b")
        assert geist["veraltet"] is True
        assert (geist["hexQ"], geist["hexR"]) == (0, -3)

    def test_vorne_ist_frisch(self):
        a = token("a", 0, 0, blickrichtung=0)
        b = token("b", 2, 0, personType="NPC")
        speicher = aktualisiere([a, b], start_speicher([a, b]))
        b["hexQ"] = 3
        speicher = aktualisiere([a, b], speicher)
        gesehen = ansicht([a, b], speicher, rolle="PLAYER", person_id="a")
        ziel = next(t for t in gesehen if t["id"] == "b")
        assert ziel["veraltet"] is False
        assert ziel["hexQ"] == 3

    def test_versteckt_schlägt_den_kegel(self):
        a = token("a", 0, 0)
        b = token("b", 2, 0, versteckt=True, personType="PC", personId="b")
        speicher = aktualisiere([a, b], {})
        gesehen = ansicht([a, b], speicher, rolle="PLAYER", person_id="a")
        assert [t["id"] for t in gesehen] == ["a"]

    def test_eigener_versteckter_bleibt(self):
        a = token("a", 0, 0, versteckt=True)
        gesehen = ansicht([a], {}, rolle="PLAYER", person_id="a")
        assert gesehen[0]["id"] == "a"

    def test_rundumsicht_sieht_hinten_live(self):
        a = token("a", 0, 0, rundumsicht=True, blickrichtung=0)
        b = token("b", 0, -4, personType="NPC")
        speicher = start_speicher([a, b])
        b["hexR"] = -6
        speicher = aktualisiere([a, b], speicher)
        gesehen = ansicht([a, b], speicher, rolle="PLAYER", person_id="a")
        ziel = next(t for t in gesehen if t["id"] == "b")
        assert ziel["hexR"] == -6
        assert ziel["veraltet"] is False

    def test_drohne_eigene_augen_rigger_chrom_gilt_nicht(self):
        rigger = token("r", 0, 0, rundumsicht=True)
        drohne = token("d", 0, -2, personId="d", besitzerId="r", rundumsicht=False, blickrichtung=0)
        gegner = token("g", 0, -5, personType="NPC")
        speicher = start_speicher([rigger, drohne, gegner])
        gegner["hexR"] = -8
        speicher = aktualisiere([rigger, drohne, gegner], speicher)
        # Die Drohne schaut nach Osten, der Gegner liegt nordwest hinter ihr.
        # Der Rigger sieht rundum, also ist die Vereinigung live.
        gesehen = ansicht([rigger, drohne, gegner], speicher, rolle="PLAYER", person_id="r")
        ziel = next(t for t in gesehen if t["id"] == "g")
        assert ziel["hexR"] == -8

    def test_party_teilt_nicht(self):
        a = token("a", 0, 0, blickrichtung=0)
        freund = token("f", 1, 0, blickrichtung=2)
        gegner = token("g", 0, -4, personType="NPC")
        speicher = start_speicher([a, freund, gegner])
        gegner["hexR"] = -7
        speicher = aktualisiere([a, freund, gegner], speicher)
        gesehen = ansicht([a, freund, gegner], speicher, rolle="PLAYER", person_id="a")
        geist = next(t for t in gesehen if t["id"] == "g")
        assert geist["veraltet"] is True
        assert geist["hexR"] == -4

    def test_sl_sieht_wahrheit(self):
        a = token("a", 0, 0, versteckt=True)
        gesehen = ansicht([a], {}, rolle="GM", person_id=None)
        assert gesehen[0]["versteckt"] is True
        assert gesehen[0]["hexQ"] == 0


def test_fog_standard_aus():
    assert EINSTELLUNGEN_DEFAULTS["fogOfWar"] is False


def _kante_osten():
    """Gemeinsame Kante zwischen (0,0) und (1,0)."""
    a = zentrum(0, 0)
    import math

    return {
        "ax": a[0] + math.cos(math.radians(-30)),
        "ay": a[1] + math.sin(math.radians(-30)),
        "bx": a[0] + math.cos(math.radians(30)),
        "by": a[1] + math.sin(math.radians(30)),
    }


def _kante_westen():
    """Gemeinsame Kante zwischen (0,0) und (-1,0)."""
    a = zentrum(0, 0)
    import math

    return {
        "ax": a[0] + math.cos(math.radians(150)),
        "ay": a[1] + math.sin(math.radians(150)),
        "bx": a[0] + math.cos(math.radians(210)),
        "by": a[1] + math.sin(math.radians(210)),
    }


class TestWaende:
    def test_wand_blockiert_rundumsicht(self):
        a = token("a", 0, 0, rundumsicht=True)
        b = token("b", 2, 0, personType="NPC")
        wand = [_kante_osten()]
        assert blockiert(0, 0, 2, 0, wand) is True
        speicher = start_speicher([a, b], wand)
        assert "b" not in speicher["a"]
        gesehen = ansicht([a, b], speicher, rolle="PLAYER", person_id="a", waende=wand)
        assert [t["id"] for t in gesehen] == ["a"]

    def test_ohne_wand_sieht_rundum(self):
        a = token("a", 0, 0, rundumsicht=True)
        b = token("b", 2, 0, personType="NPC")
        speicher = aktualisiere([a, b], start_speicher([a, b]))
        gesehen = ansicht([a, b], speicher, rolle="PLAYER", person_id="a")
        assert next(t for t in gesehen if t["id"] == "b")["veraltet"] is False

    def test_wand_verdeckt_auch_ohne_kegel(self):
        a = token("a", 0, 0)
        b = token("b", 2, 0, personType="NPC")
        gesehen = ansicht_waende([a, b], rolle="PLAYER", person_id="a", waende=[_kante_osten()])
        assert [t["id"] for t in gesehen] == ["a"]

    def test_hinter_dem_blick_ist_weg(self):
        from app.battlemap.sicht import ansicht_jetzt

        a = token("a", 0, 0, blickrichtung=0)
        hinten = token("h", -3, 0, personType="NPC")
        speicher = start_speicher([a, hinten])
        hinten["hexQ"] = -6
        speicher = aktualisiere([a, hinten], speicher)
        gesehen = ansicht([a, hinten], speicher, rolle="PLAYER", person_id="a")
        geist = next(t for t in gesehen if t["id"] == "h")
        assert geist["veraltet"] is True
        assert geist["hexQ"] == -3

    def test_geist_hinter_neuer_wand_faellt(self):
        a = token("a", 0, 0, blickrichtung=0)
        b = token("b", 2, 0, personType="NPC")
        speicher = start_speicher([a, b])
        assert "b" in speicher["a"]
        wand = [_kante_osten()]
        speicher = aktualisiere([a, b], speicher, wand)
        assert "b" not in speicher["a"]
        gesehen = ansicht([a, b], speicher, rolle="PLAYER", person_id="a", waende=wand)
        assert [t["id"] for t in gesehen] == ["a"]


class TestMatrixPing:
    """Matrix-Navigation-Erfolg: ein Auge pingt seine eigene Erinnerung auf
    den aktuellen Stand, egal wohin es schaut (Mark, 06.11.2026)."""

    def test_ping_aktualisiert_auch_hinten_als_erinnerung(self):
        """Ping aktualisiert die Erinnerung (ALT-Position), macht aus dem
        hinteren Halbkreis aber kein Live-Sehen — dieselbe Erinnerungslogik
        wie beim normalen Hinsehen, nur mit frischerem Stand."""
        a = token("a", 0, 0, blickrichtung=0)
        hinten = token("h", -3, 0, personType="NPC")
        speicher = start_speicher([a, hinten])
        hinten["hexQ"] = -6
        speicher = ping([a, hinten], speicher, "a")
        gesehen = ansicht([a, hinten], speicher, rolle="PLAYER", person_id="a")
        ziel = next(t for t in gesehen if t["id"] == "h")
        assert ziel["veraltet"] is True
        assert ziel["hexQ"] == -6

    def test_ping_ist_nur_schnappschuss(self):
        a = token("a", 0, 0, blickrichtung=0)
        hinten = token("h", -3, 0, personType="NPC")
        speicher = ping([a, hinten], start_speicher([a, hinten]), "a")
        hinten["hexQ"] = -9
        speicher = aktualisiere([a, hinten], speicher)
        gesehen = ansicht([a, hinten], speicher, rolle="PLAYER", person_id="a")
        ziel = next(t for t in gesehen if t["id"] == "h")
        assert ziel["veraltet"] is True
        assert ziel["hexQ"] == -3

    def test_ping_findet_versteckte_nicht(self):
        a = token("a", 0, 0)
        b = token("b", -3, 0, versteckt=True, personType="PC", personId="b")
        speicher = ping([a, b], {}, "a")
        gesehen = ansicht([a, b], speicher, rolle="PLAYER", person_id="a")
        assert [t["id"] for t in gesehen] == ["a"]

    def test_ping_ignoriert_waende(self):
        """Matrix-Ortung ist kein Sichtkontakt — eine Wand hält kein
        Funksignal auf (Bugfix 06.11.2026, siehe docs/wiki)."""
        vorne = token("v", 2, 0, personType="NPC")
        a = token("a", 0, 0, blickrichtung=0)
        wand = [_kante_osten()]
        speicher = ping([a, vorne], {}, "a")
        assert "v" in speicher["a"]

    def test_ping_ueberlebt_aktualisiere_trotz_wand(self):
        """Bugfix 06.11.2026: ein ping-geortetes, wandblockiertes Ziel darf
        nicht beim nächsten Kartenzug irgendwo auf der Karte (jeder Zug ruft
        aktualisiere() auf) wieder aus der Erinnerung fallen — sonst wäre der
        Ping in der Praxis sofort wieder weg. Ziel liegt HINTER dem Decker
        (nicht im Kegel), damit der erste Durchlauf von aktualisiere() es
        nicht schon wegen 'im Kegel + blockiert' entfernt — das ist ein
        separater, akzeptierter Randfall wie bei normalen Geistern."""
        hinter_wand = token("h", -3, 0, personType="NPC")
        a = token("a", 0, 0, blickrichtung=0)  # schaut nach Osten, h liegt im Westen (hinten)
        wand = [_kante_westen()]
        speicher = ping([a, hinter_wand], {}, "a")
        assert "h" in speicher["a"]
        # Irgendein anderer Kartenzug löst aktualisiere() aus, mit derselben Wand:
        speicher = aktualisiere([a, hinter_wand], speicher, wand)
        assert "h" in speicher["a"], "Matrix-geortetes Ziel darf nicht am Wand-Verfallscheck hängen"

    def test_ping_unbekanntes_auge_bleibt_unveraendert(self):
        a = token("a", 0, 0)
        assert ping([a], {"a": {}}, "unbekannt") == {"a": {}}

    def test_ansicht_zeigt_ping_trotz_wand(self):
        """Bugfix 06.11.2026 (dritte Fundstelle): ansicht() prüft beim Lesen
        des Speichers UNABHÄNGIG von aktualisiere() nochmal selbst auf Wände
        (Zeile mit `blockiert(...)` im Geister-Zweig). Dieselbe
        matrixGeortet-Ausnahme muss auch hier greifen — sonst speichert der
        Ping korrekt, aber GET /kampf/karte zeigt trotzdem nur den Decker
        selbst, weil ansicht() die ping-georteten Ziele beim Rendern wieder
        rausfiltert (genau der Live-Fall, der nach dem ersten Fix noch kaputt
        war)."""
        hinter_wand = token("h", -3, 0, personType="NPC")
        a = token("a", 0, 0, blickrichtung=0)
        wand = [_kante_westen()]
        speicher = ping([a, hinter_wand], {}, "a")
        gesehen = ansicht([a, hinter_wand], speicher, rolle="PLAYER", person_id="a", waende=wand)
        assert any(t["id"] == "h" for t in gesehen), "ansicht() muss den Ping trotz Wand zeigen"


class TestAnsichtWaendeVersteckt:
    """Bugfix 06.11.2026: ohne Wände gab ansicht_waende Versteckte lautlos
    frei — Versteckt ist ein eigener Schalter, kein Teil von Fog of War."""

    def test_versteckt_schlaegt_auch_ganz_ohne_waende(self):
        a = token("a", 0, 0)
        b = token("b", 2, 0, versteckt=True, personType="PC", personId="b")
        gesehen = ansicht_waende([a, b], rolle="PLAYER", person_id="a", waende=[])
        assert [t["id"] for t in gesehen] == ["a"]

    def test_eigener_versteckter_bleibt_auch_ohne_waende(self):
        a = token("a", 0, 0, versteckt=True)
        gesehen = ansicht_waende([a], rolle="PLAYER", person_id="a", waende=None)
        assert gesehen[0]["id"] == "a"

    def test_unversteckte_bleiben_ohne_waende_sichtbar(self):
        a = token("a", 0, 0)
        b = token("b", 2, 0, personType="NPC")
        gesehen = ansicht_waende([a, b], rolle="PLAYER", person_id="a", waende=None)
        assert {t["id"] for t in gesehen} == {"a", "b"}
