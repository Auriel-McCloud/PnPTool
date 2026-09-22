"""Shop-Repository: Sortiment (VERKAUFT-Kanten + automatische Vorlagen) und
Standort. Kauf-Logik selbst liegt in routes.py, weil sie items/repository.py
und entities/repository.py orchestriert (Guthaben prüfen, Ware kopieren/
übergeben) — dieselbe Aufteilung wie bei kontakte/routes.py, das
mitteilungen_repo für den Seiteneffekt aufruft.

**Kein eigenes Node-Label.** Ein Händler ist ein `Person`-Knoten mit
`istHaendler=true` (siehe app/entities/schemas.py). Die VERKAUFT-Kante trägt
nur den Preis:

    (:Person {istHaendler:true})-[:VERKAUFT {preis: int}]->(:Gegenstand)

Zeigt sie auf eine **Vorlage** (istVorlage=true), ist die Ware unendlich
verfügbar — jeder Kauf kopiert sie (wie beim bestehenden Zuweisen-Endpunkt,
items/routes.py::zuweisen). Zeigt sie auf ein **einzigartiges, dem Händler
gehörendes Stück** (BESITZT-Kante vom Händler), ist sie nach dem ersten Kauf
weg — der Käufer übernimmt es per Besitzerwechsel, die VERKAUFT-Kante wird
gelöscht.
"""

from app.db.neo4j_driver import get_driver

_HAENDLER_FELDER = """
    h.id AS id, h.name AS name, h.bildUrl AS bildUrl, h.description AS beschreibung,
    h.spezialisierung AS spezialisierung,
    ort.id AS ortId, coalesce(ort.name, NULL) AS ortName,
    h.sichtbarkeit AS sichtbarkeit, h.sichtbarFuer AS sichtbarFuer
"""


def _decode_haendler(record: dict) -> dict:
    daten = dict(record)
    daten["bildUrl"] = daten.get("bildUrl") or ""
    daten["beschreibung"] = daten.get("beschreibung") or ""
    daten["spezialisierung"] = daten.get("spezialisierung") or []
    daten["sichtbarkeit"] = daten.get("sichtbarkeit") or "GM"
    daten["sichtbarFuer"] = daten.get("sichtbarFuer") or []
    return daten


async def liste(campaign_id: str) -> list[dict]:
    """Alle Händler dieser Kampagne, mit Standort — für Kachel-Übersicht und
    Kontaktliste. Schlank wie list_critter/list_ki (app/entities/repository.py),
    kein Charakterblatt."""
    driver = get_driver()
    query = f"""
        MATCH (h:Person {{campaignId: $campaign_id, istHaendler: true}})
        OPTIONAL MATCH (h)-[:BEFINDET_SICH_AN]->(ort:Ort)
        RETURN {_HAENDLER_FELDER}
        ORDER BY h.name
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_decode_haendler(dict(r)) async for r in result]


async def hole(campaign_id: str, haendler_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (h:Person {{id: $haendler_id, campaignId: $campaign_id, istHaendler: true}})
        OPTIONAL MATCH (h)-[:BEFINDET_SICH_AN]->(ort:Ort)
        RETURN {_HAENDLER_FELDER}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, haendler_id=haendler_id)
        record = await result.single()
        return _decode_haendler(dict(record)) if record else None


async def standort_setzen(campaign_id: str, haendler_id: str, ort_id: str | None) -> dict | None:
    """Setzt oder löst den Laden-Standort — dieselbe Kante wie bei Party
    (party/repository.py::aufenthaltsort_setzen), nur ohne Event als Ziel:
    ein Laden ist immer ein fester Ort, keine Szene."""
    driver = get_driver()
    async with driver.session() as session:
        if ort_id:
            query = """
                MATCH (h:Person {id: $haendler_id, campaignId: $campaign_id, istHaendler: true})
                MATCH (neu:Ort {id: $ort_id, campaignId: $campaign_id})
                OPTIONAL MATCH (h)-[alt:BEFINDET_SICH_AN]->()
                DELETE alt
                CREATE (h)-[:BEFINDET_SICH_AN]->(neu)
                RETURN h.id AS id
            """
            result = await session.run(query, campaign_id=campaign_id, haendler_id=haendler_id, ort_id=ort_id)
        else:
            query = """
                MATCH (h:Person {id: $haendler_id, campaignId: $campaign_id, istHaendler: true})
                OPTIONAL MATCH (h)-[alt:BEFINDET_SICH_AN]->()
                DELETE alt
                RETURN h.id AS id
            """
            result = await session.run(query, campaign_id=campaign_id, haendler_id=haendler_id)
        record = await result.single()
    return await hole(campaign_id, haendler_id) if record else None


# --- Sortiment --------------------------------------------------------------

_EXPLIZIT_FELDER = """
    g.id AS gegenstandId, g.name AS name, g.bildUrl AS bildUrl, g.typ AS typ,
    r.preis AS preis, g.istVorlage AS istVorlage
"""

_AUTOMATISCH_FELDER = """
    g.id AS gegenstandId, g.name AS name, g.bildUrl AS bildUrl, g.typ AS typ,
    g.preis AS preis, g.istVorlage AS istVorlage
"""


async def sortiment(campaign_id: str, haendler_id: str) -> list[dict]:
    """Explizit eingetragene Ware + automatischer Katalog-Bestand, dedupliziert.

    Automatisch = globale Vorlagen mit `automatischImShop=true`, gefiltert
    nach `spezialisierung` (leer = Gemischtwarenladen, zeigt alles) — Marks
    Vorgabe: "bei einem Waffenladen sollte es keinen Brokkoli geben". Eine
    Vorlage, die zusätzlich explizit eingetragen ist (z.B. mit Sonderpreis),
    erscheint nur einmal mit dem expliziten Preis.
    """
    driver = get_driver()
    async with driver.session() as session:
        explizit = await session.run(
            f"""
            MATCH (h:Person {{id: $haendler_id, campaignId: $campaign_id, istHaendler: true}})
                  -[r:VERKAUFT]->(g:Gegenstand)
            RETURN {_EXPLIZIT_FELDER}
            ORDER BY g.name
            """,
            campaign_id=campaign_id,
            haendler_id=haendler_id,
        )
        explizite_eintraege = [dict(r) async for r in explizit]
        explizite_ids = {e["gegenstandId"] for e in explizite_eintraege}

        automatisch = await session.run(
            """
            MATCH (h:Person {id: $haendler_id, campaignId: $campaign_id, istHaendler: true})
            MATCH (g:Gegenstand {
                campaignId: $campaign_id, istVorlage: true,
                automatischImShop: true, istEntwurf: false
            })
            WHERE size(h.spezialisierung) = 0 OR g.typ IN h.spezialisierung
            RETURN """ + _AUTOMATISCH_FELDER + """
            ORDER BY g.name
            """,
            campaign_id=campaign_id,
            haendler_id=haendler_id,
        )
        automatische_eintraege = [dict(r) async for r in automatisch if dict(r)["gegenstandId"] not in explizite_ids]

    ergebnis = [{**e, "automatisch": False} for e in explizite_eintraege]
    ergebnis += [{**e, "automatisch": True} for e in automatische_eintraege]
    for e in ergebnis:
        e["bildUrl"] = e.get("bildUrl") or ""
        e["preis"] = e.get("preis") or 0
    return ergebnis


async def effektiver_preis(campaign_id: str, haendler_id: str, gegenstand_id: str) -> int | None:
    """Der Preis, zu dem dieser Händler dieses Stück verkauft — oder None,
    wenn es nicht (mehr) in seinem Sortiment ist. Prüft explizit vor
    automatisch, weil ein expliziter Eintrag den automatischen überschreibt
    (siehe sortiment())."""
    fuer_sortiment = await sortiment(campaign_id, haendler_id)
    for eintrag in fuer_sortiment:
        if eintrag["gegenstandId"] == gegenstand_id:
            return eintrag["preis"]
    return None


async def verkauft_hinzufuegen(campaign_id: str, haendler_id: str, gegenstand_id: str, preis: int) -> bool:
    driver = get_driver()
    query = """
        MATCH (h:Person {id: $haendler_id, campaignId: $campaign_id, istHaendler: true})
        MATCH (g:Gegenstand {id: $gegenstand_id, campaignId: $campaign_id})
        MERGE (h)-[r:VERKAUFT]->(g)
        SET r.preis = $preis
        RETURN h.id AS id
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, haendler_id=haendler_id, gegenstand_id=gegenstand_id, preis=preis
        )
        return await result.single() is not None


async def verkauft_entfernen(campaign_id: str, haendler_id: str, gegenstand_id: str) -> bool:
    driver = get_driver()
    query = """
        MATCH (h:Person {id: $haendler_id, campaignId: $campaign_id, istHaendler: true})
              -[r:VERKAUFT]->(g:Gegenstand {id: $gegenstand_id})
        DELETE r
        RETURN count(r) AS geloescht
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, haendler_id=haendler_id, gegenstand_id=gegenstand_id)
        record = await result.single()
        return bool(record and record["geloescht"])
