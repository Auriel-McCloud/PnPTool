"""Spieler-Zugänge: fester Benutzername statt flüchtiger Beitrittssitzung.

Vorher gab es einen Kampagnen-Code, mit dem man beitrat und sich dann einen
freien Charakter nahm. Das führte laufend zu Konflikten: wer sich von einem
zweiten Gerät anmeldete, fand seinen Charakter belegt — von sich selbst.
Jetzt gehört ein Charakter dauerhaft zu einem Benutzernamen.
"""

import uuid

import bcrypt

from app.db.neo4j_driver import get_driver


def _hash(passwort: str) -> str:
    return bcrypt.hashpw(passwort.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def pruefe_passwort(passwort: str, hash_wert: str | None) -> bool:
    """Prüft das Passwort — ein leeres Feld heisst *kein Passwort nötig*.

    Bewusst so: In einer privaten Runde soll niemand erst ein Passwort
    ausdenken müssen. Wer eines setzt, wird ab dann danach gefragt.
    """
    if not hash_wert:
        return True
    if not passwort:
        return False
    return bcrypt.checkpw(passwort.encode("utf-8"), hash_wert.encode("utf-8"))


async def create_spieler(campaign_id: str, benutzername: str, person_id: str | None, passwort: str = "") -> dict | None:
    """Legt einen Spielerzugang an. Name muss in der Kampagne eindeutig sein."""
    name = benutzername.strip()
    if not name:
        return None

    driver = get_driver()
    async with driver.session() as session:
        # Vergleich über die kleingeschriebene Fassung: "Auriel" und "auriel"
        # sind derselbe Zugang.
        vorhanden = await session.run(
            """
            MATCH (s:Spieler)-[:GEHOERT_ZU]->(:Campaign {id: $campaign_id})
            WHERE toLower(s.benutzername) = toLower($name)
            RETURN s.id AS id
            """,
            campaign_id=campaign_id,
            name=name,
        )
        if await vorhanden.single() is not None:
            return None

        result = await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})
            CREATE (s:Spieler {
                id: $spieler_id, benutzername: $name, passwortHash: $hash, createdAt: datetime()
            })
            CREATE (s)-[:GEHOERT_ZU]->(c)
            WITH s, c
            OPTIONAL MATCH (p:Person {id: $person_id, campaignId: c.id})
            FOREACH (_ IN CASE WHEN p IS NULL THEN [] ELSE [1] END | CREATE (s)-[:SPIELT]->(p))
            RETURN s.id AS id, s.benutzername AS benutzername
            """,
            campaign_id=campaign_id,
            spieler_id=str(uuid.uuid4()),
            name=name,
            hash=_hash(passwort) if passwort else None,
            person_id=person_id or "",
        )
        record = await result.single()
        return dict(record) if record else None


async def finde_spieler(benutzername: str) -> dict | None:
    """Sucht kampagnenübergreifend nach dem Benutzernamen, ohne Rücksicht auf
    Gross- und Kleinschreibung — beim Anmelden weiss man die Kampagne nicht."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Spieler)-[:GEHOERT_ZU]->(c:Campaign)
            WHERE toLower(s.benutzername) = toLower($name)
            OPTIONAL MATCH (s)-[:SPIELT]->(p:Person)
            RETURN s.id AS id, s.benutzername AS benutzername, s.passwortHash AS passwortHash,
                   c.id AS campaignId, c.name AS campaignName,
                   p.id AS personId, p.name AS personName, p.bildUrl AS personBildUrl
            """,
            name=benutzername.strip(),
        )
        record = await result.single()
        return dict(record) if record else None


async def get_spieler(spieler_id: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Spieler {id: $spieler_id})-[:GEHOERT_ZU]->(c:Campaign)
            OPTIONAL MATCH (s)-[:SPIELT]->(p:Person)
            RETURN s.id AS id, s.benutzername AS benutzername, s.passwortHash AS passwortHash,
                   c.id AS campaignId, c.name AS campaignName,
                   p.id AS personId, p.name AS personName, p.bildUrl AS personBildUrl
            """,
            spieler_id=spieler_id,
        )
        record = await result.single()
        return dict(record) if record else None


async def setze_passwort(spieler_id: str, passwort: str) -> bool:
    """Setzt oder entfernt das Passwort. Leer bedeutet: keines mehr nötig."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (s:Spieler {id: $spieler_id}) SET s.passwortHash = $hash RETURN s.id AS id",
            spieler_id=spieler_id,
            hash=_hash(passwort) if passwort else None,
        )
        return await result.single() is not None


async def setze_charakter(campaign_id: str, spieler_id: str, person_id: str | None) -> bool:
    """Ordnet den Charakter zu. Eine bestehende Zuordnung wird ersetzt."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Spieler {id: $spieler_id})-[:GEHOERT_ZU]->(c:Campaign {id: $campaign_id})
            OPTIONAL MATCH (s)-[alt:SPIELT]->()
            DELETE alt
            WITH s, c
            OPTIONAL MATCH (p:Person {id: $person_id, campaignId: c.id})
            FOREACH (_ IN CASE WHEN p IS NULL THEN [] ELSE [1] END | CREATE (s)-[:SPIELT]->(p))
            RETURN s.id AS id
            """,
            campaign_id=campaign_id,
            spieler_id=spieler_id,
            person_id=person_id or "",
        )
        return await result.single() is not None


async def list_spieler(campaign_id: str) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Spieler)-[:GEHOERT_ZU]->(:Campaign {id: $campaign_id})
            OPTIONAL MATCH (s)-[:SPIELT]->(p:Person)
            RETURN s.id AS id, s.benutzername AS benutzername,
                   s.passwortHash IS NOT NULL AS hatPasswort,
                   p.id AS personId, p.name AS personName
            ORDER BY toLower(s.benutzername)
            """,
            campaign_id=campaign_id,
        )
        return [dict(record) async for record in result]


async def verfuegbare_pcs(campaign_id: str) -> list[dict]:
    """Vorgebaute PCs dieser Kampagne, die noch niemandem zugeordnet sind.

    Ersteinstiegs-Fenster (players/SpielerEinstieg.tsx): "vorgefertigter
    Charakter" ist bewusst kein eigenes Feld, sondern schlicht ein PC ohne
    SPIELT-Kante — Mark: "das macht am meisten Sinn". Nur abgeschlossene,
    nicht-Entwurfs-Charaktere: was hier erscheint, muss sofort spielbar sein.
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {campaignId: $campaign_id, personType: 'PC'})
            WHERE p.erstellungAbgeschlossen = true
              AND coalesce(p.istEntwurf, false) = false
              AND NOT EXISTS { MATCH (:Spieler)-[:SPIELT]->(p) }
            RETURN p.id AS id, p.name AS name, coalesce(p.bildUrl, '') AS bildUrl,
                   coalesce(p.konzept, '') AS konzept, coalesce(p.rasse, '') AS rasse,
                   coalesce(p.weg, 'KEINER') AS weg
            ORDER BY toLower(p.name)
            """,
            campaign_id=campaign_id,
        )
        return [dict(record) async for record in result]


async def charakter_waehlen(spieler_id: str, campaign_id: str, person_id: str) -> bool:
    """Weist einem Spieler ohne eigenen Charakter einen freien, vorgebauten PC
    fix zu — atomar in einer einzigen Cypher-Anweisung.

    Taucht zwischen dem Laden der Liste und diesem Aufruf eine SPIELT-Kante
    eines anderen Spielers auf (zwei Leute tippen gleichzeitig denselben
    Charakter an), greift die NOT EXISTS-Bedingung nicht mehr und die
    Anweisung liefert keine Zeile — genau dann verliert, wer zu spät war,
    statt dass zwei Spieler denselben Charakter bekommen. Ebenso, wenn der
    Spieler selbst inzwischen schon einen Charakter hat.
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Spieler {id: $spieler_id})-[:GEHOERT_ZU]->(:Campaign {id: $campaign_id})
            WHERE NOT EXISTS { MATCH (s)-[:SPIELT]->() }
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id, personType: 'PC'})
            WHERE p.erstellungAbgeschlossen = true
              AND coalesce(p.istEntwurf, false) = false
              AND NOT EXISTS { MATCH (:Spieler)-[:SPIELT]->(p) }
            CREATE (s)-[:SPIELT]->(p)
            RETURN s.id AS id
            """,
            spieler_id=spieler_id,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        return await result.single() is not None


async def bindet_neuen_charakter(spieler_id: str, campaign_id: str, person_id: str) -> bool:
    """Bindet einen frisch angelegten, noch leeren PC an den Spieler, der ihn
    gerade selbst erstellt (`charakter_neu_bauen`) — bewusst eine eigene
    Anweisung statt `charakter_waehlen` wiederzuverwenden: die verlangt
    `erstellungAbgeschlossen = true` (für vorgefertigte, fertige PCs), was ein
    gerade erst angelegter Entwurf nie erfüllt. Vorher führte das dazu, dass
    "Charakter selbst erstellen" immer mit 409 scheiterte, egal wie frisch
    der Spieler war.
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Spieler {id: $spieler_id})-[:GEHOERT_ZU]->(:Campaign {id: $campaign_id})
            WHERE NOT EXISTS { MATCH (s)-[:SPIELT]->() }
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id, personType: 'PC'})
            WHERE NOT EXISTS { MATCH (:Spieler)-[:SPIELT]->(p) }
            CREATE (s)-[:SPIELT]->(p)
            RETURN s.id AS id
            """,
            spieler_id=spieler_id,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        return await result.single() is not None


async def delete_spieler(campaign_id: str, spieler_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:Spieler {id: $spieler_id})-[:GEHOERT_ZU]->(:Campaign {id: $campaign_id})
            DETACH DELETE s
            RETURN count(s) AS weg
            """,
            campaign_id=campaign_id,
            spieler_id=spieler_id,
        )
        record = await result.single()
        return bool(record and record["weg"])
