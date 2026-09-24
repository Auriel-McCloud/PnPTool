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

import uuid
from datetime import datetime, timezone

_HAENDLER_FELDER = """
    h.id AS id, h.name AS name, h.bildUrl AS bildUrl, h.description AS beschreibung,
    h.spezialisierung AS spezialisierung, h.vertriebsart AS vertriebsart,
    ort.id AS ortId, coalesce(ort.name, NULL) AS ortName,
    h.sichtbarkeit AS sichtbarkeit, h.sichtbarFuer AS sichtbarFuer
"""


def _decode_haendler(record: dict) -> dict:
    daten = dict(record)
    daten["bildUrl"] = daten.get("bildUrl") or ""
    daten["beschreibung"] = daten.get("beschreibung") or ""
    daten["spezialisierung"] = daten.get("spezialisierung") or []
    daten["vertriebsart"] = daten.get("vertriebsart") or "PHYSISCH"
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
    r.preis AS preis, g.istVorlage AS istVorlage,
    coalesce(r.rabattProzent, 0) AS rabattProzent, coalesce(r.rabattHinweis, '') AS rabattHinweis
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
    ergebnis += [{**e, "automatisch": True, "rabattProzent": 0, "rabattHinweis": ""} for e in automatische_eintraege]
    for e in ergebnis:
        e["bildUrl"] = e.get("bildUrl") or ""
        e["preis"] = e.get("preis") or 0
    return ergebnis


async def effektiver_preis(campaign_id: str, haendler_id: str, gegenstand_id: str) -> int | None:
    """Der tatsächliche Kaufpreis (Grundpreis minus Rabatt), zu dem dieser
    Händler dieses Stück verkauft — oder None, wenn es nicht (mehr) in
    seinem Sortiment ist. Prüft explizit vor automatisch, weil ein
    expliziter Eintrag den automatischen überschreibt (siehe sortiment())."""
    fuer_sortiment = await sortiment(campaign_id, haendler_id)
    for eintrag in fuer_sortiment:
        if eintrag["gegenstandId"] == gegenstand_id:
            rabatt = eintrag.get("rabattProzent") or 0
            return eintrag["preis"] * (100 - rabatt) // 100
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


async def rabatt_setzen(
    campaign_id: str, haendler_id: str, gegenstand_id: str, prozent: int, hinweis: str
) -> bool:
    """Sonderangebot auf einen EXPLIZITEN Sortiment-Eintrag (Rabatt braucht
    eine VERKAUFT-Kante als Träger, siehe schemas.py::SortimentEintrag).
    prozent=0 nimmt den Rabatt wieder weg."""
    driver = get_driver()
    query = """
        MATCH (h:Person {id: $haendler_id, campaignId: $campaign_id, istHaendler: true})
              -[r:VERKAUFT]->(g:Gegenstand {id: $gegenstand_id})
        SET r.rabattProzent = $prozent, r.rabattHinweis = $hinweis
        RETURN count(r) AS gesetzt
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            haendler_id=haendler_id,
            gegenstand_id=gegenstand_id,
            prozent=prozent,
            hinweis=hinweis,
        )
        record = await result.single()
        return bool(record and record["gesetzt"])


# --- Bestellungen (digitaler Shop) ------------------------------------------
#
# Ein digitaler Kauf (Vertriebsart DIGITAL) übergibt die Ware nicht sofort —
# stattdessen entsteht eine Bestellung, die SL löst die Lieferung manuell per
# Knopf aus (kein fester Termin, Marks Vorgabe 24.09.2026). Eigener
# Node-Typ statt Wiederverwendung von :Verhandlung — eine Bestellung hat
# keinen Annehmen/Ablehnen-Schritt (Kapital ist beim Bestellen schon weg),
# nur einen Status offen->geliefert.

_BESTELLUNG_FELDER = """
    b.id AS id, b.haendlerId AS haendlerId, b.haendlerName AS haendlerName,
    b.kaeuferPersonId AS kaeuferPersonId, b.gegenstandId AS gegenstandId,
    b.gegenstandName AS gegenstandName, b.preis AS preis, b.status AS status,
    b.bestelltAm AS bestelltAm, b.geliefertAm AS geliefertAm
"""


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decode_bestellung(record: dict) -> dict:
    b = dict(record)
    b["status"] = b.get("status") or "OFFEN"
    b["geliefertAm"] = b.get("geliefertAm") or ""
    return b


async def bestellung_anlegen(
    campaign_id: str,
    haendler_id: str,
    haendler_name: str,
    kaeufer_person_id: str,
    gegenstand_id: str,
    gegenstand_name: str,
    preis: int,
) -> dict:
    driver = get_driver()
    query = f"""
        MATCH (c:Campaign {{id: $campaign_id}})
        CREATE (b:Bestellung {{
            id: $bid, campaignId: $campaign_id,
            haendlerId: $haendler_id, haendlerName: $haendler_name,
            kaeuferPersonId: $kaeufer_person_id,
            gegenstandId: $gegenstand_id, gegenstandName: $gegenstand_name,
            preis: $preis, status: 'OFFEN', bestelltAm: $jetzt, geliefertAm: ''
        }})
        CREATE (c)-[:HAT_BESTELLUNG]->(b)
        RETURN {_BESTELLUNG_FELDER}
    """
    async with driver.session() as session:
        result = await session.run(
            query,
            campaign_id=campaign_id,
            bid=str(uuid.uuid4()),
            haendler_id=haendler_id,
            haendler_name=haendler_name,
            kaeufer_person_id=kaeufer_person_id,
            gegenstand_id=gegenstand_id,
            gegenstand_name=gegenstand_name,
            preis=preis,
            jetzt=_jetzt(),
        )
        record = await result.single()
        return _decode_bestellung(dict(record))


async def offene_bestellungen(campaign_id: str) -> list[dict]:
    """Alle offenen Bestellungen dieser Kampagne — für die SL-Liste mit dem
    'Jetzt liefern'-Knopf (alle Händler zusammen, nicht pro Händler gescoped,
    da die SL global den Überblick behalten soll)."""
    driver = get_driver()
    query = f"""
        MATCH (b:Bestellung {{campaignId: $campaign_id, status: 'OFFEN'}})
        RETURN {_BESTELLUNG_FELDER}
        ORDER BY b.bestelltAm ASC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        return [_decode_bestellung(dict(r)) async for r in result]


async def bestellungen_fuer_person(campaign_id: str, person_id: str) -> list[dict]:
    """Eigene Bestellungen (offen + geliefert) — für die Spieler-Ansicht im
    Online-Shop, damit sichtbar ist, was noch unterwegs ist."""
    driver = get_driver()
    query = f"""
        MATCH (b:Bestellung {{campaignId: $campaign_id, kaeuferPersonId: $person_id}})
        RETURN {_BESTELLUNG_FELDER}
        ORDER BY b.bestelltAm DESC
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [_decode_bestellung(dict(r)) async for r in result]


async def bestellung_hole(campaign_id: str, bestellung_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (b:Bestellung {{id: $bid, campaignId: $campaign_id}})
        RETURN {_BESTELLUNG_FELDER}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, bid=bestellung_id)
        record = await result.single()
        return _decode_bestellung(dict(record)) if record else None


async def bestellung_liefern(campaign_id: str, bestellung_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (b:Bestellung {{id: $bid, campaignId: $campaign_id, status: 'OFFEN'}})
        SET b.status = 'GELIEFERT', b.geliefertAm = $jetzt
        RETURN {_BESTELLUNG_FELDER}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, bid=bestellung_id, jetzt=_jetzt())
        record = await result.single()
        return _decode_bestellung(dict(record)) if record else None
