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
                   p.id AS personId, p.name AS personName
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
                   p.id AS personId, p.name AS personName
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
