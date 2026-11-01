"""Spieler-Routen fürs Deaktivieren. Self-Service, kein GM-Zwang."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import Viewer, get_viewer, require_campaign_zugang
from app.ereignisprotokoll import hooks
from app.kampf import matrix, matrix_store, repository
from app.kampf.matrix import (
    DECK_EINSTIEG,
    ELECTRONIC_WARFARE,
    NAVIGATION,
)

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/kampf/matrix",
    tags=["kampf"],
    dependencies=[Depends(require_campaign_zugang)],
)


class ProbeInput(BaseModel):
    erfolge: int = Field(ge=0)


class TrefferInput(BaseModel):
    zielPersonId: str
    erfolge: int = Field(ge=0)
    fertigkeit: str


class Posten(BaseModel):
    id: str
    runden: int = Field(ge=1, le=3)


class BestaetigenInput(BaseModel):
    zielPersonId: str
    posten: list[Posten] = []
    schlag: bool = False


async def _kampf_oder_404(campaign_id: str) -> dict:
    kampf = await matrix_store.lade(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return kampf


async def _akteur(campaign_id: str, viewer: Viewer) -> str:
    if not viewer.person_id or not await matrix_store.ist_akteur(campaign_id, viewer.person_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Nur Decker oder Neuroweaver")
    return viewer.person_id


@router.get("/aus/{person_id}")
async def aus_von(campaign_id: str, person_id: str, viewer: Viewer = Depends(get_viewer)):
    """Was an dieser Person gerade aus ist. Sie selbst, die Party und die SL sehen es."""
    kampf = await _kampf_oder_404(campaign_id)
    if viewer.role != "GM" and viewer.person_id != person_id:
        party = await matrix_store.party_ids(campaign_id, person_id)
        if viewer.person_id not in party:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht sichtbar")
    return {"aus": matrix_store.aus_fuer(kampf["stand"], person_id), **(await matrix_store.karten_stand(campaign_id, person_id, kampf["stand"], kampf["runde"]))}


@router.get("")
async def uebersicht(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    ich = await _akteur(campaign_id, viewer)
    kampf = await _kampf_oder_404(campaign_id)
    stand = kampf["stand"]
    runde = kampf["runde"]
    party = await matrix_store.party_ids(campaign_id, ich)
    party.add(ich)
    sichtbar = matrix_store.gesehen(stand, ich)
    voll = await repository.hole(campaign_id)
    if voll is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    zeilen = []
    for t in voll["teilnehmer"]:
        pid = t.get("personId")
        if not pid or t.get("zusatzzug"):
            continue
        basis = (await matrix_store.matrix_basis(campaign_id, pid))
        bonus = matrix.aktiver_bonus(stand.get("ew") or {}, pid, runde)
        maximum = matrix.ice_maximum(basis["wert"], bonus)
        aktuell = matrix_store.aktuelles_ice(stand, pid, maximum)
        ist_party = pid in party
        zeige = matrix.zahl_sichtbar(ist_party, pid in sichtbar)
        zeilen.append({
            "personId": pid,
            "name": t["name"],
            "istParty": ist_party,
            "ice": aktuell if zeige else None,
            "iceMax": maximum if zeige else None,
            "iceArt": basis["quelle"] if zeige else None,
            "klickbar": zeige and pid != ich,
            "aus": matrix_store.aus_fuer(stand, pid) if ist_party or viewer.role == "GM" else [],
        })
    return {"runde": runde, "teilnehmer": zeilen}


@router.post("/navigation")
async def navigation(campaign_id: str, body: ProbeInput, viewer: Viewer = Depends(get_viewer)):
    ich = await _akteur(campaign_id, viewer)
    kampf = await _kampf_oder_404(campaign_id)
    if not matrix.navigation_trifft(body.erfolge):
        return {"gesehen": False}
    stand = kampf["stand"]
    voll = await repository.hole(campaign_id)
    if voll is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    party = await matrix_store.party_ids(campaign_id, ich)
    party.add(ich)
    gegner = [
        t["personId"]
        for t in voll["teilnehmer"]
        if t.get("personId") and t["personId"] not in party and not t.get("zusatzzug")
    ]
    stand.setdefault("gesehen", {}).setdefault(ich, [])
    for gid in gegner:
        if gid not in stand["gesehen"][ich]:
            stand["gesehen"][ich].append(gid)
    await matrix_store.speichere(campaign_id, stand)
    return {"gesehen": True, "anzahl": len(stand["gesehen"][ich])}


@router.post("/electronic-warfare")
async def electronic_warfare(campaign_id: str, body: ProbeInput, viewer: Viewer = Depends(get_viewer)):
    ich = await _akteur(campaign_id, viewer)
    kampf = await _kampf_oder_404(campaign_id)
    bonus = matrix.ew_bonus(body.erfolge)
    if bonus <= 0:
        return {"bonus": 0}
    party = list(await matrix_store.party_ids(campaign_id, ich))
    if ich not in party:
        party.append(ich)
    stand = kampf["stand"]
    stand["ew"] = matrix.ew_setzen(stand.get("ew") or {}, party, bonus, kampf["runde"])
    await matrix_store.speichere(campaign_id, stand)
    return {"bonus": bonus, "runden": 3}


@router.post("/treffer")
async def treffer(campaign_id: str, body: TrefferInput, viewer: Viewer = Depends(get_viewer)):
    ich = await _akteur(campaign_id, viewer)
    if body.fertigkeit not in DECK_EINSTIEG:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Brute Force oder Schleichen")
    kampf = await _kampf_oder_404(campaign_id)
    stand = kampf["stand"]
    party = await matrix_store.party_ids(campaign_id, ich)
    party.add(ich)
    if body.zielPersonId == ich:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nicht sich selbst")
    if body.zielPersonId not in party and body.zielPersonId not in matrix_store.gesehen(stand, ich):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "ICE noch nicht gesehen")
    info = await matrix_store.matrix_basis(campaign_id, body.zielPersonId)
    zustand = await repository.hot_lesen(campaign_id, body.zielPersonId)
    art = matrix.treffer_art(info["weg"], zustand["matrixHot"], info["drohne"])
    bonus = matrix.aktiver_bonus(stand.get("ew") or {}, body.zielPersonId, kampf["runde"])
    maximum = matrix.ice_maximum(info["wert"], bonus)
    vorher = matrix_store.aktuelles_ice(stand, body.zielPersonId, maximum)
    nachher = matrix.ice_nach_treffer(vorher, body.erfolge)
    schlag = matrix.ueberschuss(body.erfolge, vorher)
    punkte = 0 if art == "schaden" else matrix.netto(body.erfolge, vorher)
    matrix_store.merke_ice(stand, body.zielPersonId, nachher)
    stand.setdefault("offen", {})[ich] = {
        "zielPersonId": body.zielPersonId,
        "punkte": punkte,
        "schlag": schlag,
        "art": art,
    }
    await matrix_store.speichere(campaign_id, stand)
    ziele = []
    if art != "schaden" and punkte:
        ziele = await matrix_store.schaltbare(campaign_id, body.zielPersonId)
    return {
        "iceVorher": vorher,
        "iceNachher": nachher,
        "punkte": punkte,
        "schlag": schlag,
        "art": art,
        "quelle": info["quelle"],
        "ziele": ziele,
    }


@router.post("/bestaetigen")
async def bestaetigen(campaign_id: str, body: BestaetigenInput, viewer: Viewer = Depends(get_viewer)):
    ich = await _akteur(campaign_id, viewer)
    kampf = await _kampf_oder_404(campaign_id)
    stand = kampf["stand"]
    offen = (stand.get("offen") or {}).get(ich) or {}
    if offen.get("zielPersonId") != body.zielPersonId:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Zuerst die Probe")
    art = offen.get("art") or "schalten"
    if body.schlag:
        if art not in ("schaden", "wahl"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Der ist nicht hot")
        menge = int(offen.get("schlag") or 0)
        if menge < 1:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein Überschuss")
        gebucht = await matrix_store.schlag_buchen(campaign_id, body.zielPersonId, menge)
        if gebucht < 1:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
        matrix_store.offen_loeschen(stand, ich)
        await matrix_store.speichere(campaign_id, stand)
        await hooks.kampf_treffer(
            campaign_id,
            art="TREFFER",
            ziel_person_id=body.zielPersonId,
            angreifer_person_id=ich,
            kampf_id=kampf["id"],
            runde=kampf["runde"],
            hp_art="schlag",
            hp_menge=gebucht,
            kaestchen_schaden=0,
        )
        return {"schlag": gebucht}
    if art == "schaden":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Den Neuroweaver schaltet man nicht")
    katalog = {z["id"]: z for z in await matrix_store.schaltbare(campaign_id, body.zielPersonId)}
    gewaehlt = []
    for posten in body.posten:
        ziel = katalog.get(posten.id)
        if ziel is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Das lässt sich dort nicht schalten")
        gewaehlt.append({**ziel, "runden": posten.runden})
    if not matrix.aufteilung_gueltig(int(offen.get("punkte") or 0), [p.runden for p in body.posten]):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mehr Runden als Punkte")
    matrix_store.schalte(stand, body.zielPersonId, ich, gewaehlt)
    for ziel in gewaehlt:
        if ziel["art"] == "konsole":
            ids = await matrix_store.drohnen_fallen(campaign_id, body.zielPersonId)
            matrix_store.merke_sprung(stand, body.zielPersonId, ids)
    matrix_store.offen_loeschen(stand, ich)
    await matrix_store.speichere(campaign_id, stand)
    await matrix_store.hot_wegen_aus(campaign_id, body.zielPersonId)
    return {"aus": matrix_store.aus_fuer(stand, body.zielPersonId)}


@router.post("/reaktivieren/{eintrag_id}")
async def reaktivieren(campaign_id: str, eintrag_id: str, viewer: Viewer = Depends(get_viewer)):
    ich = await _akteur(campaign_id, viewer)
    kampf = await _kampf_oder_404(campaign_id)
    stand = kampf["stand"]
    party = await matrix_store.party_ids(campaign_id, ich)
    party.add(ich)
    bleibt = []
    gefunden = None
    for eintrag in stand.get("aus") or []:
        if eintrag.get("id") == eintrag_id and eintrag.get("traegerId") in party:
            gefunden = eintrag
            continue
        bleibt.append(eintrag)
    if gefunden is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nichts zum Anschalten")
    stand["aus"] = bleibt
    await matrix_store.speichere(campaign_id, stand)
    if gefunden.get("art") == "konsole":
        await matrix_store.drohnen_zurueck(campaign_id, gefunden.get("gesprungeneIds") or [])
        await matrix_store.hot_wahl_frei(campaign_id, gefunden.get("traegerId") or "")
    return {"ok": True}
