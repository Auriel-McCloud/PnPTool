"""Spieler↔Spieler-Chat (PC ↔ PC): Sichtbarkeit, Absender, Zustellung, Annahme.

Kein Neo4j nötig — Repository und Verteiler sind gemockt. Der Cypher-Teil
(`spielerkontakt_anlegen`, `mitspieler`) wurde einmal von Hand gegen die lokale
Neo4j geprüft (Anlegen idempotent, Ungelesen-Zähler, SL-Liste ohne Spielerkontakt).
"""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.auth.dependencies import Viewer
from app.kontakte import routes
from app.kontakte.schemas import NachrichtCreate, SpielerKontaktAnfrage
from app.kontakte.security import darf_kontakt_sehen, kontakt_fuer_gm, kontakt_fuer_viewer
from app.verhandlung import logic
from app.verhandlung.logic import VerhandlungsFehler

_run = asyncio.run

ICH = Viewer(role="PLAYER", person_id="pc-a")
ANDERER = Viewer(role="PLAYER", person_id="pc-b")
SL = Viewer(role="GM", person_id=None)


def pc_kontakt(**kwargs) -> dict:
    """Die KENNT-Kante von Spieler A zu Spieler B."""
    basis = {
        "id": "k-ab",
        "pcId": "pc-a",
        "pcName": "Ryu",
        "npcId": "pc-b",
        "npcName": "Mara Voss",
        "npcAlias": "",
        "npcRasse": "Elf",
        "npcPersonType": "PC",
        "npcBildUrl": "mara.png",
        "npcDescription": "Geheimer Hintergrund: Doppelagentin.",
        "alias": "",
        "persoenlicherAlias": "",
        "persoenlicheNotizen": "",
        "stufe": "KONTAKT_AUSGETAUSCHT",
        "echterNameBekannt": True,
        "kontaktAnfrageStatus": "ANGENOMMEN",
        "chatOffen": True,
        "ungelesen": 0,
    }
    basis.update(kwargs)
    return basis


class TestSichtbarkeit:
    def test_nur_der_besitzer_der_kante_sieht_sie(self):
        assert darf_kontakt_sehen(pc_kontakt(), ICH)
        assert not darf_kontakt_sehen(pc_kontakt(), ANDERER)

    def test_spielleitung_sieht_spielerchats_nicht(self):
        assert not darf_kontakt_sehen(pc_kontakt(), SL)

    def test_npc_kontakte_bleiben_fuer_die_spielleitung_sichtbar(self):
        npc = pc_kontakt(npcPersonType="NPC")
        assert darf_kontakt_sehen(npc, SL)

    def test_ohne_eigene_person_gar_nichts(self):
        assert not darf_kontakt_sehen(pc_kontakt(), Viewer(role="PLAYER", person_id=None))


class TestSortierung:
    """Der neueste Chat steht oben: die Liste liefert die Zeit der letzten Aktivität mit."""

    def _liste(self, monkeypatch, kontakte, letzte):
        monkeypatch.setattr(routes.repository, "liste_fuer_pc", AsyncMock(return_value=kontakte))
        monkeypatch.setattr(routes.repository, "letzte_nachrichten", AsyncMock(return_value=letzte))
        return _run(routes.meine_kontakte("c-1", ICH))

    def test_letzte_nachricht_schlaegt_die_anlage(self, monkeypatch):
        a = pc_kontakt(id="k-a", npcId="x1", erstelltAm="2026-01-01T00:00:00+00:00")
        b = pc_kontakt(id="k-b", npcId="x2", erstelltAm="2026-02-01T00:00:00+00:00")
        antwort = self._liste(monkeypatch, [a, b], {"x1": "2026-03-01T00:00:00+00:00"})
        zeiten = {k.id: k.letzteAktivitaet for k in antwort}
        assert zeiten == {"k-a": "2026-03-01T00:00:00+00:00", "k-b": "2026-02-01T00:00:00+00:00"}

    def test_ohne_nachricht_gilt_die_anlage_des_kontakts(self, monkeypatch):
        a = pc_kontakt(npcId="x1", erstelltAm="2026-01-01T00:00:00+00:00")
        assert self._liste(monkeypatch, [a], {})[0].letzteAktivitaet == "2026-01-01T00:00:00+00:00"

    def test_altbestand_ohne_zeit_bleibt_leer_und_stoert_nicht(self, monkeypatch):
        a = pc_kontakt(npcId="x1")
        assert self._liste(monkeypatch, [a], {})[0].letzteAktivitaet == ""


class TestAnzeige:
    def test_name_des_mitspielers_ohne_alias(self):
        antwort = kontakt_fuer_viewer(pc_kontakt(), ICH)
        assert antwort.alias == "Mara Voss"
        assert antwort.echterName == "Mara Voss"
        assert antwort.chatOffen is True

    def test_eigener_alias_schlaegt_den_namen(self):
        antwort = kontakt_fuer_viewer(pc_kontakt(persoenlicherAlias="Die Elfe"), ICH)
        assert antwort.alias == "Die Elfe"

    def test_beschreibung_des_mitspielers_bleibt_privat(self):
        antwort = kontakt_fuer_viewer(pc_kontakt(), ICH)
        assert antwort.beschreibung == ""
        assert "Doppelagentin" not in str(antwort.model_dump())

    def test_rasse_ergibt_keinen_unbekannter_alias(self):
        # Bei NPCs wäre der Fallback „Unbekannter Elf“ — bei PCs gilt der Name.
        assert "Unbekannter" not in kontakt_fuer_viewer(pc_kontakt(), ICH).alias

    def test_npc_beschreibung_bleibt_wie_vorher(self):
        npc = pc_kontakt(npcPersonType="NPC", echterNameBekannt=False, stufe="GESPROCHEN")
        assert "Doppelagentin" in kontakt_fuer_viewer(npc, ICH).beschreibung
        assert kontakt_fuer_gm(npc).npcName == "Mara Voss"


def _senden_vorbereiten(monkeypatch, roh):
    monkeypatch.setattr(routes.repository, "hole", AsyncMock(return_value=roh))
    # Die Kante des EMPFÄNGERS (Gegenrichtung) — dorthin führt „Zum Chat“.
    monkeypatch.setattr(routes.repository, "spielerkontakt_id", AsyncMock(return_value="k-ba"))
    sende = AsyncMock(
        return_value={"id": "n-1", "inhalt": "x", "erstelltAm": "", "gelesenAm": None, "vonId": roh["pcId"]}
    )
    monkeypatch.setattr(routes.repository, "sende", sende)
    mitteilung = AsyncMock(return_value={"id": "m-1"})
    monkeypatch.setattr(routes.mitteilungen_repo, "create_mitteilung", mitteilung)
    verteilt = AsyncMock()
    monkeypatch.setattr(routes.verteiler, "verteilen", verteilt)
    return sende, mitteilung


class TestSenden:
    def test_nachricht_geht_an_den_anderen_spieler_nicht_an_die_sl(self, monkeypatch):
        sende, mitteilung = _senden_vorbereiten(monkeypatch, pc_kontakt())

        _run(routes.nachricht_senden("c-1", "k-ab", NachrichtCreate(inhalt="Hallo"), ICH))

        # VON = ich, AN = Mitspieler
        assert sende.await_args.args[1:3] == ("pc-a", "pc-b")
        kwargs = mitteilung.await_args.kwargs
        # Leere Liste würde die SL benachrichtigen — hier muss der Empfänger stehen.
        assert kwargs["empfaenger_ids"] == ["pc-b"]
        assert kwargs["art"] == "NACHRICHT"
        assert kwargs["inhalt"].startswith("Ryu:")
        # „Zum Chat“ beim Mitspieler: SEINE Kante (Gegenrichtung), nicht die des Absenders.
        assert (kwargs["chat_art"], kwargs["chat_id"]) == ("KONTAKT", "k-ba")

    def test_npc_chat_geht_weiter_an_die_sl(self, monkeypatch):
        sende, mitteilung = _senden_vorbereiten(monkeypatch, pc_kontakt(npcPersonType="NPC"))

        _run(routes.nachricht_senden("c-1", "k-ab", NachrichtCreate(inhalt="Hallo"), ICH))

        assert mitteilung.await_args.kwargs["empfaenger_ids"] == []
        # NPC-Chat: dieselbe Kante für SL und Spieler.
        assert (mitteilung.await_args.kwargs["chat_art"], mitteilung.await_args.kwargs["chat_id"]) == (
            "KONTAKT",
            "k-ab",
        )

    def test_npc_popup_beim_spieler_nennt_den_alias_nie_den_echten_namen(self, monkeypatch):
        # Die SL schreibt als NPC — das Popup landet beim Spieler.
        sende, mitteilung = _senden_vorbereiten(
            monkeypatch,
            pc_kontakt(npcPersonType="NPC", npcName="Viktor Kane", npcRasse="Ork", echterNameBekannt=False),
        )

        _run(routes.nachricht_senden("c-1", "k-ab", NachrichtCreate(inhalt="Moin"), SL))

        text = mitteilung.await_args.kwargs["inhalt"]
        assert text == "Unbekannter Ork: Moin"
        assert "Viktor" not in text

    def test_fremder_spieler_kommt_nicht_an_den_chat(self, monkeypatch):
        _senden_vorbereiten(monkeypatch, pc_kontakt())
        with pytest.raises(HTTPException) as fehler:
            _run(routes.nachricht_senden("c-1", "k-ab", NachrichtCreate(inhalt="Hallo"), ANDERER))
        assert fehler.value.status_code == 404

    def test_spielleitung_kann_nicht_in_spielerchats_schreiben(self, monkeypatch):
        sende, _ = _senden_vorbereiten(monkeypatch, pc_kontakt())
        with pytest.raises(HTTPException) as fehler:
            _run(routes.nachricht_senden("c-1", "k-ab", NachrichtCreate(inhalt="Hallo"), SL))
        assert fehler.value.status_code == 404
        sende.assert_not_awaited()


class TestLesen:
    def test_spielerchat_zeigt_den_namen_als_absender(self, monkeypatch):
        monkeypatch.setattr(routes.repository, "hole", AsyncMock(return_value=pc_kontakt()))
        monkeypatch.setattr(routes.repository, "markiere_gelesen", AsyncMock())
        monkeypatch.setattr(
            routes.repository,
            "nachrichten",
            AsyncMock(
                return_value=[
                    {"id": "n-1", "inhalt": "Hi", "erstelltAm": "", "gelesenAm": None, "vonId": "pc-b"},
                    {"id": "n-2", "inhalt": "Na", "erstelltAm": "", "gelesenAm": None, "vonId": "pc-a"},
                ]
            ),
        )

        chat = _run(routes.chat_lesen("c-1", "k-ab", ICH))

        assert chat.alias == "Mara Voss"
        assert chat.nachrichten[0].vonMir is False and chat.nachrichten[0].absender == "Mara Voss"
        assert chat.nachrichten[1].vonMir is True

    def test_sl_bekommt_den_verlauf_nicht(self, monkeypatch):
        monkeypatch.setattr(routes.repository, "hole", AsyncMock(return_value=pc_kontakt()))
        with pytest.raises(HTTPException) as fehler:
            _run(routes.chat_lesen("c-1", "k-ab", SL))
        assert fehler.value.status_code == 404


class TestAnfrage:
    def _vorbereiten(self, monkeypatch, *, bereits=False, offene=None):
        mitspieler = [{"id": "pc-b", "name": "Mara Voss", "bildUrl": "", "bereitsKontakt": bereits}]
        monkeypatch.setattr(routes.repository, "mitspieler", AsyncMock(return_value=mitspieler))
        monkeypatch.setattr(
            routes.verhandlung_repository, "list_offene_fuer", AsyncMock(return_value=offene or [])
        )
        monkeypatch.setattr(
            routes.entities_repository, "get_node", AsyncMock(return_value={"name": "Ryu"})
        )
        angelegt = AsyncMock(return_value={"id": "v-1", "empfaengerPersonId": "pc-b"})
        monkeypatch.setattr(routes.verhandlung_repository, "create_verhandlung", angelegt)
        verteilt = AsyncMock()
        monkeypatch.setattr(routes.verteiler, "verteilen", verteilt)
        return angelegt, verteilt

    def test_anfrage_geht_als_verhandlung_an_den_mitspieler(self, monkeypatch):
        angelegt, verteilt = self._vorbereiten(monkeypatch)

        _run(routes.spieler_kontakt_anfragen("c-1", SpielerKontaktAnfrage(personId="pc-b"), ICH))

        args = angelegt.await_args.args
        assert args[1] == "pc-b" and args[2] == "SPIELER_KONTAKT"
        assert args[3][0]["bezeichnung"] == "Ryu möchte Kontakt mit dir austauschen"
        assert args[4] == {"anfragenderPersonId": "pc-a"}
        # Live-Zustellung nur an den Empfänger.
        assert verteilt.await_args.args[1]["empfaengerIds"] == ["pc-b"]

    @pytest.mark.parametrize(
        "ziel,erwartet",
        [("pc-a", 400), ("pc-unbekannt", 404)],
    )
    def test_ungueltige_ziele(self, monkeypatch, ziel, erwartet):
        self._vorbereiten(monkeypatch)
        with pytest.raises(HTTPException) as fehler:
            _run(routes.spieler_kontakt_anfragen("c-1", SpielerKontaktAnfrage(personId=ziel), ICH))
        assert fehler.value.status_code == erwartet

    def test_schon_kontakt_ergibt_409(self, monkeypatch):
        self._vorbereiten(monkeypatch, bereits=True)
        with pytest.raises(HTTPException) as fehler:
            _run(routes.spieler_kontakt_anfragen("c-1", SpielerKontaktAnfrage(personId="pc-b"), ICH))
        assert fehler.value.status_code == 409

    @pytest.mark.parametrize("empfaenger_offen", ["pc-b", "pc-a"])
    def test_keine_doppelte_anfrage_in_keine_richtung(self, monkeypatch, empfaenger_offen):
        anfragender = "pc-a" if empfaenger_offen == "pc-b" else "pc-b"
        offen = [{"art": "SPIELER_KONTAKT", "kontext": {"anfragenderPersonId": anfragender}}]

        async def offene_fuer(_cid, person_id):
            return offen if person_id == empfaenger_offen else []

        angelegt, _ = self._vorbereiten(monkeypatch)
        monkeypatch.setattr(routes.verhandlung_repository, "list_offene_fuer", offene_fuer)
        with pytest.raises(HTTPException) as fehler:
            _run(routes.spieler_kontakt_anfragen("c-1", SpielerKontaktAnfrage(personId="pc-b"), ICH))
        assert fehler.value.status_code == 409
        angelegt.assert_not_awaited()

    def test_spielleitung_hat_keinen_eigenen_charakter(self, monkeypatch):
        self._vorbereiten(monkeypatch)
        with pytest.raises(HTTPException) as fehler:
            _run(routes.spieler_kontakt_anfragen("c-1", SpielerKontaktAnfrage(personId="pc-b"), SL))
        assert fehler.value.status_code == 400


class TestAnnahme:
    def _verhandlung(self):
        return {
            "id": "v-1",
            "art": "SPIELER_KONTAKT",
            "empfaengerPersonId": "pc-b",
            "kontext": {"anfragenderPersonId": "pc-a"},
        }

    def test_annahme_legt_beide_richtungen_an(self, monkeypatch):
        anlegen = AsyncMock(return_value=True)
        monkeypatch.setattr(logic.kontakte_repository, "spielerkontakt_anlegen", anlegen)

        ergebnis = _run(logic.ausfuehren("c-1", self._verhandlung()))

        anlegen.assert_awaited_once_with("c-1", "pc-a", "pc-b")
        assert ergebnis == {"anfragenderPersonId": "pc-a"}

    def test_verschwundener_charakter_bricht_ab(self, monkeypatch):
        monkeypatch.setattr(
            logic.kontakte_repository, "spielerkontakt_anlegen", AsyncMock(return_value=False)
        )
        with pytest.raises(VerhandlungsFehler):
            _run(logic.ausfuehren("c-1", self._verhandlung()))

    def test_kontakt_mit_sich_selbst_wird_abgelehnt(self, monkeypatch):
        anlegen = AsyncMock(return_value=True)
        monkeypatch.setattr(logic.kontakte_repository, "spielerkontakt_anlegen", anlegen)
        verhandlung = self._verhandlung()
        verhandlung["kontext"]["anfragenderPersonId"] = "pc-b"
        with pytest.raises(VerhandlungsFehler):
            _run(logic.ausfuehren("c-1", verhandlung))
        anlegen.assert_not_awaited()
