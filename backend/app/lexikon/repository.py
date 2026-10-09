"""Automatische Entdeckung fürs Spieler-Lexikon — Erreichbarkeits-BFS.

Siehe docs/wiki/entities/spieler-lexikon.md für die vollständige
Design-Begründung. Kurzfassung: ein PC entdeckt Orte/Events/Fraktionen/
Critter/Gewächse/story-relevante Gegenstände automatisch, sobald sie über
Struktur- und Beziehungskanten erreichbar sind (max. 7 Hops) — das schaltet
nur die *Existenz* frei (Name+Bild im Lexikon), nicht die Beschreibung (die
bleibt weiter über das bestehende `sichtbarkeit`-Feld gesteuert, wie gehabt
nach einem erfolgreichen Wissenswurf von Hand gesetzt). Eine SL-geheime
VERBINDUNG oder ein für diesen PC nicht sichtbarer Knoten blockiert die
Traversierung komplett, auch innerhalb der erlaubten Tiefe — nichts leakt
durch ein Geheimnis hindurch.

Berechnung läuft in Python (BFS über einen einmal geladenen Graphen), nicht
in Cypher — dieselbe Wahl wie beim bestehenden Beziehungsgraph
(graph/routes.py::_neighborhood): die Pro-Kante-Sichtbarkeitslogik lässt
sich in Cypher nur schwer während einer variablen Pfadlänge auswerten, und
bei diesem Datenvolumen (ein Spieltisch pro Kampagne) ist Python-BFS über
den ganzen Graphen mühelos schnell genug.

Discovery ist rein additiv: ein einmal entdeckter Knoten bleibt entdeckt,
auch wenn er laut aktuellem Graphen nicht mehr erreichbar wäre (z. B. löst
sich eine Party wieder auf) — "einmal gewusst" wird nicht wieder vergessen.
"""

from collections import deque

from app.db.neo4j_driver import get_driver
from app.entities.visibility import is_visible_to

# Zählt Kanten (nicht Knoten) ab der eigenen Person — Marks Beispielkette
# PC->Party->Event->Ort->NPCParty->NPC->MacGuffin hat 7 Stationen inklusive
# der eigenen Person, 6 Kanten dazwischen; hier bewusst grosszügig auf 7
# Kanten gesetzt statt 6, damit die genannte Kette sicher noch durchkommt.
MAX_TIEFE = 7

# Reine Durchgangsknoten: tragen keine fuer Spieler relevante Sichtbarkeit,
# werden nie selbst als entdeckt gespeichert, blockieren die Traversierung
# aber auch nie.
_DURCHGANG_LABELS = {"Party"}

# Strukturkanten sind immer durchlaessig: sie tragen selbst keine eigene
# Sichtbarkeit, anders als VERBINDUNG. Richtung spielt fuer die
# Erreichbarkeit keine Rolle (siehe _erreichbare_ids, Kanten werden
# symmetrisch indiziert).
_STRUKTUR_KANTEN = ["MITGLIED_VON", "BEFINDET_SICH_AN", "LEBT_IN", "BESITZT", "BETREIBT", "VERKAUFT"]

# Kategorie-Zuordnung fuers Frontend-Burgermenue (Welt/Fauna/Flora/Objekte).
_KATEGORIE_VON_LABEL = {
    "Ort": "welt",
    "Event": "welt",
    "Fraktion": "welt",
    "Person": "fauna",  # nur Critter werden ueberhaupt als entdeckbar erfasst, siehe _ist_entdeckbar
    "Gewaechs": "flora",
    "Gegenstand": "objekte",
}


def _ist_entdeckbar(info: dict) -> bool:
    """Welche Knoten ueberhaupt als Lexikon-Eintrag gelten.

    Party ist reiner Durchgang. Ein normaler NPC/PC ist kein Lexikon-Eintrag
    (keine UI-Kategorie dafuer) — nur Critter zaehlen als "Fauna". Ein
    Gegenstand zaehlt nur, wenn er story-relevant ist (MacGuffins, nicht die
    08/15-Pistole).
    """
    label = info["label"]
    if label in ("Ort", "Event", "Fraktion", "Gewaechs"):
        return True
    if label == "Person":
        return bool(info.get("istCritter"))
    if label == "Gegenstand":
        return bool(info.get("storyRelevant"))
    return False


async def _graph_laden(campaign_id: str) -> tuple[dict[str, dict], list[dict]]:
    """Lädt alle für die Traversierung relevanten Knoten und Kanten einmal.

    Nicht-story-relevante Gegenstände werden gar nicht erst geladen — sie
    sind in diesem Projekt immer Blätter (nichts hängt strukturell von
    ihnen ab) und würden nur unnötig das Inventar jeder Person mitschleppen.
    """
    driver = get_driver()
    async with driver.session() as session:
        knoten_result = await session.run(
            """
            MATCH (n)
            WHERE n.campaignId = $campaign_id
              AND (
                n:Ort OR n:Event OR n:Fraktion OR n:Party OR n:Gewaechs OR n:Person
                OR (n:Gegenstand AND n.storyRelevant = true)
              )
            RETURN n.id AS id, labels(n)[0] AS label,
                   n.sichtbarkeit AS sichtbarkeit, n.sichtbarFuer AS sichtbarFuer,
                   n.istCritter AS istCritter
            """,
            campaign_id=campaign_id,
        )
        knoten = {r["id"]: dict(r) async for r in knoten_result}

        kanten_result = await session.run(
            """
            MATCH (a)-[r]->(b)
            WHERE a.campaignId = $campaign_id AND b.campaignId = $campaign_id
              AND (type(r) IN $struktur_typen OR type(r) = 'VERBINDUNG')
            RETURN a.id AS von, b.id AS zu, type(r) AS typ,
                   r.sichtbarkeit AS sichtbarkeit, r.sichtbarFuer AS sichtbarFuer
            """,
            campaign_id=campaign_id,
            struktur_typen=_STRUKTUR_KANTEN,
        )
        kanten = [dict(r) async for r in kanten_result]
    return knoten, kanten


def _adjazenz(kanten: list[dict]) -> dict[str, list[dict]]:
    """Ungerichtete Nachbarschaftsliste — Erreichbarkeit zaehlt in beide
    Richtungen, nur die Anzeige-Richtung der Kante bleibt in der DB fix."""
    adj: dict[str, list[dict]] = {}
    for kante in kanten:
        adj.setdefault(kante["von"], []).append(kante)
        adj.setdefault(kante["zu"], []).append({**kante, "von": kante["zu"], "zu": kante["von"]})
    return adj


def erreichbare_ids(
    start_id: str,
    knoten: dict[str, dict],
    kanten: list[dict],
    person_id: str,
    *, max_tiefe: int = MAX_TIEFE,
) -> set[str]:
    """BFS ab `start_id` (die eigene Person), respektiert Sichtbarkeit.

    Reine Funktion ohne DB-Zugriff — so direkt mit konstruierten
    Beispielgraphen testbar (siehe tests/test_lexikon.py).
    """
    adj = _adjazenz(kanten)

    def _knoten_sichtbar(node_id: str) -> bool:
        info = knoten.get(node_id)
        if info is None:
            return False
        if info["label"] in _DURCHGANG_LABELS:
            return True
        return is_visible_to(info.get("sichtbarkeit") or "GM", info.get("sichtbarFuer") or [], "PLAYER", person_id)

    entdeckt: set[str] = set()
    besucht = {start_id}
    frontier = deque([(start_id, 0)])
    while frontier:
        node_id, tiefe = frontier.popleft()
        if tiefe >= max_tiefe:
            continue
        for kante in adj.get(node_id, ()):
            nachbar = kante["zu"]
            if nachbar in besucht:
                continue
            # VERBINDUNG traegt eine eigene Sichtbarkeit — SL-geheime oder
            # fuer diesen PC nicht freigegebene Verbindungen blockieren die
            # Traversierung an dieser Stelle komplett.
            if kante["typ"] == "VERBINDUNG" and not is_visible_to(
                kante.get("sichtbarkeit") or "GM", kante.get("sichtbarFuer") or [], "PLAYER", person_id
            ):
                continue
            # Ein fuer diesen PC nicht sichtbarer Knoten blockiert ebenfalls
            # komplett: weder wird er entdeckt, noch wird durch ihn hindurch
            # weiterzaehlt.
            if not _knoten_sichtbar(nachbar):
                continue
            besucht.add(nachbar)
            info = knoten.get(nachbar, {})
            if _ist_entdeckbar(info):
                entdeckt.add(nachbar)
            frontier.append((nachbar, tiefe + 1))
    return entdeckt


def naehe_raenge(start_id: str | None, knoten: dict[str, dict], kanten: list[dict]) -> dict[str, int]:
    """Topologische Distanz ab einem Ausgangsknoten (z.B. der aktuelle
    Aufenthaltsort der Party) — rein strukturell, ohne Sichtbarkeitsgate,
    weil hier nur bereits entdeckte Eintraege einsortiert werden. Fehlt ein
    Ausgangspunkt (Party gerade nirgendwo), bekommt alles denselben Rang und
    die Sortierung faellt auf Alphabetisch zurueck."""
    if start_id is None or start_id not in knoten:
        return {}
    adj = _adjazenz(kanten)
    raenge = {start_id: 0}
    frontier = deque([(start_id, 0)])
    while frontier:
        node_id, dist = frontier.popleft()
        for kante in adj.get(node_id, ()):
            nachbar = kante["zu"]
            if nachbar in raenge:
                continue
            raenge[nachbar] = dist + 1
            frontier.append((nachbar, dist + 1))
    return raenge


async def _bereits_entdeckt(campaign_id: str, person_id: str) -> set[str]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:ENTDECKT]->(z)
            RETURN z.id AS id
            """,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        return {r["id"] async for r in result}


async def neu_berechnen_fuer_person(campaign_id: str, person_id: str) -> int:
    """Berechnet Erreichbarkeit neu und legt fehlende ENTDECKT-Kanten an.

    Gibt die Anzahl neu entdeckter Knoten zurueck (fuer Tests/Logging).
    """
    knoten, kanten = await _graph_laden(campaign_id)
    erreichbar = erreichbare_ids(person_id, knoten, kanten, person_id)
    vorhanden = await _bereits_entdeckt(campaign_id, person_id)
    neu = erreichbar - vorhanden
    if not neu:
        return 0

    driver = get_driver()
    async with driver.session() as session:
        await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})
            UNWIND $ziel_ids AS ziel_id
            MATCH (z {id: ziel_id, campaignId: $campaign_id})
            MERGE (p)-[r:ENTDECKT]->(z)
            ON CREATE SET r.seit = datetime()
            """,
            campaign_id=campaign_id,
            person_id=person_id,
            ziel_ids=list(neu),
        )
    return len(neu)


async def _partei_aufenthaltsort(campaign_id: str, person_id: str) -> str | None:
    """Der Ort/Event, an dem die Party dieses PCs gerade steht — Grundlage
    der "In meiner Naehe"-Standardsortierung."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:MITGLIED_VON]->(:Party)
                  -[:BEFINDET_SICH_AN]->(ziel)
            RETURN ziel.id AS id
            """,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        record = await result.single()
        return record["id"] if record else None


async def entdeckte_eintraege(campaign_id: str, person_id: str) -> list[dict]:
    """Alle fuer diesen PC entdeckten Lexikon-Eintraege, roh (ungefiltert
    bzgl. Beschreibung — die Redaktion macht die Route per
    entities/visibility.py, dieselbe Logik wie ueberall sonst)."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[r:ENTDECKT]->(z)
            OPTIONAL MATCH (p)-[f:FAVORISIERT]->(z)
            RETURN z.id AS id, labels(z)[0] AS kind,
                   coalesce(z.name, z.title) AS name,
                   coalesce(z.bildUrl, '') AS bildUrl,
                   coalesce(z.description, '') AS description,
                   coalesce(z.sichtbarkeit, 'GM') AS sichtbarkeit,
                   coalesce(z.sichtbarFuer, []) AS sichtbarFuer,
                   toString(r.seit) AS entdecktSeit,
                   f IS NOT NULL AS favorisiert
            """,
            campaign_id=campaign_id,
            person_id=person_id,
        )
        eintraege = [dict(rec) async for rec in result]

    ort_id = await _partei_aufenthaltsort(campaign_id, person_id)
    if ort_id is not None:
        knoten, kanten = await _graph_laden(campaign_id)
        raenge = naehe_raenge(ort_id, knoten, kanten)
        for e in eintraege:
            e["naehe"] = raenge.get(e["id"], 9999)
    else:
        for e in eintraege:
            e["naehe"] = 9999

    for e in eintraege:
        e["kategorie"] = _KATEGORIE_VON_LABEL.get(e["kind"], "welt")
    return eintraege


async def favorisieren(campaign_id: str, person_id: str, ziel_id: str) -> bool:
    """Setzt FAVORISIERT — nur fuer bereits entdeckte Eintraege sinnvoll,
    daher ueber ENTDECKT gematcht statt direkt ueber die ID."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[:ENTDECKT]->(z {id: $ziel_id})
            MERGE (p)-[:FAVORISIERT]->(z)
            RETURN count(z) AS n
            """,
            campaign_id=campaign_id,
            person_id=person_id,
            ziel_id=ziel_id,
        )
        record = await result.single()
        return bool(record and record["n"] > 0)


async def favorisieren_entfernen(campaign_id: str, person_id: str, ziel_id: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Person {id: $person_id, campaignId: $campaign_id})-[f:FAVORISIERT]->(z {id: $ziel_id})
            DELETE f
            RETURN count(z) AS n
            """,
            campaign_id=campaign_id,
            person_id=person_id,
            ziel_id=ziel_id,
        )
        record = await result.single()
        return bool(record and record["n"] > 0)
