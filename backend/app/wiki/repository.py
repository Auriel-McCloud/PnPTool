"""Neo4j-Zugriff für Wiki-Seiten.

Modell (docs/produktvision-wiki.md):

    (:Campaign)-[:HAT_SEITE]->(:WikiSeite {campaignId})
    (:WikiSeite)-[:UNTERSEITE_VON]->(:WikiSeite)
    (:WikiSeite)-[:VERWEIST_AUF]->(:Person|:Ort|:Event|:Gegenstand)

Ein Typ statt Dokument+Seite: was oben als Tab erscheint, ist eine Seite ohne
Elternteil. Damit kann jedes Kapitel später zur Unterseite werden, ohne dass
Daten migriert werden müssen.

`campaignId` steht wie bei den Entitäten zusätzlich am Knoten — die
Kampagnenzugehörigkeit ist damit ohne Pfad prüfbar.
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver
from app.wiki.logic import verweise_sammeln

# Entitätstypen, auf die eine Seite verweisen darf. Weisse Liste, damit ein
# manipuliertes Dokument keine beliebigen Labels in den Graphen schreibt —
# der Typ geht direkt in die Cypher-Abfrage ein.
ERLAUBTE_ZIELTYPEN = {"Person", "Ort", "Event", "Gegenstand"}

LEERES_DOKUMENT = '{"type":"doc","content":[]}'

_FELDER = """
    s.id AS id, s.titel AS titel, s.inhalt AS inhalt,
    s.sichtbarkeit AS sichtbarkeit, s.sichtbarFuer AS sichtbarFuer,
    s.sortierung AS sortierung, s.symbol AS symbol,
    s.erstelltAm AS erstelltAm, s.aktualisiertAm AS aktualisiertAm
"""


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mit_defaults(record) -> dict:
    """Fehlende Felder auffüllen, damit das Response-Schema nicht scheitert.

    Alte Zeilen ohne ein später hinzugekommenes Feld würden sonst die ganze
    Liste mit einem 500er herunterreissen (Stolperstein 9 in CLAUDE.md).
    """
    seite = dict(record)
    seite["inhalt"] = seite.get("inhalt") or LEERES_DOKUMENT
    seite["sichtbarFuer"] = seite.get("sichtbarFuer") or []
    seite["sichtbarkeit"] = seite.get("sichtbarkeit") or "GM"
    seite["sortierung"] = seite.get("sortierung") if seite.get("sortierung") is not None else 0
    seite["symbol"] = seite.get("symbol") or ""
    seite["titel"] = seite.get("titel") or "Ohne Titel"
    seite["erstelltAm"] = seite.get("erstelltAm") or ""
    seite["aktualisiertAm"] = seite.get("aktualisiertAm") or ""
    seite.setdefault("parentId", None)
    return seite


async def list_seiten(campaign_id: str) -> list[dict]:
    """Alle Seiten einer Kampagne, flach. Den Baum baut die Fachlogik."""
    driver = get_driver()
    query = f"""
        MATCH (s:WikiSeite {{campaignId: $campaign_id}})
        OPTIONAL MATCH (s)-[:UNTERSEITE_VON]->(eltern:WikiSeite)
        RETURN {_FELDER}, eltern.id AS parentId
        ORDER BY s.sortierung, s.titel
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_mit_defaults(record) async for record in result]


async def get_seite(campaign_id: str, seiten_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (s:WikiSeite {{id: $seiten_id, campaignId: $campaign_id}})
        OPTIONAL MATCH (s)-[:UNTERSEITE_VON]->(eltern:WikiSeite)
        RETURN {_FELDER}, eltern.id AS parentId
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, seiten_id=seiten_id)
        record = await result.single()
        return _mit_defaults(record) if record else None


async def _naechste_sortierung(session, campaign_id: str, parent_id: str | None) -> int:
    """Neue Seite hinter die letzte auf derselben Ebene."""
    result = await session.run(
        """
        MATCH (s:WikiSeite {campaignId: $campaign_id})
        OPTIONAL MATCH (s)-[:UNTERSEITE_VON]->(e:WikiSeite)
        WITH s, e.id AS pid
        WHERE coalesce(pid, '') = coalesce($parent_id, '')
        RETURN coalesce(max(s.sortierung), -1) + 1 AS naechste
        """,
        campaign_id=campaign_id,
        parent_id=parent_id,
    )
    record = await result.single()
    return int(record["naechste"]) if record else 0


async def _eltern_setzen(session, campaign_id: str, seiten_id: str, parent_id: str | None) -> None:
    """Elternbeziehung setzen oder lösen.

    Der Zyklusschutz sitzt bewusst hier und nicht nur in der Anzeige: Eine
    Seite unter ihre eigene Unterseite zu hängen, würde beim Lesen des Baums
    eine Endlosschleife erzeugen.
    """
    await session.run(
        """
        MATCH (s:WikiSeite {id: $seiten_id, campaignId: $campaign_id})-[alt:UNTERSEITE_VON]->()
        DELETE alt
        """,
        campaign_id=campaign_id,
        seiten_id=seiten_id,
    )
    if not parent_id or parent_id == seiten_id:
        return

    await session.run(
        """
        MATCH (s:WikiSeite {id: $seiten_id, campaignId: $campaign_id})
        MATCH (e:WikiSeite {id: $parent_id, campaignId: $campaign_id})
        WHERE NOT (e)-[:UNTERSEITE_VON*1..20]->(s)
        CREATE (s)-[:UNTERSEITE_VON]->(e)
        """,
        campaign_id=campaign_id,
        seiten_id=seiten_id,
        parent_id=parent_id,
    )


async def _verweise_schreiben(session, campaign_id: str, seiten_id: str, inhalt: str) -> None:
    """Verknüpfungen aus dem Dokument als echte Graphkanten spiegeln.

    Erst alle alten weg, dann die aktuellen neu — so verschwindet eine
    Verknüpfung auch dann, wenn der Verweis aus dem Text gelöscht wurde.

    Das Ziel muss zur selben Kampagne gehören: Ein manipuliertes Dokument darf
    keine Kante in eine fremde Kampagne ziehen.
    """
    await session.run(
        """
        MATCH (s:WikiSeite {id: $seiten_id, campaignId: $campaign_id})-[v:VERWEIST_AUF]->()
        DELETE v
        """,
        campaign_id=campaign_id,
        seiten_id=seiten_id,
    )

    for verweis in verweise_sammeln(inhalt):
        if verweis["zielTyp"] not in ERLAUBTE_ZIELTYPEN:
            continue
        await session.run(
            f"""
            MATCH (s:WikiSeite {{id: $seiten_id, campaignId: $campaign_id}})
            MATCH (ziel:{verweis["zielTyp"]} {{id: $ziel_id, campaignId: $campaign_id}})
            MERGE (s)-[:VERWEIST_AUF]->(ziel)
            """,
            campaign_id=campaign_id,
            seiten_id=seiten_id,
            ziel_id=verweis["zielId"],
        )


async def create_seite(
    campaign_id: str,
    titel: str,
    inhalt: str = LEERES_DOKUMENT,
    parent_id: str | None = None,
    sichtbarkeit: str = "GM",
    sichtbar_fuer: list[str] | None = None,
    symbol: str = "",
) -> dict | None:
    """Legt eine Seite an. Standard ist SL-geheim (siehe wiki/visibility.py)."""
    driver = get_driver()
    jetzt = _jetzt()
    async with driver.session() as session:
        sortierung = await _naechste_sortierung(session, campaign_id, parent_id)

        result = await session.run(
            f"""
            MATCH (c:Campaign {{id: $campaign_id}})
            CREATE (s:WikiSeite {{
                id: $seiten_id, campaignId: $campaign_id,
                titel: $titel, inhalt: $inhalt,
                sichtbarkeit: $sichtbarkeit, sichtbarFuer: $sichtbar_fuer,
                sortierung: $sortierung, symbol: $symbol,
                erstelltAm: $jetzt, aktualisiertAm: $jetzt
            }})
            CREATE (c)-[:HAT_SEITE]->(s)
            RETURN {_FELDER}
            """,
            campaign_id=campaign_id,
            seiten_id=str(uuid.uuid4()),
            titel=titel,
            inhalt=inhalt,
            sichtbarkeit=sichtbarkeit,
            sichtbar_fuer=sichtbar_fuer or [],
            sortierung=sortierung,
            symbol=symbol,
            jetzt=jetzt,
        )
        record = await result.single()
        if record is None:
            return None

        seite = _mit_defaults(record)
        if parent_id:
            await _eltern_setzen(session, campaign_id, seite["id"], parent_id)
            seite["parentId"] = parent_id
        await _verweise_schreiben(session, campaign_id, seite["id"], inhalt)
        return seite


SETZBAR = {"titel", "inhalt", "sichtbarkeit", "sichtbarFuer", "sortierung", "symbol"}


async def update_seite(campaign_id: str, seiten_id: str, felder: dict) -> dict | None:
    """Teilaktualisierung. Nur mitgeschickte Felder werden angefasst."""
    aenderung = {k: v for k, v in felder.items() if k in SETZBAR and v is not None}

    driver = get_driver()
    async with driver.session() as session:
        if aenderung:
            zuweisung = ", ".join(f"s.{k} = ${k}" for k in aenderung)
            result = await session.run(
                f"""
                MATCH (s:WikiSeite {{id: $seiten_id, campaignId: $campaign_id}})
                SET {zuweisung}, s.aktualisiertAm = $jetzt
                RETURN s.id AS id
                """,
                campaign_id=campaign_id,
                seiten_id=seiten_id,
                jetzt=_jetzt(),
                **aenderung,
            )
            if await result.single() is None:
                return None
        elif await get_seite(campaign_id, seiten_id) is None:
            return None

        # parentId kann bewusst None sein (Seite auf oberste Ebene holen),
        # deshalb Prüfung auf Anwesenheit statt auf Wahrheitswert.
        if "parentId" in felder:
            await _eltern_setzen(session, campaign_id, seiten_id, felder["parentId"])

        if "inhalt" in aenderung:
            await _verweise_schreiben(session, campaign_id, seiten_id, aenderung["inhalt"])

    return await get_seite(campaign_id, seiten_id)


async def delete_seite(campaign_id: str, seiten_id: str) -> bool:
    """Löscht eine Seite; Unterseiten rücken eine Ebene nach oben.

    Bewusst kein kaskadierendes Löschen: Beim Aufräumen eines Kapitels sollen
    nicht unbemerkt alle Szenen darunter verschwinden.
    """
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (s:WikiSeite {id: $seiten_id, campaignId: $campaign_id})
            OPTIONAL MATCH (kind:WikiSeite)-[runter:UNTERSEITE_VON]->(s)
            OPTIONAL MATCH (s)-[:UNTERSEITE_VON]->(gross:WikiSeite)
            DELETE runter
            WITH kind, gross
            WHERE kind IS NOT NULL AND gross IS NOT NULL
            CREATE (kind)-[:UNTERSEITE_VON]->(gross)
            """,
            campaign_id=campaign_id,
            seiten_id=seiten_id,
        )
        result = await session.run(
            """
            MATCH (s:WikiSeite {id: $seiten_id, campaignId: $campaign_id})
            DETACH DELETE s
            RETURN count(s) AS weg
            """,
            campaign_id=campaign_id,
            seiten_id=seiten_id,
        )
        record = await result.single()
        return bool(record and record["weg"])


async def freigeben(campaign_id: str, seiten_ids: list[str], sichtbarkeit: str, sichtbar_fuer: list[str]) -> int:
    """Mehrere Seiten auf einmal freigeben ("bis hierher freigeben")."""
    if not seiten_ids:
        return 0
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:WikiSeite {campaignId: $campaign_id})
            WHERE s.id IN $ids
            SET s.sichtbarkeit = $modus, s.sichtbarFuer = $fuer, s.aktualisiertAm = $jetzt
            RETURN count(s) AS anzahl
            """,
            campaign_id=campaign_id,
            ids=seiten_ids,
            modus=sichtbarkeit,
            fuer=sichtbar_fuer,
            jetzt=_jetzt(),
        )
        record = await result.single()
        return int(record["anzahl"]) if record else 0


async def rueckverweise(campaign_id: str, ziel_id: str) -> list[dict]:
    """Welche Wiki-Seiten erwähnen diese Entität? ("Erwähnt in: Kapitel 1")

    Liefert die Sichtbarkeit mit, damit die Route sie filtern kann — sonst
    verriete die Liste dem Spieler die Existenz geheimer Seiten.
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (s:WikiSeite {campaignId: $campaign_id})-[:VERWEIST_AUF]->(ziel {id: $ziel_id})
            RETURN s.id AS id, s.titel AS titel,
                   s.sichtbarkeit AS sichtbarkeit, s.sichtbarFuer AS sichtbarFuer
            ORDER BY s.sortierung, s.titel
            """,
            campaign_id=campaign_id,
            ziel_id=ziel_id,
        )
        return [dict(record) async for record in result]
