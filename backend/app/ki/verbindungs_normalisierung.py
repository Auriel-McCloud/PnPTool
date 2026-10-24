"""Normalisierung von Verbindungstyp-Strings — Vorschlag + Anwenden.

Beziehungstyp ist bewusst Freitext (siehe entities/schemas.py::FilterOptionen),
deshalb sammeln sich über die Zeit Varianten fuer dasselbe Konzept an
("kennt", "kennt sich", "ist bekannt mit"). Der "✨ Kantentypen normalisieren"-
Knopf im Graph-Filter (24.10.2026, Marks Wunsch: das Ausblenden einzelner
Kantentypen beim Filtern lohnt sich erst, wenn nicht fünf Varianten von
"kennt" nebeneinander existieren) lässt die KI einmalig vorschlagen, welche
Typen sinngemäß dasselbe bedeuten. Mark bestätigt jede Gruppe einzeln (kein
Autocommit) — erst dann benennt eine Cypher-Query alle betroffenen Kanten um.
"""

from pydantic import BaseModel

from app.db.neo4j_driver import get_driver
from app.ki.client import generiere_json

_SYSTEM = (
    "Du hilfst, die Kantenbezeichnungen (Beziehungstypen) eines "
    "Beziehungsgraphen in einem Pen-and-Paper-Tool zu vereinheitlichen. "
    "Du bekommst eine Liste bereits verwendeter Typ-Strings mit ihrer "
    "Häufigkeit. Gruppiere NUR Typen, die inhaltlich dasselbe Konzept "
    "ausdrücken (z.B. \"kennt\" und \"kennt sich\" und \"ist bekannt mit\"), "
    "niemals Typen mit unterschiedlicher Bedeutung (z.B. \"kennt\" und "
    "\"feindet\" bleiben getrennt, auch \"Schuldet\" bleibt für sich). Für "
    "jede Gruppe mit mindestens zwei verschiedenen Strings schlägst du einen "
    "kurzen kanonischen Namen vor — bevorzuge dabei einen der bereits "
    "verwendeten Strings (den häufigsten oder kürzesten), erfinde nur im "
    "Zweifel einen neuen kurzen Begriff. Typen, die zu keiner sinnvollen "
    "Gruppe passen, lässt du komplett weg."
)

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "gruppen": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "kanonisch": {"type": "STRING"},
                    "varianten": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["kanonisch", "varianten"],
            },
        },
    },
    "required": ["gruppen"],
}


class NormalisierungsGruppe(BaseModel):
    kanonisch: str
    varianten: list[str]
    anzahl: int


class NormalisierungsVorschlaegeAntwort(BaseModel):
    gruppen: list[NormalisierungsGruppe] = []


class NormalisierungAnwendenInput(BaseModel):
    kanonisch: str
    varianten: list[str]


class NormalisierungAnwendenErgebnis(BaseModel):
    geaendert: int


async def verbindungstypen_mit_anzahl(campaign_id: str) -> list[dict]:
    """Jeder in der Kampagne verwendete Beziehungstyp mit Anzahl der Kanten."""
    driver = get_driver()
    query = """
        MATCH (a)-[r:VERBINDUNG]->(b)
        WHERE a.campaignId = $campaign_id AND b.campaignId = $campaign_id
          AND r.typ IS NOT NULL AND r.typ <> ''
        RETURN r.typ AS typ, count(r) AS anzahl
        ORDER BY typ
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(record) async for record in result]


async def vorschlaege(campaign_id: str) -> NormalisierungsVorschlaegeAntwort:
    """Lässt die KI Zusammenlegungs-Gruppen vorschlagen.

    Nur Varianten, die tatsächlich existieren, landen im Ergebnis — eine
    Gruppe mit weniger als zwei echten Varianten wäre keine Normalisierung,
    nur ein Umbenennen ins Leere, und wird herausgefiltert.
    """
    typen = await verbindungstypen_mit_anzahl(campaign_id)
    if len(typen) < 2:
        return NormalisierungsVorschlaegeAntwort(gruppen=[])

    anzahl_je_typ = {t["typ"]: t["anzahl"] for t in typen}
    zeilen = "\n".join(f"- {t['typ']} ({t['anzahl']}x)" for t in typen)
    prompt = f"Verwendete Beziehungstypen dieser Kampagne:\n{zeilen}"

    ergebnis = await generiere_json(prompt, _SYSTEM, _SCHEMA, campaign_id=campaign_id)
    bekannte_typen = set(anzahl_je_typ)

    gruppen: list[NormalisierungsGruppe] = []
    gesehen: set[str] = set()
    for roh in ergebnis.get("gruppen") or []:
        if not isinstance(roh, dict):
            continue
        kanonisch = (roh.get("kanonisch") or "").strip()
        varianten_roh = roh.get("varianten") or []
        varianten = sorted(
            {v.strip() for v in varianten_roh if isinstance(v, str) and v.strip() in bekannte_typen}
        )
        if not kanonisch or len(varianten) < 2:
            continue
        # Nur Varianten, die sich tatsächlich ändern würden, zählen als
        # "echte" Zusammenlegung — eine Gruppe aus nur dem kanonischen Namen
        # selbst wäre ein No-Op.
        aendernde = [v for v in varianten if v != kanonisch]
        if not aendernde:
            continue
        schluessel = kanonisch + "|" + ",".join(varianten)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        gesamt = sum(anzahl_je_typ.get(v, 0) for v in varianten)
        gruppen.append(NormalisierungsGruppe(kanonisch=kanonisch, varianten=varianten, anzahl=gesamt))

    return NormalisierungsVorschlaegeAntwort(gruppen=gruppen)


async def anwenden(campaign_id: str, kanonisch: str, varianten: list[str]) -> NormalisierungAnwendenErgebnis:
    """Benennt alle VERBINDUNG-Kanten mit typ in `varianten` auf `kanonisch` um."""
    ziel = kanonisch.strip()
    quell_typen = [v.strip() for v in varianten if v.strip() and v.strip() != ziel]
    if not ziel or not quell_typen:
        return NormalisierungAnwendenErgebnis(geaendert=0)

    driver = get_driver()
    query = """
        MATCH (a)-[r:VERBINDUNG]->(b)
        WHERE a.campaignId = $campaign_id AND b.campaignId = $campaign_id
          AND r.typ IN $quell_typen
        SET r.typ = $ziel
        RETURN count(r) AS geaendert
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, quell_typen=quell_typen, ziel=ziel)
        record = await result.single()
        return NormalisierungAnwendenErgebnis(geaendert=int(record["geaendert"]) if record else 0)
