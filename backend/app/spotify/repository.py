"""Speichert die globale Spotify-Verbindung (Refresh-Token) in Neo4j.

Ein Konto fuers ganze Tool, nicht pro Kampagne (Marks Entscheidung) — ein
einzelner Knoten mit fester ID statt einer Liste. Der Access-Token selbst
wird nicht persistiert, nur im Prozessspeicher zwischengehalten (er lebt eh
nur eine Stunde); nach einem Neustart holt sich der erste Aufruf einfach
einen frischen ueber den gespeicherten Refresh-Token.
"""

import time

from app.db.neo4j_driver import get_driver
from app.spotify import client
from app.spotify.client import SpotifyFehler

_KONTO_ID = "global"

# Prozessweiter Cache — vermeidet einen Refresh-Request bei jedem einzelnen
# Spotify-Aufruf. Kein Neo4j-Feld: Access-Tokens sind kurzlebig genug, dass
# ein Neustart einfach einen neuen anfordert.
_cache: dict[str, float | str] = {}


async def _hole_konto() -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (k:SpotifyKonto {id: $id}) RETURN k.refreshToken AS refreshToken, "
            "k.anzeigename AS anzeigename",
            id=_KONTO_ID,
        )
        record = await result.single()
        return dict(record) if record else None


async def status() -> dict:
    konto = await _hole_konto()
    if konto is None or not konto.get("refreshToken"):
        return {"verbunden": False, "anzeigename": None}
    return {"verbunden": True, "anzeigename": konto.get("anzeigename")}


async def verbinden(refresh_token: str, anzeigename: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MERGE (k:SpotifyKonto {id: $id})
            SET k.refreshToken = $refresh_token, k.anzeigename = $anzeigename,
                k.verbundenAm = datetime()
            """,
            id=_KONTO_ID,
            refresh_token=refresh_token,
            anzeigename=anzeigename,
        )
    _cache.clear()


async def trennen() -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (k:SpotifyKonto {id: $id}) DETACH DELETE k", id=_KONTO_ID)
    _cache.clear()


async def gueltiger_access_token() -> str:
    """Liefert einen frischen Access-Token, erneuert ihn bei Bedarf.

    Wirft SpotifyFehler, wenn (noch) keine Verbindung besteht.
    """
    jetzt = time.time()
    ablauf = _cache.get("ablauf")
    if _cache.get("access_token") and isinstance(ablauf, (int, float)) and ablauf > jetzt + 5:
        return str(_cache["access_token"])

    konto = await _hole_konto()
    if konto is None or not konto.get("refreshToken"):
        raise SpotifyFehler("Kein Spotify-Konto verbunden")

    antwort = await client.token_erneuern(konto["refreshToken"])
    _cache["access_token"] = antwort["access_token"]
    _cache["ablauf"] = jetzt + float(antwort.get("expires_in", 3600))

    # Spotify liefert nur manchmal einen neuen refresh_token mit zurueck —
    # wenn ja, den alten ersetzen (er kann inzwischen rotiert worden sein).
    if antwort.get("refresh_token"):
        driver = get_driver()
        async with driver.session() as session:
            await session.run(
                "MATCH (k:SpotifyKonto {id: $id}) SET k.refreshToken = $rt",
                id=_KONTO_ID,
                rt=antwort["refresh_token"],
            )
    return str(_cache["access_token"])
