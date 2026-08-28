"""Server-side visibility filtering for the GM/ALLE/SPEZIFISCH visibility model.

Not yet wired into any route — there is no player-facing route until Phase 4
(player access). This module exists now so the GM-side UI can already set
per-entity and per-notes visibility, and so the actual enforcement logic is
written and testable ahead of time. Filtering must always happen here
(server-side) and never rely on the client hiding data it already received.
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


def filter_entity_for_viewer(entity: dict, viewer_role: str, viewer_person_id: str | None) -> dict | None:
    if not is_visible_to(entity["sichtbarkeit"], entity.get("sichtbarFuer", []), viewer_role, viewer_person_id):
        return None

    result = dict(entity)
    if "description" in result:
        result["description"] = redact_rich_text(result["description"], viewer_role)

    if is_visible_to(
        entity["notizenSichtbarkeit"], entity.get("notizenSichtbarFuer", []), viewer_role, viewer_person_id
    ):
        result["notes"] = redact_rich_text(result.get("notes", ""), viewer_role)
    else:
        result["notes"] = ""
    return result


def filter_entities_for_viewer(entities: list[dict], viewer_role: str, viewer_person_id: str | None) -> list[dict]:
    filtered = (filter_entity_for_viewer(e, viewer_role, viewer_person_id) for e in entities)
    return [e for e in filtered if e is not None]


def filter_verbindung_for_viewer(edge: dict, viewer_role: str, viewer_person_id: str | None) -> dict | None:
    if not is_visible_to(edge["sichtbarkeit"], edge.get("sichtbarFuer", []), viewer_role, viewer_person_id):
        return None
    return edge


def filter_verbindungen_for_viewer(edges: list[dict], viewer_role: str, viewer_person_id: str | None) -> list[dict]:
    filtered = (filter_verbindung_for_viewer(e, viewer_role, viewer_person_id) for e in edges)
    return [e for e in filtered if e is not None]


def filter_gegenstand_for_viewer(item: dict, viewer_role: str, viewer_person_id: str | None) -> dict | None:
    if not is_visible_to(item["sichtbarkeit"], item.get("sichtbarFuer", []), viewer_role, viewer_person_id):
        return None
    result = dict(item)
    result["description"] = redact_rich_text(result.get("description", ""), viewer_role)
    return result


def filter_gegenstaende_for_viewer(items: list[dict], viewer_role: str, viewer_person_id: str | None) -> list[dict]:
    filtered = (filter_gegenstand_for_viewer(i, viewer_role, viewer_person_id) for i in items)
    return [i for i in filtered if i is not None]
