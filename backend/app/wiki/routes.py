"""HTTP-Routen des Kampagnen-Wikis.

Leserouten hängen am Kampagnenzugang (Spieler dürfen freigegebene Seiten
lesen), schreibende Routen an der Spielleitung. Der strukturelle Test in
tests/test_zugriffsschutz.py prüft das für jede Route automatisch.

Gefiltert wird immer serverseitig über wiki/visibility.py — eine geheime
Seite wird gar nicht erst ausgeliefert.
"""

import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.wiki import repository
from app.wiki.logic import baum_bauen, inhaltsverzeichnis, seiten_bis_einschliesslich
from app.wiki.schemas import (
    BaumKnoten,
    BildAntwort,
    FreigabeAntwort,
    FreigabeRequest,
    Rueckverweis,
    SeiteCreate,
    SeiteMitVerzeichnis,
    SeiteResponse,
    SeiteUpdate,
    VerschiebeRequest,
)
from app.wiki.visibility import filter_seite_for_viewer, filter_seiten_for_viewer

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/wiki",
    tags=["wiki"],
    dependencies=[Depends(require_campaign_zugang)],
)

UPLOAD_DIR = Path("uploads")
ERLAUBTE_BILDTYPEN = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_BILD_BYTES = 8 * 1024 * 1024


def _ohne_inhalt(seite: dict) -> dict:
    """Baumknoten tragen keinen Inhalt — Dokumente können gross werden."""
    return {
        "id": seite["id"],
        "titel": seite["titel"],
        "symbol": seite.get("symbol") or "",
        "sortierung": seite.get("sortierung") or 0,
        "sichtbarkeit": seite.get("sichtbarkeit") or "GM",
        "sichtbarFuer": seite.get("sichtbarFuer") or [],
        "kinder": [_ohne_inhalt(k) for k in seite.get("kinder", [])],
    }


@router.get("/baum", response_model=list[BaumKnoten])
async def seitenbaum(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Seitenbaum für Tabs und Seitenleiste, bereits gefiltert.

    Erst filtern, dann den Baum bauen: Eine sichtbare Seite unter einem
    geheimen Kapitel würde sonst mitsamt ihrem Elternteil verschwinden.
    baum_bauen hängt sie stattdessen auf die oberste Ebene.
    """
    seiten = await repository.list_seiten(campaign_id)
    sichtbar = filter_seiten_for_viewer(seiten, viewer.role, viewer.person_id)
    return [_ohne_inhalt(k) for k in baum_bauen(sichtbar)]


@router.get("/seiten/{seiten_id}", response_model=SeiteMitVerzeichnis)
async def seite_lesen(campaign_id: str, seiten_id: str, viewer: Viewer = Depends(get_viewer)):
    seite = await repository.get_seite(campaign_id, seiten_id)
    if seite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Seite nicht gefunden")

    gefiltert = filter_seite_for_viewer(seite, viewer.role, viewer.person_id)
    if gefiltert is None:
        # 404 statt 403: Die Existenz einer geheimen Seite ist selbst geheim.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Seite nicht gefunden")

    # Verzeichnis aus dem *bereits gefilterten* Inhalt — sonst stünden geheime
    # Überschriften im Verzeichnis, obwohl der Absatz redigiert wurde.
    gefiltert["inhaltsverzeichnis"] = inhaltsverzeichnis(gefiltert["inhalt"], viewer.role)
    return gefiltert


@router.post("/seiten", response_model=SeiteResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_campaign_gm)])
async def seite_anlegen(campaign_id: str, body: SeiteCreate):
    seite = await repository.create_seite(
        campaign_id,
        titel=body.titel,
        inhalt=body.inhalt,
        parent_id=body.parentId,
        sichtbarkeit=body.sichtbarkeit,
        sichtbar_fuer=body.sichtbarFuer,
        symbol=body.symbol,
    )
    if seite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne nicht gefunden")
    return seite


@router.patch("/seiten/{seiten_id}", response_model=SeiteResponse,
              dependencies=[Depends(require_campaign_gm)])
async def seite_aendern(campaign_id: str, seiten_id: str, body: SeiteUpdate):
    seite = await repository.update_seite(campaign_id, seiten_id, body.model_dump(exclude_unset=True))
    if seite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Seite nicht gefunden")
    return seite


@router.post("/seiten/{seiten_id}/verschieben", response_model=SeiteResponse,
             dependencies=[Depends(require_campaign_gm)])
async def seite_verschieben(campaign_id: str, seiten_id: str, body: VerschiebeRequest):
    """Eigene Route, weil `parentId: null` hier "oberste Ebene" bedeutet.

    Im PATCH wäre das nicht von "Feld nicht mitgeschickt" zu unterscheiden.
    """
    felder: dict = {"parentId": body.parentId}
    if body.sortierung is not None:
        felder["sortierung"] = body.sortierung
    seite = await repository.update_seite(campaign_id, seiten_id, felder)
    if seite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Seite nicht gefunden")
    return seite


@router.delete("/seiten/{seiten_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_campaign_gm)])
async def seite_loeschen(campaign_id: str, seiten_id: str):
    if not await repository.delete_seite(campaign_id, seiten_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Seite nicht gefunden")


@router.post("/freigeben", response_model=FreigabeAntwort, dependencies=[Depends(require_campaign_gm)])
async def seiten_freigeben(campaign_id: str, body: FreigabeRequest):
    """Mehrere Seiten auf einmal freigeben.

    Mit `bisSeiteId` das "was bisher geschah": alles in Lesereihenfolge bis
    einschliesslich dieser Seite. Nach Session 3 einmal auf Kapitel 3 statt
    jede Seite einzeln.
    """
    seiten = await repository.list_seiten(campaign_id)

    if body.bisSeiteId:
        ids = seiten_bis_einschliesslich(seiten, body.bisSeiteId)
        if not ids:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Seite nicht gefunden")
    elif body.seitenIds:
        vorhanden = {s["id"] for s in seiten}
        ids = [i for i in body.seitenIds if i in vorhanden]
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "bisSeiteId oder seitenIds angeben")

    anzahl = await repository.freigeben(campaign_id, ids, body.sichtbarkeit, body.sichtbarFuer)
    return {"freigegeben": anzahl, "seitenIds": ids}


@router.get("/verweise/{ziel_id}", response_model=list[Rueckverweis])
async def rueckverweise(campaign_id: str, ziel_id: str, viewer: Viewer = Depends(get_viewer)):
    """Wo wird diese Entität erwähnt? ("Erwähnt in: Kapitel 1")

    Gefiltert wie alles andere: Ein Spieler darf nicht aus der Trefferliste
    schliessen, dass es eine geheime Seite über ihn gibt.
    """
    treffer = await repository.rueckverweise(campaign_id, ziel_id)
    sichtbar = filter_seiten_for_viewer(treffer, viewer.role, viewer.person_id)
    return [{"id": t["id"], "titel": t["titel"]} for t in sichtbar]


@router.post("/bilder", response_model=BildAntwort, dependencies=[Depends(require_campaign_gm)])
async def bild_hochladen(campaign_id: str, file: UploadFile = File(...)):
    """Bild für eine Wiki-Seite hochladen.

    Gleiche Ablage wie die Gegenstandsbilder (uploads/<campaign_id>/), damit
    es beim Sichern nur einen Ordner gibt. Der Dateiname wird neu vergeben —
    ein hochgeladener Name könnte sonst aus dem Ordner ausbrechen.
    """
    if file.content_type not in ERLAUBTE_BILDTYPEN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Bilddateien (PNG/JPEG/WEBP/GIF) erlaubt")

    inhalt = await file.read()
    if len(inhalt) > MAX_BILD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 8 MB)")

    ordner = UPLOAD_DIR / campaign_id
    ordner.mkdir(parents=True, exist_ok=True)
    endung = mimetypes.guess_extension(file.content_type) or ""
    name = f"wiki-{uuid.uuid4()}{endung}"
    (ordner / name).write_bytes(inhalt)

    return {"url": f"/uploads/{campaign_id}/{name}"}
