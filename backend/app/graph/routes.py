from collections import deque

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_campaign_gm
from app.graph.repository import get_all_edges, get_all_nodes

router = APIRouter(prefix="/api/campaigns/{campaign_id}/graph", tags=["graph"], dependencies=[Depends(require_campaign_gm)])


def _neighborhood(focus: str, edges: list[dict], depth: int) -> set[str]:
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge["source"], set()).add(edge["target"])
        adjacency.setdefault(edge["target"], set()).add(edge["source"])

    visited = {focus}
    frontier = deque([(focus, 0)])
    while frontier:
        node_id, dist = frontier.popleft()
        if dist >= depth:
            continue
        for neighbor in adjacency.get(node_id, ()):
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append((neighbor, dist + 1))
    return visited


@router.get("")
async def get_graph(campaign_id: str, focus: str | None = None, depth: int = Query(default=2, ge=1, le=5)):
    nodes = await get_all_nodes(campaign_id)
    edges = await get_all_edges(campaign_id)

    if focus is not None:
        visible_ids = _neighborhood(focus, edges, depth)
        nodes = [n for n in nodes if n["id"] in visible_ids]
        edges = [e for e in edges if e["source"] in visible_ids and e["target"] in visible_ids]

    return {
        "nodes": [{"data": n} for n in nodes],
        "edges": [{"data": e} for e in edges],
    }
