"""Gruppenchat: Sichtbarkeit der Namen, Rechte, Absender und Benachrichtigung.

Kein Neo4j nötig — Repository und Verteiler sind gemockt. Der Cypher-Teil wurde
einmal von Hand gegen die lokale Neo4j geprüft (siehe CLAUDE.md).
"""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Viewer
from app.gruppenchat import routes
from app.gruppenchat.schemas import GruppeCreate, GruppenNachrichtCreate, GruppeUpdate
from app.gruppenchat.security import gruppe_fuer, nachricht_fuer

_run = asyncio.run

RYU = Viewer(role="PLAYER", person_id="pc-a")
MARA = Viewer(role="PLAYER", person_id="pc-b")
FREMD = Viewer(role="PLAYER", person_id="pc-x")
SL = Viewer(role="GM", person_id=None)


def gruppe(offen: bool = True, mit_npc: bool = True) -> dict:
    teilnehmer = [
        {"id": "pc-a", "name": "Ryu", "personType": "PC", "bildUrl": "", "alias": "", "rasse": "Mensch"},
        {"id": "pc-b", "name": "Mara Voss", "personType": "PC", "bildUrl": "m.png", "alias": "", "rasse": "Elf"},
    ]
    if mit_npc:
        teilnehmer.append(
            {"id": "npc-1", "name": "Viktor Kane", "personType": "NPC", "bildUrl": "v.png", "alias": "", "rasse": "Ork"}
        )
    return {"id": "g1", "name": "Nachtschicht", "offen": offen, "ungelesen": 0, "teilnehmer": teilnehmer}


def nachricht(von: str, name: str, typ: str, text: str = "Hi", **extra) -> dict:
    return {
        "id": f"n-{von}",
        "inhalt": text,
        "erstelltAm": "2026-11-07T10:00:00+00:00",
        "rolle": "PLAYER",
        "vonId": von,
        "vonName": name,
        "vonTyp": typ,
        "vonBildUrl": "",
        "vonAlias": "",
        "vonRasse": "Ork" if typ == "NPC" else "Mensch",
        **extra,
    }


class TestNamenProBetrachter:
    def test_spieler_sieht_npc_nur_unter_alias(self):
        antwort = gruppe_fuer(gruppe(), ich_id="pc-a", aliase={}, als_gm=False)
        npc = next(t for t in antwort.teilnehmer if t.istNpc)
        assert npc.name == "Unbekannter Ork"
        # Der echte Name darf in KEINEM Feld der Spielerantwort stehen.
        assert "Viktor" not in str(antwort.model_dump())

    def test_eigener_alias_schlaegt_die_rasse(self):
        antwort = gruppe_fuer(gruppe(), ich_id="pc-a", aliase={"npc-1": "Der Schläger"}, als_gm=False)
        assert next(t for t in antwort.teilnehmer if t.istNpc).name == "Der Schläger"

    def test_npc_alias_des_spielleiters_gilt_ohne_eigenen_alias(self):
        roh = gruppe()
        roh["teilnehmer"][2]["alias"] = "Die Faust"
        antwort = gruppe_fuer(roh, ich_id="pc-a", aliase={}, als_gm=False)
        assert next(t for t in antwort.teilnehmer if t.istNpc).name == "Die Faust"

    def test_mitspieler_erscheint_unter_charaktername_oder_eigenem_alias(self):
        ohne = gruppe_fuer(gruppe(), ich_id="pc-a", aliase={}, als_gm=False)
        assert next(t for t in ohne.teilnehmer if t.id == "pc-b").name == "Mara Voss"
        mit = gruppe_fuer(gruppe(), ich_id="pc-a", aliase={"pc-b": "Die Elfe"}, als_gm=False)
        assert next(t for t in mit.teilnehmer if t.id == "pc-b").name == "Die Elfe"

    def test_die_spielleitung_sieht_echte_namen(self):
        antwort = gruppe_fuer(gruppe(), ich_id=None, aliase={}, als_gm=True)
        assert {t.name for t in antwort.teilnehmer} == {"Ryu", "Mara Voss", "Viktor Kane"}

    def test_ich_ist_markiert(self):
        antwort = gruppe_fuer(gruppe(), ich_id="pc-a", aliase={}, als_gm=False)
        assert [t.id for t in antwort.teilnehmer if t.ich] == ["pc-a"]

    def test_bilder_werden_wie_im_einzelchat_mitgeliefert(self):
        antwort = gruppe_fuer(gruppe(), ich_id="pc-a", aliase={}, als_gm=False)
        assert next(t for t in antwort.teilnehmer if t.id == "npc-1").bildUrl == "v.png"


class TestNachrichtAnzeige:
    def test_spieler_eigene_rechts_ohne_absender_fremde_mit_alias(self):
        eigene = nachricht_fuer(nachricht("pc-a", "Ryu", "PC"), ich_id="pc-a", aliase={}, als_gm=False)
        assert eigene.vonMir is True and eigene.absender == ""
        npc = nachricht_fuer(nachricht("npc-1", "Viktor Kane", "NPC"), ich_id="pc-a", aliase={}, als_gm=False)
        assert npc.vonMir is False and npc.absender == "Unbekannter Ork"
        assert "Viktor" not in str(npc.model_dump())
        mitspieler = nachricht_fuer(nachricht("pc-b", "Mara Voss", "PC"), ich_id="pc-a", aliase={}, als_gm=False)
        assert mitspieler.vonMir is False and mitspieler.absender == "Mara Voss"

    def test_spielleitung_npc_rechts_pcs_links_mit_echten_namen(self):
        npc = nachricht_fuer(nachricht("npc-1", "Viktor Kane", "NPC"), ich_id=None, aliase={}, als_gm=True)
        pc = nachricht_fuer(nachricht("pc-a", "Ryu", "PC"), ich_id=None, aliase={}, als_gm=True)
        assert npc.vonMir is True and npc.absender == "Viktor Kane"
        assert pc.vonMir is False and pc.absender == "Ryu"


def _vorbereiten(monkeypatch, roh=None, verlauf=None):
    roh = roh or gruppe()
    repo = routes.repository
    monkeypatch.setattr(repo, "hole", AsyncMock(return_value=roh))
    monkeypatch.setattr(repo, "nachrichten", AsyncMock(return_value=verlauf or []))
    monkeypatch.setattr(repo, "persoenliche_aliase", AsyncMock(return_value={}))
    monkeypatch.setattr(repo, "markiere_gelesen", AsyncMock())
    monkeypatch.setattr(
        repo, "sende", AsyncMock(return_value=nachricht("pc-a", "Ryu", "PC", "Hallo"))
    )
    mitteilung = AsyncMock(return_value={"id": "m-1"})
    monkeypatch.setattr(routes.mitteilungen_repo, "create_mitteilung", mitteilung)
    monkeypatch.setattr(routes.verteiler, "verteilen", AsyncMock())
    return repo, mitteilung


class TestZugriff:
    def test_nichtmitglied_bekommt_404(self, monkeypatch):
        _vorbereiten(monkeypatch)
        with pytest.raises(HTTPException) as fehler:
            _run(routes.chat_lesen("c", "g1", FREMD))
        assert fehler.value.status_code == 404

    def test_geschlossene_gruppe_ist_fuer_spieler_unsichtbar_fuer_die_sl_nicht(self, monkeypatch):
        _vorbereiten(monkeypatch, gruppe(offen=False))
        with pytest.raises(HTTPException) as fehler:
            _run(routes.chat_lesen("c", "g1", RYU))
        assert fehler.value.status_code == 404
        assert _run(routes.chat_lesen("c", "g1", SL)).gruppe.offen is False

    def test_spieler_ohne_charakter_hat_keine_gruppen(self, monkeypatch):
        _vorbereiten(monkeypatch)
        assert _run(routes.meine_gruppen("c", Viewer(role="PLAYER", person_id=None))) == []

    def test_liste_des_spielers_nutzt_nur_den_eigenen_charakter(self, monkeypatch):
        repo, _ = _vorbereiten(monkeypatch)
        monkeypatch.setattr(repo, "liste_fuer_person", AsyncMock(return_value=[gruppe()]))
        antwort = _run(routes.meine_gruppen("c", RYU))
        repo.liste_fuer_person.assert_awaited_once_with("c", "pc-a")
        assert "Viktor" not in str(antwort)

    def test_lesen_markiert_fuer_spieler_gelesen_nicht_fuer_die_sl(self, monkeypatch):
        repo, _ = _vorbereiten(monkeypatch)
        _run(routes.chat_lesen("c", "g1", RYU))
        repo.markiere_gelesen.assert_awaited_once_with("c", "g1", "pc-a")
        repo.markiere_gelesen.reset_mock()
        _run(routes.chat_lesen("c", "g1", SL))
        repo.markiere_gelesen.assert_not_awaited()

    def test_sprecher_gibt_es_nur_fuer_die_spielleitung(self, monkeypatch):
        _vorbereiten(monkeypatch)
        assert _run(routes.chat_lesen("c", "g1", RYU)).sprecher == []
        sprecher = _run(routes.chat_lesen("c", "g1", SL)).sprecher
        assert [s.name for s in sprecher] == ["Viktor Kane"]

    def test_neue_mitglieder_sehen_die_ganze_historie(self, monkeypatch):
        # Der Verlauf wird nicht nach Beitrittszeit gefiltert.
        alt = [nachricht("pc-b", "Mara Voss", "PC", "ganz früher")]
        repo, _ = _vorbereiten(monkeypatch, verlauf=alt)
        antwort = _run(routes.chat_lesen("c", "g1", RYU))
        assert [n.id for n in antwort.nachrichten] == ["n-pc-b"]
        repo.nachrichten.assert_awaited_once_with("c", "g1")


class TestSenden:
    def test_spieler_schreibt_als_eigener_charakter(self, monkeypatch):
        repo, _ = _vorbereiten(monkeypatch)
        _run(routes.nachricht_senden("c", "g1", GruppenNachrichtCreate(inhalt="Hallo"), RYU))
        assert repo.sende.await_args.args[2] == "pc-a"
        assert repo.sende.await_args.args[4] == "PLAYER"

    def test_spieler_darf_nicht_als_jemand_anderes_schreiben(self, monkeypatch):
        repo, _ = _vorbereiten(monkeypatch)
        with pytest.raises(HTTPException) as fehler:
            _run(routes.nachricht_senden("c", "g1", GruppenNachrichtCreate(inhalt="x", alsPersonId="npc-1"), RYU))
        assert fehler.value.status_code == 403
        repo.sende.assert_not_awaited()

    def test_sl_schreibt_als_gewaehlter_npc(self, monkeypatch):
        repo, _ = _vorbereiten(monkeypatch)
        repo.sende.return_value = nachricht("npc-1", "Viktor Kane", "NPC", "Moin")
        antwort = _run(
            routes.nachricht_senden("c", "g1", GruppenNachrichtCreate(inhalt="Moin", alsPersonId="npc-1"), SL)
        )
        assert repo.sende.await_args.args[2] == "npc-1"
        assert antwort.vonMir is True

    @pytest.mark.parametrize("sprecher", [None, "pc-a", "npc-fremd"])
    def test_sl_braucht_ein_npc_mitglied_als_sprecher(self, monkeypatch, sprecher):
        repo, _ = _vorbereiten(monkeypatch)
        with pytest.raises(HTTPException) as fehler:
            _run(routes.nachricht_senden("c", "g1", GruppenNachrichtCreate(inhalt="x", alsPersonId=sprecher), SL))
        assert fehler.value.status_code == 400
        repo.sende.assert_not_awaited()

    def test_in_geschlossene_gruppe_schreibt_auch_die_sl_nicht(self, monkeypatch):
        _vorbereiten(monkeypatch, gruppe(offen=False))
        with pytest.raises(HTTPException) as fehler:
            _run(routes.nachricht_senden("c", "g1", GruppenNachrichtCreate(inhalt="x", alsPersonId="npc-1"), SL))
        assert fehler.value.status_code == 409

    def test_nichtmitglied_kann_nicht_schreiben(self, monkeypatch):
        repo, _ = _vorbereiten(monkeypatch)
        with pytest.raises(HTTPException) as fehler:
            _run(routes.nachricht_senden("c", "g1", GruppenNachrichtCreate(inhalt="x"), FREMD))
        assert fehler.value.status_code == 404
        repo.sende.assert_not_awaited()


class TestBenachrichtigung:
    @staticmethod
    def _empfaenger(mitteilung):
        return [c.kwargs["empfaenger_ids"] for c in mitteilung.await_args_list]

    def test_spieler_schreibt_andere_spieler_und_sl_wegen_npc(self, monkeypatch):
        _, mitteilung = _vorbereiten(monkeypatch)
        _run(routes.nachricht_senden("c", "g1", GruppenNachrichtCreate(inhalt="Hallo"), RYU))
        # Mara (ohne den Absender selbst) und die SL (leere Liste = an SL).
        assert self._empfaenger(mitteilung) == [["pc-b"], []]

    def test_ohne_npc_in_der_gruppe_erfaehrt_die_sl_nichts(self, monkeypatch):
        _, mitteilung = _vorbereiten(monkeypatch, gruppe(mit_npc=False))
        _run(routes.nachricht_senden("c", "g1", GruppenNachrichtCreate(inhalt="Hallo"), RYU))
        assert self._empfaenger(mitteilung) == [["pc-b"]]

    def test_sl_schreibt_nur_die_spieler_werden_benachrichtigt(self, monkeypatch):
        repo, mitteilung = _vorbereiten(monkeypatch)
        repo.sende.return_value = nachricht("npc-1", "Viktor Kane", "NPC", "Moin")
        _run(routes.nachricht_senden("c", "g1", GruppenNachrichtCreate(inhalt="Moin", alsPersonId="npc-1"), SL))
        assert self._empfaenger(mitteilung) == [["pc-a", "pc-b"]]

    def test_text_an_spieler_nennt_nur_die_gruppe_nie_den_npc_namen(self, monkeypatch):
        repo, mitteilung = _vorbereiten(monkeypatch)
        repo.sende.return_value = nachricht("npc-1", "Viktor Kane", "NPC", "Moin")
        _run(routes.nachricht_senden("c", "g1", GruppenNachrichtCreate(inhalt="Moin", alsPersonId="npc-1"), SL))
        text = mitteilung.await_args_list[0].kwargs["inhalt"]
        assert text == "Nachtschicht: Moin" and "Viktor" not in text

    def test_fehler_beim_benachrichtigen_blockiert_das_senden_nicht(self, monkeypatch):
        _, mitteilung = _vorbereiten(monkeypatch)
        mitteilung.side_effect = RuntimeError("ws weg")
        antwort = _run(routes.nachricht_senden("c", "g1", GruppenNachrichtCreate(inhalt="Hallo"), RYU))
        assert antwort.vonMir is True


class TestVerwaltung:
    def test_unbekannte_person_beim_anlegen_nimmt_die_gruppe_zurueck(self, monkeypatch):
        repo = routes.repository
        monkeypatch.setattr(repo, "anlegen", AsyncMock(return_value="g9"))
        monkeypatch.setattr(repo, "teilnehmer_hinzu", AsyncMock(side_effect=[True, False]))
        monkeypatch.setattr(repo, "loeschen", AsyncMock(return_value=True))
        with pytest.raises(HTTPException) as fehler:
            _run(routes.gruppe_anlegen("c", GruppeCreate(name="Neu", personIds=["pc-a", "weg"])))
        assert fehler.value.status_code == 404
        repo.loeschen.assert_awaited_once_with("c", "g9")

    def test_doppelte_personen_werden_nur_einmal_aufgenommen(self, monkeypatch):
        repo = routes.repository
        monkeypatch.setattr(repo, "anlegen", AsyncMock(return_value="g9"))
        monkeypatch.setattr(repo, "teilnehmer_hinzu", AsyncMock(return_value=True))
        monkeypatch.setattr(repo, "hole", AsyncMock(return_value=gruppe()))
        _run(routes.gruppe_anlegen("c", GruppeCreate(name=" Neu ", personIds=["pc-a", "pc-a", "npc-1"])))
        assert repo.teilnehmer_hinzu.await_count == 2
        assert repo.anlegen.await_args.args == ("c", "Neu")

    def test_schliessen_loescht_nichts(self, monkeypatch):
        repo = routes.repository
        monkeypatch.setattr(repo, "aendern", AsyncMock(return_value=True))
        monkeypatch.setattr(repo, "loeschen", AsyncMock())
        monkeypatch.setattr(repo, "hole", AsyncMock(return_value=gruppe(offen=False)))
        antwort = _run(routes.gruppe_aendern("c", "g1", GruppeUpdate(offen=False)))
        assert antwort.offen is False
        repo.loeschen.assert_not_awaited()
