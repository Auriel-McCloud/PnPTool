import mimetypes
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.entities import repository
from app.entities import filterung
from app.entities.repository import EVENT_FIELDS, FRAKTION_FIELDS, ORT_FIELDS, PERSON_FIELDS
from app.entities.visibility import (
    filter_entities_for_viewer,
    filter_entity_for_viewer,
    filter_verbindungen_for_viewer,
    is_visible_to,
)
from app.entities.schemas import (
    EinflussEintrag,
    EinflussSetzen,
    EventCreate,
    EventResponse,
    EventUpdate,
    FilterOptionen,
    FraktionCreate,
    FraktionResponse,
    FraktionUpdate,
    OrtCreate,
    OrtResponse,
    OrtUpdate,
    PersonCreate,
    PersonResponse,
    PersonUpdate,
    VerbindungCreate,
    VerbindungResponse,
)

router = APIRouter(prefix="/api/campaigns/{campaign_id}", tags=["entities"], dependencies=[Depends(require_campaign_zugang)])


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


async def _sichtbare_kanten(campaign_id: str, viewer: Viewer) -> list[dict]:
    """Verbindungen, die dieser Blickwinkel sehen darf.

    Grundlage für den Beziehungsfilter. Ungefiltert würde eine geheime Kante
    einen Spieler auf einen NPC stossen lassen, den er nicht kennen darf —
    der Treffer allein wäre schon die Auskunft.
    """
    kanten = await repository.list_verbindungen(campaign_id)
    return filter_verbindungen_for_viewer(kanten, viewer.role, viewer.person_id)


async def _aufbereiten(
    knoten: list[dict],
    campaign_id: str,
    viewer: Viewer,
    *,
    namensfeld: str,
    suche: str | None,
    sortierung: str | None,
    verbunden_mit: str | None = None,
    verbindungs_typ: str | None = None,
    nur_entwuerfe: bool = False,
) -> list[dict]:
    """Sichtbarkeit → Entwurf-Filter → Suche → Beziehung → Reihenfolge.

    Die Reihenfolge ist wesentlich: Erst wird weggefiltert, was der Blickwinkel
    nicht sehen darf, und **danach** gesucht. Andersherum könnte ein Spieler
    einen 🔒-redigierten Satz finden, indem er danach sucht — dass er einen
    Treffer bekommt, wäre selbst die Auskunft.

    Entwürfe (istEntwurf=true) werden standardmäßig ausgeblendet — sie gehören
    in die Ideenschmiede, nicht in die normale Ansicht. Mit nur_entwuerfe=True
    werden stattdessen nur Entwürfe gezeigt.
    """
    sichtbar = filter_entities_for_viewer(knoten, viewer.role, viewer.person_id)
    # Entwurf-Filter: standardmäßig ausblenden, für Ideenschmiede invertieren
    if nur_entwuerfe:
        sichtbar = [e for e in sichtbar if e.get("istEntwurf", False)]
    else:
        sichtbar = [e for e in sichtbar if not e.get("istEntwurf", False)]
    sichtbar = filterung.nach_suche(sichtbar, suche, namensfeld)

    braucht_kanten = bool(verbunden_mit or verbindungs_typ) or sortierung == "verbindungen"
    kanten = await _sichtbare_kanten(campaign_id, viewer) if braucht_kanten else []

    if verbunden_mit or verbindungs_typ:
        sichtbar = filterung.nach_beziehung(sichtbar, kanten, verbunden_mit, verbindungs_typ)
    return filterung.sortiere(sichtbar, sortierung, namensfeld, kanten)


@router.post("/personen", response_model=PersonResponse, dependencies=[Depends(require_campaign_gm)])
async def create_person(campaign_id: str, body: PersonCreate):
    return await repository.create_node("Person", PERSON_FIELDS, campaign_id, body.model_dump())


@router.get("/personen", response_model=list[PersonResponse])
async def list_personen(
    campaign_id: str,
    suche: str | None = Query(default=None, description="Sucht in Name, Beschreibung und Notizen."),
    sortierung: filterung.Sortierung | None = Query(default=None),
    personType: Literal["PC", "NPC"] | None = Query(default=None, description="Nur PCs oder nur NPCs."),
    verbundenMit: str | None = Query(
        default=None,
        description="Nur Personen mit einer Verbindung zu dieser Entität (Ort, Event, Person, Gegenstand).",
    ),
    verbindungsTyp: str | None = Query(
        default=None, description="Nur Personen mit einer Verbindung dieser Bezeichnung (z.B. 'Gegner')."
    ),
    viewer: Viewer = Depends(get_viewer),
):
    nodes = await repository.list_nodes("Person", PERSON_FIELDS, campaign_id)
    if personType is not None:
        nodes = [n for n in nodes if n.get("personType") == personType]
    return await _aufbereiten(
        nodes,
        campaign_id,
        viewer,
        namensfeld="name",
        suche=suche,
        sortierung=sortierung,
        verbunden_mit=verbundenMit,
        verbindungs_typ=verbindungsTyp,
    )


@router.get("/personen/{node_id}", response_model=PersonResponse)
async def get_person(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Person", PERSON_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Person")


@router.patch("/personen/{node_id}", response_model=PersonResponse, dependencies=[Depends(require_campaign_gm)])
async def update_person(campaign_id: str, node_id: str, body: PersonUpdate):
    node = await repository.update_node("Person", PERSON_FIELDS, campaign_id, node_id, body.model_dump())
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    return node


@router.delete("/personen/{node_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_person(campaign_id: str, node_id: str):
    if not await repository.delete_node("Person", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")


@router.post("/personen/{node_id}/extra-ep", response_model=PersonResponse, dependencies=[Depends(require_campaign_gm)])
async def extra_ep_erhoehen(campaign_id: str, node_id: str, body: dict):
    """Erhöht die Extra-EP eines PCs um einen Betrag (nur positiv, irreversibel).
    
    Body: {"betrag": 1}  — muss > 0 sein.
    """
    betrag = body.get("betrag", 0)
    if not isinstance(betrag, int) or betrag <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Betrag muss eine positive Ganzzahl sein")
    person = await repository.get_node("Person", PERSON_FIELDS, campaign_id, node_id)
    if not person:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    neu = person.get("extraEP", 0) + betrag
    return await repository.update_node("Person", PERSON_FIELDS, campaign_id, node_id, {"extraEP": neu})


@router.get("/critter", response_model=list[dict])
async def list_critter(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Critter für die Begleiter-Übersicht (`begleiter/BegleiterVerwaltung.tsx`).

    Critter sind seit 20.09.2026 echte NPCs (`Person`, `istCritter=true`,
    siehe Modul-Docstring in `app/begleiter/repository.py`) — diese Route
    liefert nur die schlanken Felder, die eine Kachel braucht (Name/Bild/
    Besitzer), nicht den vollen Charakterbogen.
    """
    roh = await repository.list_critter(campaign_id)
    sichtbar = [
        c for c in roh
        if is_visible_to(c.get("sichtbarkeit") or "GM", c.get("sichtbarFuer") or [], viewer.role, viewer.person_id)
    ]
    return sichtbar


@router.post("/critter/{node_id}/besitzer", response_model=dict, dependencies=[Depends(require_campaign_gm)])
async def critter_besitzer_setzen(campaign_id: str, node_id: str, body: dict):
    person_id = body.get("personId")
    ergebnis = await repository.critter_besitzer_setzen(campaign_id, node_id, person_id)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Critter nicht gefunden")
    return ergebnis


@router.get("/ki", response_model=list[dict])
async def list_ki(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """KIs für die Begleiter-Übersicht — dasselbe Muster wie `list_critter`,
    KI ist seit 20.09.2026 (revidiert) ebenfalls eine echte Person
    (`istKI=true`) statt einer Begleiter-Art."""
    roh = await repository.list_ki(campaign_id)
    sichtbar = [
        c for c in roh
        if is_visible_to(c.get("sichtbarkeit") or "GM", c.get("sichtbarFuer") or [], viewer.role, viewer.person_id)
    ]
    return sichtbar


@router.post("/ki/{node_id}/besitzer", response_model=dict, dependencies=[Depends(require_campaign_gm)])
async def ki_besitzer_setzen(campaign_id: str, node_id: str, body: dict):
    person_id = body.get("personId")
    ergebnis = await repository.ki_besitzer_setzen(campaign_id, node_id, person_id)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "KI nicht gefunden")
    return ergebnis


@router.get("/personen/{node_id}/einfluss", response_model=list[EinflussEintrag])
async def person_einfluss_liste(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    return await repository.person_einfluss_liste(campaign_id, node_id)


@router.post(
    "/personen/{node_id}/einfluss", response_model=list[EinflussEintrag], dependencies=[Depends(require_campaign_gm)]
)
async def person_einfluss_setzen(campaign_id: str, node_id: str, body: EinflussSetzen):
    """Setzt die Einfluss-Stufe einer Person (typischerweise einer KI) auf
    einen Ort/eine Fraktion/ein Event/einen Gegenstand — echte Graphkante,
    damit die Spielleitung sie im Kampf gezielt kappen kann. **Nur SL.**"""
    ergebnis = await repository.person_einfluss_setzen(campaign_id, node_id, body.zielKind, body.zielId, body.stufe)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person oder Ziel nicht gefunden")
    return ergebnis


@router.delete(
    "/personen/{node_id}/einfluss/{ziel_kind}/{ziel_id}",
    response_model=list[EinflussEintrag],
    dependencies=[Depends(require_campaign_gm)],
)
async def person_einfluss_entfernen(campaign_id: str, node_id: str, ziel_kind: str, ziel_id: str):
    ergebnis = await repository.person_einfluss_entfernen(campaign_id, node_id, ziel_kind, ziel_id)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person oder Einflussbereich nicht gefunden")
    return ergebnis


@router.post("/orte", response_model=OrtResponse, dependencies=[Depends(require_campaign_gm)])
async def create_ort(campaign_id: str, body: OrtCreate):
    return await repository.create_node("Ort", ORT_FIELDS, campaign_id, body.model_dump())


@router.get("/orte", response_model=list[OrtResponse])
async def list_orte(
    campaign_id: str,
    suche: str | None = Query(default=None, description="Sucht in Name, Beschreibung und Notizen."),
    sortierung: filterung.Sortierung | None = Query(default=None),
    verbundenMit: str | None = Query(default=None),
    verbindungsTyp: str | None = Query(default=None),
    viewer: Viewer = Depends(get_viewer),
):
    nodes = await repository.list_nodes("Ort", ORT_FIELDS, campaign_id)
    return await _aufbereiten(
        nodes,
        campaign_id,
        viewer,
        namensfeld="name",
        suche=suche,
        sortierung=sortierung,
        verbunden_mit=verbundenMit,
        verbindungs_typ=verbindungsTyp,
    )


@router.get("/entwuerfe", response_model=list[dict])
async def list_entwuerfe(
    campaign_id: str,
    viewer: Viewer = Depends(get_viewer),
):
    """Gibt alle Entwürfe (istEntwurf=true) für die Ideenschmiede zurück."""
    from app.entities import repository
    
    # Alle Entity-Typen sammeln
    entwuerfe = []
    
    # Personen-Entwürfe
    personen = await repository.list_nodes("Person", repository.PERSON_FIELDS, campaign_id)
    for p in personen:
        if p.get("istEntwurf", False):
            p["typ"] = "person"
            entwuerfe.append(p)
    
    # Orte-Entwürfe
    orte = await repository.list_nodes("Ort", repository.ORT_FIELDS, campaign_id)
    for o in orte:
        if o.get("istEntwurf", False):
            o["typ"] = "ort"
            entwuerfe.append(o)
    
    # Events-Entwürfe
    events = await repository.list_nodes("Event", repository.EVENT_FIELDS, campaign_id)
    for e in events:
        if e.get("istEntwurf", False):
            e["typ"] = "event"
            entwuerfe.append(e)
    
    # Fraktions-Entwürfe
    fraktionen = await repository.list_nodes("Fraktion", repository.FRAKTION_FIELDS, campaign_id)
    for f in fraktionen:
        if f.get("istEntwurf", False):
            f["typ"] = "Fraktion"
            entwuerfe.append(f)
    
    # Wiki-Seiten-Entwürfe
    from app.wiki import repository as wiki_repository
    seiten = await wiki_repository.list_seiten(campaign_id)
    for s in seiten:
        if s.get("istEntwurf", False):
            s["typ"] = "WikiSeite"
            s["name"] = s.get("titel", "Unbenannt")
            entwuerfe.append(s)
    
    # Gegenstands-Entwürfe
    from app.items import repository as items_repository
    gegenstaende = await items_repository.list_alle_gegenstaende(campaign_id)
    for g in gegenstaende:
        if g.get("istEntwurf", False):
            g["typ"] = "Gegenstand"
            entwuerfe.append(g)
    
    # Nach Sichtbarkeit filtern
    sichtbar = filter_entities_for_viewer(entwuerfe, viewer.role, viewer.person_id)
    return sichtbar


@router.get("/orte/{node_id}", response_model=OrtResponse)
async def get_ort(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Ort", ORT_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Ort")


@router.patch("/orte/{node_id}", response_model=OrtResponse, dependencies=[Depends(require_campaign_gm)])
async def update_ort(campaign_id: str, node_id: str, body: OrtUpdate):
    node = await repository.update_node("Ort", ORT_FIELDS, campaign_id, node_id, body.model_dump())
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ort nicht gefunden")
    return node


@router.delete("/orte/{node_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_ort(campaign_id: str, node_id: str):
    if not await repository.delete_node("Ort", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ort nicht gefunden")


@router.post("/events", response_model=EventResponse, dependencies=[Depends(require_campaign_gm)])
async def create_event(campaign_id: str, body: EventCreate):
    return await repository.create_node("Event", EVENT_FIELDS, campaign_id, body.model_dump())


@router.get("/events", response_model=list[EventResponse])
async def list_events(
    campaign_id: str,
    suche: str | None = Query(default=None, description="Sucht in Titel, Zeitpunkt, Beschreibung und Notizen."),
    sortierung: filterung.Sortierung | None = Query(default=None),
    verbundenMit: str | None = Query(default=None),
    verbindungsTyp: str | None = Query(default=None),
    viewer: Viewer = Depends(get_viewer),
):
    nodes = await repository.list_nodes("Event", EVENT_FIELDS, campaign_id, order_field="title")
    return await _aufbereiten(
        nodes,
        campaign_id,
        viewer,
        namensfeld="title",
        suche=suche,
        sortierung=sortierung,
        verbunden_mit=verbundenMit,
        verbindungs_typ=verbindungsTyp,
    )


@router.get("/events/{node_id}", response_model=EventResponse)
async def get_event(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Event", EVENT_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Event")


@router.patch("/events/{node_id}", response_model=EventResponse, dependencies=[Depends(require_campaign_gm)])
async def update_event(campaign_id: str, node_id: str, body: EventUpdate):
    node = await repository.update_node("Event", EVENT_FIELDS, campaign_id, node_id, body.model_dump())
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event nicht gefunden")
    return node


@router.delete("/events/{node_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_event(campaign_id: str, node_id: str):
    if not await repository.delete_node("Event", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event nicht gefunden")


@router.post("/fraktionen", response_model=FraktionResponse, dependencies=[Depends(require_campaign_gm)])
async def create_fraktion(campaign_id: str, body: FraktionCreate):
    return await repository.create_node("Fraktion", FRAKTION_FIELDS, campaign_id, body.model_dump())


@router.get("/fraktionen", response_model=list[FraktionResponse])
async def list_fraktionen(
    campaign_id: str,
    suche: str | None = Query(default=None, description="Sucht in Name, Beschreibung und Notizen."),
    sortierung: filterung.Sortierung | None = Query(default=None),
    verbundenMit: str | None = Query(default=None),
    verbindungsTyp: str | None = Query(default=None),
    viewer: Viewer = Depends(get_viewer),
):
    nodes = await repository.list_nodes("Fraktion", FRAKTION_FIELDS, campaign_id)
    return await _aufbereiten(
        nodes,
        campaign_id,
        viewer,
        namensfeld="name",
        suche=suche,
        sortierung=sortierung,
        verbunden_mit=verbundenMit,
        verbindungs_typ=verbindungsTyp,
    )


@router.get("/fraktionen/{node_id}", response_model=FraktionResponse)
async def get_fraktion(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Fraktion", FRAKTION_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Fraktion")


@router.patch("/fraktionen/{node_id}", response_model=FraktionResponse, dependencies=[Depends(require_campaign_gm)])
async def update_fraktion(campaign_id: str, node_id: str, body: FraktionUpdate):
    node = await repository.update_node("Fraktion", FRAKTION_FIELDS, campaign_id, node_id, body.model_dump())
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fraktion nicht gefunden")
    return node


@router.delete("/fraktionen/{node_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_fraktion(campaign_id: str, node_id: str):
    if not await repository.delete_node("Fraktion", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fraktion nicht gefunden")


@router.post("/verbindungen", response_model=VerbindungResponse, dependencies=[Depends(require_campaign_gm)])
async def create_verbindung(campaign_id: str, body: VerbindungCreate):
    edge = await repository.create_verbindung(campaign_id, body.model_dump())
    if edge is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Start- oder Zielentität nicht gefunden")
    return edge


@router.get("/verbindungen", response_model=list[VerbindungResponse])
async def list_verbindungen(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    edges = await repository.list_verbindungen(campaign_id)
    return filter_verbindungen_for_viewer(edges, viewer.role, viewer.person_id)


# Beschriftung eines Filterziels. Gegenstände erscheinen nur, wenn sie
# ausdrücklich im Graph geführt werden (MacGuffins) — normale Inventarstücke
# würden die Auswahl überschwemmen.
_FILTER_QUELLEN: tuple[tuple[str, list[str], str], ...] = (
    ("Person", PERSON_FIELDS, "name"),
    ("Ort", ORT_FIELDS, "name"),
    ("Event", EVENT_FIELDS, "title"),
    ("Fraktion", FRAKTION_FIELDS, "name"),
)


async def _beschriftungen(campaign_id: str, viewer: Viewer) -> dict[str, tuple[str, str]]:
    """ID → (Art, Name) für alles, was dieser Blickwinkel sehen darf.

    Sichtbarkeitsgefiltert, weil die Beschriftung sonst den Namen eines
    geheimen NPCs im Filter-Dropdown offenlegte — dieselbe Überlegung wie beim
    Kampf-Alias.
    """
    beschriftung: dict[str, tuple[str, str]] = {}
    for label, felder, namensfeld in _FILTER_QUELLEN:
        knoten = await repository.list_nodes(label, felder, campaign_id, order_field=namensfeld)
        for eintrag in filter_entities_for_viewer(knoten, viewer.role, viewer.person_id):
            beschriftung[eintrag["id"]] = (label, str(eintrag.get(namensfeld) or ""))
    return beschriftung


@router.get("/filteroptionen", response_model=FilterOptionen)
async def get_filteroptionen(
    campaign_id: str,
    art: Literal["personen", "orte", "events", "fraktionen"] = Query(
        description="Für welche Liste die Optionen gelten sollen."
    ),
    personType: Literal["PC", "NPC"] | None = Query(default=None),
    viewer: Viewer = Depends(get_viewer),
):
    """Welche Beziehungsarten und Ziele es für diese Liste wirklich gibt.

    Speist die Filterauswahl der Oberfläche. Bewusst serverseitig: das
    Frontend soll nicht aus einer ungefilterten Kantenliste ableiten müssen,
    was es anbieten darf — und ohne diese Route müsste es dafür alle
    Verbindungen laden, auch die, die es gar nicht sehen darf.
    """
    label, felder, namensfeld = {
        "personen": ("Person", PERSON_FIELDS, "name"),
        "orte": ("Ort", ORT_FIELDS, "name"),
        "events": ("Event", EVENT_FIELDS, "title"),
        "fraktionen": ("Fraktion", FRAKTION_FIELDS, "name"),
    }[art]

    knoten = await repository.list_nodes(label, felder, campaign_id, order_field=namensfeld)
    if personType is not None:
        knoten = [n for n in knoten if n.get("personType") == personType]
    sichtbar = filter_entities_for_viewer(knoten, viewer.role, viewer.person_id)

    kanten = await _sichtbare_kanten(campaign_id, viewer)
    beschriftung = await _beschriftungen(campaign_id, viewer)
    return filterung.filteroptionen(sichtbar, kanten, beschriftung)


@router.delete("/verbindungen/{edge_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_verbindung(campaign_id: str, edge_id: str):
    if not await repository.delete_verbindung(campaign_id, edge_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verbindung nicht gefunden")


# --- Bilder ------------------------------------------------------------
# Aussehen einer Person, eines Ortes oder einer Szene. Die Spielleitung kann
# es per Blitz an alle Spieler schicken (app/mitteilungen).
#
# Gleiche Ablage wie die Gegenstandsbilder (uploads/<campaign_id>/): beim
# Sichern gibt es nur einen Ordner.

UPLOAD_DIR = Path("uploads")
ERLAUBTE_BILDTYPEN = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_BILD_BYTES = 8 * 1024 * 1024

# Welches Label und welche Felder hinter einem Pfadsegment stehen. Weisse
# Liste, weil das Label direkt in die Cypher-Abfrage eingeht.
_ENTITAETEN = {
    "personen": ("Person", PERSON_FIELDS, "Person"),
    "orte": ("Ort", ORT_FIELDS, "Ort"),
    "events": ("Event", EVENT_FIELDS, "Event"),
    "fraktionen": ("Fraktion", FRAKTION_FIELDS, "Fraktion"),
}


@router.post("/personen/{node_id}/bild", dependencies=[Depends(require_campaign_gm)])
async def upload_person_bild(campaign_id: str, node_id: str, file: UploadFile = File(...)):
    return await _entitaets_bild_hochladen(campaign_id, "personen", node_id, file)


@router.post("/orte/{node_id}/bild", dependencies=[Depends(require_campaign_gm)])
async def upload_ort_bild(campaign_id: str, node_id: str, file: UploadFile = File(...)):
    return await _entitaets_bild_hochladen(campaign_id, "orte", node_id, file)


@router.post("/events/{node_id}/bild", dependencies=[Depends(require_campaign_gm)])
async def upload_event_bild(campaign_id: str, node_id: str, file: UploadFile = File(...)):
    return await _entitaets_bild_hochladen(campaign_id, "events", node_id, file)


@router.post("/fraktionen/{node_id}/bild", dependencies=[Depends(require_campaign_gm)])
async def upload_fraktion_bild(campaign_id: str, node_id: str, file: UploadFile = File(...)):
    return await _entitaets_bild_hochladen(campaign_id, "fraktionen", node_id, file)


async def _entitaets_bild_hochladen(campaign_id: str, art: str, node_id: str, file: UploadFile) -> dict:
    # Vier explizite Routen statt einer mit `{art}`: eine generische Route
    # würde auch `/rassen/{id}/bild` abfangen und "Unbekannte Entität"
    # antworten, weil der entities-Router vor dem Rassen-Router registriert ist.
    label, felder, bezeichnung = _ENTITAETEN[art]

    if file.content_type not in ERLAUBTE_BILDTYPEN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Bilddateien (PNG/JPEG/WEBP/GIF) erlaubt")

    inhalt = await file.read()
    if len(inhalt) > MAX_BILD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 8 MB)")

    if await repository.get_node(label, felder, campaign_id, node_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{bezeichnung} nicht gefunden")

    ordner = UPLOAD_DIR / campaign_id
    ordner.mkdir(parents=True, exist_ok=True)
    endung = mimetypes.guess_extension(file.content_type) or ""
    # Neuer Name: ein hochgeladener Name koennte aus dem Ordner ausbrechen.
    name = f"{art}-{uuid.uuid4()}{endung}"
    (ordner / name).write_bytes(inhalt)

    aktualisiert = await repository.update_node(
        label, felder, campaign_id, node_id, {"bildUrl": f"/uploads/{campaign_id}/{name}"}
    )
    if aktualisiert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{bezeichnung} nicht gefunden")
    return aktualisiert


async def speichere_entitaets_bild_bytes(campaign_id: str, art: str, node_id: str, inhalt: bytes, content_type: str) -> dict | None:
    """Gegenstück zu `_entitaets_bild_hochladen`, aber für Bytes statt eines
    `UploadFile` — genutzt vom KI-Bildgenerator (`app/ki/routes.py`), der ein
    generiertes Bild speichert statt eines hochgeladenen. Dieselbe Ordner-
    struktur/Namenskonvention, damit es keinen zweiten Ablage-Mechanismus gibt.
    """
    if art not in _ENTITAETEN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unbekannte Entitätsart '{art}'")
    label, felder, bezeichnung = _ENTITAETEN[art]

    if await repository.get_node(label, felder, campaign_id, node_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{bezeichnung} nicht gefunden")

    ordner = UPLOAD_DIR / campaign_id
    ordner.mkdir(parents=True, exist_ok=True)
    endung = mimetypes.guess_extension(content_type) or ".png"
    name = f"{art}-ki-{uuid.uuid4()}{endung}"
    (ordner / name).write_bytes(inhalt)

    return await repository.update_node(
        label, felder, campaign_id, node_id, {"bildUrl": f"/uploads/{campaign_id}/{name}"}
    )
