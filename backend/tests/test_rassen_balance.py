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
        """+2 Vorteile, 1 Nachteil verlangen 14 statt 15 freie Punkte
        (der eine Nachteil gibt seit 05.10.2026 einen Punkt zurück)."""
        b = bilanz({"Körperkraft": 1, "Charisma": 1, "Intelligenz": -1}, [5, 6, 3])
        assert b["summe"] == 15 and b["stimmt"]

    def test_zu_viele_punkte_werden_gemeldet(self):
        b = bilanz({"Körperkraft": 2, "Intelligenz": -1}, [7, 5, 3])
        assert not b["stimmt"]
        assert b["summe"] == 16
        assert any("über dem Budget" in h for h in b["hinweise"])

    def test_zu_wenige_nachteile_werden_gemeldet(self):
        """Drei Vorteile verlangen zwei Nachteile."""
        b = bilanz({"Körperkraft": 3, "Intelligenz": -1}, [4, 5, 3])
        assert b["nachteileSoll"] == 2
        assert not b["stimmt"]
        assert any("Zu wenig Nachteile" in h for h in b["hinweise"])

    def test_nachteile_geben_jetzt_punkte_zurueck(self):
        """Mark, 05.10.2026 (Fairness-Wunsch): "ein Minus Punkt gibt einen
        Punkt zurück, es soll also immer 24 rauskommen" — das Gegenteil der
        alten Regel (vorher brachten Nachteile gar nichts, siehe Git-
        Historie dieser Datei). Bei gleichbleibenden freien Punkten senkt
        ein zusätzlicher Nachteil die Bilanz jetzt um genau 1 — der
        Rassenbauer muss dann einen freien Punkt draufpacken, um wieder auf
        das Budget zu kommen, bekommt also den Punkt am Ende tatsächlich."""
        mit_nachteil = bilanz({"Charisma": -1}, [15, 0, 0])
        ohne = bilanz({}, [15, 0, 0])
        assert mit_nachteil["summe"] == ohne["summe"] - 1

    def test_rasse_ohne_modifikatoren_braucht_keine_nachteile(self):
        b = bilanz({}, [7, 5, 3])
        assert b["nachteileSoll"] == 0 and b["stimmt"]
