from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm
from app.entities import repository
from app.entities.repository import EVENT_FIELDS, ORT_FIELDS, PERSON_FIELDS
from app.entities.visibility import (
    filter_entities_for_viewer,
    filter_entity_for_viewer,
    filter_verbindungen_for_viewer,
)
from app.entities.schemas import (
    EventCreate,
    EventResponse,
    EventUpdate,
    OrtCreate,
    OrtResponse,
    OrtUpdate,
    PersonCreate,
    PersonResponse,
    PersonUpdate,
    VerbindungCreate,
    VerbindungResponse,
)

router = APIRouter(prefix="/api/campaigns/{campaign_id}", tags=["entities"], dependencies=[Depends(require_campaign_gm)])


def _visible_or_404(node: dict | None, viewer: Viewer, was: str) -> dict:
    """Applies visibility filtering to a single node, 404 if it survives as None.

    Deliberately 404 and not 403: a viewer who may not see something must not
    be able to tell it apart from something that does not exist.
    """
    if node is not None:
        node = filter_entity_for_viewer(node, viewer.role, viewer.person_id)
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{was} nicht gefunden")
    return node


@router.post("/personen", response_model=PersonResponse)
async def create_person(campaign_id: str, body: PersonCreate):
    return await repository.create_node("Person", PERSON_FIELDS, campaign_id, body.model_dump())


@router.get("/personen", response_model=list[PersonResponse])
async def list_personen(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    nodes = await repository.list_nodes("Person", PERSON_FIELDS, campaign_id)
    return filter_entities_for_viewer(nodes, viewer.role, viewer.person_id)


@router.get("/personen/{node_id}", response_model=PersonResponse)
async def get_person(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Person", PERSON_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Person")


@router.patch("/personen/{node_id}", response_model=PersonResponse)
async def update_person(campaign_id: str, node_id: str, body: PersonUpdate):
    node = await repository.update_node("Person", PERSON_FIELDS, campaign_id, node_id, body.model_dump())
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    return node


@router.delete("/personen/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(campaign_id: str, node_id: str):
    if not await repository.delete_node("Person", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")


@router.post("/orte", response_model=OrtResponse)
async def create_ort(campaign_id: str, body: OrtCreate):
    return await repository.create_node("Ort", ORT_FIELDS, campaign_id, body.model_dump())


@router.get("/orte", response_model=list[OrtResponse])
async def list_orte(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    nodes = await repository.list_nodes("Ort", ORT_FIELDS, campaign_id)
    return filter_entities_for_viewer(nodes, viewer.role, viewer.person_id)


@router.get("/orte/{node_id}", response_model=OrtResponse)
async def get_ort(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Ort", ORT_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Ort")


@router.patch("/orte/{node_id}", response_model=OrtResponse)
async def update_ort(campaign_id: str, node_id: str, body: OrtUpdate):
    node = await repository.update_node("Ort", ORT_FIELDS, campaign_id, node_id, body.model_dump())
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ort nicht gefunden")
    return node


@router.delete("/orte/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ort(campaign_id: str, node_id: str):
    if not await repository.delete_node("Ort", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ort nicht gefunden")


@router.post("/events", response_model=EventResponse)
async def create_event(campaign_id: str, body: EventCreate):
    return await repository.create_node("Event", EVENT_FIELDS, campaign_id, body.model_dump())


@router.get("/events", response_model=list[EventResponse])
async def list_events(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    nodes = await repository.list_nodes("Event", EVENT_FIELDS, campaign_id, order_field="title")
    return filter_entities_for_viewer(nodes, viewer.role, viewer.person_id)


@router.get("/events/{node_id}", response_model=EventResponse)
async def get_event(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Event", EVENT_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Event")


@router.patch("/events/{node_id}", response_model=EventResponse)
async def update_event(campaign_id: str, node_id: str, body: EventUpdate):
    node = await repository.update_node("Event", EVENT_FIELDS, campaign_id, node_id, body.model_dump())
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event nicht gefunden")
    return node


@router.delete("/events/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(campaign_id: str, node_id: str):
    if not await repository.delete_node("Event", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event nicht gefunden")


@router.post("/verbindungen", response_model=VerbindungResponse)
async def create_verbindung(campaign_id: str, body: VerbindungCreate):
    edge = await repository.create_verbindung(campaign_id, body.model_dump())
    if edge is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Start- oder Zielentität nicht gefunden")
    return edge


@router.get("/verbindungen", response_model=list[VerbindungResponse])
async def list_verbindungen(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    edges = await repository.list_verbindungen(campaign_id)
    return filter_verbindungen_for_viewer(edges, viewer.role, viewer.person_id)


@router.delete("/verbindungen/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_verbindung(campaign_id: str, edge_id: str):
    if not await repository.delete_verbindung(campaign_id, edge_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verbindung nicht gefunden")
