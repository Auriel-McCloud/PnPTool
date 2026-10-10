"""HTTP-Routen für Achievements.

Drei Bereiche: Katalog-CRUD (SL-Baukasten), Verleihungen (eigene für
Spieler, alle für SL + spontane manuelle Vergabe) und AUTO-Vorschläge
(live berechnet, SL bestätigt einzeln — siehe trigger.py).

Siehe docs/wiki/entities/achievements.md für die vollständige Herleitung.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.achievements import belohnung, repository, trigger
from app.achievements.schemas import (
    AUSLOESE_ARTEN,
    AUSLOESE_ARTEN_MIT_ZIEL_GEGENSTAND,
    AchievementCreate,
    AchievementResponse,
    AchievementUpdate,
    KiTextRequest,
    VerleihungCreate,
    VerleihungResponse,
    VorschlagAnwendenRequest,
    VorschlagEintrag,
)
from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_campaign
from app.ereignisprotokoll import hooks
from app.ereignisprotokoll import repository as ereignisprotokoll_repository
from app.ki.client import KiFehler, generiere_json
from app.ki.kontext import sammle_kontext

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/achievements",
    tags=["achievements"],
    dependencies=[Depends(require_campaign_zugang)],
)


def _pruefe_ausloese_art(art: str | None) -> None:
    if art is not None and art not in AUSLOESE_ARTEN:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unbekannte auslöseArt: {art}")


# ===========================================================================
# Katalog — SL-Baukasten
# ===========================================================================


@router.get("", response_model=list[AchievementResponse])
async def katalog(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Jeder darf den Katalog sehen — Spieler brauchen ihn für die eigene
    Achievement-Liste (Icon/Name/Beschreibung je Eintrag)."""
    return await repository.liste(campaign_id)


@router.post("", response_model=AchievementResponse, dependencies=[Depends(require_campaign_gm)])
async def anlegen(campaign_id: str, body: AchievementCreate):
    _pruefe_ausloese_art(body.ausloeseArt)
    if body.art == "AUTO" and not body.ausloeseArt:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "AUTO-Achievements brauchen eine auslöseArt")
    if body.ausloeseArt in AUSLOESE_ARTEN_MIT_ZIEL_GEGENSTAND and not body.zielGegenstandId:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{body.ausloeseArt} braucht einen zielGegenstandId")
    return await repository.anlegen(campaign_id, body.model_dump())


@router.patch("/{achievement_id}", response_model=AchievementResponse, dependencies=[Depends(require_campaign_gm)])
async def aendern(campaign_id: str, achievement_id: str, body: AchievementUpdate):
    _pruefe_ausloese_art(body.ausloeseArt)
    ergebnis = await repository.aendern(campaign_id, achievement_id, body.model_dump(exclude_unset=True))
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Achievement nicht gefunden")
    return ergebnis


@router.delete("/{achievement_id}", dependencies=[Depends(require_campaign_gm)])
async def loeschen(campaign_id: str, achievement_id: str):
    if not await repository.loeschen(campaign_id, achievement_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Nicht gefunden oder bereits verliehen — bereits vergebene Achievements bleiben erhalten.",
        )
    return {"ok": True}


# ===========================================================================
# Verleihungen — eigene für Spieler, alle für die SL, spontane manuelle Vergabe
# ===========================================================================


@router.get("/meine", response_model=list[VerleihungResponse])
async def meine_verleihungen(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    if viewer.person_id is None:
        return []
    return await repository.verleihungen_fuer_person(campaign_id, viewer.person_id)


@router.get("/verleihungen", response_model=list[VerleihungResponse], dependencies=[Depends(require_campaign_gm)])
async def alle_verleihungen(campaign_id: str):
    return await repository.alle_verleihungen(campaign_id)


@router.post(
    "/{achievement_id}/verleihen",
    response_model=VerleihungResponse,
    dependencies=[Depends(require_campaign_gm)],
)
async def verleihen(campaign_id: str, achievement_id: str, body: VerleihungCreate):
    """Spontane manuelle Vergabe — jederzeit, unabhängig von einem Auto-Trigger.
    Ein bereits bestehendes MANUELL-Achievement lässt sich jederzeit erneut
    vergeben (Marks Vorgabe)."""
    achievement = await repository.hole(campaign_id, achievement_id)
    if achievement is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Achievement nicht gefunden")

    if achievement.get("einzigartig"):
        bisheriger_traeger = await repository.aktueller_traeger(campaign_id, achievement_id)
        if bisheriger_traeger and bisheriger_traeger != body.personId:
            await repository.loese_ab(campaign_id, achievement_id, bisheriger_traeger)

    verleihung = await repository.verleihe(
        campaign_id, achievement_id=achievement_id, person_id=body.personId,
        text=body.text, sl_notiz=body.slNotiz,
        sitzung_id=await ereignisprotokoll_repository.aktive_sitzung_id(campaign_id),
    )
    if verleihung is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    campaign = await get_campaign(campaign_id)
    await belohnung.einloesen(
        campaign_id, campaign["ruleset"] if campaign else "neotopia",
        person_id=body.personId, achievement=achievement,
    )
    return verleihung


@router.put("/verleihungen/{verleihung_id}/geloescht", dependencies=[Depends(require_campaign_gm)])
async def verleihung_loeschen(campaign_id: str, verleihung_id: str, geloescht: bool = True):
    """Papierkorb-Prinzip — kein Hard-Delete, falls sich jemand vertan hat."""
    if not await repository.setze_geloescht(campaign_id, verleihung_id, geloescht):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verleihung nicht gefunden")
    return {"ok": True}


# ===========================================================================
# AUTO-Vorschläge — live aus dem Ereignisprotokoll berechnet, nichts gespeichert
# ===========================================================================


@router.get("/vorschlaege", response_model=list[VorschlagEintrag], dependencies=[Depends(require_campaign_gm)])
async def vorschlaege(campaign_id: str):
    return await trigger.vorschlaege(campaign_id)


@router.post(
    "/vorschlaege/anwenden",
    response_model=VerleihungResponse,
    dependencies=[Depends(require_campaign_gm)],
)
async def vorschlag_anwenden(campaign_id: str, body: VorschlagAnwendenRequest):
    """SL bestätigt EINEN AUTO-Vorschlag. Bei einem Rekord-Auslöser
    (einzigartig + wandernder Träger) wird die bisherige Trägerin zuerst
    abgelöst."""
    achievement = await repository.hole(campaign_id, body.achievementId)
    if achievement is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Achievement nicht gefunden")

    if achievement.get("einzigartig"):
        bisheriger_traeger = await repository.aktueller_traeger(campaign_id, body.achievementId)
        if bisheriger_traeger and bisheriger_traeger != body.personId:
            await repository.loese_ab(campaign_id, body.achievementId, bisheriger_traeger)

    verleihung = await repository.verleihe(
        campaign_id, achievement_id=body.achievementId, person_id=body.personId,
        text=body.text, sl_notiz=body.slNotiz,
        sitzung_id=await ereignisprotokoll_repository.aktive_sitzung_id(campaign_id),
    )
    if verleihung is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    campaign = await get_campaign(campaign_id)
    await belohnung.einloesen(
        campaign_id, campaign["ruleset"] if campaign else "neotopia",
        person_id=body.personId, achievement=achievement,
    )
    return verleihung


# ===========================================================================
# KI-Text — thematisch auf die letzten Ereignisse bezogen (Marks Wunsch)
# ===========================================================================

_KI_SYSTEM = (
    "Du schreibst einen kurzen, thematischen Achievement-Text für einen "
    "Spielercharakter in der Welt von NeotopiA (deutsches Cyberpunk-"
    "Pen-and-Paper-Rollenspiel). Du bekommst den Kampagnenkontext und den "
    "Namen/die Beschreibung des Achievements, bei Auto-Erkennungen zusätzlich "
    "den auslösenden Umstand. Schreibe 2-4 Sätze, atmosphärisch, bezogen auf "
    "Ort/Ereignis sofern bekannt — keine generische Trophäenbeschreibung."
)


@router.post("/ki-text", dependencies=[Depends(require_campaign_gm)])
async def ki_text(campaign_id: str, body: KiTextRequest):
    achievement = await repository.hole(campaign_id, body.achievementId)
    if achievement is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Achievement nicht gefunden")

    kontext = body.kontextText or await sammle_kontext(campaign_id)
    prompt = (
        f"Achievement: {achievement['name']}\n"
        f"Beschreibung: {achievement.get('beschreibung') or '(keine)'}\n\n"
        f"Kontext:\n{kontext or '(kein Kontext)'}"
    )
    try:
        ergebnis = await generiere_json(
            prompt, _KI_SYSTEM,
            {"type": "OBJECT", "properties": {"text": {"type": "STRING"}}, "required": ["text"]},
            campaign_id=campaign_id,
        )
    except KiFehler as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))

    text = (ergebnis.get("text") or "").strip()
    await hooks.ki(
        campaign_id, anlass="achievement_text", prompt=prompt,
        antwort_text=text, uebernommen=False, betrifft_id=body.personId,
    )
    return {"text": text}
