"""Unit-Tests für die reine Export/Import-Logik (kein DB-Zugriff nötig).

`remap_ids` ist bewusst als reine Funktion getrennt (siehe Modul-Docstring
in export_import.py) — hier getestet ohne laufendes Neo4j. Der volle
Round-Trip gegen echte Neo4j läuft separat als manueller E2E-Smoke-Test
(siehe pnptool-development-Skill, references/backend-smoke-test.md).
"""

import json

import pytest

from app.campaigns.export_import import remap_ids

CAMPAIGN_ID = "campaign-1"
PERSON_ID = "person-1"
ORT_ID = "ort-1"


def _daten(nodes, edges):
    return json.dumps({"nodes": nodes, "edges": edges})


def _campaign_node():
    return {"id": CAMPAIGN_ID, "labels": ["Campaign"], "props": {"id": CAMPAIGN_ID, "name": "Testkampagne"}}


def test_remap_ersetzt_alle_ids_konsistent():
    rohtext = _daten(
        nodes=[
            _campaign_node(),
            {"id": PERSON_ID, "labels": ["Person"], "props": {"id": PERSON_ID, "campaignId": CAMPAIGN_ID, "name": "Aria"}},
            {"id": ORT_ID, "labels": ["Ort"], "props": {"id": ORT_ID, "campaignId": CAMPAIGN_ID, "name": "Hafen"}},
        ],
        edges=[
            {"fromId": PERSON_ID, "relType": "VERBINDUNG", "props": {"typ": "kennt"}, "toId": ORT_ID, "toLabels": ["Ort"]},
        ],
    )

    neuer_text, id_map, neue_campaign_id = remap_ids(rohtext, CAMPAIGN_ID)
    neu = json.loads(neuer_text)

    # Kampagnen-ID wurde neu vergeben und unterscheidet sich von der alten.
    assert neue_campaign_id != CAMPAIGN_ID
    assert id_map[CAMPAIGN_ID] == neue_campaign_id

    # Jeder Knoten trägt jetzt seine neue ID, sowohl als Top-Level-`id` als
    # auch in den Properties (campaignId).
    person = next(n for n in neu["nodes"] if n["props"]["name"] == "Aria")
    assert person["id"] == id_map[PERSON_ID]
    assert person["props"]["id"] == id_map[PERSON_ID]
    assert person["props"]["campaignId"] == neue_campaign_id

    # Kante zeigt konsistent auf die neuen IDs.
    kante = neu["edges"][0]
    assert kante["fromId"] == id_map[PERSON_ID]
    assert kante["toId"] == id_map[ORT_ID]

    # Alle vergebenen IDs sind untereinander verschieden (keine Kollision).
    assert len(set(id_map.values())) == len(id_map)


def test_remap_ersetzt_id_versteckt_in_json_text_feld():
    """sichtbarFuer/empfaengerIds & Co. liegen als JSON-Text in props — die
    Ersetzung muss auch dort greifen, nicht nur auf Top-Level-Feldern."""
    versteckte_liste = json.dumps([PERSON_ID])
    rohtext = _daten(
        nodes=[
            _campaign_node(),
            {"id": PERSON_ID, "labels": ["Person"], "props": {"id": PERSON_ID, "campaignId": CAMPAIGN_ID}},
            {
                "id": "mitteilung-1",
                "labels": ["Mitteilung"],
                "props": {"id": "mitteilung-1", "campaignId": CAMPAIGN_ID, "empfaengerIds": versteckte_liste},
            },
        ],
        edges=[],
    )

    neuer_text, id_map, _ = remap_ids(rohtext, CAMPAIGN_ID)
    neu = json.loads(neuer_text)
    mitteilung = next(n for n in neu["nodes"] if n["id"] == id_map["mitteilung-1"])
    empfaenger = json.loads(mitteilung["props"]["empfaengerIds"])
    assert empfaenger == [id_map[PERSON_ID]]


def test_remap_referenz_auf_globalen_katalogknoten_bleibt_unveraendert():
    """Eine Kante auf einen globalen Katalogknoten (z.B. Rasse), der NICHT
    Teil der eingesammelten Kampagnen-Knoten ist, behält seine ID — sie wird
    beim Import über MATCH gegen die Zieldatenbank aufgelöst, nicht neu vergeben."""
    RASSE_ID = "rasse-katalog-1"
    rohtext = _daten(
        nodes=[
            _campaign_node(),
            {"id": PERSON_ID, "labels": ["Person"], "props": {"id": PERSON_ID, "campaignId": CAMPAIGN_ID, "rasse": "Elf"}},
        ],
        edges=[
            {"fromId": CAMPAIGN_ID, "relType": "ERLAUBT_RASSE", "props": {}, "toId": RASSE_ID, "toLabels": ["Rasse"]},
        ],
    )

    neuer_text, id_map, neue_campaign_id = remap_ids(rohtext, CAMPAIGN_ID)
    neu = json.loads(neuer_text)
    kante = next(e for e in neu["edges"] if e["relType"] == "ERLAUBT_RASSE")
    assert kante["fromId"] == neue_campaign_id
    assert kante["toId"] == RASSE_ID  # unverändert — nicht Teil von id_map
    assert RASSE_ID not in id_map


def test_remap_lehnt_unbekanntes_label_ab():
    rohtext = _daten(
        nodes=[_campaign_node(), {"id": "x-1", "labels": ["EingeschleustesLabel"], "props": {"id": "x-1"}}],
        edges=[],
    )
    with pytest.raises(ValueError, match="Unbekanntes Knoten-Label"):
        remap_ids(rohtext, CAMPAIGN_ID)


def test_remap_lehnt_unbekannten_kantentyp_ab():
    rohtext = _daten(
        nodes=[_campaign_node(), {"id": PERSON_ID, "labels": ["Person"], "props": {"id": PERSON_ID}}],
        edges=[{"fromId": CAMPAIGN_ID, "relType": "EINGESCHLEUST", "props": {}, "toId": PERSON_ID, "toLabels": ["Person"]}],
    )
    with pytest.raises(ValueError, match="Unbekannter Kantentyp"):
        remap_ids(rohtext, CAMPAIGN_ID)


def test_remap_lehnt_fehlende_kampagnen_id_ab():
    rohtext = _daten(
        nodes=[{"id": PERSON_ID, "labels": ["Person"], "props": {"id": PERSON_ID}}],
        edges=[],
    )
    with pytest.raises(ValueError, match="Kampagnen-ID"):
        remap_ids(rohtext, CAMPAIGN_ID)
