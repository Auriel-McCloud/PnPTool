import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth.dependencies import require_campaign_gm
from app.entities.repository import PERSON_FIELDS, get_node
from app.items import repository
from app.items.schemas import GegenstandCreate, GegenstandResponse, GegenstandUpdate

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/personen/{person_id}/gegenstaende",
    tags=["items"],
    dependencies=[Depends(require_campaign_gm)],
)

UPLOAD_DIR = Path("uploads")
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


@router.post("", response_model=GegenstandResponse)
async def create_item(campaign_id: str, person_id: str, body: GegenstandCreate):
    owner = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if owner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    sichtbarkeit = body.sichtbarkeit
    sichtbar_fuer = body.sichtbarFuer
    if sichtbarkeit is None:
        # Standard: Gegenstände von Spielercharakteren sind automatisch nur für
        # diesen Spieler sichtbar, bei NPCs bleiben sie SL-geheim. Der SL kann
        # das beim Anlegen jederzeit explizit übersteuern.
        if owner["personType"] == "PC":
            sichtbarkeit, sichtbar_fuer = "SPEZIFISCH", [person_id]
        else:
            sichtbarkeit, sichtbar_fuer = "GM", []

    item = await repository.create_gegenstand(
        campaign_id,
        person_id,
        {
            "name": body.name,
            "description": body.description,
            "notes": body.notes,
            "typ": body.typ,
            "eigenschaften": body.eigenschaften,
            "zeigeInGraph": body.zeigeInGraph,
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


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(campaign_id: str, person_id: str, item_id: str):
    if not await repository.delete_gegenstand(campaign_id, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
