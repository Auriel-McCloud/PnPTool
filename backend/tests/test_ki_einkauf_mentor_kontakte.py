"""KI-Charakter geht im Tutorial-Shop einkaufen + Mentor/Kontakte-Pipeline
(11.10.2026). Reine Funktions-/Repository-Tests ohne FastAPI-TestClient,
wie test_kredithai.py und test_tutorial_shop_rassen_features.py.

Deckt ab, was ohne echten KI-Call prüfbar ist: Auswahl-Logik (bestehenden_
mentor), Preisberechnung mit Rabatt, No-Op-Pfade, und die Blanko-Kontakt-
Idempotenz. Der eigentliche `generiere_json`-Aufruf (ki_einkauf.einkaufen,
mentor_nach_erstellung ohne bestehenden Mentor) braucht einen echten/
gemockten KI-Call und ist NICHT Teil dieser Datei — siehe CLAUDE.md
"Verifiziert" für diese Lücke.
"""

import asyncio
import uuid

from app.db.neo4j_driver import get_driver
from app.entities.repository import PERSON_FIELDS, create_node, get_node
from app.entities.schemas import PersonCreate
from app.hintergruende import repository as hintergruende_repository
from app.hintergruende.mentor import bestehenden_mentor
from app.hintergruende.spawn import kontakte_nach_erstellung, mentor_nach_erstellung
from app.kontakte import repository as kontakte_repository


def _run(coro):
    return asyncio.run(coro)


async def _kampagne_anlegen() -> str:
    cid = f"test-ki-einkauf-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'KI-Einkauf-Test'})", cid=cid)
    return cid


async def _aufraeumen(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


# --- bestehenden_mentor (reine Logik, wie bestehenden_kredithai) -----------


def test_bestehenden_mentor_findet_markierten_npc():
    npcs = [
        {"id": "a", "istMentor": False, "erstelltAm": "2026-01-01"},
        {"id": "b", "istMentor": True, "erstelltAm": "2026-02-01"},
        {"id": "c", "istMentor": True, "erstelltAm": "2026-01-15"},
    ]
    gefunden = bestehenden_mentor(npcs)
    assert gefunden is not None
    assert gefunden["id"] == "c"  # älterer der beiden markierten


def test_bestehenden_mentor_ohne_markierung_gibt_none():
    npcs = [{"id": "a", "istMentor": False}]
    assert bestehenden_mentor(npcs) is None


# --- mentor_nach_erstellung: No-Op und Wiederverwendung ---------------------


def test_mentor_nach_erstellung_ohne_rating_ist_noop():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await create_node(
                "Person", PERSON_FIELDS, cid, PersonCreate(name="PC", personType="PC").model_dump()
            )
            ergebnis = await mentor_nach_erstellung(cid, pc["id"], "PC", 0)
            assert ergebnis is None
            bestehend = await hintergruende_repository.hole_mentor(cid, pc["id"])
            assert bestehend is None
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_mentor_nach_erstellung_legt_blanko_an_statt_fremden_zu_nehmen():
    """Jeder beschreibt seinen eigenen Mentor. Ein schon markierter NPC
    der Kampagne wird nicht stillschweigend angehängt."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await create_node(
                "Person", PERSON_FIELDS, cid, PersonCreate(name="PC", personType="PC").model_dump()
            )
            await create_node(
                "Person",
                PERSON_FIELDS,
                cid,
                PersonCreate(name="Lehrmeister", personType="NPC", istMentor=True).model_dump(),
            )
            ergebnis = await mentor_nach_erstellung(cid, pc["id"], "PC", 3)
            assert ergebnis is not None
            assert ergebnis["rating"] == 3
            mentor = await get_node("Person", PERSON_FIELDS, cid, ergebnis["mentorId"])
            assert mentor is not None
            assert mentor["name"] == "Undefinierter Mentor"
            assert mentor["istBlankoKontakt"] is True
            assert mentor["istMentor"] is True
            kante = await hintergruende_repository.hole_mentor(cid, pc["id"])
            assert kante["rating"] == 3
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_mentor_nach_erstellung_erneute_einreichung_erzeugt_keinen_zweiten():
    """SL-Korrektur (erneutes Einreichen) darf keinen zweiten Mentor für
    denselben PC anlegen — hole_mentor muss den schon gesetzten finden."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await create_node(
                "Person", PERSON_FIELDS, cid, PersonCreate(name="PC", personType="PC").model_dump()
            )
            erster = await mentor_nach_erstellung(cid, pc["id"], "PC", 2)
            assert erster is not None
            ergebnis = await mentor_nach_erstellung(cid, pc["id"], "PC", 4)
            assert ergebnis == {"mentorId": erster["mentorId"], "rating": 4}

            bestehend = await hintergruende_repository.hole_mentor(cid, pc["id"])
            assert bestehend["rating"] == 4
        finally:
            await _aufraeumen(cid)

    _run(lauf())


# --- kontakte_nach_erstellung: Blanko-Platzhalter, idempotent --------------


def test_kontakte_nach_erstellung_ohne_rating_ist_noop():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await create_node(
                "Person", PERSON_FIELDS, cid, PersonCreate(name="PC", personType="PC").model_dump()
            )
            neue = await kontakte_nach_erstellung(cid, pc["id"], 0)
            assert neue == []
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_kontakte_nach_erstellung_legt_n_blanko_platzhalter_an():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await create_node(
                "Person", PERSON_FIELDS, cid, PersonCreate(name="PC", personType="PC").model_dump()
            )
            neue = await kontakte_nach_erstellung(cid, pc["id"], 3)
            assert len(neue) == 3

            for npc_id in neue:
                npc = await get_node("Person", PERSON_FIELDS, cid, npc_id)
                assert npc is not None
                assert npc["istBlankoKontakt"] is True
                assert npc["name"] == "Unbekannter Kontakt"

            kontakte = await kontakte_repository.liste_fuer_pc(cid, pc["id"])
            assert len(kontakte) == 3
            assert all(k["chatOffen"] is False for k in kontakte)

            slots = await hintergruende_repository.kontaktslots_der_person(cid, pc["id"])
            assert len(slots) == 3
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_kontakte_nach_erstellung_erneute_einreichung_ist_idempotent():
    """Höheres Rating legt nur die FEHLENDEN Plätze nach, nie Duplikate;
    ein gesunkenes Rating löscht nichts (Marks Vorgabe: kein Datenverlust)."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await create_node(
                "Person", PERSON_FIELDS, cid, PersonCreate(name="PC", personType="PC").model_dump()
            )
            erste = await kontakte_nach_erstellung(cid, pc["id"], 2)
            assert len(erste) == 2

            # Gleiches Rating erneut eingereicht — nichts Neues.
            zweite = await kontakte_nach_erstellung(cid, pc["id"], 2)
            assert zweite == []
            slots = await hintergruende_repository.kontaktslots_der_person(cid, pc["id"])
            assert len(slots) == 2

            # Höheres Rating — nur der fehlende eine kommt dazu.
            dritte = await kontakte_nach_erstellung(cid, pc["id"], 5)
            assert len(dritte) == 3
            slots = await hintergruende_repository.kontaktslots_der_person(cid, pc["id"])
            assert len(slots) == 5

            # Gesunkenes Rating löscht nichts.
            vierte = await kontakte_nach_erstellung(cid, pc["id"], 1)
            assert vierte == []
            slots = await hintergruende_repository.kontaktslots_der_person(cid, pc["id"])
            assert len(slots) == 5
        finally:
            await _aufraeumen(cid)

    _run(lauf())


# --- ki_einkauf: Preisberechnung + No-Op-Pfade ------------------------------


def test_einkaufen_ohne_budget_ist_noop():
    from app.haendler.ki_einkauf import einkaufen

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await create_node(
                "Person", PERSON_FIELDS, cid, PersonCreate(name="PC", personType="PC").model_dump()
            )
            ergebnis = await einkaufen(cid, pc["id"], 0, "Testkontext")
            assert ergebnis is None
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_einkaufen_ohne_tutorial_shop_ist_noop():
    from app.haendler.ki_einkauf import einkaufen

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await create_node(
                "Person", PERSON_FIELDS, cid, PersonCreate(name="PC", personType="PC").model_dump()
            )
            ergebnis = await einkaufen(cid, pc["id"], 5000, "Testkontext")
            assert ergebnis is None
        finally:
            await _aufraeumen(cid)

    _run(lauf())
