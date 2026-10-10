"""Plan-Autosteigerung: sparen, nicht Resteverwertung.

Mark, 10.10.2026: die KI soll nicht EP ausgeben weil sie es kann.
Nächster Schritt zu teuer → liegen lassen, nichts Billigeres hinterher kaufen.
Sonst wird aus der Ninja-Ratte ein Finanzamt.
"""

from app.traits.autosteigerung import fuehre_plan_aus, mentor_ep


def test_kauft_den_geplanten_attributschritt_wenn_das_budget_reicht():
    # Intelligenz 3→4 kostet 12 (Attribut ×4).
    ergebnis = fuehre_plan_aus(
        werte={"Intelligenz": 3, "Nahkampf": 4},
        kategorien={
            "Intelligenz": "AttributGeistig",
            "Nahkampf": "Fertigkeit",
        },
        plan=["Intelligenz"],
        budget=12,
        maxima={"Intelligenz": 6, "Nahkampf": 6},
    )

    assert ergebnis.werte["Intelligenz"] == 4
    assert ergebnis.werte["Nahkampf"] == 4
    assert ergebnis.restbudget == 0
    assert ergebnis.restplan == []
    assert [(s.name, s.von, s.nach, s.kosten) for s in ergebnis.schritte] == [
        ("Intelligenz", 3, 4, 12)
    ]


def test_spart_statt_billigere_spaetere_fertigkeit_zu_kaufen():
    # Intelligenz 3→4 kostet 12. Finanzen 1→2 kostet 2.
    # 10 EP würden Finanzen kaufen — aber Finanzen ist nicht als Nächstes dran.
    ergebnis = fuehre_plan_aus(
        werte={"Nahkampf": 4, "Finanzen": 1, "Intelligenz": 3},
        kategorien={
            "Nahkampf": "Fertigkeit",
            "Finanzen": "Fertigkeit",
            "Intelligenz": "AttributGeistig",
        },
        plan=["Intelligenz", "Finanzen"],
        budget=10,
        maxima={"Nahkampf": 6, "Finanzen": 6, "Intelligenz": 6},
    )

    assert ergebnis.werte["Intelligenz"] == 3
    assert ergebnis.werte["Finanzen"] == 1
    assert ergebnis.restbudget == 10
    assert ergebnis.restplan == ["Intelligenz", "Finanzen"]
    assert ergebnis.schritte == []


def test_arbeitet_den_plan_der_reihe_nach_ab_solange_es_reicht():
    # Nahkampf 4→5 kostet 8, dann 5→6 kostet 10. Mit 18 EP beide, Rest 0.
    ergebnis = fuehre_plan_aus(
        werte={"Nahkampf": 4},
        kategorien={"Nahkampf": "Fertigkeit"},
        plan=["Nahkampf", "Nahkampf"],
        budget=18,
        maxima={"Nahkampf": 6},
    )

    assert ergebnis.werte["Nahkampf"] == 6
    assert ergebnis.restbudget == 0
    assert ergebnis.restplan == []
    assert [s.nach for s in ergebnis.schritte] == [5, 6]


def test_lernt_keine_neue_fertigkeit_von_null():
    # Finanzen steht auf 0 — Neu-Erlernen ist verboten, auch wenn 3 EP reichen.
    # Nächster legaler Schritt (Nahkampf 4→5 = 8) ist zu teuer → sparen.
    ergebnis = fuehre_plan_aus(
        werte={"Finanzen": 0, "Nahkampf": 4},
        kategorien={"Finanzen": "Fertigkeit", "Nahkampf": "Fertigkeit"},
        plan=["Finanzen", "Nahkampf"],
        budget=5,
        maxima={"Finanzen": 6, "Nahkampf": 6},
    )

    assert ergebnis.werte["Finanzen"] == 0
    assert ergebnis.werte["Nahkampf"] == 4
    assert ergebnis.restbudget == 5
    assert ergebnis.schritte == []


def test_mentor_ep_ist_zwanzig_mal_die_punkte():
    assert mentor_ep(1) == 20
    assert mentor_ep(5) == 100
    assert mentor_ep(0) == 0
