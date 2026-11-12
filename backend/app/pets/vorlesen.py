"""Bärbel liest vor — ein KI-Anruf je Lesung, nicht je Frame.

Mark, 11.11.2026: etwa alle 15 Minuten, solange Spieler da sind, schlägt sie
sich groß auf und liest eine Bibelstelle zur Lage vor. Bleibt, bis jemand
antippt. Fällt der Anbieter aus, nimmt sie einen bekannten Vers, damit die
Lesung nicht still ausbleibt.

Mark, 12.11.2026: keine frechen Kommentare mehr — nur der Vers selbst, gern
leicht umformuliert, damit er zur Lage passt, gern auch Altes Testament. Der
Text steht im aufgeschlagenen Buch, nicht in einer Tafel daneben.
"""

import logging
import random

from app.ki.client import KiFehler, generiere_json

log = logging.getLogger(__name__)

# Mark, 12.11.2026: zufällig alle 15–45 Minuten Anwesenheit.
LESEN_MIN_S = 15 * 60
LESEN_MAX_S = 45 * 60

# Zuletzt gelesene Stellen je Kampagne (Mark, 12.11.: „zweimal das gleiche
# Zitat“ — bei gleicher Lage nimmt die KI sonst gern denselben Vers). Nur im
# Speicher; nach einem Neustart darf sich höchstens einmal etwas wiederholen.
_ZULETZT: dict[str, list[str]] = {}
_MERKEN = 12

# Ein zufälliges Leitbild je Lesung, damit dieselbe Lage nicht immer denselben
# Vers ergibt.
_LEITBILDER = [
    "Weg und Wanderschaft", "Nacht und Wache", "Feinde und Bedrängnis", "Hoffnung", "Weisheit und Torheit",
    "Stadt und Mauern", "Wasser und Sturm", "Feuer und Prüfung", "Brot und Gastfreundschaft", "Gold und Gier",
    "Mut", "Geduld", "Hochmut und Fall", "Freundschaft und Treue", "Wüste und Durst", "Licht in der Finsternis",
    "Zorn und Vergebung", "Zeit und Vergänglichkeit", "Schutz und Zuflucht", "List und Klugheit",
]
_BUECHER = [
    "Psalmen", "Sprüche", "Prediger", "Hiob", "Jesaja", "Jeremia", "Klagelieder", "1. und 2. Mose", "Richter",
    "Samuel und Könige", "Ruth", "Daniel", "die kleinen Propheten", "Sirach oder Weisheit", "die Evangelien",
    "die Briefe des Paulus", "die Offenbarung",
]

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "stelle": {"type": "STRING"},
        "zitat": {"type": "STRING"},
    },
    "required": ["stelle", "zitat"],
}

_SYSTEM = (
    "Du bist Bärbel, eine alte Bibel, die einer Pen-and-Paper-Runde vorliest. "
    "Wähle zur geschilderten Lage genau EINE passende Bibelstelle — gern aus dem "
    "Alten Testament (Psalmen, Sprüche, Prediger, Hiob, Jesaja, die Bücher Mose, "
    "Könige, Richter …), aber auch Neues Testament ist erlaubt — und gib sie auf "
    "Deutsch im feierlichen, altertümlichen Ton der Lutherbibel wieder: wörtlich "
    "oder behutsam umformuliert, sodass sie auf die Lage passt. Anspielungen nur "
    "in biblischen Bildern (Wanderer, Wüste, Tal, Stadt, Feinde, Licht, "
    "Finsternis, Sturm, Brot). Kein Kommentar, kein Witz, keine Ironie, keine "
    "Anrede der Spieler, keine Namen, keine modernen Begriffe, keine Technik. "
    "Die zugrunde liegende Stelle muss echt sein. stelle ist „Buch Kapitel,Vers“ "
    "dieser Vorlage. zitat höchstens 260 Zeichen, ohne Anführungszeichen."
)

# Echte Verse (Luther) — nur der Notnagel, wenn kein Anbieter antwortet.
_FALLBACK = [
    {
        "stelle": "Psalm 23,4",
        "zitat": "Und ob ich schon wanderte im finstern Tal, fürchte ich kein Unglück; denn du bist bei mir, dein Stecken und Stab trösten mich.",
    },
    {
        "stelle": "Prediger 3,1",
        "zitat": "Ein jegliches hat seine Zeit, und alles Vorhaben unter dem Himmel hat seine Stunde.",
    },
    {
        "stelle": "Josua 1,9",
        "zitat": "Sei getrost und unverzagt. Lass dir nicht grauen und entsetze dich nicht; denn der Herr, dein Gott, ist mit dir in allem, was du tun wirst.",
    },
    {
        "stelle": "Psalm 121,1–2",
        "zitat": "Ich hebe meine Augen auf zu den Bergen. Woher kommt mir Hilfe? Meine Hilfe kommt vom Herrn, der Himmel und Erde gemacht hat.",
    },
    {
        "stelle": "Sprüche 16,9",
        "zitat": "Des Menschen Herz erdenkt sich seinen Weg; aber der Herr allein lenkt seinen Schritt.",
    },
    {
        "stelle": "Johannes 1,5",
        "zitat": "Und das Licht scheint in der Finsternis, und die Finsternis hat's nicht ergriffen.",
    },
    {
        "stelle": "Psalm 46,2",
        "zitat": "Gott ist unsre Zuversicht und Stärke, eine Hilfe in den großen Nöten, die uns getroffen haben.",
    },
    {
        "stelle": "Jesaja 40,31",
        "zitat": "Aber die auf den Herrn harren, kriegen neue Kraft, dass sie auffahren mit Flügeln wie Adler, dass sie laufen und nicht matt werden, dass sie wandeln und nicht müde werden.",
    },
    {
        "stelle": "Psalm 91,11",
        "zitat": "Denn er hat seinen Engeln befohlen über dir, dass sie dich behüten auf allen deinen Wegen.",
    },
    {
        "stelle": "Prediger 4,9",
        "zitat": "So ist's ja besser zwei als eins; denn sie genießen doch ihrer Arbeit wohl.",
    },
    {
        "stelle": "Sprüche 27,17",
        "zitat": "Ein Messer wetzt das andere und ein Mann den andern.",
    },
]


def _kurz(wert: object, laenge: int) -> str:
    text = " ".join(str(wert or "").split())
    return text[:laenge].rstrip()


def _sauber(roh: dict) -> dict | None:
    stelle = _kurz(roh.get("stelle"), 60)
    zitat = _kurz(roh.get("zitat"), 300).strip("„“\"»«")
    if len(stelle) < 3 or len(zitat) < 12:
        return None
    return {"stelle": stelle, "zitat": zitat}


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


def _schluessel(stelle: str) -> str:
    return "".join(stelle.lower().split()).replace("–", "-")


def _merken(campaign_id: str, lesung: dict) -> dict:
    liste = _ZULETZT.setdefault(campaign_id, [])
    liste.append(_schluessel(lesung["stelle"]))
    del liste[:-_MERKEN]
    return lesung


async def erzeugen(campaign_id: str, besitzer_id: str, anwesende_ids: list[str]) -> dict:
    """Eine Lesung. Bei Ausfall oder Wiederholung ein fester, zuletzt nicht
    gelesener Vers, nie eine erfundene Stelle."""
    zuletzt = _ZULETZT.get(campaign_id, [])
    try:
        text = await lage(campaign_id, besitzer_id, anwesende_ids)
        hinweis = (
            f"\nLeitbild diesmal: {random.choice(_LEITBILDER)}. "
            f"Am liebsten aus: {random.choice(_BUECHER)}."
        )
        if zuletzt:
            hinweis += "\nDiese Stellen hast du gerade gelesen, nimm eine andere: " + ", ".join(zuletzt[-8:])
        roh = await generiere_json(
            f"Lage der Runde, zu der du vorliest:\n{text}{hinweis}",
            _SYSTEM,
            _SCHEMA,
            campaign_id=campaign_id,
        )
        sauber = _sauber(roh if isinstance(roh, dict) else {})
        if sauber and _schluessel(sauber["stelle"]) not in zuletzt:
            return _merken(campaign_id, sauber)
        if sauber:
            log.info("Bärbel-Lesung wiederholt %s, fester Vers", sauber["stelle"])
    except (KiFehler, Exception):
        log.warning("Bärbel-Lesung ohne KI, fester Vers", exc_info=True)
    frei = [v for v in _FALLBACK if _schluessel(v["stelle"]) not in zuletzt] or _FALLBACK
    return _merken(campaign_id, dict(random.choice(frei)))
