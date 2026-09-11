"""Tests des Rüstungssystems: Kästchen + Durchlass (siehe app/kampf/ruestung.py
und docs/api/ruestung.md für die ausführliche Herleitung).

Die Zahlen hier sind die im Gespräch mit Mark durchgerechneten Beispiele
(Lederjacke, Bombenschutzweste) — sie dienen zugleich als Beleg, dass der Code
tut, was besprochen wurde, UND als Regressionsschutz gegen künftige Änderungen
an der Formel.
"""

from app.kampf.ruestung import (
    berechne_treffer,
    pool,
    reihenfolge,
    repariere,
    uebersicht,
    verteile_kaestchenschaden,
)


def teil(id: str, name: str, kaestchen: int, kaestchen_max: int, durchlass: int) -> dict:
    """Ein Rüstungsteil, wie es aus items/repository.py::ruestungsteile kommt."""
    return {
        "id": id,
        "name": name,
        "ruestungKaestchenAktuell": kaestchen,
        "ruestungKaestchenMax": kaestchen_max,
        "ruestungDurchlassBasis": durchlass,
        "ruestungDurchlassAktuell": durchlass,
    }


class TestPool:
    """Alle getragenen Teile wirken als eine Rüstung."""

    def test_kaestchen_summieren_sich_durchlass_kommt_vom_dichtesten(self):
        jacke = teil("a", "Lederjacke", 5, 5, 4)
        weste = teil("b", "Kevlarweste", 3, 3, 0)
        p = pool([jacke, weste])
        assert p["kaestchenAktuell"] == 8
        assert p["kaestchenMax"] == 8
        # Nicht 4 und nicht 2 (kein Mittel, keine Summe): der Durchlass des
        # besten Teils gilt.
        assert p["durchlassAktuell"] == 0
        assert p["durchlassBasis"] == 0

    def test_ohne_wirksames_teil_gibt_es_keinen_pool(self):
        assert pool([]) is None
        assert pool([teil("a", "Zerfetzte Weste", 0, 9, 3)]) is None

    def test_zerstoerte_teile_zaehlen_nicht_mit(self):
        kaputt = teil("a", "Zerfetzte Weste", 0, 9, 0)
        heil = teil("b", "Lederjacke", 5, 5, 4)
        p = pool([kaputt, heil])
        assert p["kaestchenAktuell"] == 5
        # Der Durchlass der zerschossenen Weste (0) darf den Pool NICHT
        # dicht machen — sie wirkt nicht mehr.
        assert p["durchlassAktuell"] == 4


class TestBlattUebersicht:
    """Was das Charakterblatt als Rüstungsleiste bekommt (fertig gerechnet
    vom Server, damit die Pool-Regel nicht im Frontend nachgebaut wird)."""

    def test_fasst_den_pool_anzeigefertig_zusammen(self):
        jacke = teil("a", "Lederjacke", 5, 5, 4)
        weste = teil("b", "Kevlarweste", 2, 3, 0)
        u = uebersicht([jacke, weste])
        assert u["kaestchenAktuell"] == 7
        assert u["kaestchenMax"] == 8
        assert u["durchlass"] == 0
        # In Verbrauchsreihenfolge, damit das Blatt zeigen kann, was als
        # naechstes draufgeht.
        assert [t["name"] for t in u["teile"]] == ["Kevlarweste", "Lederjacke"]

    def test_ohne_ruestung_nur_nullen(self):
        """Das Blatt blendet die Leiste dann aus — eine Reihe "0/0" ist keine
        Auskunft."""
        assert uebersicht([]) == {"kaestchenAktuell": 0, "kaestchenMax": 0, "durchlass": 0, "teile": []}


class TestVerbrauchsreihenfolge:
    def test_dichtestes_teil_wird_zuerst_aufgebraucht(self):
        jacke = teil("a", "Lederjacke", 5, 5, 4)
        weste = teil("b", "Kevlarweste", 3, 3, 0)
        assert [t["name"] for t in reihenfolge([jacke, weste])] == ["Kevlarweste", "Lederjacke"]

    def test_bei_gleichem_durchlass_zuerst_das_kleinere_teil(self):
        """Damit es fertig aufgebraucht wird, statt dass mehrere Teile halb
        angeknackst herumliegen."""
        gross = teil("a", "Panzerjacke", 6, 6, 1)
        klein = teil("b", "Helm", 2, 2, 1)
        assert [t["name"] for t in reihenfolge([gross, klein])] == ["Helm", "Panzerjacke"]

    def test_schaden_laeuft_ins_naechste_teil_ueber(self):
        weste = teil("b", "Kevlarweste", 3, 3, 0)
        jacke = teil("a", "Lederjacke", 5, 5, 4)
        folgen = verteile_kaestchenschaden(reihenfolge([weste, jacke]), 5)
        assert [(f["name"], f["verlust"], f["zerstoert"]) for f in folgen] == [
            ("Kevlarweste", 3, True),
            ("Lederjacke", 2, False),
        ]

    def test_jedes_teil_wird_um_seinen_eigenen_verlust_loechriger(self):
        jacke = teil("a", "Lederjacke", 5, 5, 1)
        folge = verteile_kaestchenschaden([jacke], 2)[0]
        assert folge["kaestchenNeu"] == 3
        assert folge["durchlassNeu"] == 3  # 1 + 2 Verlust

    def test_mehr_schaden_als_der_pool_hat_verpufft(self):
        weste = teil("b", "Kevlarweste", 2, 2, 0)
        folgen = verteile_kaestchenschaden(reihenfolge([weste]), 99)
        assert folgen[0]["verlust"] == 2 and folgen[0]["zerstoert"]

    def test_unbeteiligte_teile_stehen_nicht_in_der_liste(self):
        weste = teil("b", "Kevlarweste", 9, 9, 0)
        jacke = teil("a", "Lederjacke", 5, 5, 4)
        folgen = verteile_kaestchenschaden(reihenfolge([weste, jacke]), 2)
        assert [f["name"] for f in folgen] == ["Kevlarweste"]


class TestSuspensoriumMissbrauch:
    """Ein winziges Teil mit Durchlass 0 darf den Pool nicht dauerhaft dicht
    machen, während ein löchriges Teil die Kästchen stellt. Die
    Verbrauchsreihenfolge verhindert das von selbst — genau das ist ihr
    zweiter Zweck."""

    def test_das_dichte_kleinteil_ist_nach_einem_treffer_weg(self):
        suspensorium = teil("a", "Kugelsicheres Suspensorium", 1, 1, 0)
        jacke = teil("b", "Lederjacke", 5, 5, 4)
        p = pool([suspensorium, jacke])
        assert p["durchlassAktuell"] == 0  # noch dicht

        ergebnis = berechne_treffer(
            "schwer", 6, p["kaestchenAktuell"], p["kaestchenMax"], p["durchlassBasis"], p["durchlassAktuell"]
        )
        folgen = verteile_kaestchenschaden(p["geordnet"], ergebnis["kaestchenSchaden"])
        assert folgen[0]["name"] == "Kugelsicheres Suspensorium" and folgen[0]["zerstoert"]

        # Danach zählt nur noch die Jacke — der Pool ist löchrig geworden.
        suspensorium["ruestungKaestchenAktuell"] = 0
        assert pool([suspensorium, jacke])["durchlassAktuell"] == 4


class TestLederjacke:
    """3/3 Kästchen, Durchlass-Basis 3 — schwache, aber am Anfang schon
    löchrige Alltagsrüstung ("schützt vor Schlägen, nicht vor Schüssen")."""

    def test_schlag_ueber_der_schwelle_wird_halbiert_und_kostet_ein_kaestchen(self):
        r = berechne_treffer("schlag", 6, 3, 3, 3, 3)
        assert r == {"hpArt": "schlag", "hpMenge": 1, "kaestchenSchaden": 1, "kaestchenNeu": 2, "durchlassNeu": 3}

    def test_toedlich_wird_nur_im_typ_abgestuft_nicht_in_der_menge(self):
        """Tödlich (schwer) -> Schlag beim Durchkommen, aber ohne Halbierung —
        die Halbierung gibt es nur für Schlag, weil dort keine leichtere Stufe
        mehr existiert."""
        r = berechne_treffer("schwer", 6, 3, 3, 3, 3)
        assert r["hpArt"] == "schlag"
        assert r["hpMenge"] == 3
        # Kaestchenschaden = halber Basis-Anteil (1) + voller Ueberschuss (3) = 4,
        # gedeckelt auf die vorhandenen 3 Kaestchen -> Ruestung komplett hin.
        assert r["kaestchenNeu"] == 0
        assert r["durchlassNeu"] == 3  # gedeckelt auf Kaestchen-Max

    def test_toedlich_genau_an_der_schwelle_kostet_trotzdem_ein_halbes_kaestchen(self):
        """Mark: 'die Rüstung hat schon was geleistet' — auch ein Treffer, der
        gar nicht über die Basis hinausgeht, nagt zur Hälfte an ihr."""
        r = berechne_treffer("schwer", 3, 3, 3, 3, 3)
        assert r["kaestchenSchaden"] == 1
        assert r["hpMenge"] == 3

    def test_zerstoerte_ruestung_wirkt_gar_nicht_mehr(self):
        """0 Kästchen = kein Abstufen, kein Abfangen — der Treffer geht
        unverändert durch (Mark: 'wirkt gar nicht mehr')."""
        r = berechne_treffer("aggraviert", 5, 0, 3, 3, 3)
        assert r == {"hpArt": "aggraviert", "hpMenge": 5, "kaestchenSchaden": 0, "kaestchenNeu": 0, "durchlassNeu": 3}


class TestBombenschutzweste:
    """9/9 Kästchen, Durchlass-Basis 0 — hochwertige Rüstung, die im
    Neuzustand *nichts* garantiert durchlässt."""

    def test_erster_treffer_wird_komplett_geschluckt(self):
        r = berechne_treffer("schlag", 6, 9, 9, 0, 0)
        assert r == {"hpArt": "schlag", "hpMenge": 0, "kaestchenSchaden": 3, "kaestchenNeu": 6, "durchlassNeu": 3}

    def test_zweiter_treffer_laesst_schon_etwas_durch(self):
        """Weil Durchlass-Aktuell durch den ersten Treffer gestiegen ist —
        die Weste wird spürbar schlechter, nicht nur ihre Kästchen weniger."""
        erster = berechne_treffer("schlag", 6, 9, 9, 0, 0)
        zweiter = berechne_treffer(
            "schlag", 6, erster["kaestchenNeu"], 9, 0, erster["durchlassNeu"]
        )
        assert zweiter["hpMenge"] == 1

    def test_schwacher_treffer_richtet_bei_intakter_weste_nichts_aus(self):
        """Trigger `2×Stärke >= Kästchen-Aktuell`: 2*4=8 < 9 -> kein
        Kästchenschaden. Eine bombensichere Weste steckt einen laschen
        Schlag komplett weg, ohne auch nur einen Kratzer zu bekommen."""
        r = berechne_treffer("schlag", 4, 9, 9, 0, 0)
        assert r["kaestchenSchaden"] == 0

    def test_knapp_ueber_dem_trigger_richtet_etwas_aus(self):
        """2*5=10 >= 9 -> Trigger erfüllt."""
        r = berechne_treffer("schlag", 5, 9, 9, 0, 0)
        assert r["kaestchenSchaden"] == 2

    def test_kaestchenschaden_bleibt_konstant_egal_wie_beschaedigt(self):
        """Der Kern des Basis/Aktuell-Splits: derselbe Tödlich-Treffer richtet
        an frischer wie an bereits angeschlagener Rüstung denselben
        Kästchenschaden an — sonst würde beschädigte Rüstung zunehmend
        UNZERSTÖRBARER statt kaputter (das ursprüngliche Paradox, siehe
        Modul-Docstring in app/kampf/ruestung.py)."""
        # kaestchen_aktuell bewusst bei beiden hoch genug, dass der reine
        # Formelvergleich nicht durch "mehr verloren als noch da war"
        # verfälscht wird (das würde die Zahl separat nach unten kappen).
        frisch = berechne_treffer("schwer", 6, 9, 9, 0, 0)
        angeschlagen = berechne_treffer("schwer", 6, 7, 9, 0, 4)
        assert frisch["kaestchenSchaden"] == angeschlagen["kaestchenSchaden"]


class TestReparatur:
    def test_stellt_kaestchen_wieder_her_und_senkt_durchlass_symmetrisch(self):
        r = repariere(kaestchen_aktuell=2, kaestchen_max=9, durchlass_basis=0, durchlass_aktuell=5, betrag=3)
        assert r == {"kaestchenNeu": 5, "durchlassNeu": 2}

    def test_kann_nicht_ueber_max_reparieren(self):
        r = repariere(kaestchen_aktuell=8, kaestchen_max=9, durchlass_basis=0, durchlass_aktuell=3, betrag=5)
        assert r["kaestchenNeu"] == 9

    def test_kann_durchlass_nicht_unter_die_basis_senken(self):
        r = repariere(kaestchen_aktuell=2, kaestchen_max=9, durchlass_basis=1, durchlass_aktuell=2, betrag=10)
        assert r["durchlassNeu"] == 1
