from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.entities.visibility import is_visible_to, redact_rich_text
from app.party import repository
from app.party.schemas import (
    AufenthaltsortRequest,
    MitgliedRequest,
    PartyCreate,
    PartyResponse,
    PartyUpdate,
)
from app.spotify import dienst as spotify_dienst

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/party",
    tags=["party"],
    dependencies=[Depends(require_campaign_zugang)],
)


async def _mit_musik_hinweis(campaign_id: str, party: dict) -> dict:
    """Löst — wenn diese Party aktiv ist und einen Aufenthaltsort mit
    hinterlegter Playlist hat — die Spotify-Wiedergabe aus und hängt einen
    Hinweistext für die SL an (Marks Wunsch: Musik folgt der aktiven Party,
    siehe docs/api/party.md). Kein Spotify-Fehler blockiert je die
    eigentliche Party-Aktion — siehe app/spotify/dienst.py."""
    if party.get("aktiv") and party.get("aufenthaltsortId") and party.get("aufenthaltsortKind"):
        party["musikHinweis"] = await spotify_dienst.playlist_fuer_ziel_abspielen(
            campaign_id, party["aufenthaltsortId"], party["aufenthaltsortKind"]
        )
    return party


def _fuer_viewer(party: dict, viewer: Viewer) -> dict | None:
    """Wie bei Begleitern: wer selbst Mitglied ist, sieht die Party immer —
    unabhängig von der gesetzten Sichtbarkeit."""
    ist_mitglied = viewer.person_id is not None and any(m["id"] == viewer.person_id for m in party.get("mitglieder", []))
    if viewer.role == "GM" or ist_mitglied:
        sichtbar = True
    else:
        sichtbar = is_visible_to(
            party.get("sichtbarkeit") or "GM",
            party.get("sichtbarFuer") or [],
            viewer.role,
            viewer.person_id,
        )
    if not sichtbar:
        return None

    gefiltert = dict(party)
    gefiltert["beschreibung"] = redact_rich_text(gefiltert.get("beschreibung", ""), viewer.role)
    if viewer.role != "GM":
        gefiltert["notizen"] = ""
    return gefiltert


@router.get("", response_model=list[PartyResponse])
async def alle(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    roh = await repository.liste(campaign_id)
    gefiltert = (_fuer_viewer(p, viewer) for p in roh)
    return [p for p in gefiltert if p is not None]


@router.get("/{party_id}", response_model=PartyResponse)
async def einzeln(campaign_id: str, party_id: str, viewer: Viewer = Depends(get_viewer)):
    party = await repository.einzeln(campaign_id, party_id)
    if party is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Party nicht gefunden")
    gefiltert = _fuer_viewer(party, viewer)
    if gefiltert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Party nicht gefunden")
    return gefiltert


@router.post("", response_model=PartyResponse, dependencies=[Depends(require_campaign_gm)])
async def anlegen(campaign_id: str, body: PartyCreate):
    ergebnis = await repository.anlegen(campaign_id, body.model_dump())
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne nicht gefunden")
    return ergebnis


@router.patch("/{party_id}", response_model=PartyResponse, dependencies=[Depends(require_campaign_gm)])
async def aendern(campaign_id: str, party_id: str, body: PartyUpdate):
    ergebnis = await repository.aendern(campaign_id, party_id, body.model_dump())
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Party nicht gefunden")
    return ergebnis


@router.delete("/{party_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def loeschen(campaign_id: str, party_id: str):
    if not await repository.loeschen(campaign_id, party_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Party nicht gefunden")


@router.post("/{party_id}/mitglieder", response_model=PartyResponse, dependencies=[Depends(require_campaign_gm)])
async def mitglied_hinzufuegen(campaign_id: str, party_id: str, body: MitgliedRequest):
    """Nimmt eine Person auf — sie verlässt dabei automatisch eine etwaige
    vorherige Party (siehe repository.py, eine Person ist immer nur in
    höchstens einer Party gleichzeitig)."""
    ergebnis = await repository.mitglied_hinzufuegen(campaign_id, party_id, body.personId)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Party oder Person nicht gefunden")
    return ergebnis


@router.delete(
    "/{party_id}/mitglieder/{person_id}", response_model=PartyResponse, dependencies=[Depends(require_campaign_gm)]
)
async def mitglied_entfernen(campaign_id: str, party_id: str, person_id: str):
    ergebnis = await repository.mitglied_entfernen(campaign_id, party_id, person_id)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Party nicht gefunden")
    return ergebnis


@router.put(
    "/{party_id}/aufenthaltsort", response_model=PartyResponse, dependencies=[Depends(require_campaign_gm)]
)
async def aufenthaltsort_setzen(campaign_id: str, party_id: str, body: AufenthaltsortRequest):
    """Ort/Event zuweisen oder (mit leerem Body) lösen — die Party ist dann
    "unterwegs", ohne festen Aufenthaltsort. Ist diese Party aktiv, löst der
    neue Aufenthaltsort gleich die passende Spotify-Playlist aus."""
    ergebnis = await repository.aufenthaltsort_setzen(campaign_id, party_id, body.zielId, body.zielKind)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Party oder Ziel nicht gefunden")
    return await _mit_musik_hinweis(campaign_id, ergebnis)


@router.post("/{party_id}/aktivieren", response_model=PartyResponse, dependencies=[Depends(require_campaign_gm)])
async def aktivieren(campaign_id: str, party_id: str):
    """Macht diese Party zur aktiven — alle anderen der Kampagne werden
    automatisch deaktiviert (höchstens eine Party ist gleichzeitig aktiv).
    Hat die Party bereits einen Aufenthaltsort, startet gleich dessen
    Playlist (Musik folgt der aktiven Party, nicht nur ihrem Ortswechsel)."""
    ergebnis = await repository.aktivieren(campaign_id, party_id)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Party nicht gefunden")
    return await _mit_musik_hinweis(campaign_id, ergebnis)


@router.post("/{party_id}/deaktivieren", response_model=PartyResponse, dependencies=[Depends(require_campaign_gm)])
async def deaktivieren(campaign_id: str, party_id: str):
    ergebnis = await repository.deaktivieren(campaign_id, party_id)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Party nicht gefunden")
    return ergebnis
