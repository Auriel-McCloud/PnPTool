import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_einstellungen
from app.entities.repository import PERSON_FIELDS, drohne_rigger, get_node
from app.kampf import repository
from app.kampf.initiative import darf_melden, initiative_pool, melde_wert
from app.kampf.sichtbarkeit import fuer_spieler
from app.items.repository import ausgeruestete_decks, initiative_modifikator, verbautes_chrom
from app.kampf.booster import (
    AMPEL_MAX,
    ampel_nach_nutzung,
    braucht_paralyse_wurf,
    darf_aktivieren,
    paralyse_pool,
    paralyse_schwelle,
    zweitwurf_pool,
)
from app.kampf.hot import (
    beantworte_bleiben,
    bleiben_faellig,
    booster_kandidaten,
    darf_drohne_waehlen,
    hat_neurolink,
    staerkstes,
    waehle_drohne,
)
from app.traits.repository import get_ratings_for_entity
from app.wuerfel.logic import wuerfle

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/kampf",
    tags=["kampf"],
    dependencies=[Depends(require_campaign_zugang)],
)

Kampfart = str  # MATRIX | NAHKAMPF | FERNKAMPF — bewusst offen, siehe unten


def _ohne_hilfsfelder(kampf: dict | None) -> dict | None:
    """Entfernt die nur zur Filterung mitgelieferten Felder.

    Schreibrouten sind der Spielleitung vorbehalten, dort ist nichts zu
    verbergen — die Felder gehören aber trotzdem nicht in die Antwort.
    """
    if kampf is None:
        return None
    for feld in ("_rassen", "_npcIds", "_begleiterBesitzer", "_drohnenBesitzer"):
        kampf.pop(feld, None)
    return kampf


class TeilnehmerResponse(BaseModel):
    id: str
    name: str
    initiative: int
    # Zusatzzug aus dem Reflex-Booster; verschwindet nach seinem Zug.
    zusatzzug: bool = False
    stammtId: str | None = None
    # Ueberhitzung Stufe 3: 0-3 wie eine Ampel.
    ampel: int = 0
    zusatzGenutzt: int = 0
    setztAus: bool = False
    # Beschwörungs-Ki-Tama (30.10.2026): Runden bis der beschworene Critter
    # automatisch den Tracker verlässt. None = kein beschworener Teilnehmer.
    rundenVerbleibend: int | None = None
    # Entscheidet die Reihenfolge bei Gleichstand (Zeile 58). Kein Enum, damit
    # sich weitere Arten ergänzen lassen, ohne das Schema anzufassen.
    kampfart: str
    notiz: str
    erledigt: bool
    personId: str | None = None
    personType: str | None = None
    begleiterId: str | None = None


class KampfResponse(BaseModel):
    id: str
    runde: int
    amZug: str | None = None
    teilnehmer: list[TeilnehmerResponse]


class TeilnehmerInput(BaseModel):
    name: str
    initiative: int = Field(default=0, ge=0)
    kampfart: str = "NAHKAMPF"
    notiz: str = ""
    personId: str | None = None
    begleiterId: str | None = None


class TeilnehmerUpdate(BaseModel):
    name: str | None = None
    initiative: int | None = Field(default=None, ge=0)
    kampfart: str | None = None
    notiz: str | None = None
    erledigt: bool | None = None
    # Manuelle SL-Korrektur des Beschwörungs-Zählers (z.B. ein Zauber
    # verlängert die Bindung).
    rundenVerbleibend: int | None = None


class AmZugInput(BaseModel):
    teilnehmerId: str | None = None


class InitiativeInput(BaseModel):
    """Ein von Hand gewürfelter Initiativwert (Anzahl Erfolge)."""

    erfolge: int = Field(ge=0)


class InitiativePoolResponse(BaseModel):
    """Was der Spieler vor dem Wurf wissen muss."""

    pool: int
    # Woraus sich der Pool zusammensetzt — sonst wirkt die Zahl willkürlich.
    geistesschaerfe: int
    geschicklichkeit: int
    cyberwareMod: int
    # Darf im Tool gewürfelt werden, oder liegen echte Würfel auf dem Tisch?
    digitalErlaubt: bool
    # Der eigene Eintrag im Kampf, falls schon vorhanden.
    teilnehmerId: str | None = None
    gemeldet: int | None = None


@router.get("", response_model=KampfResponse | None)
async def laufender_kampf(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Die Initiativliste.

    **Für alle mit Zugang lesbar** — das ist der Sinn der Sache: jeder am Tisch
    soll sehen, wann er dran ist, ohne fragen zu müssen.

    **Aber:** Spieler sehen NPCs nur unter Alias. Mark: *"die Spieler dürfen
    nur die Alias Namen der NPCs sehen nicht ihre richtigen Namen!"* Gefiltert
    wird hier serverseitig, nicht im Browser — im Netzwerkverkehr stünde der
    echte Name sonst trotzdem.
    """
    kampf = await repository.hole(campaign_id)
    if kampf is None:
        return None

    rassen = kampf.pop("_rassen", {})
    npc_ids = kampf.pop("_npcIds", set())
    begleiter_besitzer = kampf.pop("_begleiterBesitzer", {})
    drohnen_besitzer = kampf.pop("_drohnenBesitzer", {})

    if viewer.role != "GM":
        kampf["teilnehmer"] = fuer_spieler(
            kampf["teilnehmer"],
            rassen=rassen,
            eigene_person_id=viewer.person_id,
            begleiter_besitzer=begleiter_besitzer,
            npc_ids=npc_ids,
            drohnen_besitzer=drohnen_besitzer,
        )
    return kampf


@router.post("", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def beginne(campaign_id: str):
    return _ohne_hilfsfelder(await repository.beginne(campaign_id))


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def beende(campaign_id: str):
    await repository.beende(campaign_id)


@router.post("/teilnehmer", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_hinzu(campaign_id: str, body: TeilnehmerInput):
    if body.personId:
        person = await get_node("Person", PERSON_FIELDS, campaign_id, body.personId)
        if person and (person.get("istDrohne") or person.get("istFahrzeug")) and not person.get("riggerAktiv"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Inaktive Drohne/inaktives Fahrzeug kann nicht in den Kampf aufgenommen werden — erst mit der Riggerkonsole verbinden.",
            )
    kampf = await repository.teilnehmer_hinzu(campaign_id, body.model_dump())
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.patch("/teilnehmer/{teilnehmer_id}", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_aendern(campaign_id: str, teilnehmer_id: str, body: TeilnehmerUpdate):
    kampf = await repository.teilnehmer_aendern(campaign_id, teilnehmer_id, body.model_dump())
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.delete("/teilnehmer/{teilnehmer_id}", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_entfernen(campaign_id: str, teilnehmer_id: str):
    kampf = await repository.teilnehmer_entfernen(campaign_id, teilnehmer_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.post("/weiter", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def weiter(campaign_id: str):
    """Einen Zug weiter. Am Ende der Liste beginnt die nächste Runde."""
    kampf = await repository.weiter(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


@router.post("/amzug", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def am_zug(campaign_id: str, body: AmZugInput):
    """Direkt jemanden ans Ruder setzen — für den Fall, dass es durcheinander ging."""
    kampf = await repository.setze_am_zug(campaign_id, body.teilnehmerId)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)


async def _werte_von(campaign_id: str, person_id: str) -> dict[str, int]:
    """Attributwerte einer Person als {Name: Stufe}."""
    roh = await get_ratings_for_entity(campaign_id, person_id)
    return {r["name"]: r["rating"] for r in roh}


async def _chrom_mod(campaign_id: str, person_id: str) -> int:
    """Initiative-Modifikator aus getragener Cyberware.

    Dieselbe Quelle wie der Charakterbogen (`items/repository.py`) — zwei
    Rechenwege für dieselbe Zahl wären eine Fehlerquelle.
    """
    return await initiative_modifikator(campaign_id, person_id)


@router.get("/initiative/pool", response_model=InitiativePoolResponse)
async def mein_initiative_pool(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Der eigene Initiative-Pool.

    Marks Ablauf: Nach der Warnung *"Würfelt für Initiative!"* soll der
    Spieler sehen, **wie viele Würfel** er nimmt — ohne im Charakterbogen
    nachzuschlagen.
    """
    if not viewer.person_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein eigener Charakter")

    werte = await _werte_von(campaign_id, viewer.person_id)
    chrom = await _chrom_mod(campaign_id, viewer.person_id)
    einstellungen = await get_einstellungen(campaign_id)

    # Den eigenen Eintrag im laufenden Kampf suchen, damit die Oberfläche
    # zeigen kann, ob schon gemeldet wurde.
    kampf = await repository.hole(campaign_id)
    eigener = None
    if kampf:
        eigener = next(
            (t for t in kampf["teilnehmer"] if t.get("personId") == viewer.person_id),
            None,
        )

    return InitiativePoolResponse(
        pool=initiative_pool(werte, chrom),
        geistesschaerfe=werte.get("Geistesschärfe", 0),
        geschicklichkeit=werte.get("Geschicklichkeit", 0),
        cyberwareMod=chrom,
        digitalErlaubt=bool(einstellungen.get("digitalesWuerfeln")),
        teilnehmerId=eigener["id"] if eigener else None,
        gemeldet=eigener["initiative"] if eigener else None,
    )


@router.post("/teilnehmer/{teilnehmer_id}/initiative", response_model=KampfResponse)
async def melde_initiative(
    campaign_id: str,
    teilnehmer_id: str,
    body: InitiativeInput,
    viewer: Viewer = Depends(get_viewer),
):
    """Einen selbst gewürfelten Initiativwert melden.

    **Vom Spieler aufrufbar** — das ist der Sinn: er würfelt physisch und
    trägt seine Erfolge ein, statt sie der Spielleitung zuzurufen. Deshalb
    hängt hier bewusst kein `require_campaign_gm`; die Berechtigung prüft
    `darf_melden` feingranular (nur der eigene Charakter).
    """
    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")

    eintrag = next((t for t in kampf["teilnehmer"] if t["id"] == teilnehmer_id), None)
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teilnehmer nicht im Kampf")

    if not await _darf_initiative_melden(campaign_id, viewer, eintrag.get("personId")):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Nur für den eigenen Charakter")

    try:
        wert = melde_wert(body.erfolge)
    except ValueError as fehler:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(fehler)) from fehler

    kampf = await repository.teilnehmer_aendern(campaign_id, teilnehmer_id, {"initiative": wert})
    return _ohne_hilfsfelder(kampf)


async def _darf_initiative_melden(campaign_id: str, viewer: Viewer, ziel_person_id: str | None) -> bool:
    """Wie `darf_melden`, nur zusätzlich: der Rigger darf auch für seine
    eigene(n) aktive(n) Drohne(n)/Fahrzeug(e) melden (26.10.2026, Mark:
    \"er geht ins Popup rein, klickt da drauf und seine Drohnen fügen sich
    automatisch in die Initiativreihenfolge ein\"). Ein Teilnehmer ohne
    `personId` (\"Wachmann 1\") bleibt für Spieler tabu, wie bisher.
    """
    if darf_melden(viewer.role, viewer.person_id, ziel_person_id):
        return True
    if viewer.role == "GM" or not ziel_person_id or not viewer.person_id:
        return False
    rigger_id = await drohne_rigger(campaign_id, ziel_person_id)
    return rigger_id is not None and rigger_id == viewer.person_id


NUMMER_MUSTER = re.compile(r"^(.*) (\d+)$")


async def _mit_nummer_falls_doppelt(campaign_id: str, teilnehmer: list[dict], basis_name: str) -> str:
    """Hängt eine Nummer an, wenn der Name schon im Kampf steht — Mark,
    26.10.2026: zwei gleichnamige Drohnen desselben Riggers sollen als
    \"Spinne 1\"/\"Spinne 2\" unterscheidbar sein, automatisch durchnummeriert.

    Der erste, bisher unnummerierte Eintrag wird beim Dazukommen des zweiten
    nachträglich zu \"Name 1\" umbenannt — vorher gab es ja keine Verwechslung.
    """
    treffer = [
        t for t in teilnehmer
        if t["name"] == basis_name or (NUMMER_MUSTER.match(t["name"]) and NUMMER_MUSTER.match(t["name"]).group(1) == basis_name)
    ]
    if not treffer:
        return basis_name

    nummern: list[int] = []
    unnummeriert = None
    for t in treffer:
        m = NUMMER_MUSTER.match(t["name"])
        if m:
            nummern.append(int(m.group(2)))
        else:
            unnummeriert = t

    if unnummeriert is not None:
        await repository.teilnehmer_aendern(campaign_id, unnummeriert["id"], {"name": f"{basis_name} 1"})
        nummern.append(1)

    return f"{basis_name} {max(nummern, default=0) + 1}"


@router.post("/drohnen/{node_id}/beitreten", response_model=KampfResponse)
async def drohne_dem_kampf_beitreten(campaign_id: str, node_id: str, viewer: Viewer = Depends(get_viewer)):
    """Self-Service: der Rigger nimmt seine eigene aktive Drohne/sein eigenes
    Fahrzeug selbst in den laufenden Kampf auf, statt die Spielleitung zu
    bitten (Mark, 26.10.2026). Dieselbe 404-statt-403-Logik wie bei
    `entities/routes.py::_drohne_und_rigger_oder_404` — eine fremde Drohne
    soll nicht einmal als existierend erkennbar sein.
    """
    drohne = await get_node("Person", PERSON_FIELDS, campaign_id, node_id)
    if drohne is None or not (drohne.get("istDrohne") or drohne.get("istFahrzeug")):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")

    rigger_id = await drohne_rigger(campaign_id, node_id)
    if viewer.role != "GM" and (rigger_id is None or rigger_id != viewer.person_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")

    if not drohne.get("riggerAktiv"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Erst mit der Riggerkonsole verbinden, bevor sie am Kampf teilnimmt.")

    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")

    bereits_dabei = next((t for t in kampf["teilnehmer"] if t.get("personId") == node_id), None)
    if bereits_dabei:
        return _ohne_hilfsfelder(kampf)

    name = await _mit_nummer_falls_doppelt(campaign_id, kampf["teilnehmer"], drohne["name"])
    kampf = await repository.teilnehmer_hinzu(
        campaign_id,
        {"name": name, "initiative": 0, "kampfart": "FERNKAMPF", "notiz": "", "personId": node_id, "begleiterId": None},
    )
    return _ohne_hilfsfelder(kampf)


@router.post("/initiative/npcs", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def wuerfle_npc_initiative(campaign_id: str):
    """Würfelt die Initiative aller NPCs und Begleiter im Kampf.

    Marks ausdrückliche Ausnahme: *"die Ausnahme sind als SL nämlich die
    Initiative Würfel für meine im Kampf teilnehmenden NPCs die hätte schon
    gerne automatisch"*. Spieler-Charaktere bleiben unangetastet — die
    würfeln selbst.
    """
    einstellungen = await get_einstellungen(campaign_id)
    if not einstellungen.get("digitalesWuerfelnSL"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Digitales Würfeln für die Spielleitung ist in dieser Kampagne aus",
        )

    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")

    for t in kampf["teilnehmer"]:
        if t.get("personType") == "PC":
            continue  # Die würfeln selbst
        pool = 0
        if t.get("personId"):
            # Auch NPCs tragen Chrom — ein Reflex-Booster wirkt für sie genauso.
            pool = initiative_pool(
                await _werte_von(campaign_id, t["personId"]),
                await _chrom_mod(campaign_id, t["personId"]),
            )
        elif t.get("begleiterId"):
            pool = initiative_pool(await _werte_von(campaign_id, t["begleiterId"]))
        # Ein namenloser Wachmann ohne Bogen bekommt einen Standardpool,
        # damit er nicht immer als Letzter handelt.
        ergebnis = wuerfle(pool if pool > 0 else 4)
        await repository.teilnehmer_aendern(
            campaign_id, t["id"], {"initiative": ergebnis["erfolge"]}
        )

    return _ohne_hilfsfelder(await repository.hole(campaign_id))


class BoosterStatus(BaseModel):
    """Was der Spieler über seinen Booster wissen muss, wenn er dran ist."""

    hatBooster: bool = False
    boosterName: str = ""
    # 1, 2 oder -1 (jede Runde). 0 = kein Booster.
    zusatzaktionenMax: int = 0
    bereitsGenutzt: int = 0
    darfAktivieren: bool = False
    # Womit der Zweitwurf gewürfelt wird — OHNE Boosterbonus.
    zweitwurfPool: int = 0
    ampel: int = 0
    ampelMax: int = AMPEL_MAX
    # Volle Ampel: am Ende dieser Runde ist der Paralysewurf fällig.
    paralyseFaellig: bool = False
    paralysePool: int = 0
    paralyseSchwelle: int = 0
    teilnehmerId: str | None = None
    setztAus: bool = False


async def _booster_von(campaign_id: str, person_id: str) -> dict | None:
    """Stärkstes Stück mit Zusatzaktionen.

    Verbautes Chrom zählt immer. Das ausgerüstete Deck nur, solange der
    Decker Hot ist — sonst wäre die Freischaltung nur ein Schalter ohne Tür.
    """
    stuecke = await verbautes_chrom(campaign_id, person_id)
    zustand = await repository.hot_lesen(campaign_id, person_id)
    decks = await ausgeruestete_decks(campaign_id, person_id) if zustand["matrixHot"] else []
    deck = staerkstes(decks)
    return staerkstes(booster_kandidaten(stuecke, deck, zustand["matrixHot"]))


class HotStatus(BaseModel):
    hatNeurolink: bool = False
    hatDeck: bool = False
    matrixHot: bool = False
    hotDrohneId: str | None = None
    hotDrohneName: str | None = None
    bleibenFaellig: bool = False
    darfWaehlen: bool = False


class HotInput(BaseModel):
    drohneId: str | None = None
    bleiben: bool | None = None
    matrix: bool | None = None


async def _hot_status(campaign_id: str, person_id: str) -> HotStatus:
    chrom = await verbautes_chrom(campaign_id, person_id)
    decks = await ausgeruestete_decks(campaign_id, person_id)
    zustand = await repository.hot_lesen(campaign_id, person_id)
    kampf = await repository.hole(campaign_id)
    runde = kampf["runde"] if kampf else None
    eigener = None
    if kampf:
        eigener = next(
            (t for t in kampf["teilnehmer"] if t.get("personId") == person_id and not t.get("zusatzzug")),
            None,
        )
    ist_dran = bool(eigener and kampf and kampf["amZug"] == eigener["id"])
    return HotStatus(
        hatNeurolink=hat_neurolink(chrom),
        hatDeck=bool(decks),
        matrixHot=zustand["matrixHot"],
        hotDrohneId=zustand["hotDrohneId"],
        hotDrohneName=zustand["hotDrohneName"],
        bleibenFaellig=bleiben_faellig(
            zustand["hotDrohneId"], zustand["hotDrohneRunde"], runde, ist_dran
        ),
        darfWaehlen=darf_drohne_waehlen(zustand["hotDrohneId"], zustand["hotDrohneRunde"], runde),
    )


@router.get("/hot", response_model=HotStatus)
async def hot_status(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    if not viewer.person_id:
        return HotStatus()
    return await _hot_status(campaign_id, viewer.person_id)


@router.post("/hot", response_model=HotStatus)
async def hot_setzen(campaign_id: str, body: HotInput, viewer: Viewer = Depends(get_viewer)):
    """Hot gehen: Matrix-Knopf, Drohne an der Slot-Box, oder Bleiben-Antwort."""
    if not viewer.person_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein eigener Charakter")
    person_id = viewer.person_id
    kampf = await repository.hole(campaign_id)
    runde = kampf["runde"] if kampf else None
    zustand = await repository.hot_lesen(campaign_id, person_id)
    chrom = await verbautes_chrom(campaign_id, person_id)

    if body.drohneId and viewer.role == "GM":
        rigger_id = await drohne_rigger(campaign_id, body.drohneId)
        if rigger_id:
            person_id = rigger_id
            zustand = await repository.hot_lesen(campaign_id, person_id)
            chrom = await verbautes_chrom(campaign_id, person_id)

    if not hat_neurolink(chrom):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ohne verbauten Neurolink kein Hot.")

    if body.bleiben is not None:
        eigener = None
        if kampf:
            eigener = next(
                (t for t in kampf["teilnehmer"] if t.get("personId") == person_id and not t.get("zusatzzug")),
                None,
            )
        ist_dran = bool(eigener and kampf and kampf["amZug"] == eigener["id"])
        if not bleiben_faellig(zustand["hotDrohneId"], zustand["hotDrohneRunde"], runde, ist_dran):
            raise HTTPException(status.HTTP_409_CONFLICT, "Gerade steht die Frage nicht an.")
        antwort = beantworte_bleiben(body.bleiben, zustand["hotDrohneId"], runde)
        await repository.hot_schreiben(
            campaign_id, person_id, hot_drohne_id=antwort.hot_drohne_id, hot_runde=antwort.hot_runde
        )
        return await _hot_status(campaign_id, person_id)

    if body.matrix is not None:
        await repository.hot_schreiben(
            campaign_id,
            person_id,
            hot_drohne_id=zustand["hotDrohneId"],
            hot_runde=zustand["hotDrohneRunde"],
            matrix_hot=body.matrix,
        )
        return await _hot_status(campaign_id, person_id)

    if not body.drohneId:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Keine Drohne gewählt.")

    drohne = await get_node("Person", PERSON_FIELDS, campaign_id, body.drohneId)
    if drohne is None or not (drohne.get("istDrohne") or drohne.get("istFahrzeug")):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")
    if not drohne.get("riggerAktiv"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Nur eine aktive Drohne kann Hot gehen.")
    rigger_id = await drohne_rigger(campaign_id, body.drohneId)
    if rigger_id != person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")

    wahl = waehle_drohne(
        hat_neurolink=True,
        hot_drohne_id=zustand["hotDrohneId"],
        hot_runde=zustand["hotDrohneRunde"],
        kampf_runde=runde,
        drohne_id=body.drohneId,
    )
    if not wahl.ok:
        raise HTTPException(status.HTTP_409_CONFLICT, wahl.fehler or "Hot gerade nicht möglich.")
    await repository.hot_schreiben(
        campaign_id, person_id, hot_drohne_id=wahl.hot_drohne_id, hot_runde=wahl.hot_runde
    )
    return await _hot_status(campaign_id, person_id)


@router.get("/booster/status", response_model=BoosterStatus)
async def booster_status(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Der eigene Boosterzustand — Grundlage für das Popup beim Drankommen."""
    if not viewer.person_id:
        return BoosterStatus()

    booster = await _booster_von(campaign_id, viewer.person_id)
    if booster is None:
        return BoosterStatus()

    kampf = await repository.hole(campaign_id)
    eigener = None
    if kampf:
        eigener = next(
            (
                t
                for t in kampf["teilnehmer"]
                if t.get("personId") == viewer.person_id and not t.get("zusatzzug")
            ),
            None,
        )

    werte = await _werte_von(campaign_id, viewer.person_id)
    ampel = eigener["ampel"] if eigener else 0
    genutzt = eigener["zusatzGenutzt"] if eigener else 0
    maximal = int(booster.get("zusatzaktionen") or 0)

    return BoosterStatus(
        hatBooster=True,
        boosterName=booster.get("name") or "Reflex-Booster",
        zusatzaktionenMax=maximal,
        bereitsGenutzt=genutzt,
        darfAktivieren=darf_aktivieren(maximal, genutzt) and not (eigener or {}).get("setztAus"),
        # Ohne Boosterbonus — genau darum ist die Zusatzaktion ein Risiko.
        zweitwurfPool=zweitwurf_pool(werte),
        ampel=ampel,
        paralyseFaellig=braucht_paralyse_wurf(ampel),
        paralysePool=paralyse_pool(werte),
        paralyseSchwelle=paralyse_schwelle(),
        teilnehmerId=eigener["id"] if eigener else None,
        setztAus=bool((eigener or {}).get("setztAus")),
    )


class AktivierenInput(BaseModel):
    """Der selbst gewürfelte Zweitwurf (Anzahl Erfolge)."""

    erfolge: int = Field(ge=0)


@router.post("/booster/aktivieren", response_model=KampfResponse)
async def booster_aktivieren(
    campaign_id: str,
    body: AktivierenInput,
    viewer: Viewer = Depends(get_viewer),
):
    """Reflex-Booster zünden: zweiter Eintrag in der Initiativliste.

    **Vom Spieler aufrufbar** — er entscheidet im Popup selbst. Geprüft wird
    serverseitig: eigener Charakter, Booster verbaut, Aktionen übrig.
    """
    if not viewer.person_id and viewer.role != "GM":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein eigener Charakter")

    person_id = viewer.person_id
    booster = await _booster_von(campaign_id, person_id) if person_id else None
    if booster is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Kein Reflex-Booster verbaut")

    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")

    eigener = next(
        (t for t in kampf["teilnehmer"] if t.get("personId") == person_id and not t.get("zusatzzug")),
        None,
    )
    if eigener is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Du bist nicht im Kampf")

    maximal = int(booster.get("zusatzaktionen") or 0)
    if not darf_aktivieren(maximal, eigener["zusatzGenutzt"]):
        raise HTTPException(status.HTTP_409_CONFLICT, "Keine Zusatzaktion mehr übrig")
    if eigener.get("setztAus"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Du setzt diese Runde aus")

    try:
        wert = melde_wert(body.erfolge)
    except ValueError as fehler:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(fehler)) from fehler

    # Zweiter Eintrag. Er reiht sich ganz normal ein — meist später, weil
    # ohne Boosterbonus gewürfelt wurde; ist der Wurf höher, handelt die
    # Person direkt zweimal hintereinander.
    await repository.teilnehmer_hinzu(
        campaign_id,
        {
            "name": eigener["name"],
            "initiative": wert,
            "kampfart": eigener["kampfart"],
            "notiz": "",
            "personId": person_id,
            "begleiterId": None,
            "zusatzzug": True,
            "stammtId": eigener["id"],
        },
    )

    # Zähler und Überhitzung am Stammeintrag fortschreiben.
    await repository.teilnehmer_aendern(
        campaign_id,
        eigener["id"],
        {
            "zusatzGenutzt": eigener["zusatzGenutzt"] + 1,
            "ampel": ampel_nach_nutzung(eigener["ampel"]),
        },
    )

    return _ohne_hilfsfelder(await repository.hole(campaign_id))


class ParalyseInput(BaseModel):
    """Hat der Spieler den Paralysewurf geschafft?"""

    geschafft: bool


@router.post("/teilnehmer/{teilnehmer_id}/paralyse", response_model=KampfResponse)
async def paralyse_melden(
    campaign_id: str,
    teilnehmer_id: str,
    body: ParalyseInput,
    viewer: Viewer = Depends(get_viewer),
):
    """Ergebnis des Paralysewurfs melden.

    Mark: *"schafft er den nicht ... sind all seine Apel Bällchen auf 0, dafür
    graut sein eigentlicher initive Eintrag aus um zu signalisieren das er die
    nächste Runde überspringt"*.

    Geschafft: Ampel zurück auf 0, sonst nichts. Nicht geschafft: Ampel auf 0
    **und** eine Runde aussetzen.
    """
    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")

    eintrag = next((t for t in kampf["teilnehmer"] if t["id"] == teilnehmer_id), None)
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teilnehmer nicht im Kampf")

    if not darf_melden(viewer.role, viewer.person_id, eintrag.get("personId")):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Nur für den eigenen Charakter")

    await repository.teilnehmer_aendern(
        campaign_id,
        teilnehmer_id,
        {"ampel": 0, "setztAus": not body.geschafft},
    )
    return _ohne_hilfsfelder(await repository.hole(campaign_id))


@router.post("/teilnehmer/{teilnehmer_id}/aussetzen-beendet", response_model=KampfResponse,
             dependencies=[Depends(require_campaign_gm)])
async def aussetzen_beendet(campaign_id: str, teilnehmer_id: str):
    """Hebt das Aussetzen auf — der Eintrag wird wieder normal dargestellt.

    Mark: *"und wird dann wieder dunkel wenn darüber rotiert wurde"*.
    """
    kampf = await repository.teilnehmer_aendern(campaign_id, teilnehmer_id, {"setztAus": False})
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return _ohne_hilfsfelder(kampf)
