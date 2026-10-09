"""Spieler-Lexikon: Erreichbarkeits-BFS (reine Funktion, konstruierte
Graphen) + Integrationstest der echten Entdeckungs-Kette gegen Neo4j.

Siehe docs/wiki/entities/spieler-lexikon.md für die Design-Begründung.
"""

import asyncio
import uuid

from app.db.neo4j_driver import get_driver
from app.entities import repository as entities_repository
from app.entities.repository import GEWAECHS_FIELDS, ORT_FIELDS, PERSON_FIELDS
from app.lexikon import repository as lexikon_repository


def _run(coro):
    return asyncio.run(coro)


# --- Reine BFS-Logik, ohne DB ----------------------------------------------


def _knoten(id_, label, sichtbarkeit="ALLE", sichtbar_fuer=None):
    return {"id": id_, "label": label, "sichtbarkeit": sichtbarkeit, "sichtbarFuer": sichtbar_fuer or []}


def _kante(von, zu, typ, sichtbarkeit="ALLE", sichtbar_fuer=None):
    return {"von": von, "zu": zu, "typ": typ, "sichtbarkeit": sichtbarkeit, "sichtbarFuer": sichtbar_fuer or []}


def test_erreicht_direkt_verbundenen_ort():
    knoten = {
        "pc": _knoten("pc", "Person"),
        "ort": _knoten("ort", "Ort"),
    }
    kanten = [_kante("pc", "ort", "VERBINDUNG")]
    erreichbar = lexikon_repository.erreichbare_ids("pc", knoten, kanten, "pc")
    assert erreichbar == {"ort"}


def test_party_ist_reiner_durchgang_und_selbst_nicht_entdeckt():
    knoten = {
        "pc": _knoten("pc", "Person"),
        "party": _knoten("party", "Party"),
        "ort": _knoten("ort", "Ort"),
    }
    kanten = [
        _kante("pc", "party", "MITGLIED_VON"),
        _kante("party", "ort", "BEFINDET_SICH_AN"),
    ]
    erreichbar = lexikon_repository.erreichbare_ids("pc", knoten, kanten, "pc")
    assert erreichbar == {"ort"}  # party selbst taucht nicht auf


def test_sl_geheime_verbindung_blockiert_komplett():
    """Eine SL-geheime VERBINDUNG darf nichts dahinter aufdecken, auch wenn
    es innerhalb der maximalen Tiefe läge."""
    knoten = {
        "pc": _knoten("pc", "Person"),
        "npc": _knoten("npc", "Fraktion"),
        "schatz": _knoten("schatz", "Gegenstand", ), 
    }
    knoten["schatz"]["storyRelevant"] = True
    kanten = [
        _kante("pc", "npc", "VERBINDUNG", sichtbarkeit="GM"),
        _kante("npc", "schatz", "VERBINDUNG"),
    ]
    erreichbar = lexikon_repository.erreichbare_ids("pc", knoten, kanten, "pc")
    assert erreichbar == set()


def test_nicht_sichtbarer_knoten_blockiert_traversierung_dahinter():
    knoten = {
        "pc": _knoten("pc", "Person"),
        "geheimer_ort": _knoten("geheimer_ort", "Ort", sichtbarkeit="GM"),
        "dahinter": _knoten("dahinter", "Ort"),
    }
    kanten = [
        _kante("pc", "geheimer_ort", "VERBINDUNG"),
        _kante("geheimer_ort", "dahinter", "VERBINDUNG"),
    ]
    erreichbar = lexikon_repository.erreichbare_ids("pc", knoten, kanten, "pc")
    assert erreichbar == set()


def test_siebte_station_noch_erreichbar_achte_nicht():
    """Marks Beispielkette: PC->Party->Event->Ort->NPCParty->NPC->MacGuffin
    (6 Kanten, MacGuffin bei Tiefe 6) muss noch vollständig durchkommen —
    MAX_TIEFE=7 ist bewusst grosszügiger als die 6 Kanten der Beispielkette."""
    knoten = {
        "pc": _knoten("pc", "Person"),
        "party1": _knoten("party1", "Party"),
        "event": _knoten("event", "Event"),
        "ort": _knoten("ort", "Ort"),
        "party2": _knoten("party2", "Party"),
        "npc": _knoten("npc", "Person"),
        "macguffin": _knoten("macguffin", "Gegenstand"),
    }
    knoten["npc"]["istCritter"] = True  # zaehlt als Fauna-Eintrag
    knoten["macguffin"]["storyRelevant"] = True
    kanten = [
        _kante("pc", "party1", "MITGLIED_VON"),
        _kante("party1", "event", "BEFINDET_SICH_AN"),
        _kante("event", "ort", "VERBINDUNG"),
        _kante("ort", "party2", "BEFINDET_SICH_AN"),
        _kante("party2", "npc", "MITGLIED_VON"),
        _kante("npc", "macguffin", "BESITZT"),
    ]
    erreichbar = lexikon_repository.erreichbare_ids("pc", knoten, kanten, "pc", max_tiefe=7)
    assert erreichbar == {"event", "ort", "npc", "macguffin"}

    # Tiefe 7 (ein Hop mehr als macguffin) liegt noch innerhalb von max_tiefe=7.
    knoten["siebte_tiefe"] = _knoten("siebte_tiefe", "Ort")
    kanten.append(_kante("macguffin", "siebte_tiefe", "VERBINDUNG"))
    # Tiefe 8 (noch ein Hop mehr) liegt klar ausserhalb.
    knoten["zu_weit"] = _knoten("zu_weit", "Ort")
    kanten.append(_kante("siebte_tiefe", "zu_weit", "VERBINDUNG"))

    erreichbar_begrenzt = lexikon_repository.erreichbare_ids("pc", knoten, kanten, "pc", max_tiefe=7)
    assert "siebte_tiefe" in erreichbar_begrenzt
    assert "zu_weit" not in erreichbar_begrenzt


def test_nicht_story_relevanter_gegenstand_zaehlt_nicht_als_entdeckt():
    knoten = {
        "pc": _knoten("pc", "Person"),
        "pistole": _knoten("pistole", "Gegenstand"),
    }
    knoten["pistole"]["storyRelevant"] = False
    kanten = [_kante("pc", "pistole", "BESITZT")]
    erreichbar = lexikon_repository.erreichbare_ids("pc", knoten, kanten, "pc")
    assert erreichbar == set()  # erreichbar fuer die Traversierung, aber kein Lexikon-Eintrag


def test_spezifisch_sichtbare_verbindung_nur_fuer_berechtigten_pc():
    knoten = {
        "pc1": _knoten("pc1", "Person"),
        "pc2": _knoten("pc2", "Person"),
        "ort": _knoten("ort", "Ort"),
    }
    kanten = [_kante("pc1", "ort", "VERBINDUNG", sichtbarkeit="SPEZIFISCH", sichtbar_fuer=["pc1"])]
    assert lexikon_repository.erreichbare_ids("pc1", knoten, kanten, "pc1") == {"ort"}
    assert lexikon_repository.erreichbare_ids("pc1", knoten, kanten, "pc2") == set()


# --- Integrationstest gegen echtes Neo4j -----------------------------------


async def _kampagne_anlegen() -> str:
    cid = f"test-lexikon-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'Lexikon-Test'})", cid=cid)
    return cid


async def _aufraeumen(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


async def _pc_anlegen(cid: str, name: str) -> dict:
    daten = {f: None for f in PERSON_FIELDS}
    daten.update({
        "name": name, "personType": "PC", "description": "", "notes": "",
        "bildUrl": "", "bilder": [], "istEntwurf": False, "istCritter": False, "istKI": False,
        "istHaendler": False, "istPflanzenCritter": False, "istVorgefertigt": False,
        "spezialisierung": [], "vertriebsart": "PHYSISCH", "shopHintergrundUrl": "",
        "weg": "KEINER", "magieFlavor": "MAGIER", "rasse": "",
        "schadenSchlag": 0, "schadenSchwer": 0, "schadenAggraviert": 0, "willenskraftVerbraucht": 0,
        "iceSchaden": 0, "erfahrung": 0, "erfahrungAusgegeben": 0, "extraEP": 0, "willenskraftBonus": 0,
        "konzept": "", "alter": "", "ambition": "", "verlangen": "", "ziel": "", "kapital": 0, "schulden": 0,
        "alias": "", "erstellungAbgeschlossen": False, "silhouette": "maennlich", "erstelltAm": "",
        "sichtbarkeit": "ALLE", "sichtbarFuer": [], "notizenSichtbarkeit": "GM", "notizenSichtbarFuer": [],
    })
    return await entities_repository.create_node("Person", PERSON_FIELDS, cid, daten)


async def _ort_anlegen(cid: str, name: str, sichtbarkeit="ALLE") -> dict:
    return await entities_repository.create_node(
        "Ort", ORT_FIELDS, cid,
        {
            "name": name, "description": "", "notes": "", "bildUrl": "", "bilder": [],
            "istEntwurf": False, "istShop": False, "spezialisierung": [], "vertriebsart": "PHYSISCH",
            "shopHintergrundUrl": "", "spotifyPlaylistUri": "", "spotifyPlaylistName": "", "spotifyPlaylistBild": "",
            "sichtbarkeit": sichtbarkeit, "sichtbarFuer": [], "notizenSichtbarkeit": "GM", "notizenSichtbarFuer": [],
        },
    )


async def _gewaechs_anlegen(cid: str, name: str, sichtbarkeit="ALLE") -> dict:
    return await entities_repository.create_node(
        "Gewaechs", GEWAECHS_FIELDS, cid,
        {
            "name": name, "description": "", "notes": "", "bildUrl": "", "bilder": [], "istEntwurf": False,
            "giftig": False, "essbar": False, "gefaehrlichkeit": "", "eigenschaften": "",
            "sichtbarkeit": sichtbarkeit, "sichtbarFuer": [], "notizenSichtbarkeit": "GM", "notizenSichtbarFuer": [],
        },
    )


async def _party_anlegen(cid: str, name: str) -> str:
    driver = get_driver()
    pid = str(uuid.uuid4())
    async with driver.session() as session:
        await session.run(
            """
            MATCH (c:Campaign {id: $cid})
            CREATE (party:Party {id: $pid, campaignId: $cid, name: $name, aktiv: false,
                                  sichtbarkeit: 'GM', sichtbarFuer: []})
            CREATE (c)-[:HAT_ENTITAET]->(party)
            """,
            cid=cid, pid=pid, name=name,
        )
    return pid


async def _mitglied(cid: str, party_id: str, person_id: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (party:Party {id: $party_id, campaignId: $cid})
            MATCH (p:Person {id: $person_id, campaignId: $cid})
            CREATE (p)-[:MITGLIED_VON]->(party)
            """,
            cid=cid, party_id=party_id, person_id=person_id,
        )


async def _aufenthaltsort(cid: str, party_id: str, ort_id: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (party:Party {id: $party_id, campaignId: $cid})
            MATCH (o:Ort {id: $ort_id, campaignId: $cid})
            CREATE (party)-[:BEFINDET_SICH_AN]->(o)
            """,
            cid=cid, party_id=party_id, ort_id=ort_id,
        )


def test_integration_pc_entdeckt_ort_ueber_party():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await _pc_anlegen(cid, "Runner")
            ort = await _ort_anlegen(cid, "Unterschlupf")
            party_id = await _party_anlegen(cid, "Team A")
            await _mitglied(cid, party_id, pc["id"])
            await _aufenthaltsort(cid, party_id, ort["id"])

            anzahl = await lexikon_repository.neu_berechnen_fuer_person(cid, pc["id"])
            assert anzahl == 1

            eintraege = await lexikon_repository.entdeckte_eintraege(cid, pc["id"])
            assert len(eintraege) == 1
            assert eintraege[0]["id"] == ort["id"]
            assert eintraege[0]["kategorie"] == "welt"
            assert eintraege[0]["naehe"] == 0  # aktueller Aufenthaltsort selbst
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_integration_sl_geheimer_ort_wird_nicht_entdeckt():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await _pc_anlegen(cid, "Runner")
            ort = await _ort_anlegen(cid, "Geheimversteck", sichtbarkeit="GM")
            party_id = await _party_anlegen(cid, "Team A")
            await _mitglied(cid, party_id, pc["id"])
            await _aufenthaltsort(cid, party_id, ort["id"])

            anzahl = await lexikon_repository.neu_berechnen_fuer_person(cid, pc["id"])
            assert anzahl == 0
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_integration_favorisieren_nur_fuer_entdecktes():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pc = await _pc_anlegen(cid, "Runner")
            ort = await _ort_anlegen(cid, "Markt")
            fremder_ort = await _ort_anlegen(cid, "Unbekannt")
            party_id = await _party_anlegen(cid, "Team A")
            await _mitglied(cid, party_id, pc["id"])
            await _aufenthaltsort(cid, party_id, ort["id"])
            await lexikon_repository.neu_berechnen_fuer_person(cid, pc["id"])

            assert await lexikon_repository.favorisieren(cid, pc["id"], ort["id"]) is True
            assert await lexikon_repository.favorisieren(cid, pc["id"], fremder_ort["id"]) is False

            eintraege = await lexikon_repository.entdeckte_eintraege(cid, pc["id"])
            assert eintraege[0]["favorisiert"] is True
        finally:
            await _aufraeumen(cid)

    _run(lauf())
