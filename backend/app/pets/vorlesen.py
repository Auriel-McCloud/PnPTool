"""Bärbel liest vor — ein KI-Anruf je Lesung, nicht je Frame.

Mark, 11.11.2026: etwa alle 15 Minuten, solange Spieler da sind, schlägt sie
sich groß auf und kommentiert die Lage mit einem echten Bibelzitat. Bleibt,
bis jemand antippt. Fällt der Anbieter aus, nimmt sie einen bekannten Vers,
damit die Lesung nicht still ausbleibt.
"""

import logging

from app.ki.client import KiFehler, generiere_json

log = logging.getLogger(__name__)

LESEN_MIN_S = 13 * 60
LESEN_MAX_S = 17 * 60

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "stelle": {"type": "STRING"},
        "zitat": {"type": "STRING"},
        "kommentar": {"type": "STRING"},
    },
    "required": ["stelle", "zitat", "kommentar"],
}

_SYSTEM = (
    "Du bist Bärbel, eine sprechende Bibel und zugleich ein kleines Zauberbuch "
    "in einem Cyberpunk-Pen-and-Paper. Du kommentierst die Lage der Spielrunde "
    "ausschließlich über ein echtes Bibelzitat auf Deutsch (Luther oder "
    "Einheitsübersetzung) plus einen kurzen, frechen Satz, der das Zitat auf "
    "genau diese Situation münzt. Keine Predigt, keine moderne Politik, kein "
    "Belehren. Nur eine Stelle, von der du die Wortlaut sicher kennst — lieber "
    "ein bekannter Vers als ein erfundener. stelle ist „Buch Kapitel,Vers“. "
    "zitat höchstens 240 Zeichen, kommentar höchstens 160, ohne Anführungszeichen "
    "um das Zitat."
)

# Echte, kurze Verse — nur der Notnagel, wenn kein Anbieter antwortet.
_FALLBACK = [
    {
        "stelle": "Johannes 1,5",
        "zitat": "Und das Licht scheint in der Finsternis, und die Finsternis hat's nicht ergriffen.",
        "kommentar": "Steht hier auch so. Ob ihr das Licht seid oder die Finsternis, sagt sie nicht.",
    },
    {
        "stelle": "Prediger 3,1",
        "zitat": "Ein jegliches hat seine Zeit, und alles Vorhaben unter dem Himmel hat seine Stunde.",
        "kommentar": "Auch das Herumstehen. Sie blättert weiter und tut so, als wäre das Trost.",
    },
    {
        "stelle": "Psalm 23,4",
        "zitat": "Und ob ich schon wanderte im finstern Tal, fürchte ich kein Unglück; denn du bist bei mir.",
        "kommentar": "Sie ist ja da. Ob das beruhigt, ist eine andere Frage.",
    },
    {
        "stelle": "Matthäus 5,14",
        "zitat": "Ihr seid das Licht der Welt.",
        "kommentar": "Sie klappt eine Seite um und murmelt, das sei hier eher die Ausnahme.",
    },
]


def _kurz(wert: object, laenge: int) -> str:
    text = " ".join(str(wert or "").split())
    return text[:laenge].rstrip()


def _sauber(roh: dict) -> dict | None:
    stelle = _kurz(roh.get("stelle"), 60)
    zitat = _kurz(roh.get("zitat"), 280)
    kommentar = _kurz(roh.get("kommentar"), 180)
    if len(stelle) < 3 or len(zitat) < 12 or len(kommentar) < 8:
        return None
    return {"stelle": stelle, "zitat": zitat, "kommentar": kommentar}


async def lage(campaign_id: str, besitzer_id: str, anwesende_ids: list[str]) -> str:
    """Wer ist da, wo steht die Party, welche Events hängen am Ort. Klein halten."""
    from app.db.neo4j_driver import get_driver

    ids = [i for i in anwesende_ids if i][:12]
    try:
        async with get_driver().session() as session:
            namen = await session.run(
                """
                MATCH (p:Person {campaignId: $cid})
                WHERE p.id IN $ids
                RETURN p.name AS name
                """,
                cid=campaign_id,
                ids=ids or ["-"],
            )
            namen = [r["name"] for r in await namen.data() if r.get("name")]
            ort = await session.run(
                """
                MATCH (besitzer:Person {id: $besitzer, campaignId: $cid})-[:MITGLIED_VON]->(party:Party)
                WHERE coalesce(party.aktiv, false) = true
                OPTIONAL MATCH (party)-[:BEFINDET_SICH_AN]->(ziel)
                OPTIONAL MATCH (e:Event {campaignId: $cid})-[:VERBINDUNG]-(ziel)
                RETURN party.name AS party,
                       coalesce(ziel.name, ziel.title, '') AS ort,
                       [x IN collect(DISTINCT coalesce(e.title, e.name))
                        WHERE x IS NOT NULL AND x <> ''][0..3] AS events
                """,
                cid=campaign_id,
                besitzer=besitzer_id,
            )
            zeile = await ort.single()
    except Exception:
        log.warning("Bärbel-Lage nicht lesbar", exc_info=True)
        return "Spieler sind da. Ort unbekannt."
    teile = []
    if namen:
        teile.append("Anwesend: " + ", ".join(namen[:8]))
    if zeile and zeile.get("ort"):
        teile.append(f"Party „{zeile.get('party') or 'Party'}“ ist bei „{zeile['ort']}“")
    events = [e for e in (zeile.get("events") if zeile else []) or [] if e]
    if events:
        teile.append("Ereignisse dort: " + "; ".join(events))
    return ". ".join(teile) or "Spieler sind da. Mehr weiß sie gerade nicht."


async def erzeugen(campaign_id: str, besitzer_id: str, anwesende_ids: list[str]) -> dict:
    """Eine Lesung. Bei Ausfall ein fester Vers, nie eine erfundene Stelle."""
    try:
        text = await lage(campaign_id, besitzer_id, anwesende_ids)
        roh = await generiere_json(
            f"Situation, die du kommentierst:\n{text}",
            _SYSTEM,
            _SCHEMA,
            campaign_id=campaign_id,
        )
        sauber = _sauber(roh if isinstance(roh, dict) else {})
        if sauber:
            return sauber
    except (KiFehler, Exception):
        log.warning("Bärbel-Lesung ohne KI, fester Vers", exc_info=True)
    return dict(_FALLBACK[sum(ord(c) for c in campaign_id) % len(_FALLBACK)])
