"""Prüfung der Charaktererstellung — ohne Datenbank.

Die Regeln stammen aus `docs/reference/Neotopia.xlsx`, Blatt *Regeln*. Getestet
wird vor allem, dass **regelwidrige** Einreichungen auffliegen: die Oberfläche
führt zwar durch den Ablauf, aber sie ist nicht die Instanz, die entscheidet.
"""

import pytest

from app.traits import erfahrung, erstellung

# Ein Katalog, wie ihn `repository.list_catalog` liefert — nur die Felder, die
# die Prüfung tatsächlich anfasst.
KATALOG = [
    {"id": f"neotopia:{kat}:{name}", "name": name, "category": kat, "defaultMax": maximum}
    for kat, namen, maximum in [
        ("AttributKörperlich", ["Körperkraft", "Geschicklichkeit", "Widerstandsfähigkeit"], 6),
        ("AttributGesellschaftlich", ["Charisma", "Manipulation", "Fassung"], 6),
        ("AttributGeistig", ["Intelligenz", "Geistesschärfe", "Entschlossenheit"], 6),
        (
            "Fertigkeit",
            [
                "Schusswaffen",
                "Heimlichkeit",
                "Nahkampf",
                "Wahrnehmung",
                "Matrix",
                "Fahren",
                "Sportlichkeit",
                "Etiketten",
                "Ermitteln",
            ],
            5,
        ),
        ("Sphäre", ["Kräfte", "Leben"], 5),
        ("Arete", ["Arete"], 10),
        ("NeuroWeaving", ["Brute Force"], 5),
        ("Hintergrund", [h["name"] for h in erstellung.HINTERGRUENDE], 5),
    ]
    for name in namen
]


def grundgeruest(**abweichung):
    """Eine regelkonforme Erstellung: Mensch, Profi-Paket, keine Freebees."""
    auswahl = {
        "weg": "KEINER",
        "rasse": "Mensch",
        "schwerpunkte": {
            "AttributKörperlich": 7,
            "AttributGesellschaftlich": 3,
            "AttributGeistig": 5,
        },
        # Mensch: StartMax 4, Startwert 1 — also höchstens 3 Punkte je Attribut.
        "attributPunkte": {
            "Körperkraft": 3,
            "Geschicklichkeit": 3,
            "Widerstandsfähigkeit": 1,
            "Charisma": 1,
            "Manipulation": 1,
            "Fassung": 1,
            "Intelligenz": 2,
            "Geistesschärfe": 2,
            "Entschlossenheit": 1,
        },
        # Profi verlangt genau acht Fertigkeiten: 1×4, 3×3, 3×2, 1×1.
        "fertigkeitsPaket": "PROFI",
        "fertigkeitPunkte": {
            "Schusswaffen": 4,
            "Heimlichkeit": 3,
            "Nahkampf": 3,
            "Wahrnehmung": 3,
            "Matrix": 2,
            "Fahren": 2,
            "Sportlichkeit": 2,
            "Etiketten": 1,
        },
        "hintergrundPunkte": {},
        "freebeePunkte": {},
        "freebeeWillenskraft": 0,
        "freebeeKredit": 0,
        "freebeeEigenkapital": 0,
    }
    auswahl.update(abweichung)
    return auswahl


# --- Rassen -------------------------------------------------------------


@pytest.mark.parametrize(
    "rasse,attribut,erwartet",
    [
        ("Mensch", "Körperkraft", 1),
        ("Troll", "Körperkraft", 3),  # 1 + 2
        ("Troll", "Geschicklichkeit", 0),  # 1 - 1
        ("Elf", "Charisma", 2),
        ("Elf", "Widerstandsfähigkeit", 0),
        ("Ork", "Intelligenz", 0),
        ("Zwerg", "Fassung", 2),
    ],
)
def test_startwerte_folgen_den_rassenmodifikatoren(rasse, attribut, erwartet):
    assert erstellung.startwerte(rasse)[attribut] == erwartet


@pytest.mark.parametrize(
    "rasse,attribut,erwartet",
    [
        ("Mensch", "Körperkraft", 4),
        ("Troll", "Körperkraft", 6),
        ("Troll", "Geistesschärfe", 3),
        ("Elf", "Geschicklichkeit", 5),
        ("Ork", "Intelligenz", 3),
    ],
)
def test_startmaxima_entsprechen_der_rassentabelle(rasse, attribut, erwartet):
    """Die Spalte StartMax aus Zeilen 4-18 ist durchgehend 4 + Modifikator."""
    assert erstellung.startmaxima(rasse)[attribut] == erwartet


# --- Attributverteilung -------------------------------------------------


def test_regelkonforme_erstellung_geht_durch():
    assert erstellung.pruefe(grundgeruest(), KATALOG) == []


def test_falsche_kontingente_fallen_auf():
    """Der Mensch verteilt 7/5/3 — nicht 7/7/3."""
    fehler = erstellung.pruefe(
        grundgeruest(
            schwerpunkte={
                "AttributKörperlich": 7,
                "AttributGesellschaftlich": 7,
                "AttributGeistig": 3,
            }
        ),
        KATALOG,
    )
    assert any("Attributpunkte" in f for f in fehler)


def test_kontingente_duerfen_beliebig_auf_die_spalten_fallen():
    """Zeile 21: welches Kontingent wohin geht, ist frei wählbar."""
    auswahl = grundgeruest(
        schwerpunkte={
            "AttributKörperlich": 3,
            "AttributGesellschaftlich": 5,
            "AttributGeistig": 7,
        },
        attributPunkte={
            "Körperkraft": 1,
            "Geschicklichkeit": 1,
            "Widerstandsfähigkeit": 1,
            "Charisma": 2,
            "Manipulation": 2,
            "Fassung": 1,
            "Intelligenz": 3,
            "Geistesschärfe": 3,
            "Entschlossenheit": 1,
        },
    )
    assert erstellung.pruefe(auswahl, KATALOG) == []


def test_nicht_verteilte_punkte_fallen_auf():
    auswahl = grundgeruest()
    auswahl["attributPunkte"]["Körperkraft"] = 2  # einer zu wenig
    fehler = erstellung.pruefe(auswahl, KATALOG)
    assert any("Körperlich" in f for f in fehler)


def test_startmax_wird_durchgesetzt():
    """Ohne Freebees ist beim Menschen bei 4 Schluss (Zeile 24)."""
    auswahl = grundgeruest(
        schwerpunkte={
            "AttributKörperlich": 7,
            "AttributGesellschaftlich": 3,
            "AttributGeistig": 5,
        },
    )
    auswahl["attributPunkte"] = {
        "Körperkraft": 4,  # 1 + 4 = 5, erlaubt sind 4
        "Geschicklichkeit": 2,
        "Widerstandsfähigkeit": 1,
        "Charisma": 1,
        "Manipulation": 1,
        "Fassung": 1,
        "Intelligenz": 2,
        "Geistesschärfe": 2,
        "Entschlossenheit": 1,
    }
    fehler = erstellung.pruefe(auswahl, KATALOG)
    assert any("Körperkraft" in f and "5" in f for f in fehler)


# --- Fertigkeitspakete --------------------------------------------------


def test_paketverteilung_muss_genau_stimmen():
    auswahl = grundgeruest()
    auswahl["fertigkeitPunkte"]["Schusswaffen"] = 5  # Profi hat kein 5er
    fehler = erstellung.pruefe(auswahl, KATALOG)
    assert any("Profi" in f for f in fehler)


def test_ausgeglichenes_paket():
    """15 Fertigkeiten: 3×3, 5×2, 7×1 — hier nur die Verteilung geprüft."""
    verteilung = erstellung.FERTIGKEITS_PAKETE["AUSGEGLICHEN"]["verteilung"]
    assert sum(verteilung.values()) == 15
    assert sum(w * a for w, a in verteilung.items()) == 3 * 3 + 5 * 2 + 7 * 1


def test_sphaeren_nur_fuer_magier():
    """Zeile 27: Sphären zählen als Fertigkeit — aber nur, wer sie hat."""
    auswahl = grundgeruest(weg="KEINER")
    auswahl["fertigkeitPunkte"] = {
        "Schusswaffen": 4,
        "Heimlichkeit": 3,
        "Nahkampf": 3,
        "Wahrnehmung": 3,
        "Matrix": 2,
        "Fahren": 2,
        "Kräfte": 2,
        "Leben": 1,
    }
    fehler = erstellung.pruefe(auswahl, KATALOG)
    assert any("Kräfte" in f and "Weg" in f for f in fehler)

    # Als Magier ist dieselbe Verteilung in Ordnung.
    assert erstellung.pruefe({**auswahl, "weg": "MAGIER"}, KATALOG) == []


def test_arete_zaehlt_als_fertigkeit():
    auswahl = grundgeruest(weg="MAGIER")
    auswahl["fertigkeitPunkte"] = {
        "Arete": 4,
        "Kräfte": 3,
        "Leben": 3,
        "Wahrnehmung": 3,
        "Matrix": 2,
        "Fahren": 2,
        "Heimlichkeit": 2,
        "Nahkampf": 1,
    }
    assert erstellung.pruefe(auswahl, KATALOG) == []


# --- Freebees -----------------------------------------------------------


def test_freebees_sind_bei_fuenfzehn_zu_ende():
    """Vier Attributpunkte à 5 sind 20 — zwei mehr als erlaubt."""
    auswahl = grundgeruest(
        freebeePunkte={"Körperkraft": 2, "Charisma": 2},
    )
    fehler = erstellung.pruefe(auswahl, KATALOG)
    assert any("Freebees" in f for f in fehler)


def test_freebees_duerfen_ueber_das_startmax():
    """Zeile 24: 'Der StartMax Wert gilt nicht für FreeBees'."""
    auswahl = grundgeruest(freebeePunkte={"Körperkraft": 1})
    assert erstellung.pruefe(auswahl, KATALOG) == []
    # Körperkraft: 1 Start + 3 verteilt + 1 Freebee = 5, über dem StartMax 4.
    assert erstellung.endwerte(auswahl)["Körperkraft"] == 5


def test_freebees_kommen_nicht_ueber_das_maximum_des_wertes():
    """Der StartMax gilt nicht für Freebees — das Maximum des Wertes schon.

    Von Mark beim Durchklicken gefunden: Körperkraft liess sich auf 9 kaufen.
    """
    # Mensch: Start 1 + 3 verteilt = 4. Zwei Freebees brächten 6 (erlaubt),
    # drei brächten 7 — mehr als das Attributmaximum.
    assert erstellung.pruefe(grundgeruest(freebeePunkte={"Körperkraft": 2}), KATALOG) == []
    fehler = erstellung.pruefe(grundgeruest(freebeePunkte={"Körperkraft": 3}), KATALOG)
    assert any("Körperkraft" in f and "7" in f for f in fehler)


def test_fertigkeit_steigt_per_freebee_nur_um_einen_punkt():
    """Zeile 40: 'Fertigkeit 2 (max +1)'."""
    fehler = erstellung.pruefe(grundgeruest(freebeePunkte={"Nahkampf": 2}), KATALOG)
    assert any("Nahkampf" in f for f in fehler)
    assert erstellung.pruefe(grundgeruest(freebeePunkte={"Nahkampf": 1}), KATALOG) == []


def test_preise_richten_sich_nach_der_kategorie():
    kategorie_von = {t["name"]: t["category"] for t in KATALOG}
    auswahl = grundgeruest(
        freebeePunkte={"Körperkraft": 1, "Nahkampf": 1, "Kontakte": 2},
        freebeeWillenskraft=1,
    )
    # 5 (Attribut) + 2 (Fertigkeit) + 2×1 (Hintergrund) + 1 (Willenskraft)
    assert erstellung.freebee_kosten(auswahl, kategorie_von) == 10


def test_kapital_kredit_ist_billiger_als_eigenkapital():
    """Zeile 42: Kredit 10.000¥ = 1 Freebee, Eigenkapital = 2."""
    kategorie_von = {t["name"]: t["category"] for t in KATALOG}
    kredit = grundgeruest(freebeeKredit=2)
    eigen = grundgeruest(freebeeEigenkapital=2)
    assert erstellung.freebee_kosten(kredit, kategorie_von) == 2
    assert erstellung.freebee_kosten(eigen, kategorie_von) == 4

    vermoegen, schulden = erstellung.kapital(kredit)
    assert vermoegen == erstellung.STARTKAPITAL + 20_000
    assert schulden == 20_000, "Kredit muss als Schuld stehenbleiben"

    vermoegen, schulden = erstellung.kapital(eigen)
    assert vermoegen == erstellung.STARTKAPITAL + 20_000
    assert schulden == 0


# --- Hintergründe -------------------------------------------------------


def test_hintergrundpunkte_sind_bei_fuenf_zu_ende():
    fehler = erstellung.pruefe(
        grundgeruest(hintergrundPunkte={"Kontakte": 3, "Ressourcen": 3}), KATALOG
    )
    assert any("Hintergrundpunkte" in f for f in fehler)


def test_hintergruende_landen_in_den_endwerten():
    werte = erstellung.endwerte(grundgeruest(hintergrundPunkte={"Kontakte": 2}))
    assert werte["Kontakte"] == 2


def test_unbekannter_hintergrund_faellt_auf():
    fehler = erstellung.pruefe(grundgeruest(hintergrundPunkte={"Adelstitel": 1}), KATALOG)
    assert any("Adelstitel" in f for f in fehler)


# --- Endwerte -----------------------------------------------------------


def test_endwerte_summieren_start_verteilung_und_freebees():
    werte = erstellung.endwerte(
        grundgeruest(rasse="Troll", freebeePunkte={"Körperkraft": 1})
    )
    # Troll startet mit 3 auf Körperkraft, 3 verteilt, 1 Freebee.
    assert werte["Körperkraft"] == 3 + 3 + 1


def test_regelwerk_ist_vollstaendig_fuer_die_oberflaeche():
    regeln = erstellung.regelwerk()
    assert {w["id"] for w in regeln["wege"]} == {"KEINER", "MAGIER", "TECHNOMANCER"}
    assert {r["name"] for r in regeln["rassen"]} == {"Mensch", "Elf", "Ork", "Zwerg", "Troll"}
    assert len(regeln["fertigkeitsPakete"]) == 3
    assert regeln["freebees"]["gesamt"] == 15
    for rasse in regeln["rassen"]:
        assert len(rasse["freiePunkte"]) == 3
        assert len(rasse["startwerte"]) == 9


# --- Erfahrung ----------------------------------------------------------


def test_steigern_wird_mit_jedem_punkt_teurer():
    assert erfahrung.kosten("Fertigkeit", 1) == 2
    assert erfahrung.kosten("Fertigkeit", 4) == 8
    assert erfahrung.kosten("AttributKörperlich", 3) == 12


def test_erster_punkt_hat_einen_eigenen_preis():
    """Die Formel gäbe bei 0 nichts her — geschenkt soll nichts sein."""
    assert erfahrung.kosten("Fertigkeit", 0) == 3
    assert erfahrung.kosten("Arete", 0) == 5


def test_arete_kostet_wie_ein_attribut_sphaeren_wie_fertigkeiten():
    """Marks Zuordnung vom 30.08.2026 — dieselbe wie bei den Freebees."""
    assert erfahrung.kosten("Arete", 3) == erfahrung.kosten("AttributGeistig", 3)
    assert erfahrung.kosten("Sphäre", 3) == erfahrung.kosten("Fertigkeit", 3)


def test_freebee_zuordnung_deckt_sich_damit():
    """Arete wie ein Attribut (5), Sphäre wie eine Fertigkeit (2)."""
    preise = erstellung.FREEBEE_KOSTEN_JE_KATEGORIE
    assert preise["Arete"] == preise["AttributGeistig"] == 5
    assert preise["Sphäre"] == preise["Fertigkeit"] == 2


def test_unbekannte_kategorie_ist_nicht_steigerbar():
    assert erfahrung.kosten("Ausrüstungsslot", 2) is None
    assert erfahrung.kosten("Ausrüstungsslot", 0) is None


def test_preisliste_laesst_nicht_steigerbares_weg():
    liste = erfahrung.preisliste(
        [*KATALOG, {"id": "x", "name": "Etwas", "category": "Unbekannt", "defaultMax": 3}],
        {"Schusswaffen": 2},
    )
    namen = {e["name"] for e in liste}
    assert "Etwas" not in namen
    schuss = next(e for e in liste if e["name"] == "Schusswaffen")
    assert schuss["aktuell"] == 2 and schuss["kosten"] == 4
