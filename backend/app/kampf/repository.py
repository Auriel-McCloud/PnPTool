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

import json
import uuid

from app.db.neo4j_driver import get_driver
from app.kampf.hot import am_zug_nach_faltung, falte_hot, hot_rueckschlag

# Reihenfolge bei Gleichstand (Zeile 58). Kleinere Zahl handelt zuerst.
KAMPFART_RANG = {"MATRIX": 0, "NAHKAMPF": 1, "FERNKAMPF": 2}

# istGross steht an der Person (Checkbox auf der Kachel). Die Rasse setzt nur den Startwert.
TEILNEHMER_FELDER = """
    t.id AS id, t.name AS name, t.initiative AS initiative, t.kampfart AS kampfart,
    t.notiz AS notiz, t.erledigt AS erledigt,
    t.zusatzzug AS zusatzzug, t.stammtId AS stammtId,
    t.ampel AS ampel, t.zusatzGenutzt AS zusatzGenutzt, t.setztAus AS setztAus,
    t.rundenVerbleibend AS rundenVerbleibend,
    t.hexQ AS hexQ, t.hexR AS hexR, t.hexDrehung AS hexDrehung,
    t.zugStartQ AS zugStartQ, t.zugStartR AS zugStartR,
    t.blickrichtung AS blickrichtung, coalesce(t.versteckt, false) AS versteckt,
    p.id AS personId, p.personType AS personType,
    p.bildUrl AS bildUrl, coalesce(p.istGross, false) AS istGross,
    p.istDrohne AS istDrohne, p.istFahrzeug AS istFahrzeug, p.istCritter AS istCritter,
    coalesce(head([(rasse:Rasse {ruleset: 'neotopia'}) WHERE rasse.name = p.rasse AND p.rasse <> '' AND NOT coalesce(rasse.geloescht, false) | rasse.rundumsicht]), false) AS rasseRundum,
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
    # Beschwörungs-Ki-Tama (30.10.2026): wie viele Runden dieser beschworene
    # Critter noch mitkämpft, bevor er automatisch verschwindet. None = kein
    # beschworener Teilnehmer, ganz normaler Teilnehmer ohne Zeitlimit.
    roh_runden = daten.get("rundenVerbleibend")
    daten["rundenVerbleibend"] = int(roh_runden) if roh_runden is not None else None
    for feld in ("hexQ", "hexR", "hexDrehung", "zugStartQ", "zugStartR"):
        roh = daten.get(feld)
        daten[feld] = int(roh) if roh is not None else None
    daten["bildUrl"] = daten.get("bildUrl") or ""
    daten["istGross"] = bool(daten.get("istGross"))
    daten["istDrohne"] = bool(daten.get("istDrohne"))
    daten["istFahrzeug"] = bool(daten.get("istFahrzeug"))
    daten["istCritter"] = bool(daten.get("istCritter"))
    roh_blick = daten.get("blickrichtung")
    daten["blickrichtung"] = int(roh_blick) % 6 if roh_blick is not None else 0
    daten["versteckt"] = bool(daten.get("versteckt"))
    daten["rundumsicht"] = bool(daten.get("rasseRundum")) or bool(daten.get("chromRundum"))
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
            RETURN k.id AS id, k.runde AS runde, k.amZug AS amZug, k.begonnen AS begonnen,
                   coalesce(k.verbrauchteBeschwoerungen, []) AS verbrauchteBeschwoerungen,
                   k.battlemapId AS battlemapId, k.sichtSpeicher AS sichtSpeicher
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

        # Drohnen/Fahrzeuge UND Critter sind technisch personType NPC, aber
        # keine geheimen Gegner — die eigene Sichtbarkeitsregel hängt am
        # Besitzer (Mark, 29.10.2026): PC-Besitzer -> Name sichtbar,
        # NPC-Besitzer -> verdeckt. Ein Critter-Besitz kann wie bei
        # `entities/repository.py::critter_besitzer` entweder über eine
        # manuelle BEGLEITET-Kante ODER über das Ki-Tama-Item kommen, das
        # `beschworenerCritterId` auf den Critter setzt — der Normalfall beim
        # automatischen Beschwören. Diese Abfrage kannte bisher nur die
        # BEGLEITET-Kante von Drohnen/Fahrzeugen und ignorierte Critter
        # komplett: ein frisch beschworener Critter (nur über das Ki-Tama
        # verknüpft, nie per BEGLEITET) zeigte Spielern/der Vorschau deshalb
        # "Unbekannte Person" statt seines echten Namens, obwohl er dem
        # eigenen Charakter gehört (Mark-Bugreport 31.10.2026).
        result = await session.run(
            """
            MATCH (d:Person {campaignId: $campaign_id})
            WHERE d.istDrohne = true OR d.istFahrzeug = true OR d.istCritter = true
            OPTIONAL MATCH (d)-[:BEGLEITET]->(p1:Person)
            OPTIONAL MATCH (p2:Person {campaignId: $campaign_id})-[:BESITZT]->
                (:Gegenstand {campaignId: $campaign_id, beschworenerCritterId: d.id})
            WITH d, coalesce(p1.id, p2.id) AS besitzerId
            WHERE besitzerId IS NOT NULL
            RETURN d.id AS drohneId, besitzerId AS riggerId
            """,
            campaign_id=campaign_id,
        )
        drohnen_besitzer = {r["drohneId"]: r["riggerId"] async for r in result}

        result = await session.run(
            """
            MATCH (p:Person {campaignId: $campaign_id})-[:BESITZT]->(g:Gegenstand)
            WHERE g.typ IN ['Cyberware', 'Bioware', 'Hexware']
              AND coalesce(g.verbaut, false)
              AND coalesce(g.rundumsicht, false)
              AND NOT coalesce(g.weggeworfen, false)
            RETURN DISTINCT p.id AS id
            """,
            campaign_id=campaign_id,
        )
        chrom_rundum = {r["id"] async for r in result}

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

    for t in teilnehmer:
        pid = t.get("personId")
        bid = t.get("begleiterId")
        t["besitzerId"] = (drohnen_besitzer.get(pid) if pid else None) or (
            begleiter_besitzer.get(bid) if bid else None
        )
        if pid and pid in chrom_rundum:
            t["rundumsicht"] = True

    roh_speicher = kampf.get("sichtSpeicher")
    try:
        speicher = json.loads(roh_speicher) if roh_speicher else {}
    except (json.JSONDecodeError, TypeError):
        speicher = {}

    return {
        "id": kampf["id"],
        "runde": kampf["runde"] or 1,
        # Nur fuer die serverseitige Filterung, nicht Teil der Antwort.
        "_rassen": rassen,
        "_npcIds": npc_ids,
        "_begleiterBesitzer": begleiter_besitzer,
        "_drohnenBesitzer": drohnen_besitzer,
        "_sichtSpeicher": speicher if isinstance(speicher, dict) else {},
        # Kennung des Teilnehmers, der gerade handelt. Kennung statt Position,
        # weil sich die Reihenfolge ändern kann (jemand kommt dazu) — eine
        # Position zeigte danach auf jemand anderen.
        "amZug": am_zug,
        "teilnehmer": teilnehmer,
        "verbrauchteBeschwoerungen": list(kampf["verbrauchteBeschwoerungen"] or []),
        "battlemapId": kampf.get("battlemapId"),
        "_campaignId": campaign_id,
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
                   coalesce(p.matrixHotRunde, 0) AS matrixHotRunde,
                   d.name AS hotDrohneName
            """,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        record = await result.single()
    if record is None:
        return {"hotDrohneId": None, "hotDrohneRunde": 0, "matrixHot": False, "matrixHotRunde": 0, "hotDrohneName": None}
    drohne_id = record["hotDrohneId"] or None
    return {
        "hotDrohneId": drohne_id,
        "hotDrohneRunde": int(record["hotDrohneRunde"] or 0),
        "matrixHot": bool(record["matrixHot"]),
        "matrixHotRunde": int(record["matrixHotRunde"] or 0),
        "hotDrohneName": record["hotDrohneName"] if drohne_id else None,
    }


async def hot_schreiben(
    campaign_id: str,
    person_id: str,
    *,
    hot_drohne_id: str | None,
    hot_runde: int,
    matrix_hot: bool | None = None,
    matrix_hot_runde: int | None = None,
) -> None:
    """Schreibt die Drohnen-Wahl. Matrix-Felder nur, wenn ausdrücklich gesetzt."""
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
            SET p.hotDrohneId = CASE WHEN $hot_id = '' THEN null ELSE $hot_id END,
                p.hotDrohneRunde = $runde,
                p.matrixHot = CASE WHEN $matrix_gesetzt THEN $matrix_hot ELSE coalesce(p.matrixHot, false) END,
                p.matrixHotRunde = CASE WHEN $matrix_runde_gesetzt THEN $matrix_hot_runde ELSE coalesce(p.matrixHotRunde, 0) END
            """,
            campaign_id=campaign_id,
            person_id=person_id,
            hot_id=hot_drohne_id or "",
            runde=int(hot_runde),
            matrix_gesetzt=matrix_hot is not None,
            matrix_hot=bool(matrix_hot),
            matrix_runde_gesetzt=matrix_hot_runde is not None,
            matrix_hot_runde=int(matrix_hot_runde or 0),
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
    await matrix_hot_loeschen(campaign_id)
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


async def matrix_hot_loeschen(campaign_id: str) -> None:
    """Kampf vorbei: kein Knopf mehr, also auch kein hängendes Hot.

    Sonst träfe die Matrix ihn im nächsten Kampf, bevor die Bleiben-Frage
    überhaupt drankommt.
    """
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (p:Person {campaignId: $campaign_id})
            WHERE coalesce(p.matrixHot, false)
            SET p.matrixHot = false, p.matrixHotRunde = 0
            """,
            campaign_id=campaign_id,
        )


async def beschwoerung_verbrauchen(campaign_id: str, item_id: str) -> None:
    """Merkt am laufenden Kampf, dass dieses Ki-Tama seinen einen Ruf verbraucht hat.

    Die Liste hängt am Kampf-Knoten, nicht am Critter: wenn die Runden ablaufen,
    verschwindet der Teilnehmer, der Ruf bleibt aber weg. Ein neuer Kampf
    (beginne löscht den Knoten) setzt das Limit zurück.
    """
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            SET k.verbrauchteBeschwoerungen =
                CASE
                    WHEN $item_id IN coalesce(k.verbrauchteBeschwoerungen, [])
                    THEN k.verbrauchteBeschwoerungen
                    ELSE coalesce(k.verbrauchteBeschwoerungen, []) + [$item_id]
                END
            """,
            campaign_id=campaign_id,
            item_id=item_id,
        )


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
                ampel: 0, zusatzGenutzt: 0, setztAus: false,
                rundenVerbleibend: $runden_verbleibend
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
            runden_verbleibend=daten.get("rundenVerbleibend"),
        )
    await platziere_unplatzierte(campaign_id)
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
            WITH k
            MATCH (k)-[:KAEMPFT]->(t:KampfTeilnehmer)
            SET t.zugStartQ = null, t.zugStartR = null
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
        # Beschwörungs-Ki-Tama (30.10.2026): Runden-Zähler aller beschworenen
        # Critter tickt beim Rundenwechsel runter, wer bei 0 ankommt,
        # verschwindet automatisch aus dem Tracker.
        await tick_beschwoerungen(campaign_id)
        from app.kampf.matrix_store import tick as matrix_tick
        await matrix_tick(campaign_id, kampf["runde"] + 1)
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


async def tick_beschwoerungen(campaign_id: str) -> None:
    """Beschwörungs-Ki-Tama (30.10.2026): EIN Rundenwechsel = EIN Tick für
    jeden beschworenen Critter im Kampf. Wer dabei bei 0 ankommt, verlässt
    automatisch den Initiative-Tracker — Mark: "das Level der Beschwörung
    gibt an, wie viele Runden der Critter am Kampf teilnimmt". Läuft wie
    `kuehle_alle_ab` beim Rundenwechsel in `weiter()`, kein eigener Knopf.
    """
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer)
            WHERE t.rundenVerbleibend IS NOT NULL AND t.rundenVerbleibend > 0
            SET t.rundenVerbleibend = t.rundenVerbleibend - 1
            """,
            campaign_id=campaign_id,
        )
        await session.run(
            """
            MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer)
            WHERE t.rundenVerbleibend = 0
            DETACH DELETE t
            """,
            campaign_id=campaign_id,
        )


async def setze_karte(campaign_id: str, battlemap_id: str | None) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            SET k.battlemapId = $karte
            """,
            campaign_id=campaign_id,
            karte=battlemap_id,
        )
    if battlemap_id:
        await platziere_unplatzierte(campaign_id)
    return await hole(campaign_id)


async def setze_sicht(campaign_id: str, speicher: dict) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (k:Kampf {campaignId: $campaign_id})
            SET k.sichtSpeicher = $roh
            """,
            campaign_id=campaign_id,
            roh=json.dumps(speicher),
        )


async def setze_blick(campaign_id: str, teilnehmer_id: str, blick: int) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer {id: $id})
            SET t.blickrichtung = $blick
            """,
            campaign_id=campaign_id,
            id=teilnehmer_id,
            blick=int(blick) % 6,
        )
    return await hole(campaign_id)


async def setze_versteckt(campaign_id: str, teilnehmer_id: str, versteckt: bool) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer {id: $id})
            SET t.versteckt = $versteckt
            """,
            campaign_id=campaign_id,
            id=teilnehmer_id,
            versteckt=bool(versteckt),
        )
    return await hole(campaign_id)


async def setze_token_position(
    campaign_id: str,
    teilnehmer_id: str,
    q: int,
    r: int,
    drehung: int,
    *,
    zug_start: bool,
) -> dict | None:
    driver = get_driver()
    async with driver.session() as session:
        if zug_start:
            await session.run(
                """
                MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer {id: $id})
                SET t.hexQ = $q, t.hexR = $r, t.hexDrehung = $drehung,
                    t.zugStartQ = coalesce(t.zugStartQ, t.hexQ, $q),
                    t.zugStartR = coalesce(t.zugStartR, t.hexR, $r)
                """,
                campaign_id=campaign_id,
                id=teilnehmer_id,
                q=q,
                r=r,
                drehung=drehung,
            )
        else:
            await session.run(
                """
                MATCH (:Kampf {campaignId: $campaign_id})-[:KAEMPFT]->(t:KampfTeilnehmer {id: $id})
                SET t.hexQ = $q, t.hexR = $r, t.hexDrehung = $drehung
                """,
                campaign_id=campaign_id,
                id=teilnehmer_id,
                q=q,
                r=r,
                drehung=drehung,
            )
    return await hole(campaign_id)


def _belegt_karte(teilnehmer: list[dict], ausser_id: str | None = None) -> dict[tuple[int, int], str]:
    from app.battlemap.hex import y_felder

    belegt: dict[tuple[int, int], str] = {}
    for t in teilnehmer:
        if t.get("zusatzzug"):
            continue
        if ausser_id and t["id"] == ausser_id:
            continue
        if t.get("hexQ") is None or t.get("hexR") is None:
            continue
        for feld in y_felder(t["hexQ"], t["hexR"], gross=bool(t.get("istGross")), drehung=int(t.get("hexDrehung") or 0)):
            belegt[feld] = t["id"]
    return belegt


async def platziere_unplatzierte(campaign_id: str) -> None:
    """Tokens ohne Hex an die Spawn-Felder der angehängten Karte."""
    from app.battlemap import repository as karten_repo
    from app.battlemap.hex import spawn_platz

    kampf = await hole(campaign_id)
    if kampf is None or not kampf.get("battlemapId"):
        return
    karte = await karten_repo.holen(campaign_id, kampf["battlemapId"])
    if karte is None:
        return
    besitzer = kampf.get("_drohnenBesitzer") or {}
    for t in kampf["teilnehmer"]:
        if t.get("zusatzzug") or t.get("hexQ") is not None:
            continue
        person_id = t.get("personId")
        rigger = besitzer.get(person_id) if person_id else None
        neben = None
        if rigger:
            haupt = next(
                (
                    x
                    for x in kampf["teilnehmer"]
                    if x.get("personId") == rigger and not x.get("zusatzzug") and x.get("hexQ") is not None
                ),
                None,
            )
            if haupt:
                neben = (haupt["hexQ"], haupt["hexR"])
        ist_pc = t.get("personType") == "PC" and not t.get("istDrohne") and not t.get("istFahrzeug") and not t.get("istCritter")
        if neben is not None:
            start = neben
        elif ist_pc and karte.get("spawnPcQ") is not None:
            start = (karte["spawnPcQ"], karte["spawnPcR"])
        elif karte.get("spawnNpcQ") is not None:
            start = (karte["spawnNpcQ"], karte["spawnNpcR"])
        elif karte.get("spawnPcQ") is not None:
            start = (karte["spawnPcQ"], karte["spawnPcR"])
        else:
            continue
        belegt = _belegt_karte(kampf["teilnehmer"])
        platz = spawn_platz(start[0], start[1], gross=bool(t.get("istGross")), belegt=belegt)
        if platz is None:
            continue
        q, r, dreh = platz
        await setze_token_position(campaign_id, t["id"], q, r, dreh, zug_start=False)
        t["hexQ"], t["hexR"], t["hexDrehung"] = q, r, dreh

