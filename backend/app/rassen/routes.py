"""Rassen-Baukasten und Freigabe je Kampagne.

Die Pfade hängen an einer Kampagne, die **Daten** aber nicht: der Katalog ist
global (siehe `repository.py`). Das ist derselbe Zuschnitt wie bei
`/chromstufen` — die Kennung im Pfad dient der Rechteprüfung
(`require_campaign_zugang`), nicht der Zuordnung. Ein eigener, kampagnenloser
Pfad bräuchte eine zweite Absicherung, ohne dass jemand etwas davon hätte.
"""

import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth.dependencies import require_campaign_gm, require_campaign_zugang
from app.rassen import repository
from app.rassen.balance import bilanz
from app.rassen.schemas import FreigabeRequest, RasseCreate, RasseResponse, RasseUpdate

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/rassen",
    tags=["rassen"],
    dependencies=[Depends(require_campaign_zugang)],
)

UPLOAD_DIR = Path("uploads")
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


def _mit_bilanz(rasse: dict, freigegeben: set[str] | None = None) -> dict:
    return {
        **rasse,
        "bilanz": bilanz(rasse["modifikatoren"], rasse["freiePunkte"]),
        "freigegeben": rasse["id"] in freigegeben if freigegeben is not None else False,
    }


@router.get("", response_model=list[RasseResponse])
async def verfuegbare_rassen(campaign_id: str):
    """Die in dieser Kampagne wählbaren Rassen — Grundlage der Erstellung.

    Für alle mit Zugang lesbar: welche Völker es in der Welt gibt, ist keine
    Auskunft der Spielleitung, sondern die Voraussetzung dafür, überhaupt
    einen Charakter bauen zu können.
    """
    rassen = await repository.liste_fuer_kampagne(campaign_id)
    return [_mit_bilanz(r) for r in rassen]


@router.get("/katalog", response_model=list[RasseResponse], dependencies=[Depends(require_campaign_gm)])
async def katalog(campaign_id: str):
    """Alle Rassen des Regelwerks, mit Häkchen für diese Kampagne.

    **Nur Spielleitung.** Muss vor `/{rasse_id}` stehen, sonst fängt die
    dortige Route den Pfad ab und "katalog" sähe wie eine Kennung aus —
    derselbe Grund wie beim Mülleimer in items/routes.py.
    """
    frei = set(await repository.freigegebene_ids(campaign_id))
    return [_mit_bilanz(r, frei) for r in await repository.liste()]


@router.put("/freigabe", response_model=list[str], dependencies=[Depends(require_campaign_gm)])
async def freigabe(campaign_id: str, body: FreigabeRequest):
    """Welche Rassen in dieser Kampagne zur Wahl stehen. **Nur Spielleitung.**"""
    return await repository.setze_freigabe(campaign_id, body.rasseIds)


@router.post("", response_model=RasseResponse, dependencies=[Depends(require_campaign_gm)])
async def anlegen(campaign_id: str, body: RasseCreate):
    """Neue Rasse bauen. **Nur Spielleitung.**

    Die Bilanz wird berechnet und mitgeliefert, aber **nicht erzwungen**
    (Marks Entscheidung): ein bewusst übermächtiges NPC-Volk muss möglich
    bleiben. Der Editor zeigt die Abweichung an, das Speichern gelingt.
    """
    return _mit_bilanz(await repository.anlegen(body.model_dump()))


@router.patch("/{rasse_id}", response_model=RasseResponse, dependencies=[Depends(require_campaign_gm)])
async def aendern(campaign_id: str, rasse_id: str, body: RasseUpdate):
    """Rasse bearbeiten. **Nur Spielleitung.** Eine Umbenennung wird auf alle
    Charaktere nachgezogen, die diese Rasse tragen (siehe repository.py)."""
    rasse = await repository.aendern(rasse_id, body.model_dump())
    if rasse is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rasse nicht gefunden")
    return _mit_bilanz(rasse)


@router.delete("/{rasse_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def loeschen(campaign_id: str, rasse_id: str):
    """Rasse aus dem Katalog entfernen. **Nur Spielleitung.**

    Bestehende Charaktere behalten ihren Rassennamen als Text — sie soll sich
    nur nicht mehr neu wählen lassen.
    """
    if not await repository.loeschen(rasse_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rasse nicht gefunden")


@router.post("/{rasse_id}/bild", response_model=RasseResponse, dependencies=[Depends(require_campaign_gm)])
async def bild_hochladen(campaign_id: str, rasse_id: str, file: UploadFile = File(...)):
    """Bild für die Infobox in der Charaktererstellung. **Nur Spielleitung.**

    Gleiches Vorgehen wie beim Gegenstandsbild (items/routes.py): Typ- und
    Größenprüfung, Ablage unter uploads/{campaign_id}/.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Bilddateien (PNG/JPEG/WEBP/GIF) erlaubt")

    inhalt = await file.read()
    if len(inhalt) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 8 MB)")

    ordner = UPLOAD_DIR / campaign_id
    ordner.mkdir(parents=True, exist_ok=True)
    endung = mimetypes.guess_extension(file.content_type) or ""
    dateiname = f"{uuid.uuid4()}{endung}"
    (ordner / dateiname).write_bytes(inhalt)

    rasse = await repository.setze_bild(rasse_id, f"/uploads/{campaign_id}/{dateiname}")
    if rasse is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rasse nicht gefunden")
    return _mit_bilanz(rasse)
