from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.auth.dependencies import get_current_claims, require_campaign_gm
from app.auth.security import create_access_token
from app.entities.repository import PERSON_FIELDS, get_node, update_node
from app.items.routes import ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.entities.repository import PERSON_FIELDS as _PERSON_FIELDS, create_node
from app.entities.schemas import PersonCreate
from app.players import repository
from app.players.schemas import (
    CharakterWaehlenRequest,
    CharakterZuordnenRequest,
    LoginRequest,
    PasswortRequest,
    SpielerAnlegenRequest,
    SpielerMeResponse,
    SpielerResponse,
    VorgefertigterCharakter,
)

# Anmeldung laeuft ohne bestehende Sitzung.
login_router = APIRouter(prefix="/api/spieler", tags=["players"])
# Verwaltung durch die Spielleitung.
gm_router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/spieler",
    tags=["players"],
    dependencies=[Depends(require_campaign_gm)],
)

SESSION_COOKIE = "pnptool_session"


def _antwort(spieler: dict) -> SpielerMeResponse:
    return SpielerMeResponse(
        spielerId=spieler["id"],
        benutzername=spieler["benutzername"],
        campaignId=spieler["campaignId"],
        campaignName=spieler["campaignName"],
        personId=spieler["personId"],
        personName=spieler["personName"],
        hatPasswort=bool(spieler.get("passwortHash")),
        personBildUrl=spieler.get("personBildUrl"),
    )


async def require_spieler(claims: dict = Depends(get_current_claims)) -> dict:
    if claims.get("role") != "PLAYER":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "player role required")
    spieler = await repository.get_spieler(claims["sub"])
    if spieler is None:
        # Zugang inzwischen geloescht - fuer den Aufrufer dasselbe wie
        # "nicht angemeldet", er soll sich neu anmelden.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Zugang existiert nicht mehr")
    return spieler


@login_router.post("/login", response_model=SpielerMeResponse)
async def login(body: LoginRequest, response: Response):
    """Anmeldung mit Benutzername, Passwort nur falls gesetzt.

    Gross- und Kleinschreibung spielt keine Rolle. Ist kein Passwort
    hinterlegt, genuegt der Name - in einer privaten Runde soll sich niemand
    erst eines ausdenken muessen.
    """
    spieler = await repository.finde_spieler(body.benutzername)
    if spieler is None or not repository.pruefe_passwort(body.passwort, spieler.get("passwortHash")):
        # Dieselbe Meldung fuer "gibt es nicht" und "falsches Passwort" -
        # sonst liesse sich herausfinden, welche Namen vergeben sind.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Benutzername oder Passwort stimmt nicht")

    token = create_access_token({"role": "PLAYER", "sub": spieler["id"], "name": spieler["benutzername"]})
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return _antwort(spieler)


@login_router.get("/me", response_model=SpielerMeResponse)
async def spieler_me(spieler: dict = Depends(require_spieler)):
    return _antwort(spieler)


@login_router.post("/passwort", response_model=SpielerMeResponse)
async def passwort_setzen(body: PasswortRequest, spieler: dict = Depends(require_spieler)):
    """Der Spieler vergibt sich selbst ein Passwort - oder entfernt es wieder."""
    await repository.setze_passwort(spieler["id"], body.passwort)
    frisch = await repository.get_spieler(spieler["id"])
    assert frisch is not None
    return _antwort(frisch)


@login_router.post("/mein-bild", response_model=SpielerMeResponse)
async def eigenes_charakterportrait_hochladen(
    file: UploadFile = File(...), spieler: dict = Depends(require_spieler)
):
    """Charakterportrait für den eigenen zugeordneten Charakter.

    Anders als bei allen anderen Bild-Uploads im Projekt bewusst KEIN
    `require_campaign_gm` — Mark, 22.09.2026: Spieler haben aktuell keine
    Möglichkeit, selbst ein Bild für ihren Charakter zu setzen. Schreibt
    direkt auf den zugeordneten `Person`-Knoten (dasselbe `bildUrl`-Feld wie
    beim SL-Upload in entities/routes.py), nur MVP-Wege (Datei/Kamera) — ein
    Zeichentool und KI-Bildgenerierung sind separat in CLAUDE.md offen
    notiert, hier bewusst noch nicht gebaut.
    """
    if not spieler.get("personId"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dir ist noch kein Charakter zugeordnet")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Bilddateien (PNG/JPEG/WEBP/GIF) erlaubt")

    inhalt = await file.read()
    if len(inhalt) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 8 MB)")

    campaign_id = spieler["campaignId"]
    person_id = spieler["personId"]
    if await get_node("Person", PERSON_FIELDS, campaign_id, person_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Charakter nicht gefunden")

    import mimetypes
    import uuid

    ordner = UPLOAD_DIR / campaign_id
    ordner.mkdir(parents=True, exist_ok=True)
    endung = mimetypes.guess_extension(file.content_type) or ""
    name = f"portrait-{uuid.uuid4()}{endung}"
    (ordner / name).write_bytes(inhalt)

    await update_node("Person", PERSON_FIELDS, campaign_id, person_id, {"bildUrl": f"/uploads/{campaign_id}/{name}"})

    frisch = await repository.get_spieler(spieler["id"])
    assert frisch is not None
    return _antwort(frisch)


@login_router.post("/abmelden")
async def abmelden(response: Response):
    """Meldet ab. Der Zugang bleibt bestehen - er gehoert dauerhaft zu diesem
    Spieler, anders als die frueheren Beitrittssitzungen."""
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@gm_router.get("", response_model=list[SpielerResponse])
async def spieler_liste(campaign_id: str):
    return await repository.list_spieler(campaign_id)


@gm_router.post("", response_model=SpielerResponse)
async def spieler_anlegen(campaign_id: str, body: SpielerAnlegenRequest):
    if body.personId:
        person = await get_node("Person", PERSON_FIELDS, campaign_id, body.personId)
        if person is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    neu = await repository.create_spieler(campaign_id, body.benutzername, body.personId, body.passwort)
    if neu is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Diesen Benutzernamen gibt es schon")

    for s in await repository.list_spieler(campaign_id):
        if s["id"] == neu["id"]:
            return s
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Anlegen fehlgeschlagen")


@gm_router.post("/{spieler_id}/charakter", response_model=list[SpielerResponse])
async def charakter_zuordnen(campaign_id: str, spieler_id: str, body: CharakterZuordnenRequest):
    if not await repository.setze_charakter(campaign_id, spieler_id, body.personId):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Spieler nicht gefunden")
    return await repository.list_spieler(campaign_id)


@gm_router.delete("/{spieler_id}", status_code=status.HTTP_204_NO_CONTENT)
async def spieler_entfernen(campaign_id: str, spieler_id: str):
    if not await repository.delete_spieler(campaign_id, spieler_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Spieler nicht gefunden")
