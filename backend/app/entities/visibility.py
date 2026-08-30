"""Server-side visibility filtering for the GM/ALLE/SPEZIFISCH visibility model.

Wired into the read routes via the `Viewer` dependency (app/auth/dependencies.py).
Today the only way to get a non-GM viewer is the GM's own "Sehen wie Spieler X"
preview (`?alsSpieler=<personId>`); the real player login follows in Phase 4 and
only needs to supply a different `Viewer`, not a different filter path.

Filtering must always happen here (server-side) and never rely on the client
hiding data it already received.

Defaults are deliberately restrictive: a missing visibility field is treated as
"GM" (hidden) rather than "ALLE". Legacy nodes predating the visibility model
therefore stay invisible to players instead of leaking, and a typo in a field
name fails closed.
"""

import json


def _strip_gm_secret_marks(node: dict) -> dict | None:
    """Drops any TipTap text node carrying the 'gmSecret' mark, recursively."""
    if node.get("type") == "text":
        if any(m.get("type") == "gmSecret" for m in node.get("marks", [])):
            return None
        return node

    content = node.get("content")
    if content is not None:
        stripped = (_strip_gm_secret_marks(child) for child in content)
        node = {**node, "content": [child for child in stripped if child is not None]}
    return node


def redact_rich_text(raw: str, viewer_role: str) -> str:
    """Removes inline 'SL-geheim' marked spans from a TipTap JSON document string.

    GMs always see the raw, unredacted document (including the markup itself,
    so they can see what they've marked secret while editing). Non-JSON values
    (legacy plain-text fields, or empty strings) pass through unchanged, since
    they can't contain a gmSecret mark in the first place.
    """
    if viewer_role == "GM" or not raw:
        return raw
    try:
        doc = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw
    if not isinstance(doc, dict) or doc.get("type") != "doc":
        return raw
    return json.dumps(_strip_gm_secret_marks(doc))


def is_visible_to(modus: str, sichtbar_fuer: list[str], viewer_role: str, viewer_person_id: str | None) -> bool:
    if viewer_role == "GM":
        return True
    if modus == "ALLE":
        return True
    if modus == "SPEZIFISCH":
        return viewer_person_id is not None and viewer_person_id in sichtbar_fuer
    return False  # modus == "GM" -> nur der Spielleiter sieht es


# Kopfzeile des Charakterbogens. Bei einem NPC ist genau das der Stoff, aus
# dem die Kampagne besteht — was er will, was er fürchtet, wieviel Geld er hat.
# Es gibt dafür keine eigene Sichtbarkeitsstufe, deshalb bekommt sie ausser dem
# Spielleiter nur, wem der Charakter selbst gehört. Gleiche Entscheidung wie
# bei den Gegenstandsnotizen: lieber ganz zurückhalten als halb redigieren.
BOGEN_KOPF_FELDER = ("konzept", "alter", "ambition", "verlangen", "ziel", "kapital", "schulden")

# Ersatzwerte müssen zum Typ in PersonResponse passen, sonst scheitert die
# Prüfung und reisst die ganze Liste mit 500 herunter (Stolperstein 9).
_KOPF_LEER: dict[str, object] = {"kapital": 0, "schulden": 0}


def filter_entity_for_viewer(entity: dict, viewer_role: str, viewer_person_id: str | None) -> dict | None:
    if not is_visible_to(
        entity.get("sichtbarkeit") or "GM", entity.get("sichtbarFuer") or [], viewer_role, viewer_person_id
    ):
        return None

    result = dict(entity)
    if "description" in result:
        result["description"] = redact_rich_text(result["description"], viewer_role)

    if is_visible_to(
        entity.get("notizenSichtbarkeit") or "GM",
        entity.get("notizenSichtbarFuer") or [],
        viewer_role,
        viewer_person_id,
    ):
        result["notes"] = redact_rich_text(result.get("notes", ""), viewer_role)
    else:
        result["notes"] = ""

    if viewer_role != "GM" and entity.get("id") != viewer_person_id:
        for feld in BOGEN_KOPF_FELDER:
            if feld in result:
                result[feld] = _KOPF_LEER.get(feld, "")
    return result


def filter_entities_for_viewer(entities: list[dict], viewer_role: str, viewer_person_id: str | None) -> list[dict]:
    filtered = (filter_entity_for_viewer(e, viewer_role, viewer_person_id) for e in entities)
    return [e for e in filtered if e is not None]


def _is_element_visible(element: dict, viewer_role: str, viewer_person_id: str | None) -> bool:
    return is_visible_to(
        element.get("sichtbarkeit") or "GM",
        element.get("sichtbarFuer") or [],
        viewer_role,
        viewer_person_id,
    )


def filter_verbindung_for_viewer(edge: dict, viewer_role: str, viewer_person_id: str | None) -> dict | None:
    return edge if _is_element_visible(edge, viewer_role, viewer_person_id) else None


def _endpoint_visible(edge: dict, prefix: str, viewer_role: str, viewer_person_id: str | None) -> bool:
    return is_visible_to(
        edge.get(f"{prefix}Sichtbarkeit") or "GM",
        edge.get(f"{prefix}SichtbarFuer") or [],
        viewer_role,
        viewer_person_id,
    )


def filter_verbindungen_for_viewer(edges: list[dict], viewer_role: str, viewer_person_id: str | None) -> list[dict]:
    """Filters connections by their own visibility *and* both endpoints'.

    Expects each edge to carry von/zu endpoint visibility (see
    repository.list_verbindungen). A connection that is itself public but ends
    at a GM-only NPC still has to go, or it announces that NPC's existence.

    Graph edges do not carry those keys — the graph route filters its edges
    against its already-filtered node set instead (drop_edges_with_hidden_endpoints).
    """
    return [
        e
        for e in edges
        if _is_element_visible(e, viewer_role, viewer_person_id)
        and _endpoint_visible(e, "von", viewer_role, viewer_person_id)
        and _endpoint_visible(e, "zu", viewer_role, viewer_person_id)
    ]


def filter_graph_edges_for_viewer(
    edges: list[dict], visible_node_ids: set[str], viewer_role: str, viewer_person_id: str | None
) -> list[dict]:
    """Graph-shaped counterpart: own visibility plus both endpoints surviving.

    `visible_node_ids` must come from an already-filtered node set, so the
    endpoint check needs no per-edge endpoint metadata here.
    """
    return [
        e
        for e in edges
        if _is_element_visible(e, viewer_role, viewer_person_id)
        and e["source"] in visible_node_ids
        and e["target"] in visible_node_ids
    ]


def filter_graph_nodes_for_viewer(nodes: list[dict], viewer_role: str, viewer_person_id: str | None) -> list[dict]:
    """Graph nodes only carry id/kind/label/visibility — no rich text to redact.

    Callers must additionally drop edges whose endpoints disappeared here,
    otherwise a hidden node's existence still leaks through its edges.
    """
    return [n for n in nodes if _is_element_visible(n, viewer_role, viewer_person_id)]


def filter_gegenstand_for_viewer(item: dict, viewer_role: str, viewer_person_id: str | None) -> dict | None:
    if not _is_element_visible(item, viewer_role, viewer_person_id):
        return None
    result = dict(item)
    result["description"] = redact_rich_text(result.get("description", ""), viewer_role)
    # Unlike Person/Ort/Event, a Gegenstand has no separate notizenSichtbarkeit:
    # its notes are purely GM notes and there is no way to release them to a
    # player. So they are withheld wholesale rather than redacted — redacting
    # would still hand over every unmarked sentence. If player-visible item
    # notes are ever wanted, add a notizenSichtbarkeit field like the entities
    # have instead of loosening this.
    if viewer_role != "GM":
        result["notes"] = ""
    return result


def filter_gegenstaende_for_viewer(items: list[dict], viewer_role: str, viewer_person_id: str | None) -> list[dict]:
    filtered = (filter_gegenstand_for_viewer(i, viewer_role, viewer_person_id) for i in items)
    return [i for i in filtered if i is not None]
