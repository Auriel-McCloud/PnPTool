from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.auth.dependencies import require_campaign_gm, require_campaign_zugang
from app.auth.dependencies import require_gm
from app.campaigns.export_import import export_campaign_zip, import_campaign_zip
from app.campaigns.repository import (
    EINSTELLUNGEN_DEFAULTS,
    create_campaign,
    get_einstellungen,
    list_campaigns_for_gm,
    set_einstellungen,
)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

# Maximale Grösse einer Import-ZIP — grosszügiger als ein einzelnes Bild
# (items/routes.py::MAX_BILD_BYTES), weil hier viele Bilder + der komplette
# Graph in einer Datei stecken.
MAX_IMPORT_BYTES = 200 * 1024 * 1024


class CampaignCreateRequest(BaseModel):
    name: str
    ruleset: str = "neotopia"


class CampaignResponse(BaseModel):
    id: str
    name: str
    regelsystemId: str = ""
    regelsystem: str = "neotopia"


@router.post("", response_model=CampaignResponse)
async def create(body: CampaignCreateRequest, claims: dict = Depends(require_gm)):
    return await create_campaign(body.name, body.ruleset, claims["sub"])


@router.get("", response_model=list[CampaignResponse])
async def list_mine(claims: dict = Depends(require_gm)):
    return await list_campaigns_for_gm(claims["sub"])


# --- Export/Import -----------------------------------------------------
# "/import" MUSS vor "/{campaign_id}/export" bzw. jeder anderen
# {campaign_id}-Route dieses Prefixes registriert sein: FastAPI matcht nach
# Registrierungsreihenfolge, nicht nach Spezifität (siehe Fallstricke in
# pnptool-development-Skill) — sonst würde "/api/campaigns/import" von einer
# {campaign_id}-Route mit campaign_id="import" abgefangen.


@router.post("/import", response_model=CampaignResponse)
async def import_campaign(claims: dict = Depends(require_gm), datei: UploadFile = File(...)):
    """Importiert eine per `/export` erzeugte ZIP-Datei als NEUE Kampagne.

    Jeder eingeloggte GM darf importieren — es entsteht dabei immer eine neue
    Kampagne mit neuer ID, die ausschliesslich dem importierenden GM gehört
    (`OWNS`-Kante). Es wird nie eine bestehende Kampagne überschrieben.
    """
    inhalt = await datei.read()
    if len(inhalt) > MAX_IMPORT_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 200 MB)")
    try:
        return await import_campaign_zip(inhalt, claims["sub"])
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.get("/{campaign_id}/export", dependencies=[Depends(require_campaign_gm)])
async def export_campaign(campaign_id: str):
    """Liefert die komplette Kampagne (alle Knoten/Kanten/Bilder/Spieler-
    Accounts) als ZIP-Datei zum Download. Nur die Spielleitung dieser
    Kampagne (require_campaign_gm prüft Besitz)."""
    try:
        inhalt, dateiname = await export_campaign_zip(campaign_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    return Response(
        content=inhalt,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{dateiname}"'},
    )


# Kampagnenweite Spieleinstellungen. Lesen darf jeder mit Zugang — die
# Spieler-Oberfläche braucht z.B. zu wissen, ob Gewicht angezeigt wird.
# Ändern darf nur die Spielleitung.
einstellungen_router = APIRouter(prefix="/api/campaigns/{campaign_id}/einstellungen", tags=["campaigns"])


@einstellungen_router.get("", dependencies=[Depends(require_campaign_zugang)])
async def einstellungen_lesen(campaign_id: str) -> dict:
    return await get_einstellungen(campaign_id)


@einstellungen_router.patch("", dependencies=[Depends(require_campaign_gm)])
async def einstellungen_aendern(campaign_id: str, body: dict) -> dict:
    """Ändert einzelne Einstellungen.

    Bewusst ein offenes dict statt eines festen Schemas: die Sammlung soll
    wachsen können, ohne dass hier und im Frontend jedes Mal ein Feld
    nachgetragen werden muss. Unbekannte Schlüssel verwirft das Repository.
    """
    return await set_einstellungen(campaign_id, body)


@einstellungen_router.get("/standard", dependencies=[Depends(require_campaign_zugang)])
async def einstellungen_standard(campaign_id: str) -> dict:
    """Die Ausgangswerte — damit die Oberfläche weiß, was es überhaupt gibt."""
    return EINSTELLUNGEN_DEFAULTS


@einstellungen_router.post("/ep-erhoehen", dependencies=[Depends(require_campaign_gm)])
async def kampagnen_ep_erhoehen(campaign_id: str, body: dict) -> dict:
    """Erhöht die kampagnenweiten EP um einen Betrag (nur positiv, irreversibel).
    
    Body: {"betrag": 1}  — muss > 0 sein.
    """
    from fastapi import HTTPException
    betrag = body.get("betrag", 0)
    if not isinstance(betrag, int) or betrag <= 0:
        raise HTTPException(400, "Betrag muss eine positive Ganzzahl sein")
    aktuell = await get_einstellungen(campaign_id)
    neu = aktuell.get("kampagnenEP", 0) + betrag
    return await set_einstellungen(campaign_id, {"kampagnenEP": neu})
