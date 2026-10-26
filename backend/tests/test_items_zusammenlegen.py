"""Zusammenlegen (26.10.2026): mehrere gleichwertige Gegenstände zu einem
Stapel zusammenführen — siehe docs/wiki/entities/gegenstand-stapel.md.

`stapel_gleich` ist reine Vergleichslogik (kein DB-Zugriff nötig).
`zusammenlegen`/`stapelkandidaten` brauchen echte Neo4j-Daten, weil sie über
`create_gegenstand`/`get_owner_person_id` laufen — Testaufbau nach dem Muster
von test_shop_am_ort.py (eigene Wegwerf-Kampagne, DETACH DELETE im finally).
"""

import asyncio
import uuid

import pytest
from app.db.neo4j_driver import close_driver, get_driver
from app.items import repository


def _run(coro):
    # Jeder Test bekommt seine eigene asyncio-Eventloop (asyncio.run) — der
    # globale Neo4j-Driver muss danach geschlossen werden, sonst stirbt der
    # nächste Test am toten Transport des vorigen ("attached to a different
    # loop"), siehe references/live-daten-debugging.md.
    async def mit_cleanup():
        try:
            return await coro
        finally:
            await close_driver()

    return asyncio.run(mit_cleanup())


# ---------------------------------------------------------------------------
# stapel_gleich: reine Funktion, keine Datenbank nötig.
# ---------------------------------------------------------------------------


def _basis(**overrides) -> dict:
    basis = {
        "id": "a",
        "name": "Maschinenteil",
        "typ": "Sonstiges",
        "preis": 50,
        "kraft": 0,
        "istMaschinenteil": True,
        "maschinenteilQualitaet": "normal",
        "menge": 1,
        "hatMenge": False,
        "einzigartig": False,
        "description": "",
        "notes": "",
        "ablage": "RUCKSACK",
        "bildUrl": "",
    }
    basis.update(overrides)
    return basis


def test_stapel_gleich_bei_identischen_mechanischen_feldern():
    a = _basis(id="a", menge=1, hatMenge=False)
    b = _basis(id="b", menge=2, hatMenge=True, description="andere Notiz")
    assert repository.stapel_gleich(a, b)


def test_stapel_gleich_erkennt_unterschiedliche_qualitaet():
    a = _basis(maschinenteilQualitaet="normal")
    b = _basis(maschinenteilQualitaet="hochwertig")
    assert not repository.stapel_gleich(a, b)


def test_stapel_gleich_erkennt_unterschiedlichen_preis():
    a = _basis(preis=50)
    b = _basis(preis=75)
    assert not repository.stapel_gleich(a, b)


def test_stapel_gleich_ignoriert_ablage_und_bild():
    a = _basis(ablage="RUCKSACK", bildUrl="/a.png")
    b = _basis(ablage="GELAGERT", bildUrl="/b.png")
    assert repository.stapel_gleich(a, b)


# ---------------------------------------------------------------------------
# zusammenlegen / stapelkandidaten: gegen die echte Dev-Neo4j.
# ---------------------------------------------------------------------------


async def _kampagne_mit_person() -> tuple[str, str]:
    cid = f"test-zusammenlegen-{uuid.uuid4()}"
    pid = str(uuid.uuid4())
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            CREATE (c:Campaign {id: $cid, name: 'Zusammenlegen-Test'})
            CREATE (p:Person {
                id: $pid, campaignId: $cid, name: 'Testperson', personType: 'PC',
                description: '', notes: '', sichtbarkeit: 'ALLE', sichtbarFuer: []
            })
            CREATE (c)-[:HAT_ENTITAET]->(p)
            """,
            cid=cid,
            pid=pid,
        )
    return cid, pid


async def _aufraeumen(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


def _maschinenteil_daten(name="Maschinenteil", qualitaet="normal", menge=1) -> dict:
    return {
        "name": name,
        "description": "",
        "notes": "",
        "typ": "Sonstiges",
        "preis": 0,
        "kraft": 0,
        "eigenschaften": {},
        "storyRelevant": False,
        "einzigartig": False,
        "hatMenge": True,
        "menge": menge,
        "istVorlage": False,
        "seltenheit": 1,
        "automatischImShop": False,
        "sichtbarkeit": "SPEZIFISCH",
        "sichtbarFuer": [],
        "istMaschinenteil": True,
        "maschinenteilQualitaet": qualitaet,
    }


def test_zusammenlegen_summiert_menge_und_wirft_quellen_weg():
    async def szenario():
        cid, pid = await _kampagne_mit_person()
        try:
            a = await repository.create_gegenstand(cid, pid, _maschinenteil_daten(menge=1))
            b = await repository.create_gegenstand(cid, pid, _maschinenteil_daten(menge=2))
            c = await repository.create_gegenstand(cid, pid, _maschinenteil_daten(menge=3))

            ergebnis = await repository.zusammenlegen(cid, a["id"], [b["id"], c["id"]], "Spielleitung")

            assert ergebnis["hatMenge"] is True
            assert ergebnis["menge"] == 6

            quelle_b = await repository.get_gegenstand(cid, b["id"])
            quelle_c = await repository.get_gegenstand(cid, c["id"])
            assert quelle_b["weggeworfen"] is True
            assert quelle_c["weggeworfen"] is True
            # Reversibel, nicht gelöscht.
            assert quelle_b["weggeworfenVon"] == "Spielleitung"
        finally:
            await _aufraeumen(cid)

    _run(szenario())


def test_zusammenlegen_lehnt_unterschiedliche_qualitaet_ab():
    async def szenario():
        cid, pid = await _kampagne_mit_person()
        try:
            a = await repository.create_gegenstand(cid, pid, _maschinenteil_daten(qualitaet="normal"))
            b = await repository.create_gegenstand(cid, pid, _maschinenteil_daten(qualitaet="hochwertig"))

            with pytest.raises(repository.UnterschiedlicherGegenstand):
                await repository.zusammenlegen(cid, a["id"], [b["id"]], "Spielleitung")

            # Nichts verändert.
            unveraendert_a = await repository.get_gegenstand(cid, a["id"])
            unveraendert_b = await repository.get_gegenstand(cid, b["id"])
            assert unveraendert_a["menge"] == 1
            assert unveraendert_b["weggeworfen"] is False
        finally:
            await _aufraeumen(cid)

    _run(szenario())


def test_zusammenlegen_lehnt_einzigartige_stuecke_ab():
    async def szenario():
        cid, pid = await _kampagne_mit_person()
        try:
            daten = _maschinenteil_daten()
            daten["einzigartig"] = True
            a = await repository.create_gegenstand(cid, pid, daten)
            b = await repository.create_gegenstand(cid, pid, _maschinenteil_daten())

            with pytest.raises(repository.NichtStapelbar):
                await repository.zusammenlegen(cid, a["id"], [b["id"]], "Spielleitung")
        finally:
            await _aufraeumen(cid)

    _run(szenario())


def test_zusammenlegen_lehnt_fremden_besitzer_ab():
    async def szenario():
        cid, pid = await _kampagne_mit_person()
        pid2 = str(uuid.uuid4())
        driver = get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (c:Campaign {id: $cid})
                CREATE (p2:Person {
                    id: $pid2, campaignId: $cid, name: 'Zweite Person', personType: 'PC',
                    description: '', notes: '', sichtbarkeit: 'ALLE', sichtbarFuer: []
                })
                CREATE (c)-[:HAT_ENTITAET]->(p2)
                """,
                cid=cid,
                pid2=pid2,
            )
        try:
            a = await repository.create_gegenstand(cid, pid, _maschinenteil_daten())
            b = await repository.create_gegenstand(cid, pid2, _maschinenteil_daten())

            with pytest.raises(repository.NichtStapelbar):
                await repository.zusammenlegen(cid, a["id"], [b["id"]], "Spielleitung")
        finally:
            await _aufraeumen(cid)

    _run(szenario())


def test_stapelkandidaten_findet_nur_gleichwertige_eigene_stuecke():
    async def szenario():
        cid, pid = await _kampagne_mit_person()
        try:
            ziel = await repository.create_gegenstand(cid, pid, _maschinenteil_daten(qualitaet="normal"))
            gleich = await repository.create_gegenstand(cid, pid, _maschinenteil_daten(qualitaet="normal"))
            andere_qualitaet = await repository.create_gegenstand(cid, pid, _maschinenteil_daten(qualitaet="hochwertig"))

            kandidaten = await repository.stapelkandidaten(cid, ziel["id"])
            kandidaten_ids = {k["id"] for k in kandidaten}

            assert gleich["id"] in kandidaten_ids
            assert andere_qualitaet["id"] not in kandidaten_ids
            assert ziel["id"] not in kandidaten_ids
        finally:
            await _aufraeumen(cid)

    _run(szenario())
