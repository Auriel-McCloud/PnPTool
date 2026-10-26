import mimetypes
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_campaign, get_einstellungen
from app.entities import repository
from app.entities import filterung
from app.ereignisprotokoll import hooks
from app.lexikon import hooks as lexikon_hooks
from app.entities.repository import EVENT_FIELDS, FRAKTION_FIELDS, GEWAECHS_FIELDS, ORT_FIELDS, PERSON_FIELDS
from app.items import repository as items_repository
from app.traits import repository as traits_repository
from app.traits import erfahrung
from app.traits.bogen import sichtbare_kategorien
from app.traits.drohnen import DROHNE_GESPERRTE_FERTIGKEITEN, kann_aktivieren, kann_bezahlen, maschinenteil_reicht
from app.zusatzfertigkeiten import repository as zf_repository
from app.entities.visibility import (
    filter_entities_for_viewer,
    filter_entity_for_viewer,
    filter_verbindungen_for_viewer,
    is_visible_to,
)
from app.entities.schemas import (
    EinflussEintrag,
    EinflussSetzen,
    EventCreate,
    EventResponse,
    EventUpdate,
    FilterOptionen,
    FraktionCreate,
    FraktionResponse,
    FraktionUpdate,
    GewaechsCreate,
    GewaechsResponse,
    GewaechsUpdate,
    LebtInEintrag,
    LebtInHinzufuegen,
    LebtInOrtEintrag,
    OrtCreate,
    OrtResponse,
    OrtUpdate,
    PersonCreate,
    PersonResponse,
    PersonUpdate,
    VerbindungCreate,
    VerbindungResponse,
    VerbindungUpdate,
)

router = APIRouter(prefix="/api/campaigns/{campaign_id}", tags=["entities"], dependencies=[Depends(require_campaign_zugang)])


def _visible_or_404(node: dict | None, viewer: Viewer, was: str) -> dict:
    """Applies visibility filtering to a single node, 404 if it survives as None.

    Deliberately 404 and not 403: a viewer who may not see something must not
    be able to tell it apart from something that does not exist.
    """
    if node is not None:
        node = filter_entity_for_viewer(node, viewer.role, viewer.person_id)
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{was} nicht gefunden")
    return node


async def _sichtbare_kanten(campaign_id: str, viewer: Viewer) -> list[dict]:
    """Verbindungen, die dieser Blickwinkel sehen darf.

    Grundlage für den Beziehungsfilter. Ungefiltert würde eine geheime Kante
    einen Spieler auf einen NPC stossen lassen, den er nicht kennen darf —
    der Treffer allein wäre schon die Auskunft.
    """
    kanten = await repository.list_verbindungen(campaign_id)
    return filter_verbindungen_for_viewer(kanten, viewer.role, viewer.person_id)


async def _aufbereiten(
    knoten: list[dict],
    campaign_id: str,
    viewer: Viewer,
    *,
    namensfeld: str,
    suche: str | None,
    sortierung: str | None,
    verbunden_mit: str | None = None,
    verbindungs_typ: str | None = None,
    nur_entwuerfe: bool = False,
) -> list[dict]:
    """Sichtbarkeit → Entwurf-Filter → Suche → Beziehung → Reihenfolge.

    Die Reihenfolge ist wesentlich: Erst wird weggefiltert, was der Blickwinkel
    nicht sehen darf, und **danach** gesucht. Andersherum könnte ein Spieler
    einen 🔒-redigierten Satz finden, indem er danach sucht — dass er einen
    Treffer bekommt, wäre selbst die Auskunft.

    Entwürfe (istEntwurf=true) werden standardmäßig ausgeblendet — sie gehören
    in die Ideenschmiede, nicht in die normale Ansicht. Mit nur_entwuerfe=True
    werden stattdessen nur Entwürfe gezeigt.
    """
    sichtbar = filter_entities_for_viewer(knoten, viewer.role, viewer.person_id)
    # Entwurf-Filter: standardmäßig ausblenden, für Ideenschmiede invertieren
    if nur_entwuerfe:
        sichtbar = [e for e in sichtbar if e.get("istEntwurf", False)]
    else:
        sichtbar = [e for e in sichtbar if not e.get("istEntwurf", False)]
    sichtbar = filterung.nach_suche(sichtbar, suche, namensfeld)

    braucht_kanten = bool(verbunden_mit or verbindungs_typ) or sortierung == "verbindungen"
    kanten = await _sichtbare_kanten(campaign_id, viewer) if braucht_kanten else []

    if verbunden_mit or verbindungs_typ:
        sichtbar = filterung.nach_beziehung(sichtbar, kanten, verbunden_mit, verbindungs_typ)
    return filterung.sortiere(sichtbar, sortierung, namensfeld, kanten)


@router.post("/personen", response_model=PersonResponse, dependencies=[Depends(require_campaign_gm)])
async def create_person(campaign_id: str, body: PersonCreate):
    return await repository.create_node("Person", PERSON_FIELDS, campaign_id, body.model_dump())


@router.get("/personen", response_model=list[PersonResponse])
async def list_personen(
    campaign_id: str,
    suche: str | None = Query(default=None, description="Sucht in Name, Beschreibung und Notizen."),
    sortierung: filterung.Sortierung | None = Query(default=None),
    personType: Literal["PC", "NPC"] | None = Query(default=None, description="Nur PCs oder nur NPCs."),
    verbundenMit: str | None = Query(
        default=None,
        description="Nur Personen mit einer Verbindung zu dieser Entität (Ort, Event, Person, Gegenstand).",
    ),
    verbindungsTyp: str | None = Query(
        default=None, description="Nur Personen mit einer Verbindung dieser Bezeichnung (z.B. 'Gegner')."
    ),
    viewer: Viewer = Depends(get_viewer),
):
    nodes = await repository.list_nodes("Person", PERSON_FIELDS, campaign_id)
    if personType is not None:
        nodes = [n for n in nodes if n.get("personType") == personType]
    return await _aufbereiten(
        nodes,
        campaign_id,
        viewer,
        namensfeld="name",
        suche=suche,
        sortierung=sortierung,
        verbunden_mit=verbundenMit,
        verbindungs_typ=verbindungsTyp,
    )


@router.get("/personen/{node_id}", response_model=PersonResponse)
async def get_person(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Person", PERSON_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Person")


@router.patch("/personen/{node_id}", response_model=PersonResponse, dependencies=[Depends(require_campaign_gm)])
async def update_person(campaign_id: str, node_id: str, body: PersonUpdate):
    daten = body.model_dump()
    # Ereignisprotokoll (27.09.2026, CharakterEntwicklung RASSE_GEAENDERT):
    # `rasse` ist ein generisches PATCH-Feld ohne eigenen Endpunkt — deshalb
    # hier per Vorher/Nachher-Vergleich erkannt statt an einer eigenen Route.
    # Mark: "kann ja auch storytechnisch begründet passieren... Body Swap
    # oder sowas" — jeder tatsächliche Wechsel wird geloggt, unabhängig vom
    # Grund.
    vorherige_rasse = None
    if daten.get("rasse") is not None:
        vorher = await repository.get_node("Person", PERSON_FIELDS, campaign_id, node_id)
        vorherige_rasse = vorher.get("rasse") if vorher else None

    node = await repository.update_node("Person", PERSON_FIELDS, campaign_id, node_id, daten)
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    if daten.get("rasse") is not None and daten["rasse"] != vorherige_rasse:
        await hooks.charakterentwicklung(
            campaign_id, person_id=node_id, art="RASSE_GEAENDERT",
            alt=vorherige_rasse or "", neu=daten["rasse"],
        )
    if daten.get("sichtbarkeit") is not None or daten.get("istCritter") is not None:
        await lexikon_hooks.campaign_weit_neu_berechnen(campaign_id)
    return node


@router.delete("/personen/{node_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_person(campaign_id: str, node_id: str):
    if not await repository.delete_node("Person", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")


@router.post("/personen/{node_id}/zu-npc", response_model=PersonResponse, dependencies=[Depends(require_campaign_gm)])
async def person_zu_npc(campaign_id: str, node_id: str):
    """Wandelt einen PC in-place in einen NPC um (siehe repository.person_zu_npc).

    Typischer Anlass: ein vorgefertigter Charakter wurde von keinem Spieler
    gewählt, ist aber story-relevant genug, um als NPC weiterzuleben.
    """
    node = await repository.person_zu_npc(campaign_id, node_id)
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PC nicht gefunden")
    await hooks.charakterentwicklung(campaign_id, person_id=node_id, art="ZU_NPC_GEMACHT", alt="PC", neu="NPC")
    return node


@router.post("/personen/{node_id}/zu-pc", response_model=PersonResponse, dependencies=[Depends(require_campaign_gm)])
async def person_zu_pc(campaign_id: str, node_id: str):
    """Wandelt einen NPC in-place in einen PC um (siehe repository.person_zu_pc)."""
    node = await repository.person_zu_pc(campaign_id, node_id)
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NPC nicht gefunden")
    await hooks.charakterentwicklung(campaign_id, person_id=node_id, art="ZU_PC_GEMACHT", alt="NPC", neu="PC")
    return node


@router.post("/personen/{node_id}/extra-ep", response_model=PersonResponse, dependencies=[Depends(require_campaign_gm)])
async def extra_ep_erhoehen(campaign_id: str, node_id: str, body: dict):
    """Erhöht die Extra-EP eines PCs um einen Betrag (nur positiv, irreversibel).
    
    Body: {"betrag": 1}  — muss > 0 sein.
    """
    betrag = body.get("betrag", 0)
    if not isinstance(betrag, int) or betrag <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Betrag muss eine positive Ganzzahl sein")
    person = await repository.get_node("Person", PERSON_FIELDS, campaign_id, node_id)
    if not person:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    neu = person.get("extraEP", 0) + betrag
    return await repository.update_node("Person", PERSON_FIELDS, campaign_id, node_id, {"extraEP": neu})


@router.get("/critter", response_model=list[dict])
async def list_critter(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Critter für die Begleiter-Übersicht (`begleiter/BegleiterVerwaltung.tsx`).

    Critter sind seit 20.09.2026 echte NPCs (`Person`, `istCritter=true`,
    siehe Modul-Docstring in `app/begleiter/repository.py`) — diese Route
    liefert nur die schlanken Felder, die eine Kachel braucht (Name/Bild/
    Besitzer), nicht den vollen Charakterbogen.
    """
    roh = await repository.list_critter(campaign_id)
    sichtbar = [
        c for c in roh
        if is_visible_to(c.get("sichtbarkeit") or "GM", c.get("sichtbarFuer") or [], viewer.role, viewer.person_id)
    ]
    return sichtbar


@router.post("/critter/{node_id}/besitzer", response_model=dict, dependencies=[Depends(require_campaign_gm)])
async def critter_besitzer_setzen(campaign_id: str, node_id: str, body: dict):
    person_id = body.get("personId")
    ergebnis = await repository.critter_besitzer_setzen(campaign_id, node_id, person_id)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Critter nicht gefunden")
    return ergebnis


@router.get("/drohnen", response_model=list[dict])
async def list_drohnen(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Drohnen/Fahrzeuge fürs geplante Burgermenü — dasselbe schlanke Muster
    wie `list_critter`/`list_ki`, siehe docs/wiki/concepts/drohnen-fahrzeuge.md."""
    roh = await repository.list_drohnen(campaign_id)
    sichtbar = [
        d for d in roh
        if is_visible_to(d.get("sichtbarkeit") or "GM", d.get("sichtbarFuer") or [], viewer.role, viewer.person_id)
    ]

    # Riggerkonsole-Slots je Rigger einmal berechnen, nicht pro Drohne neu —
    # die Deckel-Regel (`kann_aktivieren`) gab es seit Phase 2 nur backendseitig
    # fürs Aktivieren selbst, nie als Anzeige (Mark, 26.10.2026: "ich seh die
    # freien Slots nirgends"). None/None = kein Rigger gebunden.
    rigger_ids = {d["riggerId"] for d in sichtbar if d.get("riggerId")}
    slots: dict[str, tuple[int, int]] = {}
    for rid in rigger_ids:
        max_drohnen = await items_repository.riggerkonsole_max_drohnen(campaign_id, rid)
        aktuell = await repository.aktive_drohnen_zahl(campaign_id, rid)
        slots[rid] = (aktuell, max_drohnen)
    for d in sichtbar:
        rid = d.get("riggerId")
        belegt_max = slots.get(rid) if rid else None
        d["riggerSlotsBelegt"] = belegt_max[0] if belegt_max else None
        d["riggerSlotsMax"] = belegt_max[1] if belegt_max else None

    return sichtbar


@router.post("/drohnen/{node_id}/rigger", response_model=dict, dependencies=[Depends(require_campaign_gm)])
async def drohne_rigger_setzen(campaign_id: str, node_id: str, body: dict):
    """Bindet eine Drohne/ein Fahrzeug an ihren Rigger — oder löst die Bindung."""
    person_id = body.get("personId")
    ergebnis = await repository.drohne_rigger_setzen(campaign_id, node_id, person_id)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")
    return ergebnis


@router.post("/drohnen/{node_id}/aktiv", response_model=dict)
async def drohne_aktiv_setzen(campaign_id: str, node_id: str, body: dict, viewer: Viewer = Depends(get_viewer)):
    """Aktiviert/deaktiviert die Verbindung zur Riggerkonsole.

    25.10.2026 (docs/wiki/concepts/drohnen-fahrzeuge.md): nur der eigene
    Rigger oder die Spielleitung dürfen das. Aktivieren wird gegen
    `maxDrohnen` der ausgerüsteten Riggerkonsole gedeckelt — Deaktivieren ist
    immer erlaubt (ein zu niedriger neuer Deckel zwingt niemanden offline).
    """
    aktiv = bool(body.get("aktiv"))
    drohne = await repository.get_node("Person", PERSON_FIELDS, campaign_id, node_id)
    if drohne is None or not (drohne.get("istDrohne") or drohne.get("istFahrzeug")):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")

    rigger_id = await repository.drohne_rigger(campaign_id, node_id)
    if viewer.role != "GM" and (rigger_id is None or rigger_id != viewer.person_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")

    if aktiv and not drohne.get("riggerAktiv"):
        if rigger_id is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Diese Drohne/dieses Fahrzeug hat keinen Rigger.")
        max_drohnen = await items_repository.riggerkonsole_max_drohnen(campaign_id, rigger_id)
        aktuell = await repository.aktive_drohnen_zahl(campaign_id, rigger_id)
        if not kann_aktivieren(aktuell, max_drohnen):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Riggerkonsole erlaubt nur {max_drohnen} aktive Drohne(n)/Fahrzeug(e) gleichzeitig.",
            )

    return await repository.update_node("Person", PERSON_FIELDS, campaign_id, node_id, {"riggerAktiv": aktiv})


class DrohneSteigernInput(BaseModel):
    traitDefId: str
    # Material statt Nuyen (26.10.2026): wenn gesetzt, bezahlt ein
    # Maschinenteil-Gegenstand des Riggers statt Nuyen-Abzug — siehe
    # traits/drohnen.py::maschinenteil_reicht.
    materialGegenstandId: str | None = None


async def _drohne_und_rigger_oder_404(
    campaign_id: str, node_id: str, viewer: Viewer
) -> tuple[dict, str | None]:
    """Lädt die Drohne/das Fahrzeug und prüft den Zugriff — gleiches Muster
    wie in `drohne_aktiv_setzen`: 404 statt 403, ein Spieler soll nicht
    erfahren, ob eine fremde Drohne überhaupt existiert."""
    drohne = await repository.get_node("Person", PERSON_FIELDS, campaign_id, node_id)
    if drohne is None or not (drohne.get("istDrohne") or drohne.get("istFahrzeug")):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")

    rigger_id = await repository.drohne_rigger(campaign_id, node_id)
    if viewer.role != "GM" and (rigger_id is None or rigger_id != viewer.person_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")
    return drohne, rigger_id


@router.get("/drohnen/{node_id}/steigern")
async def drohne_steigerungspreise(
    campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)
) -> dict:
    """Was der nächste Punkt auf jedem Drohnen-/Fahrzeug-Wert in Nuyen kostet.

    Bezahlt wird aus dem Kapital des RIGGERS, nicht der Drohne — die hat
    kein eigenes Kapital (Mark, 25.10.2026: "Der Rigger zahlt es aus seinem
    Kapitel, die Drohne hat keins!"). `verfuegbar` zeigt deshalb
    `kapitalBasis` des Riggers; ohne gebundenen Rigger ist nichts kaufbar.
    """
    drohne, rigger_id = await _drohne_und_rigger_oder_404(campaign_id, node_id, viewer)

    einstellungen = await get_einstellungen(campaign_id)
    nuyen_pro_xp = int(einstellungen.get("nuyenProXp") or 0)

    campaign = await get_campaign(campaign_id)
    katalog = await traits_repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
    erlaubt = sichtbare_kategorien(drohne.get("weg") or "KEINER", {t["category"] for t in katalog}, False, True)

    werte = await traits_repository.get_ratings_for_entity(campaign_id, node_id)
    nach_name = {w["name"]: w["rating"] for w in werte}
    grenzen = {w["traitDefId"]: w["max"] for w in werte}

    preise = []
    for eintrag in katalog:
        if eintrag["category"] not in erlaubt:
            continue
        # Eine Drohne riggt sich nicht selbst — siehe
        # traits/drohnen.py::DROHNE_GESPERRTE_FERTIGKEITEN.
        if eintrag["name"] in DROHNE_GESPERRTE_FERTIGKEITEN:
            continue
        aktuell = nach_name.get(eintrag["name"], 0)
        preis = erfahrung.nuyen_kosten(eintrag["category"], aktuell, nuyen_pro_xp)
        if preis is None:
            continue
        preise.append(
            {
                "traitDefId": eintrag["id"],
                "name": eintrag["name"],
                "category": eintrag["category"],
                "aktuell": aktuell,
                "max": grenzen.get(eintrag["id"], eintrag["defaultMax"]),
                "kosten": preis,
            }
        )

    # Zusatzfertigkeiten (26.10.2026): campaign-gebundener Katalog, läuft
    # nicht über TraitDef/list_catalog — separat angehängt, Id-Präfix "zf:"
    # unterscheidet sie beim Kauf (siehe drohne_steigern unten). Dieselbe
    # Nuyen-Formel wie normale Fertigkeiten (erfahrung.kosten("Fertigkeit", ...)
    # im EP-Pendant, siehe zusatzfertigkeiten/routes.py).
    zf_katalog = await zf_repository.liste(campaign_id)
    zf_gewaehlt = {z["id"]: z for z in await zf_repository.zusatzfertigkeiten_der_person(campaign_id, node_id)}
    for zf in zf_katalog:
        gewaehlt = zf_gewaehlt.get(zf["id"])
        aktuell = gewaehlt["rating"] if gewaehlt else 0
        preis = erfahrung.nuyen_kosten("Fertigkeit", aktuell, nuyen_pro_xp)
        if preis is None:
            continue
        preise.append(
            {
                "traitDefId": f"zf:{zf['id']}",
                "name": zf["name"],
                "category": "Zusatzfertigkeit",
                "aktuell": aktuell,
                "max": 6,
                "kosten": preis,
            }
        )

    rigger_kapital = 0
    if rigger_id:
        rigger = await repository.get_node("Person", PERSON_FIELDS, campaign_id, rigger_id)
        rigger_kapital = int(rigger.get("kapitalBasis") or 0) if rigger else 0

    return {"riggerId": rigger_id, "verfuegbar": rigger_kapital, "nuyenProXp": nuyen_pro_xp, "werte": preise}


@router.post("/drohnen/{node_id}/steigern")
async def drohne_steigern(
    campaign_id: str,
    node_id: str,
    body: DrohneSteigernInput,
    viewer: Viewer = Depends(get_viewer),
) -> dict:
    """Einen Punkt an einer Drohne/einem Fahrzeug kaufen — TraitDef ODER
    Zusatzfertigkeit (Id-Präfix "zf:", siehe drohne_steigerungspreise).

    Bezahlt der RIGGER, entweder aus eigenem Kapital (`kapitalBasis`) ODER
    mit einem eigenen Maschinenteil statt Nuyen (26.10.2026,
    `materialGegenstandId`, siehe `maschinenteil_reicht`) — nie beides. Der
    Preis wird hier neu berechnet und nicht vom Client übernommen, gleiche
    Logik wie beim EP-Pendant `steigere_wert` in `traits/routes.py`.
    """
    drohne, rigger_id = await _drohne_und_rigger_oder_404(campaign_id, node_id, viewer)
    if rigger_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Diese Drohne/dieses Fahrzeug hat keinen Rigger.")

    rigger = await repository.get_node("Person", PERSON_FIELDS, campaign_id, rigger_id)
    if rigger is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rigger nicht gefunden")

    ist_zusatzfertigkeit = body.traitDefId.startswith("zf:")
    gewaehlte_zf = None
    if ist_zusatzfertigkeit:
        zf_id = body.traitDefId[len("zf:") :]
        zusatzfertigkeit = await zf_repository.hole(campaign_id, zf_id)
        if zusatzfertigkeit is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Zusatzfertigkeit nicht gefunden")
        name = zusatzfertigkeit["name"]
        category = "Zusatzfertigkeit"
        gewaehlte_zf = next(
            (z for z in await zf_repository.zusatzfertigkeiten_der_person(campaign_id, node_id) if z["id"] == zf_id),
            None,
        )
        aktuell = gewaehlte_zf["rating"] if gewaehlte_zf else 0
        grenze = 6
    else:
        campaign = await get_campaign(campaign_id)
        katalog = await traits_repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
        eintrag = next((t for t in katalog if t["id"] == body.traitDefId), None)
        if eintrag is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Wert nicht gefunden")
        # Eine Drohne riggt sich nicht selbst — dieselbe Sperre wie in der
        # Preisliste, hier zusätzlich serverseitig gegen direkte POSTs.
        if eintrag["name"] in DROHNE_GESPERRTE_FERTIGKEITEN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"{eintrag['name']} steht einer Drohne/einem Fahrzeug nicht offen.")
        erlaubt = sichtbare_kategorien(drohne.get("weg") or "KEINER", {t["category"] for t in katalog}, False, True)
        if eintrag["category"] not in erlaubt:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Dieser Wert steht dieser Drohne/diesem Fahrzeug nicht offen.")
        name = eintrag["name"]
        category = eintrag["category"]
        werte = await traits_repository.get_ratings_for_entity(campaign_id, node_id)
        nach_name = {w["name"]: w["rating"] for w in werte}
        aktuell = nach_name.get(name, 0)
        grenze = next((w["max"] for w in werte if w["traitDefId"] == body.traitDefId), eintrag["defaultMax"])

    if aktuell >= grenze:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{name} steht bereits auf {grenze}.")

    einstellungen = await get_einstellungen(campaign_id)
    nuyen_pro_xp = int(einstellungen.get("nuyenProXp") or 0)
    preis = erfahrung.nuyen_kosten("Fertigkeit" if ist_zusatzfertigkeit else category, aktuell, nuyen_pro_xp)
    if preis is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dieser Wert lässt sich nicht steigern.")

    # Zahlung: entweder Nuyen aus dem Rigger-Kapital ODER ein Maschinenteil
    # aus dessen Besitz (26.10.2026, docs/wiki/concepts/drohnen-fahrzeuge.md).
    material = None
    if body.materialGegenstandId:
        material = await items_repository.get_gegenstand(campaign_id, body.materialGegenstandId)
        if material is None or not material.get("istMaschinenteil"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Maschinenteil.")
        besitzer_id = await items_repository.get_owner_person_id(campaign_id, body.materialGegenstandId)
        if besitzer_id != rigger_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Maschinenteil gehört nicht dem Rigger.")
        if material.get("menge", 1) <= 0:
            raise HTTPException(status.HTTP_409_CONFLICT, "Dieses Maschinenteil ist aufgebraucht.")
        if not maschinenteil_reicht(material.get("maschinenteilQualitaet") or "", "Fertigkeit" if ist_zusatzfertigkeit else category):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Ein {material.get('maschinenteilQualitaet') or 'unbrauchbares'} Maschinenteil reicht dafür nicht.",
            )

    kapital = int(rigger.get("kapitalBasis") or 0)
    if material is None and not kann_bezahlen(preis, kapital):
        raise HTTPException(status.HTTP_409_CONFLICT, f"{preis}¥ nötig, {kapital}¥ beim Rigger vorhanden.")

    if ist_zusatzfertigkeit:
        if gewaehlte_zf is None:
            await zf_repository.hinzufuegen(campaign_id, node_id, zf_id, 1)
        else:
            await zf_repository.steigere(campaign_id, node_id, zf_id, aktuell + 1)
    else:
        await traits_repository.steigere(campaign_id, node_id, body.traitDefId, aktuell + 1)

    if material is not None:
        neue_menge = max(0, material["menge"] - 1)
        await items_repository.update_gegenstand(campaign_id, body.materialGegenstandId, {"menge": neue_menge})
        kapital_neu = kapital
        sl_notiz = f"Bezahlt mit Maschinenteil {material['name']} (verbraucht, Rigger {rigger.get('name', '')})"
    else:
        kapital_neu = kapital - preis
        await repository.update_node("Person", PERSON_FIELDS, campaign_id, rigger_id, {"kapitalBasis": kapital_neu})
        sl_notiz = f"Bezahlt vom Rigger {rigger.get('name', '')} ({preis}¥ aus dessen Kapital)"

    # Ereignisprotokoll: dieselbe CharakterEntwicklung-Art wie beim EP-Kauf,
    # SL-Notiz macht die abweichende Bezahlquelle (Rigger statt eigene XP)
    # auf einen Blick erkennbar.
    await hooks.charakterentwicklung(
        campaign_id,
        person_id=node_id,
        art="STEIGERUNG",
        trait_def_id=body.traitDefId,
        trait_name=name,
        alt=str(aktuell),
        neu=str(aktuell + 1),
        kosten_oder_menge=preis,
        sl_notiz=sl_notiz,
    )

    drohne_frisch = await repository.get_node("Person", PERSON_FIELDS, campaign_id, node_id)
    return {"drohne": drohne_frisch, "riggerKapitalBasis": kapital_neu}


@router.get("/drohnen/{node_id}/maschinenteile")
async def drohne_maschinenteile(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)) -> list[dict]:
    """Maschinenteile im Besitz DES RIGGERS (nicht der Drohne — die hat
    keinen eigenen Besitz, siehe drohne_steigerungspreise) — für die
    Zahlungsauswahl beim Umbau."""
    _, rigger_id = await _drohne_und_rigger_oder_404(campaign_id, node_id, viewer)
    if rigger_id is None:
        return []
    return await items_repository.list_maschinenteile_von(campaign_id, rigger_id)


@router.get("/ki", response_model=list[dict])
async def list_ki(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """KIs für die Begleiter-Übersicht — dasselbe Muster wie `list_critter`,
    KI ist seit 20.09.2026 (revidiert) ebenfalls eine echte Person
    (`istKI=true`) statt einer Begleiter-Art."""
    roh = await repository.list_ki(campaign_id)
    sichtbar = [
        c for c in roh
        if is_visible_to(c.get("sichtbarkeit") or "GM", c.get("sichtbarFuer") or [], viewer.role, viewer.person_id)
    ]
    return sichtbar


@router.post("/ki/{node_id}/besitzer", response_model=dict, dependencies=[Depends(require_campaign_gm)])
async def ki_besitzer_setzen(campaign_id: str, node_id: str, body: dict):
    person_id = body.get("personId")
    ergebnis = await repository.ki_besitzer_setzen(campaign_id, node_id, person_id)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "KI nicht gefunden")
    return ergebnis


@router.get("/personen/{node_id}/einfluss", response_model=list[EinflussEintrag])
async def person_einfluss_liste(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    return await repository.person_einfluss_liste(campaign_id, node_id)


@router.post(
    "/personen/{node_id}/einfluss", response_model=list[EinflussEintrag], dependencies=[Depends(require_campaign_gm)]
)
async def person_einfluss_setzen(campaign_id: str, node_id: str, body: EinflussSetzen):
    """Setzt die Einfluss-Stufe einer Person (typischerweise einer KI) auf
    einen Ort/eine Fraktion/ein Event/einen Gegenstand — echte Graphkante,
    damit die Spielleitung sie im Kampf gezielt kappen kann. **Nur SL.**"""
    ergebnis = await repository.person_einfluss_setzen(campaign_id, node_id, body.zielKind, body.zielId, body.stufe)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person oder Ziel nicht gefunden")
    return ergebnis


@router.delete(
    "/personen/{node_id}/einfluss/{ziel_kind}/{ziel_id}",
    response_model=list[EinflussEintrag],
    dependencies=[Depends(require_campaign_gm)],
)
async def person_einfluss_entfernen(campaign_id: str, node_id: str, ziel_kind: str, ziel_id: str):
    ergebnis = await repository.person_einfluss_entfernen(campaign_id, node_id, ziel_kind, ziel_id)
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person oder Einflussbereich nicht gefunden")
    return ergebnis


@router.post("/orte", response_model=OrtResponse, dependencies=[Depends(require_campaign_gm)])
async def create_ort(campaign_id: str, body: OrtCreate):
    return await repository.create_node("Ort", ORT_FIELDS, campaign_id, body.model_dump())


@router.get("/orte", response_model=list[OrtResponse])
async def list_orte(
    campaign_id: str,
    suche: str | None = Query(default=None, description="Sucht in Name, Beschreibung und Notizen."),
    sortierung: filterung.Sortierung | None = Query(default=None),
    verbundenMit: str | None = Query(default=None),
    verbindungsTyp: str | None = Query(default=None),
    viewer: Viewer = Depends(get_viewer),
):
    nodes = await repository.list_nodes("Ort", ORT_FIELDS, campaign_id)
    return await _aufbereiten(
        nodes,
        campaign_id,
        viewer,
        namensfeld="name",
        suche=suche,
        sortierung=sortierung,
        verbunden_mit=verbundenMit,
        verbindungs_typ=verbindungsTyp,
    )


@router.get("/entwuerfe", response_model=list[dict])
async def list_entwuerfe(
    campaign_id: str,
    viewer: Viewer = Depends(get_viewer),
):
    """Gibt alle Entwürfe (istEntwurf=true) für die Ideenschmiede zurück."""
    from app.entities import repository
    
    # Alle Entity-Typen sammeln
    entwuerfe = []
    
    # Personen-Entwürfe
    personen = await repository.list_nodes("Person", repository.PERSON_FIELDS, campaign_id)
    for p in personen:
        if p.get("istEntwurf", False):
            p["typ"] = "person"
            entwuerfe.append(p)
    
    # Orte-Entwürfe
    orte = await repository.list_nodes("Ort", repository.ORT_FIELDS, campaign_id)
    for o in orte:
        if o.get("istEntwurf", False):
            o["typ"] = "ort"
            entwuerfe.append(o)
    
    # Events-Entwürfe
    events = await repository.list_nodes("Event", repository.EVENT_FIELDS, campaign_id)
    for e in events:
        if e.get("istEntwurf", False):
            e["typ"] = "event"
            entwuerfe.append(e)
    
    # Fraktions-Entwürfe
    fraktionen = await repository.list_nodes("Fraktion", repository.FRAKTION_FIELDS, campaign_id)
    for f in fraktionen:
        if f.get("istEntwurf", False):
            f["typ"] = "Fraktion"
            entwuerfe.append(f)
    
    # Wiki-Seiten-Entwürfe
    from app.wiki import repository as wiki_repository
    seiten = await wiki_repository.list_seiten(campaign_id)
    for s in seiten:
        if s.get("istEntwurf", False):
            s["typ"] = "WikiSeite"
            s["name"] = s.get("titel", "Unbenannt")
            entwuerfe.append(s)
    
    # Gegenstands-Entwürfe
    from app.items import repository as items_repository
    gegenstaende = await items_repository.list_alle_gegenstaende(campaign_id)
    for g in gegenstaende:
        if g.get("istEntwurf", False):
            g["typ"] = "Gegenstand"
            entwuerfe.append(g)
    
    # Nach Sichtbarkeit filtern
    sichtbar = filter_entities_for_viewer(entwuerfe, viewer.role, viewer.person_id)
    return sichtbar


@router.get("/orte/{node_id}", response_model=OrtResponse)
async def get_ort(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Ort", ORT_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Ort")


@router.patch("/orte/{node_id}", response_model=OrtResponse, dependencies=[Depends(require_campaign_gm)])
async def update_ort(campaign_id: str, node_id: str, body: OrtUpdate):
    node = await repository.update_node("Ort", ORT_FIELDS, campaign_id, node_id, body.model_dump())
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ort nicht gefunden")
    if body.sichtbarkeit is not None:
        await lexikon_hooks.campaign_weit_neu_berechnen(campaign_id)
    return node


@router.delete("/orte/{node_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_ort(campaign_id: str, node_id: str):
    if not await repository.delete_node("Ort", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ort nicht gefunden")


@router.post("/events", response_model=EventResponse, dependencies=[Depends(require_campaign_gm)])
async def create_event(campaign_id: str, body: EventCreate):
    return await repository.create_node("Event", EVENT_FIELDS, campaign_id, body.model_dump())


@router.get("/events", response_model=list[EventResponse])
async def list_events(
    campaign_id: str,
    suche: str | None = Query(default=None, description="Sucht in Titel, Zeitpunkt, Beschreibung und Notizen."),
    sortierung: filterung.Sortierung | None = Query(default=None),
    verbundenMit: str | None = Query(default=None),
    verbindungsTyp: str | None = Query(default=None),
    viewer: Viewer = Depends(get_viewer),
):
    nodes = await repository.list_nodes("Event", EVENT_FIELDS, campaign_id, order_field="title")
    return await _aufbereiten(
        nodes,
        campaign_id,
        viewer,
        namensfeld="title",
        suche=suche,
        sortierung=sortierung,
        verbunden_mit=verbundenMit,
        verbindungs_typ=verbindungsTyp,
    )


@router.get("/events/{node_id}", response_model=EventResponse)
async def get_event(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Event", EVENT_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Event")


@router.patch("/events/{node_id}", response_model=EventResponse, dependencies=[Depends(require_campaign_gm)])
async def update_event(campaign_id: str, node_id: str, body: EventUpdate):
    node = await repository.update_node("Event", EVENT_FIELDS, campaign_id, node_id, body.model_dump())
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event nicht gefunden")
    if body.sichtbarkeit is not None:
        await lexikon_hooks.campaign_weit_neu_berechnen(campaign_id)
    return node


@router.delete("/events/{node_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_event(campaign_id: str, node_id: str):
    if not await repository.delete_node("Event", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event nicht gefunden")


@router.post("/fraktionen", response_model=FraktionResponse, dependencies=[Depends(require_campaign_gm)])
async def create_fraktion(campaign_id: str, body: FraktionCreate):
    return await repository.create_node("Fraktion", FRAKTION_FIELDS, campaign_id, body.model_dump())


@router.get("/fraktionen", response_model=list[FraktionResponse])
async def list_fraktionen(
    campaign_id: str,
    suche: str | None = Query(default=None, description="Sucht in Name, Beschreibung und Notizen."),
    sortierung: filterung.Sortierung | None = Query(default=None),
    verbundenMit: str | None = Query(default=None),
    verbindungsTyp: str | None = Query(default=None),
    viewer: Viewer = Depends(get_viewer),
):
    nodes = await repository.list_nodes("Fraktion", FRAKTION_FIELDS, campaign_id)
    return await _aufbereiten(
        nodes,
        campaign_id,
        viewer,
        namensfeld="name",
        suche=suche,
        sortierung=sortierung,
        verbunden_mit=verbundenMit,
        verbindungs_typ=verbindungsTyp,
    )


@router.get("/fraktionen/{node_id}", response_model=FraktionResponse)
async def get_fraktion(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Fraktion", FRAKTION_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Fraktion")


@router.patch("/fraktionen/{node_id}", response_model=FraktionResponse, dependencies=[Depends(require_campaign_gm)])
async def update_fraktion(campaign_id: str, node_id: str, body: FraktionUpdate):
    node = await repository.update_node("Fraktion", FRAKTION_FIELDS, campaign_id, node_id, body.model_dump())
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fraktion nicht gefunden")
    if body.sichtbarkeit is not None:
        await lexikon_hooks.campaign_weit_neu_berechnen(campaign_id)
    return node


@router.delete("/fraktionen/{node_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_fraktion(campaign_id: str, node_id: str):
    if not await repository.delete_node("Fraktion", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fraktion nicht gefunden")


# --- Gewächs (Flora & Fauna) ----------------------------------------------
# Exakt dasselbe generische Muster wie Ort/Event/Fraktion oben — bewusst kein
# eigener Mechanismus, siehe entities/repository.py::GEWAECHS_FIELDS.

@router.post("/gewaechse", response_model=GewaechsResponse, dependencies=[Depends(require_campaign_gm)])
async def create_gewaechs(campaign_id: str, body: GewaechsCreate):
    return await repository.create_node("Gewaechs", GEWAECHS_FIELDS, campaign_id, body.model_dump())


@router.get("/gewaechse", response_model=list[GewaechsResponse])
async def list_gewaechse(
    campaign_id: str,
    suche: str | None = Query(default=None, description="Sucht in Name, Beschreibung und Notizen."),
    sortierung: filterung.Sortierung | None = Query(default=None),
    viewer: Viewer = Depends(get_viewer),
):
    nodes = await repository.list_nodes("Gewaechs", GEWAECHS_FIELDS, campaign_id)
    return await _aufbereiten(
        nodes,
        campaign_id,
        viewer,
        namensfeld="name",
        suche=suche,
        sortierung=sortierung,
    )


@router.get("/gewaechse/{node_id}", response_model=GewaechsResponse)
async def get_gewaechs(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    node = await repository.get_node("Gewaechs", GEWAECHS_FIELDS, campaign_id, node_id)
    return _visible_or_404(node, viewer, "Gewächs")


@router.patch("/gewaechse/{node_id}", response_model=GewaechsResponse, dependencies=[Depends(require_campaign_gm)])
async def update_gewaechs(campaign_id: str, node_id: str, body: GewaechsUpdate):
    node = await repository.update_node("Gewaechs", GEWAECHS_FIELDS, campaign_id, node_id, body.model_dump())
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gewächs nicht gefunden")
    if body.sichtbarkeit is not None:
        await lexikon_hooks.campaign_weit_neu_berechnen(campaign_id)
    return node


@router.delete("/gewaechse/{node_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_gewaechs(campaign_id: str, node_id: str):
    if not await repository.delete_node("Gewaechs", campaign_id, node_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gewächs nicht gefunden")


# --- Flora & Fauna (LEBT_IN) ----------------------------------------------
# Dasselbe Rückgabe-Muster wie person_einfluss_setzen/-entfernen oben: jede
# Mutation liefert die frische, komplette Liste zurück statt nur eines
# Erfolgs-Flags — der Aufrufer (Ort-Detail-Tab) braucht sie direkt danach
# sowieso wieder.

@router.get("/orte/{ort_id}/flora-fauna", response_model=list[LebtInEintrag])
async def flora_fauna_liste(campaign_id: str, ort_id: str, viewer: Viewer = Depends(get_viewer)):
    roh = await repository.lebt_in_liste_fuer_ort(campaign_id, ort_id)
    return [
        e for e in roh
        if is_visible_to(e.get("sichtbarkeit") or "GM", e.get("sichtbarFuer") or [], viewer.role, viewer.person_id)
    ]


@router.post(
    "/orte/{ort_id}/flora-fauna", response_model=list[LebtInEintrag], dependencies=[Depends(require_campaign_gm)]
)
async def flora_fauna_hinzufuegen(campaign_id: str, ort_id: str, body: LebtInHinzufuegen):
    ok = await repository.lebt_in_hinzufuegen(campaign_id, ort_id, body.artId)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ort oder Critter/Gewächs nicht gefunden")
    await lexikon_hooks.campaign_weit_neu_berechnen(campaign_id)
    return await repository.lebt_in_liste_fuer_ort(campaign_id, ort_id)


@router.delete(
    "/orte/{ort_id}/flora-fauna/{art_id}",
    response_model=list[LebtInEintrag],
    dependencies=[Depends(require_campaign_gm)],
)
async def flora_fauna_entfernen(campaign_id: str, ort_id: str, art_id: str):
    await repository.lebt_in_entfernen(campaign_id, ort_id, art_id)
    return await repository.lebt_in_liste_fuer_ort(campaign_id, ort_id)


@router.get("/flora-fauna/{art_id}/orte", response_model=list[LebtInOrtEintrag])
async def flora_fauna_orte(campaign_id: str, art_id: str, viewer: Viewer = Depends(get_viewer)):
    """Reverse-Lookup: an welchen Orten dieser Critter/dieses Gewächs vorkommt.

    Bewusst ungefiltert nach Sichtbarkeit des Ortes — dieselbe Abwägung wie
    bei `list_critter`: wer den Critter/das Gewächs selbst schon sehen darf,
    darf auch wissen, wo er/es vorkommt.
    """
    return await repository.lebt_in_liste_fuer_art(campaign_id, art_id)


@router.post("/verbindungen", response_model=VerbindungResponse, dependencies=[Depends(require_campaign_gm)])
async def create_verbindung(campaign_id: str, body: VerbindungCreate):
    edge = await repository.create_verbindung(campaign_id, body.model_dump())
    if edge is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Start- oder Zielentität nicht gefunden")
    # Neue Kante kann fuer beliebige PCs neue Entdeckungspfade oeffnen —
    # campaignweiter Neulauf statt Versuch, die betroffenen PCs vorab
    # einzugrenzen (siehe Begruendung in lexikon/hooks.py).
    await lexikon_hooks.campaign_weit_neu_berechnen(campaign_id)
    return edge


@router.get("/verbindungen", response_model=list[VerbindungResponse])
async def list_verbindungen(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    edges = await repository.list_verbindungen(campaign_id)
    return filter_verbindungen_for_viewer(edges, viewer.role, viewer.person_id)


@router.patch("/verbindungen/{edge_id}", response_model=VerbindungResponse, dependencies=[Depends(require_campaign_gm)])
async def update_verbindung(campaign_id: str, edge_id: str, body: VerbindungUpdate):
    edge = await repository.update_verbindung(campaign_id, edge_id, body.model_dump())
    if edge is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verbindung nicht gefunden")
    # Sichtbarkeit der Kante kann sich geaendert haben (z.B. SL gibt sie
    # frei) — betrifft potenziell jeden PC, daher derselbe Neulauf wie beim
    # Anlegen.
    await lexikon_hooks.campaign_weit_neu_berechnen(campaign_id)
    return edge


# Beschriftung eines Filterziels. Gegenstände erscheinen nur, wenn sie
# ausdrücklich im Graph geführt werden (MacGuffins) — normale Inventarstücke
# würden die Auswahl überschwemmen.
_FILTER_QUELLEN: tuple[tuple[str, list[str], str], ...] = (
    ("Person", PERSON_FIELDS, "name"),
    ("Ort", ORT_FIELDS, "name"),
    ("Event", EVENT_FIELDS, "title"),
    ("Fraktion", FRAKTION_FIELDS, "name"),
)


async def _beschriftungen(campaign_id: str, viewer: Viewer) -> dict[str, tuple[str, str]]:
    """ID → (Art, Name) für alles, was dieser Blickwinkel sehen darf.

    Sichtbarkeitsgefiltert, weil die Beschriftung sonst den Namen eines
    geheimen NPCs im Filter-Dropdown offenlegte — dieselbe Überlegung wie beim
    Kampf-Alias.
    """
    beschriftung: dict[str, tuple[str, str]] = {}
    for label, felder, namensfeld in _FILTER_QUELLEN:
        knoten = await repository.list_nodes(label, felder, campaign_id, order_field=namensfeld)
        for eintrag in filter_entities_for_viewer(knoten, viewer.role, viewer.person_id):
            beschriftung[eintrag["id"]] = (label, str(eintrag.get(namensfeld) or ""))
    return beschriftung


@router.get("/filteroptionen", response_model=FilterOptionen)
async def get_filteroptionen(
    campaign_id: str,
    art: Literal["personen", "orte", "events", "fraktionen"] = Query(
        description="Für welche Liste die Optionen gelten sollen."
    ),
    personType: Literal["PC", "NPC"] | None = Query(default=None),
    viewer: Viewer = Depends(get_viewer),
):
    """Welche Beziehungsarten und Ziele es für diese Liste wirklich gibt.

    Speist die Filterauswahl der Oberfläche. Bewusst serverseitig: das
    Frontend soll nicht aus einer ungefilterten Kantenliste ableiten müssen,
    was es anbieten darf — und ohne diese Route müsste es dafür alle
    Verbindungen laden, auch die, die es gar nicht sehen darf.
    """
    label, felder, namensfeld = {
        "personen": ("Person", PERSON_FIELDS, "name"),
        "orte": ("Ort", ORT_FIELDS, "name"),
        "events": ("Event", EVENT_FIELDS, "title"),
        "fraktionen": ("Fraktion", FRAKTION_FIELDS, "name"),
    }[art]

    knoten = await repository.list_nodes(label, felder, campaign_id, order_field=namensfeld)
    if personType is not None:
        knoten = [n for n in knoten if n.get("personType") == personType]
    sichtbar = filter_entities_for_viewer(knoten, viewer.role, viewer.person_id)

    kanten = await _sichtbare_kanten(campaign_id, viewer)
    beschriftung = await _beschriftungen(campaign_id, viewer)
    return filterung.filteroptionen(sichtbar, kanten, beschriftung)


@router.delete("/verbindungen/{edge_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def delete_verbindung(campaign_id: str, edge_id: str):
    if not await repository.delete_verbindung(campaign_id, edge_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verbindung nicht gefunden")


# --- Bilder ------------------------------------------------------------
# Aussehen einer Person, eines Ortes oder einer Szene. Die Spielleitung kann
# es per Blitz an alle Spieler schicken (app/mitteilungen).
#
# Gleiche Ablage wie die Gegenstandsbilder (uploads/<campaign_id>/): beim
# Sichern gibt es nur einen Ordner.

UPLOAD_DIR = Path("uploads")
ERLAUBTE_BILDTYPEN = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_BILD_BYTES = 8 * 1024 * 1024

# Welches Label und welche Felder hinter einem Pfadsegment stehen. Weisse
# Liste, weil das Label direkt in die Cypher-Abfrage eingeht.
_ENTITAETEN = {
    "personen": ("Person", PERSON_FIELDS, "Person"),
    "orte": ("Ort", ORT_FIELDS, "Ort"),
    "events": ("Event", EVENT_FIELDS, "Event"),
    "fraktionen": ("Fraktion", FRAKTION_FIELDS, "Fraktion"),
    "gewaechse": ("Gewaechs", GEWAECHS_FIELDS, "Gewächs"),
}


@router.post("/personen/{node_id}/bild", dependencies=[Depends(require_campaign_gm)])
async def upload_person_bild(campaign_id: str, node_id: str, file: UploadFile = File(...)):
    return await _entitaets_bild_hochladen(campaign_id, "personen", node_id, file)


@router.post("/orte/{node_id}/bild", dependencies=[Depends(require_campaign_gm)])
async def upload_ort_bild(campaign_id: str, node_id: str, file: UploadFile = File(...)):
    return await _entitaets_bild_hochladen(campaign_id, "orte", node_id, file)


@router.post("/events/{node_id}/bild", dependencies=[Depends(require_campaign_gm)])
async def upload_event_bild(campaign_id: str, node_id: str, file: UploadFile = File(...)):
    return await _entitaets_bild_hochladen(campaign_id, "events", node_id, file)


@router.post("/fraktionen/{node_id}/bild", dependencies=[Depends(require_campaign_gm)])
async def upload_fraktion_bild(campaign_id: str, node_id: str, file: UploadFile = File(...)):
    return await _entitaets_bild_hochladen(campaign_id, "fraktionen", node_id, file)


@router.post("/gewaechse/{node_id}/bild", dependencies=[Depends(require_campaign_gm)])
async def upload_gewaechs_bild(campaign_id: str, node_id: str, file: UploadFile = File(...)):
    return await _entitaets_bild_hochladen(campaign_id, "gewaechse", node_id, file)


async def _entitaets_bild_hochladen(campaign_id: str, art: str, node_id: str, file: UploadFile) -> dict:
    # Vier explizite Routen statt einer mit `{art}`: eine generische Route
    # würde auch `/rassen/{id}/bild` abfangen und "Unbekannte Entität"
    # antworten, weil der entities-Router vor dem Rassen-Router registriert ist.
    label, felder, bezeichnung = _ENTITAETEN[art]

    if file.content_type not in ERLAUBTE_BILDTYPEN:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Bilddateien (PNG/JPEG/WEBP/GIF) erlaubt")

    inhalt = await file.read()
    if len(inhalt) > MAX_BILD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 8 MB)")

    if await repository.get_node(label, felder, campaign_id, node_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{bezeichnung} nicht gefunden")

    ordner = UPLOAD_DIR / campaign_id
    ordner.mkdir(parents=True, exist_ok=True)
    endung = mimetypes.guess_extension(file.content_type) or ""
    # Neuer Name: ein hochgeladener Name koennte aus dem Ordner ausbrechen.
    name = f"{art}-{uuid.uuid4()}{endung}"
    (ordner / name).write_bytes(inhalt)

    aktualisiert = await repository.update_node(
        label, felder, campaign_id, node_id, {"bildUrl": f"/uploads/{campaign_id}/{name}"}
    )
    if aktualisiert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{bezeichnung} nicht gefunden")
    return aktualisiert
