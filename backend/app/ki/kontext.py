"""Kampagnen-Kontext für die KI.

Sammelt alle *freigegebenen* Entitäten einer Kampagne (also alles, was kein
Entwurf in der Ideenschmiede ist) zu einem kompakten Text. Genau diesen Blick
bekommt Gemini, wenn es einen Charakter, Ort oder Event erzeugt — so fügt sich
das Neue in die bestehende Welt ein, statt isoliert daneben zu stehen.

Absichtlich knapp: Jede Beschreibung wird gekappt, damit auch eine voll
ausgebaute Kampagne ins Kontextfenster passt.
"""

from app.db.neo4j_driver import get_driver

import json

_BESCHREIBUNG_MAX = 200


def tiptap_zu_text(roh: str) -> str:
    """TipTap-JSON (Richtext) zu Fließtext — oder Fließtext unverändert zurück.

    Manche Entitäten speichern ihre Beschreibung als TipTap-Dokument, andere
    als schlichten Text. Für den KI-Kontext zählt nur der reine Text.

    Öffentlich (kein führender Unterstrich): wird auch von der Wiki-
    Rechtschreib-/Grammatik-/Logikprüfung (app/ki/wiki_pruefung.py)
    gebraucht, um denselben Text zu bekommen wie der KI-Kontext.
    """
    if not roh or not roh.strip().startswith("{"):
        return (roh or "").strip()
    try:
        dokument = json.loads(roh)
    except (ValueError, TypeError):
        return roh.strip()

    texte: list[str] = []

    def sammle(knoten) -> None:
        if isinstance(knoten, dict):
            if isinstance(knoten.get("text"), str):
                texte.append(knoten["text"])
            for wert in knoten.values():
                sammle(wert)
        elif isinstance(knoten, list):
            for eintrag in knoten:
                sammle(eintrag)

    sammle(dokument)
    return " ".join(t for t in texte if t)


async def sammle_kontext(campaign_id: str) -> str:
    """Alle freigegebenen Entitäten einer Kampagne als lesbaren Textblock.

    Gibt einen leeren String zurück, wenn die Kampagne noch keine freigegebene
    Entität hat (dann erzeugt die KI eben „aus dem Nichts").
    """
    driver = get_driver()
    query = """
        MATCH (n {campaignId: $campaign_id})
        WHERE (n:Person OR n:Ort OR n:Event OR n:Fraktion OR n:Gegenstand OR n:WikiSeite)
          AND coalesce(n.istEntwurf, false) = false
        RETURN labels(n)[0] AS kind,
               coalesce(n.name, n.title, n.titel, '') AS name,
               coalesce(n.description, '') AS description,
               n.personType AS personType
        ORDER BY kind, name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        eintraege = [dict(record) async for record in result]

    if not eintraege:
        return ""

    zeilen: list[str] = []
    for e in eintraege:
        kind = e["kind"]
        name = (e["name"] or "").strip()
        beschreibung = tiptap_zu_text(e["description"])
        if len(beschreibung) > _BESCHREIBUNG_MAX:
            beschreibung = beschreibung[:_BESCHREIBUNG_MAX].rstrip() + "…"

        zusatz = ""
        if kind == "Person" and e.get("personType") == "PC":
            zusatz = " (Spielercharakter)"

        if beschreibung:
            zeilen.append(f"- {kind}: {name}{zusatz} — {beschreibung}")
        else:
            zeilen.append(f"- {kind}: {name}{zusatz}")

    return "\n".join(zeilen)


async def sammle_entitaeten(campaign_id: str) -> list[dict]:
    """Freigegebene Personen/Orte/Events/Fraktionen mit ID.

    Grundlage für die Auto-Verknüpfung (app/ki/auto_verknuepfung.py): die KI
    bekommt nur die Namen (kein Kontext-Fließtext), erkennt darin eine
    Erwähnung im Wiki-Text und liefert den exakten Namen zurück — die
    Zuordnung Name → ID passiert danach in Python (siehe
    ``auto_verknuepfung._passende_id``), nie durch die KI selbst.
    """
    driver = get_driver()
    query = """
        MATCH (n {campaignId: $campaign_id})
        WHERE (n:Person OR n:Ort OR n:Event OR n:Fraktion)
          AND coalesce(n.istEntwurf, false) = false
        RETURN n.id AS id, labels(n)[0] AS kind,
               coalesce(n.name, n.title, '') AS name
        ORDER BY kind, name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [dict(record) async for record in result]
