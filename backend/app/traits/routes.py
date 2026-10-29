from typing import Literal
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_campaign, get_einstellungen
from app.entities.repository import PERSON_FIELDS, drohne_rigger, get_node, update_node
from app.ereignisprotokoll import hooks
from app.kampf import repository as kampf_repository
from app.kampf.hot import hot_anpassung, verbindung_bricht, werte_mit_hot
from app.items.repository import (
    ausruestungs_trait_boni,
    ausruestungsfertigkeiten_liste,
    commlink_cyberwall,
    deck_boni,
    initiative_modifikator,
    natuerliche_ruestungsteile,
    riggerkonsole_bonus,
    ruestungsteile,
    set_ablage,
    update_gegenstand,
    willenskraft_verlust,
)
from app.items import repository as items_repository
from app.kampf.ruestung import (
    anwende_natuerliche_ruestung,
    berechne_treffer,
    pool,
    uebersicht as ruestungs_uebersicht,
    verteile_kaestchenschaden,
)
from app.ki.client import KiFehler, generiere_json
from app.haendler import repository as haendler_repository
from app.hintergruende import repository as hintergruende_repository
from app.hintergruende.spawn import (
    kontakte_nach_erstellung,
    mentor_nach_erstellung,
    nach_erstellung as kredithai_nach_erstellung,
)
from app.rassen import repository as rassen_repository
from app.spezialisierungen import repository as spezialisierungen_repository
from app.traits import berater, catchup, erfahrung, erstellung, rast, repository
from app.traits.bogen import (
    bogen_uebersicht,
    sichtbare_kategorien,
    willenskraft_max,
    zustand_verboten,
)
from app.traits.schemas import (
    TraitDefResponse,
    TraitRatingResponse,
    TraitRatingUpdate,
    TraitVorschlaegeUpdate,
)
from app.zusatzfertigkeiten import repository as zusatzfertigkeiten_repository

router = APIRouter(prefix="/api/campaigns/{campaign_id}", tags=["traits"], dependencies=[Depends(require_campaign_zugang)])


async def _darf_person_sehen(campaign_id: str, person_id: str, person: dict, viewer: Viewer) -> bool:
    """Darf dieser Blickwinkel den Bogen/Zustand DIESER Person lesen/ändern?

    Bugfix 26.10.2026 (Mark): Spieler durften bisher ausschliesslich ihren
    EIGENEN Charakter sehen (`person_id == viewer.person_id`) — eine Drohne
    oder ein Fahrzeug ist aber ein EIGENER Person-Knoten, nie identisch mit
    dem des Riggers. Der Rigger bekam beim Öffnen des Drohnen-Charakterblatts
    serverseitig immer 404, was das Frontend (`shell/nachladen.ts::useNachladen`,
    schluckt Fehler lautlos fürs nächste Poll-Intervall) als endlos
    drehendes "Lade Charakterblatt…" zeigte, ohne je eine Fehlermeldung.
    Jetzt zusätzlich erlaubt: der an diese Drohne/dieses Fahrzeug gebundene
    Rigger (`entities/repository.py::drohne_rigger`, BEGLEITET-Kante) —
    bewusst NICHT generisch für jede BEGLEITET-Kante (Critter/Sprite/KI
    nutzen dieselbe Kante mit anderer Besitz-Semantik und blieben unberührt),
    sondern nur wenn die Zielperson tatsächlich `istDrohne`/`istFahrzeug` ist.
    """
    if viewer.role == "GM" or person_id == viewer.person_id:
        return True
    if person.get("istDrohne") or person.get("istFahrzeug"):
        return await drohne_rigger(campaign_id, person_id) == viewer.person_id
    return False


@router.get("/traitkatalog", response_model=list[TraitDefResponse])
async def get_catalog(campaign_id: str):
    campaign = await get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne nicht gefunden")
    return await repository.list_catalog(campaign["ruleset"])


@router.put(
    "/traits/{trait_def_id}/vorschlaege",
    response_model=TraitDefResponse,
    dependencies=[Depends(require_campaign_gm)],
)
async def set_trait_vorschlaege(campaign_id: str, trait_def_id: str, body: TraitVorschlaegeUpdate):
    """Spezialisierungs-Vorschlagstexte einer Fertigkeit setzen (GM-Oberfläche,
    Folge-Feature 22.10.2026 zur Fertigkeiten-Spezialisierung).

    Bisher kam `vorschlaege` ausschliesslich aus TRAIT_VORSCHLAEGE in
    traits/seed.py — es gab keine Route, die es live ändert. Siehe
    ZusatzfertigkeitenVerwaltung.tsx, Tab "Spezialisierungs-Vorschläge"
    (bewusst in diesem Tab untergebracht, nicht in einem neuen Menüpunkt —
    Mark meinte damit das bestehende "Zusatzfertigkeiten"-Menü).

    Nur Fertigkeiten/NeuroWeaving/Sphären (dieselbe Kategorie-Liste wie bei
    der automatischen Spezialisierungs-Vergabe, siehe
    spezialisierungen/repository.py::ALLE_SPEZIALISIERUNGS_KATEGORIEN) —
    Attribute kennen keine Spezialisierungs-Slots und damit auch keine
    Vorschlagstexte dafür. Sphären kamen am 23.10.2026 dazu.

    **v1-Vereinfachung, bewusst (siehe Feature-Bericht):** TraitDef ist
    ruleset-weit, nicht campaign-gebunden wie Zusatzfertigkeiten — diese
    Route ändert den gemeinsamen Katalogeintrag für ALLE Kampagnen dieses
    Regelwerks, nicht nur die aufrufende. In der Praxis gibt es aktuell nur
    ein Regelwerk ('neotopia'); eine per-Kampagne-Override-Variante ist kein
    v1-Umfang.
    """
    campaign = await get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kampagne nicht gefunden")
    ruleset = campaign["ruleset"]
    katalog = await repository.list_catalog(ruleset)
    eintrag = next((t for t in katalog if t["id"] == trait_def_id), None)
    if eintrag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fertigkeit nicht gefunden")
    if eintrag["category"] not in spezialisierungen_repository.ALLE_SPEZIALISIERUNGS_KATEGORIEN:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Spezialisierungs-Vorschläge gibt es nur für Fertigkeiten/NeuroWeaving/Sphären, "
            "nicht für Attribute.",
        )
    saubere_liste = [v.strip() for v in body.vorschlaege if v.strip()]
    aktualisiert = await repository.set_vorschlaege(trait_def_id, ruleset, saubere_liste)
    if aktualisiert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fertigkeit nicht gefunden")
    return aktualisiert


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
    Magier ist, bekommt Sphaeren und Hexkraft gar nicht erst zu sehen.
    """
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    if not await _darf_person_sehen(campaign_id, person_id, person, viewer):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    campaign = await get_campaign(campaign_id)
    einstellungen = await get_einstellungen(campaign_id)
    kampagnen_ep = einstellungen.get("kampagnenEP", 0)
    katalog = await repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)

    nach_name = {w["name"]: w["rating"] for w in werte}
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    chrom = await willenskraft_verlust(campaign_id, person_id)
    init_mod = await initiative_modifikator(campaign_id, person_id)
    ist_drohne = bool(person.get("istDrohne")) or bool(person.get("istFahrzeug"))
    erlaubt = sichtbare_kategorien(
        person.get("weg") or "KEINER",
        {t["category"] for t in katalog},
        bool(person.get("istKI")),
        ist_drohne,
    )
    # Natürliche Rüstung (11.10.2026): Kästchen-Max kommt live aus der
    # Widerstandsfähigkeit-Rating, nicht aus dem gespeicherten Item-Wert
    # (siehe kampf/ruestung.py::anwende_natuerliche_ruestung). Drohnen/
    # Fahrzeuge (26.10.2026, Mark): zusätzlich die Reduktion live aus der
    # Außenhülle-Rating — siehe `anwende_natuerliche_ruestung`-Docstring.
    ruestungsteile_live = anwende_natuerliche_ruestung(
        await ruestungsteile(campaign_id, person_id),
        nach_name.get("Widerstandsfähigkeit", 0),
        aussenhuelle=nach_name.get("Außenhülle", 0) if ist_drohne else None,
    )

    katalog_sichtbar = [t for t in katalog if t["category"] in erlaubt]
    rigger_id = await kampf_repository.hot_rigger_id(campaign_id, person_id) if ist_drohne else None
    if rigger_id:
        rigger_ratings = await repository.get_ratings_for_entity(campaign_id, rigger_id)
        rigger_nach = {w["name"]: int(w["rating"] or 0) for w in rigger_ratings}
        drohne_zf = await zusatzfertigkeiten_repository.zusatzfertigkeiten_der_person(campaign_id, person_id)
        rigger_zf = await zusatzfertigkeiten_repository.zusatzfertigkeiten_der_person(campaign_id, rigger_id)
        anpassung = hot_anpassung(
            nach_name,
            rigger_nach,
            await riggerkonsole_bonus(campaign_id, rigger_id),
            {z["name"]: int(z.get("rating") or 0) for z in drohne_zf},
            {z["name"]: int(z.get("rating") or 0) for z in rigger_zf},
        )
        werte, extra = werte_mit_hot(werte, katalog, anpassung)
        schon = {t["id"] for t in katalog_sichtbar}
        katalog_sichtbar += [t for t in extra if t["id"] not in schon]
        hot_zusatz = (
            [{"name": "Fliegen", "rating": anpassung["Fliegen"]}]
            if "Fliegen" in anpassung
            else []
        )
    else:
        hot_zusatz = []

    return {
        "person": {
            "id": person["id"],
            "name": person["name"],
            "personType": person["personType"],
            "istKI": bool(person.get("istKI")),
            "istDrohne": bool(person.get("istDrohne")),
            "istFahrzeug": bool(person.get("istFahrzeug")),
        },
        "uebersicht": bogen_uebersicht(person, nach_name, cyberwall, chrom, init_mod, kampagnen_ep),
        "deckBoni": await deck_boni(campaign_id, person_id),
        "ausruestungsBoni": await ausruestungs_trait_boni(campaign_id, person_id),
        "ausruestungsfertigkeiten": await ausruestungsfertigkeiten_liste(campaign_id, person_id),
        "ruestung": ruestungs_uebersicht(ruestungsteile_live),
        "katalog": katalog_sichtbar,
        "werte": werte,
        "hotZusatz": hot_zusatz,
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

    **Willenskraft ist eine Einbahnstraße für Spieler**: ausgeben ja,
    zurückholen nein. Sie kehrt zurück, wenn die Spielleitung es sagt.
    """
    aenderung = body.model_dump()

    # Die Regel selbst steht in bogen.py und ist dort geprüft.
    if viewer.role != "GM":
        vorher = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
        if vorher is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
        if not await _darf_person_sehen(campaign_id, person_id, vorher, viewer):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
        grund = zustand_verboten(viewer.role, vorher, aenderung)
        if grund:
            raise HTTPException(status.HTTP_403_FORBIDDEN, grund)

    person = await update_node("Person", PERSON_FIELDS, campaign_id, person_id, aenderung)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    einstellungen = await get_einstellungen(campaign_id)
    kampagnen_ep = einstellungen.get("kampagnenEP", 0)
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    chrom = await willenskraft_verlust(campaign_id, person_id)
    init_mod = await initiative_modifikator(campaign_id, person_id)
    return bogen_uebersicht(person, {w["name"]: w["rating"] for w in werte}, cyberwall, chrom, init_mod, kampagnen_ep)


class SteckbriefUpdate(BaseModel):
    """Der nachträglich änderbare Teil der Kopfzeile des Papierblatts.

    Konzept steht bei der Erstellung fest genug, dass Mark es dort beliess —
    Ambition, Verlangen und Ziel entwickeln sich dagegen im Spiel weiter
    (CLAUDE.md, Punkt 12). Alter bleibt im fertigen Blatt bewusst aussen vor
    (kein UI) — der Assistent schreibt es hier trotzdem als Entwurf, sonst
    ist ein Gerätewechsel vor "Charakter anlegen" ein leeres Formular.

    Alias (06.10.2026, Mark: "könnte sich ja auch ändern") gehört aus
    demselben Grund hierher statt nur in die Erstellung: es ist der Name,
    den ein PC in den Kontakten für diese Person sieht, bis der echte Name
    freigegeben ist (app/kontakte/logic.py::effektiver_alias) — vorher gab
    es dafür keine editierbare Stelle.

    Name (09.10.2026): derselbe Entwurfsweg. Die Erstellung hält den Namen
    sonst nur im React-State; ohne PATCH landet "Quill" nie auf dem Knoten.
    """

    konzept: str | None = None
    ambition: str | None = None
    verlangen: str | None = None
    ziel: str | None = None
    alias: str | None = None
    name: str | None = None
    alter: str | None = None
    # Während der Erstellung, sonst kennt der Tutorial-Shop die Rasse nicht
    # (die steht bis zum finalen Submit nur im Browser). Nach dem Anlegen
    # ignoriert die Route das Feld — Rasse ändert man nicht über den Steckbrief.
    rasse: str | None = None
    # Charakterbeschreibung (24.10.2026, Mark: Spieler soll lesen+editieren
    # können, was die SL reingeschrieben hat). Dasselbe Feld wie
    # entities/Person.description — hier kriegt auch der Spieler für den
    # eigenen Charakter Schreibzugriff darauf (derselbe Owner-oder-GM-Check
    # wie beim Rest dieser Route, kein eigener Endpunkt nötig).
    description: str | None = None


@router.patch("/personen/{person_id}/steckbrief")
async def set_steckbrief(
    campaign_id: str,
    person_id: str,
    body: SteckbriefUpdate,
    viewer: Viewer = Depends(get_viewer),
) -> dict:
    """Konzept, Ambition, Verlangen, Ziel, Alias, Beschreibung — und als Entwurf Name/Alter.

    Dieselbe Erlaubnis wie bei `zustand`: Spieler nur am eigenen Charakter
    (404 bei fremden Personen), die Spielleitung überall. Anders als bei
    Zustand keine Einbahnstraße — ein leerer String löscht ein Feld bewusst,
    `update_node` filtert nur `None` heraus, nicht die leere Zeichenkette.
    Die Charaktererstellung nutzt denselben PATCH als Autosave, damit der
    Person-Schritt einen Gerätewechsel überlebt.
    """
    person_vorher = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person_vorher is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    if not await _darf_person_sehen(campaign_id, person_id, person_vorher, viewer):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    daten = body.model_dump()
    if daten.get("rasse") is not None and person_vorher.get("erstellungAbgeschlossen"):
        daten["rasse"] = None

    person = await update_node("Person", PERSON_FIELDS, campaign_id, person_id, daten)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    einstellungen = await get_einstellungen(campaign_id)
    kampagnen_ep = einstellungen.get("kampagnenEP", 0)
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    chrom = await willenskraft_verlust(campaign_id, person_id)
    init_mod = await initiative_modifikator(campaign_id, person_id)
    return bogen_uebersicht(person, {w["name"]: w["rating"] for w in werte}, cyberwall, chrom, init_mod, kampagnen_ep)


class TutorialKapitalInput(BaseModel):
    """Freebee-Kredit/Eigenkapital-Regler im laufenden Freebees-Schritt
    (10.10.2026, Tutorial-Shop): neu berechnetes Guthaben, bevor die
    Erstellung final eingereicht wird."""

    freebeeKredit: int = Field(default=0, ge=0)
    freebeeEigenkapital: int = Field(default=0, ge=0)


@router.put("/personen/{person_id}/erstellung/tutorial-kapital")
async def tutorial_kapital_setzen(
    campaign_id: str,
    person_id: str,
    body: TutorialKapitalInput,
    viewer: Viewer = Depends(get_viewer),
) -> dict:
    """Rechnet `kapitalBasis`/`kapital` neu, wenn der Kredit-/Eigenkapital-
    Regler im Freebees-Schritt bewegt wird, NACHDEM im Tutorial-Shop schon
    etwas gekauft wurde (siehe `Person.tutorialAusgegeben`). Ohne diese
    Route würde ein bereits ausgegebener Betrag beim Reglerverstellen
    kommentarlos wieder auftauchen, weil `erstelle_charakter` die Formel
    sonst erst beim finalen Submit anwendet."""
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    if person.get("erstellungAbgeschlossen"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Dieser Charakter ist bereits erstellt.")

    vermoegen, _schulden = erstellung.kapital(
        {"freebeeKredit": body.freebeeKredit, "freebeeEigenkapital": body.freebeeEigenkapital}
    )
    geschrieben = await haendler_repository.tutorial_kapital_schreiben(campaign_id, person_id, vermoegen)
    if geschrieben is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    return {
        "kapital": geschrieben["kapital"],
        "ausgegeben": geschrieben["ausgegeben"],
        "gedeckt": geschrieben["gedeckt"],
    }


# =====================================================================
# Rüstungstreffer (Formel: kampf/ruestung.py, Begründung: docs/api/ruestung.md)
# =====================================================================

# Dieselben drei Begriffe wie überall sonst im Tool (schadenSchlag/Schwer/
# Aggraviert, Kaestchen.tsx::Schadensart) — am Tisch heissen sie
# Schlag/Tödlich/Schwerheilbar, die Übersetzung passiert nur in der Oberfläche.
RuestungsArt = Literal["schlag", "schwer", "aggraviert"]

_SCHADEN_FELD = {"schlag": "schadenSchlag", "schwer": "schadenSchwer", "aggraviert": "schadenAggraviert"}


class RuestungTrefferInput(BaseModel):
    """Ein Treffer, wie er am Tisch angesagt wird: Art und Stärke.

    Mehr braucht es nicht — die Rüstung wirkt als **ein Pool** (Marks
    Vorgabe, ausdrücklich ohne Körperzonen), es gibt also nichts zu zielen.
    Welche Teile der Kästchenschaden aufbraucht, entscheidet die Regel
    (`ruestung.reihenfolge`: das dichteste zuerst).
    """

    art: RuestungsArt
    staerke: int = Field(ge=0)
    # Ereignisprotokoll (27.09.2026): Angreifer wird normalerweise automatisch
    # aus Kampf.amZug abgeleitet (Marks Vorgabe: "wenn mein Spieler dran ist,
    # und ein NPC leben verliert, hat der Spieler diesen NPC verletzt").
    # Override nur für Ausnahmefälle: Treffer außerhalb der Zugreihenfolge,
    # Umwelt-/Fallenschaden ohne Angreifer, nachträgliche SL-Korrektur.
    angreiferPersonId: str | None = None


class RuestungsteilFolge(BaseModel):
    """Was ein einzelnes Rüstungsteil von diesem Treffer abbekommen hat."""

    id: str
    name: str
    verlust: int
    kaestchenNeu: int
    # Bei 0 Kästchen wirkt es nicht mehr und gilt nicht mehr als
    # ausgerüstet — es liegt danach im Mitgeführten.
    zerstoert: bool


class RuestungTrefferErgebnis(BaseModel):
    # Was nach Abstufung/Halbierung tatsächlich angekommen ist — die
    # Oberfläche soll zeigen können, was sie gerade bewirkt hat, ohne die
    # Formel nachzubauen.
    hpArt: RuestungsArt
    hpMenge: int
    # Wie viele Kästchen der Pool insgesamt verloren hat, und welche Teile
    # es getroffen hat (leer = keine wirksame Rüstung, der Schaden kam
    # ungebremst an).
    kaestchenSchaden: int = 0
    betroffen: list[RuestungsteilFolge] = []
    uebersicht: dict
    # Hot-Rückschlag: halber angekommener Schaden als Schlag beim Rigger.
    hotRueckschlag: list[dict] = []
    dumpshock: list[dict] = []


@router.post("/personen/{person_id}/ruestung/treffer", response_model=RuestungTrefferErgebnis)
async def ruestungstreffer(
    campaign_id: str,
    person_id: str,
    body: RuestungTrefferInput,
    viewer: Viewer = Depends(get_viewer),
) -> RuestungTrefferErgebnis:
    """"3× Tödlich" eintragen — Rüstung und Gesundheit rechnen automatisch mit.

    Der Ablauf aus Marks Konzept: angesagt wird nur, **was** getroffen hat.
    Alles Getragene wirkt dabei als **ein Pool** (`ruestung.pool`: Kästchen
    summiert, Durchlass vom dichtesten Teil) — es gibt keine Körperzonen und
    nichts zu zielen. Diese Route rechnet daraus, was an Kästchen draufgeht,
    verteilt das auf die Teile (dichtestes zuerst, `verteile_kaestchenschaden`),
    schreibt deren Durchlass fort und legt zerstörte Teile ins Mitgeführte
    zurück — und bucht den abgestuften Rest auf die Gesundheit.

    **Ohne wirksame Rüstung** (nichts angelegt, oder alles auf 0 Kästchen)
    trifft der Schaden ungebremst und unverändert in seiner Art. Das ist
    kein Fehlerfall: so lässt sich das Popup auch für ungerüstete Charaktere
    benutzen.

    Fünfte Route, die auch Spieler schreiben dürfen — wie `zustand` nur am
    eigenen Charakter (404 bei fremden, damit deren Existenz nicht bestätigt
    wird), und nur Schaden nach oben: die Menge wird **addiert**, nichts
    überschrieben.
    """
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    if not await _darf_person_sehen(campaign_id, person_id, person, viewer):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    # Werte früh holen (statt erst am Ende wie sonst üblich): natürliche
    # Rüstung (11.10.2026) braucht die Widerstandsfähigkeit-Rating schon für
    # den Pool, nicht erst für die abschliessende Bogen-Übersicht. Eine
    # zweite Abfrage am Ende entfällt dadurch — die Werte der Person ändern
    # sich innerhalb dieser Route nicht.
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    nach_name = {w["name"]: w["rating"] for w in werte}
    ist_drohne = bool(person.get("istDrohne")) or bool(person.get("istFahrzeug"))
    ruestungsteile_live = anwende_natuerliche_ruestung(
        await ruestungsteile(campaign_id, person_id),
        nach_name.get("Widerstandsfähigkeit", 0),
        aussenhuelle=nach_name.get("Außenhülle", 0) if ist_drohne else None,
    )
    gesamt = pool(ruestungsteile_live)
    if gesamt is None:
        # Keine wirksame Rüstung: voller Schaden, unveränderte Art.
        ergebnis = {"hpArt": body.art, "hpMenge": body.staerke, "kaestchenSchaden": 0}
        folgen: list[dict] = []
    else:
        # Vom Ergebnis gilt hier nur hpArt/hpMenge/kaestchenSchaden — die
        # Kästchenwerte darin beziehen sich auf den Pool als Ganzes, die
        # echten Teile bekommen ihre Werte aus der Verteilung.
        ergebnis = berechne_treffer(
            body.art,
            body.staerke,
            gesamt["kaestchenAktuell"],
            gesamt["kaestchenMax"],
            gesamt["reduktionBasis"],
        )
        folgen = verteile_kaestchenschaden(gesamt["geordnet"], ergebnis["kaestchenSchaden"])
        for folge in folgen:
            await update_gegenstand(
                campaign_id,
                folge["id"],
                {"ruestungKaestchenAktuell": folge["kaestchenNeu"]},
            )
            if folge["zerstoert"]:
                # Zerschossene Rüstung gilt nicht mehr als ausgerüstet
                # (Marks Vorgabe). Ins Mitgeführte statt in den Mülleimer:
                # sie bleibt reparierbar — dasselbe Muster wie bei
                # chirurgisch entferntem Chrom.
                await set_ablage(campaign_id, folge["id"], "RUCKSACK", None)

    if ergebnis["hpMenge"] > 0:
        feld = _SCHADEN_FELD[ergebnis["hpArt"]]
        person = await update_node(
            "Person",
            PERSON_FIELDS,
            campaign_id,
            person_id,
            {feld: int(person.get(feld) or 0) + ergebnis["hpMenge"]},
        )

    rueckschlag: list[dict] = []
    if ist_drohne and ergebnis["hpMenge"] > 0:
        rueckschlag = await kampf_repository.hot_rueckschlag_buchen(
            campaign_id, person_id, ergebnis["hpMenge"]
        )

    # Ereignisprotokoll: KampfLogEintrag mit automatischer Angreifer-
    # Zuordnung aus Kampf.amZug (Marks Vorgabe, docs/wiki/entities/
    # ereignisprotokoll.md) — Override per Body hat Vorrang, sonst wird
    # nachgeschaut, wer laut laufendem Kampf gerade dran ist. Außerhalb
    # eines Kampfs (kein Zug bekannt) bleibt Angreifer leer.
    angreifer_id = body.angreiferPersonId or await kampf_repository.angreifer_person_id(campaign_id)
    laufender_kampf = await kampf_repository.hole(campaign_id)
    await hooks.kampf_treffer(
        campaign_id,
        art="KRITISCH" if ergebnis["hpArt"] == "aggraviert" else "TREFFER",
        ziel_person_id=person_id,
        angreifer_person_id=angreifer_id,
        kampf_id=(laufender_kampf or {}).get("id", ""),
        runde=(laufender_kampf or {}).get("runde", 0),
        hp_art=ergebnis["hpArt"],
        hp_menge=ergebnis["hpMenge"],
        kaestchen_schaden=ergebnis["kaestchenSchaden"],
    )
    for r in rueckschlag:
        await hooks.kampf_treffer(
            campaign_id,
            art="TREFFER",
            ziel_person_id=r["riggerId"],
            angreifer_person_id=angreifer_id,
            kampf_id=(laufender_kampf or {}).get("id", ""),
            runde=(laufender_kampf or {}).get("runde", 0),
            hp_art="schlag",
            hp_menge=r["schlag"],
            kaestchen_schaden=0,
        )

    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    einstellungen = await get_einstellungen(campaign_id)
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    chrom = await willenskraft_verlust(campaign_id, person_id)
    init_mod = await initiative_modifikator(campaign_id, person_id)
    uebersicht = bogen_uebersicht(
        person,
        nach_name,
        cyberwall,
        chrom,
        init_mod,
        einstellungen.get("kampagnenEP", 0),
    )
    dumpshock: list[dict] = []
    if (
        ist_drohne
        and rueckschlag
        and person is not None
        and verbindung_bricht(uebersicht["gesundheitMax"] - uebersicht["gesundheitSchaden"])
    ):
        for r in rueckschlag:
            await kampf_repository.dumpshock(campaign_id, r["riggerId"])
            dumpshock.append({"riggerId": r["riggerId"], "riggerName": r["riggerName"]})
    return RuestungTrefferErgebnis(
        hpArt=ergebnis["hpArt"],
        hpMenge=ergebnis["hpMenge"],
        kaestchenSchaden=ergebnis["kaestchenSchaden"],
        betroffen=[RuestungsteilFolge(**f) for f in folgen],
        hotRueckschlag=rueckschlag,
        dumpshock=dumpshock,
        uebersicht=uebersicht,
    )


# =====================================================================
# Rast-Mechanik (Formel: app/traits/rast.py, Begründung: docs/api/rast.md)
# =====================================================================


class RastInput(BaseModel):
    """Eine oder mehrere Personen, auf die die Aktion angewendet wird."""

    personIds: list[str] = Field(default_factory=list)


async def _bogen_fuer_person(campaign_id: str, person: dict, kampagnen_ep: int) -> dict:
    """Dieselbe Bogen-Übersicht-Zusammenstellung wie bei `zustand`/`steckbrief`
    — hier als kleiner Helfer, weil Rasten/Vollheilung sie pro ausgewählter
    Person wiederholt brauchen (anders als die übrigen Routen, die nur EINE
    Person je Aufruf behandeln)."""
    person_id = person["id"]
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    chrom = await willenskraft_verlust(campaign_id, person_id)
    init_mod = await initiative_modifikator(campaign_id, person_id)
    return bogen_uebersicht(
        person, {w["name"]: w["rating"] for w in werte}, cyberwall, chrom, init_mod, kampagnen_ep
    )


@router.post("/personen/rasten", dependencies=[Depends(require_campaign_gm)])
async def personen_rasten(campaign_id: str, body: RastInput) -> dict:
    """SL-Aktion "Rasten": EIN Klick = EINE Rast pro ausgewählter Person.

    Formel (Mark, 11.10.2026, siehe docs/api/rast.md und app/traits/rast.py):
    Schlagschaden heilt immer vollständig, schwerer Schaden sinkt um 1 (mit
    einem Zähler fürs Schwerheilbar-Wraparound bei 7), und ist die Person danach
    komplett gesund, heilt jedes getragene `istNatuerlich`-Rüstungsteil mit
    Defizit +1 Kästchen — auch schon in dieser Rast. Unberührte Personen-IDs
    (falsch/gelöscht) werden übersprungen, nicht als Fehler gemeldet, damit
    eine Mehrfachauswahl nicht an einem einzelnen ungültigen Eintrag scheitert.

    Bug-Fix 12.10.2026 (Mark): natürliche Rüstung heilt auch dann über Rast,
    wenn sie wegen vorheriger Zerstörung gerade im Mitgeführten liegt
    (`natuerliche_ruestungsteile` holt sie unabhängig von der Ablage, siehe
    dort) — und wird, sobald sie dadurch wieder über 0 Kästchen steht,
    automatisch erneut ausgerüstet. Sie ist Körperteil, kein Kleidungsstück,
    das man vergisst anzulegen. Gilt bewusst NUR für `istNatuerlich`; normale
    Rüstung bleibt im Mitgeführten liegen und braucht weiter den regulären
    Reparaturweg.
    """
    einstellungen = await get_einstellungen(campaign_id)
    kampagnen_ep = einstellungen.get("kampagnenEP", 0)
    ergebnisse: dict[str, dict] = {}
    for person_id in body.personIds:
        person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
        if person is None:
            continue
        aenderung = rast.person_aenderung(person)
        person = await update_node("Person", PERSON_FIELDS, campaign_id, person_id, aenderung)
        if person is None:
            continue

        if rast.ist_vollstaendig_gesund(aenderung):
            werte = await repository.get_ratings_for_entity(campaign_id, person_id)
            nach_name = {w["name"]: w["rating"] for w in werte}
            teile = anwende_natuerliche_ruestung(
                await natuerliche_ruestungsteile(campaign_id, person_id), nach_name.get("Widerstandsfähigkeit", 0)
            )
            for folge in rast.ruestung_heilung(teile):
                await update_gegenstand(
                    campaign_id, folge["id"], {"ruestungKaestchenAktuell": folge["ruestungKaestchenAktuell"]}
                )
                quelle = next(t for t in teile if t["id"] == folge["id"])
                if quelle.get("ablage") != "AUSGERUESTET" and folge["ruestungKaestchenAktuell"] > 0:
                    # War durch Zerstörung ins Mitgeführte gelegt und ist
                    # jetzt wieder intakt: automatisch erneut ausrüsten.
                    await set_ablage(campaign_id, folge["id"], "AUSGERUESTET", None)

        ergebnisse[person_id] = await _bogen_fuer_person(campaign_id, person, kampagnen_ep)
    return ergebnisse


@router.post("/personen/vollstaendige-heilung", dependencies=[Depends(require_campaign_gm)])
async def personen_vollstaendige_heilung(campaign_id: str, body: RastInput) -> dict:
    """Fallback-Knopf "für den Fall der Fälle": keine Bedingungen, kein
    Würfeln. Setzt Schaden + Heil-Zähler auf 0 und heilt JEDES getragene
    Rüstungsteil (auch nicht-natürliches) sofort auf den vollen Max.

    Natürliche Rüstung (12.10.2026, derselbe Fix wie bei `personen_rasten`)
    auch dann, wenn sie wegen Zerstörung gerade im Mitgeführten liegt —
    danach automatisch wieder ausgerüstet. Normale Rüstung bleibt dagegen
    bewusst nur erfasst, solange sie ausgerüstet ist.
    """
    einstellungen = await get_einstellungen(campaign_id)
    kampagnen_ep = einstellungen.get("kampagnenEP", 0)
    ergebnisse: dict[str, dict] = {}
    for person_id in body.personIds:
        person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
        if person is None:
            continue
        person = await update_node(
            "Person", PERSON_FIELDS, campaign_id, person_id, rast.vollheilung_person()
        )
        if person is None:
            continue

        werte = await repository.get_ratings_for_entity(campaign_id, person_id)
        nach_name = {w["name"]: w["rating"] for w in werte}
        nicht_natuerlich = [t for t in await ruestungsteile(campaign_id, person_id) if not t.get("istNatuerlich")]
        natuerlich = await natuerliche_ruestungsteile(campaign_id, person_id)
        teile = anwende_natuerliche_ruestung(
            nicht_natuerlich + natuerlich, nach_name.get("Widerstandsfähigkeit", 0)
        )
        for folge in rast.vollheilung_ruestung(teile):
            await update_gegenstand(
                campaign_id, folge["id"], {"ruestungKaestchenAktuell": folge["ruestungKaestchenAktuell"]}
            )
            quelle = next(t for t in teile if t["id"] == folge["id"])
            if (
                quelle.get("istNatuerlich")
                and quelle.get("ablage") != "AUSGERUESTET"
                and folge["ruestungKaestchenAktuell"] > 0
            ):
                await set_ablage(campaign_id, folge["id"], "AUSGERUESTET", None)

        ergebnisse[person_id] = await _bogen_fuer_person(campaign_id, person, kampagnen_ep)
    return ergebnisse


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
    # Zusatzfertigkeiten: Paketpunkte aus dem Fertigkeiten-Schritt
    # (Schlüssel = Katalog-ID, 0 = gewählt ohne Slot). Zählen in dieselbe
    # Paketverteilung wie normale Fertigkeiten.
    zusatzfertigkeitPunkte: dict[str, int] = Field(default_factory=dict)
    # Freebee-Aufschlag darauf (0 oder 1), aus dem gemeinsamen Hauptpool.
    zusatzfertigkeitFreebees: dict[str, int] = Field(default_factory=dict)
    freebeeWillenskraft: int = Field(default=0, ge=0)
    freebeeKredit: int = Field(default=0, ge=0)
    freebeeEigenkapital: int = Field(default=0, ge=0)
    konzept: str = ""
    alter: str = ""
    ambition: str = ""
    verlangen: str = ""
    ziel: str = ""
    # Der Charaktername selbst — bisher legte die Spielleitung ihn beim
    # Anlegen fest und der Spieler sah ihn nur read-only in der Erstellung.
    # Mark: "das sollte nicht zwingend der SL für ihn machen". Leer bleibt
    # unzulässig (Prüfung unten), ein Platzhalter wie "Neuer PC" darf aber
    # ruhig ohne Änderung durchgehen, solange der Spieler ihn ersetzt hat.
    name: str = ""


async def _rassen_der_kampagne(campaign_id: str) -> dict[str, dict]:
    """Die in dieser Kampagne freigegebenen Rassen, im Format des Regelwerks.

    Der Katalog liegt in der Datenbank und wird im Baukasten gepflegt (siehe
    app/rassen/); die Erstellung kennt nur noch die **freigegebenen**. Marks
    Vorgabe: *"es sollten nicht automatisch alle zur Verfügung stehen,
    sondern nur ausgewählte."*
    """
    return {
        r["name"]: {
            "modifikatoren": r["modifikatoren"],
            "freiePunkte": r["freiePunkte"],
            "beschreibung": r["beschreibung"],
            "bildUrl": r["bildUrl"],
            # Rassen-Features (10.10.2026, budget-neutral): waren hier bis
            # jetzt versehentlich NICHT dabei — bonusFreebees/gratis* kamen
            # dadurch in pruefe()/endwerte() immer als 0/leer an, obwohl der
            # Baukasten sie schon speicherte. Echter Bug, nicht nur fehlendes
            # Feature (siehe CLAUDE.md Stolperstein 5: 6-Schichten-Check).
            "bonusFreebees": r["bonusFreebees"],
            "gratisGegenstandId": r["gratisGegenstandId"],
            "gratisErsterKaufTyp": r["gratisErsterKaufTyp"],
            "gratisZusatzfertigkeitId": r["gratisZusatzfertigkeitId"],
            "gratisFertigkeitName": r["gratisFertigkeitName"],
            "gratisFertigkeitBonus": r["gratisFertigkeitBonus"],
            "kannKredithai": r.get("kannKredithai") or False,
        }
        for r in await rassen_repository.liste_fuer_kampagne(campaign_id)
    }


async def _rassen_extras_benennen(campaign_id: str, rassen: list[dict]) -> None:
    """Löst Gratis-Gegenstand und Gratis-Zusatzfertigkeit zu Namen auf.

    Wenige Rassen, einzelne Lookups reichen. Eine gelöschte Vorlage bleibt
    leer — der Steckbrief zeigt dann nur, dass es ein Extra gibt.
    """
    gegenstand_namen: dict[str, str] = {}
    zusatz_namen: dict[str, str] = {}
    for eintrag in rassen:
        gid = eintrag.get("gratisGegenstandId") or ""
        if gid and gid not in gegenstand_namen:
            gegenstand = await items_repository.get_gegenstand(campaign_id, gid)
            gegenstand_namen[gid] = (gegenstand or {}).get("name") or ""
        zid = eintrag.get("gratisZusatzfertigkeitId") or ""
        if zid and zid not in zusatz_namen:
            zusatz = await zusatzfertigkeiten_repository.hole(campaign_id, zid)
            zusatz_namen[zid] = (zusatz or {}).get("name") or ""
    erstellung.rassen_extras_benennen(rassen, gegenstand_namen, zusatz_namen)


@router.get("/erstellung/regeln")
async def get_erstellungsregeln(campaign_id: str) -> dict:
    """Rassen, Pakete, Hintergründe, Freebee-Preise.

    Auch für Spieler lesbar — sie erstellen ihren Charakter selbst, und die
    Regeln sind nichts Geheimes. Die Rassen kommen aus der Freigabe dieser
    Kampagne, nicht mehr aus der fest verdrahteten Tabelle.
    """
    einstellungen = await get_einstellungen(campaign_id)
    hintergrund_pool = await hintergruende_repository.pool_fuer_erstellung(campaign_id, einstellungen)
    regeln = erstellung.regelwerk(await _rassen_der_kampagne(campaign_id), einstellungen, hintergrund_pool)
    await _rassen_extras_benennen(campaign_id, regeln["rassen"])
    return regeln


class ErstellungKommentarInput(BaseModel):
    """Zwischenstand der LAUFENDEN Erstellung — noch nicht eingereicht,
    kein DB-Zugriff nötig für die Zahlen selbst (siehe traits/berater.py)."""

    werte: dict[str, int] = Field(default_factory=dict)
    weg: str = "KEINER"
    magieFlavor: str = "MAGIER"


_KOMMENTAR_SYSTEM = (
    "Du bist eine schrullige, alles kommentierende KI in einem Cyberpunk-"
    "Pen-and-Paper-Rollenspiel (NeotopiA) — im Ton wie das Erzähler-System aus "
    "\"Dungeon Crawler Carl\": eine übertrieben dramatische Show-Stimme, die "
    "Zahlen und Builds mit großer Geste kommentiert, so als wäre es eine "
    "Live-Übertragung. Der Humor kommt aus Übertreibung, absurden Vergleichen "
    "und cleveren Pointen — NICHT aus Beleidigungen, Herabsetzung oder "
    "gespieltem 'Roasten'. Schreib NIE wie ein frecher Jugendlicher, der "
    "billig anmacht — das ist nicht witzig, sondern peinlich. Stattdessen: "
    "warmherzig-schräg, wie ein overenthusiastischer Kommentator bei einer "
    "Gameshow, der auch bei einer schwachen Leistung noch Charme und "
    "Wortwitz findet statt Häme.\n\n"
    "Format: du verleihst ein spöttisch-liebevolles Achievement, wie ein "
    "Videospiel es beim Abschluss eines Levels tut. Gib ZWEI Teile zurück:\n"
    "- 'achievement': ein kurzer, prägnanter Titel in Großbuchstaben (2-5 "
    "Wörter), der die Haltung des Spielers zu den Balance-Hinweisen einfängt "
    "— z.B. 'BEFEHLSEMPFÄNGER' für jemanden, der brav auf die Warnungen "
    "gehört hat, oder 'UNVERBESSERLICHER REBELL' für jemanden, der sie "
    "ignoriert hat. Sei kreativ, keine Wiederholung dieser Beispiele.\n"
    "- 'kommentar': 2-4 Sätze, die zuerst konkret auf die Zahlen eingehen "
    "(was besonders hoch/niedrig ist, was auffällt) und DANN explizit "
    "thematisieren, ob der Spieler die mitgelieferten Hinweise beherzigt "
    "oder bewusst in den Wind geschlagen hat — der Statuszeile im Prompt "
    "('Status: ...') folgend. Keine Allgemeinplätze. Kein Rollenspiel-"
    "Fließtext über die Spielwelt, kein Regel-Erklärbär, keine "
    "Kraftausdrücke oder vulgäre Sprache."
)

_KOMMENTAR_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "achievement": {"type": "STRING"},
        "kommentar": {"type": "STRING"},
    },
    "required": ["achievement", "kommentar"],
}


@router.post("/erstellung/kommentar")
async def erstellung_kommentar(campaign_id: str, body: ErstellungKommentarInput) -> dict:
    """KI-Abschlusskommentar zum fertigen Fertigkeiten-Build (27.09.2026).

    EIN Aufruf pro Klick, ausdrücklich über einen Knopf im Frontend
    (ErstellungsKommentar.tsx) — nie automatisch, Mark ist kostenbewusst
    beim LLM-Verbrauch. Anders als /erstellung/berater (rein regelbasiert,
    kostenlos) generiert dieser Text tatsächlich über die KI-Anbindung,
    genau wie der ✨-Knopf bei Objekttexten (app/ki/routes.py) — dieselbe
    generiere_json()-Infrastruktur, nur ohne require_campaign_gm: Spieler
    bauen ihren Charakter selbst und dürfen den Kommentar dazu auch selbst
    anfordern.

    27.09.2026, Marks Wunsch: der Kommentar bekommt ein spielerisches
    "NEW ACHIEVEMENT"-Format und geht explizit darauf ein, ob am Ende noch
    Karl-Klammer-Warnungen offen sind (= ignoriert, "Rebell") oder nicht
    (= beherzigt, "Befehlsempfänger") — dafür bekommt die KI den Status
    unmissverständlich als eigene Zeile im Prompt, nicht nur implizit über
    die Warnliste (das reichte Mistral in der Praxis nicht zum verlässlichen
    Einordnen).
    """
    weg_intern, magie_flavor = erstellung.normalisiere_weg(body.weg)
    if body.magieFlavor == "HAERETIKER":
        magie_flavor = "HAERETIKER"
    regeln = erstellung.regelwerk(await _rassen_der_kampagne(campaign_id))
    daten = berater.kommentar_daten(body.werte, weg_intern, regeln["attributKategorien"], magie_flavor)

    zeilen = [f"Weg: {daten['weg_anzeige']}"]
    zeilen.append(
        "Attribute: " + ", ".join(f"{k} {v}" for k, v in daten["attribut_summen"].items())
    )
    if daten["top_fertigkeiten"]:
        zeilen.append(f"Stärkste Fertigkeiten: {daten['top_fertigkeiten']}")
    if daten["magie_label"] is not None:
        zeilen.append(f"{daten['magie_label']}: {daten['magie_wert']}")
    if daten["warnungen"]:
        zeilen.append("Ignorierte Hinweise: " + " / ".join(daten["warnungen"]))
        zeilen.append("Status: hat die Balance-Hinweise NICHT beherzigt, baut stur weiter wie er will.")
    else:
        zeilen.append("Status: hat aktuell keine offenen Balance-Hinweise — wirkt ausgeglichen gebaut.")
    prompt = "\n".join(zeilen)

    try:
        ergebnis = await generiere_json(prompt, _KOMMENTAR_SYSTEM, _KOMMENTAR_SCHEMA, campaign_id=campaign_id)
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))

    kommentar = (ergebnis.get("kommentar") or "").strip()
    achievement = (ergebnis.get("achievement") or "").strip()
    if not kommentar:
        raise HTTPException(status_code=502, detail="Die KI hat keinen Kommentar geliefert.")
    await hooks.ki(
        campaign_id,
        anlass="erstellung-kommentar",
        prompt=prompt,
        antwort_text=f"{achievement}\n{kommentar}".strip(),
        uebernommen=False,
    )
    return {"achievement": achievement, "kommentar": kommentar}


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
    # Zusatzfertigkeiten (28.09.2026, Marks Korrektur): campaign-gebundener
    # Katalog, nicht Teil des ruleset-weiten TraitDef-Katalogs — eigene
    # Existenzprüfung der eingereichten IDs.
    zusatzfertigkeiten_katalog = await zusatzfertigkeiten_repository.liste(campaign_id)
    zusatzfertigkeit_ids = {z["id"] for z in zusatzfertigkeiten_katalog}
    # Rassenbindung (10.10.2026, Vaet-Transformation): ein nurFuerRasse-
    # Eintrag lässt sich nur von Charakteren DIESER Rasse wählen — gleiches
    # Häkchen-Prinzip wie Rassen-Freigabe, nur umgekehrt zugeordnet.
    nur_fuer_rasse = {z["id"]: z["nurFuerRasse"] for z in zusatzfertigkeiten_katalog if z.get("nurFuerRasse")}

    auswahl = body.model_dump()
    # Häretiker ist kein eigener Weg für die Mechanik (siehe WEGE in
    # erstellung.py) — auf "MAGIER" normalisieren, bevor geprüft/gerechnet
    # wird, und den gewählten Flavor separat mitschreiben.
    weg_intern, magie_flavor = erstellung.normalisiere_weg(body.weg)
    auswahl["weg"] = weg_intern
    verfuegbare_rassen = await _rassen_der_kampagne(campaign_id)
    einstellungen = await get_einstellungen(campaign_id)
    hintergrund_pool = await hintergruende_repository.pool_fuer_erstellung(campaign_id, einstellungen)
    fehler = erstellung.pruefe(auswahl, katalog, verfuegbare_rassen, einstellungen, hintergrund_pool)
    for zid in set(body.zusatzfertigkeitPunkte) | set(body.zusatzfertigkeitFreebees):
        if zid not in zusatzfertigkeit_ids:
            fehler.append(f"Unbekannte Zusatzfertigkeit: {zid}")
        elif zid in nur_fuer_rasse and nur_fuer_rasse[zid] != body.rasse:
            fehler.append(f"Diese Zusatzfertigkeit steht nur der Rasse {nur_fuer_rasse[zid]} offen.")
    if not body.name.strip():
        fehler.append("Der Charakter braucht einen Namen.")
    vermoegen, _schulden = erstellung.kapital(auswahl)
    tutorial_ausgegeben = int(person.get("tutorialAusgegeben") or 0)
    if erstellung.tutorial_rest(vermoegen, tutorial_ausgegeben) is None:
        fehler.append(
            f"Im Tutorial-Shop sind schon {tutorial_ausgegeben}¥ ausgegeben — "
            "Kredit und Eigenkapital müssen das decken."
        )
    if fehler:
        # 422 statt 400: die Anfrage ist wohlgeformt, nur regelwidrig.
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, {"fehler": fehler})

    werte = erstellung.endwerte(auswahl, verfuegbare_rassen)
    # Alles aus dem Katalog, was nicht vorkommt, ausdrücklich auf 0 — sonst
    # bliebe bei einer Korrektur durch die Spielleitung ein alter Wert stehen.
    erlaubte_kategorien = (
        {"Fertigkeit", erstellung.HINTERGRUND_KATEGORIE}
        | erstellung.KATEGORIEN_JE_WEG.get(weg_intern, set())
        | set(erstellung.ATTRIBUT_KATEGORIEN)
    )
    for eintrag in katalog:
        if eintrag["name"] not in werte and eintrag["category"] in erlaubte_kategorien:
            werte[eintrag["name"]] = 0
    # Rassen-Feature "gratisFertigkeitName" (10.10.2026, Zorak-Beispiel: +1
    # Anführen) — additiv auf eine NORMALE Fertigkeit aus dem Katalog, egal
    # was der Spieler dort selbst verteilt hat.
    rassen_feature = verfuegbare_rassen.get(body.rasse, {}) or {}
    werte = erstellung.wende_gratis_fertigkeit_an(werte, rassen_feature, katalog)
    await repository.set_ratings_bulk(campaign_id, person_id, werte)
    # Zusatzfertigkeiten: jede im Fertigkeiten-Schritt gewählte ID bekommt
    # eine Kante (auch mit rating 0 — sie wandert ins Blatt und kann dort
    # bzw. per Freebees/EP Punkte bekommen). Rating = Paket + Freebee.
    bereits_gewaehlt = await zusatzfertigkeiten_repository.gewaehlte_ids(campaign_id, person_id)
    neu_gewaehlt = set(body.zusatzfertigkeitPunkte or {})
    # Rassen-Feature "gratisZusatzfertigkeitId" (10.10.2026, Vaet-
    # Transformation): automatisch vergeben, zählt NICHT als normale Wahl —
    # darf deshalb von der Entfernen-Schleife unten nicht als "abgewählt"
    # missverstanden werden, nur weil sie nicht im body.zusatzfertigkeitPunkte
    # steht (sie kommt ja nicht aus dem Fertigkeiten-Schritt-Flow).
    gratis_zf_id = (verfuegbare_rassen.get(body.rasse, {}) or {}).get("gratisZusatzfertigkeitId") or ""
    for zid in bereits_gewaehlt - neu_gewaehlt - {gratis_zf_id}:
        await zusatzfertigkeiten_repository.entferne_von_person(campaign_id, person_id, zid)
    freebees_zf = body.zusatzfertigkeitFreebees or {}
    for zid in neu_gewaehlt:
        rating = int(body.zusatzfertigkeitPunkte.get(zid, 0)) + int(freebees_zf.get(zid, 0))
        if zid == gratis_zf_id:
            # Analog zum Hexkraft-/NeuroWeaving-Sockel (erstellung.py::
            # MAGIE_FIXWERT): das Frontend schickt hier NUR die zusätzliche
            # Investition über den festen 1-Punkt-Sockel hinaus (23.10.2026,
            # Mark: "es lässt mich keinen weiteren Punkt dazu vergeben" —
            # der Sockel-Punkt selbst fehlte in der Summe). Der feste Punkt
            # kommt hier oben drauf, unabhängig vom Paket-Budget.
            rating += 1
        await zusatzfertigkeiten_repository.hinzufuegen(campaign_id, person_id, zid, rating)
    # Automatische Vergabe mit 1 Punkt — nur falls der Spieler in diesem
    # Schritt GAR NICHTS dazu eingereicht hat (zid nicht in body.
    # zusatzfertigkeitPunkte) UND es noch nicht vorher vergeben war. Eine
    # erneute Einreichung (SL-Korrektur) darf eine vom Spieler zwischenzeitlich
    # gesteigerte Stufe nicht wieder auf 1 zurücksetzen.
    if gratis_zf_id and gratis_zf_id not in bereits_gewaehlt and gratis_zf_id not in neu_gewaehlt:
        gratis_zf_katalog = {z["id"] for z in zusatzfertigkeiten_katalog}
        if gratis_zf_id in gratis_zf_katalog:
            await zusatzfertigkeiten_repository.hinzufuegen(campaign_id, person_id, gratis_zf_id, 1)
    # Der Rassendeckel gilt ein Leben lang, nicht nur bei der Erstellung —
    # er muss deshalb als maxOverride ans Blatt (siehe
    # erstellung.py::lebensmaxima). Ohne diesen Schritt fiel jedes Attribut
    # nach der Erstellung auf das Katalogmaximum zurück, und die Rasse war
    # danach wirkungslos.
    await repository.setze_maxima_bulk(
        campaign_id, person_id, erstellung.lebensmaxima(body.rasse, katalog, verfuegbare_rassen)
    )

    # Rassen-Feature "gratisGegenstandId" (10.10.2026, Dug'Rah-Rüstung): bei
    # der Erstellung automatisch zugewiesen, nur einmal (SL-Korrektur legt
    # keine zweite Kopie nach). Rein additiv — kein eigener Fehlerpfad, ein
    # fehlender/gelöschter Gegenstand lässt die Erstellung trotzdem durch.
    gratis_gegenstand_id = (verfuegbare_rassen.get(body.rasse, {}) or {}).get("gratisGegenstandId") or ""
    gratis_erhalten = bool(person.get("gratisGegenstandErhalten"))
    if gratis_gegenstand_id and not gratis_erhalten:
        vorlage = await items_repository.get_gegenstand(campaign_id, gratis_gegenstand_id)
        if vorlage is not None:
            kopie = await items_repository.assign_copy(campaign_id, vorlage, person_id, "SPEZIFISCH", [person_id])
            # Bugfix (12.10.2026, Dug'Rah-Fall live auf bebop nachgestellt):
            # zwei Probleme, beide bei derselben Zuweisung.
            # (1) assign_copy übernimmt `ablage` unverändert von der Vorlage
            # — Vorlagen liegen auf dem Schema-Default "RUCKSACK". Für
            # istNatuerlich-Rüstung gibt es aber gar keinen Weg, sie
            # "anzulegen": sie ist dem Spieler im Inventar absichtlich
            # verborgen (siehe SpielerAnsicht.tsx::istVersteckteAusruestung).
            # (2) `ruestungKaestchenAktuell` kommt ebenfalls als Vorlagen-
            # Platzhalter (0) mit — `anwende_natuerliche_ruestung` klemmt das
            # Kästchen-Max zwar live auf die Widerstandsfähigkeit, hebt aber
            # nie ein zu niedriges Aktuell an (das wäre sonst ununterscheidbar
            # von einer echten Beschädigung). Ohne Initialisierung hier blieb
            # die frische Rüstung für immer bei 0/0 "zerstört" hängen, und
            # `kampf/ruestung.py::reihenfolge` filtert 0-Kästchen-Teile aus dem
            # Pool — das Blatt zeigte die ganze Rüstungszeile gar nicht erst
            # an (`bogen.ruestung.kaestchenMax > 0`-Check in Charakterblatt.tsx).
            # Beides zusammen macht sie erst zu dem, was sie sein soll: von
            # Anfang an vollständig intakt und angelegt, ohne Spieler-Zutun.
            if kopie is not None and kopie.get("istNatuerlich"):
                await items_repository.set_ablage(campaign_id, kopie["id"], "AUSGERUESTET", None)
                widerstandsfaehigkeit = max(0, int(werte.get("Widerstandsfähigkeit", 0)))
                await items_repository.update_gegenstand(
                    campaign_id, kopie["id"], {"ruestungKaestchenAktuell": widerstandsfaehigkeit}
                )
            gratis_erhalten = True

    vermoegen, schulden = erstellung.kapital(auswahl)
    # Tutorial-Shop (10.10.2026): bereits im Freebees-Schritt ausgegebenes
    # Geld wird hier final abgezogen, NICHT überschrieben — sonst würde ein
    # Shop-Einkauf beim finalen Submit kommentarlos rückgängig gemacht.
    tutorial_ausgegeben = int(person.get("tutorialAusgegeben") or 0)
    aktualisiert = await update_node(
        "Person",
        PERSON_FIELDS,
        campaign_id,
        person_id,
        {
            "weg": weg_intern,
            "magieFlavor": magie_flavor,
            "rasse": body.rasse,
            "willenskraftBonus": body.freebeeWillenskraft,
            "name": body.name.strip(),
            "konzept": body.konzept,
            "alter": body.alter,
            "ambition": body.ambition,
            "verlangen": body.verlangen,
            "ziel": body.ziel,
            "kapital": max(0, vermoegen - tutorial_ausgegeben),
            "kapitalBasis": max(0, vermoegen - tutorial_ausgegeben),
            "schulden": schulden,
            "gratisGegenstandErhalten": gratis_erhalten,
            "erstellungAbgeschlossen": True,
        },
    )

    # Schulden aus Kredit-Freebees: Hai wiederverwenden oder Stub in der
    # Schmiede. Scheitert das, ist der PC trotzdem fertig — der Hai ist Folge.
    if body.freebeeKredit > 0:
        try:
            await kredithai_nach_erstellung(campaign_id, person_id, body.freebeeKredit)
        except Exception:
            logging.getLogger(__name__).exception(
                "Kredithai nach Erstellung fehlgeschlagen (person=%s)", person_id
            )

    # Mentor/Kontakte aus Hintergrundpunkten (11.10.2026): derselbe
    # Grundsatz wie Kredithai — der PC ist auch fertig, wenn das hier
    # scheitert, siehe hintergruende/spawn.py.
    mentor_rating = int(werte.get("Mentor") or 0)
    if mentor_rating > 0:
        try:
            await mentor_nach_erstellung(campaign_id, person_id, body.name.strip(), mentor_rating)
        except Exception:
            logging.getLogger(__name__).exception(
                "Mentor-Pipeline nach Erstellung fehlgeschlagen (person=%s)", person_id
            )
    kontakte_rating = int(werte.get("Kontakte") or 0)
    if kontakte_rating > 0:
        try:
            await kontakte_nach_erstellung(campaign_id, person_id, kontakte_rating)
        except Exception:
            logging.getLogger(__name__).exception(
                "Kontakte-Pipeline nach Erstellung fehlgeschlagen (person=%s)", person_id
            )

    neue_werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    einstellungen = await get_einstellungen(campaign_id)
    kampagnen_ep = einstellungen.get("kampagnenEP", 0)
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    chrom = await willenskraft_verlust(campaign_id, person_id)
    init_mod = await initiative_modifikator(campaign_id, person_id)
    return {
        "uebersicht": bogen_uebersicht(
            aktualisiert or person, {w["name"]: w["rating"] for w in neue_werte}, cyberwall, chrom, init_mod, kampagnen_ep
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


async def _materia_preise(campaign_id: str, person_id: str) -> list[dict]:
    """Materia-Fertigkeiten (29.10.2026) als Einträge im selben Format wie
    `erfahrung.preisliste` — erscheinen dadurch unverändert im normalen
    "Fähigkeiten"-Abschnitt des EP-Blatts (Kategorie immer "Fertigkeit"),
    obwohl ihre Stufe am GEGENSTAND statt an der Person hängt. Siehe
    `erfahrung.materia_schluessel`/`materia_entschluesseln` für den
    synthetischen traitDefId, der beide Welten verbindet.
    """
    rohdaten = await items_repository.materia_fertigkeiten_liste(campaign_id, person_id)
    eintraege = []
    for r in rohdaten:
        preis = erfahrung.kosten("Fertigkeit", r["aktuell"])
        if preis is None:
            continue
        eintraege.append(
            {
                "traitDefId": erfahrung.materia_schluessel(r["gegenstandId"], r["name"]),
                "name": f"{r['name']} ({r['gegenstandName']})",
                "category": "Fertigkeit",
                "aktuell": r["aktuell"],
                "max": 6,
                "kosten": preis,
            }
        )
    return eintraege


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
    erlaubt = sichtbare_kategorien(
        person.get("weg") or "KEINER",
        {t["category"] for t in katalog},
        bool(person.get("istKI")),
        bool(person.get("istDrohne")) or bool(person.get("istFahrzeug")),
    )
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    nach_name = {w["name"]: w["rating"] for w in werte}
    # Vom Spielleiter angehobene Maxima gelten auch beim Steigern.
    grenzen = {w["traitDefId"]: w["max"] for w in werte}

    preise = erfahrung.preisliste([t for t in katalog if t["category"] in erlaubt], nach_name)
    for eintrag in preise:
        eintrag["max"] = grenzen.get(eintrag["traitDefId"], eintrag["max"])
    preise += await _materia_preise(campaign_id, person_id)

    chrom = await willenskraft_verlust(campaign_id, person_id)
    willenskraft = willenskraft_max(nach_name, int(person.get("willenskraftBonus") or 0), chrom)
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
        chrom = await willenskraft_verlust(campaign_id, person_id)
        aktuell = willenskraft_max(nach_name, int(person.get("willenskraftBonus") or 0), chrom)
        preis = erfahrung.kosten_willenskraft(aktuell)
        if preis > verfuegbar:
            raise HTTPException(status.HTTP_409_CONFLICT, f"{preis} EP nötig, {verfuegbar} vorhanden.")
        neuer_bonus = int(person.get("willenskraftBonus") or 0) + 1
        await update_node(
            "Person",
            PERSON_FIELDS,
            campaign_id,
            person_id,
            {
                "willenskraftBonus": neuer_bonus,
                "erfahrungAusgegeben": ausgegeben + preis,
            },
        )
        # Ereignisprotokoll: Willenskraft-Steigerung ist EINE der drei
        # CharakterEntwicklung-Arten (docs/wiki/entities/ereignisprotokoll.md).
        await hooks.charakterentwicklung(
            campaign_id, person_id=person_id, art="WILLENSKRAFT",
            alt=str(neuer_bonus - 1), neu=str(neuer_bonus), kosten_oder_menge=preis,
        )
    else:
        if not body.traitDefId:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein Wert angegeben")

        materia_info = erfahrung.materia_entschluesseln(body.traitDefId)
        if materia_info is not None:
            gegenstand_id, materia_name = materia_info
            rohdaten = await items_repository.materia_fertigkeiten_liste(campaign_id, person_id)
            eintrag = next(
                (r for r in rohdaten if r["gegenstandId"] == gegenstand_id and r["name"] == materia_name),
                None,
            )
            if eintrag is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    "Diese Materia-Fähigkeit ist nicht (mehr) verfügbar — Gegenstand nicht "
                    "mehr im Besitz, nicht mehr ausgerüstet, oder nicht mehr als Materia markiert.",
                )
            if eintrag["aktuell"] >= 6:
                raise HTTPException(status.HTTP_409_CONFLICT, f"{materia_name} steht bereits auf dem Maximum 6.")

            preis = erfahrung.kosten("Fertigkeit", eintrag["aktuell"]) or 0
            if preis > verfuegbar:
                raise HTTPException(status.HTTP_409_CONFLICT, f"{preis} EP nötig, {verfuegbar} vorhanden.")

            aktualisiertes_item = await items_repository.steigere_materia_fertigkeit(
                campaign_id, gegenstand_id, person_id, materia_name
            )
            if aktualisiertes_item is None:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "Der Gegenstand ist zwischenzeitlich nicht mehr verfügbar.",
                )
            await update_node(
                "Person",
                PERSON_FIELDS,
                campaign_id,
                person_id,
                {"erfahrungAusgegeben": ausgegeben + preis},
            )
            # Ereignisprotokoll: Materia-Steigerung zählt wie eine normale
            # Punktsteigerung, nur mit dem Gegenstandsnamen in der Notiz —
            # kein eigener traitDefId (der gehört ja keinem TraitDef-Katalog).
            await hooks.charakterentwicklung(
                campaign_id, person_id=person_id, art="STEIGERUNG",
                trait_name=f"{materia_name} ({aktualisiertes_item['name']})",
                alt=str(eintrag["aktuell"]), neu=str(eintrag["aktuell"] + 1), kosten_oder_menge=preis,
            )
            return await get_steigerungspreise(campaign_id, person_id, viewer)

        campaign = await get_campaign(campaign_id)
        katalog = await repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
        eintrag = next((t for t in katalog if t["id"] == body.traitDefId), None)
        if eintrag is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Wert nicht gefunden")

        erlaubt = sichtbare_kategorien(
            person.get("weg") or "KEINER",
            {t["category"] for t in katalog},
            bool(person.get("istKI")),
            bool(person.get("istDrohne")) or bool(person.get("istFahrzeug")),
        )
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
        # Ereignisprotokoll: Punktkauf ist die zweite CharakterEntwicklung-Art.
        await hooks.charakterentwicklung(
            campaign_id, person_id=person_id, art="STEIGERUNG",
            trait_def_id=body.traitDefId, trait_name=eintrag["name"],
            alt=str(aktuell), neu=str(aktuell + 1), kosten_oder_menge=preis,
        )

    return await get_steigerungspreise(campaign_id, person_id, viewer)


class ErfahrungInput(BaseModel):
    punkte: int = Field(ge=0)
    # Ereignisprotokoll (27.09.2026, Marks Wunsch): optionale Begründung,
    # landet direkt in slNotiz des CharakterEntwicklung-Eintrags — kein
    # eigenes Feld nötig (siehe docs/wiki/entities/ereignisprotokoll.md).
    begruendung: str = ""


@router.post("/personen/{person_id}/erfahrung", dependencies=[Depends(require_campaign_gm)])
async def vergib_erfahrung(campaign_id: str, person_id: str, body: ErfahrungInput) -> dict:
    """Erfahrung vergeben. Ausschliesslich Sache der Spielleitung."""
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")
    alte_erfahrung = int(person.get("erfahrung") or 0)
    aktualisiert = await update_node(
        "Person",
        PERSON_FIELDS,
        campaign_id,
        person_id,
        {"erfahrung": alte_erfahrung + body.punkte},
    )
    # Ereignisprotokoll: EP-Vergabe ist die dritte CharakterEntwicklung-Art.
    await hooks.charakterentwicklung(
        campaign_id, person_id=person_id, art="ERFAHRUNG_VERGEBEN",
        alt=str(alte_erfahrung), neu=str(alte_erfahrung + body.punkte),
        kosten_oder_menge=body.punkte, sl_notiz=body.begruendung,
    )
    einstellungen = await get_einstellungen(campaign_id)
    kampagnen_ep = einstellungen.get("kampagnenEP", 0)
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    chrom = await willenskraft_verlust(campaign_id, person_id)
    init_mod = await initiative_modifikator(campaign_id, person_id)
    return bogen_uebersicht(aktualisiert or person, {w["name"]: w["rating"] for w in werte}, cyberwall, chrom, init_mod, kampagnen_ep)


# =====================================================================
# NPC-Catch-up
# =====================================================================


class CatchupInput(BaseModel):
    """Referenz-PC + Skalierung. 100% = gleichauf mit dem Referenz-PC,
    >100% = bewusst stärker (Bosse), <100% = bewusst schwächer."""

    referenzPersonId: str
    prozent: int = Field(gt=0, le=1000)


@router.post("/personen/{person_id}/catchup", dependencies=[Depends(require_campaign_gm)])
async def npc_catchup(campaign_id: str, person_id: str, body: CatchupInput) -> dict:
    """Hebt einen NPC auf (einen Anteil von) das EP- und Vermögensniveau
    eines Referenz-PCs — inklusive automatischer Werteverteilung und
    Einkauf/Ausrüstung. Siehe app/traits/catchup.py für die Herleitung.
    """
    campaign = await get_campaign(campaign_id)
    einstellungen = await get_einstellungen(campaign_id)
    ergebnis = await catchup.fuehre_catchup_durch(
        campaign_id, person_id, body.referenzPersonId, body.prozent,
        einstellungen, campaign["ruleset"] if campaign else "neotopia",
    )
    if ergebnis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "NPC oder Referenz-Charakter nicht gefunden")
    return ergebnis.model_dump()
