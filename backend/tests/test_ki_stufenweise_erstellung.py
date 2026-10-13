"""Die stufenweise KI-Charaktererstellung (13.10.2026, Marks Wunsch): die KI

liefert nur noch Namen/Prioritäten, nie Zahlen — der Server baut daraus
deterministisch eine `auswahl`, die `erstellung.pruefe()` IMMER besteht,
egal wie unvollständig oder "falsch sortiert" die KI-Eingabe ist. Das ist
der eigentliche Punkt dieser Tests: nicht nur einzelne Funktionen prüfen,
sondern zeigen, dass die KI strukturell keine Regel mehr verletzen kann.
"""

from app.traits import erstellung

from tests.test_erstellung import KATALOG

RASSEN = erstellung.RASSEN


# --- schwerpunkte_aus_rangfolge ------------------------------------------


def test_schwerpunkte_folgen_der_prioritaet():
    sp = erstellung.schwerpunkte_aus_rangfolge(
        "Mensch", ["AttributGeistig", "AttributKörperlich", "AttributGesellschaftlich"]
    )
    assert sp == {"AttributGeistig": 7, "AttributKörperlich": 5, "AttributGesellschaftlich": 3}


def test_schwerpunkte_bei_leerer_oder_kaputter_rangfolge_bleiben_gueltig():
    """Eine leere, unvollständige oder mit Unsinn gefüllte Reihenfolge darf

    nie einen Fehler werfen oder ein unvollständiges Ergebnis liefern — sie
    wird aufgefüllt."""
    sp_leer = erstellung.schwerpunkte_aus_rangfolge("Mensch", [])
    assert sorted(sp_leer.values(), reverse=True) == [7, 5, 3]
    assert set(sp_leer) == set(erstellung.ATTRIBUT_KATEGORIEN)

    sp_unsinn = erstellung.schwerpunkte_aus_rangfolge(
        "Mensch", ["Quatsch", "AttributGeistig", "AttributGeistig"]
    )
    assert sorted(sp_unsinn.values(), reverse=True) == [7, 5, 3]
    assert sp_unsinn["AttributGeistig"] == 7


# --- attributpunkte_aus_rangfolge ----------------------------------------


def test_attributpunkte_treffen_das_kontingent_exakt():
    ap = erstellung.attributpunkte_aus_rangfolge(
        "AttributKörperlich", ["Geschicklichkeit", "Körperkraft", "Widerstandsfähigkeit"], 7
    )
    assert sum(ap.values()) == 7
    assert all(0 <= v <= erstellung.ATTRIBUT_PUNKTE_MAX_JE_WERT for v in ap.values())
    assert ap["Geschicklichkeit"] == 3 and ap["Körperkraft"] == 3 and ap["Widerstandsfähigkeit"] == 1


def test_attributpunkte_ohne_reihenfolge_verteilen_trotzdem_vollstaendig():
    ap = erstellung.attributpunkte_aus_rangfolge("AttributGeistig", [], 5)
    assert sum(ap.values()) == 5
    assert set(ap) == set(erstellung.ATTRIBUTE_JE_KATEGORIE["AttributGeistig"])


# --- fertigkeitpunkte_aus_rangfolge ---------------------------------------

_ERLAUBTE_FERTIGKEITEN = [
    "Schusswaffen", "Heimlichkeit", "Nahkampf", "Wahrnehmung",
    "Matrix", "Fahren", "Sportlichkeit", "Etiketten", "Ermitteln",
]


def test_fertigkeitpunkte_treffen_die_paketverteilung_exakt():
    fp = erstellung.fertigkeitpunkte_aus_rangfolge(
        "PROFI", ["Schusswaffen", "Heimlichkeit", "Nahkampf"], _ERLAUBTE_FERTIGKEITEN
    )
    verteilung_ist: dict[int, int] = {}
    for wert in fp.values():
        verteilung_ist[wert] = verteilung_ist.get(wert, 0) + 1
    assert verteilung_ist == erstellung.FERTIGKEITS_PAKETE["PROFI"]["verteilung"]
    # Die priorisierten Namen bekommen tatsächlich die höchsten Werte.
    assert fp["Schusswaffen"] == 4


def test_fertigkeitpunkte_fuellt_bei_zu_kurzer_liste_aus_dem_katalog_auf():
    fp = erstellung.fertigkeitpunkte_aus_rangfolge("PROFI", ["Schusswaffen"], _ERLAUBTE_FERTIGKEITEN)
    assert len(fp) == sum(erstellung.FERTIGKEITS_PAKETE["PROFI"]["verteilung"].values())
    assert fp["Schusswaffen"] == 4


def test_fertigkeitpunkte_ignoriert_unbekannte_namen():
    fp = erstellung.fertigkeitpunkte_aus_rangfolge(
        "PROFI", ["Pilz-Manipulation", "Schusswaffen"], _ERLAUBTE_FERTIGKEITEN
    )
    assert "Pilz-Manipulation" not in fp
    assert fp["Schusswaffen"] == 4


def test_fertigkeitpunkte_mit_magiebonus_verbraucht_einen_einser_platz():
    erlaubte = ["Kräfte", "Leben"] + _ERLAUBTE_FERTIGKEITEN[:6]
    fp = erstellung.fertigkeitpunkte_aus_rangfolge(
        "PROFI", ["Kräfte", "Leben"], erlaubte, magie_bonus=True, magie_trait="Hexkraft"
    )
    assert fp["Hexkraft"] == erstellung.MAGIE_FIXWERT_PROFI_BONUS
    rest = {k: v for k, v in fp.items() if k != "Hexkraft"}
    soll = dict(erstellung.FERTIGKEITS_PAKETE["PROFI"]["verteilung"])
    soll[1] -= 1
    ist: dict[int, int] = {}
    for wert in rest.values():
        ist[wert] = ist.get(wert, 0) + 1
    assert ist == {w: a for w, a in soll.items() if a > 0}


# --- hintergrundpunkte_aus_rangfolge --------------------------------------

_HINTERGRUND_POOL = {h["name"] for h in erstellung.HINTERGRUENDE}


def test_hintergrundpunkte_verteilen_das_volle_budget():
    hp = erstellung.hintergrundpunkte_aus_rangfolge(
        ["Mentor", "Kontakte", "Ressourcen"], _HINTERGRUND_POOL
    )
    assert sum(hp.values()) == erstellung.HINTERGRUND_PUNKTE_GESAMT
    assert all(v <= erstellung.HINTERGRUND_MAX for v in hp.values())
    assert hp["Mentor"] >= hp["Kontakte"] >= hp["Ressourcen"]


def test_hintergrundpunkte_bei_einem_namen_bekommt_alles():
    hp = erstellung.hintergrundpunkte_aus_rangfolge(["Mentor"], _HINTERGRUND_POOL)
    assert hp == {"Mentor": erstellung.HINTERGRUND_PUNKTE_GESAMT}


def test_hintergrundpunkte_ohne_wahl_bleibt_leer():
    assert erstellung.hintergrundpunkte_aus_rangfolge([], _HINTERGRUND_POOL) == {}


def test_hintergrundpunkte_unbekannter_name_wird_uebersprungen():
    hp = erstellung.hintergrundpunkte_aus_rangfolge(["Ausstattung", "Mentor"], _HINTERGRUND_POOL)
    assert "Ausstattung" not in hp
    assert hp == {"Mentor": erstellung.HINTERGRUND_PUNKTE_GESAMT}


# --- freebees_aus_wunsch --------------------------------------------------

_KATEGORIE_VON = {t["name"]: t["category"] for t in KATALOG}


def test_freebees_bleiben_immer_innerhalb_des_budgets():
    aktuelle_werte = {"Schusswaffen": 4, "Körperkraft": 4}
    maximum_von = {"Schusswaffen": 6, "Körperkraft": 6}
    ergebnis = erstellung.freebees_aus_wunsch(
        budget=5,
        kredit_wunsch=10,
        eigenkapital_wunsch=10,
        ziel_rangfolge=["Schusswaffen", "Körperkraft", "Willenskraft"],
        kategorie_von=_KATEGORIE_VON,
        hintergrund_namen=set(),
        aktuelle_werte=aktuelle_werte,
        maximum_von=maximum_von,
    )
    gesamt = (
        ergebnis["freebeeKredit"] * erstellung.FREEBEE_KOSTEN_KREDIT
        + ergebnis["freebeeEigenkapital"] * erstellung.FREEBEE_KOSTEN_EIGENKAPITAL
        + ergebnis["freebeeWillenskraft"] * erstellung.FREEBEE_KOSTEN_WILLENSKRAFT
        + sum(
            erstellung.FREEBEE_KOSTEN_JE_KATEGORIE.get(_KATEGORIE_VON.get(n) or "Hintergrund", 0) * p
            for n, p in ergebnis["freebeePunkte"].items()
        )
    )
    assert gesamt <= 5


def test_freebees_deckeln_fertigkeiten_auf_plus_eins():
    ergebnis = erstellung.freebees_aus_wunsch(
        budget=20,
        kredit_wunsch=0,
        eigenkapital_wunsch=0,
        ziel_rangfolge=["Nahkampf"],
        kategorie_von=_KATEGORIE_VON,
        hintergrund_namen=set(),
        aktuelle_werte={"Nahkampf": 1},
        maximum_von={"Nahkampf": 6},
    )
    assert ergebnis["freebeePunkte"]["Nahkampf"] == erstellung.FREEBEE_MAX_JE_FERTIGKEIT


def test_freebees_ueberschreiten_nie_das_lebensmaximum():
    """Schon am Limit stehende Werte bekommen keine weiteren Freebees drauf,

    selbst wenn das Budget dafür reichen würde."""
    ergebnis = erstellung.freebees_aus_wunsch(
        budget=20,
        kredit_wunsch=0,
        eigenkapital_wunsch=0,
        ziel_rangfolge=["Körperkraft"],
        kategorie_von=_KATEGORIE_VON,
        hintergrund_namen=set(),
        aktuelle_werte={"Körperkraft": 6},
        maximum_von={"Körperkraft": 6},
    )
    assert "Körperkraft" not in ergebnis["freebeePunkte"]


def test_freebees_unbekannter_name_wird_uebersprungen_statt_abgelehnt():
    ergebnis = erstellung.freebees_aus_wunsch(
        budget=15,
        kredit_wunsch=0,
        eigenkapital_wunsch=0,
        ziel_rangfolge=["Pilz-Manipulation", "Willenskraft"],
        kategorie_von=_KATEGORIE_VON,
        hintergrund_namen=set(),
        aktuelle_werte={},
        maximum_von={},
    )
    assert "Pilz-Manipulation" not in ergebnis["freebeePunkte"]
    assert ergebnis["freebeeWillenskraft"] == 1


def test_freebees_mindestgeld_greift_wenn_kein_geld_gewuenscht():
    ergebnis = erstellung.freebees_aus_wunsch(
        budget=15,
        kredit_wunsch=0,
        eigenkapital_wunsch=0,
        ziel_rangfolge=[],
        kategorie_von=_KATEGORIE_VON,
        hintergrund_namen=set(),
        aktuelle_werte={},
        maximum_von={},
    )
    assert ergebnis["freebeeKredit"] == 1
    assert ergebnis["freebeeEigenkapital"] == 0


# --- Ende-zu-Ende: das Gesamtergebnis besteht IMMER pruefe() -------------


def _stufenweise_auswahl(
    rasse="Mensch",
    weg="KEINER",
    kategorien_reihenfolge=None,
    paket_id="PROFI",
    fertigkeiten_reihenfolge=None,
    hintergruende_reihenfolge=None,
    freebee_ziele=None,
    kredit_wunsch=0,
    eigenkapital_wunsch=0,
):
    """Baut eine komplette `auswahl` exakt so zusammen wie ki/routes.py es

    für den stufenweisen KI-Pfad tut — nur mit Python-Werten statt echten
    KI-Antworten, damit sich der ganze Ablauf ohne Netzwerk/DB testen lässt.
    """
    schwerpunkte = erstellung.schwerpunkte_aus_rangfolge(rasse, kategorien_reihenfolge or [])
    attribut_punkte: dict[str, int] = {}
    for kategorie in erstellung.ATTRIBUT_KATEGORIEN:
        attribut_punkte.update(
            erstellung.attributpunkte_aus_rangfolge(kategorie, [], schwerpunkte.get(kategorie, 0))
        )
    erlaubte_kategorien = ({"Fertigkeit"} | erstellung.KATEGORIEN_JE_WEG.get(weg, set())) - {
        "Hexkraft", "NeuroWeavingWert",
    }
    erlaubte_fertigkeiten = [t["name"] for t in KATALOG if t["category"] in erlaubte_kategorien]
    fertigkeit_punkte = erstellung.fertigkeitpunkte_aus_rangfolge(
        paket_id, fertigkeiten_reihenfolge or [], erlaubte_fertigkeiten
    )
    hintergrund_punkte = erstellung.hintergrundpunkte_aus_rangfolge(
        hintergruende_reihenfolge or [], _HINTERGRUND_POOL
    )
    auswahl_ohne_freebees = {
        "weg": weg, "rasse": rasse, "schwerpunkte": schwerpunkte,
        "attributPunkte": attribut_punkte, "fertigkeitsPaket": paket_id,
        "fertigkeitPunkte": fertigkeit_punkte, "hintergrundPunkte": hintergrund_punkte,
    }
    aktuelle_werte = erstellung.endwerte(auswahl_ohne_freebees)
    maximum_von = {t["name"]: t["defaultMax"] for t in KATALOG}
    maximum_von.update(erstellung.lebensmaxima(rasse, KATALOG))
    budget = erstellung.FREEBEES_GESAMT + int(RASSEN.get(rasse, {}).get("bonusFreebees") or 0)
    freebee_ergebnis = erstellung.freebees_aus_wunsch(
        budget, kredit_wunsch, eigenkapital_wunsch, freebee_ziele or [],
        _KATEGORIE_VON, _HINTERGRUND_POOL, aktuelle_werte, maximum_von,
    )
    return {**auswahl_ohne_freebees, **freebee_ergebnis}


def test_stufenweise_erstellung_besteht_immer_pruefe_mensch():
    auswahl = _stufenweise_auswahl(
        rasse="Mensch",
        kategorien_reihenfolge=["AttributKörperlich", "AttributGeistig", "AttributGesellschaftlich"],
        fertigkeiten_reihenfolge=["Schusswaffen", "Heimlichkeit", "Nahkampf"],
        hintergruende_reihenfolge=["Mentor", "Kontakte"],
        freebee_ziele=["Schusswaffen", "Willenskraft"],
    )
    assert erstellung.pruefe(auswahl, KATALOG) == []


def test_stufenweise_erstellung_besteht_immer_pruefe_magier_mit_leerer_ki_eingabe():
    """Selbst eine komplett leere/fehlende KI-Antwort (worst case) darf nie

    gegen die Regeln verstoßen — genau das ist der Kern von Marks Wunsch."""
    auswahl = _stufenweise_auswahl(rasse="Troll", weg="MAGIER")
    assert erstellung.pruefe(auswahl, KATALOG) == []


def test_stufenweise_erstellung_besteht_immer_pruefe_mit_halluzinierten_namen():
    """Die KI nennt erfundene Fertigkeiten/Hintergründe (wie im echten

    Mark-Fehlerbericht vom 13.10.2026: 'Pilz-Manipulation', 'Ausstattung')
    — die Erstellung bleibt trotzdem regelkonform, die Namen werden nur
    stillschweigend übersprungen statt die ganze Erstellung zu kippen."""
    auswahl = _stufenweise_auswahl(
        rasse="Ork",
        kategorien_reihenfolge=["AttributGeistig", "AttributKörperlich", "AttributGesellschaftlich"],
        fertigkeiten_reihenfolge=["Pilz-Manipulation", "Schusswaffen"],
        hintergruende_reihenfolge=["Ausstattung", "Mentor"],
        freebee_ziele=["Pilz-Manipulation", "Willenskraft"],
    )
    assert erstellung.pruefe(auswahl, KATALOG) == []


def test_stufenweise_erstellung_besteht_immer_pruefe_fuer_alle_rassen():
    """PROFI (8 Fertigkeiten) passt in den 9-Fertigkeiten-Testkatalog — für

    AUSGEGLICHEN/VIELSEITIG (15/19 Fertigkeiten) siehe den eigenen Test unten
    mit einem größeren Katalog, wie ihn die echte Kampagne hat (30 Einträge,
    siehe traits/seed.py)."""
    for rasse in RASSEN:
        auswahl = _stufenweise_auswahl(rasse=rasse, paket_id="PROFI")
        fehler = erstellung.pruefe(auswahl, KATALOG)
        assert fehler == [], f"{rasse}/PROFI: {fehler}"


def test_stufenweise_erstellung_besteht_pruefe_fuer_grosse_pakete_mit_ausreichend_katalog():
    """AUSGEGLICHEN (15) und VIELSEITIG (19) Fertigkeiten brauchen entsprechend

    viele Katalog-Einträge — die echte Kampagne hat 30 (traits/seed.py),
    der kleine Testkatalog (9) reicht dafür nicht. Mit genug Namen bestehen
    beide Pakete trotzdem leer/mit kaputter KI-Eingabe die Prüfung."""
    grosser_katalog = KATALOG + [
        {"id": f"neotopia:Fertigkeit:Extra{i}", "name": f"Extra{i}", "category": "Fertigkeit", "defaultMax": 6}
        for i in range(25)
    ]
    for paket_id in ("AUSGEGLICHEN", "VIELSEITIG"):
        schwerpunkte = erstellung.schwerpunkte_aus_rangfolge("Mensch", [])
        attribut_punkte: dict[str, int] = {}
        for kategorie in erstellung.ATTRIBUT_KATEGORIEN:
            attribut_punkte.update(
                erstellung.attributpunkte_aus_rangfolge(kategorie, [], schwerpunkte.get(kategorie, 0))
            )
        erlaubte = [t["name"] for t in grosser_katalog if t["category"] == "Fertigkeit"]
        fertigkeit_punkte = erstellung.fertigkeitpunkte_aus_rangfolge(paket_id, [], erlaubte)
        auswahl = {
            "weg": "KEINER", "rasse": "Mensch", "schwerpunkte": schwerpunkte,
            "attributPunkte": attribut_punkte, "fertigkeitsPaket": paket_id,
            "fertigkeitPunkte": fertigkeit_punkte, "hintergrundPunkte": {},
            "freebeeKredit": 1, "freebeeEigenkapital": 0, "freebeePunkte": {}, "freebeeWillenskraft": 0,
        }
        fehler = erstellung.pruefe(auswahl, grosser_katalog)
        assert fehler == [], f"{paket_id}: {fehler}"
