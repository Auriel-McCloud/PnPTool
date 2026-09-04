import mimetypes
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_einstellungen
from app.entities.repository import PERSON_FIELDS, get_node
from app.entities.visibility import filter_gegenstaende_for_viewer
from app.items import repository
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
        "traitBoni": body.traitBoni,
        "ausruestungsfertigkeiten": body.ausruestungsfertigkeiten,
        "riggerBonus": body.riggerBonus,
        "maxDrohnen": body.maxDrohnen,
        "immerSichtbar": body.immerSichtbar,
        "deckBruteForce": body.deckBruteForce,
        "deckSchleichen": body.deckSchleichen,
        "deckDaten": body.deckDaten,
        "deckKompilieren": body.deckKompilieren,
        "stufe": body.stufe,
        "widerstand": body.widerstand,
        "angriff": body.angriff,
        "agilitaet": body.agilitaet,
        "fahrzeugFertigkeiten": body.fahrzeugFertigkeiten,
        # Reflex-Booster & Co. (Regelblatt Zeile 57, 421-444).
        "initiativeBonus": body.initiativeBonus,
        "sichtbarkeit": sichtbarkeit,
        "sichtbarFuer": sichtbar_fuer,
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

    # Slot-Kollision nur prüfen, wenn ausgerüstet wird UND das Stück
    # überhaupt einen festen Platz hat (Chrom-/Bio-/MagWare mit Zone+Slot).
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
