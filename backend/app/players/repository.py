import secrets
import uuid

from app.db.neo4j_driver import get_driver

# Verwechslungsarmes Alphabet: der Code wird am Spieltisch vorgelesen, also
# ohne 0/O, 1/I/L, 8/B. Lieber ein kürzeres Alphabet als Rückfragen.
_CODE_ALPHABET = "ACDEFGHJKMNPQRTUVWXY2345679"
_CODE_LAENGE = 6


def erzeuge_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LAENGE))


async def set_zugangscode(campaign_id: str, code: str | None) -> None:
    """Setzt oder entfernt den Beitrittscode einer Kampagne."""
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            "MATCH (c:Campaign {id: $campaign_id}) SET c.zugangscode = $code",
            campaign_id=campaign_id,
            code=code,
        )


async def get_zugangscode(campaign_id: str) -> str | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (c:Campaign {id: $campaign_id}) RETURN c.zugangscode AS code",
            campaign_id=campaign_id,
        )
        record = await result.single()
        return record["code"] if record else None


def normalisiere_code(roh: str) -> str:
    """Macht einen abgetippten Code vergleichbar.

    Der Code wird am Spieltisch vorgelesen und auf Tablets eingetippt. Dabei
    schleichen sich Leerzeichen ein (Autokorrektur hängt gern eines an),
    manche schreiben ihn gruppiert als "FMT-26V", und Groß-/Kleinschreibung
    soll ohnehin egal sein. All das wird hier weggeräumt, statt den Nutzer
    mit "Code ungültig" im Regen stehen zu lassen.
    """
    return "".join(z for z in roh if z.isalnum()).upper()


async def finde_kampagne_zu_code(code: str) -> dict | None:
    """Sucht die Kampagne zu einem Beitrittscode."""
    sauber = normalisiere_code(code)
    if not sauber:
        return None

    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (c:Campaign) WHERE c.zugangscode IS NOT NULL "
            "AND toUpper(c.zugangscode) = $code "
            "RETURN c.id AS id, c.name AS name",
            code=sauber,
        )
        record = await result.single()
        return dict(record) if record else None


async def create_session(campaign_id: str, name: str) -> dict:
    driver = get_driver()
    session_id = str(uuid.uuid4())
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})
            CREATE (s:PlayerSession {id: $session_id, name: $name, createdAt: datetime()})
            CREATE (s)-[:GEHOERT_ZU]->(c)
            RETURN s.id AS id, s.name AS name
            """,
            campaign_id=campaign_id,
            session_id=session_id,
            name=name,
        )
        record = await result.single()
        return dict(record)


async def get_session(session_id: str) -> dict | None:
    """Sitzung samt Kampagne und beanspruchtem Charakter.

    `personId` ist None, solange kein Charakter beansprucht wurde — die
    Sichtbarkeitsfilterung behandelt das korrekt (sieht dann nur, was für
    alle sichtbar ist).
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:PlayerSession {id: $session_id})-[:GEHOERT_ZU]->(c:Campaign)
            OPTIONAL MATCH (s)-[:SPIELT]->(p:Person)
            RETURN s.id AS id, s.name AS name, c.id AS campaignId, c.name AS campaignName,
                   p.id AS personId, p.name AS personName
            """,
            session_id=session_id,
        )
        record = await result.single()
        return dict(record) if record else None


async def freie_charaktere(campaign_id: str) -> list[dict]:
    """Spielercharaktere, die noch niemand beansprucht hat."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {campaignId: $campaign_id, personType: 'PC'})
            WHERE NOT EXISTS { MATCH (:PlayerSession)-[:SPIELT]->(p) }
            RETURN p.id AS id, p.name AS name ORDER BY p.name
            """,
            campaign_id=campaign_id,
        )
        return [dict(record) async for record in result]


async def claim_charakter(session_id: str, person_id: str) -> bool:
    """Beansprucht einen Charakter für die Sitzung.

    Scheitert (False), wenn der Charakter schon jemandem gehört oder nicht zur
    Kampagne der Sitzung zählt. Eine bestehende Zuordnung der Sitzung wird
    ersetzt — wer sich vertippt hat, kann wechseln, solange frei ist.
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:PlayerSession {id: $session_id})-[:GEHOERT_ZU]->(c:Campaign)
            MATCH (p:Person {id: $person_id, campaignId: c.id, personType: 'PC'})
            WHERE NOT EXISTS { MATCH (anderer:PlayerSession)-[:SPIELT]->(p) WHERE anderer.id <> $session_id }
            OPTIONAL MATCH (s)-[alt:SPIELT]->()
            DELETE alt
            CREATE (s)-[:SPIELT]->(p)
            RETURN p.id AS id
            """,
            session_id=session_id,
            person_id=person_id,
        )
        return await result.single() is not None


async def list_sessions(campaign_id: str) -> list[dict]:
    """Alle Sitzungen einer Kampagne — für die Übersicht des Spielleiters."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:PlayerSession)-[:GEHOERT_ZU]->(c:Campaign {id: $campaign_id})
            OPTIONAL MATCH (s)-[:SPIELT]->(p:Person)
            RETURN s.id AS id, s.name AS name, toString(s.createdAt) AS createdAt,
                   p.id AS personId, p.name AS personName
            ORDER BY s.createdAt
            """,
            campaign_id=campaign_id,
        )
        return [dict(record) async for record in result]


async def delete_session(campaign_id: str, session_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:PlayerSession {id: $session_id})-[:GEHOERT_ZU]->(:Campaign {id: $campaign_id})
            DETACH DELETE s
            RETURN count(s) AS geloescht
            """,
            campaign_id=campaign_id,
            session_id=session_id,
        )
        record = await result.single()
        return bool(record and record["geloescht"])
