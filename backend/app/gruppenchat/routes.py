"""HTTP-Routen für Gruppenchats.

Dieselbe optionale Kampagnenfunktion wie der Einzelchat (`messengerAktiv`):
ist sie aus, antworten alle Routen mit 403.

Berechtigungen:

* **Anlegen, Mitglieder, Schließen, Löschen: nur die Spielleitung.**
* Ein Spieler sieht und beschreibt nur **offene Gruppen, in denen sein
  Charakter Mitglied ist** — alles andere ist für ihn ein 404.
* Die Spielleitung sieht alle Gruppen und schreibt als eines der NPC-Mitglieder.
  Ihr Name taucht nirgends auf.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.gruppenchat import repository
from app.gruppenchat.schemas import (
    GruppeCreate,
    GruppenChatResponse,
    GruppenNachrichtCreate,
    GruppenNachrichtResponse,
    GruppeResponse,
    GruppeUpdate,
    TeilnehmerHinzufuegen,
)
from app.gruppenchat.security import gruppe_fuer, ist_npc, nachricht_fuer, teilnehmer_fuer
from app.kontakte.routes import require_messenger_active
from app.mitteilungen import repository as mitteilungen_repo
from app.mitteilungen.verteiler import verteiler

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/gruppenchats",
    tags=["gruppenchat"],
    dependencies=[Depends(require_campaign_zugang), Depends(require_messenger_active)],
)


def _ist_gm(viewer: Viewer) -> bool:
    return viewer.role == "GM"


async def _aliase(campaign_id: str, viewer: Viewer, ids: list[str]) -> dict[str, str]:
    """Eigene Aliase des Spielers — die SL braucht keine (sie sieht echte Namen)."""
    if _ist_gm(viewer) or not viewer.person_id:
        return {}
    return await repository.persoenliche_aliase(campaign_id, viewer.person_id, sorted(set(ids)))


async def _gruppe_oder_404(campaign_id: str, gruppe_id: str, viewer: Viewer) -> dict:
    """Holt die Gruppe und prüft, ob der Betrachter sie sehen darf.

    404 statt 403: ein Spieler soll nicht erfahren, dass es eine Gruppe gibt,
    in der er nicht sitzt.
    """
    roh = await repository.hole(campaign_id, gruppe_id)
    if roh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gruppe nicht gefunden")
    if _ist_gm(viewer):
        return roh
    mitglied = any(t["id"] == viewer.person_id for t in roh["teilnehmer"])
    if not viewer.person_id or not mitglied or not roh["offen"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gruppe nicht gefunden")
    return roh


async def _gm_antwort(campaign_id: str, gruppe_id: str) -> GruppeResponse:
    roh = await repository.hole(campaign_id, gruppe_id)
    if roh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gruppe nicht gefunden")
    return gruppe_fuer(roh, ich_id=None, aliase={}, als_gm=True)


@router.get("", response_model=list[GruppeResponse])
async def meine_gruppen(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Spieler: die eigenen offenen Gruppen. SL: alle Gruppen."""
    if _ist_gm(viewer):
        return [
            gruppe_fuer(r, ich_id=None, aliase={}, als_gm=True)
            for r in await repository.liste_fuer_gm(campaign_id)
        ]
    if not viewer.person_id:
        return []
    roh = await repository.liste_fuer_person(campaign_id, viewer.person_id)
    ids = [t["id"] for r in roh for t in r["teilnehmer"]]
    aliase = await _aliase(campaign_id, viewer, ids)
    return [gruppe_fuer(r, ich_id=viewer.person_id, aliase=aliase, als_gm=False) for r in roh]


@router.post("", response_model=GruppeResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_campaign_gm)])
async def gruppe_anlegen(campaign_id: str, body: GruppeCreate):
    """Die Spielleitung legt eine Gruppe an."""
    gruppe_id = await repository.anlegen(campaign_id, body.name.strip())
    for person_id in dict.fromkeys(body.personIds):
        if not await repository.teilnehmer_hinzu(campaign_id, gruppe_id, person_id):
            await repository.loeschen(campaign_id, gruppe_id)
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    return await _gm_antwort(campaign_id, gruppe_id)


@router.patch("/{gruppe_id}", response_model=GruppeResponse, dependencies=[Depends(require_campaign_gm)])
async def gruppe_aendern(campaign_id: str, gruppe_id: str, body: GruppeUpdate):
    """Umbenennen oder schließen/öffnen. Schließen löscht nichts — die Gruppe
    verschwindet nur für die Spieler."""
    name = body.name.strip() if body.name is not None else None
    if not await repository.aendern(campaign_id, gruppe_id, name, body.offen):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gruppe nicht gefunden")
    return await _gm_antwort(campaign_id, gruppe_id)


@router.delete("/{gruppe_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_campaign_gm)])
async def gruppe_loeschen(campaign_id: str, gruppe_id: str):
    """Löscht die Gruppe samt Verlauf (die Oberfläche fragt vorher nach)."""
    if not await repository.loeschen(campaign_id, gruppe_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gruppe nicht gefunden")


@router.post("/{gruppe_id}/teilnehmer", response_model=GruppeResponse,
             dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_hinzufuegen(campaign_id: str, gruppe_id: str, body: TeilnehmerHinzufuegen):
    if not await repository.teilnehmer_hinzu(campaign_id, gruppe_id, body.personId):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gruppe oder Person nicht gefunden")
    return await _gm_antwort(campaign_id, gruppe_id)


@router.delete("/{gruppe_id}/teilnehmer/{person_id}", response_model=GruppeResponse,
               dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_entfernen(campaign_id: str, gruppe_id: str, person_id: str):
    if not await repository.teilnehmer_entfernen(campaign_id, gruppe_id, person_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teilnehmer nicht gefunden")
    return await _gm_antwort(campaign_id, gruppe_id)


@router.get("/{gruppe_id}/chat", response_model=GruppenChatResponse)
async def chat_lesen(campaign_id: str, gruppe_id: str, viewer: Viewer = Depends(get_viewer)):
    """Der Verlauf einer Gruppe. Neue Mitglieder sehen die ganze Historie."""
    roh = await _gruppe_oder_404(campaign_id, gruppe_id, viewer)
    als_gm = _ist_gm(viewer)
    ich_id = None if als_gm else viewer.person_id
    verlauf = await repository.nachrichten(campaign_id, gruppe_id)

    ids = [t["id"] for t in roh["teilnehmer"]] + [n["vonId"] for n in verlauf]
    aliase = await _aliase(campaign_id, viewer, ids)

    if not als_gm and ich_id:
        # Beim Öffnen gilt die Post als gelesen — sonst bliebe der Zähler stehen.
        await repository.markiere_gelesen(campaign_id, gruppe_id, ich_id)

    gruppe = gruppe_fuer(roh, ich_id=ich_id, aliase=aliase, als_gm=als_gm)
    return GruppenChatResponse(
        gruppe=gruppe,
        nachrichten=[nachricht_fuer(n, ich_id=ich_id, aliase=aliase, als_gm=als_gm) for n in verlauf],
        # Nur die SL schreibt als NPC — sie wählt aus den NPC-Mitgliedern.
        sprecher=[t for t in gruppe.teilnehmer if t.istNpc] if als_gm else [],
    )


@router.post("/{gruppe_id}/chat", response_model=GruppenNachrichtResponse)
async def nachricht_senden(
    campaign_id: str,
    gruppe_id: str,
    body: GruppenNachrichtCreate,
    viewer: Viewer = Depends(get_viewer),
):
    """Eine Nachricht in die Gruppe schreiben.

    **Vom Spieler aufrufbar** — als der eigene Charakter. Die SL schreibt als
    eines der NPC-Mitglieder (`alsPersonId`); ihr Name taucht nirgends auf.
    """
    roh = await _gruppe_oder_404(campaign_id, gruppe_id, viewer)
    if not roh["offen"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Die Gruppe ist geschlossen")
    als_gm = _ist_gm(viewer)

    if als_gm:
        npcs = {t["id"]: t for t in roh["teilnehmer"] if ist_npc(t)}
        if body.alsPersonId is None or body.alsPersonId not in npcs:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Wähle einen NPC aus der Gruppe, als der du schreibst"
            )
        von_id, rolle = body.alsPersonId, "GM"
    else:
        if body.alsPersonId is not None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Du schreibst immer als dein Charakter")
        if not viewer.person_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein eigener Charakter")
        von_id, rolle = viewer.person_id, "PLAYER"

    gesendet = await repository.sende(campaign_id, gruppe_id, von_id, body.inhalt, rolle)
    await _benachrichtigen(campaign_id, roh, von_id, body.inhalt)

    ich_id = None if als_gm else viewer.person_id
    aliase = await _aliase(campaign_id, viewer, [von_id])
    return nachricht_fuer(gesendet, ich_id=ich_id, aliase=aliase, als_gm=als_gm)


async def _benachrichtigen(campaign_id: str, gruppe: dict, von_id: str, inhalt: str) -> None:
    """Live-Hinweis über das Mitteilungen-System (wie beim Einzelchat).

    Eine Mitteilung hat nur eine Empfängerliste für alle — deshalb steht im Text
    nur der Gruppenname, nie ein Absender (der Name wäre je Empfänger ein anderer).
    Leere Liste heißt „an die SL“: die bekommt nur einen Hinweis, wenn ein Spieler
    schreibt UND mindestens ein NPC in der Gruppe sitzt (sie spricht ja für ihn).
    """
    vorschau = inhalt[:50] + ("..." if len(inhalt) > 50 else "")
    teilnehmer = gruppe["teilnehmer"]
    pcs = [t["id"] for t in teilnehmer if not ist_npc(t) and t["id"] != von_id]
    absender = next((t for t in teilnehmer if t["id"] == von_id), None)
    spieler_schreibt = absender is not None and not ist_npc(absender)
    hat_npc = any(ist_npc(t) for t in teilnehmer)
    absender_name = absender["name"] if absender else "Jemand"

    try:
        if pcs:
            m = await mitteilungen_repo.create_mitteilung(
                campaign_id=campaign_id,
                art="NACHRICHT",
                inhalt=f"{gruppe['name']}: {vorschau}",
                an_alle=False,
                empfaenger_ids=pcs,
                chat_art="GRUPPE",
                chat_id=gruppe["id"],
            )
            await verteiler.verteilen(campaign_id, m)
        if spieler_schreibt and hat_npc:
            m = await mitteilungen_repo.create_mitteilung(
                campaign_id=campaign_id,
                art="NACHRICHT",
                inhalt=f"{absender_name} in {gruppe['name']}: {vorschau}",
                an_alle=False,
                empfaenger_ids=[],
                chat_art="GRUPPE",
                chat_id=gruppe["id"],
            )
            await verteiler.verteilen(campaign_id, m)
    except Exception as e:  # Benachrichtigung darf das Senden nie blockieren
        logging.warning(f"Gruppenchat-Benachrichtigung fehlgeschlagen: {e}")
