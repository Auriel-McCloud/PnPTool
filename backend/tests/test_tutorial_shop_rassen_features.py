"""Tutorial-Shop + Rassen-Features (10.10.2026): Repository-Ebene.

Deckt das, was ohne FastAPI-TestClient (im Projekt bisher nicht verwendet,
siehe test_shop_am_ort.py-Stil — reine asyncio.run()-Aufrufe gegen
Repository-Funktionen) prüfbar ist:
- Rassen-Baukasten speichert/liest die neuen Feature-Felder korrekt
- Tutorial-Shop wird aus der normalen Shop-Liste ausgeschlossen, aber über
  die eigene Funktion gefunden

**Nicht abgedeckt** (bräuchte einen echten HTTP-Request mit Viewer-Context,
siehe `app/haendler/routes.py::kaufen`/`app/traits/routes.py::
erstelle_charakter`): der Quill-Gratis-Hextech-Preis-auf-0-Pfad und die
Dug'Rah-Gratis-Gegenstand-Zuweisung beim Erstellungs-Submit. Die Logik ist
code-review-geprüft, aber nicht über einen echten Request durchgespielt.
"""

import asyncio
import uuid

from app.db.neo4j_driver import get_driver
from app.haendler import repository as haendler_repository
from app.rassen import repository as rassen_repository


def _run(coro):
    return asyncio.run(coro)


async def _kampagne_anlegen() -> str:
    cid = f"test-tutorial-shop-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'Tutorial-Shop-Test'})", cid=cid)
    return cid


async def _aufraeumen(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


def test_rasse_speichert_feature_felder():
    async def lauf():
        daten = {
            "name": "Quill-Test",
            "beschreibung": "",
            "modifikatoren": {},
            "freiePunkte": [7, 5, 3],
            "bonusFreebees": 0,
            "gratisGegenstandId": "",
            "gratisErsterKaufTyp": "Hexware",
            "featureHinweis": "Erstes Hextech gratis",
        }
        rasse = await rassen_repository.anlegen(daten)
        try:
            assert rasse["gratisErsterKaufTyp"] == "Hexware"
            assert rasse["featureHinweis"] == "Erstes Hextech gratis"
            assert rasse["bonusFreebees"] == 0

            geholt = await rassen_repository.hole(rasse["id"])
            assert geholt is not None
            assert geholt["gratisErsterKaufTyp"] == "Hexware"

            # Ändern: bonusFreebees nachträglich setzen (Mensch-Fall)
            geaendert = await rassen_repository.aendern(rasse["id"], {"bonusFreebees": 2})
            assert geaendert is not None
            assert geaendert["bonusFreebees"] == 2
            # Unverändert gelassene Felder bleiben stehen
            assert geaendert["gratisErsterKaufTyp"] == "Hexware"
        finally:
            await rassen_repository.loeschen(rasse["id"])

    _run(lauf())


def test_rasse_ohne_feature_felder_bekommt_leere_defaults():
    """Bestandsrassen ohne die neuen Properties (vor 10.10.2026 angelegt)
    dürfen nicht mit Pydantic-Validierungsfehlern abstürzen — coalesce in
    FELDER/_decode muss greifen (Stolperstein 3 in CLAUDE.md)."""
    async def lauf():
        driver = get_driver()
        rid = str(uuid.uuid4())
        async with driver.session() as session:
            await session.run(
                """
                CREATE (r:Rasse {
                    id: $id, ruleset: 'neotopia', name: 'Alt-Rasse-Test',
                    beschreibung: '', bildUrl: '', modifikatoren: '{}',
                    freiePunkte: [7, 5, 3], sortOrder: 0
                })
                """,
                id=rid,
            )
        try:
            geholt = await rassen_repository.hole(rid)
            assert geholt is not None
            assert geholt["bonusFreebees"] == 0
            assert geholt["gratisGegenstandId"] == ""
            assert geholt["gratisErsterKaufTyp"] == ""
            assert geholt["featureHinweis"] == ""
        finally:
            driver = get_driver()
            async with driver.session() as session:
                await session.run("MATCH (r:Rasse {id: $id}) DETACH DELETE r", id=rid)

    _run(lauf())


def test_tutorial_shop_ausgeschlossen_aus_normaler_liste():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            hid = str(uuid.uuid4())
            driver = get_driver()
            async with driver.session() as session:
                await session.run(
                    """
                    MATCH (c:Campaign {id: $cid})
                    CREATE (h:Person {
                        id: $hid, campaignId: $cid, name: 'Tutorial-Verkäufer',
                        personType: 'NPC', istHaendler: true, istTutorialHaendler: true,
                        sichtbarkeit: 'ALLE', sichtbarFuer: []
                    })
                    CREATE (c)-[:HAT_ENTITAET]->(h)
                    """,
                    cid=cid,
                    hid=hid,
                )

            # liste() (normale Shop-Übersicht) darf den Tutorial-Shop NICHT zeigen.
            alle = await haendler_repository.liste(cid)
            assert len(alle) == 0

            # tutorial_shop() findet ihn trotzdem.
            tut = await haendler_repository.tutorial_shop(cid)
            assert tut is not None
            assert tut["istTutorialShop"] is True
            assert tut["name"] == "Tutorial-Verkäufer"
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_normaler_shop_bleibt_in_der_liste():
    """Gegenprobe: ein Händler OHNE das Tutorial-Flag taucht weiterhin ganz
    normal in der Übersicht auf — der Ausschluss darf nicht zu breit greifen."""
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            hid = str(uuid.uuid4())
            driver = get_driver()
            async with driver.session() as session:
                await session.run(
                    """
                    MATCH (c:Campaign {id: $cid})
                    CREATE (h:Person {
                        id: $hid, campaignId: $cid, name: 'Echter Händler',
                        personType: 'NPC', istHaendler: true,
                        sichtbarkeit: 'ALLE', sichtbarFuer: []
                    })
                    CREATE (c)-[:HAT_ENTITAET]->(h)
                    """,
                    cid=cid,
                    hid=hid,
                )

            alle = await haendler_repository.liste(cid)
            assert len(alle) == 1
            assert alle[0]["name"] == "Echter Händler"
            assert alle[0]["istTutorialShop"] is False

            tut = await haendler_repository.tutorial_shop(cid)
            assert tut is None
        finally:
            await _aufraeumen(cid)

    _run(lauf())
