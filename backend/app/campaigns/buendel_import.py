"""Kampagnen-Bündel — Import (Phase 2).

Nimmt ein von `buendel_export.py` erzeugtes ZIP und spielt es in eine
**bestehende** Kampagne ein (die, die gerade im Bündel-Bildschirm offen ist —
kein Kampagnen-Picker, siehe Frontend). Das unterscheidet dieses Modul
grundlegend von `export_import.py::import_campaign_zip`, das IMMER eine neue
Kampagne anlegt: hier muss für jeden einzelnen Knoten entschieden werden, ob
er in der Zielkampagne schon existiert (dann überspringen oder aktualisieren)
oder neu ist (dann anlegen) — `import_campaign_zip` kennt diese Fallunterscheidung
nicht, weil bei ihr jeder Knoten per Definition neu ist.

**Abgleich über `stammtVonId`, pro Zielkampagne.** Jeder der neun Bündel-Typen
bekommt `stammtVonId` beim Anlegen gesetzt (siehe `entities/repository.py`,
`items/repository.py`, `wiki/repository.py`, `rassen/repository.py`,
`achievements/repository.py`) — stabil über `id`-Neuvergaben bei künftigen
Re-Importen hinweg. Ein eingehender Knoten gilt als "schon vorhanden", wenn
die Zielkampagne (bzw. bei Rasse: irgendeine Kampagne, siehe unten) bereits
einen NICHT gelöschten Knoten desselben Labels mit derselben `stammtVonId`
hat.

**Rasse ist eine Ausnahme** (wie schon beim Export, siehe buendel_export.py):
kein `campaignId`, globaler Ruleset-Katalog. Der Abgleich läuft deshalb
campaign-UNABHÄNGIG rein über `stammtVonId` — importiert ein zweiter GM
dasselbe Bündel in eine andere Kampagne, soll die bereits vom ersten Import
angelegte Rasse wiedergefunden werden, nicht dupliziert. Eine neu angelegte
ODER wiedergefundene Rasse wird zusätzlich für die Zielkampagne per
`(:Campaign)-[:ERLAUBT_RASSE]->(:Rasse)` freigegeben (MERGE, idempotent) —
unabhängig vom gewählten Modus, das ist eine separate Freigabe-Aktion, keine
Eigenschaftsänderung an der Rasse selbst.

**Zwei Modi für bereits vorhandene Knoten** (einmal für den ganzen Lauf
gewählt, nicht pro Knoten):
  - `ueberspringen`: Eigenschaften bleiben komplett unangetastet.
  - `aktualisieren`: der aktuelle Stand des bestehenden Knotens wird zuerst
    unverändert in einen neuen, separaten Knoten mit `geloescht: true`
    dupliziert (Papierkorb-Schnappschuss — eigene frische `id`, sonst
    identische Properties), DANACH werden die Properties des echten,
    bestehenden Knotens mit den Bündel-Werten überschrieben. `id`,
    `stammtVonId` und `campaignId` des echten Knotens bleiben dabei
    unangetastet; `istEntwurf` (siehe unten) ebenfalls — ein Update ist kein
    neuer Entwurf, sondern eine direkte Änderung an etwas bereits Lebendigem.

**Sicherheit:** jedes Label/jeder Kantentyp wird vor jeder Nutzung in Cypher
gegen `buendel_export.BUENDEL_LABELS`/`BUENDEL_REL_TYPES` geprüft (dieselbe
Weissliste wie beim Export, bewusst NICHT `export_import.KNOWN_LABELS` — siehe
dortigen Modul-Docstring). Jede Abweichung bricht den GESAMTEN Import mit
`ValueError` ab, kein stillschweigendes Überspringen einzelner Knoten — das
ZIP kann von einer fremden, nicht vertrauenswürdigen Quelle stammen (Mark will
Bündel auf GitHub veröffentlichen).

**Bild-Pfade:** die IDs im Bündel werden pro Knoten einzeln behandelt (anders
als bei `import_campaign_zip`, das eine einzige globale ID-Ersetzung über den
gesamten Rohtext macht — hier bräuchte jeder Knoten eine eigene, situative
Entscheidung, eine blinde Text-Ersetzung ginge nicht). Für Bild-URLs
(`/uploads/{campaignId}/...`) gilt das Gegenteil: die Kampagnen-ID im Pfad ist
in JEDEM Bündel genau eine einzige (`herkunftCampaignId` aus dem Manifest),
die blind durch die Ziel-Kampagnen-ID ersetzt werden kann, bevor der Rohtext
geparst wird — dieselbe Text-Ersetzungs-Technik wie bei `remap_ids`, nur für
einen Pfad-Baustein statt für IDs.

**istEntwurf (Ideenschmiede) — geprüft, nicht angenommen:** sieben der neun
Typen kennen das Feld (Person/Ort/Event/Fraktion/Gewaechs/WikiSeite/
Gegenstand, siehe die jeweiligen `*_FIELDS`-Listen/Schemas). Rasse (globaler
Katalog, nur Freigabe-Mechanik) und Achievement (Definition, kein
Entwurfs-Konzept) kennen es NICHT — für sie hat der Live/Ideenschmiede-Regler
keine Wirkung, sie landen immer live. Siehe PR-Bericht für die Begründung.
"""

from __future__ import annotations

import io
import json
import uuid
import zipfile
from pathlib import Path

from app.campaigns.buendel_export import BUENDEL_FORMAT_VERSION, BUENDEL_LABELS, BUENDEL_REL_TYPES
from app.campaigns.repository import get_campaign
from app.db.neo4j_driver import get_driver

UPLOAD_DIR = Path("uploads")

# Sieben der neun Bündel-Typen kennen istEntwurf — gegen die echten
# *_FIELDS-Listen/Schemas geprüft (siehe Modul-Docstring), nicht angenommen.
# Rasse und Achievement fehlen bewusst.
ISTENTWURF_FAEHIGE_LABELS = {
    "Ort", "Gegenstand", "Fraktion", "Person", "Gewaechs", "Event", "WikiSeite",
}

# Welche Campaign-Besitz-Kante eine frisch angelegte Entität bekommt — dieselbe,
# die die jeweilige normale Erstellungsfunktion auch zieht (create_node,
# create_seite, achievements_repo.anlegen). Gegenstand und Rasse fehlen bewusst:
# ein Gegenstand hängt nur über campaignId an der Kampagne (kein Campaign-Edge,
# auch bei normaler Erstellung nicht), eine Rasse ist global und bekommt
# stattdessen die separate ERLAUBT_RASSE-Freigabe weiter unten.
_OWNERSHIP_EDGE = {
    "Ort": "HAT_ENTITAET",
    "Person": "HAT_ENTITAET",
    "Event": "HAT_ENTITAET",
    "Fraktion": "HAT_ENTITAET",
    "Gewaechs": "HAT_ENTITAET",
    "WikiSeite": "HAT_SEITE",
    "Achievement": "HAT_ACHIEVEMENT",
}


def _label_von(labels: list[str]) -> str:
    for label in labels:
        if label in BUENDEL_LABELS:
            return label
    raise ValueError(f"Kein bekanntes Bündel-Label in {labels}")


def _validiere(knoten: list[dict], kanten: list[dict]) -> None:
    """Weissliste wie `export_import.remap_ids` — jede Abweichung bricht den
    GESAMTEN Import ab, kein stillschweigendes Überspringen (siehe Modul-
    Docstring: das ZIP kann von einer nicht vertrauenswürdigen Quelle stammen).
    """
    for n in knoten:
        labels = n.get("labels") or []
        for label in labels:
            if label not in BUENDEL_LABELS:
                raise ValueError(f"Unbekanntes Knoten-Label im Bündel: {label}")
        if not any(label in BUENDEL_LABELS for label in labels):
            raise ValueError(f"Knoten ohne gültiges Bündel-Label im Bündel: {labels}")
        if not n.get("id"):
            raise ValueError("Knoten ohne id im Bündel")
        if not (n.get("props") or {}).get("stammtVonId"):
            raise ValueError("Knoten ohne stammtVonId im Bündel — kein gültiges Bündel-Paket")

    for e in kanten:
        if e.get("relType") not in BUENDEL_REL_TYPES:
            raise ValueError(f"Unbekannter Kantentyp im Bündel: {e.get('relType')}")
        if not e.get("fromId") or not e.get("toId"):
            raise ValueError("Kante ohne fromId/toId im Bündel")


async def _finde_match(session, campaign_id: str, label: str, stammt_von_id: str) -> str | None:
    """Gibt die echte `id` eines bereits vorhandenen Knotens zurück, oder
    `None` wenn keiner gefunden wurde. Rasse sucht campaign-unabhängig (siehe
    Modul-Docstring), alle anderen acht Typen nur innerhalb der Zielkampagne.
    """
    if label == "Rasse":
        result = await session.run(
            "MATCH (r:Rasse {stammtVonId: $svid}) WHERE NOT coalesce(r.geloescht, false) "
            "RETURN r.id AS id LIMIT 1",
            svid=stammt_von_id,
        )
    else:
        result = await session.run(
            f"MATCH (n:{label} {{campaignId: $cid, stammtVonId: $svid}}) "
            f"WHERE NOT coalesce(n.geloescht, false) RETURN n.id AS id LIMIT 1",
            cid=campaign_id,
            svid=stammt_von_id,
        )
    record = await result.single()
    return record["id"] if record else None


async def _rasse_freigeben(session, campaign_id: str, rasse_id: str) -> None:
    """MERGE statt CREATE: idempotent, falls diese Kampagne die Rasse schon
    freigegeben hatte (z.B. aus einem früheren Bündel-Import) — siehe
    Modul-Docstring, gilt unabhängig vom gewählten Import-Modus."""
    await session.run(
        "MATCH (c:Campaign {id: $cid}) MATCH (r:Rasse {id: $rid}) "
        "MERGE (c)-[:ERLAUBT_RASSE]->(r)",
        cid=campaign_id,
        rid=rasse_id,
    )


async def _neu_anlegen(session, campaign_id: str, label: str, props: dict, ideenschmiede: bool) -> str:
    """Legt einen brandneuen Knoten an: frische echte `id`, `stammtVonId`
    bleibt aus dem Bündel unverändert (damit künftige Re-Importe ihn
    wiedererkennen), `campaignId` wird auf die Zielkampagne gesetzt (ausser
    bei Rasse, die keine hat)."""
    neu = dict(props)
    neue_id = str(uuid.uuid4())
    neu["id"] = neue_id
    if label != "Rasse":
        neu["campaignId"] = campaign_id
    if label in ISTENTWURF_FAEHIGE_LABELS:
        neu["istEntwurf"] = ideenschmiede

    edge_type = _OWNERSHIP_EDGE.get(label)
    if edge_type:
        query = f"""
            MATCH (c:Campaign {{id: $campaign_id}})
            CREATE (n:{label})
            SET n = $props
            CREATE (c)-[:{edge_type}]->(n)
            RETURN n.id AS id
        """
        result = await session.run(query, campaign_id=campaign_id, props=neu)
    else:
        result = await session.run(f"CREATE (n:{label}) SET n = $props RETURN n.id AS id", props=neu)
    record = await result.single()
    return record["id"]


async def _snapshot_und_ueberschreiben(
    session, campaign_id: str, label: str, matched_id: str, incoming_props: dict
) -> None:
    """Modus 'aktualisieren': erst ein unveränderter Schnappschuss der
    AKTUELLEN Werte in den Papierkorb (frische eigene id, geloescht=true),
    dann der echte Knoten mit den Bündel-Werten überschrieben. id/
    stammtVonId/campaignId bleiben am echten Knoten unverändert; istEntwurf
    bleibt ebenfalls beim bisherigen Wert (siehe Modul-Docstring — ein Update
    ist kein neuer Entwurf)."""
    result = await session.run(f"MATCH (n:{label} {{id: $id}}) RETURN properties(n) AS props", id=matched_id)
    record = await result.single()
    aktuell = dict(record["props"]) if record else {}

    schnappschuss = dict(aktuell)
    schnappschuss["id"] = str(uuid.uuid4())
    schnappschuss["geloescht"] = True
    await session.run(f"CREATE (s:{label}) SET s = $props", props=schnappschuss)

    neu = dict(incoming_props)
    neu["id"] = matched_id
    neu["stammtVonId"] = aktuell.get("stammtVonId", incoming_props.get("stammtVonId"))
    if label != "Rasse":
        neu["campaignId"] = campaign_id
    if label in ISTENTWURF_FAEHIGE_LABELS:
        neu["istEntwurf"] = aktuell.get("istEntwurf", False)

    await session.run(f"MATCH (n:{label} {{id: $id}}) SET n = $props", id=matched_id, props=neu)


def _bilder_extrahieren(zf: zipfile.ZipFile, namen: set[str], campaign_id: str) -> None:
    """Kopiert `bilder/<datei>` aus dem ZIP nach `uploads/{campaignId}/` —
    ohne das wären importierte Bild-URLs (nach der Pfad-Umschreibung unten)
    Links ins Leere. Ausbruchsicher wie `import_campaign_zip`: kein
    Pfadsegment aus dem Archiv darf den Zielordner verlassen."""
    bild_namen = [n for n in namen if n.startswith("bilder/") and not n.endswith("/")]
    if not bild_namen:
        return
    ziel_ordner = UPLOAD_DIR / campaign_id
    ziel_ordner.mkdir(parents=True, exist_ok=True)
    for name in bild_namen:
        dateiname = name.split("/", 1)[1]
        if not dateiname or "/" in dateiname or "\\" in dateiname:
            continue
        ziel_pfad = ziel_ordner / dateiname
        if not ziel_pfad.exists():
            ziel_pfad.write_bytes(zf.read(name))


async def preview_buendel_zip(campaign_id: str, inhalt: bytes) -> dict:
    """Liest das ZIP und meldet nur, was drin ist und wie viel davon in der
    Zielkampagne bereits existiert — schreibt nichts. Nice-to-have für die
    Oberfläche ("3 Orte, davon 1 schon vorhanden"); der eigentliche Import
    funktioniert auch ohne vorherigen Aufruf dieser Funktion.
    """
    campaign = await get_campaign(campaign_id)
    if campaign is None:
        raise ValueError("Zielkampagne nicht gefunden")

    with zipfile.ZipFile(io.BytesIO(inhalt)) as zf:
        namen = set(zf.namelist())
        if "manifest.json" not in namen or "daten.json" not in namen:
            raise ValueError("Kein gültiges Bündel-Paket (manifest.json/daten.json fehlt)")
        manifest = json.loads(zf.read("manifest.json"))
        if manifest.get("formatVersion") != BUENDEL_FORMAT_VERSION:
            raise ValueError(f"Unbekannte Bündel-Format-Version: {manifest.get('formatVersion')}")
        daten = json.loads(zf.read("daten.json").decode("utf-8"))

    knoten = daten.get("nodes", [])
    kanten = daten.get("edges", [])
    _validiere(knoten, kanten)

    pro_typ: dict[str, dict[str, int]] = {}
    driver = get_driver()
    async with driver.session() as session:
        for n in knoten:
            label = _label_von(n["labels"])
            svid = n["props"]["stammtVonId"]
            vorhanden = await _finde_match(session, campaign_id, label, svid) is not None
            eintrag = pro_typ.setdefault(label, {"neu": 0, "vorhanden": 0})
            eintrag["vorhanden" if vorhanden else "neu"] += 1

    return {
        "bundleName": manifest.get("name", ""),
        "beschreibung": manifest.get("beschreibung", ""),
        "tags": manifest.get("tags", []),
        "herkunftCampaignName": manifest.get("herkunftCampaignName", ""),
        "anzahlKnoten": len(knoten),
        "proTyp": pro_typ,
    }


async def import_buendel_zip(campaign_id: str, inhalt: bytes, *, modus: str, ideenschmiede: bool) -> dict:
    """Importiert ein Bündel-ZIP in eine BESTEHENDE Kampagne. `modus` ist
    `"ueberspringen"` oder `"aktualisieren"`, gilt für den gesamten Lauf.
    `ideenschmiede` gilt NUR für Neuanlagen (siehe Modul-Docstring)."""
    if modus not in ("ueberspringen", "aktualisieren"):
        raise ValueError(f"Unbekannter Import-Modus: {modus}")

    campaign = await get_campaign(campaign_id)
    if campaign is None:
        raise ValueError("Zielkampagne nicht gefunden")

    with zipfile.ZipFile(io.BytesIO(inhalt)) as zf:
        namen = set(zf.namelist())
        if "manifest.json" not in namen or "daten.json" not in namen:
            raise ValueError("Kein gültiges Bündel-Paket (manifest.json/daten.json fehlt)")

        manifest = json.loads(zf.read("manifest.json"))
        if manifest.get("formatVersion") != BUENDEL_FORMAT_VERSION:
            raise ValueError(f"Unbekannte Bündel-Format-Version: {manifest.get('formatVersion')}")

        rohtext = zf.read("daten.json").decode("utf-8")
        herkunft_id = manifest.get("herkunftCampaignId") or ""
        if herkunft_id:
            # Einzige Kampagnen-ID im ganzen Bündel (siehe Modul-Docstring) —
            # blinde Text-Ersetzung vor dem Parsen ist hier sicher, dieselbe
            # Technik wie remap_ids, nur für Bild-Pfade statt IDs.
            rohtext = rohtext.replace(f"/uploads/{herkunft_id}/", f"/uploads/{campaign_id}/")
        daten = json.loads(rohtext)

        knoten = daten.get("nodes", [])
        kanten = daten.get("edges", [])
        _validiere(knoten, kanten)

        _bilder_extrahieren(zf, namen, campaign_id)

    zaehler = {"neu": 0, "aktualisiert": 0, "uebersprungen": 0}
    pro_typ: dict[str, dict[str, int]] = {}

    def _zaehle(art: str, label: str) -> None:
        zaehler[art] += 1
        eintrag = pro_typ.setdefault(label, {"neu": 0, "aktualisiert": 0, "uebersprungen": 0})
        eintrag[art] += 1

    driver = get_driver()
    id_map: dict[str, str] = {}  # Bündel-eigene id (Herkunftskampagne) -> echte id in der Zielkampagne

    async with driver.session() as session:
        for node in knoten:
            label = _label_von(node["labels"])
            props = dict(node["props"])
            stammt_von_id = props["stammtVonId"]

            bestehende_id = await _finde_match(session, campaign_id, label, stammt_von_id)

            if bestehende_id is None:
                neue_id = await _neu_anlegen(session, campaign_id, label, props, ideenschmiede)
                id_map[node["id"]] = neue_id
                _zaehle("neu", label)
                if label == "Rasse":
                    await _rasse_freigeben(session, campaign_id, neue_id)
            else:
                id_map[node["id"]] = bestehende_id
                if label == "Rasse":
                    await _rasse_freigeben(session, campaign_id, bestehende_id)
                if modus == "ueberspringen":
                    _zaehle("uebersprungen", label)
                else:
                    await _snapshot_und_ueberschreiben(session, campaign_id, label, bestehende_id, props)
                    _zaehle("aktualisiert", label)

        for edge in kanten:
            rel = edge["relType"]
            von = id_map.get(edge["fromId"])
            zu = id_map.get(edge["toId"])
            if von is None or zu is None:
                continue  # durch _validiere ausgeschlossen, defensiv trotzdem
            # MERGE statt CREATE: ein zweiter Import desselben Bündels (z.B.
            # im Modus "ueberspringen") darf keine doppelte Kante anlegen.
            # ON CREATE SET statt immer SET: eine vom GM inzwischen von Hand
            # geänderte Kanteneigenschaft (z.B. VERBINDUNG-Beschreibung) wird
            # von einem erneuten Import nicht überschrieben.
            await session.run(
                f"""
                MATCH (a {{id: $von}})
                MATCH (b {{id: $zu}})
                MERGE (a)-[r:{rel}]->(b)
                ON CREATE SET r = $props
                """,
                von=von,
                zu=zu,
                props=edge.get("props") or {},
            )

    return {
        "neu": zaehler["neu"],
        "aktualisiert": zaehler["aktualisiert"],
        "uebersprungen": zaehler["uebersprungen"],
        "proTyp": pro_typ,
        "bundleName": manifest.get("name", ""),
        "herkunftCampaignName": manifest.get("herkunftCampaignName", ""),
    }
