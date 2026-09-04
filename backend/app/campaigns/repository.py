import json
import uuid

from app.db.neo4j_driver import get_driver


async def create_campaign(name: str, ruleset: str, gm_id: str) -> dict:
    driver = get_driver()
    campaign_id = str(uuid.uuid4())
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (g:GMUser {id: $gm_id})
            CREATE (c:Campaign {id: $campaign_id, name: $name, ruleset: $ruleset, createdAt: datetime()})
            CREATE (g)-[:OWNS]->(c)
            RETURN c.id AS id, c.name AS name, c.ruleset AS ruleset
            """,
            gm_id=gm_id,
            campaign_id=campaign_id,
            name=name,
            ruleset=ruleset,
        )
        record = await result.single()
        return dict(record)


async def list_campaigns_for_gm(gm_id: str) -> list[dict]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (g:GMUser {id: $gm_id})-[:OWNS]->(c:Campaign) "
            "RETURN c.id AS id, c.name AS name, coalesce(c.ruleset, 'neotopia') AS ruleset ORDER BY c.name",
            gm_id=gm_id,
        )
        return [dict(record) async for record in result]


async def campaign_owned_by(campaign_id: str, gm_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (g:GMUser {id: $gm_id})-[:OWNS]->(c:Campaign {id: $campaign_id}) RETURN c.id AS id",
            gm_id=gm_id,
            campaign_id=campaign_id,
        )
        return await result.single() is not None


# Kampagnenweite Spieleinstellungen mit ihren Ausgangswerten.
# Bewusst als offene Sammlung angelegt: Gewicht ist die erste solche Regel,
# weitere (Munitionsverfolgung, Erfahrungspunkte-Automatik ...) kommen hier
# dazu, ohne dass Schema oder Routen sich ändern müssen.
EINSTELLUNGEN_DEFAULTS: dict = {
    # Der Messenger ist eine optionale In-World-Funktion und wird pro
    # Kampagne ausdrücklich aktiviert. Bestandskampagnen bleiben dadurch
    # kompatibel und D&D-Kampagnen bekommen keinen unpassenden Chat.
    "messengerAktiv": False,
    # Zeigt Gewicht und Kapazität an. Rein informativ — nichts wird verhindert,
    # der Balken färbt sich nur rot. Die Spielleitung zieht die Konsequenzen.
    "gewichtAktiv": True,
    # Woraus sich die Traglast einer Person ergibt. In NeotopiA heißt das
    # Attribut "Körperkraft", in anderen Systemen "Stärke" — deshalb nicht
    # fest verdrahtet.
    "traglastAttribut": "Körperkraft",
    # Kilogramm je Attributpunkt.
    "traglastProPunkt": 10.0,
    # Würfeln die Spieler im Tool statt am Tisch? Mark spielt mit echten
    # Würfeln — deshalb aus. Wer digital würfelt, schaltet es je Kampagne ein.
    "digitalesWuerfeln": False,
    # Die Ausnahme: die Spielleitung würfelt die Initiative ihrer NPCs
    # automatisch, auch wenn die Spieler physisch würfeln. Mark: "die hätte
    # ich schon gerne automatisch".
    "digitalesWuerfelnSL": True,
}


async def get_einstellungen(campaign_id: str) -> dict:
    """Spieleinstellungen einer Kampagne, fehlende auf Standardwert.

    Gespeichert wird nur, was abweicht; alles Übrige kommt aus den Defaults.
    So wirken neue Einstellungen sofort für Bestandskampagnen, ohne Migration.
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (c:Campaign {id: $campaign_id}) RETURN c.einstellungen AS roh",
            campaign_id=campaign_id,
        )
        record = await result.single()

    werte = dict(EINSTELLUNGEN_DEFAULTS)
    if record and record["roh"]:
        try:
            werte.update(json.loads(record["roh"]))
        except (json.JSONDecodeError, TypeError):
            # Kaputter Inhalt darf die Kampagne nicht unbenutzbar machen
            pass
    return werte


async def set_einstellungen(campaign_id: str, aenderungen: dict) -> dict:
    """Ändert einzelne Einstellungen; unbekannte Schlüssel werden verworfen."""
    aktuell = await get_einstellungen(campaign_id)
    aktuell.update({k: v for k, v in aenderungen.items() if k in EINSTELLUNGEN_DEFAULTS})

    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            "MATCH (c:Campaign {id: $campaign_id}) SET c.einstellungen = $roh",
            campaign_id=campaign_id,
            roh=json.dumps(aktuell),
        )
    return aktuell


async def get_campaign(campaign_id: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (c:Campaign {id: $campaign_id}) RETURN c.id AS id, c.name AS name, coalesce(c.ruleset, 'neotopia') AS ruleset",
            campaign_id=campaign_id,
        )
        record = await result.single()
        return dict(record) if record else None
