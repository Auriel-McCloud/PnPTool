from dataclasses import dataclass

import jwt
from fastapi import Cookie, Depends, HTTPException, Query, status

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


@dataclass(frozen=True)
class Viewer:
    """Whose eyes a read request is answered through.

    `role` is "GM" or "PLAYER"; `person_id` is the Person node of the character
    being viewed as (None for a GM). Passed straight into
    app/entities/visibility.py.
    """

    role: str
    person_id: str | None = None


async def get_viewer(
    als_spieler: str | None = Query(
        default=None,
        alias="alsSpieler",
        description="Person-ID eines Spielercharakters. Liefert die Antwort gefiltert, "
        "so wie dieser Spieler sie sähe (SL-Vorschau).",
    ),
    claims: dict = Depends(require_campaign_gm),
) -> Viewer:
    """Builds the viewing context for a read route.

    Only the campaign's own GM gets here (require_campaign_gm), so the preview
    cannot be used to peek into someone else's campaign. Passing ?alsSpieler=
    downgrades the caller to that character's view for this one request.

    Read routes only. Writes stay unconditionally GM-scoped — a preview must
    never be able to change anything, so no write route takes this dependency.

    Phase 4 note: when players get real logins, this is the single place that
    changes — it would return Viewer("PLAYER", <own character>) from the
    player's session instead of from a query parameter.
    """
    if als_spieler:
        return Viewer(role="PLAYER", person_id=als_spieler)
    return Viewer(role="GM")
