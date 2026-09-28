"""Zusatzfertigkeiten: SL-Katalog-CRUD + KI-Vorschläge + Spieler-Selbstbedienung
(Wählen/Steigern am eigenen Charakter).

Kein Freigabe-Schalter wie bei Rassen — die Tabelle in `repository.py` IST
schon die Freigabe für diese Kampagne (Marks Vorgabe, siehe dortiger
Modul-Docstring).

**Kosten-Design (eigene Entscheidung, siehe Abschlussbericht):** dieselbe
Freebee-/EP-Kostentabelle wie eine normale Fertigkeit (`FREEBEE_KOSTEN_JE_
KATEGORIE["Fertigkeit"]` bei der Erstellung, `erfahrung.kosten("Fertigkeit",
...)` beim Steigern nach der Erstellung). Das neu Erlernen einer
Zusatzfertigkeit während der Erstellung zieht aus einem EIGENEN, kleinen
Freebee-Kontingent (`ZUSATZFERTIGKEIT_FREEBEE_BUDGET`), nicht aus dem
Haupt-Freebee-Pool (`erstellung.FREEBEES_GESAMT`): der Hauptpool wird erst
bei der finalen `/erstellung`-Einreichung atomar geprüft (`pruefe()`/
`freebee_kosten()` rechnen rein aus dem eingereichten `ErstellungInput`-Body,
ohne Datenbankzustand) — ein separat auslösbarer Popup-Knopf, der schon
WÄHREND des mehrstufigen Assistenten sofort einen DB-Schreibzugriff macht,
kann in diese Rechnung nicht eingehängt werden, ohne den gesamten
Erstellungs-Flow umzubauen. Ein eigenes kleines Budget (analog zu
`HINTERGRUND_PUNKTE_GESAMT`, das ebenfalls ausserhalb des Haupt-Fertigkeits-
pakets separat budgetiert ist) ist die am wenigsten invasive Lösung.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.entities.repository import PERSON_FIELDS, get_node, update_node
from app.ki.client import KiFehler
from app.traits import erfahrung
from app.traits.erstellung import FREEBEE_KOSTEN_JE_KATEGORIE
from app.zusatzfertigkeiten import ki_vorschlag, repository
from app.zusatzfertigkeiten.ki_vorschlag import ZusatzfertigkeitVorschlag
from app.zusatzfertigkeiten.schemas import (
    ZusatzfertigkeitCreate,
    ZusatzfertigkeitHinzufuegenInput,
    ZusatzfertigkeitResponse,
    ZusatzfertigkeitUpdate,
)

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/zusatzfertigkeiten",
    tags=["zusatzfertigkeiten"],
    dependencies=[Depends(require_campaign_zugang)],
)

# Freebee-Kosten je NEU erlernter Zusatzfertigkeit während der Erstellung —
# derselbe Punktpreis wie eine normale Fertigkeit (siehe Moduldocstring).
FREEBEE_KOSTEN = FREEBEE_KOSTEN_JE_KATEGORIE["Fertigkeit"]
# Eigenes, kleines Kontingent nur für Zusatzfertigkeiten — reicht für drei
# Stück bei der Erstellung. Siehe Moduldocstring zur Begründung.
ZUSATZFERTIGKEIT_FREEBEE_BUDGET = 6


@router.get("", response_model=list[ZusatzfertigkeitResponse])
async def liste(campaign_id: str):
    """Der ganze Katalog dieser Kampagne — für SL-Tabelle UND Spieler-Popup
    (beide dürfen lesen, es gibt keine geheime Auswahl davon)."""
    return await repository.liste(campaign_id)


@router.post("", response_model=ZusatzfertigkeitResponse, dependencies=[Depends(require_campaign_gm)])
async def anlegen(campaign_id: str, body: ZusatzfertigkeitCreate):
    """Neuer Katalogeintrag. **Nur Spielleitung.**"""
    return await repository.anlegen(campaign_id, body.model_dump())


@router.patch("/{zusatzfertigkeit_id}", response_model=ZusatzfertigkeitResponse, dependencies=[Depends(require_campaign_gm)])
async def aendern(campaign_id: str, zusatzfertigkeit_id: str, body: ZusatzfertigkeitUpdate):
    """Katalogeintrag bearbeiten. **Nur Spielleitung.**"""
    eintrag = await repository.aendern(campaign_id, zusatzfertigkeit_id, body.model_dump())
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zusatzfertigkeit nicht gefunden")
    return eintrag


@router.delete("/{zusatzfertigkeit_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def loeschen(campaign_id: str, zusatzfertigkeit_id: str):
    """Aus dem Katalog entfernen — samt der Kanten zu Personen, die sie
    gewählt haben. **Nur Spielleitung.** Begründung siehe repository.py."""
    if not await repository.loeschen(campaign_id, zusatzfertigkeit_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zusatzfertigkeit nicht gefunden")


# =====================================================================
# KI-Vorschläge
# =====================================================================


class KiVorschlaegeAntwort(BaseModel):
    vorschlaege: list[ZusatzfertigkeitVorschlag] = []


@router.get("/ki-vorschlaege", response_model=KiVorschlaegeAntwort, dependencies=[Depends(require_campaign_gm)])
async def ki_vorschlaege(campaign_id: str, anzahl: int = 5):
    """Liefert 3-5 KI-Kandidaten zur Ansicht — speichert nichts.
    **Nur Spielleitung**, wie beim Händler-Sortiment-Vorschlag."""
    try:
        ergebnis = await ki_vorschlag.vorschlaege(campaign_id, anzahl)
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))
    return KiVorschlaegeAntwort(vorschlaege=ergebnis.vorschlaege)


@router.post("/ki-vorschlaege/uebernehmen", response_model=ZusatzfertigkeitResponse, dependencies=[Depends(require_campaign_gm)])
async def ki_vorschlag_uebernehmen(campaign_id: str, body: ZusatzfertigkeitVorschlag):
    """Legt EINEN bestätigten (ggf. editierten) Vorschlag im Katalog an.
    **Nur Spielleitung.**"""
    return await ki_vorschlag.uebernehmen(campaign_id, body)


# =====================================================================
# Personen: wählen und steigern
# =====================================================================


class PersonZusatzfertigkeitenAntwort(BaseModel):
    gewaehlt: list[dict]
    erstellungAbgeschlossen: bool
    # Nur vor Erstellungsabschluss relevant (Freebee-Kontingent).
    freebeesUebrig: int
    # Nur nach Erstellungsabschluss relevant (EP-Kontingent).
    erfahrungVerfuegbar: int


async def _antwort(campaign_id: str, person: dict) -> PersonZusatzfertigkeitenAntwort:
    gewaehlt = await repository.zusatzfertigkeiten_der_person(campaign_id, person["id"])
    ausgegeben = int(person.get("zusatzfertigkeitenFreebeesAusgegeben") or 0)
    verfuegbar = max(0, int(person.get("erfahrung") or 0) - int(person.get("erfahrungAusgegeben") or 0))
    return PersonZusatzfertigkeitenAntwort(
        gewaehlt=gewaehlt,
        erstellungAbgeschlossen=bool(person.get("erstellungAbgeschlossen")),
        freebeesUebrig=max(0, ZUSATZFERTIGKEIT_FREEBEE_BUDGET - ausgegeben),
        erfahrungVerfuegbar=verfuegbar,
    )


# Eigener Router für die Personen-Unterrouten, weil der Pfad
# .../personen/{person_id}/zusatzfertigkeiten NICHT unter dem
# /zusatzfertigkeiten-Präfix des Katalog-Routers liegt.
personen_router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/personen/{person_id}/zusatzfertigkeiten",
    tags=["zusatzfertigkeiten"],
    dependencies=[Depends(require_campaign_zugang)],
)


@personen_router.get("", response_model=PersonZusatzfertigkeitenAntwort)
async def get_person_zusatzfertigkeiten(campaign_id: str, person_id: str, viewer: Viewer = Depends(get_viewer)):
    """Gewählte Zusatzfertigkeiten samt Kostenkontingent — für Charakterblatt,
    Spieler-Popup UND LevelUp.

    Wie bei anderen Personen-Leserouten (traits/routes.py::get_werte):
    Spieler sehen ausschliesslich ihren eigenen Charakter.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    return await _antwort(campaign_id, person)


@personen_router.post("", response_model=PersonZusatzfertigkeitenAntwort)
async def zusatzfertigkeit_hinzufuegen(
    campaign_id: str, person_id: str, body: ZusatzfertigkeitHinzufuegenInput, viewer: Viewer = Depends(get_viewer)
):
    """Eine noch nicht gewählte Zusatzfertigkeit mit Stufe 1 anlegen.

    Spieler dürfen das an ihrem eigenen Charakter — genau wie das normale
    Steigern (traits/routes.py::steigere_wert). Zieht Freebee ODER EP ab,
    je nachdem ob die Erstellung schon abgeschlossen ist (Moduldocstring).
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    zusatzfertigkeit = await repository.hole(campaign_id, body.zusatzfertigkeitId)
    if zusatzfertigkeit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zusatzfertigkeit nicht gefunden")

    bereits = await repository.gewaehlte_ids(campaign_id, person_id)
    if body.zusatzfertigkeitId in bereits:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{zusatzfertigkeit['name']} ist bereits gewählt.")

    if person.get("erstellungAbgeschlossen"):
        # Spielphase: wie eine ganz normale Fertigkeit von 0 auf 1 kaufen.
        preis = erfahrung.kosten("Fertigkeit", 0) or 0
        verfuegbar = max(0, int(person.get("erfahrung") or 0) - int(person.get("erfahrungAusgegeben") or 0))
        if preis > verfuegbar:
            raise HTTPException(status.HTTP_409_CONFLICT, f"{preis} EP nötig, {verfuegbar} vorhanden.")
        await repository.hinzufuegen(campaign_id, person_id, body.zusatzfertigkeitId, 1)
        aktualisiert = await update_node(
            "Person", PERSON_FIELDS, campaign_id, person_id,
            {"erfahrungAusgegeben": int(person.get("erfahrungAusgegeben") or 0) + preis},
        )
    else:
        # Erstellungsphase: eigenes kleines Freebee-Kontingent (Moduldocstring).
        ausgegeben = int(person.get("zusatzfertigkeitenFreebeesAusgegeben") or 0)
        uebrig = max(0, ZUSATZFERTIGKEIT_FREEBEE_BUDGET - ausgegeben)
        if FREEBEE_KOSTEN > uebrig:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"{FREEBEE_KOSTEN} Freebees nötig, {uebrig} vorhanden."
            )
        await repository.hinzufuegen(campaign_id, person_id, body.zusatzfertigkeitId, 1)
        aktualisiert = await update_node(
            "Person", PERSON_FIELDS, campaign_id, person_id,
            {"zusatzfertigkeitenFreebeesAusgegeben": ausgegeben + FREEBEE_KOSTEN},
        )

    return await _antwort(campaign_id, aktualisiert or person)


@personen_router.post("/{zusatzfertigkeit_id}/steigern", response_model=PersonZusatzfertigkeitenAntwort)
async def zusatzfertigkeit_steigern(
    campaign_id: str, person_id: str, zusatzfertigkeit_id: str, viewer: Viewer = Depends(get_viewer)
):
    """Eine bereits gewählte Zusatzfertigkeit um einen Punkt anheben.

    Immer EP-Kosten wie eine normale Fertigkeit — genau wie beim
    Haupt-Katalog gibt es für das Steigern (im Unterschied zum Neu-Lernen)
    keine Freebee-Variante, siehe traits/routes.py::steigere_wert (kennt
    ebenfalls keine Erstellungsphasen-Unterscheidung).
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    gewaehlt = await repository.zusatzfertigkeiten_der_person(campaign_id, person_id)
    eintrag = next((z for z in gewaehlt if z["id"] == zusatzfertigkeit_id), None)
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Diese Zusatzfertigkeit ist nicht gewählt.")
    if eintrag["rating"] >= 6:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{eintrag['name']} steht bereits auf dem Maximum 6.")

    preis = erfahrung.kosten("Fertigkeit", eintrag["rating"]) or 0
    verfuegbar = max(0, int(person.get("erfahrung") or 0) - int(person.get("erfahrungAusgegeben") or 0))
    if preis > verfuegbar:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{preis} EP nötig, {verfuegbar} vorhanden.")

    await repository.steigere(campaign_id, person_id, zusatzfertigkeit_id, eintrag["rating"] + 1)
    aktualisiert = await update_node(
        "Person", PERSON_FIELDS, campaign_id, person_id,
        {"erfahrungAusgegeben": int(person.get("erfahrungAusgegeben") or 0) + preis},
    )
    return await _antwort(campaign_id, aktualisiert or person)
