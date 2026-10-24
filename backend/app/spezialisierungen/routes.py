"""Fertigkeiten-Spezialisierungen: Slots benennen und zusätzliche kaufen.

Die AUTOMATISCHE Vergabe (Rating 4/6) passiert nicht hier, sondern in
app/traits/repository.py (set_rating/steigere/set_ratings_bulk) — diese
Routen decken nur die beiden Spieler-/SL-Aktionen ab: einen Slot (be)nennen
und einen zusätzlichen Slot für 4 EP kaufen.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.entities.repository import PERSON_FIELDS, get_node, update_node
from app.ereignisprotokoll import hooks
from app.spezialisierungen import repository
from app.spezialisierungen.schemas import (
    SpezialisierungAufraeumenResponse,
    SpezialisierungBenennenInput,
    SpezialisierungKampagneResponse,
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
    (Mark: "das darf gerne unbegrenzt wachsen"), solange die Fertigkeit/
    Sphäre mindestens auf ihrer ersten Auto-Grant-Schwelle steht (4 bei
    Fertigkeiten/NeuroWeaving, 2 bei Sphären — siehe
    spezialisierungen_repository.schwellen_fuer). Dieselbe EP-Bilanz wie
    beim normalen Steigern (`erfahrung - erfahrungAusgegeben`), aber ohne
    die Formel aus `erfahrung.kosten()` — fester Preis statt wert-
    abhängiger Staffelung.
    """
    _pruefe_zugriff(viewer, person_id)
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    werte = await traits_repository.get_ratings_for_entity(campaign_id, person_id)
    eintrag = next((w for w in werte if w["traitDefId"] == body.traitDefId), None)
    if eintrag is None or eintrag["category"] not in repository.ALLE_SPEZIALISIERUNGS_KATEGORIEN:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Keine Fertigkeit oder Sphäre, die Spezialisierungen kennt."
        )
    mindest_rating = repository.schwellen_fuer(eintrag["category"])[0]
    if eintrag["rating"] < mindest_rating:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{eintrag['name']} muss mindestens auf {mindest_rating} stehen, bevor zusätzliche Spezialisierungen möglich sind.",
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


@router.delete(
    "/{spezialisierung_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_campaign_gm)],
)
async def entfernen(campaign_id: str, person_id: str, spezialisierung_id: str):
    """Slot löschen — nur die SL. Senken des Ratings löscht nie von selbst
    (repository.automatische_slot_anzahl); das hier ist der ausdrückliche
    Weg, einen versehentlich vergebenen Slot wieder wegzunehmen.

    Ein gekaufter Slot erstattet die 4 EP (Gegenbuchung auf
    erfahrungAusgegeben). Ein automatischer erstattet nichts — der Anspruch
    kam von der Schwelle, nicht von EP.
    """
    eintrag = await repository.hole(campaign_id, person_id, spezialisierung_id)
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Spezialisierung nicht gefunden")

    weg = await repository.loeschen(campaign_id, person_id, spezialisierung_id)
    if weg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Spezialisierung nicht gefunden")

    erstattet = 0
    if weg["quelle"] == "gekauft":
        person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
        if person is not None:
            ausgegeben = int(person.get("erfahrungAusgegeben") or 0)
            erstattet = min(KAUF_PREIS, ausgegeben)
            await update_node(
                "Person", PERSON_FIELDS, campaign_id, person_id,
                {"erfahrungAusgegeben": ausgegeben - erstattet},
            )

    werte = await traits_repository.get_ratings_for_entity(campaign_id, person_id)
    trait = next((w for w in werte if w["traitDefId"] == weg["traitDefId"]), None)
    await hooks.charakterentwicklung(
        campaign_id, person_id=person_id, art="SPEZIALISIERUNG_ENTFERNT",
        trait_def_id=weg["traitDefId"], trait_name=trait["name"] if trait else None,
        alt=weg["text"] or "(unbenannt)", neu="",
        kosten_oder_menge=-erstattet,
        sl_notiz="Gekaufter Spezialisierungs-Slot entfernt, 4 EP erstattet"
        if erstattet
        else "Spezialisierungs-Slot entfernt",
    )


kampagne_router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/spezialisierungen",
    tags=["spezialisierungen"],
    dependencies=[Depends(require_campaign_gm)],
)


@kampagne_router.get("", response_model=list[SpezialisierungKampagneResponse])
async def kampagne_liste(campaign_id: str):
    """Alle Slots der Kampagne — zum Aufräumen, nicht für Spieler."""
    return await repository.fuer_kampagne(campaign_id)


@kampagne_router.post("/leere-unter-schwelle", response_model=SpezialisierungAufraeumenResponse)
async def leere_unter_schwelle_entfernen(campaign_id: str):
    """Räumt nur leere automatische Slots auf, deren Fertigkeit die erste
    Schwelle nicht mehr erreicht. Benannte und gekaufte bleiben — die
    nimmt die SL einzeln weg, falls sie das will."""
    alle = await repository.fuer_kampagne(campaign_id)
    ziel = [
        e for e in alle
        if e["unterSchwelle"] and not e["text"] and e["quelle"] == "automatisch"
    ]
    entfernt = 0
    for eintrag in ziel:
        weg = await repository.loeschen(campaign_id, eintrag["personId"], eintrag["id"])
        if weg is None:
            continue
        entfernt += 1
        await hooks.charakterentwicklung(
            campaign_id, person_id=eintrag["personId"], art="SPEZIALISIERUNG_ENTFERNT",
            trait_def_id=weg["traitDefId"], trait_name=eintrag["traitName"],
            alt="(unbenannt)", neu="", kosten_oder_menge=0,
            sl_notiz="Leerer Spezialisierungs-Slot unter der Schwelle entfernt",
        )
    return {"entfernt": entfernt}
