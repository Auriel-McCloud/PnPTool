from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.ereignisprotokoll import repository
from app.ereignisprotokoll.schemas import (
    KorrekturInput,
    LoeschenInput,
    SitzungCreate,
    SitzungResponse,
    SitzungUpdate,
)

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/ereignisprotokoll",
    tags=["ereignisprotokoll"],
    dependencies=[Depends(require_campaign_zugang)],
)


# ===========================================================================
# Sitzung — Verwaltung liegt bei der SL, aber alle dürfen die Liste sehen
# (z.B. um im eigenen Log nach einem Datum zu filtern).
# ===========================================================================


@router.get("/sitzungen", response_model=list[SitzungResponse])
async def sitzungen_liste(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    return await repository.list_sitzungen(campaign_id)


@router.post("/sitzungen", response_model=SitzungResponse, dependencies=[Depends(require_campaign_gm)])
async def sitzung_anlegen(campaign_id: str, body: SitzungCreate):
    return await repository.erzeuge_sitzung(campaign_id, body.datum, body.ingameDatum, body.titel, body.notiz)


@router.patch("/sitzungen/{sitzung_id}", response_model=SitzungResponse, dependencies=[Depends(require_campaign_gm)])
async def sitzung_aendern(campaign_id: str, sitzung_id: str, body: SitzungUpdate):
    ergebnis = await repository.aendere_sitzung(campaign_id, sitzung_id, body.model_dump())
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sitzung nicht gefunden")
    return ergebnis


# ===========================================================================
# Zeitleiste — "was ist am Abend X passiert", nur SL (enthält u.a. KI-Rohtext
# und alle Bewegungen aller Personen, nicht personenscoped filterbar).
# ===========================================================================


@router.get("/zeitleiste", dependencies=[Depends(require_campaign_gm)])
async def zeitleiste(campaign_id: str, sitzung_id: str | None = None):
    return await repository.zeitleiste(campaign_id, sitzung_id)


# ===========================================================================
# Kategorie-Listen — je eigener Pfad, optionaler Filter (Gegenstand/Person/...)
# ===========================================================================


@router.get("/ki", dependencies=[Depends(require_campaign_gm)])
async def ki_liste(campaign_id: str):
    return await repository.list_ki_eintraege(campaign_id)


@router.get("/gegenstandsbewegungen")
async def gegenstandsbewegungen_liste(
    campaign_id: str, gegenstand_id: str | None = None, viewer: Viewer = Depends(get_viewer)
):
    return await repository.list_gegenstandsbewegungen(campaign_id, gegenstand_id)


@router.get("/geldbewegungen")
async def geldbewegungen_liste(campaign_id: str, person_id: str | None = None, viewer: Viewer = Depends(get_viewer)):
    # Spieler dürfen nur ihre eigenen Geldbewegungen sehen — Kapital anderer
    # Personen ist genauso geheim wie das Inventar anderer (siehe items/).
    if viewer.role != "GM":
        person_id = viewer.person_id
        if person_id is None:
            return []
    return await repository.list_geldbewegungen(campaign_id, person_id)


@router.get("/aufenthalte")
async def aufenthalte_liste(campaign_id: str, party_id: str | None = None, viewer: Viewer = Depends(get_viewer)):
    return await repository.list_aufenthalte(campaign_id, party_id)


@router.get("/npc-wissenszuwachs", dependencies=[Depends(require_campaign_gm)])
async def npc_wissenszuwachs_liste(campaign_id: str, npc_person_id: str | None = None):
    return await repository.list_npc_wissenszuwachs(campaign_id, npc_person_id)


@router.get("/kampf")
async def kampf_liste(campaign_id: str, person_id: str | None = None, viewer: Viewer = Depends(get_viewer)):
    return await repository.list_kampf_eintraege(campaign_id, person_id)


@router.get("/verhandlungen")
async def verhandlungen_liste(campaign_id: str, person_id: str | None = None, viewer: Viewer = Depends(get_viewer)):
    if viewer.role != "GM":
        person_id = viewer.person_id
        if person_id is None:
            return []
    return await repository.list_verhandlungsausgaenge(campaign_id, person_id)


@router.get("/charakterentwicklung")
async def charakterentwicklung_liste(
    campaign_id: str, person_id: str | None = None, viewer: Viewer = Depends(get_viewer)
):
    return await repository.list_charakterentwicklung(campaign_id, person_id)


# ===========================================================================
# Papierkorb-Prinzip: SL darf jeden Eintrag korrigieren oder als gelöscht
# markieren (nie Hard-Delete) — generisch über alle Kategorien.
# ===========================================================================


@router.patch("/{kategorie}/{eintrag_id}", dependencies=[Depends(require_campaign_gm)])
async def eintrag_korrigieren(campaign_id: str, kategorie: str, eintrag_id: str, body: KorrekturInput):
    if kategorie not in repository.LOG_LABELS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unbekannte Kategorie")
    if not await repository.korrigiere_eintrag(campaign_id, kategorie, eintrag_id, body.felder):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Eintrag nicht gefunden")
    return {"ok": True}


@router.put("/{kategorie}/{eintrag_id}/geloescht", dependencies=[Depends(require_campaign_gm)])
async def eintrag_loeschen(campaign_id: str, kategorie: str, eintrag_id: str, body: LoeschenInput):
    if kategorie not in repository.LOG_LABELS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unbekannte Kategorie")
    if not await repository.setze_geloescht(campaign_id, kategorie, eintrag_id, body.geloescht):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Eintrag nicht gefunden")
    return {"ok": True}
