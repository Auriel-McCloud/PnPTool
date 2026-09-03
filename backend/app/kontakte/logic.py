"""Seiteneffektfreie Fachregeln für Kontaktwissen und Messenger."""

from collections import deque
import json

from app.entities.visibility import filter_graph_edges_for_viewer, filter_graph_nodes_for_viewer

KONTAKTSTUFEN = ("GESEHEN", "GESPROCHEN", "KONTAKT_AUSGETAUSCHT")
KONTAKTANFRAGE_STATUS = ("KEINE", "OFFEN", "ANGENOMMEN", "ABGELEHNT")
_STUFEN_RANG = {name: rang for rang, name in enumerate(KONTAKTSTUFEN)}

_RASSEN_ALIAS = {
    "mensch": "Unbekannter Mensch",
    "ork": "Unbekannter Ork",
    "elf": "Unbekannter Elf",
    "zwerg": "Unbekannter Zwerg",
    "troll": "Unbekannter Troll",
}


def standard_alias(rasse: str | None) -> str:
    """Liefert den gemeinsamen NPC-Standardalias aus der Rasse."""
    sauber = (rasse or "").strip()
    if not sauber:
        return "Unbekannte Person"
    return _RASSEN_ALIAS.get(sauber.casefold(), f"Unbekannter {sauber}")


def effektiver_alias(npc_standard: str | None, persoenlicher_alias: str | None) -> str:
    """Persönlicher Alias gewinnt; leer bedeutet NPC-Standard."""
    persoenlich = (persoenlicher_alias or "").strip()
    if persoenlich:
        return persoenlich
    standard = (npc_standard or "").strip()
    return standard or "Unbekannte Person"


def ist_mindestens_stufe(aktuell: str | None, erforderlich: str) -> bool:
    """Vergleicht Kontaktstufen fail-closed."""
    return _STUFEN_RANG.get(aktuell or "", -1) >= _STUFEN_RANG.get(erforderlich, len(KONTAKTSTUFEN))


def kann_kontakt_anfragen(kontaktstufe: str | None, anfrage_status: str | None) -> bool:
    """Eine Anfrage ist erst nach einem Gespräch und nur einmalig möglich."""
    return ist_mindestens_stufe(kontaktstufe, "GESPROCHEN") and (anfrage_status or "KEINE") == "KEINE"


def kontakt_anzeige(
    echter_name: str | None,
    npc_standard: str | None,
    persoenlicher_alias: str | None,
    echter_name_bekannt: bool,
) -> dict[str, str | None]:
    """Baut die sichere Kontaktanzeige für einen Spieler.

    Der Alias bleibt auch nach Bekanntwerden des echten Namens erhalten. Der
    echte Name wird nur als separates Feld freigegeben.
    """
    return {
        "alias": effektiver_alias(npc_standard, persoenlicher_alias),
        "echterName": echter_name if echter_name_bekannt else None,
    }


def normalisiere_nachrichteninhalt(inhalt: str | None) -> str:
    """Speichert Klartext als TipTap-JSON und erhält Unicode-Emojis.

    Bereits gültige TipTap-Dokumente werden bytegenau belassen. Das erlaubt
    den Übergang von Klartext zu TipTap, ohne vorhandene Markierungen oder
    Attribute beim nächsten Speichern umzuschreiben.
    """
    roh = inhalt or ""
    try:
        dokument = json.loads(roh)
    except (json.JSONDecodeError, TypeError):
        dokument = None
    if isinstance(dokument, dict) and dokument.get("type") == "doc":
        return roh

    absätze = []
    for zeile in roh.splitlines() or [""]:
        absatz: dict[str, object] = {"type": "paragraph"}
        if zeile:
            absatz["content"] = [{"type": "text", "text": zeile}]
        absätze.append(absatz)
    return json.dumps({"type": "doc", "content": absätze}, ensure_ascii=False)


def erreichbare_npcs(
    pc_id: str,
    nodes: list[dict],
    edges: list[dict],
    max_kanten: int = 7,
    viewer_role: str = "PLAYER",
    viewer_person_id: str | None = None,
) -> set[str]:
    """Findet NPCs über sichtbare, ungerichtete Graphwege.

    Ein Ort/Event mit ``kontaktwissenWeitergeben=False`` darf erreicht werden,
    wird aber nicht weiter durchlaufen. Die Obergrenze zählt Kanten, nicht
    Knoten. Die Sichtbarkeitsprüfung passiert vor der Suche.
    """
    if max_kanten < 0:
        return set()

    sichtbare_nodes = filter_graph_nodes_for_viewer(nodes, viewer_role, viewer_person_id)
    node_by_id = {node["id"]: node for node in sichtbare_nodes}

    # Der eigene PC ist der zulässige Suchstartpunkt, auch wenn sein
    # Charakterblatt selbst noch SL-sichtbar ist. Andere verborgene Knoten
    # bleiben aus dem Kontaktweg ausgeschlossen.
    if pc_id not in node_by_id and viewer_person_id == pc_id:
        start_node = next(
            (
                node
                for node in nodes
                if node.get("id") == pc_id
                and node.get("kind") == "Person"
                and node.get("personType") == "PC"
            ),
            None,
        )
        if start_node is not None:
            node_by_id[pc_id] = start_node

    sichtbare_edges = filter_graph_edges_for_viewer(
        edges, set(node_by_id), viewer_role, viewer_person_id
    )
    adjacency: dict[str, set[str]] = {}
    for edge in sichtbare_edges:
        adjacency.setdefault(edge["source"], set()).add(edge["target"])
        adjacency.setdefault(edge["target"], set()).add(edge["source"])

    if pc_id not in node_by_id:
        return set()

    gefunden: set[str] = set()
    besucht = {pc_id}
    frontier = deque([(pc_id, 0)])
    while frontier:
        current_id, distanz = frontier.popleft()
        current = node_by_id[current_id]
        if distanz >= max_kanten:
            continue
        if current.get("kind") in {"Ort", "Event"} and current.get("kontaktwissenWeitergeben") is False:
            continue

        for nachbar_id in adjacency.get(current_id, ()):
            if nachbar_id in besucht:
                continue
            besucht.add(nachbar_id)
            nachbar = node_by_id.get(nachbar_id)
            if nachbar is None:
                continue
            neue_distanz = distanz + 1
            if nachbar.get("kind") == "Person" and nachbar.get("personType") == "NPC":
                gefunden.add(nachbar_id)
            if neue_distanz < max_kanten:
                frontier.append((nachbar_id, neue_distanz))

    return gefunden
