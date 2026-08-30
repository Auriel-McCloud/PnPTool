from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_campaign
from app.entities.repository import PERSON_FIELDS, get_node, update_node
from app.items.repository import commlink_cyberwall
from app.traits import erfahrung, erstellung, repository
from app.traits.bogen import bogen_uebersicht, sichtbare_kategorien, willenskraft_max
from app.traits.schemas import TraitDefResponse, TraitRatingResponse, TraitRatingUpdate
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/campaigns/{campaign_id}", tags=["traits"], dependencies=[Depends(require_campaign_zugang)])


@router.get("/traitkatalog", response_model=list[TraitDefResponse])
async def get_catalog(campaign_id: str):
    campaign = await get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne nicht gefunden")
    return await repository.list_catalog(campaign["ruleset"])


@router.get("/personen/{person_id}/werte", response_model=list[TraitRatingResponse])
async def get_werte(campaign_id: str, person_id: str, viewer: Viewer = Depends(get_viewer)):
    """Werte einer Person.

    **Spieler sehen ausschliesslich ihren eigenen Charakter** — fremde
    Charakterbögen sind tabu, weder von Mitspielern noch von NPCs. 404 statt
    403, damit die Existenz der Person nicht bestätigt wird.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    return await repository.get_ratings_for_entity(campaign_id, person_id)


@router.get("/personen/{person_id}/bogen")
async def get_bogen(campaign_id: str, person_id: str, viewer: Viewer = Depends(get_viewer)) -> dict:
    """Alles fuer das Charakterblatt in einer Antwort.

    Fasst Katalog, gesetzte Werte und die abgeleiteten Groessen zusammen —
    das Blatt braucht sie ohnehin immer gemeinsam, und einzeln geladen waeren
    es drei Abfragen, deren Ergebnisse zueinander passen muessen.

    Der Katalog ist bereits nach dem eingeschlagenen Weg gefiltert: wer kein
    Magier ist, bekommt Sphaeren und Arete gar nicht erst zu sehen.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    campaign = await get_campaign(campaign_id)
    katalog = await repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)

    nach_name = {w["name"]: w["rating"] for w in werte}
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    erlaubt = sichtbare_kategorien(person.get("weg") or "KEINER", {t["category"] for t in katalog})

    return {
        "person": {"id": person["id"], "name": person["name"], "personType": person["personType"]},
        "uebersicht": bogen_uebersicht(person, nach_name, cyberwall),
        "katalog": [t for t in katalog if t["category"] in erlaubt],
        "werte": werte,
    }


@router.put("/personen/{person_id}/werte/{trait_def_id}", response_model=TraitRatingResponse, dependencies=[Depends(require_campaign_gm)])
async def set_wert(campaign_id: str, person_id: str, trait_def_id: str, body: TraitRatingUpdate):
    result = await repository.set_rating(campaign_id, person_id, trait_def_id, body.rating, body.maxOverride)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person oder Fähigkeit nicht gefunden")
    return result


class ZustandUpdate(BaseModel):
    """Was ein Spieler an sich selbst ändern darf.

    Ausdrücklich **nur Zustand**, keine Werte: Schaden abhaken und Willenskraft
    verbrauchen gehört zum Spielen, Punkte vergeben nicht. Alles andere bleibt
    der Spielleitung vorbehalten.
    """

    schadenSchlag: int | None = Field(default=None, ge=0)
    schadenSchwer: int | None = Field(default=None, ge=0)
    schadenAggraviert: int | None = Field(default=None, ge=0)
    willenskraftVerbraucht: int | None = Field(default=None, ge=0)
    iceSchaden: int | None = Field(default=None, ge=0)


@router.patch("/personen/{person_id}/zustand")
async def set_zustand(
    campaign_id: str,
    person_id: str,
    body: ZustandUpdate,
    viewer: Viewer = Depends(get_viewer),
) -> dict:
    """Schaden eintragen und Willenskraft verbrauchen.

    Zweite Route, die auch Spieler schreiben dürfen — und wie beim Umlegen
    von Gegenständen streng begrenzt: nur am eigenen Charakter und nur diese
    Felder. 404 bei fremden Personen, damit deren Existenz nicht bestätigt
    wird. Steht dafür in der Ausnahmeliste von tests/test_zugriffsschutz.py.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await update_node("Person", PERSON_FIELDS, campaign_id, person_id, body.model_dump())
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    return bogen_uebersicht(person, {w["name"]: w["rating"] for w in werte}, cyberwall)


# =====================================================================
# Charaktererstellung
# =====================================================================


class ErstellungInput(BaseModel):
    """Eine eingereichte Charaktererstellung.

    Getrennt nach Herkunft der Punkte statt nur die Endwerte zu schicken:
    ein Wert über dem StartMax ist erlaubt, *wenn* er mit Freebees bezahlt
    wurde, und sonst nicht. Aus einer blossen Endzahl liesse sich das nicht
    mehr ablesen, die Prüfung wäre dann nur noch geraten.
    """

    weg: str = "KEINER"
    rasse: str = ""
    # Welches Kontingent der Rasse auf welche Attributspalte fällt.
    schwerpunkte: dict[str, int] = Field(default_factory=dict)
    # Verteilung innerhalb der Spalten, ohne Startwert.
    attributPunkte: dict[str, int] = Field(default_factory=dict)
    fertigkeitsPaket: str = ""
    fertigkeitPunkte: dict[str, int] = Field(default_factory=dict)
    hintergrundPunkte: dict[str, int] = Field(default_factory=dict)
    freebeePunkte: dict[str, int] = Field(default_factory=dict)
    freebeeWillenskraft: int = Field(default=0, ge=0)
    freebeeKredit: int = Field(default=0, ge=0)
    freebeeEigenkapital: int = Field(default=0, ge=0)
    konzept: str = ""
    alter: str = ""
    ambition: str = ""
    verlangen: str = ""
    ziel: str = ""


@router.get("/erstellung/regeln")
async def get_erstellungsregeln() -> dict:
    """Rassen, Pakete, Hintergründe, Freebee-Preise.

    Auch für Spieler lesbar — sie erstellen ihren Charakter selbst, und die
    Regeln sind nichts Geheimes.
    """
    return erstellung.regelwerk()


@router.post("/personen/{person_id}/erstellung")
async def erstelle_charakter(
    campaign_id: str,
    person_id: str,
    body: ErstellungInput,
    viewer: Viewer = Depends(get_viewer),
) -> dict:
    """Charaktererstellung abschliessen.

    Dritte Route, die auch Spieler schreiben dürfen — nach demselben Muster
    wie `zustand`: nur am eigenen Charakter, 404 bei fremden. Zusätzlich
    **nur einmal**: ist die Erstellung abgeschlossen, lehnt die Route ab.
    Sonst liesse sich ein gespielter Charakter jederzeit neu zusammenstellen
    und alle Erfahrung damit umverteilen. Die Spielleitung darf erneut
    einreichen — sie muss Fehler korrigieren können.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    if person.get("erstellungAbgeschlossen") and viewer.role != "GM":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Dieser Charakter ist bereits erstellt. Änderungen macht die Spielleitung.",
        )

    campaign = await get_campaign(campaign_id)
    katalog = await repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")

    auswahl = body.model_dump()
    fehler = erstellung.pruefe(auswahl, katalog)
    if fehler:
        # 422 statt 400: die Anfrage ist wohlgeformt, nur regelwidrig.
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"fehler": fehler})

    werte = erstellung.endwerte(auswahl)
    # Alles aus dem Katalog, was nicht vorkommt, ausdrücklich auf 0 — sonst
    # bliebe bei einer Korrektur durch die Spielleitung ein alter Wert stehen.
    erlaubte_kategorien = (
        {"Fertigkeit", erstellung.HINTERGRUND_KATEGORIE}
        | erstellung.KATEGORIEN_JE_WEG.get(body.weg, set())
        | set(erstellung.ATTRIBUT_KATEGORIEN)
    )
    for eintrag in katalog:
        if eintrag["name"] not in werte and eintrag["category"] in erlaubte_kategorien:
            werte[eintrag["name"]] = 0
    await repository.set_ratings_bulk(campaign_id, person_id, werte)

    vermoegen, schulden = erstellung.kapital(auswahl)
    aktualisiert = await update_node(
        "Person",
        PERSON_FIELDS,
        campaign_id,
        person_id,
        {
            "weg": body.weg,
            "rasse": body.rasse,
            "willenskraftBonus": body.freebeeWillenskraft,
            "konzept": body.konzept,
            "alter": body.alter,
            "ambition": body.ambition,
            "verlangen": body.verlangen,
            "ziel": body.ziel,
            "kapital": vermoegen,
            "schulden": schulden,
            "erstellungAbgeschlossen": True,
        },
    )

    neue_werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    return {
        "uebersicht": bogen_uebersicht(
            aktualisiert or person, {w["name"]: w["rating"] for w in neue_werte}, cyberwall
        ),
        "freebeesVerbraucht": erstellung.freebee_kosten(
            auswahl, {t["name"]: t["category"] for t in katalog}
        ),
    }


# =====================================================================
# Level Up
# =====================================================================


class SteigernInput(BaseModel):
    """Ein einzelner Punkt.

    Bewusst kein Stapel mehrerer Steigerungen: Preise hängen vom aktuellen
    Wert ab, ein Stapel müsste also in genau der eingereichten Reihenfolge
    abgerechnet werden. Einzeln ist die Abrechnung eindeutig, und ein
    abgebrochener Vorgang hinterlässt keinen halben Kauf.
    """

    # Entweder ein Katalogwert ...
    traitDefId: str | None = None
    # ... oder Willenskraft, die keiner ist.
    willenskraft: bool = False


@router.get("/personen/{person_id}/steigern")
async def get_steigerungspreise(
    campaign_id: str, person_id: str, viewer: Viewer = Depends(get_viewer)
) -> dict:
    """Was der nächste Punkt auf jedem Wert kostet."""
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    campaign = await get_campaign(campaign_id)
    katalog = await repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
    erlaubt = sichtbare_kategorien(person.get("weg") or "KEINER", {t["category"] for t in katalog})
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    nach_name = {w["name"]: w["rating"] for w in werte}
    # Vom Spielleiter angehobene Maxima gelten auch beim Steigern.
    grenzen = {w["traitDefId"]: w["max"] for w in werte}

    preise = erfahrung.preisliste([t for t in katalog if t["category"] in erlaubt], nach_name)
    for eintrag in preise:
        eintrag["max"] = grenzen.get(eintrag["traitDefId"], eintrag["max"])

    willenskraft = willenskraft_max(nach_name, int(person.get("willenskraftBonus") or 0))
    return {
        "verfuegbar": max(0, int(person.get("erfahrung") or 0) - int(person.get("erfahrungAusgegeben") or 0)),
        "gesamt": int(person.get("erfahrung") or 0),
        "werte": preise,
        "willenskraft": {
            "aktuell": willenskraft,
            "kosten": erfahrung.kosten_willenskraft(willenskraft),
        },
    }


@router.post("/personen/{person_id}/steigern")
async def steigere_wert(
    campaign_id: str,
    person_id: str,
    body: SteigernInput,
    viewer: Viewer = Depends(get_viewer),
) -> dict:
    """Einen Punkt kaufen und die Erfahrung dafür abbuchen.

    Vierte Route, die Spieler schreiben dürfen — am eigenen Charakter, und
    nur solange die Erfahrung reicht. Der Preis wird hier neu berechnet und
    **nicht** vom Client übernommen; sonst könnte man ihn selbst bestimmen.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    nach_name = {w["name"]: w["rating"] for w in werte}
    verfuegbar = max(0, int(person.get("erfahrung") or 0) - int(person.get("erfahrungAusgegeben") or 0))
    ausgegeben = int(person.get("erfahrungAusgegeben") or 0)

    if body.willenskraft:
        aktuell = willenskraft_max(nach_name, int(person.get("willenskraftBonus") or 0))
        preis = erfahrung.kosten_willenskraft(aktuell)
        if preis > verfuegbar:
            raise HTTPException(status.HTTP_409_CONFLICT, f"{preis} EP nötig, {verfuegbar} vorhanden.")
        await update_node(
            "Person",
            PERSON_FIELDS,
            campaign_id,
            person_id,
            {
                "willenskraftBonus": int(person.get("willenskraftBonus") or 0) + 1,
                "erfahrungAusgegeben": ausgegeben + preis,
            },
        )
    else:
        if not body.traitDefId:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein Wert angegeben")
        campaign = await get_campaign(campaign_id)
        katalog = await repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
        eintrag = next((t for t in katalog if t["id"] == body.traitDefId), None)
        if eintrag is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Wert nicht gefunden")

        erlaubt = sichtbare_kategorien(person.get("weg") or "KEINER", {t["category"] for t in katalog})
        if eintrag["category"] not in erlaubt:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Dieser Wert steht dem Charakter nicht offen.")

        aktuell = nach_name.get(eintrag["name"], 0)
        grenze = next((w["max"] for w in werte if w["traitDefId"] == body.traitDefId), eintrag["defaultMax"])
        if aktuell >= grenze:
            raise HTTPException(status.HTTP_409_CONFLICT, f"{eintrag['name']} steht bereits auf {grenze}.")

        preis = erfahrung.kosten(eintrag["category"], aktuell)
        if preis is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dieser Wert lässt sich nicht steigern.")
        if preis > verfuegbar:
            raise HTTPException(status.HTTP_409_CONFLICT, f"{preis} EP nötig, {verfuegbar} vorhanden.")

        await repository.steigere(campaign_id, person_id, body.traitDefId, aktuell + 1)
        await update_node(
            "Person",
            PERSON_FIELDS,
            campaign_id,
            person_id,
            {"erfahrungAusgegeben": ausgegeben + preis},
        )

    return await get_steigerungspreise(campaign_id, person_id, viewer)


class ErfahrungInput(BaseModel):
    punkte: int = Field(ge=0)


@router.post("/personen/{person_id}/erfahrung", dependencies=[Depends(require_campaign_gm)])
async def vergib_erfahrung(campaign_id: str, person_id: str, body: ErfahrungInput) -> dict:
    """Erfahrung vergeben. Ausschliesslich Sache der Spielleitung."""
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    aktualisiert = await update_node(
        "Person",
        PERSON_FIELDS,
        campaign_id,
        person_id,
        {"erfahrung": int(person.get("erfahrung") or 0) + body.punkte},
    )
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    return bogen_uebersicht(aktualisiert or person, {w["name"]: w["rating"] for w in werte}, cyberwall)
