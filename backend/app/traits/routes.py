from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_campaign
from app.entities.repository import PERSON_FIELDS, get_node
from app.traits import repository
from app.traits.bogen import bogen_uebersicht, sichtbare_kategorien
from app.traits.schemas import TraitDefResponse, TraitRatingResponse, TraitRatingUpdate

router = APIRouter(prefix="/api/campaigns/{campaign_id}", tags=["traits"], dependencies=[Depends(require_campaign_zugang)])


@router.get("/traitkatalog", response_model=list[TraitDefResponse])
async def get_catalog(campaign_id: str):
    campaign = await get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne nicht gefunden")
    return await repository.list_catalog(campaign["ruleset"])


@router.get("/personen/{person_id}/werte", response_model=list[TraitRatingResponse])
async def get_werte(campaign_id: str, person_id: str, viewer: Viewer = Depends(get_viewer)):
    """Werte einer Person.

    **Spieler sehen ausschliesslich ihren eigenen Charakter** — fremde
    Charakterbögen sind tabu, weder von Mitspielern noch von NPCs. 404 statt
    403, damit die Existenz der Person nicht bestätigt wird.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    return await repository.get_ratings_for_entity(campaign_id, person_id)


@router.get("/personen/{person_id}/bogen")
async def get_bogen(campaign_id: str, person_id: str, viewer: Viewer = Depends(get_viewer)) -> dict:
    """Alles fuer das Charakterblatt in einer Antwort.

    Fasst Katalog, gesetzte Werte und die abgeleiteten Groessen zusammen —
    das Blatt braucht sie ohnehin immer gemeinsam, und einzeln geladen waeren
    es drei Abfragen, deren Ergebnisse zueinander passen muessen.

    Der Katalog ist bereits nach dem eingeschlagenen Weg gefiltert: wer kein
    Magier ist, bekommt Sphaeren und Arete gar nicht erst zu sehen.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    campaign = await get_campaign(campaign_id)
    katalog = await repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)

    nach_name = {w["name"]: w["rating"] for w in werte}
    erlaubt = sichtbare_kategorien(person.get("weg") or "KEINER", {t["category"] for t in katalog})

    return {
        "person": {"id": person["id"], "name": person["name"], "personType": person["personType"]},
        "uebersicht": bogen_uebersicht(person, nach_name),
        "katalog": [t for t in katalog if t["category"] in erlaubt],
        "werte": werte,
    }


@router.put("/personen/{person_id}/werte/{trait_def_id}", response_model=TraitRatingResponse, dependencies=[Depends(require_campaign_gm)])
async def set_wert(campaign_id: str, person_id: str, trait_def_id: str, body: TraitRatingUpdate):
    result = await repository.set_rating(campaign_id, person_id, trait_def_id, body.rating, body.maxOverride)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person oder Fähigkeit nicht gefunden")
    return result
