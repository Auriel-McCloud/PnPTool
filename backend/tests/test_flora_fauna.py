"""Flora & Fauna: LEBT_IN (many-to-many Ort <-> Critter/Gewaechs) und das
generische Gewaechs-CRUD.

Echte-Neo4j-Integrationstests nach demselben Muster wie test_shop_am_ort.py.
"""

import asyncio
import uuid

from app.db.neo4j_driver import get_driver
from app.entities import repository
from app.entities.repository import GEWAECHS_FIELDS, ORT_FIELDS, PERSON_FIELDS


def _run(coro):
    return asyncio.run(coro)


async def _kampagne_anlegen() -> str:
    cid = f"test-flora-fauna-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'Flora-Fauna-Test'})", cid=cid)
    return cid


async def _aufraeumen(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


async def _ort_anlegen(cid: str, name: str) -> dict:
    return await repository.create_node(
        "Ort", ORT_FIELDS, cid,
        {
            "name": name, "description": "", "notes": "", "bildUrl": "", "bilder": [],
            "istEntwurf": False, "istShop": False, "spezialisierung": [], "vertriebsart": "PHYSISCH",
            "shopHintergrundUrl": "", "spotifyPlaylistUri": "", "spotifyPlaylistName": "", "spotifyPlaylistBild": "",
            "sichtbarkeit": "GM", "sichtbarFuer": [], "notizenSichtbarkeit": "GM", "notizenSichtbarFuer": [],
        },
    )


async def _critter_anlegen(cid: str, name: str) -> dict:
    daten = {f: None for f in PERSON_FIELDS}
    daten.update({
        "name": name, "personType": "NPC", "description": "", "notes": "",
        "bildUrl": "", "bilder": [], "istEntwurf": False, "istCritter": True, "istKI": False,
        "istHaendler": False, "istPflanzenCritter": False, "spezialisierung": [], "vertriebsart": "PHYSISCH",
        "shopHintergrundUrl": "", "weg": "KEINER", "magieFlavor": "MAGIER", "rasse": "",
        "schadenSchlag": 0, "schadenSchwer": 0, "schadenAggraviert": 0, "willenskraftVerbraucht": 0,
        "iceSchaden": 0, "erfahrung": 0, "erfahrungAusgegeben": 0, "extraEP": 0, "willenskraftBonus": 0,
        "konzept": "", "alter": "", "ambition": "", "verlangen": "", "ziel": "", "kapital": 0, "schulden": 0,
        "alias": "", "erstellungAbgeschlossen": False, "silhouette": "maennlich", "erstelltAm": "",
        "sichtbarkeit": "GM", "sichtbarFuer": [], "notizenSichtbarkeit": "GM", "notizenSichtbarFuer": [],
    })
    return await repository.create_node("Person", PERSON_FIELDS, cid, daten)


async def _gewaechs_anlegen(cid: str, name: str) -> dict:
    return await repository.create_node(
        "Gewaechs", GEWAECHS_FIELDS, cid,
        {
            "name": name, "description": "", "notes": "", "bildUrl": "", "bilder": [], "istEntwurf": False,
            "giftig": True, "essbar": False, "gefaehrlichkeit": "reizend", "eigenschaften": "leuchtet im Dunkeln",
            "sichtbarkeit": "GM", "sichtbarFuer": [], "notizenSichtbarkeit": "GM", "notizenSichtbarFuer": [],
        },
    )


def test_gewaechs_create_und_liste():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            g = await _gewaechs_anlegen(cid, "Dornranke")
            assert g["name"] == "Dornranke"
            assert g["giftig"] is True
            assert g["essbar"] is False
            assert g["notes"] == ""
            assert g["sichtbarkeit"] == "GM"

            liste = await repository.list_nodes("Gewaechs", GEWAECHS_FIELDS, cid)
            assert len(liste) == 1
            assert liste[0]["id"] == g["id"]
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_lebt_in_many_to_many_critter_und_gewaechs():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            ort_a = await _ort_anlegen(cid, "Slum-Park")
            ort_b = await _ort_anlegen(cid, "Hafenufer")
            critter = await _critter_anlegen(cid, "Streunerkatze")
            gewaechs = await _gewaechs_anlegen(cid, "Dornranke")

            # Dieselbe Spezies an ZWEI Orten — vorher gab es nur die
            # exklusive BEFINDET_SICH_AN-Logik, die das nicht erlaubt hätte.
            assert await repository.lebt_in_hinzufuegen(cid, ort_a["id"], critter["id"])
            assert await repository.lebt_in_hinzufuegen(cid, ort_b["id"], critter["id"])
            assert await repository.lebt_in_hinzufuegen(cid, ort_a["id"], gewaechs["id"])

            liste_a = await repository.lebt_in_liste_fuer_ort(cid, ort_a["id"])
            kinds_a = sorted((e["kind"], e["name"]) for e in liste_a)
            assert kinds_a == [("Gewaechs", "Dornranke"), ("Person", "Streunerkatze")]

            liste_b = await repository.lebt_in_liste_fuer_ort(cid, ort_b["id"])
            assert [e["name"] for e in liste_b] == ["Streunerkatze"]

            # Reverse-Lookup: der Critter lebt an beiden Orten.
            orte_des_critters = await repository.lebt_in_liste_fuer_art(cid, critter["id"])
            assert sorted(o["name"] for o in orte_des_critters) == ["Hafenufer", "Slum-Park"]

            # Idempotent: ein zweites Hinzufügen legt keine Doppel-Kante an.
            assert await repository.lebt_in_hinzufuegen(cid, ort_a["id"], critter["id"])
            liste_a_erneut = await repository.lebt_in_liste_fuer_ort(cid, ort_a["id"])
            assert len(liste_a_erneut) == 2

            # Entfernen bei Ort A lässt Ort B unberührt (vorher: BEFINDET_SICH_AN
            # hätte die alte Kante beim Hinzufügen der neuen schon gelöscht).
            assert await repository.lebt_in_entfernen(cid, ort_a["id"], critter["id"])
            liste_a_danach = await repository.lebt_in_liste_fuer_ort(cid, ort_a["id"])
            assert [e["name"] for e in liste_a_danach] == ["Dornranke"]
            liste_b_danach = await repository.lebt_in_liste_fuer_ort(cid, ort_b["id"])
            assert [e["name"] for e in liste_b_danach] == ["Streunerkatze"]
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_lebt_in_lehnt_gewoehnliche_person_ab():
    """Nur Critter (istCritter=true) oder Gewaechs dürfen LEBT_IN bekommen —
    ein gewöhnlicher NPC/PC nicht (sonst "Mensch wohnt im Zoo" aus Versehen)."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            ort = await _ort_anlegen(cid, "Marktplatz")
            normale_person = await _critter_anlegen(cid, "Kein Critter")
            await repository.update_node("Person", PERSON_FIELDS, cid, normale_person["id"], {"istCritter": False})

            ok = await repository.lebt_in_hinzufuegen(cid, ort["id"], normale_person["id"])
            assert ok is False
            liste = await repository.lebt_in_liste_fuer_ort(cid, ort["id"])
            assert liste == []
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_lebt_in_unbekannte_ids_melden_false():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            ort = await _ort_anlegen(cid, "Niemandsland")
            assert await repository.lebt_in_hinzufuegen(cid, ort["id"], str(uuid.uuid4())) is False
            assert await repository.lebt_in_hinzufuegen(cid, str(uuid.uuid4()), str(uuid.uuid4())) is False
            assert await repository.lebt_in_entfernen(cid, ort["id"], str(uuid.uuid4())) is False
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_export_weissliste_kennt_gewaechs_und_lebt_in():
    from app.campaigns.export_import import KNOWN_LABELS, KNOWN_REL_TYPES

    assert "Gewaechs" in KNOWN_LABELS
    assert "LEBT_IN" in KNOWN_REL_TYPES


def test_gewaechs_felder_vollstaendig_im_rueckgabe_dict():
    """Dieselbe Prüfung wie test_bogenfeld_defaults.py — prüft, dass eine
    generische Liste nicht an einem fehlenden Gewaechs-Feld scheitert."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            await _gewaechs_anlegen(cid, "Vollständigkeitstest")
            liste = await repository.list_nodes("Gewaechs", GEWAECHS_FIELDS, cid)
            assert len(liste) == 1
            for feld in GEWAECHS_FIELDS:
                assert feld in liste[0], f"Feld fehlt im Gewaechs-Rückgabe-Dict: {feld}"
        finally:
            await _aufraeumen(cid)

    _run(lauf())
