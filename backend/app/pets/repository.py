"""Neo4j-Zugriff der Critter-Pets.

Die Pet-Art steht als `petArt` direkt am Critter-`Person`-Knoten (kein
eigener Knoten) — oder an einem `Gegenstand` (Bärbel, 11.11.2026: „Bärbel
wäre ja ein Gegenstand und kein Critter“). Beim Gegenstand ist Besitzer, wer
ihn per `BESITZT` hat; ausgerüstet muss er nicht sein („Bärbel lässt sich
nicht einsperren“) — nur weggeworfen oder in einer verschlossenen Kiste
(auch verschachtelt) fliegt sie nicht. Häufchen sind kleine eigene Knoten, weil sie liegen
bleiben, wenn das Pet weiterzieht — auch über einen Neustart hinweg.
Wo das Pet gerade herumläuft, hält dagegen nur der Server im Speicher
(siehe motor.py): nach einem Neustart fängt es einfach beim Besitzer an.
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver
import random

from app.pets.logic import (
    FALLENDE_SPUREN,
    HAEUFCHEN_MAX,
    TIPPS_MAX,
    TIPPS_MIN,
    faehigkeiten,
    risse,
    stufe,
    waechst,
)


async def pets_der_kampagne(campaign_id: str) -> list[dict]:
    """Alle Critter mit Pet-Art, die an einen Spielercharakter gebunden sind.

    `mitglieder` = Spielercharaktere der Party des Besitzers, inklusive
    Besitzer. Ohne Party nur der Besitzer selbst.
    """
    query = """
        MATCH (c:Person {campaignId: $campaign_id, istCritter: true})-[:BEGLEITET]->(b:Person {personType: 'PC'})
        WHERE c.petArt IS NOT NULL AND c.petArt <> ''
        OPTIONAL MATCH (b)-[:MITGLIED_VON]->(:Party)<-[:MITGLIED_VON]-(m:Person {personType: 'PC'})
        RETURN c.id AS id, coalesce(c.alias, c.name) AS name, c.petArt AS art,
               b.id AS besitzerId, b.name AS besitzerName,
               collect(DISTINCT m.id) AS mitglieder,
               c.petStufe AS petStufe, c.petTipps AS petTipps, c.petTippsNoetig AS petTippsNoetig,
               c.petEpStart AS petEpStart,
               coalesce(c.erfahrung, 0) + coalesce(c.extraEP, 0) AS epEigen
        UNION
        MATCH (b:Person {campaignId: $campaign_id, personType: 'PC'})-[:BESITZT]->(c:Gegenstand {campaignId: $campaign_id})
        WHERE c.petArt IS NOT NULL AND c.petArt <> ''
          AND NOT coalesce(c.weggeworfen, false)
          AND NOT EXISTS {
              MATCH (c)-[:LIEGT_IN*1..8]->(kiste:Gegenstand)
              WHERE kiste.schlossArt IN ['passwort', 'schluessel', 'spiel']
                AND NOT coalesce(kiste.aufgeschlossen, false)
          }
        // Gehört er mehreren (Party-Safehouse), fliegt er beim ersten los.
        WITH c, b ORDER BY b.id
        WITH c, head(collect(b)) AS b
        OPTIONAL MATCH (b)-[:MITGLIED_VON]->(:Party)<-[:MITGLIED_VON]-(m:Person {personType: 'PC'})
        RETURN c.id AS id, c.name AS name, c.petArt AS art,
               b.id AS besitzerId, b.name AS besitzerName,
               collect(DISTINCT m.id) AS mitglieder,
               null AS petStufe, null AS petTipps, null AS petTippsNoetig, null AS petEpStart, 0 AS epEigen
    """
    kampagnen_ep = await _kampagnen_ep(campaign_id)
    async with get_driver().session() as session:
        result = await session.run(query, campaign_id=campaign_id)
        pets = []
        async for r in result:
            d = dict(r)
            mitglieder = set(d["mitglieder"] or [])
            mitglieder.add(d["besitzerId"])
            d["mitglieder"] = sorted(mitglieder)
            _stufe_ergaenzen(d, kampagnen_ep)
            pets.append(d)
        return pets


async def _kampagnen_ep(campaign_id: str) -> int:
    from app.campaigns.repository import get_einstellungen

    return int((await get_einstellungen(campaign_id)).get("kampagnenEP", 0) or 0)


def _stufe_ergaenzen(d: dict, kampagnen_ep: int) -> None:
    """Wachstum aus den Rohfeldern: `stufe`, `kann`, `risse` (nur beim Ei).
    EP wie im Charakterbogen: eigene + Kampagnen- + Extra-EP."""
    ep_gesamt = int(d.pop("epEigen", 0) or 0) + kampagnen_ep
    st, gewachsen = stufe(d["art"], d.pop("petStufe", None), ep_gesamt, d.pop("petEpStart", None))
    tipps = int(d.pop("petTipps", 0) or 0)
    noetig = int(d.pop("petTippsNoetig", 0) or 0)
    d["stufe"] = st
    d["kann"] = faehigkeiten(d["art"], st, gewachsen)
    d["risse"] = risse(tipps, noetig) if st == "ei" else 0


# Critter (Person mit istCritter) oder Gegenstand — dieselbe Route für beide.
_PET_TRAEGER = """
        MATCH (c {id: $critter_id, campaignId: $campaign_id})
        WHERE (c:Person AND c.istCritter = true) OR c:Gegenstand
"""


async def pets_pausiert(campaign_id: str) -> bool:
    """Keine Pets unterwegs: in den Kampagnenoptionen abgedreht oder es läuft
    ein Kampf (Mark, 11.11.2026: „grundsätzlich will ich nicht, dass die Pets
    im Kampf rumlaufen“ — sie kommen nach dem Kampf von selbst wieder)."""
    from app.campaigns.repository import get_einstellungen

    if not (await get_einstellungen(campaign_id)).get("petsAktiv", True):
        return True
    async with get_driver().session() as session:
        result = await session.run(
            "MATCH (k:Kampf {campaignId: $campaign_id}) RETURN count(k) AS n", campaign_id=campaign_id
        )
        r = await result.single()
        return bool(r and r["n"])


async def art_lesen(campaign_id: str, critter_id: str) -> dict | None:
    query = _PET_TRAEGER + """
        RETURN c.id AS id, c.petArt AS art
    """
    async with get_driver().session() as session:
        result = await session.run(query, campaign_id=campaign_id, critter_id=critter_id)
        r = await result.single()
        return dict(r) if r else None


async def art_setzen(campaign_id: str, critter_id: str, art: str | None) -> dict | None:
    """Pet-Art setzen. Bekommt ein Critter zum ersten Mal einen Drachen, fängt
    der als Ei an (Mark, 12.11.2026: „klein wäre er wieder, wenn er mit einem
    neuen Critter verbunden wird“). Wechsel zwischen Drachen-Farben oder
    Abwählen behält die Stufe; Bestandsdrachen (ohne `petStufe`) bleiben groß."""
    query = _PET_TRAEGER + """
        WITH c, c.petArt AS vorher
        SET c.petArt = $art
        WITH c, vorher
        FOREACH (_ IN CASE WHEN c:Person AND $waechst AND c.petStufe IS NULL
                                AND NOT coalesce(vorher, '') IN $wachsende THEN [1] ELSE [] END |
            SET c.petStufe = 'ei', c.petTipps = 0, c.petTippsNoetig = $noetig, c.petEpStart = null)
        RETURN c.id AS id, c.petArt AS art
    """
    from app.pets.logic import WACHSENDE_ARTEN

    async with get_driver().session() as session:
        result = await session.run(query, campaign_id=campaign_id, critter_id=critter_id, art=art,
                                   waechst=waechst(art), wachsende=list(WACHSENDE_ARTEN),
                                   noetig=random.randint(TIPPS_MIN, TIPPS_MAX))
        r = await result.single()
        return dict(r) if r else None


async def ei_tippen(campaign_id: str, critter_id: str) -> bool:
    """Einmal aufs Ei getippt. True = geschlüpft. Ab dann zählen EP fürs
    Wachsen — `petEpStart` merkt sich die EP des Critters in diesem Moment."""
    kampagnen_ep = await _kampagnen_ep(campaign_id)
    query = """
        MATCH (c:Person {id: $critter_id, campaignId: $campaign_id, istCritter: true})
        WHERE c.petStufe = 'ei'
        SET c.petTipps = coalesce(c.petTipps, 0) + 1
        WITH c, c.petTipps >= coalesce(c.petTippsNoetig, 1) AS fertig
        FOREACH (_ IN CASE WHEN fertig THEN [1] ELSE [] END |
            SET c.petStufe = 'geschluepft',
                c.petEpStart = coalesce(c.erfahrung, 0) + coalesce(c.extraEP, 0) + $kampagnen_ep)
        RETURN fertig
    """
    async with get_driver().session() as session:
        result = await session.run(query, campaign_id=campaign_id, critter_id=critter_id, kampagnen_ep=kampagnen_ep)
        r = await result.single()
        return bool(r and r["fertig"])


async def haeufchen_liste(campaign_id: str, person_id: str) -> list[dict]:
    query = """
        MATCH (h:PetHaeufchen {campaignId: $campaign_id, personId: $person_id})
        RETURN h.id AS id, h.petId AS petId, h.x AS x, h.y AS y, h.erstellt AS erstellt,
               coalesce(h.art, 'haeufchen') AS art
        ORDER BY h.erstellt
    """
    async with get_driver().session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [dict(r) async for r in result]


async def haeufchen_anlegen(campaign_id: str, person_id: str, pet_id: str, x: float, y: float,
                            art: str = "haeufchen") -> None:
    """Legt eine Spur (Häufchen/Brandfleck) auf diesen Bildschirm; die älteste
    derselben Art fällt bei Überlauf weg. Bestandsknoten ohne `art` sind Häufchen."""
    query = """
        CREATE (:PetHaeufchen {id: $id, campaignId: $campaign_id, personId: $person_id,
                               petId: $pet_id, x: $x, y: $y, erstellt: $erstellt, art: $art})
        WITH 1 AS _
        MATCH (h:PetHaeufchen {campaignId: $campaign_id, personId: $person_id})
        WHERE coalesce(h.art, 'haeufchen') = $art
        WITH h ORDER BY h.erstellt DESC
        WITH collect(h) AS alle
        UNWIND alle[$max..] AS zuviel
        DETACH DELETE zuviel
    """
    async with get_driver().session() as session:
        await session.run(
            query,
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            person_id=person_id,
            pet_id=pet_id,
            x=x,
            y=y,
            erstellt=datetime.now(timezone.utc).isoformat(),
            max=HAEUFCHEN_MAX,
            art=art,
        )


async def haeufchen_verschieben(campaign_id: str, person_id: str, haeufchen_id: str, x: float, y: float) -> None:
    """Häufchen ist vom Element gefallen, auf dem es lag (Mark, 11.11.2026) —
    neue Bildschirmposition merken. Nur Häufchen und Bärbels Seiten (die segeln
    zu Boden), nur auf dem eigenen Bildschirm; Brandflecken sitzen am Display
    und bewegen sich nie."""
    query = """
        MATCH (h:PetHaeufchen {id: $id, campaignId: $campaign_id, personId: $person_id})
        WHERE coalesce(h.art, 'haeufchen') IN $arten
        SET h.x = $x, h.y = $y
    """
    async with get_driver().session() as session:
        await session.run(query, id=haeufchen_id, campaign_id=campaign_id, person_id=person_id, x=x, y=y,
                          arten=list(FALLENDE_SPUREN))


async def haeufchen_weg(campaign_id: str, person_id: str, haeufchen_id: str) -> None:
    """Nur vom eigenen Bildschirm — fremde Häufchen kann man nicht wegmachen."""
    query = """
        MATCH (h:PetHaeufchen {id: $id, campaignId: $campaign_id, personId: $person_id})
        DETACH DELETE h
    """
    async with get_driver().session() as session:
        await session.run(query, id=haeufchen_id, campaign_id=campaign_id, person_id=person_id)


async def haeufchen_lesen(campaign_id: str, person_id: str, haeufchen_id: str) -> dict | None:
    query = """
        MATCH (h:PetHaeufchen {id: $id, campaignId: $campaign_id, personId: $person_id})
        RETURN h.id AS id, coalesce(h.art, 'haeufchen') AS art
    """
    async with get_driver().session() as session:
        result = await session.run(query, id=haeufchen_id, campaign_id=campaign_id, person_id=person_id)
        r = await result.single()
        return dict(r) if r else None


async def napf_futter_verbrauchen(campaign_id: str, person_id: str, item_id: str) -> str | None:
    """Ein Stück Tierfutter aus dem eigenen Besitz. Rückgabe: Fehlertext oder
    None. Wie beim Schlucken: Stapel −1, ein Einzelstück wandert in den
    Mülleimer der SL (nichts wird gelöscht)."""
    from app.items import repository as items_repo

    item = await items_repo.get_gegenstand(campaign_id, item_id)
    if item is None:
        return "Gegenstand nicht gefunden"
    if item.get("weggeworfen"):
        return "Das Futter ist schon aufgebraucht."
    if not item.get("istTierfutter"):
        return "Das ist kein Tierfutter."
    if await items_repo.get_owner_person_id(campaign_id, item_id) != person_id:
        return "Gegenstand nicht gefunden"
    if item.get("hatMenge"):
        menge = int(item.get("menge") or 0)
        if menge <= 0:
            return "Der Futtersack ist leer."
        await items_repo.update_gegenstand(campaign_id, item_id, {"menge": menge - 1})
    else:
        await items_repo.wegwerfen(campaign_id, item_id, "verfüttert")
    return None


async def critter_heilen(campaign_id: str, critter_id: str, schlag: int) -> None:
    """Gefressen: Schlagschaden des Critters sinkt (nie unter 0). Bärbel ist ein
    Gegenstand und frisst nicht — trifft deshalb nur Person-Critter."""
    query = """
        MATCH (c:Person {id: $id, campaignId: $campaign_id, istCritter: true})
        WITH c, coalesce(c.schadenSchlag, 0) - $schlag AS rest
        SET c.schadenSchlag = CASE WHEN rest < 0 THEN 0 ELSE rest END
    """
    async with get_driver().session() as session:
        await session.run(query, id=critter_id, campaign_id=campaign_id, schlag=schlag)


async def zutraulichkeit_erhoehen(campaign_id: str, person_id: str, pet_id: str, plus: int,
                                  abklingen_s: float = 0.0) -> int | None:
    """Kante (Spieler-PC)-[:ZUTRAULICH {wert}]->(Pet-Träger: Critter oder Gegenstand).
    Mit `abklingen_s` zählt es nur, wenn der letzte zählende Schub so lange her ist
    (Streicheln: höchstens +1 alle 5 Minuten je Spieler). Rückgabe: neuer Wert."""
    query = """
        MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
        MATCH (t {id: $pet_id, campaignId: $campaign_id})
        WHERE t:Gegenstand OR (t:Person AND t.istCritter = true)
        MERGE (p)-[z:ZUTRAULICH]->(t)
        ON CREATE SET z.wert = 0
        WITH z, ($abklingen_s <= 0 OR $jetzt - coalesce(z.zuletzt, 0) >= $abklingen_s) AS zaehlt
        SET z.wert = coalesce(z.wert, 0) + CASE WHEN zaehlt THEN $plus ELSE 0 END,
            z.zuletzt = CASE WHEN zaehlt THEN $jetzt ELSE z.zuletzt END
        RETURN z.wert AS wert
    """
    async with get_driver().session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id, pet_id=pet_id, plus=plus,
                                   abklingen_s=float(abklingen_s),
                                   jetzt=datetime.now(timezone.utc).timestamp())
        r = await result.single()
        return int(r["wert"]) if r else None
