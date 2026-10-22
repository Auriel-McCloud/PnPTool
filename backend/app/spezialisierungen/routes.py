"""Fertigkeiten-Spezialisierungen: Slots benennen und zusätzliche kaufen.

Die AUTOMATISCHE Vergabe (Rating 4/6) passiert nicht hier, sondern in
app/traits/repository.py (set_rating/steigere/set_ratings_bulk) — diese
Routen decken nur die beiden Spieler-/SL-Aktionen ab: einen Slot (be)nennen
und einen zusätzlichen Slot für 4 EP kaufen.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_zugang
from app.entities.repository import PERSON_FIELDS, get_node, update_node
from app.ereignisprotokoll import hooks
from app.spezialisierungen import repository
from app.spezialisierungen.schemas import (
    SpezialisierungBenennenInput,
    SpezialisierungKaufenInput,
    SpezialisierungResponse,
)
from app.traits import repository as traits_repository

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/personen/{person_id}/spezialisierungen",
    tags=["spezialisierungen"],
    dependencies=[Depends(require_campaign_zugang)],
)

# Flacher Kaufpreis (Marks Vorgabe) — KEINE erfahrung.kosten()-Formel, siehe
# Moduldocstring in repository.py und den Feature-Bericht.
KAUF_PREIS = 4


def _pruefe_zugriff(viewer: Viewer, person_id: str) -> None:
    """Gleiche Ownership-Regel wie überall sonst bei Personen-Unterrouten
    (siehe zusatzfertigkeiten/routes.py): SL sieht/ändert jede Person dieser
    Kampagne, ein Spieler nur den eigenen Charakter."""
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")


@router.get("", response_model=list[SpezialisierungResponse])
async def liste(campaign_id: str, person_id: str, viewer: Viewer = Depends(get_viewer)):
    """Alle Spezialisierungen dieser Person — benannte UND noch leere Slots.
    Das Charakterblatt gruppiert clientseitig nach traitDefId."""
    _pruefe_zugriff(viewer, person_id)
    return await repository.fuer_person(campaign_id, person_id)


@router.post("/{spezialisierung_id}/benennen", response_model=SpezialisierungResponse)
async def benennen(
    campaign_id: str,
    person_id: str,
    spezialisierung_id: str,
    body: SpezialisierungBenennenInput,
    viewer: Viewer = Depends(get_viewer),
):
    """Einen Slot (be)nennen.

    Zweiphasiges Namensrecht (Marks Vorgabe, wörtlich: "nachträglich sollte
    nur der SL sie ändern können" — 'nachträglich' = nach der ersten
    Benennung, also darf die ERSTE Benennung durch den Spieler passieren):
    ein noch LEERER Slot darf vom Spieler ODER der SL einmalig benannt
    werden (Vorschlag-Chip oder Freitext, siehe Frontend-Popup). Ist einmal
    Text drin, darf nur noch die SL ihn ändern — der Spieler bekommt dann
    403. Die SL selbst ist nie gesperrt, auch nicht bei einem schon
    benannten Slot.
    """
    _pruefe_zugriff(viewer, person_id)
    eintrag = await repository.hole(campaign_id, person_id, spezialisierung_id)
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Spezialisierung nicht gefunden")
    if eintrag["text"] and viewer.role != "GM":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Bereits benannt — nachträglich ändert nur die Spielleitung das.",
        )
    aktualisiert = await repository.benennen(
        campaign_id, person_id, spezialisierung_id, body.text.strip(), als_spieler=viewer.role != "GM"
    )
    if aktualisiert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Spezialisierung nicht gefunden")
    return aktualisiert


@router.post("/kaufen", response_model=SpezialisierungResponse)
async def kaufen(
    campaign_id: str, person_id: str, body: SpezialisierungKaufenInput, viewer: Viewer = Depends(get_viewer)
):
    """Einen ZUSÄTZLICHEN Slot für 4 EP kaufen — unbegrenzt oft wiederholbar
    (Mark: "das darf gerne unbegrenzt wachsen"), solange die Fertigkeit
    mindestens auf 4 steht. Dieselbe EP-Bilanz wie beim normalen Steigern
    (`erfahrung - erfahrungAusgegeben`), aber ohne die Formel aus
    `erfahrung.kosten()` — fester Preis statt wert-abhängiger Staffelung.
    """
    _pruefe_zugriff(viewer, person_id)
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    werte = await traits_repository.get_ratings_for_entity(campaign_id, person_id)
    eintrag = next((w for w in werte if w["traitDefId"] == body.traitDefId), None)
    if eintrag is None or eintrag["category"] not in repository.FERTIGKEIT_KATEGORIEN:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Keine Fertigkeit, die Spezialisierungen kennt."
        )
    if eintrag["rating"] < 4:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{eintrag['name']} muss mindestens auf 4 stehen, bevor zusätzliche Spezialisierungen möglich sind.",
        )

    verfuegbar = max(0, int(person.get("erfahrung") or 0) - int(person.get("erfahrungAusgegeben") or 0))
    if KAUF_PREIS > verfuegbar:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{KAUF_PREIS} EP nötig, {verfuegbar} vorhanden.")

    neu = await repository.gekauft_anlegen(campaign_id, person_id, body.traitDefId)
    ausgegeben = int(person.get("erfahrungAusgegeben") or 0)
    await update_node(
        "Person", PERSON_FIELDS, campaign_id, person_id,
        {"erfahrungAusgegeben": ausgegeben + KAUF_PREIS},
    )
    # Ereignisprotokoll: eigene CharakterEntwicklung-Art, analog zu
    # STEIGERUNG/WILLENSKRAFT/ERFAHRUNG_VERGEBEN (siehe traits/routes.py).
    # `art` ist ein freier String (kein Enum) — keine Erweiterung nötig.
    await hooks.charakterentwicklung(
        campaign_id, person_id=person_id, art="SPEZIALISIERUNG",
        trait_def_id=body.traitDefId, trait_name=eintrag["name"],
        alt="", neu="", kosten_oder_menge=KAUF_PREIS,
        sl_notiz="Zusätzlicher Spezialisierungs-Slot gekauft",
    )
    return neu
