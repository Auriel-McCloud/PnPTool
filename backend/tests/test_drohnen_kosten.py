"""Kostenformel für Drohnen-/Fahrzeug-Attribute (25.10.2026).

Bezahlt wird später in Nuyen statt EP (nuyenProXp-Umrechnung, noch nicht
gebaut) — die Formel selbst ist aber dieselbe Faktor-Formel wie bei
menschlichen Attributen, siehe docs/wiki/concepts/drohnen-fahrzeuge.md.
"""

from app.traits.erfahrung import kosten


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
