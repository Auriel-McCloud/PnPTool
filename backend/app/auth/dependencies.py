import jwt
from fastapi import Cookie, Depends, HTTPException, status

from app.auth.security import decode_access_token
from app.campaigns.repository import campaign_owned_by


def get_current_claims(pnptool_session: str | None = Cookie(default=None)) -> dict:
    if pnptool_session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    try:
        return decode_access_token(pnptool_session)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired session")


def require_gm(claims: dict = Depends(get_current_claims)) -> dict:
    if claims.get("role") != "GM":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "GM role required")
    return claims


async def require_campaign_gm(campaign_id: str, claims: dict = Depends(require_gm)) -> dict:
    if not await campaign_owned_by(campaign_id, claims["sub"]):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "campaign not found")
    return claims
