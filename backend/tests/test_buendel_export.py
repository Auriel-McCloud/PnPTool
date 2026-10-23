"""Tests für das Kampagnen-Bündel-Feature (Phase 1: nur Export).

Echte Neo4j-Integration wie test_achievements.py: reine asyncio.run()-Aufrufe
gegen Repository-/Export-Funktionen, keine HTTP-Schicht. Knoten werden über
die echten Pydantic-Create-Schemas + model_dump() angelegt (wie die
tatsächlichen Routen es tun) statt über handgestrickte Teil-Dicts — sonst
fehlen create_node() Pflichtparameter aus den langen *_FIELDS-Listen.
"""

import asyncio
import io
import json
import uuid
import zipfile

from app.achievements import repository as achievements_repo
from app.campaigns.buendel_export import BUENDEL_REL_TYPES, collect_buendel_graph, export_buendel_zip
from app.db.neo4j_driver import get_driver
from app.entities import repository as entities_repo
from app.entities.schemas import FraktionCreate, OrtCreate, PersonCreate
from app.items import repository as items_repo
from app.rassen import repository as rassen_repo
from app.wiki import repository as wiki_repo


def _run(coro):
    return asyncio.run(coro)


async def _kampagne_anlegen() -> str:
    cid = f"test-buendel-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'Buendel-Test'})", cid=cid)
    return cid


async def _aufraeumen(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            "MATCH (c:Campaign {id: $cid}) OPTIONAL MATCH (c)-[:ERLAUBT_RASSE]->(r:Rasse) DETACH DELETE r",
            cid=cid,
        )
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


async def _ort(cid: str, name: str, **overrides) -> dict:
    daten = OrtCreate(name=name, **overrides).model_dump()
    return await entities_repo.create_node("Ort", entities_repo.ORT_FIELDS, cid, daten)


async def _person(cid: str, name: str, **overrides) -> dict:
    daten = PersonCreate(name=name, **overrides).model_dump()
    return await entities_repo.create_node("Person", entities_repo.PERSON_FIELDS, cid, daten)


async def _fraktion(cid: str, name: str, **overrides) -> dict:
    daten = FraktionCreate(name=name, **overrides).model_dump()
    return await entities_repo.create_node("Fraktion", entities_repo.FRAKTION_FIELDS, cid, daten)


async def _gegenstand(cid: str, owner_id: str | None, name: str, **overrides) -> dict:
    basis = {
        "name": name, "description": "", "notes": "", "typ": "Waffe", "preis": 10,
        "kraft": 0, "eigenschaften": {}, "storyRelevant": False, "einzigartig": True,
        "hatMenge": False, "menge": 1, "istVorlage": False, "seltenheit": 1,
        "automatischImShop": False, "sichtbarkeit": "GM", "sichtbarFuer": [],
    }
    basis.update(overrides)
    return await items_repo.create_gegenstand(cid, owner_id, basis)


async def _achievement(cid: str, name: str, **overrides) -> dict:
    basis = {"name": name, "art": "MANUELL", "einzigartig": False, "belohnungsArt": "KEINE", "belohnungsMenge": 0}
    basis.update(overrides)
    return await achievements_repo.anlegen(cid, basis)


async def _stammt_von_id(node_id: str) -> str | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run("MATCH (n {id: $id}) RETURN n.stammtVonId AS s", id=node_id)
        record = await result.single()
        return record["s"] if record else None


# ===========================================================================
# stammtVonId wird bei der Erstellung gesetzt — alle 9 Typen
# ===========================================================================


def test_stammt_von_id_bei_erstellung_fuer_generische_typen():
    """Ort/Event/Fraktion/Gewaechs/Person teilen sich create_node — Ort,
    Fraktion und Person decken die Stamp-Logik dort stellvertretend ab."""
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            ort = await _ort(cid, "Hafen")
            fraktion = await _fraktion(cid, "Zaibatsu")
            npc = await _person(cid, "Fixer", personType="NPC")

            for knoten in (ort, fraktion, npc):
                assert await _stammt_von_id(knoten["id"]) == knoten["id"]
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_stammt_von_id_gegenstand_wiki_rasse_achievement():
    async def lauf():
        cid = await _kampagne_anlegen()
        rasse = None
        try:
            item = await _gegenstand(cid, None, "Messer")
            seite = await wiki_repo.create_seite(cid, titel="Kapitel 1")
            rasse = await rassen_repo.anlegen({"name": f"Testrasse-{uuid.uuid4()}"})
            achievement = await _achievement(cid, "Testachievement")

            for nid in (item["id"], seite["id"], rasse["id"], achievement["id"]):
                assert await _stammt_von_id(nid) == nid
        finally:
            await _aufraeumen(cid)
            if rasse is not None:
                await rassen_repo.loeschen(rasse["id"])

    _run(lauf())


# ===========================================================================
# Papierkorb-Retrofit: delete setzt geloescht statt hart zu löschen
# ===========================================================================


def test_entities_delete_node_ist_jetzt_papierkorb():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            fraktion = await _fraktion(cid, "Zaibatsu")
            assert await entities_repo.delete_node("Fraktion", cid, fraktion["id"]) is True

            # Verschwunden aus der normalen Liste/Einzelabfrage...
            assert await entities_repo.get_node("Fraktion", entities_repo.FRAKTION_FIELDS, cid, fraktion["id"]) is None
            liste = await entities_repo.list_nodes("Fraktion", entities_repo.FRAKTION_FIELDS, cid)
            assert all(f["id"] != fraktion["id"] for f in liste)

            # ...aber der Knoten existiert weiter, nur mit geloescht=true.
            driver = get_driver()
            async with driver.session() as session:
                result = await session.run(
                    "MATCH (n:Fraktion {id: $id}) RETURN n.geloescht AS g", id=fraktion["id"]
                )
                record = await result.single()
                assert record is not None
                assert record["g"] is True
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_person_delete_wirft_besessene_gegenstaende_in_muelleimer():
    """Trash-Retrofit kaskadiert auf besessene Gegenstände über den
    bestehenden weggeworfen-Mechanismus statt sie verwaist zu lassen oder
    hart zu löschen."""
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            npc = await _person(cid, "Fixer", personType="NPC")
            item = await _gegenstand(cid, npc["id"], "Pistole")

            assert await entities_repo.delete_node("Person", cid, npc["id"]) is True

            frisch = await items_repo.get_gegenstand(cid, item["id"])
            assert frisch is not None
            assert frisch["weggeworfen"] is True
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_pc_delete_bleibt_hart_und_loest_spielt_kante():
    """PCs sind bewusst NICHT im Bündel-Scope (siehe Aufgabenstellung) — die
    Papierkorb-Retrofit in entities_repo.delete_node() darf PCs nicht
    anfassen, sonst bliebe die (:Spieler)-[:SPIELT]->(:Person)-Bindung nach
    einer SL-Löschung bestehen und der Spieler säße scheinbar weiter auf
    seinem (eigentlich gelöschten) alten Charakter, statt in den
    Ersteinstieg zu kommen (echte Regression, per Browser-Verifikation
    gefunden und hier fixiert)."""
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await _person(cid, "Held Max", personType="PC")

            driver = get_driver()
            spieler_id = f"test-spieler-{uuid.uuid4()}"
            async with driver.session() as session:
                await session.run(
                    """
                    MATCH (c:Campaign {id: $cid})
                    CREATE (s:Spieler {id: $sid, benutzername: $sid, campaignId: $cid})-[:GEHOERT_ZU]->(c)
                    WITH s
                    MATCH (p:Person {id: $pid})
                    CREATE (s)-[:SPIELT]->(p)
                    """,
                    cid=cid, sid=spieler_id, pid=pc["id"],
                )

            assert await entities_repo.delete_node("Person", cid, pc["id"]) is True

            async with driver.session() as session:
                # Knoten ist wirklich weg (hart gelöscht), nicht nur geloescht=true.
                result = await session.run("MATCH (p:Person {id: $id}) RETURN p", id=pc["id"])
                assert await result.single() is None
                # SPIELT-Kante ist mitentfernt worden (DETACH DELETE-Nebeneffekt).
                result = await session.run(
                    "MATCH (s:Spieler {id: $sid}) OPTIONAL MATCH (s)-[:SPIELT]->(p:Person) RETURN p",
                    sid=spieler_id,
                )
                record = await result.single()
                assert record["p"] is None
        finally:
            driver = get_driver()
            async with driver.session() as session:
                await session.run("MATCH (s:Spieler {campaignId: $cid}) DETACH DELETE s", cid=cid)
            await _aufraeumen(cid)

    _run(lauf())


def test_wiki_delete_seite_ist_papierkorb_und_zieht_kinder_hoch():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            eltern = await wiki_repo.create_seite(cid, titel="Kapitel 1")
            kind = await wiki_repo.create_seite(cid, titel="Szene 1", parent_id=eltern["id"])

            assert await wiki_repo.delete_seite(cid, eltern["id"]) is True
            assert await wiki_repo.get_seite(cid, eltern["id"]) is None

            kind_frisch = await wiki_repo.get_seite(cid, kind["id"])
            assert kind_frisch is not None
            assert kind_frisch["parentId"] is None  # eine Ebene hochgerückt
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_rasse_loeschen_ist_papierkorb():
    async def lauf():
        rasse = await rassen_repo.anlegen({"name": f"Testrasse-{uuid.uuid4()}"})
        try:
            assert await rassen_repo.loeschen(rasse["id"]) is True
            assert await rassen_repo.hole(rasse["id"]) is None
            alle = await rassen_repo.liste()
            assert all(r["id"] != rasse["id"] for r in alle)
        finally:
            driver = get_driver()
            async with driver.session() as session:
                await session.run("MATCH (r:Rasse {id: $id}) DETACH DELETE r", id=rasse["id"])

    _run(lauf())


def test_achievement_loeschen_ist_jetzt_papierkorb_ohne_guard():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            achievement = await _achievement(cid, "Test")
            assert await achievements_repo.loeschen(cid, achievement["id"]) is True
            assert await achievements_repo.hole(cid, achievement["id"]) is None
        finally:
            await _aufraeumen(cid)

    _run(lauf())


# ===========================================================================
# Export-Sammlung: PCs/geloescht/AchievementVerleihung/Ausschlüsse raus
# ===========================================================================


def test_collect_buendel_graph_schliesst_pc_geloescht_und_ausschluss_aus():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            npc = await _person(cid, "Bleibt", personType="NPC")
            pc = await _person(cid, "PC-Raus", personType="PC")
            geloescht_npc = await _person(cid, "Geloescht-Raus", personType="NPC")
            await entities_repo.delete_node("Person", cid, geloescht_npc["id"])
            ausgeschlossener_ort = await _ort(cid, "Abgewaehlt")

            knoten, _ = await collect_buendel_graph(cid, {ausgeschlossener_ort["id"]})
            ids = {n["id"] for n in knoten}

            assert npc["id"] in ids
            assert pc["id"] not in ids
            assert geloescht_npc["id"] not in ids
            assert ausgeschlossener_ort["id"] not in ids
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_collect_buendel_graph_rasse_ueber_erlaubt_rasse_kante():
    """Rasse hat kein campaignId — Kandidaten kommen über ERLAUBT_RASSE."""
    async def lauf():
        cid = await _kampagne_anlegen()
        rasse = await rassen_repo.anlegen({"name": f"Testrasse-{uuid.uuid4()}"})
        try:
            driver = get_driver()
            async with driver.session() as session:
                await session.run(
                    "MATCH (c:Campaign {id: $cid}), (r:Rasse {id: $rid}) MERGE (c)-[:ERLAUBT_RASSE]->(r)",
                    cid=cid, rid=rasse["id"],
                )
            knoten, _ = await collect_buendel_graph(cid, set())
            ids = {n["id"] for n in knoten}
            assert rasse["id"] in ids
        finally:
            await _aufraeumen(cid)
            driver = get_driver()
            async with driver.session() as session:
                await session.run("MATCH (r:Rasse {id: $id}) DETACH DELETE r", id=rasse["id"])

    _run(lauf())


def test_collect_buendel_graph_kanten_nur_zwischen_kollektierten_knoten():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            npc = await _person(cid, "Besitzer", personType="NPC")
            item = await _gegenstand(cid, npc["id"], "Katana")

            knoten, kanten = await collect_buendel_graph(cid, set())
            assert len(knoten) == 2
            besitzt_kanten = [k for k in kanten if k["relType"] == "BESITZT"]
            assert len(besitzt_kanten) == 1
            assert besitzt_kanten[0]["fromId"] == npc["id"]
            assert besitzt_kanten[0]["toId"] == item["id"]
            assert "BESITZT" in BUENDEL_REL_TYPES
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_export_buendel_zip_manifest_und_daten_form():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            ort = await _ort(cid, "Slum")

            inhalt, dateiname = await export_buendel_zip(
                cid, name="Mein Bündel", beschreibung="Testbeschreibung",
                tags=["test", "cyberpunk"], exclude_ids=[],
            )
            assert dateiname.startswith("buendel-")
            assert dateiname.endswith(".zip")

            with zipfile.ZipFile(io.BytesIO(inhalt)) as zf:
                namen = set(zf.namelist())
                assert "manifest.json" in namen
                assert "daten.json" in namen

                manifest = json.loads(zf.read("manifest.json"))
                assert manifest["formatVersion"] == 1
                assert manifest["name"] == "Mein Bündel"
                assert manifest["beschreibung"] == "Testbeschreibung"
                assert manifest["tags"] == ["test", "cyberpunk"]
                assert manifest["herkunftCampaignId"] == cid
                assert manifest["herkunftCampaignName"] == "Buendel-Test"
                assert manifest["anzahlKnoten"] == 1
                assert manifest["anzahlProTyp"] == {"Ort": 1}
                assert "exportedAt" in manifest

                daten = json.loads(zf.read("daten.json"))
                assert len(daten["nodes"]) == 1
                node = daten["nodes"][0]
                assert node["id"] == ort["id"]
                assert node["props"]["stammtVonId"] == ort["id"]
        finally:
            await _aufraeumen(cid)

    _run(lauf())
