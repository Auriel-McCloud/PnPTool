import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth.dependencies import require_campaign_gm
from app.entities.repository import PERSON_FIELDS, get_node
from app.items import repository
from app.items.schemas import GegenstandCreate, GegenstandMitBesitzer, GegenstandResponse, GegenstandUpdate, ZuweisenRequest

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/personen/{person_id}/gegenstaende",
    tags=["items"],
    dependencies=[Depends(require_campaign_gm)],
)

# Kampagnenweite Übersicht (alle Gegenstände aller Personen) — eigener Router,
# weil der Pfad kein {person_id} enthält und daher nicht in obiges Prefix passt.
campaign_router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/gegenstaende",
    tags=["items"],
    dependencies=[Depends(require_campaign_gm)],
)

UPLOAD_DIR = Path("uploads")
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


@campaign_router.get("", response_model=list[GegenstandMitBesitzer])
async def list_all_items(campaign_id: str):
    return await repository.list_alle_gegenstaende(campaign_id)


def _default_sichtbarkeit(person_type: str, person_id: str) -> tuple[str, list[str]]:
    # Standard: Gegenstände von Spielercharakteren sind automatisch nur für
    # diesen Spieler sichtbar, bei NPCs bleiben sie SL-geheim. Der SL kann das
    # beim Anlegen/Zuweisen jederzeit explizit übersteuern.
    if person_type == "PC":
        return "SPEZIFISCH", [person_id]
    return "GM", []


@router.post("", response_model=GegenstandResponse)
async def create_item(campaign_id: str, person_id: str, body: GegenstandCreate):
    owner = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if owner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    sichtbarkeit = body.sichtbarkeit
    sichtbar_fuer = body.sichtbarFuer
    if sichtbarkeit is None:
        sichtbarkeit, sichtbar_fuer = _default_sichtbarkeit(owner["personType"], person_id)

    item = await repository.create_gegenstand(
        campaign_id,
        person_id,
        {
            "name": body.name,
            "description": body.description,
            "notes": body.notes,
            "typ": body.typ,
            "preis": body.preis,
            "kraft": body.kraft,
            "eigenschaften": body.eigenschaften,
            "zeigeInGraph": body.zeigeInGraph,
            "einzigartig": body.einzigartig,
            "hatMenge": body.hatMenge,
            "menge": body.menge,
            "istVorlage": body.istVorlage,
            "seltenheit": body.seltenheit,
            "sichtbarkeit": sichtbarkeit,
            "sichtbarFuer": sichtbar_fuer or [],
        },
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    return item


@router.get("", response_model=list[GegenstandResponse])
async def list_items(campaign_id: str, person_id: str):
    return await repository.list_gegenstaende(campaign_id, person_id)


@router.patch("/{item_id}", response_model=GegenstandResponse)
async def update_item(campaign_id: str, person_id: str, item_id: str, body: GegenstandUpdate):
    item = await repository.update_gegenstand(campaign_id, item_id, body.model_dump())
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    return item


@router.post("/{item_id}/bild", response_model=GegenstandResponse)
async def upload_bild(campaign_id: str, person_id: str, item_id: str, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Bilddateien (PNG/JPEG/WEBP/GIF) erlaubt")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 8 MB)")

    campaign_dir = UPLOAD_DIR / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    ext = mimetypes.guess_extension(file.content_type) or ""
    filename = f"{uuid.uuid4()}{ext}"
    (campaign_dir / filename).write_bytes(contents)

    item = await repository.set_bild_url(campaign_id, item_id, f"/uploads/{campaign_id}/{filename}")
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    return item


@router.post("/{item_id}/zuweisen", response_model=GegenstandResponse)
async def zuweisen(campaign_id: str, person_id: str, item_id: str, body: ZuweisenRequest):
    source = await repository.get_gegenstand(campaign_id, item_id)
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    if not source["istVorlage"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Vorlagen können zugewiesen werden")

    ziel = await get_node("Person", PERSON_FIELDS, campaign_id, body.zielPersonId)
    if ziel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zielperson nicht gefunden")

    sichtbarkeit, sichtbar_fuer = _default_sichtbarkeit(ziel["personType"], body.zielPersonId)
    copy = await repository.assign_copy(campaign_id, source, body.zielPersonId, sichtbarkeit, sichtbar_fuer)
    if copy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zuweisen fehlgeschlagen")
    return copy


@router.post("/{item_id}/besitzer", response_model=GegenstandResponse)
async def besitzer_wechseln(campaign_id: str, person_id: str, item_id: str, body: ZuweisenRequest):
    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    ziel = await get_node("Person", PERSON_FIELDS, campaign_id, body.zielPersonId)
    if ziel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zielperson nicht gefunden")

    alter_besitzer = await repository.get_owner_id(campaign_id, item_id)
    updates: dict = {}
    if item["sichtbarkeit"] == "SPEZIFISCH" and item["sichtbarFuer"] == [alter_besitzer]:
        # Sichtbarkeit war exklusiv auf den alten Besitzer zugeschnitten (Standardfall
        # beim Anlegen) — für den neuen Besitzer frisch berechnen. War die Sichtbarkeit
        # bewusst breiter gewählt (ALLE, GM oder mehrere Spieler), bleibt sie unangetastet.
        sichtbarkeit, sichtbar_fuer = _default_sichtbarkeit(ziel["personType"], body.zielPersonId)
        updates = {"sichtbarkeit": sichtbarkeit, "sichtbarFuer": sichtbar_fuer}

    moved = await repository.transfer_owner(campaign_id, item_id, body.zielPersonId)
    if moved is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Übertragung fehlgeschlagen")
    if updates:
        moved = await repository.update_gegenstand(campaign_id, item_id, updates)
    return moved


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(campaign_id: str, person_id: str, item_id: str):
    if not await repository.delete_gegenstand(campaign_id, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
