"""KI-Idee und Beratung-Entwurf: alle anlegbaren Welttypen."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from app.ki.auto_verknuepfung import BeziehungAnwendenErgebnis
from app.ki.routes import BeratungEntwurfInput, KiIdeeInput, _idee_anlegen
from app.traits.erstellung import HINTERGRUENDE
from tests.test_erstellung import KATALOG

WELTTYPEN = ("story", "charakter", "gegenstand", "ort", "event", "fraktion", "verbindung")


def _run(coro):
    return asyncio.run(coro)


def test_idee_und_beratung_erlauben_dieselben_welttypen():
    for typ in WELTTYPEN:
        KiIdeeInput(typ=typ, prompt="x")
        BeratungEntwurfInput(typ=typ)


def test_unbekannter_idee_typ_wird_abgelehnt():
    with pytest.raises(ValidationError):
        KiIdeeInput(typ="rasse", prompt="x")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        BeratungEntwurfInput(typ="begleiter")  # type: ignore[arg-type]


def test_ort_wird_als_ort_angelegt_nicht_als_charakter():
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(return_value={"name": "Hafen", "beschreibung": "nass"}),
            ),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "o1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await _idee_anlegen("c1", "ort", "ein Hafen")
            assert ergebnis["typ"] == "ort"
            assert create.await_args.args[0] == "Ort"

    _run(run())


def test_notizen_aus_der_ki_antwort_landen_im_notes_feld():
    """Details, die nicht in die knappe beschreibung passen, gehen ins SL-Notizfeld."""
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(
                    return_value={
                        "name": "Hafen",
                        "beschreibung": "nass",
                        "notizen": "Hier stehen alle Details aus dem Gespräch.",
                    }
                ),
            ),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "o1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            await _idee_anlegen("c1", "ort", "ein Hafen")
            daten = create.await_args.args[3]
            assert daten["notes"] == "Hier stehen alle Details aus dem Gespräch."

    _run(run())


def test_fehlende_notizen_in_der_antwort_brechen_nichts():
    """Ältere/gemockte Antworten ohne notizen-Feld bleiben gültig (leerer String)."""
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(return_value={"name": "Hafen", "beschreibung": "nass"}),
            ),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "o1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            await _idee_anlegen("c1", "ort", "ein Hafen")
            daten = create.await_args.args[3]
            assert daten["notes"] == ""

    _run(run())


def test_fraktion_bekommt_ziele_und_ressourcen():
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(
                    return_value={
                        "name": "Chrysalis",
                        "beschreibung": "Konzern",
                        "ziele": [{"titel": "Markt", "beschreibung": "kaufen"}],
                        "ressourcen": [{"titel": "Kapital", "beschreibung": "viel"}],
                    }
                ),
            ),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "f1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await _idee_anlegen("c1", "fraktion", "ein Konzern")
            assert ergebnis["typ"] == "fraktion"
            assert create.await_args.args[0] == "Fraktion"
            daten = create.await_args.args[3]
            assert daten["ziele"][0]["titel"] == "Markt"
            assert daten["ressourcen"][0]["titel"] == "Kapital"

    _run(run())


def test_verbindung_nutzt_beziehung_anwenden():
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="Fred (Person)")),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(
                    return_value={
                        "vonName": "Fred",
                        "vonTyp": "Person",
                        "zuName": "Hafen",
                        "zuTyp": "Ort",
                        "typ": "hält sich auf",
                        "beschreibung": "stammt von dort",
                    }
                ),
            ),
            patch("app.ki.routes.verknuepfung_beziehung_anwenden", AsyncMock()) as anwenden,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            anwenden.return_value = BeziehungAnwendenErgebnis(
                verbindungId="v1",
                zielId1="p1",
                zielId2="o1",
                neuAngelegt1=False,
                neuAngelegt2=True,
            )
            ergebnis = await _idee_anlegen("c1", "verbindung", "Fred und der Hafen")
            assert ergebnis["typ"] == "verbindung"
            assert ergebnis["id"] == "v1"
            assert anwenden.await_count == 1

    _run(run())


def _stufe1_antwort(**overrides) -> dict:
    """Eine gültige Stufe-1-Antwort (Konzept/Rasse/Weg/Paket/Prioritäten) für

    die stufenweise KI-Charaktererstellung (13.10.2026) — siehe
    ki/routes.py::_charakter_konzept_schema."""
    basis = {
        "name": "Kira",
        "beschreibung": "x",
        "notizen": "",
        "konzept": "Fixer",
        "alter": "29",
        "ambition": "",
        "verlangen": "",
        "ziel": "",
        "rasse": "Mensch",
        "weg": "KEINER",
        "fertigkeitsPaket": "PROFI",
        "kategorienReihenfolge": ["AttributKörperlich", "AttributGeistig", "AttributGesellschaftlich"],
        "attributReihenfolgeKoerperlich": ["Körperkraft", "Geschicklichkeit", "Widerstandsfähigkeit"],
        "attributReihenfolgeGesellschaftlich": ["Charisma", "Manipulation", "Fassung"],
        "attributReihenfolgeGeistig": ["Intelligenz", "Geistesschärfe", "Entschlossenheit"],
    }
    basis.update(overrides)
    return basis


def _stufe2_antwort(**overrides) -> dict:
    """Eine gültige Stufe-2-Antwort (Fertigkeiten/Hintergründe/Freebees) —

    siehe ki/routes.py::_charakter_fertigkeiten_schema."""
    basis = {
        "fertigkeitenReihenfolge": ["Schusswaffen", "Heimlichkeit", "Nahkampf"],
        "hintergruendeReihenfolge": [],
        "freebeeKredit": 1,
        "freebeeEigenkapital": 0,
        "freebeeZielReihenfolge": [],
    }
    basis.update(overrides)
    return basis


# patch("app.ki.routes.get_einstellungen", ...) UND
# patch("app.ki.routes.hintergruende_repository.pool_fuer_erstellung", ...)
# sind bei jedem charakter-Test nötig: die stufenweise Erstellung
# (13.10.2026) respektiert die Mentor-/Kontakte-/Schulden-Kampagnentoggles
# und holt seit dem Baukasten-Sync-Fix (13.10.2026, Mark) den echten
# Hintergrund-Katalog der Kampagne — beides ungemockt würde einen echten,
# hier nicht verfügbaren DB-Zugriff auslösen.


def test_idee_charakter_kann_keine_regelwidrige_erstellung_mehr_liefern():
    """Kernversprechen der stufenweisen Erstellung (13.10.2026, Marks

    Bugreport): selbst eine KI-Antwort voller Unsinn — erfundene Fertigkeiten/
    Hintergründe, widersprüchliche Prioritäten, Freebee-Wünsche weit über
    Budget — darf nie mehr zu einem 422 "KI hat sich nicht an die Regeln
    gehalten" führen. Der Server baut die Zahlen selbst, die KI liefert nur
    noch (hier bewusst kaputte) Namen/Prioritäten."""

    async def run():
        stufe1 = _stufe1_antwort(
            rasse="Mensch",
            kategorienReihenfolge=["Quatsch", "AttributGeistig", "AttributGeistig"],
            attributReihenfolgeKoerperlich=["Nicht-Existent"],
        )
        stufe2 = _stufe2_antwort(
            fertigkeitenReihenfolge=["Pilz-Manipulation", "Schusswaffen"],
            hintergruendeReihenfolge=["Ausstattung", "Mentor"],
            freebeeKredit=99,
            freebeeEigenkapital=99,
            freebeeZielReihenfolge=["Pilz-Manipulation", "Willenskraft"],
        )
        ki = AsyncMock(side_effect=[stufe1, stufe2])
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.generiere_json", ki),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch("app.ki.routes.rassen_repository.liste_fuer_kampagne", AsyncMock(return_value=[])),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.get_einstellungen", AsyncMock(return_value={})),
            patch(
                "app.ki.routes.hintergruende_repository.pool_fuer_erstellung",
                AsyncMock(return_value=HINTERGRUENDE),
            ),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "p1"})) as create,
            patch("app.ki.routes.set_ratings_bulk", AsyncMock()) as bulk,
            patch("app.ki.routes.setze_maxima_bulk", AsyncMock()),
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await _idee_anlegen("c1", "charakter", "eine Kira")
            assert ergebnis["typ"] == "charakter"
            assert create.await_count == 1
            werte = bulk.await_args.args[2]
            # Kein Fehler, aber auch keine stillschweigend akzeptierten
            # Phantomwerte: die erfundenen Namen tauchen nirgends auf.
            assert "Pilz-Manipulation" not in werte
            assert "Ausstattung" not in werte
            assert werte["Körperkraft"] <= 6

    _run(run())


def test_idee_charakter_schreibt_endwerte_aus_der_erstellung():
    async def run():
        stufe1 = _stufe1_antwort()
        stufe2 = _stufe2_antwort(freebeeKredit=1, freebeeZielReihenfolge=["Etiketten"])
        ki = AsyncMock(side_effect=[stufe1, stufe2])
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.generiere_json", ki),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch("app.ki.routes.rassen_repository.liste_fuer_kampagne", AsyncMock(return_value=[])),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.get_einstellungen", AsyncMock(return_value={})),
            patch(
                "app.ki.routes.hintergruende_repository.pool_fuer_erstellung",
                AsyncMock(return_value=HINTERGRUENDE),
            ),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "p1"})) as create,
            patch("app.ki.routes.set_ratings_bulk", AsyncMock()) as bulk,
            patch("app.ki.routes.setze_maxima_bulk", AsyncMock()),
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await _idee_anlegen("c1", "charakter", "eine Kira")
            assert ergebnis["typ"] == "charakter"
            assert ki.await_count == 2  # genau Stufe 1 + Stufe 2, keine Nachbesserung
            werte = bulk.await_args.args[2]
            assert werte["Körperkraft"] == 4
            person = create.await_args.args[3]
            assert person["erstellungAbgeschlossen"] is True

    _run(run())


def test_idee_charakter_mit_magier_weg_bekommt_hexkraft_sockel():
    """Der feste Hexkraft-Sockel (MAGIE_FIXWERT) landet unabhängig davon in

    den Endwerten, ob/was die KI in fertigkeitenReihenfolge dafür vorsieht —
    dieselbe Garantie wie in der Kern-Regelprüfung (test_erstellung.py)."""

    async def run():
        stufe1 = _stufe1_antwort(weg="MAGIER")
        stufe2 = _stufe2_antwort(fertigkeitenReihenfolge=["Kräfte", "Leben", "Schusswaffen"])
        ki = AsyncMock(side_effect=[stufe1, stufe2])
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.generiere_json", ki),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch("app.ki.routes.rassen_repository.liste_fuer_kampagne", AsyncMock(return_value=[])),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.get_einstellungen", AsyncMock(return_value={})),
            patch(
                "app.ki.routes.hintergruende_repository.pool_fuer_erstellung",
                AsyncMock(return_value=HINTERGRUENDE),
            ),
            patch("app.ki.routes.create_node", AsyncMock(return_value={"id": "p1"})) as create,
            patch("app.ki.routes.set_ratings_bulk", AsyncMock()) as bulk,
            patch("app.ki.routes.setze_maxima_bulk", AsyncMock()),
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await _idee_anlegen("c1", "charakter", "eine Magierin")
            assert ergebnis["typ"] == "charakter"
            werte = bulk.await_args.args[2]
            from app.traits.erstellung import MAGIE_FIXWERT

            assert werte["Hexkraft"] == MAGIE_FIXWERT
            person = create.await_args.args[3]
            assert person["weg"] == "MAGIER"

    _run(run())


def test_waffe_aus_der_ki_bekommt_schaden():
    """Kachel und Kampf lesen kraft. Ohne das Feld blieb jede KI-Waffe auf 0."""
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(return_value={
                    "name": "Nadel",
                    "beschreibung": "leise",
                    "notizen": "",
                    "typ": "Waffe",
                    "preis": 800,
                    "seltenheit": 3,
                    "schaden": 2,
                    "schadenArt": "schwer",
                }),
            ),
            patch("app.ki.routes.create_gegenstand", AsyncMock(return_value={"id": "g1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            await _idee_anlegen("c1", "gegenstand", "eine Nadelpistole")
            daten = create.await_args.args[2]
            assert daten["typ"] == "Waffe"
            assert daten["kraft"] == 2
            assert daten["schaden"] == 2
            assert daten["istWaffe"] is True
            assert daten["schadenArt"] == "schwer"

    _run(run())


def test_waffe_ohne_angabe_bekommt_mindestens_stufe_1():
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(return_value={
                    "name": "Knüppel",
                    "beschreibung": "Holz",
                    "typ": "Waffe",
                    "preis": 40,
                    "seltenheit": 1,
                }),
            ),
            patch("app.ki.routes.create_gegenstand", AsyncMock(return_value={"id": "g1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            await _idee_anlegen("c1", "gegenstand", "ein Knüppel")
            daten = create.await_args.args[2]
            assert daten["kraft"] == 1
            assert daten["schaden"] == 1
            assert daten["schadenArt"] == "schwer"

    _run(run())


def test_kein_waffenschaden_bei_einem_nicht_waffe():
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(return_value={
                    "name": "Jacke",
                    "beschreibung": "Leder",
                    "typ": "Sonstiges",
                    "preis": 80,
                    "seltenheit": 1,
                    "schaden": 4,
                }),
            ),
            patch("app.ki.routes.create_gegenstand", AsyncMock(return_value={"id": "g1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            await _idee_anlegen("c1", "gegenstand", "eine Jacke")
            daten = create.await_args.args[2]
            assert daten["kraft"] == 0
            assert daten["istWaffe"] is False

    _run(run())


def test_cyberware_traitbonus_aus_der_ki_landet_in_traitboni():
    """Mark-Bug 11.10.2026: ein Implantat mit "+1 auf Schusswaffen" landete
    nur im Beschreibungstext, weil die KI dafür kein Ausgabefeld hatte."""
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(return_value={
                    "name": "Zielerfassungs-Implantat",
                    "beschreibung": "Ein Neuralchip fürs Auge.",
                    "notizen": "",
                    "typ": "Cyberware",
                    "preis": 5000,
                    "seltenheit": 3,
                    "schaden": 0,
                    "traitBoni": [{"name": "Schusswaffen", "wert": 1}],
                }),
            ),
            patch("app.ki.routes.create_gegenstand", AsyncMock(return_value={"id": "g1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            await _idee_anlegen("c1", "gegenstand", "ein Implantat mit +1 auf Schusswaffen")
            daten = create.await_args.args[2]
            assert daten["traitBoni"] == {"Schusswaffen": 1}

    _run(run())


def test_erfundener_traitbonus_name_wird_verworfen():
    """Namen, die es im Katalog nicht gibt, dürfen keinen wirkungslosen
    traitBoni-Eintrag erzeugen (die KI hält sich nicht immer ans Prompt)."""
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(return_value={
                    "name": "Komisches Implantat",
                    "beschreibung": "x",
                    "notizen": "",
                    "typ": "Cyberware",
                    "preis": 1000,
                    "seltenheit": 1,
                    "schaden": 0,
                    "traitBoni": [{"name": "Feuerwaffen", "wert": 1}],
                }),
            ),
            patch("app.ki.routes.create_gegenstand", AsyncMock(return_value={"id": "g1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            await _idee_anlegen("c1", "gegenstand", "ein Implantat")
            daten = create.await_args.args[2]
            assert daten["traitBoni"] == {}

    _run(run())


def test_neue_fertigkeit_aus_der_ki_landet_in_ausruestungsfertigkeiten():
    async def run():
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch(
                "app.ki.routes.generiere_json",
                AsyncMock(return_value={
                    "name": "NeuroWeaving-Deck",
                    "beschreibung": "x",
                    "notizen": "",
                    "typ": "Cyberdeck",
                    "preis": 12000,
                    "seltenheit": 4,
                    "schaden": 0,
                    "neueFertigkeiten": [{"name": "NeuroWeaving", "wert": 2}],
                }),
            ),
            patch("app.ki.routes.create_gegenstand", AsyncMock(return_value={"id": "g1"})) as create,
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            await _idee_anlegen("c1", "gegenstand", "ein NeuroWeaving-Deck")
            daten = create.await_args.args[2]
            assert daten["ausruestungsfertigkeiten"] == {"NeuroWeaving": 2}

    _run(run())
