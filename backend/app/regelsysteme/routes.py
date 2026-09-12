"""API-Routen für Regelsysteme.

Regelsysteme sind systemübergreifend (nicht an eine Kampagne gebunden).
Nur SL darf anlegen/bearbeiten/löschen.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_gm
from app.regelsysteme import repository
from app.regelsysteme.schemas import (
    RegelsystemCreate,
    RegelsystemResponse,
    RegelsystemUpdate,
)

router = APIRouter(prefix="/api/regelsysteme", tags=["regelsysteme"])


@router.get("", response_model=list[RegelsystemResponse])
async def liste():
    """Alle Regelsysteme auflisten (öffentlich lesbar)."""
    return await repository.liste()


@router.get("/{regelsystem_id}", response_model=RegelsystemResponse)
async def einzeln(regelsystem_id: str):
    """Ein Regelsystem abrufen."""
    result = await repository.einzeln(regelsystem_id)
    if not result:
        raise HTTPException(404, "Regelsystem nicht gefunden")
    return result


@router.post("", response_model=RegelsystemResponse, dependencies=[Depends(require_gm)])
async def anlegen(body: RegelsystemCreate):
    """Neues Regelsystem erstellen (nur SL)."""
    return await repository.anlegen(body.name, body.beschreibung)


@router.patch(
    "/{regelsystem_id}",
    response_model=RegelsystemResponse,
    dependencies=[Depends(require_gm)],
)
async def aendern(regelsystem_id: str, body: RegelsystemUpdate):
    """Regelsystem bearbeiten (nur SL)."""
    result = await repository.aendern(regelsystem_id, body.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(404, "Regelsystem nicht gefunden")
    return result


@router.delete(
    "/{regelsystem_id}",
    dependencies=[Depends(require_gm)],
)
async def loeschen(regelsystem_id: str):
    """Regelsystem löschen (nur SL, nur wenn keine Kampagnen es nutzen)."""
    erfolg = await repository.loeschen(regelsystem_id)
    if not erfolg:
        raise HTTPException(
            409,
            "Regelsystem kann nicht gelöscht werden — noch Kampagnen verknüpft oder nicht gefunden",
        )
    return {"status": "gelöscht"}
