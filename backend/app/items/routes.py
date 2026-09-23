import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_einstellungen
from app.entities.repository import PERSON_FIELDS, get_node
from app.entities.visibility import filter_gegenstaende_for_viewer
from app.items import chirurgie, repository
from app.items.chrom import KOERPERZONEN, stufen_uebersicht
from app.items.schemas import (
    AblageRequest,
    AblageZiel,
    GegenstandCreate,
    GegenstandMitBesitzer,
    GegenstandResponse,
    GegenstandUpdate,
    ZuweisenRequest,
)
from app.kampf.ruestung import (
    haendler_reparatur_preis,
    hardware_probe_pool,
    repariere,
    selbstreparatur_ergebnis,
)
from app.traits.repository import get_ratings_for_entity
from app.wuerfel.logic import wuerfle

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/personen/{person_id}/gegenstaende",
    tags=["items"],
    dependencies=[Depends(require_campaign_zugang)],
)

# Kampagnenweite Übersicht (alle Gegenstände aller Personen) — eigener Router,
# weil der Pfad kein {person_id} enthält und daher nicht in obiges Prefix passt.
campaign_router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/gegenstaende",
    tags=["items"],
    dependencies=[Depends(require_campaign_zugang)],
)

UPLOAD_DIR = Path("uploads")
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


@campaign_router.get("", response_model=list[GegenstandMitBesitzer])
async def list_all_items(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    items = await repository.list_alle_gegenstaende(campaign_id)
    return filter_gegenstaende_for_viewer(items, viewer.role, viewer.person_id)


def _default_sichtbarkeit(person_type: str, person_id: str) -> tuple[str, list[str]]:
    # Standard: Gegenstände von Spielercharakteren sind automatisch nur für
    # diesen Spieler sichtbar, bei NPCs bleiben sie SL-geheim. Der SL kann das
    # beim Anlegen/Zuweisen jederzeit explizit übersteuern.
    if person_type == "PC":
        return "SPEZIFISCH", [person_id]
    return "GM", []


# Was man nicht am Körper trägt: ein Fahrzeug liegt nicht im Rucksack.
# Sonst zählte sein Gewicht gegen die Traglast seines Besitzers.
NICHT_AM_KOERPER = {"Fahrzeug"}


def _create_data(body: GegenstandCreate, ist_vorlage: bool, sichtbarkeit: str, sichtbar_fuer: list[str]) -> dict:
    ablage = body.ablage
    # Nur vorbelegen, wenn nichts Abweichendes gewünscht war — ein Modellauto
    # darf durchaus im Rucksack liegen, das kann jederzeit umgestellt werden.
    if body.typ in NICHT_AM_KOERPER and ablage == "RUCKSACK":
        ablage = "GELAGERT"
    return {
        "name": body.name,
        "description": body.description,
        "notes": body.notes,
        "typ": body.typ,
        "preis": body.preis,
        "kraft": body.kraft,
        "cyberwall": body.cyberwall,
        "eigenschaften": body.eigenschaften,
        "zeigeInGraph": body.zeigeInGraph,
        "einzigartig": body.einzigartig,
        "hatMenge": body.hatMenge,
        "menge": body.menge,
        "istVorlage": ist_vorlage,
        "seltenheit": body.seltenheit,
        "automatischImShop": body.automatischImShop,
        "ablage": ablage,
        "gewicht": body.gewicht,
        "kapazitaet": body.kapazitaet,
        # Cyber-/Bioware und Sonderwirkungen. Diese Liste war unvollständig:
        # Felder, die hier fehlen, gehen beim Anlegen still verloren — sie
        # lassen sich danach nur per PATCH nachtragen. Beim Ergänzen eines
        # neuen Feldes im Schema also IMMER auch hier eintragen.
        "wVerlust": body.wVerlust,
        "koerperzone": body.koerperzone,
        "slot": body.slot,
        "istWaffe": body.istWaffe,
        "schaden": body.schaden,
        "traitBoni": body.traitBoni,
        "ausruestungsfertigkeiten": body.ausruestungsfertigkeiten,
        "riggerBonus": body.riggerBonus,
        "maxDrohnen": body.maxDrohnen,
        "immerSichtbar": body.immerSichtbar,
        "deckBruteForce": body.deckBruteForce,
        "deckSchleichen": body.deckSchleichen,
        "deckDaten": body.deckDaten,
        "deckKompilieren": body.deckKompilieren,
        "deckElectronicWarfare": body.deckElectronicWarfare,
        "deckMatrixNavigation": body.deckMatrixNavigation,
        "stufe": body.stufe,
        "widerstand": body.widerstand,
        "angriff": body.angriff,
        "agilitaet": body.agilitaet,
        "fahrzeugFertigkeiten": body.fahrzeugFertigkeiten,
        # Reflex-Booster & Co. (Regelblatt Zeile 57, 421-444).
        "initiativeBonus": body.initiativeBonus,
        "verbaut": body.verbaut,
        "zusatzaktionen": body.zusatzaktionen,
        "sichtbarkeit": sichtbarkeit,
        "sichtbarFuer": sichtbar_fuer,
        # Rüstung: Kästchen + Schadensreduktion (siehe kampf/ruestung.py).
        # Aktuell bleibt hier ausdrücklich None, wenn nicht angegeben — das
        # Repository setzt es dann auf Max (frisches Stück = unbeschädigt).
        "ruestungKaestchenMax": body.ruestungKaestchenMax,
        "ruestungKaestchenAktuell": body.ruestungKaestchenAktuell,
        "ruestungReduktionBasis": body.ruestungReduktionBasis,
        "istReparaturmaterial": body.istReparaturmaterial,
        "reparaturKapazitaet": body.reparaturKapazitaet,
        # Ideenschmiede: Entwürfe sind noch nicht Teil der aktiven Kampagne
        "istEntwurf": body.istEntwurf,
    }


@router.post("", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def create_item(campaign_id: str, person_id: str, body: GegenstandCreate):
    owner = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if owner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    sichtbarkeit = body.sichtbarkeit
    sichtbar_fuer = body.sichtbarFuer
    if sichtbarkeit is None:
        sichtbarkeit, sichtbar_fuer = _default_sichtbarkeit(owner["personType"], person_id)

    # istVorlage wird hier immer False erzwungen (nicht body.istVorlage) — ein
    # Gegenstand mit Besitzer ist per Invariante nie eine Vorlage, siehe
    # schemas.py. Vorlagen entstehen ausschließlich über create_vorlage unten.
    item = await repository.create_gegenstand(
        campaign_id, person_id, _create_data(body, False, sichtbarkeit, sichtbar_fuer or [])
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    return item


@router.get("", response_model=list[GegenstandResponse])
async def list_items(campaign_id: str, person_id: str, viewer: Viewer = Depends(get_viewer)):
    items = await repository.list_gegenstaende(campaign_id, person_id)
    return filter_gegenstaende_for_viewer(items, viewer.role, viewer.person_id)


@campaign_router.post("", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def create_vorlage(campaign_id: str, body: GegenstandCreate):
    """Legt einen besitzerlosen Gegenstand an — per Invariante immer eine
    Vorlage (siehe schemas.py). Für Gegenstände mit Besitzer siehe create_item."""
    sichtbarkeit = body.sichtbarkeit or "GM"
    sichtbar_fuer = body.sichtbarFuer or []
    item = await repository.create_gegenstand(campaign_id, None, _create_data(body, True, sichtbarkeit, sichtbar_fuer))
    if item is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Anlegen fehlgeschlagen")
    return item


@campaign_router.patch("/{item_id}", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def update_item(campaign_id: str, item_id: str, body: GegenstandUpdate):
    item = await repository.update_gegenstand(campaign_id, item_id, body.model_dump())
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    return item


@campaign_router.post("/{item_id}/bild", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def upload_bild(campaign_id: str, item_id: str, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Bilddateien (PNG/JPEG/WEBP/GIF) erlaubt")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 8 MB)")

    campaign_dir = UPLOAD_DIR / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    ext = mimetypes.guess_extension(file.content_type) or ""
    filename = f"{uuid.uuid4()}{ext}"
    (campaign_dir / filename).write_bytes(contents)

    item = await repository.set_bild_url(campaign_id, item_id, f"/uploads/{campaign_id}/{filename}")
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    return item


@campaign_router.post("/{item_id}/zuweisen", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def zuweisen(campaign_id: str, item_id: str, body: ZuweisenRequest):
    source = await repository.get_gegenstand(campaign_id, item_id)
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    if not source["istVorlage"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Vorlagen können zugewiesen werden")

    ziel = await get_node("Person", PERSON_FIELDS, campaign_id, body.zielPersonId)
    if ziel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zielperson nicht gefunden")

    sichtbarkeit, sichtbar_fuer = _default_sichtbarkeit(ziel["personType"], body.zielPersonId)

    if source["einzigartig"] or source["zeigeInGraph"]:
        # Einzigartige/MacGuffin-Vorlagen dürfen nicht vervielfältigt werden —
        # hier wird der Gegenstand selbst übergeben (verschoben), keine Kopie.
        result = await repository.assign_owner(campaign_id, item_id, body.zielPersonId, sichtbarkeit, sichtbar_fuer)
    else:
        result = await repository.assign_copy(campaign_id, source, body.zielPersonId, sichtbarkeit, sichtbar_fuer)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zuweisen fehlgeschlagen")
    return result


@campaign_router.post("/{item_id}/besitzer", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def besitzer_wechseln(campaign_id: str, item_id: str, body: ZuweisenRequest):
    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    ziel = await get_node("Person", PERSON_FIELDS, campaign_id, body.zielPersonId)
    if ziel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zielperson nicht gefunden")

    alter_besitzer = await repository.get_owner_id(campaign_id, item_id)
    updates: dict = {}
    if item["sichtbarkeit"] == "SPEZIFISCH" and item["sichtbarFuer"] == [alter_besitzer]:
        # Sichtbarkeit war exklusiv auf den alten Besitzer zugeschnitten (Standardfall
        # beim Anlegen) — für den neuen Besitzer frisch berechnen. War die Sichtbarkeit
        # bewusst breiter gewählt (ALLE, GM oder mehrere Spieler), bleibt sie unangetastet.
        sichtbarkeit, sichtbar_fuer = _default_sichtbarkeit(ziel["personType"], body.zielPersonId)
        updates = {"sichtbarkeit": sichtbarkeit, "sichtbarFuer": sichtbar_fuer}

    moved = await repository.transfer_owner(campaign_id, item_id, body.zielPersonId)
    if moved is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Übertragung fehlgeschlagen")
    if updates:
        moved = await repository.update_gegenstand(campaign_id, item_id, updates)
    return moved


@campaign_router.post("/{item_id}/vorlage", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def vorlage_machen(campaign_id: str, item_id: str):
    """Entfernt den Besitzer eines Gegenstands — er wird zur besitzerlosen
    Vorlage (Gegenstück zu Besitzer wechseln, siehe schemas.py-Invariante)."""
    moved = await repository.remove_owner(campaign_id, item_id)
    if moved is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden oder hat schon keinen Besitzer")
    return moved


@campaign_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_item(campaign_id: str, item_id: str):
    if not await repository.delete_gegenstand(campaign_id, item_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")


@campaign_router.get("/weggeworfen", response_model=list[GegenstandMitBesitzer], dependencies=[Depends(require_campaign_gm)])
async def liste_weggeworfen(campaign_id: str):
    """Der Mülleimer — **nur für die Spielleitung.**

    Muss vor `/{item_id}` stehen: sonst fängt die dortige Route den Pfad ab
    und "weggeworfen" sähe wie eine Kennung aus (derselbe Grund wie beim
    eigenen chrom_router weiter unten).

    Bewusst nicht für Spieler: dass ein Stück noch existiert und
    zurückgeholt werden könnte, ist eine Auskunft der Spielleitung.
    """
    return await repository.list_weggeworfene(campaign_id)


@campaign_router.post("/{item_id}/wegwerfen", response_model=GegenstandResponse)
async def item_wegwerfen(
    campaign_id: str,
    item_id: str,
    viewer: Viewer = Depends(get_viewer),
):
    """Wirft einen Gegenstand weg — er landet im Mülleimer der Spielleitung.

    **Zweite Schreibroute, die auch Spieler nutzen dürfen** (neben dem
    Umlegen), und genauso streng begrenzt: nur am eigenen Besitz, und sie
    löscht nichts. Steht deshalb namentlich in der Ausnahmeliste von
    tests/test_zugriffsschutz.py und prüft die Besitzverhältnisse selbst.

    Endgültig gelöscht wird nur von der Spielleitung, aus dem Mülleimer
    heraus (DELETE .../{item_id}).
    """
    if viewer.role != "GM":
        besitzer = await repository.get_owner_person_id(campaign_id, item_id)
        if besitzer is None or besitzer != viewer.person_id:
            # 404 statt 403, wie beim Umlegen: ein Spieler soll nicht
            # erfahren, ob es den Gegenstand überhaupt gibt.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    # Wer es weggeworfen hat, damit im Mülleimer steht, woher das Stück kommt.
    # Der Viewer kennt nur die Person-ID, deshalb der Namensschlag.
    von = "Spielleitung"
    if viewer.role != "GM" and viewer.person_id:
        person = await get_node("Person", PERSON_FIELDS, campaign_id, viewer.person_id)
        von = person["name"] if person else ""
    item = await repository.wegwerfen(campaign_id, item_id, von)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden oder schon weggeworfen")
    return item


@campaign_router.post("/{item_id}/zurueckholen", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def item_zurueckholen(campaign_id: str, item_id: str):
    """Holt einen Gegenstand aus dem Mülleimer zurück ins Spiel.

    Er kommt als *gelagert ohne Ziel* zurück, nicht an den Körper seines
    alten Besitzers — wohin er tatsächlich gehört, entscheidet die
    Spielleitung danach durch Umlegen.
    """
    item = await repository.zurueckholen(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden oder nicht weggeworfen")
    return item


@campaign_router.get("/{item_id}/ablageziele", response_model=list[AblageZiel])
async def ablageziele(campaign_id: str, item_id: str, viewer: Viewer = Depends(get_viewer)):
    """Wohin dieser Gegenstand gelegt werden kann: Orte der Kampagne und
    Behälter seines Besitzers (Fahrzeuge etc.)."""
    besitzer = await repository.get_owner_person_id(campaign_id, item_id)
    if besitzer is None:
        # Vorlagen haben keinen Besitzer und damit auch keine eigenen Behälter
        return await repository.moegliche_ablageziele(campaign_id, "")
    return await repository.moegliche_ablageziele(campaign_id, besitzer)


@campaign_router.post("/{item_id}/ablage", response_model=GegenstandResponse)
async def ablage_aendern(
    campaign_id: str,
    item_id: str,
    body: AblageRequest,
    viewer: Viewer = Depends(get_viewer),
):
    """Legt einen Gegenstand um — ausgerüstet, im Rucksack oder gelagert.

    **Die einzige Route, die auch Spieler schreiben dürfen**, und zwar streng
    begrenzt: nur an Gegenständen, die ihrem eigenen Charakter gehören, und
    nur dieses eine Feld. Alles andere bleibt der Spielleitung vorbehalten.
    Deshalb hängt sie an get_viewer statt an require_campaign_gm und prüft
    die Besitzverhältnisse selbst — sie steht dafür namentlich in der
    Ausnahmeliste von tests/test_zugriffsschutz.py.
    """
    if viewer.role != "GM":
        besitzer = await repository.get_owner_person_id(campaign_id, item_id)
        if besitzer is None or besitzer != viewer.person_id:
            # 404 statt 403: ein Spieler soll nicht erfahren, ob es den
            # Gegenstand überhaupt gibt.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    # Verbautes Chrom lässt sich nicht umlegen — es sitzt im Körper, nicht im
    # Rucksack. Mark: "das sind keine Gegenstände die er nach dem sie Mal
    # eigebaut wurden wieder ablegen kann". Der Weg heraus führt über
    # .../chirurgie, nicht über die Ablage.
    aktuelles = await repository.get_gegenstand(campaign_id, item_id)
    if aktuelles and not chirurgie.kann_ablegen(aktuelles):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Verbautes Implantat lässt sich nicht ablegen — es muss chirurgisch entfernt werden",
        )

    # Zerschossene Rüstung lässt sich nicht wieder anlegen: mit 0 Kästchen
    # trägt sie nichts zum Pool bei und schützt auch nicht (siehe
    # docs/api/ruestung.md). Ohne diese Prüfung könnte man sie endlos wieder
    # anziehen und würde rätseln, warum der Rüstungsbalken nicht steigt.
    if (
        body.ablage == "AUSGERUESTET"
        and aktuelles
        and aktuelles["typ"] == "Rüstung"
        and aktuelles["ruestungKaestchenMax"] > 0
        and aktuelles["ruestungKaestchenAktuell"] <= 0
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Zerschossene Rüstung schützt nicht — sie muss erst repariert werden",
        )

    # Slot-Kollision nur prüfen, wenn ausgerüstet wird UND das Stück
    # überhaupt einen festen Platz hat (Chrom-/Bio-/Hexware mit Zone+Slot).
    # Alles andere (Waffen, Kleidung, ...) hat keine Zone und blockiert nichts.
    if body.ablage == "AUSGERUESTET":
        vorhandenes_item = await repository.get_gegenstand(campaign_id, item_id)
        if vorhandenes_item and vorhandenes_item.get("koerperzone") and vorhandenes_item.get("slot"):
            besitzer_id = await repository.get_owner_person_id(campaign_id, item_id)
            if besitzer_id:
                blockiert_von = await repository.slot_konflikt(
                    campaign_id, besitzer_id, vorhandenes_item["koerperzone"], vorhandenes_item["slot"], item_id
                )
                if blockiert_von:
                    raise HTTPException(
                        status.HTTP_409_CONFLICT,
                        f"Platz {vorhandenes_item['slot']} in {vorhandenes_item['koerperzone']} ist bereits von \"{blockiert_von}\" belegt",
                    )

    item = await repository.set_ablage(campaign_id, item_id, body.ablage, body.zielId)
    if item is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ablage konnte nicht gesetzt werden")
    return item


@campaign_router.get("/traglast")
async def traglast(campaign_id: str, viewer: Viewer = Depends(get_viewer)) -> list[dict]:
    """Wer wie viel schleppt — für die Anzeige und den Überblick der Spielleitung.

    Rein informativ: nichts wird dadurch verhindert. Wer über seiner Grenze
    liegt, taucht in der Übersicht auf, die Konsequenzen zieht die
    Spielleitung.
    """
    einstellungen = await get_einstellungen(campaign_id)
    zeilen = await repository.traglast_uebersicht(
        campaign_id,
        str(einstellungen.get("traglastAttribut") or "Körperkraft"),
        float(einstellungen.get("traglastProPunkt") or 10.0),
    )
    if viewer.role == "GM":
        return zeilen
    # Spieler sehen nur sich selbst und die eigenen Behälter; wie schwer ein
    # fremdes Fahrzeug beladen ist, geht sie nichts an.
    eigene = {i["id"] for i in await repository.list_gegenstaende(campaign_id, viewer.person_id or "")}
    return [z for z in zeilen if z["id"] == viewer.person_id or z["id"] in eigene]



# Eigener Router statt einer Route am Gegenstands-Prefix: dort läge der Pfad
# unter /gegenstaende/chromstufen und würde von /gegenstaende/{item_id}
# abgefangen — "chromstufen" sähe wie eine Kennung aus.
chrom_router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/chromstufen",
    tags=["items"],
    dependencies=[Depends(require_campaign_zugang)],
)


@chrom_router.get("")
async def chromstufen(campaign_id: str, bonus: int = 1) -> dict:
    """Preis und Willenskraftverlust je Qualitätsstufe.

    Damit die Oberfläche die Wahl zeigen kann, ohne die Formel nachzubauen —
    sonst driften Anzeige und Abrechnung auseinander, sobald jemand an den
    Zahlen dreht. Lesbar für alle mit Zugang; das sind Preise, kein Geheimnis.
    """
    return {"stufen": stufen_uebersicht(max(0, bonus)), "koerperzonen": KOERPERZONEN}


class ChirurgieRequest(BaseModel):
    """Einsetzen oder entfernen."""

    einsetzen: bool


@campaign_router.post(
    "/{item_id}/chirurgie",
    response_model=GegenstandResponse,
)
async def chirurgie_durchfuehren(
    campaign_id: str,
    item_id: str,
    body: ChirurgieRequest,
    viewer: Viewer = Depends(get_viewer),
):
    """Implantat einsetzen oder chirurgisch entfernen.

    **Einsetzen:** Spieler dürfen ihre eigenen Augments selbst einsetzen
    (mit Bestätigungsdialog im Frontend: "bist du sicher? das sollte lieber
    ein Experte für dich machen"). Die SL kann es auch für sie tun.

    **Entfernen:** Nur die Spielleitung. Mark: *"wenn die verbaut ist kann
    der Spieler die nicht mehr entfernen außer bei speziellen Events (er
    besucht einen Arzt oder ein Spieler hat die Medizin skills um das zu
    tun...)"* — das Entfernen ist ein Ereignis in der Welt, keine
    Menüaktion. Spieler beantragen es über `.../entfernung-beantragen`.
    """
    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    # Spieler dürfen NUR einsetzen — entfernen bleibt der SL vorbehalten.
    if viewer.role != "GM":
        if not body.einsetzen:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Nur die Spielleitung darf Augments entfernen",
            )
        # Und auch nur ihre eigenen Gegenstände.
        besitzer = await repository.get_owner_person_id(campaign_id, item_id)
        if besitzer != viewer.person_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Das gehört dir nicht")

    if body.einsetzen and not chirurgie.kann_einsetzen(item):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Nur Cyber-, Bio- oder Hexware kann eingesetzt werden — und nur einmal",
        )
    
    # Weg-Prüfung: Magier können keine Bioware, Neuroweaver keine Hexware.
    if body.einsetzen:
        besitzer_id = await repository.get_owner_person_id(campaign_id, item_id)
        if besitzer_id:
            person = await get_node(campaign_id, besitzer_id)
            weg = person.get("weg", "KEINER") if person else "KEINER"
            typ = item.get("typ", "")
            if weg == "MAGIER" and typ == "Bioware":
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "Magier können keine Bioware einsetzen — ihr Weg ist die Magie, nicht NeuroWeaving",
                )
            if weg == "NEUROWEAVER" and typ == "Hexware":
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "Neuroweaver können keine Hexware einsetzen — ihr Weg ist NeuroWeaving, nicht Magie",
                )
    
    if not body.einsetzen and not chirurgie.kann_entfernen(item):
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Stück ist nicht verbaut")

    # Beim Einsetzen den Platz prüfen: zwei Implantate können nicht denselben
    # Körperplatz belegen (Regelblatt: je Zone drei Plätze).
    if body.einsetzen and item.get("koerperzone") and item.get("slot"):
        besitzer_id = await repository.get_owner_person_id(campaign_id, item_id)
        if besitzer_id:
            blockiert_von = await repository.slot_konflikt(
                campaign_id, besitzer_id, item["koerperzone"], item["slot"], item_id
            )
            if blockiert_von:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"Platz {item['slot']} in {item['koerperzone']} ist bereits von \"{blockiert_von}\" belegt",
                )

    ergebnis = await repository.setze_verbaut(campaign_id, item_id, body.einsetzen)
    if ergebnis is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Operation fehlgeschlagen")
    return ergebnis


@campaign_router.post("/{item_id}/entfernung-beantragen", response_model=GegenstandResponse)
async def entfernung_beantragen(
    campaign_id: str,
    item_id: str,
    viewer: Viewer = Depends(get_viewer),
):
    """Ein Spieler bittet darum, ein Implantat entfernen zu lassen.

    Setzt nur ein Kennzeichen; die Spielleitung entscheidet und operiert.
    Deshalb ohne `require_campaign_gm` — mit eigener Besitzprüfung, wie bei
    der Ablage-Route.
    """
    besitzer = await repository.get_owner_person_id(campaign_id, item_id)
    if viewer.role != "GM":
        if besitzer is None or besitzer != viewer.person_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None or not chirurgie.kann_entfernen(item):
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Stück ist nicht verbaut")

    ergebnis = await repository.setze_entfernung_beantragt(campaign_id, item_id, True)
    if ergebnis is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Antrag fehlgeschlagen")
    return ergebnis


@campaign_router.get("/verbaut/{person_id}", response_model=list[GegenstandResponse])
async def verbautes_chrom(campaign_id: str, person_id: str, viewer: Viewer = Depends(get_viewer)):
    """Was bei dieser Person im Körper sitzt — für die Übersicht im Regelmenü.

    Mark: *"Wir wollten ja auch noch dieses Menü machen das anzeigt wo was
    verbaut ist"*. Nach Körperzone und Platz sortiert.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    return await repository.verbautes_chrom(campaign_id, person_id)


# =====================================================================
# Rüstung: Kästchen + Schadensreduktion (siehe kampf/ruestung.py für die
# Formel, docs/api/ruestung.md für die ausführliche Begründung)
#
# Der Treffer selbst sitzt bewusst NICHT hier, sondern bei der Person
# (traits/routes.py: .../personen/{person_id}/ruestung/treffer) — getroffen
# wird eine Person, und ihre Rüstung wirkt als ein Pool: welche Teile der
# Kästchenschaden aufbraucht, ist eine Regelfrage (`ruestung.reihenfolge`)
# und keine Angabe des Aufrufers. Reparieren dagegen betrifft immer ein
# bestimmtes Stück und bleibt deshalb hier am Gegenstand.
# =====================================================================


class RuestungReparierenRequest(BaseModel):
    """Wie viele Kästchen die Reparatur wiederherstellt.

    Nimmt das Ergebnis direkt entgegen, ohne Probe oder Material — der
    manuelle Weg für Sonderfälle (Questbelohnung, Improvisation am Tisch).
    Der reguläre Weg mit Hardware-Probe und Material ist
    `.../ruestung/reparieren-selbst`, der Händlerweg mit Preisverhandlung
    läuft über `.../ruestung/reparatur-preis` + `POST /verhandlungen`.
    """

    kaestchen: int = Field(ge=0)


class RuestungReparierenSelbstRequest(BaseModel):
    """Selbst-Reparieren: Hardware-Skill-Probe + Material, kein Geld.

    Marks Vorgabe (siehe kampf/ruestung.py für die Herleitung): Schwelle =
    halbes Kästchen-Max, abgerundet; Erfolgsüberschuss darüber wird zu
    reparierten Kästchen, gedeckelt durch die Kapazität des eingesetzten
    Materials. Verbraucht **immer** 1 Stück Material, auch bei Fehlschlag.
    """

    materialGegenstandId: str


class ReparaturWurf(BaseModel):
    """Wurfergebnis + Auswertung der Selbst-Reparatur, fürs Popup."""

    augen: list[int]
    erfolge: int
    patzer: bool
    pool: int
    schwelle: int
    ueberschuss: int
    repariert: int
    materialKapazitaet: int
    materialName: str
    materialRestmenge: int
    gegenstand: GegenstandResponse


class ReparaturPreisAntwort(BaseModel):
    """Reine Berechnung für den Händlerpreis — kein Seiteneffekt.

    `fehlendeKaestchen` bezieht sich standardmässig auf ALLE fehlenden
    Kästchen dieses Gegenstands (kaestchenMax - kaestchenAktuell); über den
    Query-Parameter lässt sich auch der Preis einer Teil-Reparatur ansehen.
    """

    fehlendeKaestchen: int
    kaestchenMax: int
    neuwert: int
    preis: int
    deckel: int


@campaign_router.post(
    "/{item_id}/ruestung/reparieren-selbst",
    response_model=ReparaturWurf,
    dependencies=[Depends(require_campaign_gm)],
)
async def ruestung_reparieren_selbst(campaign_id: str, item_id: str, body: RuestungReparierenSelbstRequest):
    """Selbst-Reparieren: würfelt die Hardware-Probe, verbraucht Material,
    repariert Kästchen. **Nur SL** ausgelöst, wie die Kampf-Würfe der NPCs —
    ein Spieler würfelt physisch, hier würfelt der Server stellvertretend für
    die klare Materialbuchhaltung (ein Spielerwurf könnte den Materialabzug
    umgehen, wenn der Client die Anfrage einfach nicht schickt).
    """
    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    if item["typ"] != "Rüstung" or item["ruestungKaestchenMax"] <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Nur Rüstung mit Kästchen-System kann repariert werden")

    besitzer_id = await repository.get_owner_person_id(campaign_id, item_id)
    if besitzer_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Gegenstand ohne Besitzer kann nicht repariert werden")

    material = await repository.get_gegenstand(campaign_id, body.materialGegenstandId)
    if material is None or not material.get("istReparaturmaterial"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Reparaturmaterial")
    if material.get("menge", 1) <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Material ist aufgebraucht")

    werte = {r["name"]: r["rating"] for r in await get_ratings_for_entity(campaign_id, besitzer_id)}
    pool = hardware_probe_pool(werte)
    wurf = wuerfle(pool)
    ergebnis = selbstreparatur_ergebnis(
        wurf["erfolge"], item["ruestungKaestchenMax"], material["reparaturKapazitaet"]
    )

    # Material verbrauchen — IMMER, auch bei 0 reparierten Kästchen (Marks
    # ausdrückliche Vorgabe: realistisches Risiko).
    material_neue_menge = max(0, material["menge"] - 1)
    await repository.update_gegenstand(campaign_id, body.materialGegenstandId, {"menge": material_neue_menge})

    reparatur = repariere(item["ruestungKaestchenAktuell"], item["ruestungKaestchenMax"], ergebnis["repariert"])
    aktualisiert = await repository.update_gegenstand(
        campaign_id, item_id, {"ruestungKaestchenAktuell": reparatur["kaestchenNeu"]}
    )
    if aktualisiert is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reparatur fehlgeschlagen")

    return ReparaturWurf(
        augen=wurf["augen"],
        erfolge=wurf["erfolge"],
        patzer=wurf["patzer"],
        pool=pool,
        schwelle=ergebnis["schwelle"],
        ueberschuss=ergebnis["ueberschuss"],
        repariert=ergebnis["repariert"],
        materialKapazitaet=material["reparaturKapazitaet"],
        materialName=material["name"],
        materialRestmenge=material_neue_menge,
        gegenstand=aktualisiert,
    )


@campaign_router.get("/{item_id}/ruestung/reparatur-preis", response_model=ReparaturPreisAntwort)
async def ruestung_reparatur_preis(
    campaign_id: str, item_id: str, fehlendeKaestchen: int | None = None, viewer: Viewer = Depends(get_viewer)
):
    """Reiner Berechnungs-Endpunkt für den Händlerpreis, kein Seiteneffekt —
    Grundlage für den SL-Vorschlag im Verhandlungs-Popup (siehe
    docs/api/ruestung.md, "Reparatur beim Händler" für die Formelherleitung).
    """
    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    if item["typ"] != "Rüstung" or item["ruestungKaestchenMax"] <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Nur Rüstung mit Kästchen-System kann repariert werden")

    max_fehlend = item["ruestungKaestchenMax"] - item["ruestungKaestchenAktuell"]
    n = max_fehlend if fehlendeKaestchen is None else max(0, min(fehlendeKaestchen, max_fehlend))
    preis = haendler_reparatur_preis(n, item["ruestungKaestchenMax"], item["preis"])
    deckel = haendler_reparatur_preis(item["ruestungKaestchenMax"], item["ruestungKaestchenMax"], item["preis"])
    return ReparaturPreisAntwort(
        fehlendeKaestchen=n,
        kaestchenMax=item["ruestungKaestchenMax"],
        neuwert=item["preis"],
        preis=preis,
        deckel=deckel,
    )


@campaign_router.get("/{item_id}/reparaturmaterial", response_model=list[GegenstandResponse])
async def reparaturmaterial_liste(campaign_id: str, item_id: str, viewer: Viewer = Depends(get_viewer)):
    """Welches Reparaturmaterial der Besitzer dieser Rüstung zur Auswahl hat
    (für das Selbst-Reparieren-Popup)."""
    besitzer_id = await repository.get_owner_person_id(campaign_id, item_id)
    if besitzer_id is None:
        return []
    return await repository.list_reparaturmaterial_von(campaign_id, besitzer_id)


@campaign_router.post(
    "/{item_id}/ruestung/reparieren", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)]
)
async def ruestung_reparieren(campaign_id: str, item_id: str, body: RuestungReparierenRequest):
    """Kästchen manuell auffüllen, ohne Probe oder Material — der SL trägt das
    Ergebnis von Hand ein (Sonderfälle: Questbelohnung, Improvisation am
    Tisch). Die Schadensreduktion braucht seit dem Umbau vom 18.09.2026 keine
    eigene Reparatur mehr, sie folgt automatisch aus dem wiederhergestellten
    Kästchen-Verhältnis. **Nur SL** — wie jede Vergabe von Ressourcen ohne
    Gegenprobe im Tool (vgl. Erfahrung vergeben).
    """
    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    if item["typ"] != "Rüstung" or item["ruestungKaestchenMax"] <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Nur Rüstung mit Kästchen-System kann repariert werden")

    ergebnis = repariere(
        item["ruestungKaestchenAktuell"],
        item["ruestungKaestchenMax"],
        body.kaestchen,
    )
    aktualisiert = await repository.update_gegenstand(
        campaign_id,
        item_id,
        {"ruestungKaestchenAktuell": ergebnis["kaestchenNeu"]},
    )
    if aktualisiert is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reparatur fehlgeschlagen")
    return aktualisiert
