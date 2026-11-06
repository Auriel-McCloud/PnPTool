import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.battlemap.hex import drop_frei
from app.battlemap.logic import darf_schieben, karten_liste, token_stand
from app.battlemap.schemas import BlickUpdate, KarteAnKampf, PositionUpdate, VerstecktUpdate
from app.battlemap.verteiler import verteiler as karten_verteiler
from app.campaigns.repository import get_einstellungen
from app.entities.repository import PERSON_FIELDS, critter_besitzer, drohne_rigger, get_node
from app.kampf import matrix_store, repository
from app.kampf.initiative import (
    darf_melden,
    eigener_haupteintrag,
    initiative_pool,
    melde_wert,
    person_fehler_http,
    waehle_person,
)
from app.kampf.sichtbarkeit import fuer_spieler
from app.items.beschwoerung import benoetigte_erfolge as beschwoerung_benoetigte_erfolge
from app.items.beschwoerung import beschwoerungsstufe, ruf_entscheidung
from app.items.repository import ausgeruestete_decks, get_gegenstand, get_owner_person_id, initiative_modifikator, verbautes_chrom
from app.party import repository as party_repository
from app.traits.bogen import initiative as bogen_initiative
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
    beantworte_matrix,
    bleiben_faellig,
    booster_kandidaten,
    darf_drohne_waehlen,
    hat_neurolink,
    matrix_bleiben_faellig,
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
    for feld in ("_rassen", "_npcIds", "_begleiterBesitzer", "_drohnenBesitzer", "_sichtSpeicher", "_campaignId", "_waende", "_hotDrohnen"):
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
    hexQ: int | None = None
    hexR: int | None = None
    hexDrehung: int | None = None
    zugStartQ: int | None = None
    zugStartR: int | None = None
    bildUrl: str = ""
    istGross: bool = False
    istDrohne: bool = False
    istFahrzeug: bool = False
    istCritter: bool = False
    # Rigger/Beschwörer — Spieler darf den Token am Zug schieben.
    besitzerId: str | None = None
    blickrichtung: int = 0
    versteckt: bool = False
    rundumsicht: bool = False
    veraltet: bool = False
    # Hot-Gehen (28.10.2026): Körper bleibt liegen, Drohne steuert sich selbst.
    # Fehlten bisher am Response-Schema — jede HTTP-Antwort (nicht nur der
    # Live-Rundruf übers Websocket) strippte sie sang- und klanglos weg.
    hotKoerper: bool = False
    hotGesteuert: bool = False
    nurKarte: bool = False


class KampfResponse(BaseModel):
    id: str
    runde: int
    amZug: str | None = None
    teilnehmer: list[TeilnehmerResponse]
    # Ki-Tama-Item-IDs, deren einer Ruf in diesem Kampf schon weg ist.
    verbrauchteBeschwoerungen: list[str] = []
    battlemapId: str | None = None


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

    if viewer.role != "GM":
        return await _fuer_spieler_kampf(kampf, viewer.person_id)
    return _ohne_hilfsfelder(kampf)


@router.get("/karte", response_model=KampfResponse | None)
async def kampf_fuer_karte(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Eigener Lesepfad fürs Battlemap-Popup.

    `GET /kampf` (oben) bleibt für die Initiativliste gefaltet — die Hot-
    Drohne teilt dort den Slot des Riggers (`hot-gehen.md`). Die Karte
    braucht aber BEIDE als getrennte Tokens mit je eigener Position/Blick-
    richtung, genau wie der Live-Rundruf (`_tokens_senden`) es schon für
    Folgeaktionen liefert. Bisher bekam nur eine NICHT-SL-Antwort diese
    Aufteilung (`_fuer_spieler_kampf(..., karte=True)`), und auch nur bei
    laufendem Fog of War — die SL sah beim ERSTEN Öffnen der Karte (vor dem
    ersten Websocket-Push) ausschließlich den gefalteten Rigger-Eintrag,
    Schieben/Blick trafen dadurch den Körper statt der Drohne (Mark,
    06.11.2026).
    """
    kampf = await repository.hole(campaign_id)
    if kampf is None:
        return None
    if viewer.role == "GM":
        return _ohne_hilfsfelder({**kampf, "teilnehmer": karten_liste(kampf)})
    return await _fuer_spieler_kampf(kampf, viewer.person_id, karte=True)


async def _werte_und_chrom(campaign_id: str, person_id: str) -> tuple[dict[str, int], int]:
    return await _werte_von(campaign_id, person_id), await _chrom_mod(campaign_id, person_id)


async def _party_und_ort_automatisch_aufnehmen(campaign_id: str, kampf: dict | None) -> dict | None:
    """Beim Kampfbeginn automatisch alle PCs/NPCs der aktiven Party sowie am
    selben Aufenthaltsort (Ort/Event) in die Initiative aufnehmen.

    Mark, 05.11.2026: "alle PCs und NPCs in der aktiven Party, oder dem
    Ort/Event mit dem die aktive Party gerade verbunden ist" automatisch
    aufnehmen, "so dass ich sie nicht alle raussuchen muss" — die Suche im
    Auswahlfeld war ihm zu unübersichtlich. Initiative wird vorgeschlagen,
    nicht gewürfelt (dieselbe Formel wie beim manuellen Hinzufügen im
    Kampfmodus-Frontend: `traits/bogen.py::initiative`) — der bestehende
    "NPC-Initiative"-Knopf würfelt danach wie gewohnt für alle Nicht-PCs.
    Inaktive Drohnen/Fahrzeuge bleiben außen vor (dieselbe Regel wie beim
    manuellen Hinzufügen, siehe `teilnehmer_hinzu` oben).
    """
    if kampf is None:
        return None
    kandidaten = await party_repository.kampf_kandidaten(campaign_id)
    for p in kandidaten:
        person = await get_node("Person", PERSON_FIELDS, campaign_id, p["id"])
        if person is None:
            continue
        ist_drohne = bool(person.get("istDrohne") or person.get("istFahrzeug"))
        if ist_drohne and not person.get("riggerAktiv"):
            continue
        werte, chrom = await _werte_und_chrom(campaign_id, p["id"])
        kampf = await repository.teilnehmer_hinzu(
            campaign_id,
            {
                "name": p["name"],
                "initiative": bogen_initiative(werte, chrom, ist_drohne),
                "kampfart": "NAHKAMPF",
                "notiz": "",
                "personId": p["id"],
                "begleiterId": None,
            },
        )
    return kampf


@router.post("", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def beginne(campaign_id: str):
    kampf = await repository.beginne(campaign_id)
    kampf = await _party_und_ort_automatisch_aufnehmen(campaign_id, kampf)
    return await _kampf_antworten(kampf)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_campaign_gm)])
async def beende(campaign_id: str):
    kampf = await repository.hole(campaign_id)
    karte_id = kampf.get("battlemapId") if kampf else None
    await repository.beende(campaign_id)
    if karte_id:
        await karten_verteiler.rundrufen(
            karte_id,
            {"typ": "tokens", "daten": token_stand({"amZug": None, "battlemapId": None, "teilnehmer": []})},
        )


async def _fog_an(kampf: dict | None) -> bool:
    if not kampf or not kampf.get("_campaignId"):
        return False
    werte = await get_einstellungen(kampf["_campaignId"])
    return bool(werte.get("fogOfWar"))


async def _waende(kampf: dict) -> list:
    cid = kampf.get("_campaignId")
    kid = kampf.get("battlemapId")
    if not cid or not kid:
        return []
    from app.battlemap import repository as karten_repo

    karte = await karten_repo.holen(cid, kid)
    return list((karte or {}).get("waende") or [])


async def _speicher_frisch(kampf: dict) -> dict:
    from app.battlemap.sicht import aktualisiere, start_speicher

    speicher = kampf.get("_sichtSpeicher") or {}
    teilnehmer = karten_liste(kampf)
    waende = await _waende(kampf)
    kampf["_waende"] = waende
    speicher = start_speicher(teilnehmer, waende) if not speicher else aktualisiere(teilnehmer, speicher, waende)
    cid = kampf.get("_campaignId")
    if cid:
        await repository.setze_sicht(cid, speicher)
    kampf["_sichtSpeicher"] = speicher
    return speicher


async def _live_sicht_ids(campaign_id: str | None) -> set[str]:
    """Wer gerade Matrix-Hot-Live-Sicht hat: einmal erfolgreich gepingt,

    während Hot (`stand["matrixLiveSicht"]`), UND aktuell noch Hot — geprüft
    live, damit ein ausgeschaltetes Hot die Sicht sofort wieder entzieht,
    ohne dass jede Hot-Aus-Stelle diese Liste separat aufräumen muss.
    """
    if not campaign_id:
        return set()
    kampf = await matrix_store.lade(campaign_id)
    if not kampf:
        return set()
    kandidaten = list(kampf["stand"].get("matrixLiveSicht") or [])
    if not kandidaten:
        return set()
    live: set[str] = set()
    for pid in kandidaten:
        zustand = await repository.hot_lesen(campaign_id, pid)
        if zustand.get("matrixHot"):
            live.add(pid)
    return live


def _karte_fuer(
    kampf: dict,
    speicher: dict,
    rolle: str,
    person_id: str | None,
    live_sicht_ids: frozenset[str] = frozenset(),
    fog_an: bool = True,
) -> list[dict]:
    """Was dieser Betrachter auf der Karte bekommt. Ein Decker mit Matrix-Hot-
    Live-Sicht (06.11.2026) bekommt dieselbe ungefilterte Wahrheit wie die SL —
    auch ohne `fuer_spieler`-Alias, denn „wie die SL sehen“ heißt auch echte
    Namen.

    Ist Fog of War campaignweit aus, gilt „wie bisher“: Wahrheit statt
    Erinnerung/Kegel, Versteckt und Wände bleiben trotzdem wirksam
    (`ansicht_waende`, Bugfix 06.11.2026 — der Schalter wurde bisher nirgends
    gelesen)."""
    if rolle != "GM" and person_id and person_id in live_sicht_ids:
        return [dict(t) for t in karten_liste(kampf)]

    from app.battlemap.sicht import ansicht, ansicht_waende

    if rolle != "GM" and not fog_an:
        gesehen = ansicht_waende(
            karten_liste(kampf),
            rolle=rolle,
            person_id=person_id,
            waende=kampf.get("_waende"),
        )
    else:
        gesehen = ansicht(
            karten_liste(kampf),
            speicher,
            rolle=rolle,
            person_id=person_id,
            waende=kampf.get("_waende"),
        )
    if rolle != "GM":
        gesehen = fuer_spieler(
            gesehen,
            rassen=kampf.get("_rassen") or {},
            eigene_person_id=person_id,
            begleiter_besitzer=kampf.get("_begleiterBesitzer") or {},
            npc_ids=kampf.get("_npcIds") or set(),
            drohnen_besitzer=kampf.get("_drohnenBesitzer") or {},
        )
    return gesehen


async def _fuer_spieler_kampf(kampf: dict, person_id: str | None, *, karte: bool = False) -> dict:
    """HTTP-Antwort für einen Spieler. Die Initiativliste bleibt gefaltet.
    Die Karte bekommt die Sicht, inklusive Erinnerungen und der Hot-Drohne."""
    kampf = dict(kampf)
    if karte:
        if kampf.get("_waende") is None:
            kampf["_waende"] = await _waende(kampf)
        speicher = kampf.get("_sichtSpeicher") or await _speicher_frisch(kampf)
        live_ids = await _live_sicht_ids(kampf.get("_campaignId"))
        fog_an = await _fog_an(kampf)
        kampf["teilnehmer"] = _karte_fuer(kampf, speicher, "PLAYER", person_id, frozenset(live_ids), fog_an)
    else:
        kampf["teilnehmer"] = fuer_spieler(
            kampf.get("teilnehmer") or [],
            rassen=kampf.get("_rassen") or {},
            eigene_person_id=person_id,
            begleiter_besitzer=kampf.get("_begleiterBesitzer") or {},
            npc_ids=kampf.get("_npcIds") or set(),
            drohnen_besitzer=kampf.get("_drohnenBesitzer") or {},
        )
    return _ohne_hilfsfelder(kampf) or kampf


async def _tokens_senden(kampf: dict | None) -> None:
    if not kampf or not kampf.get("battlemapId"):
        return
    waende = await _waende(kampf)
    kampf["_waende"] = waende
    speicher = await _speicher_frisch(kampf)
    live_ids = frozenset(await _live_sicht_ids(kampf.get("_campaignId")))
    fog_an = await _fog_an(kampf)

    def bauen(verbindung):
        if verbindung.rolle == "GM":
            teilnehmer = karten_liste(kampf)
        else:
            teilnehmer = _karte_fuer(kampf, speicher, verbindung.rolle, verbindung.person_id, live_ids, fog_an)
        stand = token_stand({**kampf, "teilnehmer": teilnehmer})
        stand["waende"] = waende
        return {"typ": "tokens", "daten": stand}

    await karten_verteiler.rundrufen_je(kampf["battlemapId"], bauen)


async def _kampf_antworten(kampf: dict | None) -> dict | None:
    """Mutation: Tokens live raus, Hilfsfelder runter."""
    await _tokens_senden(kampf)
    return _ohne_hilfsfelder(kampf)


@router.put("/karte", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def karte_anhaengen(campaign_id: str, body: KarteAnKampf):
    kampf = await repository.setze_karte(campaign_id, body.battlemapId)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    await _tokens_senden(kampf)
    return await _kampf_antworten(kampf)


@router.patch("/teilnehmer/{teilnehmer_id}/position", response_model=KampfResponse)
async def token_schieben(
    campaign_id: str,
    teilnehmer_id: str,
    body: PositionUpdate,
    viewer: Viewer = Depends(get_viewer),
):
    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    token = _finde_token(kampf, teilnehmer_id)
    if token is None or token.get("zusatzzug"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teilnehmer nicht gefunden")
    sonder = _hot_darf(kampf, token, viewer)
    am_zug_eintrag = next((t for t in kampf["teilnehmer"] if t["id"] == kampf.get("amZug")), None)
    am_zug = False
    if sonder is True:
        am_zug = True
    elif sonder is False:
        am_zug = False
    elif am_zug_eintrag:
        am_zug = am_zug_eintrag["id"] == token["id"] or (
            token.get("personId") and am_zug_eintrag.get("personId") == token.get("personId")
        )
    besitzer = token.get("besitzerId") or (kampf.get("_drohnenBesitzer") or {}).get(token.get("personId"))
    if not besitzer and token.get("begleiterId"):
        besitzer = (kampf.get("_begleiterBesitzer") or {}).get(token.get("begleiterId"))
    if not darf_schieben(
        rolle=viewer.role,
        person_id=viewer.person_id,
        token_person_id=token.get("personId"),
        besitzer_id=besitzer,
        am_zug=bool(am_zug),
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teilnehmer nicht gefunden")
    belegt = repository._belegt_karte(karten_liste(kampf), ausser_id=token["id"])
    if not drop_frei(
        body.q,
        body.r,
        gross=bool(token.get("istGross")),
        drehung=body.drehung,
        eigene_id=token["id"],
        belegt=belegt,
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, "Feld belegt")
    from app.battlemap.sicht import sektor

    blick = int(token.get("blickrichtung") or 0)
    if token.get("hexQ") is not None and (token.get("hexQ") != body.q or token.get("hexR") != body.r):
        richtung = sektor(int(token["hexQ"]), int(token["hexR"]), body.q, body.r)
        if richtung is not None:
            blick = richtung
    kampf = await repository.setze_token_position(
        campaign_id, teilnehmer_id, body.q, body.r, body.drehung, zug_start=bool(am_zug)
    )
    if kampf:
        kampf = await repository.setze_blick(campaign_id, teilnehmer_id, blick)
    await _tokens_senden(kampf)
    if viewer.role != "GM" and kampf:
        return await _fuer_spieler_kampf(kampf, viewer.person_id, karte=True)
    return await _kampf_antworten(kampf)


def _finde_token(kampf: dict, teilnehmer_id: str) -> dict | None:
    for quelle in (kampf.get("teilnehmer") or [], kampf.get("_hotDrohnen") or []):
        for eintrag in quelle:
            if eintrag.get("id") == teilnehmer_id and not eintrag.get("zusatzzug"):
                return eintrag
    return None


def _hot_darf(kampf: dict, token: dict, viewer: Viewer) -> bool | None:
    """None = normale Regel. False = Körper bleibt liegen. True = Drohne am Rigger-Zug."""
    if viewer.role == "GM":
        return None
    if token.get("hotKoerper"):
        return False
    if not token.get("hotGesteuert"):
        return None
    rigger = next(
        (
            t for t in kampf.get("teilnehmer") or []
            if t.get("hotKoerper") and t.get("personId") == token.get("besitzerId")
        ),
        None,
    )
    return bool(rigger and kampf.get("amZug") == rigger.get("id") and token.get("besitzerId") == viewer.person_id)


def _darf_token(viewer: Viewer, token: dict, kampf: dict, *, nur_am_zug: bool) -> bool:
    sonder = _hot_darf(kampf, token, viewer)
    if sonder is not None:
        return sonder
    am_zug_eintrag = next((t for t in kampf["teilnehmer"] if t["id"] == kampf.get("amZug")), None)
    am_zug = False
    if am_zug_eintrag:
        am_zug = am_zug_eintrag["id"] == token["id"] or (
            token.get("personId") and am_zug_eintrag.get("personId") == token.get("personId")
        )
    besitzer = token.get("besitzerId") or (kampf.get("_drohnenBesitzer") or {}).get(token.get("personId"))
    if not besitzer and token.get("begleiterId"):
        besitzer = (kampf.get("_begleiterBesitzer") or {}).get(token.get("begleiterId"))
    if viewer.role == "GM":
        return True
    if not viewer.person_id:
        return False
    eigener = token.get("personId") == viewer.person_id or besitzer == viewer.person_id
    if not eigener:
        return False
    return bool(am_zug) if nur_am_zug else True


@router.patch("/teilnehmer/{teilnehmer_id}/blick", response_model=KampfResponse)
async def token_umschauen(
    campaign_id: str,
    teilnehmer_id: str,
    body: BlickUpdate,
    viewer: Viewer = Depends(get_viewer),
):
    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    token = _finde_token(kampf, teilnehmer_id)
    if token is None or not _darf_token(viewer, token, kampf, nur_am_zug=True):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teilnehmer nicht gefunden")
    kampf = await repository.setze_blick(campaign_id, teilnehmer_id, int(body.blickrichtung) % 6)
    await _tokens_senden(kampf)
    if viewer.role != "GM" and kampf:
        return await _fuer_spieler_kampf(kampf, viewer.person_id, karte=True)
    return await _kampf_antworten(kampf)


@router.patch("/teilnehmer/{teilnehmer_id}/versteckt", response_model=KampfResponse)
async def token_verstecken(
    campaign_id: str,
    teilnehmer_id: str,
    body: VerstecktUpdate,
    viewer: Viewer = Depends(get_viewer),
):
    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    token = _finde_token(kampf, teilnehmer_id)
    if token is None or not _darf_token(viewer, token, kampf, nur_am_zug=False):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teilnehmer nicht gefunden")
    kampf = await repository.setze_versteckt(campaign_id, teilnehmer_id, body.versteckt)
    await _tokens_senden(kampf)
    if viewer.role != "GM" and kampf:
        return await _fuer_spieler_kampf(kampf, viewer.person_id, karte=True)
    return await _kampf_antworten(kampf)


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
    return await _kampf_antworten(kampf)


@router.patch("/teilnehmer/{teilnehmer_id}", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_aendern(campaign_id: str, teilnehmer_id: str, body: TeilnehmerUpdate):
    kampf = await repository.teilnehmer_aendern(campaign_id, teilnehmer_id, body.model_dump())
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return await _kampf_antworten(kampf)


@router.delete("/teilnehmer/{teilnehmer_id}", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def teilnehmer_entfernen(campaign_id: str, teilnehmer_id: str):
    kampf = await repository.teilnehmer_entfernen(campaign_id, teilnehmer_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return await _kampf_antworten(kampf)


@router.post("/weiter", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def weiter(campaign_id: str):
    """Einen Zug weiter. Am Ende der Liste beginnt die nächste Runde."""
    kampf = await repository.weiter(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return await _kampf_antworten(kampf)


@router.post("/amzug", response_model=KampfResponse, dependencies=[Depends(require_campaign_gm)])
async def am_zug(campaign_id: str, body: AmZugInput):
    """Direkt jemanden ans Ruder setzen — für den Fall, dass es durcheinander ging."""
    kampf = await repository.setze_am_zug(campaign_id, body.teilnehmerId)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return await _kampf_antworten(kampf)


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
    return await _kampf_antworten(kampf)


@router.post("/ich", response_model=KampfResponse)
async def selbst_initiative(
    campaign_id: str,
    body: InitiativeInput,
    viewer: Viewer = Depends(get_viewer),
):
    """Eigene Initiative eintragen, auch wenn die SL einen noch nicht aufgenommen hat.

    Klick auf die Initiative-Zahl im Kampfmenü. Steht der Charakter schon in
    der Liste, wird nur der Wert gesetzt. Sonst kommt er mit diesem Wert dazu.
    Drohnen und Beschwörungen laufen über ihre eigenen Wege, nicht hier.
    """
    if viewer.role == "GM" or not viewer.person_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Nur für den eigenen Charakter")

    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")

    try:
        wert = melde_wert(body.erfolge)
    except ValueError as fehler:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(fehler)) from fehler

    eigener = eigener_haupteintrag(kampf["teilnehmer"], viewer.person_id)
    if eigener:
        kampf = await repository.teilnehmer_aendern(campaign_id, eigener["id"], {"initiative": wert})
        return await _kampf_antworten(kampf)

    person = await get_node("Person", PERSON_FIELDS, campaign_id, viewer.person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Charakter nicht gefunden")

    kampf = await repository.teilnehmer_hinzu(
        campaign_id,
        {
            "name": person.get("name") or "Charakter",
            "initiative": wert,
            "kampfart": "NAHKAMPF",
            "notiz": "",
            "personId": viewer.person_id,
            "begleiterId": None,
        },
    )
    return await _kampf_antworten(kampf)


async def _darf_initiative_melden(campaign_id: str, viewer: Viewer, ziel_person_id: str | None) -> bool:
    """Wie `darf_melden`, nur zusätzlich: der Rigger darf auch für seine
    eigene(n) aktive(n) Drohne(n)/Fahrzeug(e) melden (26.10.2026, Mark:
    \"er geht ins Popup rein, klickt da drauf und seine Drohnen fügen sich
    automatisch in die Initiativreihenfolge ein\"). Ein Teilnehmer ohne
    `personId` ("Wachmann 1") bleibt für Spieler tabu, wie bisher.

    Beschwörungs-Ki-Tama (30.10.2026): derselbe Vorbehalt gilt für den
    Beschwörer eines Critters — dieselbe Beziehung wie Rigger/Drohne, nur
    über `critter_besitzer` statt `drohne_rigger`.
    """
    if darf_melden(viewer.role, viewer.person_id, ziel_person_id):
        return True
    if viewer.role == "GM" or not ziel_person_id or not viewer.person_id:
        return False
    rigger_id = await drohne_rigger(campaign_id, ziel_person_id)
    if rigger_id is not None and rigger_id == viewer.person_id:
        return True
    beschwoerer_id = await critter_besitzer(campaign_id, ziel_person_id)
    return beschwoerer_id is not None and beschwoerer_id == viewer.person_id


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
        return await _kampf_antworten(kampf)

    name = await _mit_nummer_falls_doppelt(campaign_id, kampf["teilnehmer"], drohne["name"])
    kampf = await repository.teilnehmer_hinzu(
        campaign_id,
        {"name": name, "initiative": 0, "kampfart": "FERNKAMPF", "notiz": "", "personId": node_id, "begleiterId": None},
    )
    return await _kampf_antworten(kampf)


class BeschwoerenInput(BaseModel):
    """Selbstberichtete Beschwörungs-Probe (Intelligenz + Beschwörungswert).
    Erfolge würfelt der Spieler physisch am Tisch wie überall sonst im Tool
    — die Zahl entscheidet nur, OB der Critter dem Kampf beitreten darf,
    seine eigene Initiative wird separat über das schon bestehende
    `POST .../teilnehmer/{id}/initiative` gemeldet (wie bei Drohnen).

    `ausgang` ist explizit, weil 0 Erfolge kein Patzer sind (01.11.2026):
    ja = gelungen, nein = Fehlwurf (Ruf bleibt), patzer = Ruf weg, kein Critter.
    """

    erfolge: int = Field(default=0, ge=0)
    ausgang: Literal["ja", "nein", "patzer"] = "ja"


@router.post("/gegenstaende/{item_id}/beschwoeren", response_model=KampfResponse)
async def item_beschwoeren(campaign_id: str, item_id: str, body: BeschwoerenInput, viewer: Viewer = Depends(get_viewer)):
    """Self-Service (30.10.2026): der Besitzer eines Beschwörungs-Ki-Tama
    beschwört seinen gebundenen Critter in den laufenden Kampf, sobald er
    genug Erfolge gewürfelt hat — Mark: "wir müssen bevor man die initiative
    eingibt noch die probe im kampf menü einbauen". Danach läuft alles
    weiter wie bei einer Drohne: Initiative startet bei 0, wird direkt
    danach über `melde_initiative` gesetzt (eigene Zeile im Tracker, kein
    Hot-Drohne-Slot-Sharing). Gleiche 404-statt-403-Logik wie bei
    `drohne_dem_kampf_beitreten` — ein fremdes Item soll nicht einmal als
    existierend erkennbar sein.
    """
    item = await get_gegenstand(campaign_id, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    besitzer_id = await get_owner_person_id(campaign_id, item_id)
    if viewer.role != "GM" and (besitzer_id is None or besitzer_id != viewer.person_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")

    critter_id = item.get("beschworenerCritterId") or ""
    if not critter_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Kein Beschwörungs-Ki-Tama — kein Critter verknüpft.")

    # Mark, 30.10.2026 (zweite Runde nach dem Klicktest): "Ki-Tamas dürfen nur
    # dann funktionieren wenn sie mit einer Waffe verbunden sind, und wenn die
    # Waffe ausgerüstet ist" — dieselbe Regel wie bei den Ki-Tama-Attacken in
    # Kampfkarte.tsx, hier serverseitig durchgesetzt (das Frontend blendet den
    # Beschwören-Knopf zwar schon vorher aus, aber dieser Endpunkt ist auch
    # direkt erreichbar und muss selbst prüfen).
    traeger_id = item.get("montiertAnId")
    traeger = await get_gegenstand(campaign_id, traeger_id) if traeger_id else None
    if traeger is None or not (traeger.get("typ") == "Waffe" or traeger.get("istWaffe")) or traeger.get("ablage") != "AUSGERUESTET":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ki-Tama muss an einer ausgerüsteten Waffe montiert sein, um zu wirken.",
        )

    stufe = beschwoerungsstufe(item.get("ausruestungsfertigkeiten") or {}, item.get("kiTamaFertigkeiten") or {})
    benoetigt = beschwoerung_benoetigte_erfolge(stufe, int(item.get("beschwoerungsSchwierigkeit") or 0))

    kampf = await repository.hole(campaign_id)
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")

    schon = item_id in (kampf.get("verbrauchteBeschwoerungen") or [])
    entscheidung = ruf_entscheidung(body.ausgang, schon, body.erfolge, benoetigt)
    if entscheidung == "blockiert":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Diese Beschwörung wurde in diesem Kampf schon gerufen.",
        )
    if entscheidung == "zu-wenig":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Beschwörung misslungen — {benoetigt} Erfolge nötig, {body.erfolge} erzielt.",
        )
    if entscheidung == "offen":
        return await _kampf_antworten(kampf)
    if entscheidung == "verbraucht":
        await repository.beschwoerung_verbrauchen(campaign_id, item_id)
        return await _kampf_antworten(await repository.hole(campaign_id))

    critter = await get_node("Person", PERSON_FIELDS, campaign_id, critter_id)
    if critter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verknüpfter Critter nicht (mehr) gefunden")

    bereits_dabei = next((t for t in kampf["teilnehmer"] if t.get("personId") == critter_id), None)
    await repository.beschwoerung_verbrauchen(campaign_id, item_id)
    if bereits_dabei:
        return await _kampf_antworten(await repository.hole(campaign_id))

    name = await _mit_nummer_falls_doppelt(campaign_id, kampf["teilnehmer"], critter.get("name") or "Beschworener Critter")
    await repository.teilnehmer_hinzu(
        campaign_id,
        {
            "name": name,
            "initiative": 0,
            "kampfart": "NAHKAMPF",
            "notiz": "",
            "personId": critter_id,
            "begleiterId": None,
            "rundenVerbleibend": stufe,
        },
    )
    return await _kampf_antworten(await repository.hole(campaign_id))


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

    return await _kampf_antworten(await repository.hole(campaign_id))


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
    # Decker war schon Hot, die Bleiben-Frage ist noch offen. Erst die, dann die Zusatzaktion.
    matrixBleibenOffen: bool = False


async def _booster_von(campaign_id: str, person_id: str) -> dict | None:
    """Stärkstes Stück mit Zusatzaktionen.

    Verbautes Chrom zählt immer. Das ausgerüstete Deck nur, solange der
    Decker Hot ist — sonst wäre die Freischaltung nur ein Schalter ohne Tür.
    """
    stuecke = await verbautes_chrom(campaign_id, person_id)
    from app.items.drogen import zusatz as drogen_zusatz
    drogen_booster = await drogen_zusatz(campaign_id, person_id)
    zustand = await repository.hot_lesen(campaign_id, person_id)
    decks = await ausgeruestete_decks(campaign_id, person_id) if zustand["matrixHot"] else []
    deck = staerkstes(decks)
    return staerkstes(booster_kandidaten(stuecke, deck, zustand["matrixHot"]) + drogen_booster)


async def _person_der_aktion(
    campaign_id: str,
    viewer: Viewer,
    person_id: str | None,
    *,
    schreiben: bool,
) -> str | None:
    """Spieler: immer die eigene Person. SL: der genannte NPC, nie ein PC.

    Lesen ohne Ziel liefert None (leerer Status). Schreiben ohne Ziel ist
    ein Fehler — sonst zündet die SL ins Leere.
    """
    ziel_typ = None
    if viewer.role == "GM" and person_id:
        person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
        # None = Knoten fehlt. Leerer Typ am vorhandenen Knoten ist kein PC.
        ziel_typ = None if person is None else (person.get("personType") or "")
    gewaehlt, fehler = waehle_person(
        viewer.role,
        viewer.person_id,
        person_id,
        ziel_typ,
        schreiben=schreiben,
    )
    if fehler:
        code, text = person_fehler_http(fehler)
        raise HTTPException(code, text)
    return gewaehlt


class HotStatus(BaseModel):
    hatNeurolink: bool = False
    hatDeck: bool = False
    matrixHot: bool = False
    matrixBleibenFaellig: bool = False
    hotDrohneId: str | None = None
    hotDrohneName: str | None = None
    bleibenFaellig: bool = False
    darfWaehlen: bool = False


class HotInput(BaseModel):
    drohneId: str | None = None
    bleiben: bool | None = None
    matrix: bool | None = None
    matrixBleiben: bool | None = None
    # Nur die SL: für welchen NPC. Spieler-Angaben werden ignoriert.
    personId: str | None = None


async def _hot_status(campaign_id: str, person_id: str) -> HotStatus:
    verlust = await matrix_store.hot_wegen_aus(campaign_id, person_id)
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
        hatNeurolink=hat_neurolink(chrom) and verlust != "alles",
        hatDeck=bool(decks),
        matrixHot=zustand["matrixHot"],
        matrixBleibenFaellig=matrix_bleiben_faellig(
            zustand["matrixHot"], zustand["matrixHotRunde"], runde, ist_dran
        ),
        hotDrohneId=zustand["hotDrohneId"],
        hotDrohneName=zustand["hotDrohneName"],
        bleibenFaellig=bleiben_faellig(
            zustand["hotDrohneId"], zustand["hotDrohneRunde"], runde, ist_dran
        ),
        darfWaehlen=verlust == "" and darf_drohne_waehlen(zustand["hotDrohneId"], zustand["hotDrohneRunde"], runde),
    )


@router.get("/hot", response_model=HotStatus)
async def hot_status(
    campaign_id: str,
    viewer: Viewer = Depends(get_viewer),
    person_id: str | None = Query(default=None, alias="personId"),
):
    """Hot-Zustand. Spieler: der eigene. SL: der genannte NPC, sonst leer."""
    ziel = await _person_der_aktion(campaign_id, viewer, person_id, schreiben=False)
    if not ziel:
        return HotStatus()
    return await _hot_status(campaign_id, ziel)


@router.post("/hot", response_model=HotStatus)
async def hot_setzen(campaign_id: str, body: HotInput, viewer: Viewer = Depends(get_viewer)):
    """Hot gehen: Matrix-Knopf, Drohne an der Slot-Box, oder Bleiben-Antwort.

    Die SL nennt die NPC-Person. Ohne personId, aber mit drohneId, hängt
    die Drohne an ihrem Rigger — der muss ebenfalls ein NPC sein.
    """
    ziel = body.personId
    if viewer.role == "GM" and not ziel and body.drohneId:
        ziel = await drohne_rigger(campaign_id, body.drohneId)
        if not ziel:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Drohne/Fahrzeug nicht gefunden")
    person_id = await _person_der_aktion(campaign_id, viewer, ziel, schreiben=True)
    if person_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein eigener Charakter")
    kampf = await repository.hole(campaign_id)
    runde = kampf["runde"] if kampf else None
    zustand = await repository.hot_lesen(campaign_id, person_id)
    chrom = await verbautes_chrom(campaign_id, person_id)

    verlust = await matrix_store.hot_wegen_aus(campaign_id, person_id)
    if verlust == "alles":
        raise HTTPException(status.HTTP_409_CONFLICT, "Ohne Neurolink kein Hot.")
    if verlust == "drohne" and body.drohneId:
        raise HTTPException(status.HTTP_409_CONFLICT, "Die Konsole ist aus.")

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

    if body.matrixBleiben is not None:
        eigener = None
        if kampf:
            eigener = next(
                (t for t in kampf["teilnehmer"] if t.get("personId") == person_id and not t.get("zusatzzug")),
                None,
            )
        ist_dran = bool(eigener and kampf and kampf["amZug"] == eigener["id"])
        if not matrix_bleiben_faellig(zustand["matrixHot"], zustand["matrixHotRunde"], runde, ist_dran):
            raise HTTPException(status.HTTP_409_CONFLICT, "Gerade steht die Frage nicht an.")
        bleibt, neue_runde = beantworte_matrix(body.matrixBleiben, runde)
        await repository.hot_schreiben(
            campaign_id,
            person_id,
            hot_drohne_id=zustand["hotDrohneId"],
            hot_runde=zustand["hotDrohneRunde"],
            matrix_hot=bleibt,
            matrix_hot_runde=neue_runde,
        )
        return await _hot_status(campaign_id, person_id)

    if body.matrix is not None:
        if not body.matrix:
            raise HTTPException(status.HTTP_409_CONFLICT, "Hot bleibt, bis du wieder dran bist.")
        await repository.hot_schreiben(
            campaign_id,
            person_id,
            hot_drohne_id=zustand["hotDrohneId"],
            hot_runde=zustand["hotDrohneRunde"],
            matrix_hot=True,
            matrix_hot_runde=runde if runde is not None else 0,
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
async def booster_status(
    campaign_id: str,
    viewer: Viewer = Depends(get_viewer),
    person_id: str | None = Query(default=None, alias="personId"),
):
    """Boosterzustand für das Popup beim Drankommen.

    Spieler: der eigene Charakter. SL: der genannte NPC — sie steuert alle
    NPCs und bekommt dasselbe Fenster, wenn der dran ist.
    """
    ziel = await _person_der_aktion(campaign_id, viewer, person_id, schreiben=False)
    if not ziel:
        return BoosterStatus()

    booster = await _booster_von(campaign_id, ziel)
    if booster is None:
        return BoosterStatus()

    kampf = await repository.hole(campaign_id)
    eigener = None
    if kampf:
        eigener = next(
            (
                t
                for t in kampf["teilnehmer"]
                if t.get("personId") == ziel and not t.get("zusatzzug")
            ),
            None,
        )

    werte = await _werte_von(campaign_id, ziel)
    ampel = eigener["ampel"] if eigener else 0
    genutzt = eigener["zusatzGenutzt"] if eigener else 0
    maximal = int(booster.get("zusatzaktionen") or 0)
    zustand = await repository.hot_lesen(campaign_id, ziel)
    runde = kampf["runde"] if kampf else None
    ist_dran = bool(eigener and kampf and kampf["amZug"] == eigener["id"])

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
        matrixBleibenOffen=matrix_bleiben_faellig(
            zustand["matrixHot"], zustand["matrixHotRunde"], runde, ist_dran
        ),
    )


class AktivierenInput(BaseModel):
    """Der selbst gewürfelte Zweitwurf (Anzahl Erfolge)."""

    erfolge: int = Field(ge=0)
    # Nur die SL: für welchen NPC. Spieler-Angaben werden ignoriert.
    personId: str | None = None


@router.post("/booster/aktivieren", response_model=KampfResponse)
async def booster_aktivieren(
    campaign_id: str,
    body: AktivierenInput,
    viewer: Viewer = Depends(get_viewer),
):
    """Reflex-Booster zünden: zweiter Eintrag in der Initiativliste.

    Spieler entscheidet im Popup für sich. Die SL für den NPC, der dran ist.
    Geprüft wird serverseitig: Booster verbaut, Aktionen übrig, kein PC.
    """
    person_id = await _person_der_aktion(campaign_id, viewer, body.personId, schreiben=True)
    if person_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein eigener Charakter")
    booster = await _booster_von(campaign_id, person_id)
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

    return await _kampf_antworten(await repository.hole(campaign_id))


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
    return await _kampf_antworten(await repository.hole(campaign_id))


@router.post("/teilnehmer/{teilnehmer_id}/aussetzen-beendet", response_model=KampfResponse,
             dependencies=[Depends(require_campaign_gm)])
async def aussetzen_beendet(campaign_id: str, teilnehmer_id: str):
    """Hebt das Aussetzen auf — der Eintrag wird wieder normal dargestellt.

    Mark: *"und wird dann wieder dunkel wenn darüber rotiert wurde"*.
    """
    kampf = await repository.teilnehmer_aendern(campaign_id, teilnehmer_id, {"setztAus": False})
    if kampf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kein laufender Kampf")
    return await _kampf_antworten(kampf)
