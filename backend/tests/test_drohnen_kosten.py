"""Kostenformel für Drohnen-/Fahrzeug-Attribute (25.10.2026).

Bezahlt wird später in Nuyen statt EP (nuyenProXp-Umrechnung, noch nicht
gebaut) — die Formel selbst ist aber dieselbe Faktor-Formel wie bei
menschlichen Attributen, siehe docs/wiki/concepts/drohnen-fahrzeuge.md.
"""

from app.traits.erfahrung import kosten, nuyen_kosten


class TestAttributDrohne:
    """Stärke/Geschick/Geschwindigkeit/Widerstandsfähigkeit/CPU/
    Arbeitsspeicher/I.C.E. kosten wie ein normales menschliches Attribut."""

    def test_einstieg_kostet_wie_ein_normales_attribut(self):
        assert kosten("AttributDrohne", 0) == kosten("AttributKörperlich", 0) == 5

    def test_steigern_kostet_wie_ein_normales_attribut(self):
        assert kosten("AttributDrohne", 3) == kosten("AttributKörperlich", 3) == 12


class TestAttributDrohneAussenhuelle:
    """Mark: 'der erste ist noch günstig, aber ab dem zweiten wird's rapide
    teurer' — gleicher Einstieg, doppelter Faktor."""

    def test_einstieg_ist_gleich_teuer_wie_jedes_andere_drohnen_attribut(self):
        assert kosten("AttributDrohneAussenhuelle", 0) == kosten("AttributDrohne", 0) == 5

    def test_ab_dem_zweiten_punkt_doppelt_so_teuer(self):
        normal = kosten("AttributDrohne", 1)
        aussenhuelle = kosten("AttributDrohneAussenhuelle", 1)
        assert aussenhuelle == normal * 2

    def test_eskaliert_schneller_je_hoeher_der_wert(self):
        assert kosten("AttributDrohneAussenhuelle", 5) == kosten("AttributDrohne", 5) * 2


class TestNuyenKosten:
    """XP-Preis × Kampagnen-Umrechnung — Mark: 'in Wahrheit einfach XP × Nuyen
    rechnen', Start 200¥/XP-Punkt."""

    def test_rechnet_xp_mal_umrechnungsfaktor(self):
        xp = kosten("AttributDrohne", 2)
        assert nuyen_kosten("AttributDrohne", 2, nuyen_pro_xp=200) == xp * 200

    def test_unbekannte_kategorie_bleibt_nicht_kaeuflich(self):
        assert nuyen_kosten("DasGibtEsNicht", 0, nuyen_pro_xp=200) is None

    def test_negativer_umrechnungsfaktor_wird_wie_null_behandelt(self):
        assert nuyen_kosten("AttributDrohne", 0, nuyen_pro_xp=-50) == 0


class TestMaschinenteilReicht:
    """Material statt Nuyen (26.10.2026): Qualitätsstufen gestuft wie bei
    Reparaturmaterial — höhere Stufe deckt alles, was eine niedrigere auch
    deckt, siehe docs/wiki/concepts/drohnen-fahrzeuge.md Abschnitt
    "Reparatur"."""

    def test_hochwertig_deckt_attribute(self):
        from app.traits.drohnen import maschinenteil_reicht

        assert maschinenteil_reicht("hochwertig", "AttributDrohne") is True
        assert maschinenteil_reicht("hochwertig", "AttributDrohneAussenhuelle") is True

    def test_hochwertig_deckt_auch_fertigkeiten(self):
        from app.traits.drohnen import maschinenteil_reicht

        assert maschinenteil_reicht("hochwertig", "Fertigkeit") is True
        assert maschinenteil_reicht("hochwertig", "Zusatzfertigkeit") is True

    def test_normal_deckt_fertigkeiten_aber_keine_attribute(self):
        from app.traits.drohnen import maschinenteil_reicht

        assert maschinenteil_reicht("normal", "Fertigkeit") is True
        assert maschinenteil_reicht("normal", "Zusatzfertigkeit") is True
        assert maschinenteil_reicht("normal", "AttributDrohne") is False

    def test_minderwertig_deckt_keinen_umbau(self):
        from app.traits.drohnen import maschinenteil_reicht

        assert maschinenteil_reicht("minderwertig", "Fertigkeit") is False
        assert maschinenteil_reicht("minderwertig", "AttributDrohne") is False

    def test_leere_oder_unbekannte_qualitaet_deckt_nichts(self):
        from app.traits.drohnen import maschinenteil_reicht

        assert maschinenteil_reicht("", "Fertigkeit") is False
        assert maschinenteil_reicht("was-auch-immer", "Fertigkeit") is False
