"""Tests der Rast-Mechanik (siehe app/traits/rast.py und docs/api/rast.md
für die vollständige Herleitung).

Pro ausgewählter Person ist EIN Klick = EINE Rast: Schlagschaden heilt immer
vollständig, schwerer Schaden sinkt um 1 (mit einem Zähler fürs
Unheilbar-Wraparound bei genau 7), und ist die Person danach komplett
gesund, heilt natürliche Rüstung mit Defizit mit — auch schon in derselben
Rast. Daneben der Fallback "Vollständige Heilung": keine Bedingungen, kein
Würfeln.
"""

from app.kampf.ruestung import anwende_natuerliche_ruestung
from app.traits.rast import (
    ist_vollstaendig_gesund,
    person_aenderung,
    ruestung_heilung,
    vollheilung_person,
    vollheilung_ruestung,
)


def teil(id: str, aktuell: int, maximum: int, natuerlich: bool = False) -> dict:
    return {
        "id": id,
        "ruestungKaestchenAktuell": aktuell,
        "ruestungKaestchenMax": maximum,
        "istNatuerlich": natuerlich,
    }


class TestSchlagschadenHeiltImmer:
    def test_schlag_wird_immer_voll_geheilt(self):
        aenderung = person_aenderung({"schadenSchlag": 4})
        assert aenderung["schadenSchlag"] == 0

    def test_auch_ohne_schweren_schaden(self):
        """Schlag heilt unabhängig davon, ob überhaupt schwerer Schaden
        ansteht — Schritt 1 und 2 der Formel sind unabhängig voneinander."""
        aenderung = person_aenderung({"schadenSchlag": 6, "schadenSchwer": 0})
        assert aenderung == {
            "schadenSchlag": 0,
            "schadenSchwer": 0,
            "schadenAggraviert": 0,
            "schwerHeilZaehler": 0,
        }


class TestSchwerHeilZaehlerInkrementiert:
    """0->6 inkrementieren, kein Wraparound unter der Schwelle."""

    def test_schwerer_schaden_sinkt_um_eins(self):
        aenderung = person_aenderung({"schadenSchwer": 3})
        assert aenderung["schadenSchwer"] == 2

    def test_zaehler_steigt_um_eins_pro_rast(self):
        """Solange genug schwerer Schaden da ist, steigt der Zähler in
        Lockstep mit jeder Rast — 0 bis 6, noch unter der Wraparound-Schwelle."""
        person = {"schadenSchwer": 10, "schwerHeilZaehler": 0}
        for erwarteter_zaehler in range(1, 7):
            person = person_aenderung(person)
            assert person["schwerHeilZaehler"] == erwarteter_zaehler
            assert person["schadenSchwer"] == 10 - erwarteter_zaehler

    def test_ohne_schweren_schaden_bleibt_der_zaehler_stehen(self):
        aenderung = person_aenderung({"schadenSchwer": 0, "schwerHeilZaehler": 4})
        assert aenderung["schwerHeilZaehler"] == 4
        assert aenderung["schadenSchwer"] == 0


class TestWraparoundBeiGenauSieben:
    def test_wraparound_heilt_einen_unheilbar_punkt(self):
        aenderung = person_aenderung(
            {"schadenSchwer": 5, "schadenAggraviert": 2, "schwerHeilZaehler": 6}
        )
        # 6 + 1 = 7 >= Schwelle -> wrap: -7 = 0, Unheilbar -1
        assert aenderung["schwerHeilZaehler"] == 0
        assert aenderung["schadenAggraviert"] == 1
        assert aenderung["schadenSchwer"] == 4

    def test_wraparound_ohne_unheilbar_schaden_laesst_ihn_bei_null(self):
        aenderung = person_aenderung(
            {"schadenSchwer": 5, "schadenAggraviert": 0, "schwerHeilZaehler": 6}
        )
        assert aenderung["schwerHeilZaehler"] == 0
        assert aenderung["schadenAggraviert"] == 0

    def test_kurz_vor_der_schwelle_wrapt_noch_nicht(self):
        aenderung = person_aenderung({"schadenSchwer": 5, "schwerHeilZaehler": 5})
        assert aenderung["schwerHeilZaehler"] == 6

    def test_sieben_volle_rasten_wraparound_end_to_end(self):
        """Sieben Rasten in Folge mit durchgehend schwerem Schaden: am
        siebten Klick läuft der Zähler über."""
        person = {"schadenSchwer": 99, "schadenAggraviert": 3, "schwerHeilZaehler": 0}
        for i in range(1, 8):
            person = person_aenderung(person)
            if i < 7:
                assert person["schwerHeilZaehler"] == i
                assert person["schadenAggraviert"] == 3
            else:
                assert person["schwerHeilZaehler"] == 0
                assert person["schadenAggraviert"] == 2


class TestIstVollstaendigGesund:
    def test_alle_drei_arten_null_ist_gesund(self):
        assert ist_vollstaendig_gesund(
            {"schadenSchlag": 0, "schadenSchwer": 0, "schadenAggraviert": 0}
        )

    def test_noch_schwerer_schaden_ist_nicht_gesund(self):
        assert not ist_vollstaendig_gesund(
            {"schadenSchlag": 0, "schadenSchwer": 1, "schadenAggraviert": 0}
        )

    def test_noch_unheilbarer_schaden_ist_nicht_gesund(self):
        assert not ist_vollstaendig_gesund(
            {"schadenSchlag": 0, "schadenSchwer": 0, "schadenAggraviert": 1}
        )

    def test_direkt_nach_der_letzten_heilenden_rast_schon_gesund(self):
        """Wer durch GENAU diese Rast komplett gesund wird, gilt schon in
        dieser Rast als gesund — nicht erst ab der nächsten."""
        aenderung = person_aenderung({"schadenSchlag": 1, "schadenSchwer": 1, "schadenAggraviert": 0})
        assert aenderung["schadenSchwer"] == 0
        assert ist_vollstaendig_gesund(aenderung)


class TestNatuerlicheRuestungHeiltNurWennGesund:
    def test_ruestung_heilung_nur_bei_natuerlichen_teilen_mit_defizit(self):
        natuerlich_mit_defizit = teil("a", aktuell=3, maximum=5, natuerlich=True)
        natuerlich_voll = teil("b", aktuell=5, maximum=5, natuerlich=True)
        normal_mit_defizit = teil("c", aktuell=2, maximum=5, natuerlich=False)
        folgen = ruestung_heilung([natuerlich_mit_defizit, natuerlich_voll, normal_mit_defizit])
        assert folgen == [{"id": "a", "ruestungKaestchenAktuell": 4}]

    def test_ohne_natuerliche_teile_passiert_nichts(self):
        assert ruestung_heilung([teil("a", 1, 5, natuerlich=False)]) == []

    def test_heilung_ueberschreitet_nie_das_max(self):
        """+1 gecappt auf den aktuellen (live berechneten) Max — hier schon
        nur eines unter Max, die Funktion deckelt nicht nochmal extra, das
        Defizit-Prüfen VOR dem Aufruf reicht (aktuell < max garantiert
        aktuell+1 <= max)."""
        folgen = ruestung_heilung([teil("a", aktuell=4, maximum=5, natuerlich=True)])
        assert folgen == [{"id": "a", "ruestungKaestchenAktuell": 5}]


class TestVollstaendigeHeilung:
    def test_vollheilung_person_setzt_alles_auf_null(self):
        assert vollheilung_person() == {
            "schadenSchlag": 0,
            "schadenSchwer": 0,
            "schadenAggraviert": 0,
            "schwerHeilZaehler": 0,
        }

    def test_vollheilung_ruestung_heilt_auch_normale_teile(self):
        """Anders als die Rast-Heilung gilt hier KEINE istNatuerlich-
        Einschränkung — der Fallback heilt alles."""
        normal = teil("a", aktuell=1, maximum=9, natuerlich=False)
        natuerlich = teil("b", aktuell=0, maximum=4, natuerlich=True)
        voll = teil("c", aktuell=3, maximum=3, natuerlich=False)
        folgen = vollheilung_ruestung([normal, natuerlich, voll])
        assert folgen == [
            {"id": "a", "ruestungKaestchenAktuell": 9},
            {"id": "b", "ruestungKaestchenAktuell": 4},
        ]


class TestAnwendeNatuerlicheRuestungIntegration:
    """Zusammenspiel mit kampf/ruestung.py::anwende_natuerliche_ruestung —
    das Live-Max muss VOR ruestung_heilung berechnet sein, sonst heilt die
    Formel gegen den falschen (gespeicherten) Max-Wert."""

    def test_live_max_aus_widerstandsfaehigkeit_bestimmt_das_defizit(self):
        # Gespeicherter Max-Wert (5) ist Schrott — die echte Widerstands-
        # fähigkeit ist 8, davon hat die Rüstung erst 6 "gesammelt".
        roh = [teil("a", aktuell=6, maximum=5, natuerlich=True)]
        live = anwende_natuerliche_ruestung(roh, widerstandsfaehigkeit=8)
        assert live[0]["ruestungKaestchenMax"] == 8
        assert live[0]["ruestungKaestchenAktuell"] == 6
        folgen = ruestung_heilung(live)
        assert folgen == [{"id": "a", "ruestungKaestchenAktuell": 7}]

    def test_gesunkene_widerstandsfaehigkeit_klemmt_aktuell_auf_das_neue_max(self):
        roh = [teil("a", aktuell=6, maximum=5, natuerlich=True)]
        live = anwende_natuerliche_ruestung(roh, widerstandsfaehigkeit=3)
        assert live[0]["ruestungKaestchenMax"] == 3
        assert live[0]["ruestungKaestchenAktuell"] == 3
        # Kein Defizit mehr -> keine Heilung nötig.
        assert ruestung_heilung(live) == []
