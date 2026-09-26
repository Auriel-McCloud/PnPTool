"""HTTP-Routen für Verhandlungen: SL macht ein Angebot, Spieler antwortet.

Zustellung nutzt denselben Live-Verteiler wie die SL-Mitteilungen
(app/mitteilungen/verteiler.py) — eigener Umschlag-`typ` ("verhandlung"),
damit das Frontend beides klar auseinanderhalten kann, ohne zwei
WebSockets zu brauchen.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.items import repository as items_repository
from app.mitteilungen.verteiler import verteiler
from app.party import repository as party_repository
from app.verhandlung import logic, repository
from app.verhandlung.logic import VerhandlungsFehler
from app.verhandlung.schemas import (
    GegenstandWeitergebenRequest,
    VerhandlungAntwortRequest,
    VerhandlungCreate,
    VerhandlungResponse,
)

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/verhandlungen",
    tags=["verhandlung"],
    dependencies=[Depends(require_campaign_zugang)],
)


async def _verteilen(campaign_id: str, verhandlung: dict) -> None:
    """Schickt die Verhandlung über dieselbe Live-Leitung wie SL-Mitteilungen.

    `darf_empfangen` (mitteilungen/logic.py) filtert Nicht-NACHRICHT-Objekte
    über `empfaengerIds` — das Feld ist bei Verhandlungen sonst nicht
    vorhanden (dort heisst es `empfaengerPersonId`), deshalb hier ergänzt,
    ohne das gespeicherte Objekt selbst damit zu verunreinigen.
    """
    umschlag = {**verhandlung, "_typ": "verhandlung", "empfaengerIds": [verhandlung["empfaengerPersonId"]]}
    await verteiler.verteilen(campaign_id, umschlag)


@router.post("", response_model=VerhandlungResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_campaign_gm)])
async def anbieten(campaign_id: str, body: VerhandlungCreate):
    """SL schickt ein Angebot an einen Spieler (nimmt an/lehnt ab)."""
    verhandlung = await repository.create_verhandlung(
        campaign_id,
        body.empfaengerPersonId,
        body.art,
        [p.model_dump() for p in body.positionen],
        body.kontext,
    )
    await _verteilen(campaign_id, verhandlung)
    return verhandlung


@router.post("/gegenstand-weitergeben", response_model=VerhandlungResponse, status_code=status.HTTP_201_CREATED)
async def gegenstand_weitergeben(
    campaign_id: str,
    body: GegenstandWeitergebenRequest,
    viewer: Viewer = Depends(get_viewer),
):
    """Ein Spieler bietet einem Party-Mitglied einen eigenen Gegenstand an.

    Anders als bei SL-Verhandlungen (Reparatur, Kauf) ist hier kein Geld
    beteiligt — das Popup dient nur der Zustimmung: niemandem darf ungefragt
    etwas ins Inventar geschoben werden. Deshalb auch kein `gesamtbetrag`
    im Sinne eines Preises; `create_verhandlung` errechnet ihn zwar (Summe
    der Positionen), aber die Positionsliste bleibt hier absichtlich leer an
    echtem Geld — nur eine Bezeichnung fürs Popup.
    """
    if viewer.role == "GM" or not viewer.person_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Nur Spieler können Gegenstände weitergeben")
    absender_id = viewer.person_id

    if body.empfaengerPersonId == absender_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kann nicht an sich selbst weitergeben")

    besitzer = await items_repository.get_owner_id(campaign_id, body.gegenstandId)
    if besitzer != absender_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Nur eigene Gegenstände können weitergegeben werden")

    gegenstand = await items_repository.get_gegenstand(campaign_id, body.gegenstandId)
    if gegenstand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    # Nur an jemanden aus derselben Party — "gleicher Ort" im Sinne von
    # Marks Notiz. Personen ohne eigenen Standort haben nur die Party als
    # Ortsbezug (siehe party/repository.py), deshalb dieser Weg statt eines
    # direkten Standortvergleichs.
    eigene_party = await party_repository.get_party_von_person(campaign_id, absender_id)
    if eigene_party is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Du bist in keiner Party")
    mitglieder_ids = {m["id"] for m in eigene_party["mitglieder"]}
    if body.empfaengerPersonId not in mitglieder_ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur an Mitglieder der eigenen Party möglich")

    verhandlung = await repository.create_verhandlung(
        campaign_id,
        body.empfaengerPersonId,
        "GEGENSTAND_WEITERGABE",
        [{"bezeichnung": gegenstand["name"], "betrag": 0}],
        {"gegenstandId": body.gegenstandId, "absenderPersonId": absender_id},
    )
    await _verteilen(campaign_id, verhandlung)
    return verhandlung


@router.get("", response_model=list[VerhandlungResponse])
async def offene(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Offene Angebote für den eigenen Charakter — Aufhol-Liste beim Laden,
    falls ein Angebot ankam, während das Gerät nicht verbunden war."""
    if not viewer.person_id:
        return []
    return await repository.list_offene_fuer(campaign_id, viewer.person_id)


@router.get("/{verhandlung_id}", response_model=VerhandlungResponse)
async def einzeln(campaign_id: str, verhandlung_id: str, viewer: Viewer = Depends(get_viewer)):
    verhandlung = await repository.get_verhandlung(campaign_id, verhandlung_id)
    if verhandlung is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verhandlung nicht gefunden")
    if viewer.role != "GM" and verhandlung["empfaengerPersonId"] != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verhandlung nicht gefunden")
    return verhandlung


@router.post("/{verhandlung_id}/antwort", response_model=VerhandlungResponse)
async def antworten(
    campaign_id: str,
    verhandlung_id: str,
    body: VerhandlungAntwortRequest,
    viewer: Viewer = Depends(get_viewer),
):
    """Der Spieler nimmt an oder lehnt ab. **Nur der eigene Charakter**,
    genau wie beim Melden von Initiative/Paralyse — die SL kann für niemanden
    stellvertretend antworten, das wäre keine Verhandlung mehr."""
    verhandlung = await repository.get_verhandlung(campaign_id, verhandlung_id)
    if verhandlung is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verhandlung nicht gefunden")
    if verhandlung["empfaengerPersonId"] != viewer.person_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Nur für den eigenen Charakter")
    if verhandlung["status"] != "OFFEN":
        raise HTTPException(status.HTTP_409_CONFLICT, "Über dieses Angebot wurde schon entschieden")

    if not body.angenommen:
        aktualisiert = await repository.setze_status(campaign_id, verhandlung_id, "ABGELEHNT")
        if aktualisiert is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Verhandlung nicht gefunden")
        await _verteilen(campaign_id, aktualisiert)
        return aktualisiert

    try:
        ergebnis = await logic.ausfuehren(campaign_id, verhandlung)
    except VerhandlungsFehler as fehler:
        raise HTTPException(status.HTTP_409_CONFLICT, str(fehler)) from fehler

    aktualisiert = await repository.setze_status(campaign_id, verhandlung_id, "ANGENOMMEN")
    if aktualisiert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verhandlung nicht gefunden")
    aktualisiert["ergebnis"] = ergebnis
    await _verteilen(campaign_id, aktualisiert)
    return aktualisiert


@router.delete("/{verhandlung_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_campaign_gm)])
async def zurueckziehen(campaign_id: str, verhandlung_id: str):
    """SL zieht ein noch offenes Angebot zurück (oder räumt Testdaten auf)."""
    if not await repository.delete_verhandlung(campaign_id, verhandlung_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verhandlung nicht gefunden")
