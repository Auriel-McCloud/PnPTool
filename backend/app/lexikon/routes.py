"""Spieler-Lexikon: nur der eigene Spieler-Zugang sieht seine Einträge.

Beschreibung wird über dieselbe Redaktionslogik wie überall sonst
(entities/visibility.py::redact_rich_text, is_visible_to) behandelt — ein
Eintrag ist zwar "entdeckt" (taucht in der Liste auf), die Beschreibung
selbst bleibt aber gesperrt, solange sichtbarkeit noch GM ist.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.entities.visibility import is_visible_to, redact_rich_text
from app.lexikon import repository
from app.lexikon.schemas import FavorisierenRequest, LexikonEintrag
from app.players.routes import require_spieler

router = APIRouter(prefix="/api/spieler/lexikon", tags=["lexikon"])

PLATZHALTER_GESPERRT = "Noch nicht erforscht — die Spielleitung hat dies noch nicht freigegeben."


@router.get("", response_model=list[LexikonEintrag])
async def liste(spieler: dict = Depends(require_spieler)):
    if not spieler.get("personId"):
        return []
    campaign_id, person_id = spieler["campaignId"], spieler["personId"]
    roh = await repository.entdeckte_eintraege(campaign_id, person_id)

    ergebnis = []
    for e in roh:
        sichtbar = is_visible_to(e["sichtbarkeit"], e["sichtbarFuer"], "PLAYER", person_id)
        ergebnis.append(
            LexikonEintrag(
                id=e["id"],
                kategorie=e["kategorie"],
                name=e["name"] or "",
                bildUrl=e["bildUrl"],
                beschreibung=redact_rich_text(e["description"], "PLAYER") if sichtbar else PLATZHALTER_GESPERRT,
                beschreibungSichtbar=sichtbar,
                favorisiert=e["favorisiert"],
                entdecktSeit=e["entdecktSeit"] or "",
                naehe=e["naehe"],
            )
        )
    return ergebnis


@router.post("/favoriten", status_code=status.HTTP_204_NO_CONTENT)
async def favorisieren(body: FavorisierenRequest, spieler: dict = Depends(require_spieler)):
    if not spieler.get("personId"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dir ist noch kein Charakter zugeordnet")
    if not await repository.favorisieren(spieler["campaignId"], spieler["personId"], body.zielId):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Eintrag nicht gefunden oder noch nicht entdeckt")


@router.delete("/favoriten/{ziel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def favorisieren_entfernen(ziel_id: str, spieler: dict = Depends(require_spieler)):
    if not spieler.get("personId"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dir ist noch kein Charakter zugeordnet")
    await repository.favorisieren_entfernen(spieler["campaignId"], spieler["personId"], ziel_id)
