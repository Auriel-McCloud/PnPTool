"""Suche, Sortierung und Beziehungsfilter für Personen, Orte und Events.

Reine Funktionen, keine Datenbank — wie tests/test_visibility.py.

Die Beziehungsfälle bilden Marks Beispiele nach: "welche NPCs sind in der
3Heavens Bar", "welche Gegner gibt es beim Überfall auf die Bank", "welche
NPCs gehören zu einer Gruppe".
"""

import json

from app.entities.filterung import (
    filteroptionen,
    klartext,
    nach_beziehung,
    nach_suche,
    normalisiere,
    sortiere,
    verbindungszahl,
)

BAR = "ort-3heavens"
UEBERFALL = "event-ueberfall"
GRUPPE = "person-gruppe-nachtwache"


def person(kennung: str, name: str, **rest) -> dict:
    basis = {
        "id": kennung,
        "name": name,
        "personType": "NPC",
        "description": "",
        "notes": "",
        "timestamp": "",
        "sichtbarkeit": "ALLE",
        "sichtbarFuer": [],
    }
    return {**basis, **rest}


def kante(von: str, zu: str, typ: str) -> dict:
    return {"id": f"{von}->{zu}", "vonId": von, "zuId": zu, "typ": typ}


def dokument(*absaetze: str) -> str:
    """TipTap-Dokument, wie es in description/notes gespeichert wird."""
    return json.dumps(
        {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": text}]} for text in absaetze
            ],
        }
    )


# --- Normalisierung ------------------------------------------------------


def test_umlaute_sind_egal():
    assert normalisiere("Überfall") == normalisiere("uberfall")
    assert normalisiere("STRASSE") == normalisiere("Straße")


def test_klartext_holt_nur_den_lesbaren_teil():
    """Ohne das schlüge eine Suche nach "text" in jedem Dokument an — das Wort
    steht als Typname in jedem TipTap-JSON."""
    roh = dokument("Der Wirt heisst Jonas.")
    assert klartext(roh) == "Der Wirt heisst Jonas."
    assert "type" not in klartext(roh)


def test_klartext_laesst_altbestand_in_klartext_durch():
    assert klartext("Einfach nur Text") == "Einfach nur Text"


def test_klartext_vertraegt_leer():
    assert klartext("") == ""
    assert klartext(None) == ""


# --- Suche ---------------------------------------------------------------


def test_suche_findet_im_namen():
    leute = [person("a", "Mr. Chrome"), person("b", "Kira Voss")]
    assert [p["id"] for p in nach_suche(leute, "chrome")] == ["a"]


def test_suche_findet_in_der_beschreibung():
    leute = [
        person("a", "Mr. Chrome", description=dokument("Ein Fixer aus dem Hafenviertel.")),
        person("b", "Kira Voss", description=dokument("Deckerin.")),
    ]
    assert [p["id"] for p in nach_suche(leute, "hafenviertel")] == ["a"]


def test_suche_findet_in_notizen():
    leute = [person("a", "Wache", notes=dokument("Arbeitet heimlich für Renraku."))]
    assert len(nach_suche(leute, "renraku")) == 1


def test_suche_verlangt_alle_woerter():
    """Stichwörter, keine Phrase: Reihenfolge egal, aber alle müssen passen."""
    leute = [
        person("a", "Mr. Chrome", description=dokument("Trifft sich in der Bar.")),
        person("b", "Kira Voss", description=dokument("Sitzt in der Bar.")),
    ]
    assert [p["id"] for p in nach_suche(leute, "bar chrome")] == ["a"]
    assert [p["id"] for p in nach_suche(leute, "chrome bar")] == ["a"]


def test_suche_ohne_begriff_gibt_alles():
    leute = [person("a", "A"), person("b", "B")]
    assert len(nach_suche(leute, None)) == 2
    assert len(nach_suche(leute, "   ")) == 2


def test_suche_in_events_nutzt_den_titel():
    events = [
        {"id": "e1", "title": "Überfall auf die Bank", "timestamp": "Session 3", "description": "", "notes": ""},
        {"id": "e2", "title": "Der Deal", "timestamp": "", "description": "", "notes": ""},
    ]
    assert [e["id"] for e in nach_suche(events, "bank", "title")] == ["e1"]


def test_suche_findet_den_zeitpunkt():
    events = [
        {"id": "e1", "title": "Überfall", "timestamp": "Session 3", "description": "", "notes": ""},
        {"id": "e2", "title": "Deal", "timestamp": "Session 1", "description": "", "notes": ""},
    ]
    assert [e["id"] for e in nach_suche(events, "session 3", "title")] == ["e1"]


# --- Beziehungsfilter ----------------------------------------------------


def test_wer_ist_in_der_bar():
    """Marks Beispiel: welche NPCs befinden sich in der 3Heavens Bar."""
    leute = [person("a", "Wirt"), person("b", "Kira"), person("c", "Fremder")]
    kanten = [
        kante("a", BAR, "arbeitet in"),
        kante(BAR, "b", "Stammgast"),  # andere Richtung, zählt trotzdem
    ]
    assert [p["id"] for p in nach_beziehung(leute, kanten, ziel_id=BAR)] == ["a", "b"]


def test_richtung_ist_egal():
    """Ob die Spielleitung 'Kira → trifft sich in → Bar' oder 'Bar →
    Stammgast → Kira' angelegt hat, ist Erzählung, nicht Zugehörigkeit."""
    leute = [person("a", "Kira")]
    assert len(nach_beziehung(leute, [kante("a", BAR, "x")], ziel_id=BAR)) == 1
    assert len(nach_beziehung(leute, [kante(BAR, "a", "x")], ziel_id=BAR)) == 1


def test_gegner_beim_ueberfall():
    """Marks zweites Beispiel: Ziel UND Typ zusammen."""
    leute = [person("a", "Söldner"), person("b", "Geisel"), person("c", "Söldner anderswo")]
    kanten = [
        kante("a", UEBERFALL, "Gegner"),
        kante("b", UEBERFALL, "Geisel"),
        kante("c", "event-anderes", "Gegner"),
    ]
    treffer = nach_beziehung(leute, kanten, ziel_id=UEBERFALL, typ="Gegner")
    assert [p["id"] for p in treffer] == ["a"]


def test_nur_typ_ohne_ziel():
    """"Alle Gegner, egal wo" — ohne Zielangabe."""
    leute = [person("a", "Söldner"), person("b", "Geisel")]
    kanten = [kante("a", UEBERFALL, "Gegner"), kante("b", UEBERFALL, "Geisel")]
    assert [p["id"] for p in nach_beziehung(leute, kanten, typ="Gegner")] == ["a"]


def test_typ_ist_gross_klein_und_umlaut_tolerant():
    leute = [person("a", "Söldner")]
    kanten = [kante("a", UEBERFALL, "Gegner")]
    assert len(nach_beziehung(leute, kanten, typ="gegner")) == 1
    assert len(nach_beziehung(leute, kanten, typ="GEGNER")) == 1


def test_gruppenzugehoerigkeit():
    """Marks drittes Beispiel: welche NPCs gehören zu einer Party.

    Kein Sonderfeld — eine Party ist eine Entität wie jede andere, und die
    Zugehörigkeit ist eine gewöhnliche Verbindung.
    """
    leute = [person("a", "Wache 1"), person("b", "Wache 2"), person("c", "Zivilist")]
    kanten = [kante("a", GRUPPE, "gehört zu"), kante("b", GRUPPE, "gehört zu")]
    assert [p["id"] for p in nach_beziehung(leute, kanten, ziel_id=GRUPPE)] == ["a", "b"]


def test_ohne_filter_bleibt_alles():
    leute = [person("a", "A"), person("b", "B")]
    assert len(nach_beziehung(leute, [], None, None)) == 2


def test_unbekanntes_ziel_gibt_leer():
    """Fehlerhafter Zustand: die Oberfläche muss "keine Treffer" zeigen
    können, nicht stumm alles."""
    leute = [person("a", "A")]
    assert nach_beziehung(leute, [kante("a", BAR, "x")], ziel_id="gibt-es-nicht") == []


def test_geheime_kante_faellt_vorher_weg():
    """Der Filter arbeitet auf einer bereits sichtbarkeitsgefilterten
    Kantenliste — sonst stiesse ein Spieler über den Treffer auf einen NPC,
    den er nicht kennen darf."""
    leute = [person("a", "Verdeckter Ermittler")]
    # So sähe die Kantenliste aus, nachdem filter_verbindungen_for_viewer die
    # geheime Kante entfernt hat:
    assert nach_beziehung(leute, [], ziel_id=BAR) == []


# --- Sortierung ----------------------------------------------------------


def test_sortiert_alphabetisch_ohne_ruecksicht_auf_umlaute():
    leute = [person("a", "Zora"), person("b", "Änna"), person("c", "Mika")]
    assert [p["name"] for p in sortiere(leute, "name")] == ["Änna", "Mika", "Zora"]


def test_absteigend():
    leute = [person("a", "Anna"), person("b", "Zora")]
    assert [p["name"] for p in sortiere(leute, "name-ab")] == ["Zora", "Anna"]


def test_sortiert_nach_sichtbarkeit_geheim_zuerst():
    """Die Spielleitung will sehen, was noch nicht freigegeben ist."""
    leute = [
        person("a", "Offen", sichtbarkeit="ALLE"),
        person("b", "Geheim", sichtbarkeit="GM"),
        person("c", "Teilweise", sichtbarkeit="SPEZIFISCH"),
    ]
    assert [p["name"] for p in sortiere(leute, "sichtbarkeit")] == ["Geheim", "Teilweise", "Offen"]


def test_sortiert_nach_verbindungszahl():
    leute = [person("a", "Einsam"), person("b", "Vernetzt")]
    kanten = [kante("b", BAR, "x"), kante("b", UEBERFALL, "y")]
    assert [p["name"] for p in sortiere(leute, "verbindungen", "name", kanten)] == ["Vernetzt", "Einsam"]


def test_gleichstand_faellt_auf_den_namen_zurueck():
    """Sonst springt die Liste bei jedem Aufruf, und mitten im Spiel sucht man
    den Eintrag, der eben noch woanders stand."""
    leute = [person("a", "Zora", sichtbarkeit="GM"), person("b", "Anna", sichtbarkeit="GM")]
    assert [p["name"] for p in sortiere(leute, "sichtbarkeit")] == ["Anna", "Zora"]


def test_events_nach_zeitpunkt_ohne_angabe_ans_ende():
    events = [
        {"id": "a", "title": "Ohne", "timestamp": ""},
        {"id": "b", "title": "Spaet", "timestamp": "Session 5"},
        {"id": "c", "title": "Frueh", "timestamp": "Session 1"},
    ]
    assert [e["title"] for e in sortiere(events, "zeitpunkt", "title")] == ["Frueh", "Spaet", "Ohne"]


def test_unbekannte_sortierung_faellt_auf_den_namen_zurueck():
    leute = [person("a", "Zora"), person("b", "Anna")]
    assert [p["name"] for p in sortiere(leute, "quatsch")] == ["Anna", "Zora"]


def test_leere_liste_bleibt_leer():
    assert sortiere([], "verbindungen", "name", []) == []
    assert nach_suche([], "irgendwas") == []


def test_verbindungszahl_zaehlt_beide_richtungen():
    leute = [person("a", "A"), person("b", "B")]
    kanten = [kante("a", "b", "kennt"), kante(BAR, "a", "Stammgast")]
    assert verbindungszahl(leute, kanten) == {"a": 2, "b": 1}


# --- Filteroptionen ------------------------------------------------------


def test_filteroptionen_bieten_nur_echte_beziehungen_an():
    """Ein Dropdown, das ins Leere führt, ist schlimmer als keins."""
    leute = [person("a", "Wirt"), person("b", "Söldner")]
    kanten = [kante("a", BAR, "arbeitet in"), kante("b", UEBERFALL, "Gegner")]
    beschriftung = {BAR: ("Ort", "3Heavens Bar"), UEBERFALL: ("Event", "Überfall auf die Bank")}

    optionen = filteroptionen(leute, kanten, beschriftung)

    assert optionen["typen"] == ["arbeitet in", "Gegner"]
    assert [(z["kind"], z["label"]) for z in optionen["ziele"]] == [
        ("Event", "Überfall auf die Bank"),
        ("Ort", "3Heavens Bar"),
    ]


def test_filteroptionen_zaehlen_die_treffer():
    leute = [person("a", "Wirt"), person("b", "Kellner")]
    kanten = [kante("a", BAR, "x"), kante("b", BAR, "y")]
    optionen = filteroptionen(leute, kanten, {BAR: ("Ort", "3Heavens Bar")})
    assert optionen["ziele"][0]["anzahl"] == 2


def test_filteroptionen_lassen_fremde_kanten_weg():
    """Eine Kante zwischen zwei Orten geht die NPC-Liste nichts an."""
    leute = [person("a", "Wirt")]
    kanten = [kante("ort-x", "ort-y", "liegt neben")]
    optionen = filteroptionen(leute, kanten, {"ort-y": ("Ort", "Nebenan")})
    assert optionen == {"typen": [], "ziele": []}


def test_filteroptionen_verschweigen_unsichtbare_ziele():
    """Steht ein Ziel nicht in der (gefilterten) Beschriftung, taucht es nicht
    auf — sonst verriete der Filter den Namen eines geheimen NPCs."""
    leute = [person("a", "Wirt")]
    kanten = [kante("a", "person-geheim", "arbeitet für")]
    optionen = filteroptionen(leute, kanten, {})
    assert optionen["ziele"] == []
    # Die Beziehungsart selbst bleibt: sie verrät keinen Namen.
    assert optionen["typen"] == ["arbeitet für"]


def test_filteroptionen_bei_leerer_kampagne():
    assert filteroptionen([], [], {}) == {"typen": [], "ziele": []}
