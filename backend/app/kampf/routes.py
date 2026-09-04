from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_einstellungen
from app.kampf import repository
from app.kampf.initiative import darf_melden, initiative_pool, melde_wert
from app.kampf.sichtbarkeit import fuer_spieler
from app.traits.repository import get_ratings_for_entity
from app.wuerfel.logic import wuerfle

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/kampf",
    tags=["kampf"],
    dependencies=[Depends(require_campaign_zugang)],
)

Kampfart = str  # MATRIX | NAHKAMPF | FERNKAMPF — bewusst offen, siehe unten


def _ohne_hilfsfelder(kampf: dict | None) -> dict | None:
    """Entfernt die nur zur Filterung mitgelieferten Felder.

    Schreibrouten sind der Spielleitung vorbehalten, dort ist nichts zu
    verbergen — die Felder gehören aber trotzdem nicht in die Antwort.
    """
    if kampf is None:
        return None
    for feld in ("_rassen", "_npcIds", "_begleiterBesitzer"):
        kampf.pop(feld, None)
    return kampf


class TeilnehmerResponse(BaseModel):
    id: str
    name: str
    initiative: int
    # Entscheidet die Reihenfolge bei Gleichstand (Zeile 58). Kein Enum, damit
    # sich weitere Arten ergänzen lassen, ohne das Schema anzufassen.
    kampfart: str
    notiz: str
    erledigt: bool
    personId: str | None = None
    personType: str | None = None
    begleiterId: str | None = None


class KampfResponse(BaseModel):
    id: str
    runde: int
    amZug: str | None = None
    teilnehmer: list[TeilnehmerResponse]


class TeilnehmerInput(BaseModel):
    name: str
    initiative: int = Field(default=0, ge=0)
    kampfart: str = "NAHKAMPF"
    notiz: str = ""
    personId: str | None = None
    begleiterId: str | None = None


class TeilnehmerUpdate(BaseModel):
    name: str | None = None
    initiative: int | None = Field(default=None, ge=0)
    kampfart: str | None = None
    notiz: str | None = None
    erledigt: bool | None = None


class AmZugInput(BaseModel):
    teilnehmerId: str | None = None


class InitiativeInput(BaseModel):
    """Ein von Hand gewürfelter Initiativwert (Anzahl Erfolge)."""

    erfolge: int = Field(ge=0)


class InitiativePoolResponse(BaseModel):
    """Was der Spieler vor dem Wurf wissen muss."""

    pool: int
    # Woraus sich der Pool zusammensetzt — sonst wirkt die Zahl willkürlich.
    geistesschaerfe: int
    geschicklichkeit: int
    cyberwareMod: int
    # Darf im Tool gewürfelt werden, oder liegen echte Würfel auf dem Tisch?
    digitalErlaubt: bool
    # Der eigene Eintrag im Kampf, falls schon vorhanden.
    teilnehmerId: str | None = None
    gemeldet: int | None = None


@router.get("", response_model=KampfResponse | None)
async def laufender_kampf(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Die Initiativliste.

    **Für alle mit Zugang lesbar** — das ist der Sinn der Sache: jeder am Tisch
    soll sehen, wann er dran ist, ohne fragen zu müssen.

    **Aber:** Spieler sehen NPCs nur unter Alias. Mark: *"die Spieler dürfen
    nur die Alias Namen der NPCs sehen nicht ihre richtigen Namen!"* Gefiltert
    wird hier serverseitig, nicht im Browser — im Netzwerkverkehr stünde der
    echte Name sonst trotzdem.
    """
    kampf = await repository.hole(campaign_id)
    if kampf is None:
        return None

    rassen = kampf.pop("_rassen", {})
    npc_ids = kampf.pop("_npcIds", set())
    begleiter_besitzer = kampf.pop("_begleiterBesitzer", {})

    if viewer.role != "GM":
        kampf["teilnehmer"] = fuer_spieler(
            kampf["teilnehmer"],
            rassen=rassen,
            eigene_person_id=viewer.person_id,
            begleiter_besitzer=begleiter_besitzer,
            npc_ids=npc_ids,
        )
    return kampf


@router.post("", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def beginne(campaign_id: str):
    return _ohne_hilfsfelder(await repository.beginne(campaign_id))


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def beende(campaign_id: str):
    await repository.beende(campaign_id)


@router.post("/teilnehmer", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_hinzu(campaign_id: str, body: TeilnehmerInput):
    kampf = await repository.teilnehmer_hinzu(campaign_id, body.model_dump())
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.patch("/teilnehmer/{teilnehmer_id}", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_aendern(campaign_id: str, teilnehmer_id: str, body: TeilnehmerUpdate):
    kampf = await repository.teilnehmer_aendern(campaign_id, teilnehmer_id, body.model_dump())
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.delete("/teilnehmer/{teilnehmer_id}", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_entfernen(campaign_id: str, teilnehmer_id: str):
    kampf = await repository.teilnehmer_entfernen(campaign_id, teilnehmer_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.post("/weiter", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def weiter(campaign_id: str):
    """Einen Zug weiter. Am Ende der Liste beginnt die nächste Runde."""
    kampf = await repository.weiter(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.post("/amzug", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def am_zug(campaign_id: str, body: AmZugInput):
    """Direkt jemanden ans Ruder setzen — für den Fall, dass es durcheinander ging."""
    kampf = await repository.setze_am_zug(campaign_id, body.teilnehmerId)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


async def _werte_von(campaign_id: str, person_id: str) -> dict[str, int]:
    """Attributwerte einer Person als {Name: Stufe}."""
    roh = await get_ratings_for_entity(campaign_id, person_id)
    return {r["name"]: r["rating"] for r in roh}


@router.get("/initiative/pool", response_model=InitiativePoolResponse)
async def mein_initiative_pool(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Der eigene Initiative-Pool.

    Marks Ablauf: Nach der Warnung *"Würfelt für Initiative!"* soll der
    Spieler sehen, **wie viele Würfel** er nimmt — ohne im Charakterbogen
    nachzuschlagen.
    """
    if not viewer.person_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein eigener Charakter")

    werte = await _werte_von(campaign_id, viewer.person_id)
    einstellungen = await get_einstellungen(campaign_id)

    # Den eigenen Eintrag im laufenden Kampf suchen, damit die Oberfläche
    # zeigen kann, ob schon gemeldet wurde.
    kampf = await repository.hole(campaign_id)
    eigener = None
    if kampf:
        eigener = next(
            (t for t in kampf["teilnehmer"] if t.get("personId") == viewer.person_id),
            None,
        )

    return InitiativePoolResponse(
        pool=initiative_pool(werte),
        geistesschaerfe=werte.get("Geistesschärfe", 0),
        geschicklichkeit=werte.get("Geschicklichkeit", 0),
        cyberwareMod=0,
        digitalErlaubt=bool(einstellungen.get("digitalesWuerfeln")),
        teilnehmerId=eigener["id"] if eigener else None,
        gemeldet=eigener["initiative"] if eigener else None,
    )


@router.post("/teilnehmer/{teilnehmer_id}/initiative", response_model=KampfResponse)
async def melde_initiative(
    campaign_id: str,
    teilnehmer_id: str,
    body: InitiativeInput,
    viewer: Viewer = Depends(get_viewer),
):
    """Einen selbst gewürfelten Initiativwert melden.

    **Vom Spieler aufrufbar** — das ist der Sinn: er würfelt physisch und
    trägt seine Erfolge ein, statt sie der Spielleitung zuzurufen. Deshalb
    hängt hier bewusst kein `require_campaign_gm`; die Berechtigung prüft
    `darf_melden` feingranular (nur der eigene Charakter).
    """
    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")

    eintrag = next((t for t in kampf["teilnehmer"] if t["id"] == teilnehmer_id), None)
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teilnehmer nicht im Kampf")

    if not darf_melden(viewer.role, viewer.person_id, eintrag.get("personId")):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Nur für den eigenen Charakter")

    try:
        wert = melde_wert(body.erfolge)
    except ValueError as fehler:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(fehler)) from fehler

    kampf = await repository.teilnehmer_aendern(campaign_id, teilnehmer_id, {"initiative": wert})
    return _ohne_hilfsfelder(kampf)


@router.post("/initiative/npcs", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def wuerfle_npc_initiative(campaign_id: str):
    """Würfelt die Initiative aller NPCs und Begleiter im Kampf.

    Marks ausdrückliche Ausnahme: *"die Ausnahme sind als SL nämlich die
    Initiative Würfel für meine im Kampf teilnehmenden NPCs die hätte schon
    gerne automatisch"*. Spieler-Charaktere bleiben unangetastet — die
    würfeln selbst.
    """
    einstellungen = await get_einstellungen(campaign_id)
    if not einstellungen.get("digitalesWuerfelnSL"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Digitales Würfeln für die Spielleitung ist in dieser Kampagne aus",
        )

    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")

    for t in kampf["teilnehmer"]:
        if t.get("personType") == "PC":
            continue  # Die würfeln selbst
        pool = 0
        if t.get("personId"):
            pool = initiative_pool(await _werte_von(campaign_id, t["personId"]))
        elif t.get("begleiterId"):
            pool = initiative_pool(await _werte_von(campaign_id, t["begleiterId"]))
        # Ein namenloser Wachmann ohne Bogen bekommt einen Standardpool,
        # damit er nicht immer als Letzter handelt.
        ergebnis = wuerfle(pool if pool > 0 else 4)
        await repository.teilnehmer_aendern(
            campaign_id, t["id"], {"initiative": ergebnis["erfolge"]}
        )

    return _ohne_hilfsfelder(await repository.hole(campaign_id))
