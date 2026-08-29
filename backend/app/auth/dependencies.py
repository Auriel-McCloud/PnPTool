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
    campaign_id: str,
    als_spieler: str | None = Query(
        default=None,
        alias="alsSpieler",
        description="Nur für den Spielleiter: Person-ID eines Spielercharakters. Liefert die "
        "Antwort gefiltert, so wie dieser Spieler sie sähe (SL-Vorschau).",
    ),
    claims: dict = Depends(get_current_claims),
) -> Viewer:
    """Baut den Blickwinkel für eine Leseroute — für Spielleitung wie Spieler.

    Spielleitung: sieht alles; mit ?alsSpieler= wahlweise gefiltert wie der
    betreffende Charakter (Vorschau).

    Spieler: Blickwinkel kommt aus der eigenen Sitzung, der Parameter wird
    ignoriert — sonst könnte sich ein Spieler durch fremde Charaktere klicken.
    Ohne beanspruchten Charakter sieht er nur, was für alle sichtbar ist.

    Nur für Leserouten. Schreibende Routen verlangen require_campaign_gm.
    """
    rolle = claims.get("role")

    if rolle == "GM":
        if not await campaign_owned_by(campaign_id, claims["sub"]):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "campaign not found")
        if als_spieler:
            return Viewer(role="PLAYER", person_id=als_spieler)
        return Viewer(role="GM")

    if rolle == "PLAYER":
        # Spät importiert: app.players nutzt seinerseits auth, ein Import auf
        # Modulebene wäre zirkulär.
        from app.players.repository import get_spieler

        spieler = await get_spieler(claims["sub"])
        # Der Zugang könnte inzwischen gelöscht worden sein, das Token bliebe
        # aber bis zum Ablauf gültig.
        if spieler is None or spieler["campaignId"] != campaign_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "campaign not found")
        return Viewer(role="PLAYER", person_id=spieler["personId"])

    raise HTTPException(status.HTTP_403_FORBIDDEN, "no access to this campaign")


async def require_campaign_zugang(viewer: Viewer = Depends(get_viewer)) -> Viewer:
    """Zugang zur Kampagne, gleich in welcher Rolle.

    Als Router-Absicherung gedacht: schreibende Routen müssen darüber hinaus
    require_campaign_gm verlangen. Ein Test prüft, dass keine davon vergessen
    wurde (tests/test_zugriffsschutz.py).
    """
    return viewer
