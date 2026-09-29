from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_claims, require_gm
from app.auth.repository import get_gm_by_username, get_menue_layouts, set_menue_layouts
from app.auth.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

SESSION_COOKIE = "pnptool_session"


class GmLoginRequest(BaseModel):
    username: str
    password: str


class MeResponse(BaseModel):
    role: str
    username: str | None = None


@router.post("/gm/login", response_model=MeResponse)
async def gm_login(body: GmLoginRequest, response: Response):
    gm = await get_gm_by_username(body.username)
    if gm is None or not verify_password(body.password, gm["passwordHash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid username or password")

    token = create_access_token({"role": "GM", "sub": gm["id"], "username": gm["username"]})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return MeResponse(role="GM", username=gm["username"])


@router.post("/gm/logout")
async def gm_logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me(claims: dict = Depends(get_current_claims)):
    return MeResponse(role=claims.get("role", "UNKNOWN"), username=claims.get("username"))


class MenueSlot(BaseModel):
    ordnung: list[str] = []
    ausgeblendet: list[str] = []


class MenueLayouts(BaseModel):
    pc: MenueSlot = MenueSlot()
    tablet: MenueSlot = MenueSlot()


@router.get("/gm/menue", response_model=MenueLayouts, dependencies=[Depends(require_gm)])
async def menue_lesen(claims: dict = Depends(require_gm)):
    """PC- und Tablet-Layout des SL-Burgermenüs. Handy scrollt und ignoriert das."""
    return await get_menue_layouts(claims["sub"])


@router.patch("/gm/menue", response_model=MenueLayouts, dependencies=[Depends(require_gm)])
async def menue_schreiben(body: MenueLayouts, claims: dict = Depends(require_gm)):
    return await set_menue_layouts(claims["sub"], body.model_dump())
