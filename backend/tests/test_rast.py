"""Tests der Rast-Mechanik (siehe app/traits/rast.py und docs/api/rast.md
für die vollständige Herleitung).

Pro ausgewählter Person ist EIN Klick = EINE Rast: Schlagschaden heilt immer
vollständig, Tödlich-Schaden (schadenSchwer) sinkt sofort um 1 — kein
Zähler. Erst wenn Tödlich bei 0 steht, läuft ein Zähler für die (viel
langsamere) Schwerheilbar-Heilung mit, Wraparound bei genau 7 Rasten OHNE
offenen Tödlich-Schaden. Ist die Person danach komplett gesund, heilt
natürliche Rüstung mit Defizit mit — auch schon in derselben Rast. Daneben
der Fallback "Vollständige Heilung": keine Bedingungen, kein Würfeln.
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


class TestSchwererSchadenHeiltSofort:
    """Tödlich-Schaden (schadenSchwer) heilt pro Rast -1, ohne Zähler."""

    def test_schwerer_schaden_sinkt_um_eins(self):
        aenderung = person_aenderung({"schadenSchwer": 3})
        assert aenderung["schadenSchwer"] == 2

    def test_heilt_jede_rast_ohne_zaehler_solange_kein_schwerheilbar_offen(self):
        """Ohne Schwerheilbar-Schaden bleibt der Zähler grundsätzlich bei 0 —
        es gibt nichts, worauf er hinarbeiten könnte."""
        person = {"schadenSchwer": 6, "schwerHeilZaehler": 0}
        for erwarteter_schwer in range(5, -1, -1):
            person = person_aenderung(person)
            assert person["schadenSchwer"] == erwarteter_schwer
            assert person["schwerHeilZaehler"] == 0

    def test_ohne_schweren_schaden_bleibt_er_bei_null(self):
        aenderung = person_aenderung({"schadenSchwer": 0})
        assert aenderung["schadenSchwer"] == 0


class TestSchwerheilbarZaehlerLaeuftErstOhneToedlichenSchaden:
    """Der Zähler für die (langsame) Schwerheilbar-Heilung läuft nur, solange
    KEIN Tödlich-Schaden mehr offen ist — Mark, 12.10.2026: ursprünglich war
    das verkehrt herum (Zähler lief nur MIT offenem Tödlich-Schaden und fror
    ein, sobald der bei 0 stand, sodass reiner Schwerheilbar-Schaden nie
    heilte)."""

    def test_mit_offenem_toedlichem_schaden_bleibt_der_zaehler_stehen(self):
        aenderung = person_aenderung(
            {"schadenSchwer": 3, "schadenAggraviert": 1, "schwerHeilZaehler": 4}
        )
        assert aenderung["schadenSchwer"] == 2
        assert aenderung["schwerHeilZaehler"] == 4

    def test_sobald_toedlich_bei_null_steht_laeuft_der_zaehler_an(self):
        aenderung = person_aenderung(
            {"schadenSchwer": 0, "schadenAggraviert": 1, "schwerHeilZaehler": 0}
        )
        assert aenderung["schwerHeilZaehler"] == 1

    def test_laeuft_schon_in_der_rast_an_in_der_toedlich_null_wird(self):
        """Wird eine Person durch GENAU diese Rast von Tödlich-Schaden
        frei, zählt der Zähler schon in dieser Rast mit — nicht erst ab der
        nächsten (analog zur Rüstungsheilung)."""
        aenderung = person_aenderung(
            {"schadenSchwer": 1, "schadenAggraviert": 1, "schwerHeilZaehler": 0}
        )
        assert aenderung["schadenSchwer"] == 0
        assert aenderung["schwerHeilZaehler"] == 1

    def test_ohne_schwerheilbaren_schaden_bleibt_der_zaehler_bei_null(self):
        aenderung = person_aenderung(
            {"schadenSchwer": 0, "schadenAggraviert": 0, "schwerHeilZaehler": 0}
        )
        assert aenderung["schwerHeilZaehler"] == 0

    def test_zaehler_steigt_in_lockstep_bis_sechs(self):
        person = {"schadenSchwer": 0, "schadenAggraviert": 1, "schwerHeilZaehler": 0}
        for erwarteter_zaehler in range(1, 7):
            person = person_aenderung(person)
            assert person["schwerHeilZaehler"] == erwarteter_zaehler
            assert person["schadenAggraviert"] == 1


class TestWraparoundBeiGenauSieben:
    def test_wraparound_heilt_einen_schwerheilbar_punkt(self):
        aenderung = person_aenderung(
            {"schadenSchwer": 0, "schadenAggraviert": 2, "schwerHeilZaehler": 6}
        )
        # 6 + 1 = 7 >= Schwelle -> wrap: -7 = 0, Schwerheilbar -1
        assert aenderung["schwerHeilZaehler"] == 0
        assert aenderung["schadenAggraviert"] == 1

    def test_kurz_vor_der_schwelle_wrapt_noch_nicht(self):
        aenderung = person_aenderung(
            {"schadenSchwer": 0, "schadenAggraviert": 1, "schwerHeilZaehler": 5}
        )
        assert aenderung["schwerHeilZaehler"] == 6

    def test_sieben_volle_rasten_wraparound_end_to_end(self):
        """Sieben Rasten in Folge, Tödlich-Schaden bereits bei 0: am
        siebten Klick läuft der Zähler über."""
        person = {"schadenSchwer": 0, "schadenAggraviert": 3, "schwerHeilZaehler": 0}
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

    def test_noch_schwerheilbarer_schaden_ist_nicht_gesund(self):
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
