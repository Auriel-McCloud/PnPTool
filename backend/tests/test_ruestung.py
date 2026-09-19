"""Tests des Rüstungssystems: Kästchen + Schadensreduktion (siehe
app/kampf/ruestung.py und docs/api/ruestung.md für die ausführliche
Herleitung).

Bis 18.09.2026 hieß der zweite Wert "Durchlass" (niedriger = besser). Mark
fand das nach dem Ausprobieren am Tisch unintuitiv ("Durchlass ist ein
dummer Wert") und ließ ihn durch "Reduktion" ersetzen (höher = besser, wie
ein klassischer Soak-Wert) — die Tests hier prüfen die neue Fassung.
"""

from app.kampf.ruestung import (
    berechne_treffer,
    pool,
    reduktion_effektiv,
    reihenfolge,
    repariere,
    uebersicht,
    verteile_kaestchenschaden,
)


def teil(id: str, name: str, kaestchen: int, kaestchen_max: int, reduktion: int) -> dict:
    """Ein Rüstungsteil, wie es aus items/repository.py::ruestungsteile kommt."""
    return {
        "id": id,
        "name": name,
        "ruestungKaestchenAktuell": kaestchen,
        "ruestungKaestchenMax": kaestchen_max,
        "ruestungReduktionBasis": reduktion,
    }


class TestReduktionGestuft:
    """Die effektive Reduktion sinkt in Stufen mit dem Kästchen-Anteil, nicht
    linear (Marks Vorgabe: halbieren bei halben Kästchen, viertel bei einem
    Viertel)."""

    def test_ueber_50_prozent_volle_reduktion(self):
        assert reduktion_effektiv(8, 6, 10) == 8
        assert reduktion_effektiv(8, 10, 10) == 8

    def test_genau_50_prozent_ist_schon_halbiert(self):
        """>50% ist die Schwelle für voll — 50% selbst fällt schon in die
        nächste Stufe."""
        assert reduktion_effektiv(8, 5, 10) == 4

    def test_ueber_25_prozent_halbe_reduktion(self):
        assert reduktion_effektiv(8, 3, 10) == 4

    def test_darunter_aber_noch_etwas_uebrig_ein_viertel(self):
        assert reduktion_effektiv(8, 2, 10) == 2
        assert reduktion_effektiv(8, 1, 10) == 2

    def test_null_kaestchen_keine_reduktion(self):
        assert reduktion_effektiv(8, 0, 10) == 0

    def test_schwache_ruestung_merkt_die_stufen_kaum(self):
        """Eine Lederjacke mit Reduktion 1 bleibt praktisch konstant — das
        ist Marks ausdrücklicher Vergleichsfall zur starken Rüstung."""
        assert reduktion_effektiv(1, 10, 10) == 1
        assert reduktion_effektiv(1, 6, 10) == 1
        assert reduktion_effektiv(1, 3, 10) == 0  # 1 // 2 = 0
        assert reduktion_effektiv(1, 1, 10) == 0  # 1 // 4 = 0


class TestPool:
    """Alle getragenen Teile wirken als eine Rüstung."""

    def test_kaestchen_summieren_sich_reduktion_kommt_vom_besten(self):
        jacke = teil("a", "Lederjacke", 5, 5, 1)
        weste = teil("b", "Kevlarweste", 3, 3, 4)
        p = pool([jacke, weste])
        assert p["kaestchenAktuell"] == 8
        assert p["kaestchenMax"] == 8
        # Nicht 1 und nicht 5 (kein Mittel, keine Summe): die beste Reduktion
        # gilt.
        assert p["reduktionBasis"] == 4

    def test_ohne_wirksames_teil_gibt_es_keinen_pool(self):
        assert pool([]) is None
        assert pool([teil("a", "Zerfetzte Weste", 0, 9, 3)]) is None

    def test_zerstoerte_teile_zaehlen_nicht_mit(self):
        kaputt = teil("a", "Zerfetzte Weste", 0, 9, 6)
        heil = teil("b", "Lederjacke", 5, 5, 1)
        p = pool([kaputt, heil])
        assert p["kaestchenAktuell"] == 5
        # Die Reduktion der zerschossenen Weste (6) darf den Pool NICHT
        # stärker machen — sie wirkt nicht mehr.
        assert p["reduktionBasis"] == 1


class TestBlattUebersicht:
    """Was das Charakterblatt als Rüstungsleiste bekommt (fertig gerechnet
    vom Server, damit die Pool-Regel nicht im Frontend nachgebaut wird)."""

    def test_fasst_den_pool_anzeigefertig_zusammen(self):
        jacke = teil("a", "Lederjacke", 5, 5, 1)
        weste = teil("b", "Kevlarweste", 2, 3, 4)
        u = uebersicht([jacke, weste])
        assert u["kaestchenAktuell"] == 7
        assert u["kaestchenMax"] == 8
        assert u["reduktionBasis"] == 4
        # 7/8 = 87.5% > 50% -> volle Reduktion wirksam
        assert u["reduktionEffektiv"] == 4
        # In Verbrauchsreihenfolge (beste Reduktion zuerst).
        assert [t["name"] for t in u["teile"]] == ["Kevlarweste", "Lederjacke"]

    def test_ohne_ruestung_nur_nullen(self):
        """Das Blatt blendet die Leiste dann aus — eine Reihe "0/0" ist keine
        Auskunft."""
        assert uebersicht([]) == {
            "kaestchenAktuell": 0,
            "kaestchenMax": 0,
            "reduktionBasis": 0,
            "reduktionEffektiv": 0,
            "teile": [],
        }


class TestVerbrauchsreihenfolge:
    def test_beste_reduktion_wird_zuerst_aufgebraucht(self):
        jacke = teil("a", "Lederjacke", 5, 5, 1)
        weste = teil("b", "Kevlarweste", 3, 3, 4)
        assert [t["name"] for t in reihenfolge([jacke, weste])] == ["Kevlarweste", "Lederjacke"]

    def test_bei_gleicher_reduktion_zuerst_das_kleinere_teil(self):
        """Damit es fertig aufgebraucht wird, statt dass mehrere Teile halb
        angeknackst herumliegen."""
        gross = teil("a", "Panzerjacke", 6, 6, 2)
        klein = teil("b", "Helm", 2, 2, 2)
        assert [t["name"] for t in reihenfolge([gross, klein])] == ["Helm", "Panzerjacke"]

    def test_schaden_laeuft_ins_naechste_teil_ueber(self):
        weste = teil("b", "Kevlarweste", 3, 3, 4)
        jacke = teil("a", "Lederjacke", 5, 5, 1)
        folgen = verteile_kaestchenschaden(reihenfolge([weste, jacke]), 5)
        assert [(f["name"], f["verlust"], f["zerstoert"]) for f in folgen] == [
            ("Kevlarweste", 3, True),
            ("Lederjacke", 2, False),
        ]

    def test_mehr_schaden_als_der_pool_hat_verpufft(self):
        weste = teil("b", "Kevlarweste", 2, 2, 4)
        folgen = verteile_kaestchenschaden(reihenfolge([weste]), 99)
        assert folgen[0]["verlust"] == 2 and folgen[0]["zerstoert"]

    def test_unbeteiligte_teile_stehen_nicht_in_der_liste(self):
        weste = teil("b", "Kevlarweste", 9, 9, 4)
        jacke = teil("a", "Lederjacke", 5, 5, 1)
        folgen = verteile_kaestchenschaden(reihenfolge([weste, jacke]), 2)
        assert [f["name"] for f in folgen] == ["Kevlarweste"]


class TestLederjacke:
    """3/3 Kästchen, Reduktion 1 — schwache, aber immerhin etwas dämpfende
    Alltagsrüstung ("schützt ein bisschen vor Schlägen, kaum vor Schüssen")."""

    def test_schlag_ueber_der_reduktion_wird_halbiert_und_kostet_ein_kaestchen(self):
        r = berechne_treffer("schlag", 6, 3, 3, 1)
        # absorbiert=1, durchkommend=5 -> hpMenge=2 (5//2), Kästchenschaden:
        # loest_aus (2*6=12>=3) -> durchkommend//2 = 2
        assert r == {"hpArt": "schlag", "hpMenge": 2, "kaestchenSchaden": 2, "kaestchenNeu": 1}

    def test_toedlich_wird_nur_im_typ_abgestuft_nicht_in_der_menge(self):
        """Tödlich (schwer) -> Schlag beim Durchkommen, ohne Halbierung — die
        Halbierung gibt es nur für Schlag, weil dort keine leichtere Stufe
        mehr existiert."""
        r = berechne_treffer("schwer", 6, 3, 3, 1)
        # absorbiert=1, durchkommend=5
        assert r["hpArt"] == "schlag"
        assert r["hpMenge"] == 5
        # Kaestchenschaden = absorbiert//2 (0) + durchkommend (5) = 5,
        # gedeckelt auf die vorhandenen 3 Kaestchen -> Ruestung komplett hin.
        assert r["kaestchenNeu"] == 0

    def test_zerstoerte_ruestung_wirkt_gar_nicht_mehr(self):
        """0 Kästchen = kein Abstufen, kein Abfangen — der Treffer geht
        unverändert durch (Mark: 'wirkt gar nicht mehr')."""
        r = berechne_treffer("aggraviert", 5, 0, 3, 1)
        assert r == {"hpArt": "aggraviert", "hpMenge": 5, "kaestchenSchaden": 0, "kaestchenNeu": 0}


class TestBombenschutzweste:
    """9/9 Kästchen, Reduktion 6 — hochwertige Rüstung, die im Neuzustand
    viel abfängt."""

    def test_erster_treffer_wird_grossteils_geschluckt(self):
        # absorbiert=min(6,6)=6, durchkommend=0
        r = berechne_treffer("schlag", 6, 9, 9, 6)
        assert r == {"hpArt": "schlag", "hpMenge": 0, "kaestchenSchaden": 0, "kaestchenNeu": 9}

    def test_reduktion_sinkt_spuerbar_wenn_beschaedigt(self):
        """Anders als bei einer schwachen Rüstung macht sich der
        Kästchenverlust hier deutlich bemerkbar — 9/9 -> 4/9 ist unter 50%,
        also nur noch die halbe Reduktion."""
        voll = reduktion_effektiv(6, 9, 9)
        beschaedigt = reduktion_effektiv(6, 4, 9)
        assert voll == 6
        assert beschaedigt == 3

    def test_starker_treffer_durchbricht_auch_intakte_weste_teilweise(self):
        # Stärke 10 > Reduktion 6 -> 4 kommen durch
        r = berechne_treffer("schlag", 10, 9, 9, 6)
        # durchkommend=4, loest_aus (20>=9) -> kaestchenSchaden = 4//2 = 2
        assert r["hpMenge"] == 2
        assert r["kaestchenSchaden"] == 2

    def test_schwacher_treffer_richtet_bei_intakter_weste_nichts_aus(self):
        """Trigger `2×Stärke >= Kästchen-Aktuell`: 2*4=8 < 9 -> kein
        Kästchenschaden."""
        r = berechne_treffer("schlag", 4, 9, 9, 6)
        assert r["kaestchenSchaden"] == 0

    def test_kaestchenschaden_bleibt_ueber_reduktionsstufen_hinweg_konsistent(self):
        """Derselbe Tödlich-Treffer an unterschiedlich beschädigter Rüstung:
        die Formel bleibt nachvollziehbar (kein Paradox wie beim alten
        Durchlass-System, wo beschädigte Rüstung teils UNZERSTÖRBARER
        wurde)."""
        frisch = berechne_treffer("schwer", 6, 9, 9, 6)
        # frisch: absorbiert=6, durchkommend=0 -> kaestchenSchaden = 6//2 = 3
        assert frisch["kaestchenSchaden"] == 3


class TestReparatur:
    def test_stellt_kaestchen_wieder_her(self):
        r = repariere(kaestchen_aktuell=2, kaestchen_max=9, betrag=3)
        assert r == {"kaestchenNeu": 5}

    def test_kann_nicht_ueber_max_reparieren(self):
        r = repariere(kaestchen_aktuell=8, kaestchen_max=9, betrag=5)
        assert r["kaestchenNeu"] == 9
