"""Kampagnen-Export/Import: eine komplette Kampagne als ZIP-Datei sichern
und als neue Kampagne wiederherstellen.

**Ansatz: zwei generische Cypher-Abfragen statt eines Sonderfalls je
Entitätstyp.** Die meisten Knotentypen tragen `campaignId` direkt als
Eigenschaft (Person, Ort, Event, Fraktion, Gegenstand, Party, Begleiter,
WikiSeite, Mitteilung, Verhandlung, Kampf, Nachricht) — die erfasst ein
einziges `WHERE n.campaignId = $campaign_id`. Zwei Ausnahmen ohne dieses
Feld werden explizit nachgezogen: `Spieler` (nur über `GEHOERT_ZU`
erreichbar) und `KampfTeilnehmer` (nur über `Kampf-[:KAEMPFT]->`). Der
`Campaign`-Knoten selbst kommt als drittes Element dazu.

Kanten werden ebenso generisch eingesammelt: alle ausgehenden Kanten jedes
gefundenen Knotens. Das erfasst auch Kanten zu **globalen Katalogknoten**
(`Rasse`, `TraitDef`, `Regelsystem`) — deren IDs werden beim Import bewusst
NICHT neu vergeben (sie sind kein Teil dieser Kampagne, sondern ein
gemeinsamer Katalog, der in der Zieldatenbank bereits existieren muss, z.B.
durch `seed_traits`/`seed_rassen`/`seed_neotopia` beim Start).

**ID-Neuvergabe per Text-Ersetzung statt Feld-für-Feld-Mapping.** Jede
Referenz auf eine kampagnen-eigene ID — als Kanten-Endpunkt, als
`campaignId`-Eigenschaft, aber auch versteckt in einer JSON-als-Text
gespeicherten Liste (`sichtbarFuer`, `empfaengerIds`, `gelesenVon` mit
Personen-IDs, `stammtId` eines Kampfteilnehmers, Bild-URLs mit der
Kampagnen-ID im Pfad) — ist im rohen JSON-Text einfach die UUID als
Zeichenkette. Eine einzige Ersetzungsrunde über den gesamten Rohtext, bevor
er wieder geparst wird, trifft daher jede dieser Stellen auf einmal, ohne
dass jedes Datenmodell einzeln nach ID-tragenden Feldern durchsucht werden
muss. Kollisionen sind praktisch ausgeschlossen (UUIDv4, 122 Zufallsbits).
"""

from __future__ import annotations

import io
import json
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from neo4j.time import Date, DateTime, Duration, Time

from app.campaigns.repository import get_campaign
from app.db.neo4j_driver import get_driver

EXPORT_FORMAT_VERSION = 1
UPLOAD_DIR = Path("uploads")


class _Neo4jJSONEncoder(json.JSONEncoder):
    """Neo4j liefert eigene Zeittypen (z.B. `Campaign.createdAt: datetime()`),
    die `json.dumps` nicht kennt — als ISO-Text exportieren, `str()` deckt
    alle vier Typen einheitlich ab (DateTime/Date/Time/Duration)."""

    def default(self, o):
        if isinstance(o, (DateTime, Date, Time, Duration)):
            return str(o)
        return super().default(o)


# Weisse Liste: nur diese Labels/Kantentypen dürfen aus einem Importpaket
# tatsächlich als Cypher-Label/-Beziehungstyp verwendet werden. Cypher kann
# Labels und Beziehungstypen nicht parametrisieren (nur Eigenschaftswerte) —
# ohne diese Prüfung könnte eine manipulierte ZIP-Datei beliebigen
# Cypher-Text einschleusen, weil der Name direkt in die Abfrage eingeht.
KNOWN_LABELS = {
    "Campaign", "Person", "Ort", "Event", "Fraktion", "Gegenstand", "Party",
    "Begleiter", "WikiSeite", "Mitteilung", "Verhandlung", "Kampf",
    "KampfTeilnehmer", "Spieler", "Nachricht",
}

KNOWN_REL_TYPES = {
    "HAT_ENTITAET", "HAT_SEITE", "HAT_MITTEILUNG", "HAT_VERHANDLUNG",
    "HAT_KAMPF", "BESITZT", "LIEGT_IN", "UNTERSEITE_VON", "VERWEIST_AUF",
    "VERBINDUNG", "KENNT", "VON", "AN", "BEGLEITET", "MITGLIED_VON",
    "BEFINDET_SICH_AN", "VERKAUFT", "KAEMPFT", "IST", "SPIELT",
    "GEHOERT_ZU", "HAT_EINFLUSS_AUF", "HAS_TRAIT", "ERLAUBT_RASSE",
    "NUTZT_REGELSYSTEM",
}

_UUID_RE = re.compile(r"^[0-9a-fA-F-]{20,40}$")


def _slug(text: str) -> str:
    """Dateiname-taugliche Kurzfassung eines Kampagnennamens."""
    ausgabe = re.sub(r"[^a-zA-Z0-9-]+", "-", text.strip()).strip("-").lower()
    return ausgabe or "kampagne"


async def collect_campaign_graph(campaign_id: str) -> tuple[list[dict], list[dict]]:
    """Alle Knoten und Kanten einer Kampagne — siehe Modul-Docstring für die
    Begründung der beiden Sonderfälle (Spieler, KampfTeilnehmer)."""
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})
            OPTIONAL MATCH (scoped) WHERE scoped.campaignId = $campaign_id
            WITH c, collect(DISTINCT scoped) AS a
            OPTIONAL MATCH (s:Spieler)-[:GEHOERT_ZU]->(c)
            WITH c, a, collect(DISTINCT s) AS b
            OPTIONAL MATCH (c)-[:HAT_KAMPF]->(:Kampf)-[:KAEMPFT]->(t:KampfTeilnehmer)
            WITH c, a, b, collect(DISTINCT t) AS d
            WITH a + b + d + [c] AS alle
            UNWIND alle AS n
            WITH DISTINCT n
            RETURN n.id AS id, labels(n) AS labels, properties(n) AS props
            """,
            campaign_id=campaign_id,
        )
        nodes = [dict(record) async for record in result]

        ids = [n["id"] for n in nodes]
        result = await session.run(
            """
            UNWIND $ids AS id
            MATCH (a {id: id})-[r]->(b)
            WHERE b.id IS NOT NULL
            RETURN DISTINCT a.id AS fromId, type(r) AS relType, properties(r) AS props,
                   b.id AS toId, labels(b) AS toLabels
            """,
            ids=ids,
        )
        edges = [dict(record) async for record in result]

    return nodes, edges


async def export_campaign_zip(campaign_id: str) -> tuple[bytes, str]:
    """Baut das ZIP-Paket im Speicher; gibt (Bytes, vorgeschlagener Dateiname) zurück."""
    campaign = await get_campaign(campaign_id)
    if campaign is None:
        raise ValueError("Kampagne nicht gefunden")

    nodes, edges = await collect_campaign_graph(campaign_id)

    bild_ordner = UPLOAD_DIR / campaign_id
    bild_dateien = sorted(bild_ordner.glob("*")) if bild_ordner.exists() else []

    manifest = {
        "formatVersion": EXPORT_FORMAT_VERSION,
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "campaignId": campaign_id,
        "campaignName": campaign["name"],
        "regelsystem": campaign.get("regelsystem", "neotopia"),
        "anzahlKnoten": len(nodes),
        "anzahlKanten": len(edges),
        "anzahlBilder": len(bild_dateien),
    }

    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr("daten.json", json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, cls=_Neo4jJSONEncoder))
        for datei in bild_dateien:
            if datei.is_file():
                zf.write(datei, arcname=f"bilder/{datei.name}")

    zeitstempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    dateiname = f"kampagne-{_slug(campaign['name'])}-{zeitstempel}.zip"
    return puffer.getvalue(), dateiname


def remap_ids(rohtext: str, alte_campaign_id: str) -> tuple[str, dict, str]:
    """Reine Funktion (keine DB) — prüft Labels/Kantentypen und ersetzt jede
    kampagnen-eigene ID im Rohtext durch eine frische UUID.

    Getrennt von `import_campaign_zip`, damit die Kernlogik ohne laufende
    Neo4j-Instanz testbar ist. Gibt (neuer Text, alte→neue-ID-Abbildung,
    neue Kampagnen-ID) zurück. Wirft `ValueError` bei unbekanntem
    Label/Kantentyp oder wenn die Kampagnen-ID selbst fehlt.
    """
    daten = json.loads(rohtext)
    knoten = daten.get("nodes", [])
    kanten = daten.get("edges", [])

    alte_ids = set()
    for n in knoten:
        for label in n.get("labels", []):
            if label not in KNOWN_LABELS:
                raise ValueError(f"Unbekanntes Knoten-Label im Import: {label}")
        if not n.get("id"):
            raise ValueError("Knoten ohne id im Importpaket")
        alte_ids.add(n["id"])

    for e in kanten:
        if e.get("relType") not in KNOWN_REL_TYPES:
            raise ValueError(f"Unbekannter Kantentyp im Import: {e.get('relType')}")

    if alte_campaign_id not in alte_ids:
        raise ValueError("Kampagnen-ID aus manifest.json fehlt in daten.json")

    id_map = {alt: str(uuid.uuid4()) for alt in alte_ids}
    neue_campaign_id = id_map[alte_campaign_id]

    text = rohtext
    for alt, neu in id_map.items():
        text = text.replace(alt, neu)

    return text, id_map, neue_campaign_id


async def import_campaign_zip(inhalt: bytes, gm_id: str) -> dict:
    """Liest das ZIP, vergibt neue IDs und schreibt eine neue Kampagne in Neo4j.

    Legt IMMER eine neue Kampagne mit neuer ID an (nie ein Überschreiben
    einer bestehenden) — Marks Entscheidung, um versehentlichen Datenverlust
    auszuschliessen.
    """
    with zipfile.ZipFile(io.BytesIO(inhalt)) as zf:
        namen = set(zf.namelist())
        if "manifest.json" not in namen or "daten.json" not in namen:
            raise ValueError("Kein gültiges Kampagnen-Exportpaket (manifest.json/daten.json fehlt)")

        manifest = json.loads(zf.read("manifest.json"))
        if manifest.get("formatVersion") != EXPORT_FORMAT_VERSION:
            raise ValueError(f"Unbekannte Exportformat-Version: {manifest.get('formatVersion')}")

        rohtext = zf.read("daten.json").decode("utf-8")
        text, id_map, neue_campaign_id = remap_ids(rohtext, manifest["campaignId"])
        daten = json.loads(text)

        bild_namen = [n for n in namen if n.startswith("bilder/") and not n.endswith("/")]
        neuer_bildordner = UPLOAD_DIR / neue_campaign_id
        if bild_namen:
            neuer_bildordner.mkdir(parents=True, exist_ok=True)
        for name in bild_namen:
            dateiname = name.split("/", 1)[1]
            if not dateiname or "/" in dateiname or "\\" in dateiname:
                continue  # ausbruchsicher: kein Pfadsegment aus dem Archiv verlassen den Zielordner
            (neuer_bildordner / dateiname).write_bytes(zf.read(name))

    driver = get_driver()
    async with driver.session() as session:
        for node in daten["nodes"]:
            labels = ":".join(node["labels"])
            await session.run(f"CREATE (n:{labels}) SET n = $props", props=node["props"])

        for edge in daten["edges"]:
            rel = edge["relType"]
            # MATCH statt CREATE für beide Enden: existiert ein Ziel nicht
            # (z.B. ein globaler Katalogknoten, der in dieser Datenbank
            # fehlt), liefert die Abfrage schlicht keine Zeile — die Kante
            # fällt dann kommentarlos weg, statt den ganzen Import abzubrechen.
            await session.run(
                f"""
                MATCH (a {{id: $fromId}})
                MATCH (b {{id: $toId}})
                CREATE (a)-[r:{rel}]->(b)
                SET r = $props
                """,
                fromId=edge["fromId"],
                toId=edge["toId"],
                props=edge["props"],
            )

        await session.run(
            """
            MATCH (g:GMUser {id: $gm_id})
            MATCH (c:Campaign {id: $campaign_id})
            CREATE (g)-[:OWNS]->(c)
            """,
            gm_id=gm_id,
            campaign_id=neue_campaign_id,
        )

    ergebnis = await get_campaign(neue_campaign_id)
    if ergebnis is None:
        raise ValueError("Import fehlgeschlagen — Kampagne wurde nicht angelegt")
    return ergebnis
