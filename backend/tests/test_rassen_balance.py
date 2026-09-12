"""Tests der Rassen-Bilanz (siehe app/rassen/balance.py).

Der wichtigste Test ist der erste: er hält fest, dass Marks fünf gewachsene
Rassen die Formel **exakt** erfüllen. Er ist damit weniger ein Test des Codes
als der Beleg, dass die Regel aus den Daten stammt und nicht erfunden wurde —
schlägt er fehl, ist entweder eine Rasse aus der Balance geraten oder die
Formel wurde stillschweigend geändert.
"""

from app.rassen.balance import BUDGET, bilanz
from app.traits.erstellung import RASSEN


class TestGewachseneRassen:
    def test_alle_fuenf_eingebauten_rassen_sind_ausgewogen(self):
        unstimmig = {
            name: bilanz(d["modifikatoren"], d["freiePunkte"])
            for name, d in RASSEN.items()
            if not bilanz(d["modifikatoren"], d["freiePunkte"])["stimmt"]
        }
        assert unstimmig == {}

    def test_freie_punkte_plus_vorteile_ergeben_immer_das_budget(self):
        for name, d in RASSEN.items():
            b = bilanz(d["modifikatoren"], d["freiePunkte"])
            assert b["summe"] == BUDGET, f"{name}: {b['punkte']} + {b['vorteile']} = {b['summe']}"


class TestBilanz:
    def test_vorteile_kosten_freie_punkte(self):
        """+2 Vorteile verlangen 13 statt 15 freie Punkte."""
        b = bilanz({"Körperkraft": 1, "Charisma": 1, "Intelligenz": -1}, [5, 5, 3])
        assert b["summe"] == 15 and b["stimmt"]

    def test_zu_viele_punkte_werden_gemeldet(self):
        b = bilanz({"Körperkraft": 2, "Intelligenz": -1}, [7, 5, 3])
        assert not b["stimmt"]
        assert b["summe"] == 17
        assert any("über dem Budget" in h for h in b["hinweise"])

    def test_zu_wenige_nachteile_werden_gemeldet(self):
        """Drei Vorteile verlangen zwei Nachteile."""
        b = bilanz({"Körperkraft": 3, "Intelligenz": -1}, [4, 5, 3])
        assert b["nachteileSoll"] == 2
        assert not b["stimmt"]
        assert any("Zu wenig Nachteile" in h for h in b["hinweise"])

    def test_nachteile_bringen_keine_punkte(self):
        """Marks Entscheidung: Nachteile sind Pflichtbeigabe, keine Währung.
        Ein Volk mit −3 Charisma darf deshalb nicht mehr freie Punkte haben."""
        mit_vielen_nachteilen = bilanz({"Charisma": -3}, [15, 0, 0])
        ohne = bilanz({}, [15, 0, 0])
        assert mit_vielen_nachteilen["summe"] == ohne["summe"]

    def test_rasse_ohne_modifikatoren_braucht_keine_nachteile(self):
        b = bilanz({}, [7, 5, 3])
        assert b["nachteileSoll"] == 0 and b["stimmt"]
