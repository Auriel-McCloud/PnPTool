import mimetypes
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_einstellungen
from app.entities.repository import PERSON_FIELDS, drohne_rigger, get_node
from app.ereignisprotokoll import hooks
from app.entities.visibility import filter_gegenstaende_for_viewer
from app.items import chirurgie, repository
from app.items.schloss import (
    anzeige_fuer,
    besitzt_erreichbaren_schluessel,
    ids_in_verschlossenem,
    inhalt_mitnehmen,
    ist_verschlossen,
    neue_folge,
    passwort_passt,
    schloss_patch_anpassen,
    spiel_lesen,
    spiel_schreiben,
    zug_passt,
)
from app.items.augments import augment_level, benoetigte_erfolge_montage, waffentyp_passt, zieltyp_passt
from app.items.augments import AUGMENT_TRAEGER_TYPEN, wende_augment_boni_an
from app.items.chrom import KOERPERZONEN, stufen_uebersicht
from app.items.waffenbonus import kampf_fertigkeit_lesen, schaden_art_fuer_waffe
from app.traits import erstellung
from app.items.schemas import (
    AblageRequest,
    AblageZiel,
    GegenstandCreate,
    GegenstandMitBesitzer,
    GegenstandResponse,
    GegenstandUpdate,
    ZusammenlegenRequest,
    ZuweisenRequest,
)
from app.kampf.ruestung import (
    REPARATUR_SKILLS,
    haendler_reparatur_preis,
    reparatur_benoetigte_erfolge,
    reparatur_heilung_material,
    repariere,
)
from app.traits.repository import get_ratings_for_entity, list_catalog
from app.campaigns.repository import get_campaign

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


async def _sichtbar_fuer(campaign_id: str, items: list[dict], viewer: Viewer) -> list[dict]:
    """Sichtbarkeit plus: Inhalt einer noch zuen Kiste sieht nur die SL."""
    sichtbar = filter_gegenstaende_for_viewer(items, viewer.role, viewer.person_id)
    if viewer.role == "GM":
        return sichtbar
    verborgen = await ids_in_verschlossenem(campaign_id)
    return [i for i in sichtbar if i.get("id") not in verborgen]


def speichere_bild_bytes(campaign_id: str, inhalt: bytes, content_type: str) -> str:
    """Legt Bild-Bytes wie ein Upload ab und gibt die öffentliche URL zurück."""
    if content_type not in ALLOWED_IMAGE_TYPES:
        content_type = "image/png"
    if len(inhalt) > MAX_UPLOAD_BYTES:
        raise ValueError("Bild zu groß (max. 8 MB)")
    campaign_dir = UPLOAD_DIR / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    ext = mimetypes.guess_extension(content_type) or ".png"
    if ext == ".jpe":
        ext = ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    (campaign_dir / filename).write_bytes(inhalt)
    return f"/uploads/{campaign_id}/{filename}"


@campaign_router.get("", response_model=list[GegenstandMitBesitzer])
async def list_all_items(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    items = await repository.list_alle_gegenstaende(campaign_id)
    items = await _mit_augment_boni(campaign_id, items)
    sichtbar = await _sichtbar_fuer(campaign_id, items, viewer)
    # Ideenschmiede-Entwürfe gehören nicht in die normale Übersicht, genau wie
    # bei Person/Ort/Event/Fraktion/WikiSeite (siehe entities/routes.py::
    # _aufbereiten, wiki/routes.py::seitenbaum). Einzelabruf (get_item) filtert
    # das bewusst NICHT — die Ideenschmiede lädt Entwürfe darüber fürs Detail-Popup.
    return [i for i in sichtbar if not i.get("istEntwurf", False)]


async def _mit_augment_boni(campaign_id: str, items: list[dict]) -> list[dict]:
    """Legt die Effekte montierter, nicht defekter Augments (Waffenschaden/
    -art, Rüstungs-Absorption/Kästchen, Initiative/Zusatzaktionen) auf die
    betroffenen Items, BEVOR sie den Client erreichen (29.10.2026
    Nachbesserung, siehe items/augments.py::wende_augment_boni_an).

    Reine Anzeige-/Kampfwerte — nie zurückgeschrieben, deshalb hier und nicht
    in `items/repository.py::_decode` (das würde ein Vorlagen-Kopieren sonst
    unbeabsichtigt mit dem Bonus einfrieren). Nur Waffe/Rüstung/Cyberdeck/
    Riggerkonsole können überhaupt Augment-Ziel sein (`AUGMENT_TRAEGER_TYPEN`).
    """
    ziel_ids = [i["id"] for i in items if (i.get("typ") or "") in AUGMENT_TRAEGER_TYPEN]
    if not ziel_ids:
        return items
    boni = await repository.augment_boni_fuer_ziele(campaign_id, ziel_ids)
    if not boni:
        return items
    return [wende_augment_boni_an(i, boni[i["id"]]) if i["id"] in boni else i for i in items]


async def _default_sichtbarkeit(campaign_id: str, ziel: dict, ziel_id: str) -> tuple[str, list[str]]:
    """Standard beim Anlegen/Übergeben: für alle sichtbar (28.10.2026, Mark:
    "ich muss nur Dinge umstellen, die geheim sind — sonst ist immer alles
    geheim und niemand sieht es"). Bis dahin: PC-Besitzer -> nur für ihn
    sichtbar, alles andere -> SL-geheim (siehe Git-Historie für die alte
    Fassung samt Drohnen/Rigger-Sonderfall vom selben Tag, jetzt hinfällig,
    weil nichts mehr automatisch geheim startet). Der SL kann das beim
    Anlegen/Zuweisen jederzeit explizit auf GM oder SPEZIFISCH übersteuern.
    """
    return "ALLE", []
async def _eigener_kreis(campaign_id: str, viewer_person_id: str, person_id: str | None) -> bool:
    """Ist `person_id` der Spieler selbst ODER seine eigene gebundene
    Drohne/sein eigenes Fahrzeug? (26.10.2026, gemeinsamer Besitz-Check für
    `ablage_aendern` und `besitzer_wechseln` — der Rigger ist nicht
    identisch mit seiner Drohne, aber darf trotzdem an ihrer Ausrüstung
    schrauben. Gegenprobe gegen fremde Personen/Drohnen: True nur, wenn der
    gebundene Rigger der Drohne exakt `viewer_person_id` ist.)"""
    if person_id is None:
        return False
    if person_id == viewer_person_id:
        return True
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person and (person.get("istDrohne") or person.get("istFahrzeug")):
        return await drohne_rigger(campaign_id, person_id) == viewer_person_id
    return False


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
        "storyRelevant": body.storyRelevant,
        "einzigartig": body.einzigartig,
        "hatMenge": body.hatMenge,
        "menge": body.menge,
        "istVorlage": ist_vorlage,
        "seltenheit": body.seltenheit,
        "automatischImShop": body.automatischImShop,
        "ablage": ablage,
        "gewicht": body.gewicht,
        "kapazitaet": body.kapazitaet,
        "schlossArt": body.schlossArt,
        "schlossPasswort": body.schlossPasswort,
        "schlossRaetsel": body.schlossRaetsel,
        "schluesselId": body.schluesselId,
        "aufgeschlossen": body.aufgeschlossen,
        "spielLaenge": body.spielLaenge,
        # Cyber-/Bioware und Sonderwirkungen. Diese Liste war unvollständig:
        # Felder, die hier fehlen, gehen beim Anlegen still verloren — sie
        # lassen sich danach nur per PATCH nachtragen. Beim Ergänzen eines
        # neuen Feldes im Schema also IMMER auch hier eintragen.
        "wVerlust": body.wVerlust,
        "koerperzone": body.koerperzone,
        "slot": body.slot,
        "istWaffe": body.istWaffe,
        "istNeurolink": body.istNeurolink if body.typ == "Cyberware" else False,
        "schaden": body.schaden,
        "schadenArt": (
            schaden_art_fuer_waffe(body.schadenArt)
            if body.typ == "Waffe" or body.istWaffe
            else (body.schadenArt or "")
        ),
        "kampfFertigkeit": (
            kampf_fertigkeit_lesen(body.kampfFertigkeit)
            if body.typ == "Waffe" or body.istWaffe
            else ""
        ),
        "traitBoni": body.traitBoni,
        "ausruestungsfertigkeiten": body.ausruestungsfertigkeiten,
        "kiTamaFertigkeiten": body.kiTamaFertigkeiten,
        "attackenFertigkeiten": body.attackenFertigkeiten,
        "attackenSchadensart": body.attackenSchadensart,
        "beschworenerCritterId": body.beschworenerCritterId,
        "beschwoerungsSchwierigkeit": body.beschwoerungsSchwierigkeit,
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
        # Natürliche Rüstung (11.10.2026 Verfeinerung, Rassen-/Kreaturfeature
        # wie Dug'Rah): siehe docs/api/ruestung.md, Abschnitt "Natürliche
        # Rüstung" — nicht ablegbar für Spieler, nicht reparierbar, Kästchen-
        # Max wird live aus der Widerstandsfähigkeit der Trägerin berechnet.
        "istNatuerlich": body.istNatuerlich,
        # Maschinenteil (26.10.2026): Material statt Nuyen beim Drohnen-/
        # Fahrzeug-Umbau, siehe traits/drohnen.py::maschinenteil_reicht.
        "istMaschinenteil": body.istMaschinenteil,
        "maschinenteilQualitaet": body.maschinenteilQualitaet,
        # Waffen-/Rüstungs-/Drohnen-Augments (29.10.2026). Typ "Upgrade-Material"
        # (29.10.2026 Nachbesserung) impliziert istAugment=true — sonst legt
        # die SL ein Stück mit sprechendem Typ an, vergisst aber die separate
        # Checkbox in den Optionen, und es taucht in der Werkbank nie auf
        # (Mark, 29.10.2026, dritter Klicktest: "er hat ein UpgradeMaterial...
        # aber dort wird nichts angezeigt"). "Ki-Tama" (30.10.2026, eigene
        # Kategorie fürs FF7-Materia-Konzept, umbenannt da "Ki" = KI-Kristall
        # + jap. "Tama" = Perle) folgt exakt derselben Regel — funktioniert
        # dadurch 1:1 wie Upgrade-Material, montierbar auf Waffe/Rüstung/
        # Cyberdeck/Riggerkonsole (items/augments.py::AUGMENT_TRAEGER_TYPEN).
        "upgradeSlots": body.upgradeSlots,
        "istAugment": True if body.typ in ("Upgrade-Material", "Ki-Tama") else body.istAugment,
        "augmentWaffentyp": body.augmentWaffentyp,
        "augmentZielTyp": body.augmentZielTyp,
        "defekt": body.defekt,
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
        sichtbarkeit, sichtbar_fuer = await _default_sichtbarkeit(campaign_id, owner, person_id)

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
    items = await _mit_augment_boni(campaign_id, items)
    sichtbar = await _sichtbar_fuer(campaign_id, items, viewer)
    # Siehe list_all_items: Entwürfe gehören in die Ideenschmiede, nicht hierhin.
    return [i for i in sichtbar if not i.get("istEntwurf", False)]


@campaign_router.post("", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def create_vorlage(campaign_id: str, body: GegenstandCreate):
    """Legt einen besitzerlosen Gegenstand an — per Invariante immer eine
    Vorlage (siehe schemas.py). Für Gegenstände mit Besitzer siehe create_item.
    Sichtbarkeit folgt demselben Standard wie dort (28.10.2026, siehe
    _default_sichtbarkeit): ohne explizite Angabe ALLE, nicht mehr GM — diese
    Stelle war bei der Umstellung übersehen worden (29.10.2026 Bugfix)."""
    sichtbarkeit = body.sichtbarkeit or "ALLE"
    sichtbar_fuer = body.sichtbarFuer or []
    item = await repository.create_gegenstand(campaign_id, None, _create_data(body, True, sichtbarkeit, sichtbar_fuer))
    if item is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Anlegen fehlgeschlagen")
    return item


@campaign_router.patch("/{item_id}", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def update_item(campaign_id: str, item_id: str, body: GegenstandUpdate):
    daten = body.model_dump()
    # Dieselbe Regel wie beim Anlegen (siehe _create_data): Typ "Upgrade-
    # Material" ODER "Ki-Tama" erzwingt istAugment=true, auch wenn nur der
    # Typ per "Typ ändern"-Popup nachträglich umgestellt wird.
    if body.typ in ("Upgrade-Material", "Ki-Tama"):
        daten["istAugment"] = True
    schloss_daten = {
        k: daten[k]
        for k in ("schlossArt", "schlossPasswort", "schlossRaetsel", "schluesselId", "aufgeschlossen", "spielLaenge")
        if daten.get(k) is not None
    }
    if schloss_daten:
        bisher = await repository.get_gegenstand(campaign_id, item_id)
        if bisher is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
        fehler = schloss_patch_anpassen(bisher, schloss_daten)
        if fehler:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, fehler)
        daten.update(schloss_daten)
        sid = schloss_daten.get("schluesselId", bisher.get("schluesselId") or "")
        art = schloss_daten.get("schlossArt", bisher.get("schlossArt") or "")
        if art == "schluessel" and sid:
            schluessel = await repository.get_gegenstand(campaign_id, sid)
            if schluessel is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Schlüssel nicht gefunden.")
    item = await repository.update_gegenstand(campaign_id, item_id, daten)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    if body.storyRelevant is not None or body.sichtbarkeit is not None:
        from app.lexikon import hooks as lexikon_hooks

        await lexikon_hooks.campaign_weit_neu_berechnen(campaign_id)
    return item


@campaign_router.post("/{item_id}/bild", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def upload_bild(campaign_id: str, item_id: str, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Bilddateien (PNG/JPEG/WEBP/GIF) erlaubt")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 8 MB)")

    url = speichere_bild_bytes(campaign_id, contents, file.content_type or "image/png")
    item = await repository.set_bild_url(campaign_id, item_id, url)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    return item


class VorlagenArtRequest(BaseModel):
    keineVorlage: bool


@campaign_router.post("/{item_id}/vorlagen-art", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def vorlagen_art(campaign_id: str, item_id: str, body: VorlagenArtRequest):
    """Einzigartige Kopie (Vorlage) oder das Stück selbst, keine Vorlage.

    Hat das Stück einen Besitzer, kann es nicht wieder zur kopierbaren
    Vorlage werden — dafür ist „Zur Vorlage machen“.
    """
    try:
        item = await repository.setze_vorlagen_art(campaign_id, item_id, body.keineVorlage)
    except repository.VorlageHatBesitzer as fehler:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Hat einen Besitzer — erst zur Vorlage machen, dann kopierbar",
        ) from fehler
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

    sichtbarkeit, sichtbar_fuer = await _default_sichtbarkeit(campaign_id, ziel, body.zielPersonId)

    # Default: einzigartige/MacGuffin-Vorlagen werden selbst übergeben, sonst
    # kopiert. `kopie=true` ist die ausdrückliche SL-Wahl im Besitz-Reiter —
    # dann bleibt die Vorlage stehen, auch wenn sie einzigartig ist.
    if body.kopie or not (source["einzigartig"] or source["storyRelevant"]):
        result = await repository.assign_copy(campaign_id, source, body.zielPersonId, sichtbarkeit, sichtbar_fuer)
    else:
        result = await repository.assign_owner(campaign_id, item_id, body.zielPersonId, sichtbarkeit, sichtbar_fuer)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zuweisen fehlgeschlagen")
    return result


@campaign_router.post("/{item_id}/besitzer", response_model=GegenstandResponse)
async def besitzer_wechseln(campaign_id: str, item_id: str, body: ZuweisenRequest, viewer: Viewer = Depends(get_viewer)):
    """Gegenstand an eine andere Person übergeben (kein Kopieren — für
    Vorlagen siehe `zuweisen`).

    **Drohne/Fahrzeug (26.10.2026, Mark: "es müsste die Möglichkeit geben,
    etwas aus dem Inventar des Riggers auszurüsten bzw. zu übergeben"):**
    zusätzlich zur Spielleitung auch für den Rigger selbst erlaubt, aber
    streng auf seinen EIGENEN Kreis begrenzt — Quelle UND Ziel müssen jeweils
    er selbst oder seine eigene gebundene Drohne/sein eigenes Fahrzeug sein
    (`_eigener_kreis`). Damit kann der Rigger eigene Ausrüstung an seine
    Drohne geben (und zurücknehmen), aber keine fremden Gegenstände oder
    Personen anfassen. Bewusst als SOFORTIGE Übertragung (kein Annehmen/
    Ablehnen-Angebot wie bei `verhandlung/routes.py`s Party-Weitergabe) —
    die Drohne trifft keine eigene Entscheidung, das Angebots-Muster ist nur
    für echte Spieler-zu-Spieler-Transaktionen gedacht.
    """
    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    if item.get("istNatuerlich"):
        # Teil des Körpers, siehe chirurgie.kann_ablegen — ownership-Wechsel
        # wäre hier noch einschneidender als bloßes Ablegen (26.10.2026:
        # jetzt auch für den Rigger erreichbar, also lieber einmal zu viel
        # abgesichert als die automatische Drohnen-Rüstung kaputtzuschieben).
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Natürliche Rüstung ist Teil des Körpers und kann nicht übertragen werden.",
        )

    ziel = await get_node("Person", PERSON_FIELDS, campaign_id, body.zielPersonId)
    if ziel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Zielperson nicht gefunden")

    alter_besitzer = await repository.get_owner_id(campaign_id, item_id)

    if viewer.role != "GM":
        quelle_ok = await _eigener_kreis(campaign_id, viewer.person_id, alter_besitzer)
        ziel_ok = await _eigener_kreis(campaign_id, viewer.person_id, body.zielPersonId)
        if not (quelle_ok and ziel_ok):
            # 404 statt 403: ein Spieler soll nicht erfahren, ob Gegenstand/
            # Zielperson überhaupt existieren.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    updates: dict = {}
    if item["sichtbarkeit"] == "SPEZIFISCH" and item["sichtbarFuer"] == [alter_besitzer]:
        # Sichtbarkeit war exklusiv auf den alten Besitzer zugeschnitten (Standardfall
        # beim Anlegen) — für den neuen Besitzer frisch berechnen. War die Sichtbarkeit
        # bewusst breiter gewählt (ALLE, GM oder mehrere Spieler), bleibt sie unangetastet.
        sichtbarkeit, sichtbar_fuer = await _default_sichtbarkeit(campaign_id, ziel, body.zielPersonId)
        updates = {"sichtbarkeit": sichtbarkeit, "sichtbarFuer": sichtbar_fuer}

    moved = await repository.transfer_owner(campaign_id, item_id, body.zielPersonId)
    if moved is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Übertragung fehlgeschlagen")
    if updates:
        moved = await repository.update_gegenstand(campaign_id, item_id, updates)
    # Inhalt erst nach der Sichtbarkeit mitnehmen, sonst bleibt er am alten Besitzer hängen.
    await inhalt_mitnehmen(campaign_id, item_id, body.zielPersonId)
    await hooks.gegenstand(
        campaign_id,
        art="WEITERGEGEBEN",
        gegenstand_id=item_id,
        alter_besitzer_id=alter_besitzer,
        neuer_besitzer_id=body.zielPersonId,
    )
    return moved


@campaign_router.post("/{item_id}/vorlage", response_model=GegenstandResponse, dependencies=[Depends(require_campaign_gm)])
async def vorlage_machen(campaign_id: str, item_id: str):
    """Entfernt den Besitzer eines Gegenstands — er wird zur besitzerlosen
    Vorlage (Gegenstück zu Besitzer wechseln, siehe schemas.py-Invariante)."""
    moved = await repository.remove_owner(campaign_id, item_id)
    if moved is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden oder hat schon keinen Besitzer")
    return moved


@campaign_router.get(
    "/{item_id}/stapelkandidaten",
    response_model=list[GegenstandResponse],
)
async def stapelkandidaten(campaign_id: str, item_id: str, viewer: Viewer = Depends(get_viewer)):
    """Andere Gegenstände derselben Besitzerin, die sich mit diesem hier zu
    einem Stapel zusammenlegen ließen — füllt die Auswahl im
    Zusammenlegen-Popup (siehe repository.stapel_gleich für die Gleichheitsprüfung).

    Auch Spieler dürfen das, aber nur am eigenen Besitz (wie Wegwerfen/Ablage) —
    deshalb ohne require_campaign_gm, mit eigener Besitzprüfung; steht namentlich
    in der Ausnahmeliste von tests/test_zugriffsschutz.py.
    """
    if viewer.role != "GM":
        besitzer = await repository.get_owner_person_id(campaign_id, item_id)
        if besitzer is None or besitzer != viewer.person_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    return await repository.stapelkandidaten(campaign_id, item_id)


@campaign_router.post(
    "/{item_id}/zusammenlegen",
    response_model=GegenstandResponse,
)
async def zusammenlegen(
    campaign_id: str,
    item_id: str,
    body: ZusammenlegenRequest,
    viewer: Viewer = Depends(get_viewer),
):
    """Legt mehrere gleichwertige Gegenstände zu einem Stapel zusammen.

    `item_id` ist das Ziel: bekommt die Summe der Mengen und hatMenge=true.
    Die Quellen landen — wie bei jedem anderen Entsorgen — im Mülleimer der
    Spielleitung, nicht gelöscht (siehe repository.wegwerfen), damit eine
    falsche Auswahl reversibel bleibt.

    **Auch Spieler dürfen das, nur am eigenen Besitz** (Mark, 26.10.2026:
    "das müssen unbedingt auch die Spieler können"), wie Wegwerfen/Ablage —
    deshalb ohne require_campaign_gm, mit eigener Besitzprüfung hier UND in
    `repository.zusammenlegen` selbst (jede Quelle muss demselben Besitzer
    gehören wie das Ziel). Steht namentlich in der Ausnahmeliste von
    tests/test_zugriffsschutz.py.
    """
    if viewer.role != "GM":
        besitzer = await repository.get_owner_person_id(campaign_id, item_id)
        if besitzer is None or besitzer != viewer.person_id:
            # 404 statt 403, wie beim Umlegen/Wegwerfen: ein Spieler soll
            # nicht erfahren, ob es den Gegenstand überhaupt gibt.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    von = "Spielleitung"
    if viewer.role != "GM" and viewer.person_id:
        person = await get_node("Person", PERSON_FIELDS, campaign_id, viewer.person_id)
        von = person["name"] if person else ""

    try:
        ergebnis = await repository.zusammenlegen(campaign_id, item_id, body.quellItemIds, von)
    except repository.NichtStapelbar as fehler:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Einzigartige Stücke oder Gegenstände unterschiedlicher Besitzer lassen sich nicht zusammenlegen",
        ) from fehler
    except repository.UnterschiedlicherGegenstand as fehler:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Die ausgewählten Gegenstände sind mechanisch nicht gleich und lassen sich nicht zusammenlegen",
        ) from fehler
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    return ergebnis


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
    await hooks.gegenstand(
        campaign_id,
        art="ENTSORGT",
        gegenstand_id=item_id,
        alter_besitzer_id=viewer.person_id if viewer.role != "GM" else None,
    )
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
    Behälter seines Besitzers (Fahrzeuge etc.).

    **Die SL sieht alle Behälter der ganzen Kampagne** (31.10.2026, Mark
    konnte beim Schloss-Test nichts in eine besitzerlose Schatzkiste legen —
    siehe repository.py::alle_ablageziele_fuer_gm), Spieler weiterhin nur
    ihre eigenen — sonst könnte ein Spieler Dinge in fremde Rucksäcke legen.
    """
    if viewer.role == "GM":
        return await repository.alle_ablageziele_fuer_gm(campaign_id, item_id)
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

    **Drohne/Fahrzeug (26.10.2026, Mark: "ich habe auch nicht die
    Möglichkeit Waffen auszurüsten"):** zusätzlich erlaubt für den
    gebundenen Rigger an Gegenständen, die seiner eigenen aktiven Drohne/
    seinem eigenen Fahrzeug gehören — dasselbe Besitz-Prinzip wie bei
    `traits/routes.py::_darf_person_sehen`, hier für Ausrüstung statt für
    den Charakterbogen. Der Rigger IST nicht der Besitzer dieser
    Gegenstände (das ist die Drohne selbst), deshalb reicht der einfache
    Vergleich oben nicht.
    """
    if viewer.role != "GM":
        besitzer = await repository.get_owner_person_id(campaign_id, item_id)
        if not await _eigener_kreis(campaign_id, viewer.person_id, besitzer):
            # 404 statt 403: ein Spieler soll nicht erfahren, ob es den
            # Gegenstand überhaupt gibt.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    # Verbautes Chrom lässt sich nicht umlegen — es sitzt im Körper, nicht im
    # Rucksack. Mark: "das sind keine Gegenstände die er nach dem sie Mal
    # eigebaut wurden wieder ablegen kann". Der Weg heraus führt über
    # .../chirurgie, nicht über die Ablage.
    aktuelles = await repository.get_gegenstand(campaign_id, item_id)
    if aktuelles and not chirurgie.kann_ablegen(aktuelles, viewer.role == "GM"):
        if aktuelles.get("istNatuerlich"):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Natürliche Rüstung lässt sich nicht ablegen — sie ist Teil des Körpers (nur die Spielleitung kann das im Ausnahmefall).",
            )
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
            person = await get_node("Person", PERSON_FIELDS, campaign_id, besitzer_id)
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


@campaign_router.get("/{item_id}", response_model=GegenstandResponse)
async def get_item(campaign_id: str, item_id: str, viewer: Viewer = Depends(get_viewer)):
    """Einzelnen Gegenstand laden — auch Ideenschmiede-Entwürfe.

    Steht nach den statischen GET-Pfaden (`/weggeworfen`, `/traglast`,
    `/verbaut/{person_id}`), sonst würden die als Kennung gelesen.
    """
    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    item = (await _mit_augment_boni(campaign_id, [item]))[0]
    sichtbar = await _sichtbar_fuer(campaign_id, [item], viewer)
    if not sichtbar:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    return sichtbar[0]


class OeffnenRequest(BaseModel):
    passwort: str = ""


class SpielZug(BaseModel):
    folge: list[int] | None = None


class SpielStand(BaseModel):
    runde: int
    anzeige: list[int]
    falsch: bool = False
    geschafft: bool = False
    aufgeschlossen: bool = False


async def _darf_kiste(campaign_id: str, item_id: str, viewer: Viewer) -> dict:
    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    if viewer.role == "GM":
        return item
    besitzer = await repository.get_owner_person_id(campaign_id, item_id)
    if besitzer is None or besitzer != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    if item["id"] in await ids_in_verschlossenem(campaign_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    return item


@campaign_router.post("/{item_id}/oeffnen", response_model=GegenstandResponse)
async def kiste_oeffnen(campaign_id: str, item_id: str, body: OeffnenRequest, viewer: Viewer = Depends(get_viewer)):
    """Passwort oder Schlüssel. Die Tastenfolge hat ihren eigenen Endpunkt."""
    item = await _darf_kiste(campaign_id, item_id, viewer)
    if not ist_verschlossen(item):
        return (await _sichtbar_fuer(campaign_id, [item], viewer))[0]
    art = item.get("schlossArt")
    if art == "spiel":
        raise HTTPException(status.HTTP_409_CONFLICT, "Das geht nur über die Tasten.")
    if viewer.role != "GM":
        if art == "passwort" and not passwort_passt(body.passwort, item.get("schlossPasswort") or ""):
            raise HTTPException(status.HTTP_409_CONFLICT, "Falsch.")
        if art == "schluessel" and not await besitzt_erreichbaren_schluessel(
            campaign_id, viewer.person_id or "", item.get("schluesselId") or ""
        ):
            raise HTTPException(status.HTTP_409_CONFLICT, "Dir fehlt der Schlüssel.")
    geoeffnet = await repository.update_gegenstand(campaign_id, item_id, {"aufgeschlossen": True})
    if geoeffnet is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    return (await _sichtbar_fuer(campaign_id, [geoeffnet], viewer))[0]


@campaign_router.post("/{item_id}/schloss/spiel", response_model=SpielStand)
async def kiste_spiel(campaign_id: str, item_id: str, body: SpielZug, viewer: Viewer = Depends(get_viewer)):
    """Zeigt die nächste Runde, oder prüft die nachgemachte Folge.

    Ohne `folge` nur die Anzeige. Bei Fehler neue Zufallsfolge, von vorn.
    Kein Versuchslimit. Die volle Folge geht nie an den Client.
    """
    item = await _darf_kiste(campaign_id, item_id, viewer)
    if item.get("schlossArt") != "spiel" or item.get("aufgeschlossen"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Hier ist kein Tasten-Schloss zu.")
    stand = await spiel_lesen(campaign_id, item_id)
    if stand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    laenge = max(1, int(stand.get("spielLaenge") or 4))
    folge = stand["folge"]
    runde = int(stand.get("spielRunde") or 0)
    if len(folge) < laenge:
        folge = neue_folge(laenge)
        runde = 0
        await spiel_schreiben(campaign_id, item_id, folge, runde, False)
    if body.folge is None:
        return SpielStand(runde=runde + 1, anzeige=anzeige_fuer(folge, runde))
    if any(taste < 0 or taste >= 5 for taste in body.folge):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unbekannte Taste.")
    if not zug_passt(body.folge, folge, runde):
        folge = neue_folge(laenge)
        await spiel_schreiben(campaign_id, item_id, folge, 0, False)
        return SpielStand(runde=1, anzeige=anzeige_fuer(folge, 0), falsch=True)
    geschafft = runde + 1 >= laenge
    if geschafft:
        await spiel_schreiben(campaign_id, item_id, folge, laenge, True)
        return SpielStand(runde=laenge, anzeige=[], geschafft=True, aufgeschlossen=True)
    runde += 1
    await spiel_schreiben(campaign_id, item_id, folge, runde, False)
    return SpielStand(runde=runde + 1, anzeige=anzeige_fuer(folge, runde))


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
    Der reguläre Weg mit Maschinenteil + Probe ist
    `.../ruestung/reparieren-material`, der Händlerweg mit Preisverhandlung
    läuft über `.../ruestung/reparatur-preis` + `POST /verhandlungen`.
    """

    kaestchen: int = Field(ge=0)


class AttributWert(BaseModel):
    name: str
    wert: int


class ReparaturProbePool(BaseModel):
    """Pool-Infos fürs Reparatur-Popup: Handwerk-Wert DER TRÄGERIN/DES
    TRÄGERS plus alle ihre/seine Attribute zur freien Partnerwahl (Mark,
    29.10.2026: "eventuell gibt es mal einen besonderen Moment wo es mehr
    darum geht geschickt zu sein, oder Geistesschärfe zu zeigen"), dazu wie
    viele Erfolge die gewählte Materialmenge verlangt und was ein Erfolg
    heilen würde. Reine Leseabfrage, kein Seiteneffekt — gewürfelt wird am
    Tisch."""

    skill: str
    skillWert: int
    attribute: list[AttributWert]
    benoetigteErfolge: int
    heilungBeiErfolg: int
    fehlendeKaestchen: int


class ReparaturMaterialRequest(BaseModel):
    """Selbst-Reparieren: Maschinenteil + Probe, kein Geld.

    Marks Vorgabe (29.10.2026, siehe kampf/ruestung.py für die Herleitung):
    benötigte Erfolge = `menge - 1` (Minimum 1). Reiner Selbstbericht wie
    bei der Maker-Probe im Drohnen-Umbau — der Spieler würfelt physisch am
    Tisch und meldet nur das Ergebnis. "ja" heilt UND verbraucht `menge`
    Material, "patzer" verbraucht NUR das Material, "nein" lässt beides
    unangetastet.
    """

    materialGegenstandId: str
    menge: int = Field(ge=1)
    probenErgebnis: Literal["ja", "nein", "patzer"]


class ReparaturMaterialErgebnis(BaseModel):
    """Auswertung der Selbst-Reparatur, fürs Popup."""

    qualitaet: str
    menge: int
    repariert: int
    materialName: str
    materialVerbraucht: int
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


async def _ruestung_fuer_reparatur(campaign_id: str, item_id: str) -> tuple[dict, str]:
    """Lädt die Rüstung + Besitzer, prüft die Standard-Reparaturfähigkeit.
    Gemeinsame Vorprüfung für Pool-Abfrage, Selbst- und Händler-Reparatur."""
    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
    if item["typ"] != "Rüstung" or item["ruestungKaestchenMax"] <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Nur Rüstung mit Kästchen-System kann repariert werden")
    if item.get("istNatuerlich"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Natürliche Rüstung wird nicht repariert — sie heilt von selbst, sobald die Trägerin vollständig gesund ist.",
        )
    besitzer_id = await repository.get_owner_person_id(campaign_id, item_id)
    if besitzer_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Gegenstand ohne Besitzer kann nicht repariert werden")
    return item, besitzer_id


@campaign_router.get("/{item_id}/ruestung/reparatur-pool", response_model=ReparaturProbePool)
async def ruestung_reparatur_pool(
    campaign_id: str,
    item_id: str,
    materialGegenstandId: str,
    menge: int = 1,
    viewer: Viewer = Depends(get_viewer),
):
    """Pool-Infos fürs Reparatur-Popup: Rüstung repariert sich **nur über
    Handwerk** (Mark, 29.10.2026, siehe docs/wiki/concepts/drohnen-fahrzeuge.md),
    der Attribut-Partner bleibt frei wählbar."""
    item, besitzer_id = await _ruestung_fuer_reparatur(campaign_id, item_id)
    material = await repository.get_gegenstand(campaign_id, materialGegenstandId)
    if material is None or not material.get("istMaschinenteil"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Maschinenteil")

    werte = {r["name"]: r["rating"] for r in await get_ratings_for_entity(campaign_id, besitzer_id)}
    campaign = await get_campaign(campaign_id)
    katalog = await list_catalog(campaign["ruleset"] if campaign else "neotopia")
    # NUR echte Personen-Attribute (29.10.2026, derselbe Fehler wie beim
    # Augment-Pool weiter unten — Mark: "ich irgendwie auch Drohnen-Werte bei
    # meinem Rigger beim Upgraden habe"): `category.startswith("Attribut")`
    # erwischt auch "AttributDrohne"/"AttributDrohneAussenhuelle", eigene
    # Katalogeinträge für Drohnen-Werte, die ein Mensch gar nicht hat (siehe
    # `entities/routes.py::_maker_probe_pool` für dieselbe, schon richtige
    # Lösung).
    person_attribut_kategorien = {*erstellung.ATTRIBUT_KATEGORIEN, "AttributMatrix"}
    attribute = [
        AttributWert(name=t["name"], wert=werte.get(t["name"], 0))
        for t in katalog
        if t["category"] in person_attribut_kategorien
    ]
    fehlende_kaestchen = item["ruestungKaestchenMax"] - item["ruestungKaestchenAktuell"]
    skill = REPARATUR_SKILLS["ruestung"][0]
    return ReparaturProbePool(
        skill=skill,
        skillWert=werte.get(skill, 0),
        attribute=attribute,
        benoetigteErfolge=reparatur_benoetigte_erfolge(menge),
        heilungBeiErfolg=reparatur_heilung_material(material.get("maschinenteilQualitaet") or "", menge, fehlende_kaestchen),
        fehlendeKaestchen=fehlende_kaestchen,
    )


@campaign_router.get("/{item_id}/ruestung/maschinenteile", response_model=list[GegenstandResponse])
async def ruestung_maschinenteile(campaign_id: str, item_id: str, viewer: Viewer = Depends(get_viewer)):
    """Welche Maschinenteile der Besitzer dieser Rüstung zur Auswahl hat
    (für das Selbst-Reparieren-Popup)."""
    besitzer_id = await repository.get_owner_person_id(campaign_id, item_id)
    if besitzer_id is None:
        return []
    return await repository.list_maschinenteile_von(campaign_id, besitzer_id)


@campaign_router.post("/{item_id}/ruestung/reparieren-material", response_model=ReparaturMaterialErgebnis)
async def ruestung_reparieren_material(
    campaign_id: str, item_id: str, body: ReparaturMaterialRequest, viewer: Viewer = Depends(get_viewer)
):
    """Selbst-Reparieren: Maschinenteil + selbstberichtete Probe, kein Geld.
    **Self-Service** (29.10.2026, Korrektur — Mark: "das war alles für die
    Spieler gedacht!"): Spieler würfelt am Tisch, trägt das Ergebnis selbst
    ein, eigenes Material wird verbraucht — genau wie beim Drohnen-/
    Fahrzeug-Pendant (`entities/routes.py::drohne_reparieren_material`) und
    den Werkbank-Augments. GM darf uneingeschränkt, Spieler nur an der
    eigenen Rüstung (siehe `_eigener_kreis`)."""
    item, besitzer_id = await _ruestung_fuer_reparatur(campaign_id, item_id)
    if viewer.role != "GM" and (not viewer.person_id or not await _eigener_kreis(campaign_id, viewer.person_id, besitzer_id)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    material = await repository.get_gegenstand(campaign_id, body.materialGegenstandId)
    if material is None or not material.get("istMaschinenteil"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Maschinenteil")
    if await repository.get_owner_person_id(campaign_id, body.materialGegenstandId) != besitzer_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Maschinenteil gehört nicht der Trägerin/dem Träger.")
    if material.get("menge", 1) < body.menge:
        raise HTTPException(status.HTTP_409_CONFLICT, "Nicht genug von diesem Maschinenteil vorhanden.")

    qualitaet = material.get("maschinenteilQualitaet") or ""
    fehlende_kaestchen = item["ruestungKaestchenMax"] - item["ruestungKaestchenAktuell"]

    # Material wird bei "ja" UND "patzer" verbraucht — nur "nein" lässt es
    # unangetastet (gleiches Muster wie die Maker-Probe im Drohnen-Umbau).
    repariert = 0
    if body.probenErgebnis == "ja":
        repariert = reparatur_heilung_material(qualitaet, body.menge, fehlende_kaestchen)
    material_verbraucht = body.probenErgebnis in ("ja", "patzer")
    material_neue_menge = material["menge"] - body.menge if material_verbraucht else material["menge"]
    if material_verbraucht:
        await repository.update_gegenstand(campaign_id, body.materialGegenstandId, {"menge": material_neue_menge})

    ergebnis = repariere(item["ruestungKaestchenAktuell"], item["ruestungKaestchenMax"], repariert)
    aktualisiert = await repository.update_gegenstand(
        campaign_id, item_id, {"ruestungKaestchenAktuell": ergebnis["kaestchenNeu"]}
    )
    if aktualisiert is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reparatur fehlgeschlagen")

    return ReparaturMaterialErgebnis(
        qualitaet=qualitaet,
        menge=body.menge,
        repariert=repariert,
        materialName=material["name"],
        materialVerbraucht=body.menge if material_verbraucht else 0,
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
    if item.get("istNatuerlich"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Natürliche Rüstung wird nicht repariert — sie heilt von selbst, sobald die Trägerin vollständig gesund ist.",
        )

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
    if item.get("istNatuerlich"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Natürliche Rüstung wird nicht repariert — sie heilt von selbst, sobald die Trägerin vollständig gesund ist.",
        )

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


# =====================================================================
# Waffen-/Rüstungs-/Drohnen-Augments (29.10.2026, siehe items/augments.py
# für die Formeln und docs/wiki/concepts/augments-ausruestung.md für die
# volle Herleitung). Ein Augment ist ein Gegenstand (`istAugment=true`),
# der an einem ANDEREN Gegenstand (Waffe/Rüstung/Cyberdeck/Riggerkonsole)
# ODER einer Drohne/einem Fahrzeug (Person-Knoten) montiert wird.
# =====================================================================

AUGMENT_SKILLS = ("Maker (Hardware)", "Handwerk")


async def _augment_oder_404(campaign_id: str, item_id: str, viewer: Viewer) -> dict:
    item = await repository.get_gegenstand(campaign_id, item_id)
    if item is None or not item.get("istAugment"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Augment")
    if viewer.role != "GM":
        # Self-Service (29.10.2026, Mark: "natürlich war das für die Spieler
        # gedacht... damit das für sie dann auch angezeigt wird, und ihre
        # Materialien verwendet werden") — dieselbe Besitz-Prüfung wie
        # ablage_aendern/besitzer_wechseln: eigene Person ODER eigene
        # gebundene Drohne/eigenes Fahrzeug.
        besitzer_id = await repository.get_owner_person_id(campaign_id, item_id)
        if besitzer_id is None or not viewer.person_id or not await _eigener_kreis(campaign_id, viewer.person_id, besitzer_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Augment")
    return item


async def _augment_pool(campaign_id: str, augment: dict, skill: str) -> tuple[int, list[AttributWert]]:
    if skill not in AUGMENT_SKILLS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Maker (Hardware) oder Handwerk möglich")
    besitzer_id = await repository.get_owner_person_id(campaign_id, augment["id"])
    if besitzer_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Augment ohne Besitzer")
    campaign = await get_campaign(campaign_id)
    katalog = await list_catalog(campaign["ruleset"] if campaign else "neotopia")
    werte = {r["name"]: r["rating"] for r in await get_ratings_for_entity(campaign_id, besitzer_id)}
    # NUR echte Personen-Attribute, nicht die Drohnen-Attribute aus demselben
    # Katalog (29.10.2026, Mark: "ich irgendwie auch Drohnen-Werte bei meinem
    # Rigger beim Upgraden habe") — siehe Kommentar bei
    # `ruestung_reparatur_pool` weiter oben für die ausführliche Begründung.
    person_attribut_kategorien = {*erstellung.ATTRIBUT_KATEGORIEN, "AttributMatrix"}
    attribute = [
        AttributWert(name=t["name"], wert=werte.get(t["name"], 0))
        for t in katalog
        if t["category"] in person_attribut_kategorien
    ]
    return werte.get(skill, 0), attribute


class AugmentMontagePool(BaseModel):
    """Pool-Infos fürs Montieren/Demontieren-Popup: frei wählbarer Skill
    (Maker (Hardware) ODER Handwerk, Mark 29.10.2026) + freie Attributwahl,
    benötigte Erfolge = Level + 1 (items/augments.py::benoetigte_erfolge_montage)."""

    skill: str
    skillWert: int
    attribute: list[AttributWert]
    level: int
    benoetigteErfolge: int


@campaign_router.get("/{item_id}/augment/montage-pool", response_model=AugmentMontagePool)
async def augment_montage_pool(campaign_id: str, item_id: str, skill: str, viewer: Viewer = Depends(get_viewer)):
    """Reine Leseabfrage für Montieren UND Demontieren — dieselbe Schwelle
    gilt für beide Richtungen (Mark: "genau wie zum Anbringen, da ist dieser
    Wurf auch nötig")."""
    augment = await _augment_oder_404(campaign_id, item_id, viewer)
    skill_wert, attribute = await _augment_pool(campaign_id, augment, skill)
    level = augment_level(augment.get("traitBoni") or {})
    return AugmentMontagePool(
        skill=skill, skillWert=skill_wert, attribute=attribute, level=level, benoetigteErfolge=benoetigte_erfolge_montage(level)
    )


class AugmentZiel(BaseModel):
    id: str
    name: str
    typ: str
    upgradeSlots: int
    belegteSlots: int


@campaign_router.get("/{item_id}/augment/ziele", response_model=list[AugmentZiel])
async def augment_ziele(campaign_id: str, item_id: str, viewer: Viewer = Depends(get_viewer)):
    """Gegenstände im Besitz DESSELBEN Besitzers mit freiem Slot UND
    passendem Waffentyp — Drohnen/Fahrzeuge als Ziel laufen über
    `drohnenApi`/`entities/routes.py` auf der Frontend-Seite (andere
    Besitzrelation, siehe `items/repository.py::list_montierbare_ziele`)."""
    augment = await _augment_oder_404(campaign_id, item_id, viewer)
    besitzer_id = await repository.get_owner_person_id(campaign_id, item_id)
    if besitzer_id is None:
        return []
    kandidaten = await repository.list_montierbare_ziele(campaign_id, besitzer_id)
    waffentyp = augment.get("augmentWaffentyp") or ""
    zieltyp = augment.get("augmentZielTyp") or ""
    return [
        AugmentZiel(id=k["id"], name=k["name"], typ=k["typ"], upgradeSlots=k["upgradeSlots"], belegteSlots=k["belegteSlots"])
        for k in kandidaten
        if k["id"] != item_id
        and k["belegteSlots"] < k["upgradeSlots"]
        and waffentyp_passt(waffentyp, k.get("kampfFertigkeit") or "")
        and zieltyp_passt(zieltyp, k.get("typ") or "")
    ]


class AugmentMontierenRequest(BaseModel):
    zielId: str
    skill: str
    probenErgebnis: Literal["ja", "nein", "patzer"]


class AugmentAktionsErgebnis(BaseModel):
    """Auswertung für Montieren/Demontieren, fürs Popup."""

    erfolgreich: bool
    defekt: bool
    gegenstand: GegenstandResponse


@campaign_router.post("/{item_id}/augment/montieren", response_model=AugmentAktionsErgebnis)
async def augment_montieren(campaign_id: str, item_id: str, body: AugmentMontierenRequest, viewer: Viewer = Depends(get_viewer)):
    """Montiert ein Augment an ein Ziel — selbstberichtete Probe, kein
    serverseitiger Würfel. Ein Patzer beschädigt das Augment (`defekt=true`)
    statt die Montage nur scheitern zu lassen (Mark, 29.10.2026).
    **Self-Service** — Mark, 29.10.2026: "natürlich war das für die Spieler
    gedacht... damit das für sie dann auch angezeigt wird, und ihre
    Materialien verwendet werden" — Spieler würfeln am Tisch, tragen das
    Ergebnis selbst ein, auf eigenen Besitz begrenzt (siehe
    `_augment_oder_404`/`_eigener_kreis`); GM darf uneingeschränkt.
    """
    augment = await _augment_oder_404(campaign_id, item_id, viewer)
    if augment.get("defekt"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Augment ist defekt — erst reparieren.")
    if augment.get("montiertAnId"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Augment ist bereits montiert.")

    ziel = await repository.ziel_fuer_augment(campaign_id, body.zielId)
    if ziel is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ziel nicht gefunden")
    if viewer.role != "GM":
        # Ziel muss im selben Besitzkreis sein wie das Augment selbst — sonst
        # könnte ein Spieler sein Augment an fremde Ausrüstung montieren.
        if ziel["kind"] == "Gegenstand":
            ziel_besitzer = await repository.get_owner_person_id(campaign_id, body.zielId)
        else:
            ziel_besitzer = ziel["id"]
        if ziel_besitzer is None or not viewer.person_id or not await _eigener_kreis(campaign_id, viewer.person_id, ziel_besitzer):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ziel nicht gefunden")
    if ziel["upgradeSlots"] <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Ziel hat keine Augment-Slots.")
    belegte = await repository.belegte_slots(campaign_id, body.zielId)
    if belegte >= ziel["upgradeSlots"]:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Alle {ziel['upgradeSlots']} Slots sind belegt.")
    if not waffentyp_passt(augment.get("augmentWaffentyp") or "", ziel["kampfFertigkeit"]):
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Augment passt nicht an dieses Ziel.")
    if not zieltyp_passt(augment.get("augmentZielTyp") or "", ziel.get("typ") or ""):
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Augment passt nur an einen bestimmten Zieltyp.")
    if augment.get("schadenArt"):
        # Schadensart ist ein OVERRIDE, kein Bonus — zwei Schadensart-Augments
        # am selben Ziel würden sich widersprechen (29.10.2026 Nachbesserung,
        # Mark: "Montieren wird abgelehnt, wenn am Ziel schon ein
        # Schadensart-Augment sitzt").
        vorhandene_boni = await repository.augment_boni_fuer_ziel(campaign_id, body.zielId)
        if vorhandene_boni.get("schadenArt"):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "An diesem Ziel sitzt bereits ein Augment, das die Schadensart ändert — erst das demontieren.",
            )

    defekt_neu = body.probenErgebnis == "patzer"
    erfolgreich = body.probenErgebnis == "ja"
    if erfolgreich:
        aktualisiert = await repository.montiere_augment(campaign_id, item_id, body.zielId)
    elif defekt_neu:
        aktualisiert = await repository.update_gegenstand(campaign_id, item_id, {"defekt": True})
    else:
        aktualisiert = augment
    if aktualisiert is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Montage fehlgeschlagen")
    return AugmentAktionsErgebnis(erfolgreich=erfolgreich, defekt=bool(aktualisiert.get("defekt")), gegenstand=aktualisiert)


class AugmentDemontierenRequest(BaseModel):
    skill: str
    probenErgebnis: Literal["ja", "nein", "patzer"]


@campaign_router.post("/{item_id}/augment/demontieren", response_model=AugmentAktionsErgebnis)
async def augment_demontieren(campaign_id: str, item_id: str, body: AugmentDemontierenRequest, viewer: Viewer = Depends(get_viewer)):
    """Demontiert ein Augment — jederzeit möglich (kein Körper-Risiko wie
    bei Cyberware), aber dieselbe Probe wie beim Montieren. Ein Patzer
    beschädigt das Augment, lässt es aber montiert (Mark, 29.10.2026:
    dieselbe Nebenwirkung wie beim Anbringen). **Self-Service**, siehe
    `augment_montieren`."""
    augment = await _augment_oder_404(campaign_id, item_id, viewer)
    if not augment.get("montiertAnId"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Augment ist nicht montiert.")

    erfolgreich = body.probenErgebnis == "ja"
    if erfolgreich:
        aktualisiert = await repository.demontiere_augment(campaign_id, item_id)
    elif body.probenErgebnis == "patzer":
        aktualisiert = await repository.update_gegenstand(campaign_id, item_id, {"defekt": True})
    else:
        aktualisiert = augment
    if aktualisiert is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Demontage fehlgeschlagen")
    return AugmentAktionsErgebnis(erfolgreich=erfolgreich, defekt=bool(aktualisiert.get("defekt")), gegenstand=aktualisiert)


class AugmentReparaturPool(BaseModel):
    skill: str
    skillWert: int
    attribute: list[AttributWert]
    level: int
    benoetigteErfolge: int
    heilungBeiErfolg: int
    vollstaendigRepariert: bool


@campaign_router.get("/{item_id}/augment/reparatur-pool", response_model=AugmentReparaturPool)
async def augment_reparatur_pool(
    campaign_id: str, item_id: str, skill: str, materialGegenstandId: str, menge: int = 1, viewer: Viewer = Depends(get_viewer)
):
    """Reparatur eines defekten Augments — dieselbe Material-/Erfolgsformel
    wie die normale Werkbank-Reparatur (`kampf/ruestung.py::
    reparatur_benoetigte_erfolge`/`reparatur_heilung_material`), nur mit dem
    Augment-Level statt "fehlenden Kästchen" als Zielgröße. Mark, 29.10.2026:
    "die Probe ist Level des Gegenstandes -1 zum reparieren". **Self-Service**,
    siehe `augment_montieren`."""
    augment = await _augment_oder_404(campaign_id, item_id, viewer)
    if not augment.get("defekt"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Augment ist nicht defekt.")
    material = await repository.get_gegenstand(campaign_id, materialGegenstandId)
    if material is None or not material.get("istMaschinenteil"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Maschinenteil")
    if viewer.role != "GM":
        material_besitzer = await repository.get_owner_person_id(campaign_id, materialGegenstandId)
        if (
            material_besitzer is None
            or not viewer.person_id
            or not await _eigener_kreis(campaign_id, viewer.person_id, material_besitzer)
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Maschinenteil")

    skill_wert, attribute = await _augment_pool(campaign_id, augment, skill)
    level = augment_level(augment.get("traitBoni") or {})
    heilung = reparatur_heilung_material(material.get("maschinenteilQualitaet") or "", menge, level)
    return AugmentReparaturPool(
        skill=skill,
        skillWert=skill_wert,
        attribute=attribute,
        level=level,
        benoetigteErfolge=reparatur_benoetigte_erfolge(level),
        heilungBeiErfolg=heilung,
        vollstaendigRepariert=heilung >= level,
    )


class AugmentReparierenRequest(BaseModel):
    materialGegenstandId: str
    menge: int = Field(ge=1)
    probenErgebnis: Literal["ja", "nein", "patzer"]


class AugmentReparaturErgebnis(BaseModel):
    repariert: bool
    materialName: str
    materialVerbraucht: int
    materialRestmenge: int
    gegenstand: GegenstandResponse


@campaign_router.post("/{item_id}/augment/reparieren-material", response_model=AugmentReparaturErgebnis)
async def augment_reparieren_material(
    campaign_id: str, item_id: str, body: AugmentReparierenRequest, viewer: Viewer = Depends(get_viewer)
):
    """Repariert ein defektes Augment mit Maschinenteil + selbstberichteter
    Probe. **Self-Service**, siehe `augment_montieren`."""
    augment = await _augment_oder_404(campaign_id, item_id, viewer)
    if not augment.get("defekt"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Augment ist nicht defekt.")
    material = await repository.get_gegenstand(campaign_id, body.materialGegenstandId)
    if material is None or not material.get("istMaschinenteil"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Maschinenteil")
    if viewer.role != "GM":
        material_besitzer = await repository.get_owner_person_id(campaign_id, body.materialGegenstandId)
        if (
            material_besitzer is None
            or not viewer.person_id
            or not await _eigener_kreis(campaign_id, viewer.person_id, material_besitzer)
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Maschinenteil")
    if material.get("menge", 1) < body.menge:
        raise HTTPException(status.HTTP_409_CONFLICT, "Nicht genug von diesem Maschinenteil vorhanden.")

    level = augment_level(augment.get("traitBoni") or {})
    qualitaet = material.get("maschinenteilQualitaet") or ""
    repariert = False
    if body.probenErgebnis == "ja":
        heilung = reparatur_heilung_material(qualitaet, body.menge, level)
        repariert = heilung >= level
    material_verbraucht = body.probenErgebnis in ("ja", "patzer")
    material_neue_menge = material["menge"] - body.menge if material_verbraucht else material["menge"]
    if material_verbraucht:
        await repository.update_gegenstand(campaign_id, body.materialGegenstandId, {"menge": material_neue_menge})

    aktualisiert = augment
    if repariert:
        aktualisiert = await repository.update_gegenstand(campaign_id, item_id, {"defekt": False})
    if aktualisiert is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reparatur fehlgeschlagen")

    return AugmentReparaturErgebnis(
        repariert=repariert,
        materialName=material["name"],
        materialVerbraucht=body.menge if material_verbraucht else 0,
        materialRestmenge=material_neue_menge,
        gegenstand=aktualisiert,
    )


@campaign_router.get("/{item_id}/augment/material", response_model=list[GegenstandResponse])
async def augment_material(campaign_id: str, item_id: str, viewer: Viewer = Depends(get_viewer)):
    """Maschinenteile im Besitz der Person, die dieses defekte Augment
    besitzt — für die Reparatur-Material-Auswahl."""
    besitzer_id = await repository.get_owner_person_id(campaign_id, item_id)
    if besitzer_id is None:
        return []
    return await repository.list_maschinenteile_von(campaign_id, besitzer_id)
