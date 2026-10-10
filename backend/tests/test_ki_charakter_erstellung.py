"""KI-Charaktere müssen durch dieselbe Erstellung wie Spieler.

Roh-Ratings (Attribute auf 6 weil defaultMax 6) sind der Bug, den Mark
gesehen hat. Die KI liefert das Erstellungsformular, `pruefe()` entscheidet.
"""

from app.traits.erstellung import aus_ki_antwort, ki_erstellungsregeln_text

from tests.test_erstellung import KATALOG, grundgeruest


def test_ueberhoehte_attributpunkte_werden_abgelehnt():
    daten = grundgeruest(attributPunkte={
        **grundgeruest()["attributPunkte"],
        "Körperkraft": 10,
    })
    werte, fehler = aus_ki_antwort(daten, KATALOG)

    assert werte == {}
    assert any("Körperkraft" in f or "erlaubt" in f.lower() or "Start" in f or "steht auf" in f for f in fehler)


def test_regelkonforme_ki_antwort_liefert_endwerte_nicht_sechser():
    werte, fehler = aus_ki_antwort(grundgeruest(), KATALOG)

    assert fehler == []
    assert werte["Körperkraft"] == 4  # Start 1 + 3 Punkte, StartMax 4
    assert werte["Schusswaffen"] == 4
    assert werte.get("Etiketten") == 1


def test_ki_liste_statt_dict_wird_verstanden():
    daten = grundgeruest()
    daten["attributPunkte"] = [
        {"name": name, "punkte": n} for name, n in daten["attributPunkte"].items()
    ]
    daten["fertigkeitPunkte"] = [
        {"name": name, "punkte": n} for name, n in daten["fertigkeitPunkte"].items()
    ]
    werte, fehler = aus_ki_antwort(daten, KATALOG)
    assert fehler == []
    assert werte["Körperkraft"] == 4


def test_alte_trait_ratings_werden_nicht_als_endwerte_genommen():
    daten = {**grundgeruest(), "traits": [{"name": "Körperkraft", "rating": 6}]}
    werte, fehler = aus_ki_antwort(daten, KATALOG)
    assert fehler == []
    assert werte["Körperkraft"] == 4


def test_erstellungsregeln_text_nennt_pakete_und_rassen():
    text = ki_erstellungsregeln_text()
    assert "PROFI" in text
    assert "Mensch" in text
    assert "StartMax" in text
    assert "höchstens 3" in text
    assert "Kredit" in text
    assert "Körperkraft +1" in text
    assert "Freebee-Budget 17" in text  # Mensch +2
    assert "hintergrundPunkte leer" not in text


def test_endwerte_in_attributpunkten_werden_umgerechnet():
    from app.traits import erstellung

    daten = grundgeruest()
    start = erstellung.startwerte("Mensch")
    daten["attributPunkte"] = {
        name: start[name] + punkte for name, punkte in daten["attributPunkte"].items()
    }
    werte, fehler = aus_ki_antwort(daten, KATALOG)
    assert fehler == []
    assert werte["Körperkraft"] == 4


def test_endwert_ueber_startmax_bleibt_abgelehnt():
    daten = grundgeruest(attributPunkte={
        **grundgeruest()["attributPunkte"],
        "Körperkraft": 6,
    })
    werte, fehler = aus_ki_antwort(daten, KATALOG)
    assert werte == {}
    assert fehler


def test_freebee_geld_ueber_budget_wird_abgelehnt():
    daten = grundgeruest(freebeeKredit=20)
    werte, fehler = aus_ki_antwort(daten, KATALOG)
    assert werte == {}
    assert any("Freebee" in f for f in fehler)


def test_legale_freebees_auf_geld_und_fertigkeit():
    daten = grundgeruest(
        freebeePunkte={"Schusswaffen": 1},
        freebeeKredit=2,
        freebeeEigenkapital=1,
        freebeeWillenskraft=1,
    )
    werte, fehler = aus_ki_antwort(daten, KATALOG)
    assert fehler == []
    assert werte["Schusswaffen"] == 5
    from app.traits.erstellung import kapital
    vermoegen, schulden = kapital(daten)
    assert schulden == 20_000
    assert vermoegen == 10_000 + 20_000 + 10_000
