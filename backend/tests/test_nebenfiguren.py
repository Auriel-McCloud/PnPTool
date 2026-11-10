"""Nebenfiguren (10.11.2026): reine Logik und die Zu-NPC-Route (gemockt)."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.entities.repository import _mit_defaults
from app.entities.schemas import PersonCreate, PersonResponse
from app.nebenfiguren import routes
from app.nebenfiguren.logic import (
    nebenfaehigkeiten_saeubern,
    nebenfaehigkeiten_text,
    persoenlichkeit_saeubern,
    zu_npc_prompt,
)

_run = asyncio.run


class TestSaeubern:
    def test_leere_namen_und_doppelte_fliegen_raus(self):
        roh = [{"name": " Straßenwissen ", "wert": "4"}, {"name": "", "wert": 2}, {"name": "straßenwissen", "wert": 1}]
        assert nebenfaehigkeiten_saeubern(roh) == [{"name": "Straßenwissen", "wert": 4}]

    def test_von_hand_kein_deckel_aber_nicht_negativ(self):
        roh = [{"name": "Feilschen", "wert": 9}, {"name": "Lügen", "wert": -3}]
        assert nebenfaehigkeiten_saeubern(roh) == [{"name": "Feilschen", "wert": 9}, {"name": "Lügen", "wert": 0}]

    def test_ki_wird_auf_eins_bis_fuenf_und_drei_eintraege_geklemmt(self):
        roh = [{"name": n, "wert": w} for n, w in [("A", 9), ("B", 0), ("C", 3), ("D", 2)]]
        assert nebenfaehigkeiten_saeubern(roh, ki=True) == [
            {"name": "A", "wert": 5},
            {"name": "B", "wert": 1},
            {"name": "C", "wert": 3},
        ]

    def test_kaputte_eingabe_ist_leer(self):
        assert nebenfaehigkeiten_saeubern("Straßenwissen 4") == []
        assert nebenfaehigkeiten_saeubern(None) == []

    def test_text(self):
        assert nebenfaehigkeiten_text([{"name": "Straßenwissen", "wert": 4}, {"name": "Feilschen", "wert": 3}]) == (
            "Straßenwissen 4, Feilschen 3"
        )

    def test_persoenlichkeit_kurz_und_ohne_zeilenumbruch(self):
        assert persoenlichkeit_saeubern("  Leit\nwolf  ") == "Leit wolf"
        assert len(persoenlichkeit_saeubern("x" * 500)) == 60


def test_prompt_nennt_name_rasse_und_faehigkeiten():
    person = {
        "name": "Mama Okoro",
        "rasse": "Ork",
        "alter": "61",
        "persoenlichkeit": "Glucke",
        "nebenfaehigkeiten": [{"name": "Straßenwissen", "wert": 4}],
    }
    prompt = zu_npc_prompt(person, "Betreibt eine Garküche.", "")
    assert "Mama Okoro" in prompt
    assert "Rasse: Ork" in prompt
    assert "Straßenwissen 4" in prompt
    assert "Glucke" in prompt
    assert "Garküche" in prompt
    assert "SL-Notizen" not in prompt


def test_felder_ueberleben_den_json_umweg():
    # create_node/update_node legen nebenfaehigkeiten als JSON-String ab.
    roh = PersonCreate(name="X", istNebenfigur=True, nebenfaehigkeiten=[{"name": "Feilschen", "wert": 3}]).model_dump()
    gespeichert = {**roh, "id": "p1", "nebenfaehigkeiten": '[{"name": "Feilschen", "wert": 3}]'}
    antwort = PersonResponse(**_mit_defaults(gespeichert))
    assert antwort.istNebenfigur is True
    assert antwort.nebenfaehigkeiten[0].name == "Feilschen"


def test_altbestand_ohne_felder_bricht_die_liste_nicht():
    alt = {
        "id": "p1", "name": "Alt", "personType": "NPC", "description": "", "notes": "",
        "sichtbarkeit": "ALLE", "sichtbarFuer": [], "notizenSichtbarkeit": "GM", "notizenSichtbarFuer": [],
        "istNebenfigur": None, "persoenlichkeit": None, "nebenfaehigkeiten": None,
    }
    antwort = PersonResponse(**_mit_defaults(alt))
    assert antwort.istNebenfigur is False
    assert antwort.nebenfaehigkeiten == []


class TestZuNpcRoute:
    def test_unbekannt_404(self):
        with patch.object(routes, "get_node", AsyncMock(return_value=None)):
            with pytest.raises(HTTPException) as e:
                _run(routes.zu_npc_machen("c1", "p1"))
        assert e.value.status_code == 404

    def test_schon_npc_409_und_keine_ki(self):
        ki = AsyncMock()
        with patch.object(routes, "get_node", AsyncMock(return_value={"id": "p1", "istNebenfigur": False})), \
             patch.object(routes, "_idee_anlegen", ki):
            with pytest.raises(HTTPException) as e:
                _run(routes.zu_npc_machen("c1", "p1"))
        assert e.value.status_code == 409
        ki.assert_not_called()

    def test_leerer_kontaktplatz_409(self):
        ki = AsyncMock()
        platz = {"id": "p1", "istNebenfigur": True, "istBlankoKontakt": True}
        with patch.object(routes, "get_node", AsyncMock(return_value=platz)), \
             patch.object(routes, "_idee_anlegen", ki):
            with pytest.raises(HTTPException) as e:
                _run(routes.zu_npc_machen("c1", "p1"))
        assert e.value.status_code == 409
        ki.assert_not_called()

    def test_nebenfigur_geht_an_die_charakter_ki(self):
        person = {"id": "p1", "name": "Mama Okoro", "istNebenfigur": True, "description": "", "notes": ""}
        danach = {**person, "istNebenfigur": False}
        ki = AsyncMock(return_value={"id": "p1"})
        with patch.object(routes, "get_node", AsyncMock(side_effect=[person, danach])), \
             patch.object(routes, "_idee_anlegen", ki):
            ergebnis = _run(routes.zu_npc_machen("c1", "p1"))
        assert ergebnis["istNebenfigur"] is False
        args, kwargs = ki.call_args
        assert args[1] == "charakter"
        assert kwargs["nebenfigur"] is person


def test_charakter_ki_baut_bogen_in_place_mit_fixer_rasse():
    """Zu-NPC: kein neuer Knoten, Rasse bleibt, Fähigkeiten stehen im Stufe-2-Prompt."""
    from app.ki.routes import _idee_anlegen
    from app.traits.erstellung import HINTERGRUENDE
    from tests.test_erstellung import KATALOG
    from tests.test_ki_idee_typen import _stufe1_antwort, _stufe2_antwort

    nebenfigur = {
        "id": "p1", "name": "Mama Okoro", "rasse": "Ork", "alter": "61",
        "nebenfaehigkeiten": [{"name": "Straßenwissen", "wert": 4}],
    }

    async def run():
        ki = AsyncMock(side_effect=[_stufe1_antwort(rasse="Mensch"), _stufe2_antwort()])
        with (
            patch("app.ki.routes.sammle_kontext", AsyncMock(return_value="")),
            patch("app.ki.routes.generiere_json", ki),
            patch("app.ki.routes.list_catalog", AsyncMock(return_value=KATALOG)),
            patch("app.ki.routes.rassen_repository.liste_fuer_kampagne", AsyncMock(return_value=[])),
            patch("app.ki.routes.get_campaign", AsyncMock(return_value={"ruleset": "neotopia"})),
            patch("app.ki.routes.get_einstellungen", AsyncMock(return_value={})),
            patch("app.ki.routes.hintergruende_repository.pool_fuer_erstellung", AsyncMock(return_value=HINTERGRUENDE)),
            patch("app.ki.routes.create_node", AsyncMock()) as create,
            patch("app.ki.routes.update_node", AsyncMock(return_value={"id": "p1", "name": "Mama Okoro"})) as update,
            patch("app.ki.routes.set_ratings_bulk", AsyncMock()) as bulk,
            patch("app.ki.routes.setze_maxima_bulk", AsyncMock()),
            patch("app.ki.routes.ki_einkauf.einkaufen", AsyncMock()),
            patch("app.ki.routes.hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            ergebnis = await _idee_anlegen("c1", "charakter", "x", nebenfigur=nebenfigur)
            assert ergebnis["id"] == "p1"
            assert ergebnis["name"] == "Mama Okoro"
            create.assert_not_awaited()
            felder = update.await_args.args[4]
            assert felder["istNebenfigur"] is False
            assert felder["rasse"] == "Ork"
            assert felder["alter"] == "61"
            assert felder["erstellungAbgeschlossen"] is True
            assert "name" not in felder and "description" not in felder
            assert bulk.await_args.args[1] == "p1"
            prompt2 = ki.await_args_list[1].args[0]
            assert "Straßenwissen 4" in prompt2

    _run(run())


def test_ki_nebenfigur_als_entwurf_mit_beziehungsvorschlag():
    from app.nebenfiguren import ki as nf_ki

    antwort = {
        "name": "Ada Okoro", "rasse": "Elf", "alter": "17", "persoenlichkeit": "Schlitzohr",
        "beschreibung": "Tochter.", "notizen": "", "beziehung": "  Tochter   von ",
        "faehigkeiten": [{"name": "Klatsch", "wert": 9}],
    }

    async def run():
        create = AsyncMock(side_effect=lambda label, felder, cid, daten: {"id": "n1", **daten})
        with (
            patch.object(nf_ki, "_rassen_fuer_ki", lambda liste: {"Mensch": {}, "Ork": {}}),
            patch.object(nf_ki.rassen_repository, "liste_fuer_kampagne", AsyncMock(return_value=[])),
            patch.object(nf_ki, "sammle_kontext", AsyncMock(return_value="")),
            patch.object(nf_ki, "generiere_json", AsyncMock(return_value=antwort)),
            patch.object(nf_ki, "create_node", create),
            patch.object(nf_ki, "hooks") as hooks,
        ):
            hooks.ki = AsyncMock()
            person = await nf_ki.nebenfigur_generieren("c1", "Familie von X", entwurf=True)
        daten = create.await_args.args[3]
        assert daten["istEntwurf"] is True
        assert daten["istNebenfigur"] is True
        assert daten["rasse"] == "Mensch"  # Elf ist hier nicht freigegeben
        assert daten["nebenfaehigkeiten"] == [{"name": "Klatsch", "wert": 5}]
        assert person["beziehungVorschlag"] == "Tochter von"

    _run(run())


def test_idee_nebenfigur_geht_als_entwurf_an_den_nebenfiguren_generator():
    from app.ki.routes import _idee_anlegen

    async def run():
        gen = AsyncMock(return_value={"id": "n1", "name": "Ada", "beziehungVorschlag": "Tochter von"})
        with patch("app.nebenfiguren.ki.nebenfigur_generieren", gen):
            ergebnis = await _idee_anlegen("c1", "nebenfigur", "Familie")
        assert ergebnis == {"typ": "nebenfigur", "id": "n1", "name": "Ada", "beziehung": "Tochter von"}
        assert gen.await_args.kwargs["entwurf"] is True

    _run(run())


def test_massen_nebenfiguren_nehmen_den_ki_vorschlag_als_kante():
    from app.ki import routes as ki_routes

    async def run():
        idee = AsyncMock(side_effect=[
            {"typ": "nebenfigur", "id": "n1", "name": "Ada", "beziehung": "Tochter von"},
            {"typ": "nebenfigur", "id": "n2", "name": "Bo", "beziehung": ""},
        ])
        kante = AsyncMock()
        with (
            patch.object(ki_routes, "_idee_anlegen", idee),
            patch.object(ki_routes, "_ziel_node", AsyncMock(return_value={"id": "x", "name": "Okoro"})),
            patch.object(ki_routes, "verknuepfung_beziehung_anwenden", kante),
        ):
            ergebnis = await ki_routes._massen_anlegen("c1", "nebenfigur", "Familie", 2, "Person", "x", None)
        typen = [c.args[1].beziehungstyp for c in kante.await_args_list]
        assert typen == ["Tochter von", "kennt"]
        assert kante.await_args_list[0].args[1].typ1 == "Person"
        assert all(e.verknuepft for e in ergebnis.eintraege)

    _run(run())


def test_massen_feste_beziehung_schlaegt_den_ki_vorschlag():
    from app.ki import routes as ki_routes

    async def run():
        idee = AsyncMock(return_value={"typ": "nebenfigur", "id": "n1", "name": "Ada", "beziehung": "Tochter von"})
        kante = AsyncMock()
        with (
            patch.object(ki_routes, "_idee_anlegen", idee),
            patch.object(ki_routes, "_ziel_node", AsyncMock(return_value={"id": "x", "name": "Okoro"})),
            patch.object(ki_routes, "verknuepfung_beziehung_anwenden", kante),
        ):
            await ki_routes._massen_anlegen("c1", "nebenfigur", "Familie", 1, "Person", "x", "Familie von")
        assert kante.await_args.args[1].beziehungstyp == "Familie von"

    _run(run())


def test_spawn_legt_kontakt_plaetze_als_nebenfigur_an():
    from app.hintergruende import spawn

    async def run():
        create = AsyncMock(side_effect=[{"id": "k1"}, {"id": "k2"}])
        with (
            patch.object(spawn.repository, "kontaktslots_der_person", AsyncMock(return_value=[])),
            patch.object(spawn.repository, "fuege_kontaktslot_hinzu", AsyncMock()),
            patch.object(spawn.kontakte_repository, "anlegen", AsyncMock()),
            patch.object(spawn, "create_node", create),
        ):
            await spawn.kontakte_nach_erstellung("c1", "pc1", 2)
        for aufruf in create.await_args_list:
            daten = aufruf.args[3]
            assert daten["istBlankoKontakt"] is True and daten["istNebenfigur"] is True

    _run(run())
