from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_campaign, get_einstellungen
from app.entities.repository import PERSON_FIELDS, get_node, update_node
from app.ereignisprotokoll import hooks
from app.kampf import repository as kampf_repository
from app.items.repository import (
    ausruestungs_trait_boni,
    ausruestungsfertigkeiten_liste,
    commlink_cyberwall,
    deck_boni,
    initiative_modifikator,
    ruestungsteile,
    set_ablage,
    update_gegenstand,
    willenskraft_verlust,
)
from app.kampf.ruestung import (
    berechne_treffer,
    pool,
    uebersicht as ruestungs_uebersicht,
    verteile_kaestchenschaden,
)
from app.ki.client import KiFehler, generiere_json
from app.rassen import repository as rassen_repository
from app.traits import berater, erfahrung, erstellung, repository
from app.traits.bogen import (
    bogen_uebersicht,
    sichtbare_kategorien,
    willenskraft_max,
    zustand_verboten,
)
from app.traits.schemas import TraitDefResponse, TraitRatingResponse, TraitRatingUpdate
from app.zusatzfertigkeiten import repository as zusatzfertigkeiten_repository

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
    Magier ist, bekommt Sphaeren und Hexkraft gar nicht erst zu sehen.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
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
    erlaubt = sichtbare_kategorien(person.get("weg") or "KEINER", {t["category"] for t in katalog}, bool(person.get("istKI")))

    return {
        "person": {"id": person["id"], "name": person["name"], "personType": person["personType"], "istKI": bool(person.get("istKI"))},
        "uebersicht": bogen_uebersicht(person, nach_name, cyberwall, chrom, init_mod, kampagnen_ep),
        # Bonuswürfel aus ausgerüsteten Cyberdecks — gehören nicht zu den
        # Werten der Person, sondern zu ihrer Ausrüstung, deshalb daneben.
        "deckBoni": await deck_boni(campaign_id, person_id),
        # Bonuswürfel auf BESTEHENDE Werte aus ausgerüsteten Gegenständen
        # (z.B. Cyberaugen +1 auf Wahrnehmung) — Schlüssel ist der TraitDef-
        # Name, das Frontend addiert das direkt zur Anzeige des Werts dazu.
        "ausruestungsBoni": await ausruestungs_trait_boni(campaign_id, person_id),
        # NEUE Fertigkeiten, die es ohne die Ausrüstung nicht gibt (z.B. ein
        # Zauberstab mit "Springen 3") — eigener Blattabschnitt, siehe
        # CharacterSheetPanel.tsx.
        "ausruestungsfertigkeiten": await ausruestungsfertigkeiten_liste(campaign_id, person_id),
        # Rüstung als dritte Kästchenreihe neben Gesundheit und Willenskraft
        # (siehe docs/api/ruestung.md). Kommt fertig gerechnet vom Server,
        # damit die Pool-Regel nicht im Blatt nachgebaut wird.
        "ruestung": ruestungs_uebersicht(await ruestungsteile(campaign_id, person_id)),
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

    **Willenskraft ist eine Einbahnstraße für Spieler**: ausgeben ja,
    zurückholen nein. Sie kehrt zurück, wenn die Spielleitung es sagt.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    aenderung = body.model_dump()

    # Die Regel selbst steht in bogen.py und ist dort geprüft.
    if viewer.role != "GM":
        vorher = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
        if vorher is None:
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
    (CLAUDE.md, Punkt 12). Alter bleibt bewusst aussen vor.
    """

    konzept: str | None = None
    ambition: str | None = None
    verlangen: str | None = None
    ziel: str | None = None


@router.patch("/personen/{person_id}/steckbrief")
async def set_steckbrief(
    campaign_id: str,
    person_id: str,
    body: SteckbriefUpdate,
    viewer: Viewer = Depends(get_viewer),
) -> dict:
    """Konzept, Ambition, Verlangen und Ziel nachträglich ändern.

    Dieselbe Erlaubnis wie bei `zustand`: Spieler nur am eigenen Charakter
    (404 bei fremden Personen), die Spielleitung überall. Anders als bei
    Zustand keine Einbahnstraße — ein leerer String löscht ein Feld bewusst,
    `update_node` filtert nur `None` heraus, nicht die leere Zeichenkette.
    """
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await update_node("Person", PERSON_FIELDS, campaign_id, person_id, body.model_dump())
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    einstellungen = await get_einstellungen(campaign_id)
    kampagnen_ep = einstellungen.get("kampagnenEP", 0)
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    chrom = await willenskraft_verlust(campaign_id, person_id)
    init_mod = await initiative_modifikator(campaign_id, person_id)
    return bogen_uebersicht(person, {w["name"]: w["rating"] for w in werte}, cyberwall, chrom, init_mod, kampagnen_ep)


# =====================================================================
# Rüstungstreffer (Formel: kampf/ruestung.py, Begründung: docs/api/ruestung.md)
# =====================================================================

# Dieselben drei Begriffe wie überall sonst im Tool (schadenSchlag/Schwer/
# Aggraviert, Kaestchen.tsx::Schadensart) — am Tisch heissen sie
# Schlag/Tödlich/Unheilbar, die Übersetzung passiert nur in der Oberfläche.
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
    if viewer.role != "GM" and person_id != viewer.person_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    gesamt = pool(await ruestungsteile(campaign_id, person_id))
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

    einstellungen = await get_einstellungen(campaign_id)
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    cyberwall = await commlink_cyberwall(campaign_id, person_id)
    chrom = await willenskraft_verlust(campaign_id, person_id)
    init_mod = await initiative_modifikator(campaign_id, person_id)
    return RuestungTrefferErgebnis(
        hpArt=ergebnis["hpArt"],
        hpMenge=ergebnis["hpMenge"],
        kaestchenSchaden=ergebnis["kaestchenSchaden"],
        betroffen=[RuestungsteilFolge(**f) for f in folgen],
        uebersicht=bogen_uebersicht(
            person,
            {w["name"]: w["rating"] for w in werte},
            cyberwall,
            chrom,
            init_mod,
            einstellungen.get("kampagnenEP", 0),
        ),
    )


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
        }
        for r in await rassen_repository.liste_fuer_kampagne(campaign_id)
    }


@router.get("/erstellung/regeln")
async def get_erstellungsregeln(campaign_id: str) -> dict:
    """Rassen, Pakete, Hintergründe, Freebee-Preise.

    Auch für Spieler lesbar — sie erstellen ihren Charakter selbst, und die
    Regeln sind nichts Geheimes. Die Rassen kommen aus der Freigabe dieser
    Kampagne, nicht mehr aus der fest verdrahteten Tabelle.
    """
    return erstellung.regelwerk(await _rassen_der_kampagne(campaign_id))


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

    auswahl = body.model_dump()
    # Häretiker ist kein eigener Weg für die Mechanik (siehe WEGE in
    # erstellung.py) — auf "MAGIER" normalisieren, bevor geprüft/gerechnet
    # wird, und den gewählten Flavor separat mitschreiben.
    weg_intern, magie_flavor = erstellung.normalisiere_weg(body.weg)
    auswahl["weg"] = weg_intern
    verfuegbare_rassen = await _rassen_der_kampagne(campaign_id)
    fehler = erstellung.pruefe(auswahl, katalog, verfuegbare_rassen)
    for zid in set(body.zusatzfertigkeitPunkte) | set(body.zusatzfertigkeitFreebees):
        if zid not in zusatzfertigkeit_ids:
            fehler.append(f"Unbekannte Zusatzfertigkeit: {zid}")
    if not body.name.strip():
        fehler.append("Der Charakter braucht einen Namen.")
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
    await repository.set_ratings_bulk(campaign_id, person_id, werte)
    # Zusatzfertigkeiten: jede im Fertigkeiten-Schritt gewählte ID bekommt
    # eine Kante (auch mit rating 0 — sie wandert ins Blatt und kann dort
    # bzw. per Freebees/EP Punkte bekommen). Rating = Paket + Freebee.
    bereits_gewaehlt = await zusatzfertigkeiten_repository.gewaehlte_ids(campaign_id, person_id)
    neu_gewaehlt = set(body.zusatzfertigkeitPunkte or {})
    for zid in bereits_gewaehlt - neu_gewaehlt:
        await zusatzfertigkeiten_repository.entferne_von_person(campaign_id, person_id, zid)
    freebees_zf = body.zusatzfertigkeitFreebees or {}
    for zid in neu_gewaehlt:
        rating = int(body.zusatzfertigkeitPunkte.get(zid, 0)) + int(freebees_zf.get(zid, 0))
        await zusatzfertigkeiten_repository.hinzufuegen(campaign_id, person_id, zid, rating)
    # Der Rassendeckel gilt ein Leben lang, nicht nur bei der Erstellung —
    # er muss deshalb als maxOverride ans Blatt (siehe
    # erstellung.py::lebensmaxima). Ohne diesen Schritt fiel jedes Attribut
    # nach der Erstellung auf das Katalogmaximum zurück, und die Rasse war
    # danach wirkungslos.
    await repository.setze_maxima_bulk(
        campaign_id, person_id, erstellung.lebensmaxima(body.rasse, katalog, verfuegbare_rassen)
    )

    vermoegen, schulden = erstellung.kapital(auswahl)
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
            "kapital": vermoegen,
            "schulden": schulden,
            "erstellungAbgeschlossen": True,
        },
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
    erlaubt = sichtbare_kategorien(person.get("weg") or "KEINER", {t["category"] for t in katalog}, bool(person.get("istKI")))
    werte = await repository.get_ratings_for_entity(campaign_id, person_id)
    nach_name = {w["name"]: w["rating"] for w in werte}
    # Vom Spielleiter angehobene Maxima gelten auch beim Steigern.
    grenzen = {w["traitDefId"]: w["max"] for w in werte}

    preise = erfahrung.preisliste([t for t in katalog if t["category"] in erlaubt], nach_name)
    for eintrag in preise:
        eintrag["max"] = grenzen.get(eintrag["traitDefId"], eintrag["max"])

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
        campaign = await get_campaign(campaign_id)
        katalog = await repository.list_catalog(campaign["ruleset"] if campaign else "neotopia")
        eintrag = next((t for t in katalog if t["id"] == body.traitDefId), None)
        if eintrag is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Wert nicht gefunden")

        erlaubt = sichtbare_kategorien(person.get("weg") or "KEINER", {t["category"] for t in katalog}, bool(person.get("istKI")))
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
