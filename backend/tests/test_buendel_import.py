"""Tests für das Kampagnen-Bündel-Feature (Phase 2: Import).

Gleiches Muster wie test_buendel_export.py: echte Neo4j-Integration, reine
asyncio.run()-Aufrufe gegen Repository-/Export-/Import-Funktionen, keine
HTTP-Schicht. Export via `export_buendel_zip` erzeugt das echte ZIP, das dann
in eine zweite (oder dieselbe) Zielkampagne importiert wird — so testet das
genau den Pfad, den ein echter GM durchläuft.
"""

import asyncio
import uuid

from app.achievements import repository as achievements_repo
from app.campaigns.buendel_export import export_buendel_zip
from app.campaigns.buendel_import import import_buendel_zip, preview_buendel_zip
from app.db.neo4j_driver import get_driver
from app.entities import repository as entities_repo
from app.entities.schemas import FraktionCreate, OrtCreate, PersonCreate
from app.items import repository as items_repo
from app.rassen import repository as rassen_repo
from app.wiki import repository as wiki_repo


def _run(coro):
    return asyncio.run(coro)


async def _kampagne_anlegen(name: str = "Buendel-Import-Test") -> str:
    cid = f"test-buendel-import-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: $name})", cid=cid, name=name)
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


async def _gegenstand(cid: str, owner_id, name: str, **overrides) -> dict:
    basis = {
        "name": name, "description": "", "notes": "", "typ": "Waffe", "preis": 10,
        "kraft": 0, "eigenschaften": {}, "storyRelevant": False, "einzigartig": True,
        "hatMenge": False, "menge": 1, "istVorlage": False, "seltenheit": 1,
        "automatischImShop": False, "sichtbarkeit": "GM", "sichtbarFuer": [],
    }
    basis.update(overrides)
    return await items_repo.create_gegenstand(cid, owner_id, basis)


async def _count_nodes(cid: str, label: str) -> int:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(f"MATCH (n:{label} {{campaignId: $cid}}) RETURN count(n) AS n", cid=cid)
        record = await result.single()
        return int(record["n"])


async def _rasse_aufraeumen(rasse_id: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (r:Rasse {id: $id}) DETACH DELETE r", id=rasse_id)


def test_import_in_leere_zielkampagne_alles_neu():
    """(a) im Aufgabentext: Export aus A, Import in leeres B -> alles neu."""
    async def lauf():
        a = await _kampagne_anlegen("Quelle-A")
        b = await _kampagne_anlegen("Ziel-B")
        try:
            ort = await _ort(a, "Hafenviertel")
            npc = await _person(a, "Fixer Joe", personType="NPC")
            await _gegenstand(a, npc["id"], "Katana")

            inhalt, _ = await export_buendel_zip(a, name="Starterpaket", exclude_ids=[])

            ergebnis = await import_buendel_zip(b, inhalt, modus="ueberspringen", ideenschmiede=False)

            assert ergebnis["neu"] == 3
            assert ergebnis["aktualisiert"] == 0
            assert ergebnis["uebersprungen"] == 0
            assert ergebnis["proTyp"]["Ort"] == {"neu": 1, "aktualisiert": 0, "uebersprungen": 0}
            assert ergebnis["proTyp"]["Person"]["neu"] == 1
            assert ergebnis["proTyp"]["Gegenstand"]["neu"] == 1

            # In B existieren jetzt eigene Knoten mit NEUEN ids, aber derselben stammtVonId.
            assert await _count_nodes(b, "Ort") == 1
            assert await _count_nodes(b, "Person") == 1
            assert await _count_nodes(b, "Gegenstand") == 1
            # A bleibt unangetastet.
            assert await _count_nodes(a, "Ort") == 1

            driver = get_driver()
            async with driver.session() as session:
                result = await session.run(
                    "MATCH (o:Ort {campaignId: $cid}) RETURN o.id AS id, o.stammtVonId AS svid", cid=b
                )
                rec = await result.single()
                assert rec["id"] != ort["id"]
                assert rec["svid"] == ort["id"]
        finally:
            await _aufraeumen(a)
            await _aufraeumen(b)

    _run(lauf())


def test_import_rasse_neu_dann_global_wiedergefunden_statt_dupliziert():
    """Rasse ist campaign-SCOPELESS (geteilter Katalog) — eine Rasse zählt nur
    dann als 'neu', wenn die Ziel-DB sie wirklich noch nie gesehen hat (hier
    simuliert, indem das Original nach dem Export gelöscht wird: innerhalb
    EINER DB existiert eine gerade exportierte Rasse sonst immer schon,
    nämlich als das Original selbst). Ein zweiter Import in eine weitere
    Kampagne muss die neu angelegte Rasse wiederfinden, nicht duplizieren."""
    async def lauf():
        a = await _kampagne_anlegen("Quelle-Rasse-A")
        b = await _kampagne_anlegen("Ziel-Rasse-B")
        c = await _kampagne_anlegen("Ziel-Rasse-C")
        rasse = await rassen_repo.anlegen({"name": f"Katzenvolk-{uuid.uuid4()}"})
        driver = get_driver()
        async with driver.session() as session:
            await session.run(
                "MATCH (c:Campaign {id: $cid}), (r:Rasse {id: $rid}) MERGE (c)-[:ERLAUBT_RASSE]->(r)",
                cid=a, rid=rasse["id"],
            )
        try:
            inhalt, _ = await export_buendel_zip(a, name="Rassenpaket", exclude_ids=[])

            # Original aus der DB entfernen: simuliert eine Ziel-Installation,
            # die diese Rasse (z.B. aus einem GitHub-Bündel) noch nie gesehen hat.
            await _rasse_aufraeumen(rasse["id"])

            ergebnis = await import_buendel_zip(b, inhalt, modus="ueberspringen", ideenschmiede=False)
            assert ergebnis["neu"] == 1
            assert ergebnis["proTyp"]["Rasse"]["neu"] == 1

            async with driver.session() as session:
                result = await session.run(
                    "MATCH (c:Campaign {id: $cid})-[:ERLAUBT_RASSE]->(r:Rasse {stammtVonId: $svid}) RETURN r.id AS id",
                    cid=b, svid=rasse["id"],
                )
                rec = await result.single()
                assert rec is not None
                neue_rasse_id = rec["id"]

            # Re-Import derselben Rasse in eine DRITTE Kampagne findet dieselbe
            # (campaign-unabhängige) Rasse wieder statt sie zu duplizieren.
            ergebnis2 = await import_buendel_zip(c, inhalt, modus="ueberspringen", ideenschmiede=False)
            assert ergebnis2["proTyp"]["Rasse"] == {"neu": 0, "aktualisiert": 0, "uebersprungen": 1}
            async with driver.session() as session:
                result = await session.run(
                    "MATCH (:Campaign {id: $cid})-[:ERLAUBT_RASSE]->(r:Rasse {id: $rid}) RETURN count(r) AS n",
                    cid=c, rid=neue_rasse_id,
                )
                rec = await result.single()
                assert rec["n"] == 1
            async with driver.session() as session:
                result = await session.run("MATCH (r:Rasse {stammtVonId: $svid}) RETURN count(r) AS n", svid=rasse["id"])
                rec = await result.single()
                assert rec["n"] == 1  # keine Dopplung über die drei Kampagnen hinweg

            await _rasse_aufraeumen(neue_rasse_id)
        finally:
            await _aufraeumen(a)
            await _aufraeumen(b)
            await _aufraeumen(c)

    _run(lauf())


def test_import_ueberspringen_zweiter_lauf_erzeugt_keine_duplikate():
    """(c) im Aufgabentext: derselbe Bündel-Re-Import mit 'ueberspringen'
    darf nichts verdoppeln und nichts ändern."""
    async def lauf():
        a = await _kampagne_anlegen("Quelle-Skip-A")
        b = await _kampagne_anlegen("Ziel-Skip-B")
        try:
            await _ort(a, "Slum")
            await _fraktion(a, "Zaibatsu")
            inhalt, _ = await export_buendel_zip(a, name="Skip-Test", exclude_ids=[])

            erster = await import_buendel_zip(b, inhalt, modus="ueberspringen", ideenschmiede=False)
            assert erster["neu"] == 2

            vor_ort = await _count_nodes(b, "Ort")
            vor_fraktion = await _count_nodes(b, "Fraktion")

            zweiter = await import_buendel_zip(b, inhalt, modus="ueberspringen", ideenschmiede=False)
            assert zweiter["neu"] == 0
            assert zweiter["aktualisiert"] == 0
            assert zweiter["uebersprungen"] == 2

            assert await _count_nodes(b, "Ort") == vor_ort
            assert await _count_nodes(b, "Fraktion") == vor_fraktion
        finally:
            await _aufraeumen(a)
            await _aufraeumen(b)

    _run(lauf())


def test_import_aktualisieren_sichert_lokale_aenderung_in_papierkorb():
    """(d) im Aufgabentext: lokale Bearbeitung in B, dann Re-Import mit
    'aktualisieren' -> lokale Änderung landet unverändert im Papierkorb
    (geloescht=true), der Live-Knoten zeigt wieder den Bündel-Stand."""
    async def lauf():
        a = await _kampagne_anlegen("Quelle-Update-A")
        b = await _kampagne_anlegen("Ziel-Update-B")
        try:
            await _ort(a, "Industriezone", description="Rauchige Fabriken.")
            inhalt, _ = await export_buendel_zip(a, name="Update-Test", exclude_ids=[])

            await import_buendel_zip(b, inhalt, modus="ueberspringen", ideenschmiede=False)

            # Lokale Bearbeitung in B.
            driver = get_driver()
            async with driver.session() as session:
                result = await session.run(
                    "MATCH (o:Ort {campaignId: $cid}) RETURN o.id AS id", cid=b
                )
                rec = await result.single()
                ort_id_in_b = rec["id"]
            bearbeitet = await entities_repo.update_node(
                "Ort", entities_repo.ORT_FIELDS, b, ort_id_in_b,
                {"description": "GM hat das vor Ort geändert: jetzt verlassen."},
            )
            assert bearbeitet["description"] == "GM hat das vor Ort geändert: jetzt verlassen."

            ergebnis = await import_buendel_zip(b, inhalt, modus="aktualisieren", ideenschmiede=False)
            assert ergebnis["neu"] == 0
            assert ergebnis["aktualisiert"] == 1
            assert ergebnis["uebersprungen"] == 0

            # Live-Knoten zeigt wieder den Bündel-Stand, id/stammtVonId unverändert.
            frisch = await entities_repo.get_node("Ort", entities_repo.ORT_FIELDS, b, ort_id_in_b)
            assert frisch is not None
            assert frisch["description"] == "Rauchige Fabriken."
            assert frisch["id"] == ort_id_in_b

            # Die lokale Änderung liegt unverändert im Papierkorb.
            async with driver.session() as session:
                result = await session.run(
                    "MATCH (o:Ort {campaignId: $cid}) WHERE coalesce(o.geloescht, false) "
                    "RETURN o.description AS description, o.id AS id",
                    cid=b,
                )
                papierkorb = [dict(r) async for r in result]
            assert len(papierkorb) == 1
            assert papierkorb[0]["description"] == "GM hat das vor Ort geändert: jetzt verlassen."
            assert papierkorb[0]["id"] != ort_id_in_b
        finally:
            await _aufraeumen(a)
            await _aufraeumen(b)

    _run(lauf())


def test_istentwurf_toggle_gilt_nur_fuer_neuanlagen():
    async def lauf():
        a = await _kampagne_anlegen("Quelle-Entwurf-A")
        b = await _kampagne_anlegen("Ziel-Entwurf-B")
        try:
            await _ort(a, "Geheimlabor")
            inhalt, _ = await export_buendel_zip(a, name="Entwurf-Test", exclude_ids=[])

            await import_buendel_zip(b, inhalt, modus="ueberspringen", ideenschmiede=True)
            orte = await entities_repo.list_nodes("Ort", entities_repo.ORT_FIELDS, b)
            # list_nodes blendet nichts nach istEntwurf aus, Eintrag muss da sein.
            assert len(orte) == 1
            assert orte[0]["istEntwurf"] is True

            # Lokal auf "live" zurückstellen, um zu prüfen, dass ein Update
            # istEntwurf NICHT anfasst (Modul-Docstring: Update ist kein neuer Entwurf).
            await entities_repo.update_node(
                "Ort", entities_repo.ORT_FIELDS, b, orte[0]["id"], {"istEntwurf": False}
            )
            await import_buendel_zip(b, inhalt, modus="aktualisieren", ideenschmiede=True)
            frisch = await entities_repo.get_node("Ort", entities_repo.ORT_FIELDS, b, orte[0]["id"])
            assert frisch["istEntwurf"] is False
        finally:
            await _aufraeumen(a)
            await _aufraeumen(b)

    _run(lauf())


def test_validierung_lehnt_unbekanntes_label_ab():
    async def lauf():
        b = await _kampagne_anlegen("Ziel-Validierung-B")
        try:
            import io
            import json
            import zipfile

            puffer = io.BytesIO()
            with zipfile.ZipFile(puffer, "w") as zf:
                zf.writestr(
                    "manifest.json",
                    json.dumps({"formatVersion": 1, "herkunftCampaignId": "x", "name": "Böse"}),
                )
                zf.writestr(
                    "daten.json",
                    json.dumps({
                        "nodes": [
                            {"id": "n1", "labels": ["GMUser"], "props": {"stammtVonId": "n1", "name": "Hack"}}
                        ],
                        "edges": [],
                    }),
                )
            try:
                await import_buendel_zip(b, puffer.getvalue(), modus="ueberspringen", ideenschmiede=False)
                assert False, "haette ValueError werfen muessen"
            except ValueError as exc:
                assert "Label" in str(exc)

            # Node ganz ohne stammtVonId muss ebenfalls abgelehnt werden.
            puffer2 = io.BytesIO()
            with zipfile.ZipFile(puffer2, "w") as zf:
                zf.writestr(
                    "manifest.json",
                    json.dumps({"formatVersion": 1, "herkunftCampaignId": "x", "name": "Ohne-Stamm"}),
                )
                zf.writestr(
                    "daten.json",
                    json.dumps({
                        "nodes": [{"id": "n1", "labels": ["Ort"], "props": {"name": "Spukhaus"}}],
                        "edges": [],
                    }),
                )
            try:
                await import_buendel_zip(b, puffer2.getvalue(), modus="ueberspringen", ideenschmiede=False)
                assert False, "haette ValueError werfen muessen"
            except ValueError as exc:
                assert "stammtVonId" in str(exc)
        finally:
            await _aufraeumen(b)

    _run(lauf())


def test_preview_zaehlt_neu_vs_vorhanden_ohne_zu_schreiben():
    async def lauf():
        a = await _kampagne_anlegen("Quelle-Preview-A")
        b = await _kampagne_anlegen("Ziel-Preview-B")
        try:
            await _ort(a, "Vorschauplatz")
            inhalt, _ = await export_buendel_zip(a, name="Preview-Test", exclude_ids=[])

            vorschau1 = await preview_buendel_zip(b, inhalt)
            assert vorschau1["proTyp"]["Ort"] == {"neu": 1, "vorhanden": 0}
            assert await _count_nodes(b, "Ort") == 0  # nichts geschrieben

            await import_buendel_zip(b, inhalt, modus="ueberspringen", ideenschmiede=False)
            vorschau2 = await preview_buendel_zip(b, inhalt)
            assert vorschau2["proTyp"]["Ort"] == {"neu": 0, "vorhanden": 1}
        finally:
            await _aufraeumen(a)
            await _aufraeumen(b)

    _run(lauf())
