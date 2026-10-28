"""Kampfmodus — die Initiativliste, die alle am Tisch sehen.

Ein Kampf je Kampagne. Die Reihenfolge ergibt sich aus dem Regelblatt
(Zeilen 57-59):

* **Initiative = Geistesschärfe + Geschicklichkeit + Cyberware-Modifikator.**
* Bei gleicher Initiative gilt **Matrixnutzer vor Nahkämpfer vor Fernkämpfer**.
* **Angesagt wird in umgekehrter Reihenfolge** — wer zuletzt handelt, sagt
  zuerst an; dadurch kann die schnellste Person auf alles reagieren. Gewürfelt
  wird dann in der richtigen Reihenfolge.

Die Teilnehmer sind eigene Knoten statt einer Liste am Kampf: Neo4j kann keine
Listen aus Objekten als Eigenschaft, und ein Teilnehmer verweist ohnehin auf
eine Person oder einen Begleiter.
"""

import uuid

from app.db.neo4j_driver import get_driver
from app.kampf.hot import am_zug_nach_faltung, falte_hot, hot_rueckschlag

# Reihenfolge bei Gleichstand (Zeile 58). Kleinere Zahl handelt zuerst.
KAMPFART_RANG = {"MATRIX": 0, "NAHKAMPF": 1, "FERNKAMPF": 2}

TEILNEHMER_FELDER = """
    t.id AS id, t.name AS name, t.initiative AS initiative, t.kampfart AS kampfart,
    t.notiz AS notiz, t.erledigt AS erledigt,
    t.zusatzzug AS zusatzzug, t.stammtId AS stammtId,
    t.ampel AS ampel, t.zusatzGenutzt AS zusatzGenutzt, t.setztAus AS setztAus,
    p.id AS personId, p.personType AS personType,
    b.id AS begleiterId
"""


def _decode(record: dict) -> dict:
    daten = dict(record)
    daten["name"] = daten.get("name") or ""
    daten["initiative"] = daten.get("initiative") or 0
    daten["kampfart"] = daten.get("kampfart") or "NAHKAMPF"
    daten["notiz"] = daten.get("notiz") or ""
    daten["erledigt"] = bool(daten.get("erledigt"))
    # Zusatzzug aus dem Reflex-Booster: ein zweiter Eintrag derselben Person,
    # der verschwindet, sobald er dran war.
    daten["zusatzzug"] = bool(daten.get("zusatzzug"))
    daten["stammtId"] = daten.get("stammtId")
    # Ueberhitzung (Stufe 3): 0-3 wie eine Ampel.
    daten["ampel"] = int(daten.get("ampel") or 0)
    daten["zusatzGenutzt"] = int(daten.get("zusatzGenutzt") or 0)
    # Nach einem misslungenen Paralysewurf: naechste Runde aussetzen.
    daten["setztAus"] = bool(daten.get("setztAus"))
    return daten


def sortiere(teilnehmer: list[dict]) -> list[dict]:
    """Handlungsreihenfolge: hohe Initiative zuerst, dann nach Kampfart.

    Ein Zusatzzug aus dem Reflex-Booster reiht sich ganz normal ein — genau
    das ist der Sinn: er kommt meist später, weil ohne Boosterbonus
    gewürfelt wurde. Bei Gleichstand steht er hinter dem Stammeintrag, sonst
    handelte die Zusatzaktion vor der eigentlichen.
    """
    return sorted(
        teilnehmer,
        key=lambda t: (
            -t["initiative"],
            KAMPFART_RANG.get(t["kampfart"], 9),
            1 if t.get("zusatzzug") else 0,
            t["name"].lower(),
        ),
    )


async def hole(campaign_id: str) -> dict | None:
    """Der laufende Kampf samt Teilnehmern, oder None."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            RETURN k.id AS id, k.runde AS runde, k.amZug AS amZug, k.begonnen AS begonnen
            """,
            campaign_id=campaign_id,
        )
        kampf = await result.single()
        if kampf is None:
            return None

        result = await session.run(
            f"""
            MATCH (k:Kampf {{id: $kampf_id}})-[:KAEMPFT]->(t:KampfTeilnehmer)
            OPTIONAL MATCH (t)-[:IST]->(p:Person)
            OPTIONAL MATCH (t)-[:IST]->(b:Begleiter)
            RETURN {TEILNEHMER_FELDER}
            """,
            kampf_id=kampf["id"],
        )
        teilnehmer = sortiere([_decode(r) async for r in result])

        # Fuer die Spielersicht: Rasse je NPC (ergibt "Unbekannter Ork") und
        # wem ein Begleiter gehoert. In derselben Sitzung, damit die Liste
        # nicht aus zwei Zeitpunkten zusammengesetzt wird.
        result = await session.run(
            """
            MATCH (p:Person {campaignId: $campaign_id})
            RETURN p.id AS id, p.rasse AS rasse, p.personType AS personType
            """,
            campaign_id=campaign_id,
        )
        rassen: dict[str, str] = {}
        npc_ids: set[str] = set()
        async for r in result:
            rassen[r["id"]] = r["rasse"] or ""
            if r["personType"] == "NPC":
                npc_ids.add(r["id"])

        result = await session.run(
            """
            MATCH (b:Begleiter {campaignId: $campaign_id})-[:BEGLEITET]->(p:Person)
            RETURN b.id AS begleiterId, p.id AS besitzerId
            """,
            campaign_id=campaign_id,
        )
        begleiter_besitzer = {r["begleiterId"]: r["besitzerId"] async for r in result}

        result = await session.run(
            """
            MATCH (r:Person {campaignId: $campaign_id})
            WHERE coalesce(r.hotDrohneId, '') <> ''
            MATCH (d:Person {id: r.hotDrohneId, campaignId: $campaign_id})
            RETURN r.id AS riggerId, d.id AS drohneId, d.name AS drohneName
            """,
            campaign_id=campaign_id,
        )
        links = {r["riggerId"]: (r["drohneId"], r["drohneName"] or "") async for r in result}

    vorher = teilnehmer
    teilnehmer = falte_hot(vorher, links)
    teilnehmer = sortiere(teilnehmer)
    am_zug = am_zug_nach_faltung(kampf["amZug"], vorher, teilnehmer, links)

    return {
        "id": kampf["id"],
        "runde": kampf["runde"] or 1,
        # Nur fuer die serverseitige Filterung, nicht Teil der Antwort.
        "_rassen": rassen,
        "_npcIds": npc_ids,
        "_begleiterBesitzer": begleiter_besitzer,
        # Kennung des Teilnehmers, der gerade handelt. Kennung statt Position,
        # weil sich die Reihenfolge ändern kann (jemand kommt dazu) — eine
        # Position zeigte danach auf jemand anderen.
        "amZug": am_zug,
        "teilnehmer": teilnehmer,
    }


async def hot_lesen(campaign_id: str, person_id: str) -> dict:
    """Hot-Zustand einer Person. Fehlende Felder sind „nicht Hot“."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
            OPTIONAL MATCH (d:Person {id: p.hotDrohneId, campaignId: $campaign_id})
            RETURN coalesce(p.hotDrohneId, '') AS hotDrohneId,
                   coalesce(p.hotDrohneRunde, 0) AS hotDrohneRunde,
                   coalesce(p.matrixHot, false) AS matrixHot,
                   d.name AS hotDrohneName
            """,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        record = await result.single()
    if record is None:
        return {"hotDrohneId": None, "hotDrohneRunde": 0, "matrixHot": False, "hotDrohneName": None}
    drohne_id = record["hotDrohneId"] or None
    return {
        "hotDrohneId": drohne_id,
        "hotDrohneRunde": int(record["hotDrohneRunde"] or 0),
        "matrixHot": bool(record["matrixHot"]),
        "hotDrohneName": record["hotDrohneName"] if drohne_id else None,
    }


async def hot_schreiben(
    campaign_id: str,
    person_id: str,
    *,
    hot_drohne_id: str | None,
    hot_runde: int,
    matrix_hot: bool | None = None,
) -> None:
    """Schreibt die Drohnen-Wahl. matrix_hot nur, wenn ausdrücklich gesetzt."""
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
            SET p.hotDrohneId = CASE WHEN $hot_id = '' THEN null ELSE $hot_id END,
                p.hotDrohneRunde = $runde,
                p.matrixHot = CASE WHEN $matrix_gesetzt THEN $matrix_hot ELSE coalesce(p.matrixHot, false) END
            """,
            campaign_id=campaign_id,
            person_id=person_id,
            hot_id=hot_drohne_id or "",
            runde=int(hot_runde),
            matrix_gesetzt=matrix_hot is not None,
            matrix_hot=bool(matrix_hot),
        )


async def hot_rueckschlag_buchen(campaign_id: str, drohne_id: str, hp_menge: int) -> list[dict]:
    """Bucht den halben Schlagschaden auf jeden Rigger, der diese Drohne Hot steuert.

    Leer, wenn niemand Hot drin ist oder nichts angekommen ist. Der Rigger
    selbst wird nicht getroffen, falls die Kennung aus Versehen auf ihn zeigt.
    """
    schlag = hot_rueckschlag(hp_menge)
    if schlag <= 0:
        return []
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (r:Person {campaignId: $campaign_id})
            WHERE r.hotDrohneId = $drohne_id AND r.id <> $drohne_id
            SET r.schadenSchlag = coalesce(r.schadenSchlag, 0) + $schlag
            RETURN r.id AS riggerId, r.name AS riggerName, $schlag AS schlag
            """,
            campaign_id=campaign_id,
            drohne_id=drohne_id,
            schlag=schlag,
        )
        return [
            {"riggerId": r["riggerId"], "riggerName": r["riggerName"] or "", "schlag": int(r["schlag"])}
            async for r in result
        ]


async def hot_rigger_id(campaign_id: str, drohne_id: str) -> str | None:
    """Wer diese Drohne gerade Hot steuert, oder None."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (r:Person {campaignId: $campaign_id})
            WHERE r.hotDrohneId = $drohne_id AND r.id <> $drohne_id
            RETURN r.id AS id
            LIMIT 1
            """,
            campaign_id=campaign_id,
            drohne_id=drohne_id,
        )
        record = await result.single()
        return record["id"] if record else None


async def dumpshock(campaign_id: str, rigger_id: str) -> None:
    """Verbindung tot: Hot lösen und den Rigger für den Rest der Runde aussetzen."""
    await hot_schreiben(campaign_id, rigger_id, hot_drohne_id=None, hot_runde=0)
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer)-[:IST]->(p:Person {id: $rigger_id})
            WHERE NOT coalesce(t.zusatzzug, false)
            SET t.setztAus = true
            """,
            campaign_id=campaign_id,
            rigger_id=rigger_id,
        )


async def angreifer_person_id(campaign_id: str) -> str | None:
    """Wer ist gerade dran? Grundlage für die automatische Angreifer-
    Zuordnung im Ereignisprotokoll (Marks Vorgabe, docs/wiki/entities/
    ereignisprotokoll.md, Abschnitt KampfLogEintrag): "wenn mein Spieler
    dran ist und ein NPC Leben verliert, hat der Spieler diesen NPC
    verletzt — und umgekehrt". Liefert None, wenn kein Kampf läuft, niemand
    am Zug ist, oder der Teilnehmer am Zug kein Person-Knoten ist (z.B. ein
    reiner Begleiter ohne eigene Person, oder Umweltschaden).
    """
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            WHERE k.amZug IS NOT NULL
            MATCH (k)-[:KAEMPFT]->(t:KampfTeilnehmer {id: k.amZug})-[:IST]->(p:Person)
            RETURN p.id AS personId
            """,
            campaign_id=campaign_id,
        )
        record = await result.single()
        return record["personId"] if record else None


async def beginne(campaign_id: str) -> dict:
    """Startet einen Kampf. Ein laufender wird dabei ersetzt."""
    await beende(campaign_id)
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})
            CREATE (k:Kampf {id: $id, campaignId: $campaign_id, runde: 1, amZug: null})
            CREATE (c)-[:HAT_KAMPF]->(k)
            """,
            campaign_id=campaign_id,
            id=str(uuid.uuid4()),
        )
    return await hole(campaign_id)


async def beende(campaign_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            OPTIONAL MATCH (k)-[:KAEMPFT]->(t:KampfTeilnehmer)
            DETACH DELETE k, t
            RETURN count(k) AS weg
            """,
            campaign_id=campaign_id,
        )
        record = await result.single()
        return bool(record and record["weg"])


async def teilnehmer_hinzu(campaign_id: str, daten: dict) -> dict | None:
    driver = get_driver()
    neue_id = str(uuid.uuid4())
    # Verweis auf Person oder Begleiter, je nachdem was mitkommt. Beides
    # optional: ein namenloser Wachmann braucht keinen Knoten dahinter.
    async with driver.session() as session:
        await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            CREATE (t:KampfTeilnehmer {
                id: $id, name: $name, initiative: $initiative,
                kampfart: $kampfart, notiz: $notiz, erledigt: false,
                zusatzzug: $zusatzzug, stammtId: $stammt_id,
                ampel: 0, zusatzGenutzt: 0, setztAus: false
            })
            CREATE (k)-[:KAEMPFT]->(t)
            WITH t
            OPTIONAL MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
            FOREACH (_ IN CASE WHEN p IS NULL THEN [] ELSE [1] END | CREATE (t)-[:IST]->(p))
            WITH t
            OPTIONAL MATCH (b:Begleiter {id: $begleiter_id, campaignId: $campaign_id})
            FOREACH (_ IN CASE WHEN b IS NULL THEN [] ELSE [1] END | CREATE (t)-[:IST]->(b))
            """,
            campaign_id=campaign_id,
            id=neue_id,
            name=daten["name"],
            initiative=daten["initiative"],
            kampfart=daten["kampfart"],
            notiz=daten.get("notiz") or "",
            person_id=daten.get("personId"),
            begleiter_id=daten.get("begleiterId"),
            zusatzzug=bool(daten.get("zusatzzug")),
            stammt_id=daten.get("stammtId"),
        )
    return await hole(campaign_id)


async def teilnehmer_aendern(campaign_id: str, teilnehmer_id: str, daten: dict) -> dict | None:
    geaendert = {k: v for k, v in daten.items() if v is not None}
    if not geaendert:
        return await hole(campaign_id)
    driver = get_driver()
    setzen = ", ".join(f"t.{f} = ${f}" for f in geaendert)
    async with driver.session() as session:
        await session.run(
            f"""
            MATCH (:Kampf {{campaignId: $campaign_id}})-[:KAEMPFT]->(t:KampfTeilnehmer {{id: $id}})
            SET {setzen}
            """,
            campaign_id=campaign_id,
            id=teilnehmer_id,
            **geaendert,
        )
    return await hole(campaign_id)


async def teilnehmer_entfernen(campaign_id: str, teilnehmer_id: str) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer {id: $id})
            DETACH DELETE t
            """,
            campaign_id=campaign_id,
            id=teilnehmer_id,
        )
    return await hole(campaign_id)


async def setze_am_zug(campaign_id: str, teilnehmer_id: str | None, runde: int | None = None) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            SET k.amZug = $am_zug
            FOREACH (_ IN CASE WHEN $runde IS NULL THEN [] ELSE [1] END | SET k.runde = $runde)
            """,
            campaign_id=campaign_id,
            am_zug=teilnehmer_id,
            runde=runde,
        )
    return await hole(campaign_id)


async def weiter(campaign_id: str) -> dict | None:
    """Einen Zug weiterrücken; am Ende der Liste beginnt die nächste Runde.

    Dabei zwei Dinge aus dem Reflex-Booster:

    * Der eben abgehandelte **Zusatzeintrag verschwindet** (Mark: "der Eintrag
      verschwindet sobald er dran war").
    * Beim Rundenwechsel **kühlt die Ampel** aller ab, die in dieser Runde
      keine Zusatzaktion genutzt haben.
    """
    kampf = await hole(campaign_id)
    if kampf is None or not kampf["teilnehmer"]:
        return kampf

    reihenfolge = [t["id"] for t in kampf["teilnehmer"]]
    if kampf["amZug"] not in reihenfolge:
        # Kampfbeginn oder der bisher Handelnde ist ausgeschieden
        return await setze_am_zug(campaign_id, reihenfolge[0])

    aktueller = next(t for t in kampf["teilnehmer"] if t["id"] == kampf["amZug"])
    naechster = reihenfolge.index(kampf["amZug"]) + 1
    naechste_id = reihenfolge[naechster] if naechster < len(reihenfolge) else reihenfolge[0]
    rundenwechsel = naechster >= len(reihenfolge)

    # Der Zusatzeintrag hat gehandelt und wird gelöscht. Erst danach den
    # Zeiger setzen, sonst zeigt er auf einen Knoten, den es nicht mehr gibt.
    if aktueller.get("zusatzzug"):
        await entferne_zusatzzug(campaign_id, aktueller["id"])
        # Die Reihenfolge hat sich verkürzt — neu bestimmen, wer dran ist.
        if naechste_id == aktueller["id"]:
            neu_geladen = await hole(campaign_id)
            if not neu_geladen or not neu_geladen["teilnehmer"]:
                return neu_geladen
            naechste_id = neu_geladen["teilnehmer"][0]["id"]

    if rundenwechsel:
        # Wer in dieser Runde eine Zusatzaktion genutzt hat, kühlt nicht ab.
        genutzt = {t["stammtId"] for t in kampf["teilnehmer"] if t.get("zusatzzug") and t.get("stammtId")}
        await kuehle_alle_ab(campaign_id, genutzt)
        return await setze_am_zug(campaign_id, naechste_id, runde=kampf["runde"] + 1)

    return await setze_am_zug(campaign_id, naechste_id)


async def entferne_zusatzzug(campaign_id: str, teilnehmer_id: str) -> None:
    """Löscht einen Zusatzeintrag, nachdem er gehandelt hat.

    Mark: *"wichtig ist die Logik das der Eintrag verschwindet sobald er dran
    war"*. Nur Zusatzeinträge, niemals ein Stammeintrag.
    """
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer {id: $id})
            WHERE coalesce(t.zusatzzug, false)
            DETACH DELETE t
            """,
            campaign_id=campaign_id,
            id=teilnehmer_id,
        )


async def setze_ampel(campaign_id: str, teilnehmer_id: str, stand: int) -> dict | None:
    """Setzt den Überhitzungsstand (0-3) eines Teilnehmers."""
    return await teilnehmer_aendern(campaign_id, teilnehmer_id, {"ampel": stand})


async def kuehle_alle_ab(campaign_id: str, ausser_ids: set[str]) -> None:
    """Senkt die Ampel aller, die in dieser Runde KEINE Zusatzaktion nutzten.

    Mark: *"wenn er eine Runde aussetzt verschwindet wieder ein Punkt"*.
    Läuft beim Rundenwechsel, damit niemand von Hand nachhalten muss.
    """
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer)
            WHERE NOT t.id IN $ausser AND coalesce(t.ampel, 0) > 0
            SET t.ampel = t.ampel - 1
            """,
            campaign_id=campaign_id,
            ausser=list(ausser_ids),
        )
