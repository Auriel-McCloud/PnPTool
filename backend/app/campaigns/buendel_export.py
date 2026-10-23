"""Kampagnen-Bündel — Export (Phase 1).

Teilt sich den ZIP-Aufbau (`manifest.json` + `daten.json` + `bilder/`) mit
`app/campaigns/export_import.py`, ist aber ein bewusst **separates, kleineres**
Werkzeug: ein Bündel exportiert nicht die ganze Kampagne, sondern nur die neun
wiederverwendbaren Welt-Inhaltstypen (für die Weitergabe an andere Runden,
z.B. als GitHub-Download), ausdrücklich OHNE Spielstand (PCs, Kämpfe,
Verhandlungen, Spieler-Accounts, ...).

**Neun Bündel-Typen:** Ort, Gegenstand, Fraktion, Person (NPC + Begleiter/
Critter — NICHT PC), Gewaechs, Event, WikiSeite, Rasse, Achievement
(Definitionen — NICHT AchievementVerleihung, die ist reine Spielstand-Historie
pro PC und bleibt wie PCs aussen vor).

**Eigene, kleinere Weissliste statt `export_import.KNOWN_LABELS`/
`KNOWN_REL_TYPES`.** Eine künftige Änderung an der grossen Kampagnen-Export-
Weissliste (neuer Spielstand-Knotentyp) soll dieses Feature nicht
stillschweigend mitreissen, und umgekehrt — siehe Modul-Docstring dort für die
Begründung, warum Cypher Labels/Kantentypen nicht parametrisieren kann.

**Rasse ist campaign-SCOPELESS** (globaler Ruleset-Katalog, siehe
`app/rassen/repository.py`) — anders als die anderen acht Typen trägt sie
kein `campaignId`-Property. Kandidaten kommen deshalb über die
`(:Campaign)-[:ERLAUBT_RASSE]->(:Rasse)`-Kante dieser Kampagne, nicht über
einen `WHERE campaignId = ...`-Filter wie bei den übrigen Typen.
`Person.rasse` ist dabei reiner Text (der Rassenname) statt einer Kante —
die Zuordnung "welche Rasse nutzt dieser NPC" lebt daher schon als
Property auf dem exportierten Person-Knoten und braucht keine eigene
Kanten-Behandlung.

**Kanten nur zwischen zwei ausgewählten Knoten.** Anders als
`collect_campaign_graph` (das Kanten zu JEDEM Zielknoten zulässt, auch zu
global nicht mitgenommenen Katalogknoten) schneidet ein Bündel Kanten ab,
deren Ziel nicht selbst Teil der Auswahl ist — ein Bündel ist eine bewusste
Teilmenge, eine Kante ins Leere (oder zu einer absichtlich ausgeschlossenen
PC/Entität) wäre beim Re-Import in Phase 2 nicht auflösbar.

**Bilder werden auf die tatsächlich exportierten Knoten eingeschränkt** —
anders als `export_campaign_zip`, das blind den ganzen
`uploads/{campaignId}`-Ordner mitnimmt (für ein Vollbackup richtig, für eine
bewusste Teilmenge nicht: ein ausgeschlossener PC/eine abgewählte Entität
soll sein Bild nicht versehentlich mit ins Archiv ziehen).
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from app.campaigns.export_import import _Neo4jJSONEncoder, _slug
from app.campaigns.repository import get_campaign
from app.db.neo4j_driver import get_driver

BUENDEL_FORMAT_VERSION = 1
UPLOAD_DIR = Path("uploads")

# Die neun Bündel-Typen. "Rasse" fehlt in _CAMPAIGN_SCOPED_LABELS (siehe
# Modul-Docstring) und wird separat über ERLAUBT_RASSE eingesammelt.
BUENDEL_LABELS = {
    "Ort", "Gegenstand", "Fraktion", "Person", "Gewaechs",
    "Event", "WikiSeite", "Rasse", "Achievement",
}
_CAMPAIGN_SCOPED_LABELS = BUENDEL_LABELS - {"Rasse"}

# Kantentypen, die tatsächlich zwischen zwei Bündel-Typen auftreten (geprüft
# gegen die reale Nutzung im Code, Stand 23.10.2026) — bewusst NICHT
# `export_import.KNOWN_REL_TYPES` wiederverwendet, siehe Modul-Docstring.
#   BESITZT           Person -> Gegenstand (Inventar)
#   LIEGT_IN          Gegenstand -> Ort | Gegenstand (Lagerung/Behälter)
#   VERBINDUNG        generische SL-Beziehungskante zwischen Person/Ort/
#                     Event/Fraktion/Gegenstand (app/entities/schemas.py::
#                     EntityKind)
#   HAT_EINFLUSS_AUF  Person -> Ort | Fraktion | Event | Gegenstand
#   LEBT_IN           Critter (Person) | Gewaechs -> Ort (Flora & Fauna)
#   BEGLEITET         Critter (Person) -> Person (Besitzer)
#   UNTERSEITE_VON    WikiSeite -> WikiSeite (Seitenbaum)
#   VERWEIST_AUF      WikiSeite -> Person | Ort | Event | Gegenstand | Fraktion
#   BETREIBT          Person{istHaendler} -> Ort{istShop} (Shop-System)
#   VERKAUFT          Person | Ort -> Gegenstand (Sortiment)
# Absichtlich NICHT dabei: MITGLIED_VON/BEFINDET_SICH_AN (Party ist kein
# Bündel-Typ), HAT_* Campaign-Anhänge (Campaign wird nie mitexportiert, kann
# also nie Startpunkt `a` sein), ERLAUBT_RASSE (Campaign->Rasse, dito), KENNT
# & andere Spielstand-Kanten (Kontakte/Kampf/Verhandlung) — bewusst klein
# gehalten für Phase 1, siehe PR-Beschreibung für mögliche Phase-2-Ergänzungen.
BUENDEL_REL_TYPES = {
    "BESITZT", "LIEGT_IN", "VERBINDUNG", "HAT_EINFLUSS_AUF", "LEBT_IN",
    "BEGLEITET", "UNTERSEITE_VON", "VERWEIST_AUF", "BETREIBT", "VERKAUFT",
}

_UPLOAD_URL_RE = re.compile(r"^/uploads/[^/]+/([^/\\]+)$")


def _ist_bereits_geloescht(props: dict) -> bool:
    """Papierkorb-Status einer Entität — die meisten der neun Typen nutzen
    `geloescht` (siehe Retrofit in entities/wiki/rassen/achievements
    repository.py), Gegenstand historisch `weggeworfen` (sein eigener,
    älterer, aber gleichwertiger Mülleimer-Mechanismus, siehe
    app/items/repository.py::wegwerfen)."""
    return bool(props.get("geloescht")) or bool(props.get("weggeworfen"))


async def collect_buendel_graph(campaign_id: str, exclude_ids: set[str]) -> tuple[list[dict], list[dict]]:
    """Sammelt alle Bündel-fähigen Knoten/Kanten dieser Kampagne.

    Schliesst aus: PCs (`personType == "PC"`), bereits im Papierkorb
    befindliche Entitäten, und was der GM im Bündel-Bildschirm abgewählt hat
    (`exclude_ids`). `AchievementVerleihung` ist durch das Label-Matching
    (nur `Achievement`, nicht `AchievementVerleihung`) automatisch nie dabei.
    """
    driver = get_driver()
    label_filter = " OR ".join(f"n:{label}" for label in sorted(_CAMPAIGN_SCOPED_LABELS))
    async with driver.session() as session:
        result = await session.run(
            f"""
            MATCH (n)
            WHERE ({label_filter}) AND n.campaignId = $campaign_id
            RETURN n.id AS id, labels(n) AS labels, properties(n) AS props
            """,
            campaign_id=campaign_id,
        )
        knoten = [dict(r) async for r in result]

        result = await session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})-[:ERLAUBT_RASSE]->(r:Rasse)
            RETURN r.id AS id, labels(r) AS labels, properties(r) AS props
            """,
            campaign_id=campaign_id,
        )
        knoten += [dict(r) async for r in result]

        gefiltert = [
            n for n in knoten
            if n["id"] not in exclude_ids
            and n["props"].get("personType") != "PC"
            and not _ist_bereits_geloescht(n["props"])
        ]

        ids = [n["id"] for n in gefiltert]
        if not ids:
            return gefiltert, []

        result = await session.run(
            """
            UNWIND $ids AS id
            MATCH (a {id: id})-[r]->(b)
            WHERE type(r) IN $rel_types AND b.id IN $ids
            RETURN DISTINCT a.id AS fromId, type(r) AS relType, properties(r) AS props,
                   b.id AS toId, labels(b) AS toLabels
            """,
            ids=ids,
            rel_types=list(BUENDEL_REL_TYPES),
        )
        kanten = [dict(r) async for r in result]

    return gefiltert, kanten


def _bilder_eintraege(roh) -> list[dict]:
    """`bilder` kann als echte Liste (frisch aus Neo4j) oder als JSON-Text
    vorliegen (so wird es laut `entities/repository.py::create_node`
    gespeichert) — beide Formen abdecken."""
    if isinstance(roh, list):
        return [e for e in roh if isinstance(e, dict)]
    if isinstance(roh, str) and roh:
        try:
            geparst = json.loads(roh)
        except (json.JSONDecodeError, TypeError):
            return []
        return [e for e in geparst if isinstance(e, dict)]
    return []


def _referenzierte_bilddateien(campaign_id: str, knoten: list[dict]) -> list[Path]:
    """Nur Bilder, die tatsächlich zu einem exportierten Knoten gehören.

    Anders als `export_campaign_zip` (nimmt blind den ganzen
    `uploads/{campaignId}`-Ordner) — siehe Modul-Docstring.
    """
    dateinamen: set[str] = set()

    def _merke(url: str | None) -> None:
        if not url:
            return
        treffer = _UPLOAD_URL_RE.match(url)
        if treffer and f"/uploads/{campaign_id}/" in url:
            dateinamen.add(treffer.group(1))

    for n in knoten:
        props = n.get("props", {})
        _merke(props.get("bildUrl"))
        _merke(props.get("shopHintergrundUrl"))
        for eintrag in _bilder_eintraege(props.get("bilder")):
            _merke(eintrag.get("url"))

    basis = UPLOAD_DIR / campaign_id
    return [basis / name for name in sorted(dateinamen)]


async def export_buendel_zip(
    campaign_id: str,
    *,
    name: str,
    beschreibung: str = "",
    tags: list[str] | None = None,
    exclude_ids: list[str] | None = None,
) -> tuple[bytes, str]:
    """Baut das Bündel-ZIP im Speicher; gibt (Bytes, vorgeschlagener Dateiname) zurück."""
    campaign = await get_campaign(campaign_id)
    if campaign is None:
        raise ValueError("Kampagne nicht gefunden")

    knoten, kanten = await collect_buendel_graph(campaign_id, set(exclude_ids or []))

    anzahl_pro_typ: dict[str, int] = {}
    for n in knoten:
        for label in n["labels"]:
            if label in BUENDEL_LABELS:
                anzahl_pro_typ[label] = anzahl_pro_typ.get(label, 0) + 1
                break

    bild_dateien = _referenzierte_bilddateien(campaign_id, knoten)

    manifest = {
        "formatVersion": BUENDEL_FORMAT_VERSION,
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "beschreibung": beschreibung,
        "tags": tags or [],
        "herkunftCampaignId": campaign_id,
        "herkunftCampaignName": campaign["name"],
        "anzahlKnoten": len(knoten),
        "anzahlProTyp": anzahl_pro_typ,
    }

    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr(
            "daten.json",
            json.dumps({"nodes": knoten, "edges": kanten}, ensure_ascii=False, cls=_Neo4jJSONEncoder),
        )
        for datei in bild_dateien:
            if datei.is_file():
                zf.write(datei, arcname=f"bilder/{datei.name}")

    zeitstempel = datetime.now().strftime("%Y%m%d-%H%M%S")
    dateiname = f"buendel-{_slug(name)}-{zeitstempel}.zip"
    return puffer.getvalue(), dateiname
