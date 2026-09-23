"""HTTP-Routen für den Shop: Sortiment, Standort, Kaufen.

Anlegen/Bearbeiten eines Händlers (Name, Bild, Beschreibung, Spezialisierung)
läuft über die bestehenden `/personen`-Routen (`istHaendler=true`, siehe
app/entities/routes.py) — hier nur das Shop-spezifische.

**Kauf-Flow**: Bestätigung passiert im Frontend (Commlink-Popup, Marks
Vorgabe für destruktive/geldwirksame Aktionen). Der Server prüft Guthaben
serverseitig noch einmal — ein Client darf nie der einzige Wächter über
Nuyen sein.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.entities import repository as entities_repository
from app.entities.repository import PERSON_FIELDS
from app.entities.visibility import is_visible_to
from app.haendler import repository
from app.haendler import ki_vorschlag
from app.haendler.ki_vorschlag import AnwendenErgebnis, SortimentVorschlag, VorschlaegeAntwort
from app.haendler.schemas import (
    HaendlerEintrag,
    KaufRequest,
    KaufResponse,
    SortimentEintrag,
    SortimentHinzufuegenRequest,
    StandortRequest,
)
from app.items import repository as items_repository

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/haendler",
    tags=["haendler"],
    dependencies=[Depends(require_campaign_zugang)],
)


@router.get("", response_model=list[HaendlerEintrag])
async def alle(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Alle Händler dieser Kampagne — für Kachel-Übersicht/Kontaktliste."""
    roh = await repository.liste(campaign_id)
    return [
        h for h in roh
        if is_visible_to(h.get("sichtbarkeit") or "GM", h.get("sichtbarFuer") or [], viewer.role, viewer.person_id)
    ]


async def _haendler_oder_404(campaign_id: str, haendler_id: str, viewer: Viewer) -> dict:
    haendler = await repository.hole(campaign_id, haendler_id)
    if haendler is None or not is_visible_to(
        haendler.get("sichtbarkeit") or "GM", haendler.get("sichtbarFuer") or [], viewer.role, viewer.person_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Händler nicht gefunden")
    return haendler


@router.get("/{haendler_id}", response_model=HaendlerEintrag)
async def einzeln(campaign_id: str, haendler_id: str, viewer: Viewer = Depends(get_viewer)):
    return await _haendler_oder_404(campaign_id, haendler_id, viewer)


@router.put("/{haendler_id}/standort", response_model=HaendlerEintrag, dependencies=[Depends(require_campaign_gm)])
async def standort_setzen(campaign_id: str, haendler_id: str, body: StandortRequest):
    """Der Laden — an welchem Ort dieser Händler zu finden ist. Leerer Body
    löst die Bindung (Händler ohne festen Standort, nur per Messenger
    erreichbar)."""
    ergebnis = await repository.standort_setzen(campaign_id, haendler_id, body.ortId)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Händler oder Ort nicht gefunden")
    return ergebnis


@router.get("/{haendler_id}/sortiment", response_model=list[SortimentEintrag])
async def sortiment(campaign_id: str, haendler_id: str, viewer: Viewer = Depends(get_viewer)):
    """Was dieser Händler verkauft — explizite Ware + automatischer
    Katalog-Bestand nach Spezialisierung gefiltert (siehe repository.py)."""
    await _haendler_oder_404(campaign_id, haendler_id, viewer)
    return await repository.sortiment(campaign_id, haendler_id)


@router.post(
    "/{haendler_id}/sortiment", response_model=list[SortimentEintrag], dependencies=[Depends(require_campaign_gm)]
)
async def sortiment_hinzufuegen(campaign_id: str, haendler_id: str, body: SortimentHinzufuegenRequest):
    """Ware explizit ins Sortiment aufnehmen — mit optionalem Sonderpreis
    (Auf-/Abschlag). Ohne Preisangabe gilt der Grundpreis des Gegenstands."""
    gegenstand = await items_repository.get_gegenstand(campaign_id, body.gegenstandId)
    if gegenstand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    preis = body.preis if body.preis is not None else gegenstand["preis"]
    if not await repository.verkauft_hinzufuegen(campaign_id, haendler_id, body.gegenstandId, preis):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Händler nicht gefunden")
    return await repository.sortiment(campaign_id, haendler_id)


@router.delete(
    "/{haendler_id}/sortiment/{gegenstand_id}",
    response_model=list[SortimentEintrag],
    dependencies=[Depends(require_campaign_gm)],
)
async def sortiment_entfernen(campaign_id: str, haendler_id: str, gegenstand_id: str):
    """Nimmt eine explizit eingetragene Ware wieder aus dem Sortiment.

    Wirkt NICHT auf automatisch gelistete Vorlagen (automatischImShop) — die
    lassen sich nur über die Vorlage selbst oder die Spezialisierung des
    Händlers entfernen, siehe repository.py::sortiment.
    """
    await repository.verkauft_entfernen(campaign_id, haendler_id, gegenstand_id)
    return await repository.sortiment(campaign_id, haendler_id)


@router.post("/{haendler_id}/kaufen", response_model=KaufResponse)
async def kaufen(campaign_id: str, haendler_id: str, body: KaufRequest, viewer: Viewer = Depends(get_viewer)):
    """Kauft ein Stück aus dem Sortiment dieses Händlers.

    **Spieler kaufen für sich selbst** (kaeuferPersonId wird ignoriert — wie
    beim Messenger kann sich niemand als fremder Charakter ausgeben). **Die
    SL kann für jeden PC kaufen** (z.B. NPC schenkt/verkauft etwas spontan im
    Spiel). Server prüft Guthaben noch einmal selbst — ein Bestätigungs-Popup
    im Frontend ersetzt diese Prüfung nicht, sie ist nur UX.
    """
    await _haendler_oder_404(campaign_id, haendler_id, viewer)

    if viewer.role == "GM":
        if not body.kaeuferPersonId:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "kaeuferPersonId erforderlich")
        kaeufer_id = body.kaeuferPersonId
    else:
        if not viewer.person_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein eigener Charakter")
        kaeufer_id = viewer.person_id

    preis = await repository.effektiver_preis(campaign_id, haendler_id, body.gegenstandId)
    if preis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Diese Ware führt der Händler nicht (mehr)")

    kaeufer = await entities_repository.get_node("Person", PERSON_FIELDS, campaign_id, kaeufer_id)
    if kaeufer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Käufer nicht gefunden")

    kapital = kaeufer.get("kapital", 0)
    if kapital < preis:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Guthaben reicht nicht — {kapital}¥ verfügbar, {preis}¥ nötig",
        )

    gegenstand = await items_repository.get_gegenstand(campaign_id, body.gegenstandId)
    if gegenstand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    if gegenstand["istVorlage"]:
        # Unendlich verfügbar: eine unabhängige Kopie für den Käufer, die
        # Vorlage selbst bleibt im Sortiment stehen (dasselbe Muster wie
        # items/routes.py::zuweisen für Vorlagen).
        gekauft = await items_repository.assign_copy(campaign_id, gegenstand, kaeufer_id, "SPEZIFISCH", [kaeufer_id])
    else:
        # Einzigartiges Stück: Besitzerwechsel vom Händler zum Käufer, danach
        # verschwindet es aus dem Sortiment (VERKAUFT-Kante war an den
        # Gegenstand geknüpft und wird beim Besitzerwechsel nicht neu
        # gesetzt — ein Blick ins Sortiment findet es also nicht mehr).
        gekauft = await items_repository.transfer_owner(campaign_id, body.gegenstandId, kaeufer_id)
        await repository.verkauft_entfernen(campaign_id, haendler_id, body.gegenstandId)
    if gekauft is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kauf fehlgeschlagen")

    kapital_neu = kapital - preis
    await entities_repository.update_node(
        "Person", PERSON_FIELDS, campaign_id, kaeufer_id, {"kapital": kapital_neu}
    )

    return KaufResponse(gegenstand=gekauft, kapitalNeu=kapital_neu)


@router.get(
    "/{haendler_id}/ki-vorschlaege",
    response_model=VorschlaegeAntwort,
    dependencies=[Depends(require_campaign_gm)],
)
async def ki_vorschlaege(campaign_id: str, haendler_id: str, anzahl: int = 5):
    """Lässt die KI passende Sortiment-Lücken für diesen Händler vorschlagen.

    Bevorzugt bestehende Gegenstands-Vorlagen der Kampagne wiederzuverwenden,
    erfindet nur bei einer echten Lücke etwas Neues (siehe ki_vorschlag.py).
    Nichts wird hier gespeichert — der SL bestätigt jeden Vorschlag einzeln
    über /ki-vorschlaege/anwenden.
    """
    await _haendler_oder_404(campaign_id, haendler_id, Viewer(role="GM", person_id=None))
    return await ki_vorschlag.vorschlaege(campaign_id, haendler_id, anzahl)


@router.post(
    "/{haendler_id}/ki-vorschlaege/anwenden",
    response_model=AnwendenErgebnis,
    dependencies=[Depends(require_campaign_gm)],
)
async def ki_vorschlag_anwenden(campaign_id: str, haendler_id: str, body: SortimentVorschlag):
    """Übernimmt EINEN bestätigten KI-Vorschlag ins Sortiment.

    Bei einer neu erfundenen Ware entsteht zuerst eine Vorlage
    (istEntwurf=true, wie jeder andere KI-Gegenstand aus der Ideenschmiede),
    danach kommt sie genau wie eine bestehende Vorlage ins Sortiment.
    """
    ergebnis = await ki_vorschlag.anwenden(campaign_id, haendler_id, body)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Händler oder Gegenstand nicht gefunden")
    return ergebnis
