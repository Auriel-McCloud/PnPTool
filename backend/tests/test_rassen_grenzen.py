"""Was Rassenmodifikatoren an den Grenzen anrichten.

Beide Fehler hier hat Mark am 11.09.2026 beim Bauen von "Fred" (Zwerg)
gefunden, und beide haben dieselbe Wurzel: Code, der entstand, als es noch
keine Attribute ausserhalb von 1..6 gab.

* **Charisma verschwand aus dem EP-Blatt.** Zwerg hat Charisma −1, der
  Grundwert ist 1 — wer dort nichts hineinsteckt, landet auf 0. Für 0 gab es
  bei Attributen keinen Preis ("die stehen nach der Erstellung nie auf 0"),
  also warf `preisliste` den Wert still weg: unsichtbar und unsteigerbar.
* **Die Freebee-Grenze kannte die Rasse nicht.** Geprüft wurde gegen den
  Katalogwert 6 — ein Zwerg konnte Charisma auf 6 kaufen (sein Deckel ist 5)
  und kam nie auf die 7 bei Widerstandsfähigkeit, die ihm zusteht.
"""

from app.traits.erfahrung import kosten, preisliste
from app.traits.erstellung import lebensmaxima, pruefe

KATALOG = [
    {"id": "k", "name": "Körperkraft", "category": "AttributKörperlich", "defaultMax": 6},
    {"id": "g", "name": "Geschicklichkeit", "category": "AttributKörperlich", "defaultMax": 6},
    {"id": "w", "name": "Widerstandsfähigkeit", "category": "AttributKörperlich", "defaultMax": 6},
    {"id": "c", "name": "Charisma", "category": "AttributGesellschaftlich", "defaultMax": 6},
    {"id": "m", "name": "Manipulation", "category": "AttributGesellschaftlich", "defaultMax": 6},
    {"id": "f", "name": "Fassung", "category": "AttributGesellschaftlich", "defaultMax": 6},
    {"id": "i", "name": "Intelligenz", "category": "AttributGeistig", "defaultMax": 6},
    {"id": "s", "name": "Geistesschärfe", "category": "AttributGeistig", "defaultMax": 6},
    {"id": "e", "name": "Entschlossenheit", "category": "AttributGeistig", "defaultMax": 6},
]


class TestAttributAufNull:
    """Ein Attribut auf 0 gibt es, sobald eine Rasse es senkt."""

    def test_attribut_auf_null_hat_einen_preis(self):
        assert kosten("AttributGesellschaftlich", 0) == 5

    def test_attribut_auf_null_steht_im_ep_blatt(self):
        namen = [e["name"] for e in preisliste(KATALOG, {"Charisma": 0, "Körperkraft": 3})]
        assert "Charisma" in namen

    def test_kein_wert_faellt_still_aus_der_liste(self):
        """Jeder Katalogeintrag muss auftauchen — ein stilles Verschwinden ist
        schlimmer als ein hoher Preis, weil niemand danach sucht."""
        alle = preisliste(KATALOG, {})
        assert len(alle) == len(KATALOG)


class TestRassendeckelBeimErstellen:
    """Freebees dürfen über das Startmaximum, nicht über das Lebensmaximum."""

    def test_lebensmaximum_folgt_dem_modifikator(self):
        maxima = lebensmaxima("Zwerg", KATALOG)
        assert maxima["Widerstandsfähigkeit"] == 7
        assert maxima["Fassung"] == 7
        assert maxima["Charisma"] == 5

    def test_auch_unberuehrte_attribute_bekommen_ihren_deckel(self):
        """Sonst behielte ein von Zwerg auf Mensch geänderter Charakter beim
        erneuten Einreichen der Erstellung den alten Zwergen-Deckel auf
        Charisma."""
        maxima = lebensmaxima("Zwerg", KATALOG)
        assert maxima["Körperkraft"] == 6
        assert len(maxima) == len(KATALOG)

    def test_mensch_bekommt_ueberall_den_katalogwert(self):
        assert set(lebensmaxima("Mensch", KATALOG).values()) == {6}

    def _zwerg(self, freebees: dict[str, int]) -> list[str]:
        return pruefe(
            {
                "weg": "KEINER",
                "rasse": "Zwerg",
                # Zwerg verteilt 5/5/3; hier alles in eine Spalte, damit die
                # Kontingentprüfung erfüllt ist.
                "schwerpunkte": {
                    "AttributKörperlich": 5,
                    "AttributGesellschaftlich": 5,
                    "AttributGeistig": 3,
                },
                "attributPunkte": {
                    "Körperkraft": 3, "Geschicklichkeit": 2,
                    "Charisma": 3, "Manipulation": 2,
                    "Intelligenz": 3,
                },
                "fertigkeitsPaket": "",
                "freebeePunkte": freebees,
            },
            KATALOG,
        )

    def test_charisma_darf_nicht_ueber_den_gesenkten_deckel(self):
        # Charisma: Start 0, +3 verteilt = 3, +3 Freebees = 6 > Deckel 5
        fehler = self._zwerg({"Charisma": 3})
        assert any("Charisma" in f and "5" in f for f in fehler), fehler

    def test_widerstandsfaehigkeit_darf_bis_sieben(self):
        # Start 2 (1 + 1 Rassenbonus), keine verteilten Punkte, +5 Freebees = 7
        fehler = self._zwerg({"Widerstandsfähigkeit": 5})
        assert not any("Widerstandsfähigkeit" in f for f in fehler), fehler
