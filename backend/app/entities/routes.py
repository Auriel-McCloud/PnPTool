import mimetypes
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field, field_validator

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_campaign, get_einstellungen
from app.entities import repository
from app.entities import filterung
from app.ereignisprotokoll import hooks
from app.lexikon import hooks as lexikon_hooks
from app.entities.repository import EVENT_FIELDS, FRAKTION_FIELDS, GEWAECHS_FIELDS, ORT_FIELDS, PERSON_FIELDS
from app.items import repository as items_repository
from app.items.schemas import GegenstandCreate
from app.traits import repository as traits_repository
from app.traits import erfahrung
from app.traits import erstellung
from app.traits.bogen import GESUNDHEIT_GRUNDWERT, gesundheit_max, sichtbare_kategorien
from app.traits.drohnen import (
    DROHNE_GESPERRTE_FERTIGKEITEN,
    benoetigte_erfolge_maker_probe,
    kann_aktivieren,
    kann_bezahlen,
    maschinenteil_reicht,
)
from app.kampf.ruestung import (
    REPARATUR_SKILLS,
    anwende_natuerliche_ruestung,
    heile_gesundheitsschaden,
    reparatur_benoetigte_erfolge,
    reparatur_heilung_material,
)
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
    person = await repository.create_node("Person", PERSON_FIELDS, campaign_id, body.model_dump())
    if person and (person.get("istDrohne") or person.get("istFahrzeug")):
        person = await _drohnen_startausstattung(campaign_id, person)
    return person


async def _drohnen_startausstattung(campaign_id: str, person: dict) -> dict:
    """Neu angelegte Drohnen/Fahrzeuge bekommen ihre Grundausstattung
    automatisch (26.10.2026, Mark, nach dem ersten echten Spieltisch-Test).

    **3 Lebenspunkte-Basiswert statt des globalen `GESUNDHEIT_GRUNDWERT`
    (6):** der globale Wert ist für Menschen/Critter gedacht (siehe
    `traits/bogen.py::GESUNDHEIT_GRUNDWERT`); nur wenn `gesundheitGrundwert`
    noch auf dem Sentinel `-1` steht (kein expliziter Override mitgegeben,
    `entities/schemas.py::PersonCreate`), wird er auf 3 gesetzt — ein
    Aufrufer, der ausdrücklich einen anderen Wert übergeben hat, wird nicht
    überschrieben.

    **Außenhülle-Rüstung nach dem Natürliche-Rüstung-Prinzip** (Mark: "wir
    verwenden das gleiche System wie bei Natürlicher Rüstung, die
    Widerstandspunkte sind die Rüstungskästchen, und die Außenhülle ist die
    Reduktion"): automatisch erzeugtes, `istNatuerlich=true`-Item, genau wie
    Dug'Rahs Chitinpanzer — läuft dadurch ohne jede Parallelimplementierung
    im bestehenden Rüstungspool/der bestehenden Reparatur mit (siehe
    `kampf/ruestung.py::anwende_natuerliche_ruestung`, das für Drohnen jetzt
    zusätzlich die Reduktion live aus der Außenhülle-Rating setzt). Beide
    Live-Werte starten bei 0 (frische Drohne hat noch keine Punkte verteilt)
    und wachsen automatisch mit, sobald im Umbauen-Reiter gesteigert wird —
    keine zweite Pflegestelle nötig.

    Bewusst NICHT Teil davon: ein eigenes Reparatur-statt-Rasten-Heilsystem
    für die Lebenspunkte selbst (Mark: "das bauen wir danach", eigenständiges
    Folge-Feature mit Minderwertig-Material-Verbrauch).
    """
    aktualisiert = person
    if person.get("gesundheitGrundwert") in (None, -1):
        neu = await repository.update_node(
            "Person", PERSON_FIELDS, campaign_id, person["id"], {"gesundheitGrundwert": 3}
        )
        if neu is not None:
            aktualisiert = neu
    await items_repository.create_gegenstand(
        campaign_id,
        person["id"],
        GegenstandCreate(
            name="Außenhülle",
            description="Eingebaute Panzerung — Kästchen/Reduktion wachsen automatisch mit "
            "Widerstandsfähigkeit/Außenhülle mit, kein eigenes Item zum An-/Ablegen.",
            typ="Rüstung",
            istNatuerlich=True,
            einzigartig=False,
            ablage="AUSGERUESTET",
            sichtbarkeit="GM",
            sichtbarFuer=[],
        ).model_dump(),
    )
    return aktualisiert


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
    if node is not None and viewer.role != "GM":
        # Dieselbe Besitzer-Ausnahme wie traits/routes.py::_darf_person_sehen
        # (Rigger sieht seine Drohne, Beschwörer sieht seinen Critter, auch
        # wenn die allgemeine Sichtbarkeit auf GM steht) — ohne das blieb das
        # Critter-Bild in der Beschwörungs-Probe für den Spieler unsichtbar,
        # weil dieser Endpunkt (anders als get_bogen) den Besitz nie prüfte
        # (Mark, 30.10.2026).
        eigene_drohne_oder_critter = False
        if node.get("istDrohne") or node.get("istFahrzeug"):
            eigene_drohne_oder_critter = await repository.drohne_rigger(campaign_id, node_id) == viewer.person_id
        elif node.get("istCritter"):
            eigene_drohne_oder_critter = await repository.critter_besitzer(campaign_id, node_id) == viewer.person_id
        if eigene_drohne_oder_critter:
            # node["id"] als eigener viewer_person_id vorgetäuscht, damit
            # filter_entity_for_viewer dieselbe "eigener Charakter"-Behandlung
            # anwendet (Redaktion bleibt dieselbe wie beim eigenen Bogen).
            return filter_entity_for_viewer(node, viewer.role, node["id"])
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

    # Gesundheit + Außenhülle (29.10.2026, Mark: "ich sehe bei der Reparatur
    # nicht den Gesundheitszustand der Drohnen/Rüstungen... bei Drohnen muss
    # auch ihre Außenhülle mit angezeigt werden wenn die defekt ist"):
    # dieselbe Live-Berechnung wie am Charakterblatt (`get_bogen`), hier nur
    # auf die Werkbank-Kachel verdichtet. Außenhülle ist das `istNatuerlich`-
    # Rüstungsteil der Drohne selbst (siehe `anwende_natuerliche_ruestung`-
    # Docstring) — None/None, wenn (noch) kein solches Teil existiert.
    for d in sichtbar:
        drohnen_werte = {w["name"]: w["rating"] for w in await traits_repository.get_ratings_for_entity(campaign_id, d["id"])}
        roh_grundwert = d.get("gesundheitGrundwert")
        grundwert = GESUNDHEIT_GRUNDWERT if roh_grundwert is None or roh_grundwert == -1 else int(roh_grundwert)
        g_max = gesundheit_max(drohnen_werte, grundwert)
        schaden = int(d.get("schadenSchlag") or 0) + int(d.get("schadenSchwer") or 0) + int(d.get("schadenAggraviert") or 0)
        d["gesundheitMax"] = g_max
        d["gesundheitAktuell"] = max(0, g_max - schaden)

        teile_live = anwende_natuerliche_ruestung(
            await items_repository.ruestungsteile(campaign_id, d["id"]),
            drohnen_werte.get("Widerstandsfähigkeit", 0),
            aussenhuelle=drohnen_werte.get("Außenhülle", 0),
        )
        aussenhuelle_teil = next((t for t in teile_live if t.get("istNatuerlich")), None)
        d["aussenhuelleAktuell"] = aussenhuelle_teil["ruestungKaestchenAktuell"] if aussenhuelle_teil else None
        d["aussenhuelleMax"] = aussenhuelle_teil["ruestungKaestchenMax"] if aussenhuelle_teil else None

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


class DrohneNameInput(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_nicht_leer(cls, v: str) -> str:
        sauber = v.strip()
        if not sauber:
            raise ValueError("Name darf nicht leer sein")
        return sauber


@router.post("/drohnen/{node_id}/name", response_model=dict)
async def drohne_name_setzen(
    campaign_id: str, node_id: str, body: DrohneNameInput, viewer: Viewer = Depends(get_viewer)
):
    """Benennt eine Drohne/ein Fahrzeug um.

    29.10.2026, Mark: "ich hätte gerne das der Spieler seiner Drohne selbst
    einen Namen geben kann, er kann sie gerne jeder zeit umbenennen, es ist
    ja auch seine Drohne" — anders als beim PC/NPC-Namen (SL-exklusiv über
    PATCH /personen/{id}) darf hier zusätzlich der gebundene Rigger ran,
    gleiches Zugriffsmuster wie `drohne_aktiv_setzen`.
    """
    await _drohne_und_rigger_oder_404(campaign_id, node_id, viewer)
    node = await repository.update_node("Person", PERSON_FIELDS, campaign_id, node_id, {"name": body.name})
    if node is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")
    return node


class DrohneSteigernInput(BaseModel):
    traitDefId: str
    # Material statt Nuyen (26.10.2026): wenn gesetzt, bezahlt ein
    # Maschinenteil-Gegenstand des Riggers statt Nuyen-Abzug — siehe
    # traits/drohnen.py::maschinenteil_reicht.
    materialGegenstandId: str | None = None
    # Maker-Probe (26.10.2026, Mark: "es sollte nicht einfach nur möglich
    # sein ein Maschinenteil zu verwenden, sondern der Spieler muss dann
    # eine Probe auf Maker machen"): nur beim Material-Pfad Pflicht, der
    # ¥-Pfad (Auftrag an einen Profi) würfelt nicht. "ja" erhöht den Wert
    # UND verbraucht das Material, "patzer" verbraucht NUR das Material,
    # "nein" lässt alles unverändert (siehe drohne_steigern).
    probenErgebnis: Literal["ja", "nein", "patzer"] | None = None


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


async def _drohnen_steigerungs_ziel(
    campaign_id: str, node_id: str, drohne: dict, trait_def_id: str
) -> tuple[str, str, int, int, str | None, dict | None]:
    """Löst eine traitDefId (TraitDef-Id ODER "zf:<id>") zu Name/Kategorie/
    aktuellem Wert/Obergrenze auf — gemeinsame Logik für Preisabfrage, Kauf
    UND Maker-Probe-Pool, damit sie nicht an drei Stellen auseinanderläuft.

    Rückgabe: (name, category, aktuell, grenze, zf_id, gewaehlte_zf) — die
    letzten beiden nur bei einer Zusatzfertigkeit gesetzt (fürs spätere
    hinzufuegen/steigere in drohne_steigern).
    """
    if trait_def_id.startswith("zf:"):
        zf_id = trait_def_id[len("zf:") :]
        zusatzfertigkeit = await zf_repository.hole(campaign_id, zf_id)
        if zusatzfertigkeit is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Zusatzfertigkeit nicht gefunden")
        # Dieselbe Freigabe-Prüfung wie in der Preisliste (26.10.2026),
        # hier zusätzlich serverseitig gegen direkte POSTs ohne Freigabe.
        if not zusatzfertigkeit.get("fuerDrohnenFreigegeben"):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"{zusatzfertigkeit['name']} steht einer Drohne/einem Fahrzeug nicht offen."
            )
        gewaehlte_zf = next(
            (z for z in await zf_repository.zusatzfertigkeiten_der_person(campaign_id, node_id) if z["id"] == zf_id),
            None,
        )
        aktuell = gewaehlte_zf["rating"] if gewaehlte_zf else 0
        return zusatzfertigkeit["name"], "Zusatzfertigkeit", aktuell, 6, zf_id, gewaehlte_zf

    campaign = await get_campaign(campaign_id)
    katalog = await traits_repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
    eintrag = next((t for t in katalog if t["id"] == trait_def_id), None)
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Wert nicht gefunden")
    # Eine Drohne riggt sich nicht selbst — dieselbe Sperre wie in der
    # Preisliste, hier zusätzlich serverseitig gegen direkte POSTs.
    if eintrag["name"] in DROHNE_GESPERRTE_FERTIGKEITEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"{eintrag['name']} steht einer Drohne/einem Fahrzeug nicht offen.")
    erlaubt = sichtbare_kategorien(drohne.get("weg") or "KEINER", {t["category"] for t in katalog}, False, True)
    if eintrag["category"] not in erlaubt:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Dieser Wert steht dieser Drohne/diesem Fahrzeug nicht offen.")
    werte = await traits_repository.get_ratings_for_entity(campaign_id, node_id)
    nach_name = {w["name"]: w["rating"] for w in werte}
    aktuell = nach_name.get(eintrag["name"], 0)
    grenze = next((w["max"] for w in werte if w["traitDefId"] == trait_def_id), eintrag["defaultMax"])
    return eintrag["name"], eintrag["category"], aktuell, grenze, None, None


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
    # Nur explizit freigegebene (26.10.2026, Mark: "ich seh das Mimikry und
    # das dürfen nur Vael haben") — der volle Katalog ist für Personen
    # gedacht, eine Drohne/ein Fahrzeug braucht eine eigene SL-Freigabe
    # pro Eintrag (`fuerDrohnenFreigegeben`), unabhängig von `nurFuerRasse`.
    zf_katalog = [z for z in await zf_repository.liste(campaign_id) if z.get("fuerDrohnenFreigegeben")]
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


class AttributWert(BaseModel):
    name: str
    wert: int


class MakerProbePool(BaseModel):
    """Pool-Infos fürs Maker-Probe-Popup vorm Material-Umbau (siehe
    `drohne_steigern`, Material-Pfad)."""

    name: str
    benoetigteErfolge: int
    maker: int
    attribute: list[AttributWert]


@router.get("/drohnen/{node_id}/maker-probe-pool", response_model=MakerProbePool)
async def drohne_maker_probe_pool(
    campaign_id: str, node_id: str, traitDefId: str = Query(...), viewer: Viewer = Depends(get_viewer)
):
    """Pool-Infos für die Maker-Probe: Maker (Hardware)-Wert UND alle
    Attribute DES RIGGERS zur freien Partnerwahl (Mark, 26.10.2026: "den er
    dann mit einem Attribut kombinieren darf"), plus wie viele Erfolge der
    aktuelle Zielwert verlangt (`traits/drohnen.py::benoetigte_erfolge_maker_probe`).
    Reine Leseabfrage, kein Seiteneffekt — gewürfelt wird am Tisch.
    """
    drohne, rigger_id = await _drohne_und_rigger_oder_404(campaign_id, node_id, viewer)
    if rigger_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Diese Drohne/dieses Fahrzeug hat keinen Rigger.")
    name, _category, aktuell, _grenze, _zf_id, _gewaehlte_zf = await _drohnen_steigerungs_ziel(
        campaign_id, node_id, drohne, traitDefId
    )

    campaign = await get_campaign(campaign_id)
    katalog = await traits_repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
    rigger_werte = await traits_repository.get_ratings_for_entity(campaign_id, rigger_id)
    nach_name = {w["name"]: w["rating"] for w in rigger_werte}
    # NUR echte Personen-Attribute (26.10.2026, Mark: "aber die Attribute
    # von der Drohne, das macht keinen Sinn, da müssen natürlich auch die
    # Attribute des Riggers stehen") — `category.startswith("Attribut")`
    # hätte auch "AttributDrohne"/"AttributDrohneAussenhuelle" erwischt
    # (eigene Katalogeinträge für Drohnen-Werte wie Sensoren/Panzerung, mit
    # Namen, die ein Mensch gar nicht hat). Explizit nur die drei
    # menschlichen Kategorien plus AttributMatrix (KI-Rigger).
    person_attribut_kategorien = {*erstellung.ATTRIBUT_KATEGORIEN, "AttributMatrix"}
    attribute = [
        AttributWert(name=t["name"], wert=nach_name.get(t["name"], 0))
        for t in katalog
        if t["category"] in person_attribut_kategorien
    ]
    return MakerProbePool(
        name=name,
        benoetigteErfolge=benoetigte_erfolge_maker_probe(aktuell),
        maker=nach_name.get("Maker (Hardware)", 0),
        attribute=attribute,
    )


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

    **Material-Pfad verlangt zusätzlich `probenErgebnis`** (Mark, 26.10.2026):
    der Spieler würfelt die Maker-Probe physisch am Tisch (Pool/benötigte
    Erfolge aus `drohne_maker_probe_pool`) und meldet das Ergebnis.
    "ja" erhöht den Wert UND verbraucht das Material, "patzer" verbraucht
    NUR das Material (kein Fortschritt), "nein" lässt beides unverändert.
    """
    drohne, rigger_id = await _drohne_und_rigger_oder_404(campaign_id, node_id, viewer)
    if rigger_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Diese Drohne/dieses Fahrzeug hat keinen Rigger.")

    rigger = await repository.get_node("Person", PERSON_FIELDS, campaign_id, rigger_id)
    if rigger is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rigger nicht gefunden")

    name, category, aktuell, grenze, zf_id, gewaehlte_zf = await _drohnen_steigerungs_ziel(
        campaign_id, node_id, drohne, body.traitDefId
    )
    ist_zusatzfertigkeit = body.traitDefId.startswith("zf:")

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
        if body.probenErgebnis is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Für die Materialbezahlung fehlt das Probe-Ergebnis.")
        material = await items_repository.get_gegenstand(campaign_id, body.materialGegenstandId)
        if material is None or not material.get("istMaschinenteil"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Maschinenteil.")
        besitzer_id = await items_repository.get_owner_person_id(campaign_id, body.materialGegenstandId)
        if besitzer_id not in (rigger_id, node_id):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Dieses Maschinenteil gehört weder dem Rigger noch der Drohne/dem Fahrzeug."
            )
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

    # Der Wert steigt beim ¥-Pfad immer, beim Material-Pfad nur bei "ja" —
    # ein Patzer oder ein normaler Fehlwurf bringt den Umbau nicht voran.
    stat_erhoeht = material is None or body.probenErgebnis == "ja"
    if stat_erhoeht:
        if ist_zusatzfertigkeit:
            if gewaehlte_zf is None:
                await zf_repository.hinzufuegen(campaign_id, node_id, zf_id, 1)
            else:
                await zf_repository.steigere(campaign_id, node_id, zf_id, aktuell + 1)
        else:
            await traits_repository.steigere(campaign_id, node_id, body.traitDefId, aktuell + 1)

    # Material wird bei "ja" UND "patzer" verbraucht (Mark: "beim patzer wird
    # das material verbraucht und es passiert nichts") — nur "nein" lässt
    # das Stück unangetastet, der Rigger darf es später erneut versuchen.
    material_verbraucht = material is not None and body.probenErgebnis in ("ja", "patzer")
    if material_verbraucht:
        neue_menge = max(0, material["menge"] - 1)
        await items_repository.update_gegenstand(campaign_id, body.materialGegenstandId, {"menge": neue_menge})
        kapital_neu = kapital
        sl_notiz = f"Bezahlt mit Maschinenteil {material['name']} (verbraucht, Rigger {rigger.get('name', '')})"
    elif material is None:
        kapital_neu = kapital - preis
        await repository.update_node("Person", PERSON_FIELDS, campaign_id, rigger_id, {"kapitalBasis": kapital_neu})
        sl_notiz = f"Bezahlt vom Rigger {rigger.get('name', '')} ({preis}¥ aus dessen Kapital)"
    else:
        # Material-Pfad, probenErgebnis == "nein": nichts passiert.
        kapital_neu = kapital
        sl_notiz = None

    # Ereignisprotokoll: dieselbe CharakterEntwicklung-Art wie beim EP-Kauf,
    # SL-Notiz macht die abweichende Bezahlquelle (Rigger statt eigene XP)
    # auf einen Blick erkennbar. Nur protokollieren, wenn sich wirklich etwas
    # geändert hat — ein wirkungsloses "nein" ist kein Entwicklungsereignis.
    if stat_erhoeht or material_verbraucht:
        await hooks.charakterentwicklung(
            campaign_id,
            person_id=node_id,
            art="STEIGERUNG",
            trait_def_id=body.traitDefId,
            trait_name=name,
            alt=str(aktuell),
            neu=str(aktuell + 1) if stat_erhoeht else str(aktuell),
            kosten_oder_menge=preis,
            sl_notiz=sl_notiz or f"Maker-Probe misslungen (Patzer) — Maschinenteil {material['name']} verbraucht, kein Fortschritt",
        )

    drohne_frisch = await repository.get_node("Person", PERSON_FIELDS, campaign_id, node_id)
    return {
        "drohne": drohne_frisch,
        "riggerKapitalBasis": kapital_neu,
        "erfolgreich": stat_erhoeht,
        "materialVerbraucht": material_verbraucht,
    }


@router.get("/drohnen/{node_id}/maschinenteile")
async def drohne_maschinenteile(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)) -> list[dict]:
    """Maschinenteile im Besitz DES RIGGERS **oder** der Drohne/des Fahrzeugs
    selbst (26.10.2026: beides erlaubt — der Rigger zahlt zwar das Nuyen aus
    eigenem Kapital, ein Ersatzteil kann aber genauso gut schon in der
    Drohne verbaut/mitgeführt sein, siehe Ausrüstung-Reiter) — für die
    Zahlungsauswahl beim Umbau."""
    _, rigger_id = await _drohne_und_rigger_oder_404(campaign_id, node_id, viewer)
    quellen = [node_id] + ([rigger_id] if rigger_id else [])
    gesehen: set[str] = set()
    ergebnis: list[dict] = []
    for person_id in quellen:
        for teil in await items_repository.list_maschinenteile_von(campaign_id, person_id):
            if teil["id"] not in gesehen:
                gesehen.add(teil["id"])
                ergebnis.append(teil)
    return ergebnis


def _drohne_fehlende_kaestchen(drohne: dict, werte: dict[str, int]) -> int:
    """Wie viele Gesundheits-Kästchen dieser Drohne/diesem Fahrzeug fehlen
    (Summe der drei WoD-Schadensstufen, gedeckelt am Max) — für Rüstung gibt
    es dafür `ruestungKaestchenMax - ruestungKaestchenAktuell` direkt am
    Gegenstand; eine Drohne/ein Fahrzeug hat stattdessen Gesundheit wie jede
    andere Person (siehe traits/bogen.py::gesundheit_max)."""
    roh_grundwert = drohne.get("gesundheitGrundwert")
    grundwert = GESUNDHEIT_GRUNDWERT if roh_grundwert is None or roh_grundwert == -1 else int(roh_grundwert)
    g_max = gesundheit_max(werte, grundwert)
    schaden = (
        int(drohne.get("schadenSchlag") or 0)
        + int(drohne.get("schadenSchwer") or 0)
        + int(drohne.get("schadenAggraviert") or 0)
    )
    return max(0, min(schaden, g_max))


class ReparaturProbePoolDrohne(BaseModel):
    """Pool-Infos fürs Reparatur-Popup einer Drohne/eines Fahrzeugs —
    Pendant zu `items/routes.py::ReparaturProbePool` für Rüstung."""

    skill: str
    skillWert: int
    attribute: list[AttributWert]
    benoetigteErfolge: int
    heilungBeiErfolg: int
    fehlendeKaestchen: int


@router.get("/drohnen/{node_id}/reparatur-pool", response_model=ReparaturProbePoolDrohne)
async def drohne_reparatur_pool(
    campaign_id: str,
    node_id: str,
    skill: str = Query(...),
    materialGegenstandId: str = Query(...),
    menge: int = 1,
    viewer: Viewer = Depends(get_viewer),
):
    """Pool-Infos für die Reparatur-Probe: der gewählte Skill muss zum
    Zieltyp passen (Mark, 29.10.2026, siehe kampf/ruestung.py::
    REPARATUR_SKILLS — Drohne nur Maker (Hardware), Fahrzeug Handwerk ODER
    Maker). Repariert wird vom RIGGER (gleiche Quelle wie beim
    Material-Umbau), der Attribut-Partner bleibt frei wählbar. Reine
    Leseabfrage, kein Seiteneffekt — gewürfelt wird am Tisch.
    """
    drohne, rigger_id = await _drohne_und_rigger_oder_404(campaign_id, node_id, viewer)
    if rigger_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Diese Drohne/dieses Fahrzeug hat keinen Rigger.")
    zieltyp = "fahrzeug" if drohne.get("istFahrzeug") else "drohne"
    if skill not in REPARATUR_SKILLS[zieltyp]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Dieser Skill repariert kein {zieltyp.capitalize()}.")

    material = await items_repository.get_gegenstand(campaign_id, materialGegenstandId)
    if material is None or not material.get("istMaschinenteil"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Maschinenteil.")

    rigger_werte = await traits_repository.get_ratings_for_entity(campaign_id, rigger_id)
    nach_name = {w["name"]: w["rating"] for w in rigger_werte}
    campaign = await get_campaign(campaign_id)
    katalog = await traits_repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
    person_attribut_kategorien = {*erstellung.ATTRIBUT_KATEGORIEN, "AttributMatrix"}
    attribute = [
        AttributWert(name=t["name"], wert=nach_name.get(t["name"], 0))
        for t in katalog
        if t["category"] in person_attribut_kategorien
    ]

    drohnen_werte = {w["name"]: w["rating"] for w in await traits_repository.get_ratings_for_entity(campaign_id, node_id)}
    fehlende_kaestchen = _drohne_fehlende_kaestchen(drohne, drohnen_werte)

    return ReparaturProbePoolDrohne(
        skill=skill,
        skillWert=nach_name.get(skill, 0),
        attribute=attribute,
        benoetigteErfolge=reparatur_benoetigte_erfolge(menge),
        heilungBeiErfolg=reparatur_heilung_material(material.get("maschinenteilQualitaet") or "", menge, fehlende_kaestchen),
        fehlendeKaestchen=fehlende_kaestchen,
    )


class ReparaturMaterialRequestDrohne(BaseModel):
    """Selbst-Reparieren: Maschinenteil + selbstberichtete Probe, kein Geld
    — Pendant zu `items/routes.py::ReparaturMaterialRequest` für Rüstung."""

    materialGegenstandId: str
    menge: int = Field(ge=1)
    probenErgebnis: Literal["ja", "nein", "patzer"]


class ReparaturMaterialErgebnisDrohne(BaseModel):
    qualitaet: str
    menge: int
    repariert: int
    materialName: str
    materialVerbraucht: int
    materialRestmenge: int
    drohne: dict


@router.post("/drohnen/{node_id}/reparieren-material", response_model=ReparaturMaterialErgebnisDrohne)
async def drohne_reparieren_material(
    campaign_id: str, node_id: str, body: ReparaturMaterialRequestDrohne, viewer: Viewer = Depends(get_viewer)
):
    """Heilt Gesundheitsschaden der Drohne/des Fahrzeugs (sie können bisher
    nicht rasten — dies ist ihr einziger Heilweg, siehe
    docs/wiki/concepts/drohnen-fahrzeuge.md "Reparatur"). "ja" heilt UND
    verbraucht das Material, "patzer" verbraucht NUR das Material, "nein"
    lässt beides unangetastet — gleiches Muster wie die Maker-Probe."""
    drohne, rigger_id = await _drohne_und_rigger_oder_404(campaign_id, node_id, viewer)
    if rigger_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Diese Drohne/dieses Fahrzeug hat keinen Rigger.")

    material = await items_repository.get_gegenstand(campaign_id, body.materialGegenstandId)
    if material is None or not material.get("istMaschinenteil"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein gültiges Maschinenteil.")
    besitzer_id = await items_repository.get_owner_person_id(campaign_id, body.materialGegenstandId)
    if besitzer_id not in (rigger_id, node_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Dieses Maschinenteil gehört weder dem Rigger noch der Drohne/dem Fahrzeug."
        )
    if material.get("menge", 1) < body.menge:
        raise HTTPException(status.HTTP_409_CONFLICT, "Nicht genug von diesem Maschinenteil vorhanden.")

    drohnen_werte = {w["name"]: w["rating"] for w in await traits_repository.get_ratings_for_entity(campaign_id, node_id)}
    schlag = int(drohne.get("schadenSchlag") or 0)
    schwer = int(drohne.get("schadenSchwer") or 0)
    aggraviert = int(drohne.get("schadenAggraviert") or 0)
    fehlende_kaestchen = _drohne_fehlende_kaestchen(drohne, drohnen_werte)

    qualitaet = material.get("maschinenteilQualitaet") or ""
    repariert = 0
    if body.probenErgebnis == "ja":
        repariert = reparatur_heilung_material(qualitaet, body.menge, fehlende_kaestchen)
        neuer_schaden = heile_gesundheitsschaden(schlag, schwer, aggraviert, repariert)
        await repository.update_node("Person", PERSON_FIELDS, campaign_id, node_id, neuer_schaden)

    material_verbraucht = body.probenErgebnis in ("ja", "patzer")
    material_neue_menge = material["menge"] - body.menge if material_verbraucht else material["menge"]
    if material_verbraucht:
        await items_repository.update_gegenstand(campaign_id, body.materialGegenstandId, {"menge": material_neue_menge})

    drohne_frisch = await repository.get_node("Person", PERSON_FIELDS, campaign_id, node_id)
    if drohne_frisch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")
    return ReparaturMaterialErgebnisDrohne(
        qualitaet=qualitaet,
        menge=body.menge,
        repariert=repariert,
        materialName=material["name"],
        materialVerbraucht=body.menge if material_verbraucht else 0,
        materialRestmenge=material_neue_menge,
        drohne=drohne_frisch,
    )


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
