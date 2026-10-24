"""NPC-Catch-up: einen NPC gezielt auf das Niveau eines Referenz-PCs heben
(24.10.2026, Marks Wunsch).

Hintergrund: `kampagnenEP` (campaigns/repository.py) wirkt automatisch auf
JEDE Person inklusive NPCs (siehe bogen.py::bogen_uebersicht) — ein NPC ist
dadurch nie "zurück", aber auch nie gezielt STÄRKER als die Gruppe (Bosse).
Dieser Catch-up ist das gezielte Gegenstück: die SL wählt einen Referenz-PC
und einen Prozentsatz (100% = gleichauf, >100% = Boss, <100% = bewusst
schwächer) und der NPC bekommt EP UND Vermögen in diesem Verhältnis
zugewiesen — vollautomatisch verbaut/ausgerüstet und auf Werte verteilt
(Mark: "direkt ohne Rückfrage").

**Wichtig gegen Doppelzählung:** Da `kampagnenEP` dem NPC ohnehin automatisch
zufließt (s.o.), wird es beim Festlegen von `Person.erfahrung` wieder
herausgerechnet — sonst bekäme der NPC es doppelt (einmal fest eingebucht,
einmal weiterhin live aus den Kampagnen-Einstellungen).
"""

from pydantic import BaseModel

from app.entities.repository import PERSON_FIELDS, get_node, update_node
from app.ereignisprotokoll import hooks
from app.haendler import ki_einkauf
from app.items import chirurgie
from app.items.repository import get_gegenstand, list_gegenstaende, set_ablage, setze_verbaut, willenskraft_verlust
from app.traits import erfahrung, ki_catchup, repository as traits_repository
from app.traits.bogen import sichtbare_kategorien, willenskraft_max

# Diese Typen landen nicht am Körper (siehe items/routes.py::NICHT_AM_KOERPER)
# oder sind Verbrauchsgüter ohne sinnvollen "ausgerüstet"-Zustand — die
# kauft die KI zwar ggf. mit ein, aber das automatische Ausrüsten lässt sie
# im Rucksack liegen statt sie an den Körper zu legen.
_NICHT_AUTOMATISCH_AUSRUESTEN = {"Fahrzeug", "Munition", "Droge", "Reparaturmaterial"}


class CatchupErgebnis(BaseModel):
    referenzName: str
    budgetEp: int
    budgetGeld: int
    erfahrungGesamt: int
    gekauft: list[str] = []
    steigerungen: list[str] = []


def erfahrung_gesamt_person(person: dict, kampagnen_ep: int) -> int:
    """Alle EP, die dieser Person je zugeflossen sind — dieselbe Formel wie
    `bogen.py::bogen_uebersicht` ("individuelle Erfahrung + Kampagnen-EP +
    Extra-EP"), hier separat, weil der Catch-up sie für den REFERENZ-PC
    braucht, ohne den ganzen Bogen aufzubauen."""
    return int(person.get("erfahrung") or 0) + kampagnen_ep + int(person.get("extraEP") or 0)


def vermoegen_person(person: dict, gegenstaende: list[dict]) -> int:
    """Bargeld + Kaufpreis aller besessenen Gegenstände — das tatsächliche
    "Vermögen", nicht nur das, was gerade als Bargeld auf der Tasche ist
    (Mark: ein Charakter, der alles in Ausrüstung gesteckt hat, soll nicht
    als "arm" gelten)."""
    kapital = int(person.get("kapital") or 0)
    warenwert = sum(int(g.get("preis") or 0) for g in gegenstaende)
    return kapital + warenwert


def berechne_budget(wert: int, prozent: int) -> int:
    """`wert * prozent / 100`, gerundet, nie negativ."""
    return max(0, round(wert * prozent / 100))


def ziel_erfahrung(budget_ep: int, kampagnen_ep: int, npc_extra_ep: int) -> int:
    """Wie viel `erfahrung` (individuelles Feld) der NPC braucht, damit sein
    `erfahrungGesamt` (das automatisch + kampagnenEP + extraEP rechnet)
    am Ende genau `budget_ep` ergibt — ohne `kampagnenEP` doppelt zu
    zählen, das der NPC ja ohnehin schon automatisch bekommt."""
    return max(0, budget_ep - kampagnen_ep - npc_extra_ep)


async def _verteile_ep_automatisch(
    campaign_id: str, person_id: str, ruleset: str, charakterkontext: str
) -> list[str]:
    """Lässt die KI das aktuell verfügbare EP-Budget des NPCs auf Werte
    verteilen und bucht jeden bezahlbaren Schritt serverseitig ab. Gibt die
    Namen der tatsächlich gekauften Steigerungen zurück (fürs Protokoll)."""
    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        return []
    katalog = await traits_repository.list_catalog(ruleset)
    werte = await traits_repository.get_ratings_for_entity(campaign_id, person_id)
    nach_name = {w["name"]: w["rating"] for w in werte}
    grenzen = {w["traitDefId"]: w["max"] for w in werte}
    erlaubt = sichtbare_kategorien(person.get("weg") or "KEINER", {t["category"] for t in katalog}, bool(person.get("istKI")))

    preise = erfahrung.preisliste([t for t in katalog if t["category"] in erlaubt], nach_name)
    for eintrag in preise:
        eintrag["max"] = grenzen.get(eintrag["traitDefId"], eintrag["max"])
    nach_id = {e["traitDefId"]: e for e in preise}

    chrom = await willenskraft_verlust(campaign_id, person_id)
    wk_aktuell = willenskraft_max(nach_name, int(person.get("willenskraftBonus") or 0), chrom)
    willenskraft_info = {"aktuell": wk_aktuell, "kosten": erfahrung.kosten_willenskraft(wk_aktuell)}

    verfuegbar = max(0, int(person.get("erfahrung") or 0) - int(person.get("erfahrungAusgegeben") or 0))
    if verfuegbar <= 0:
        return []

    plan = await ki_catchup.vorschlag(campaign_id, charakterkontext, preise, willenskraft_info, verfuegbar)

    gekauft: list[str] = []
    ausgegeben = int(person.get("erfahrungAusgegeben") or 0)
    wk_bonus = int(person.get("willenskraftBonus") or 0)
    for trait_def_id in plan.traitDefIds:
        if trait_def_id == "WILLENSKRAFT":
            wk_stand = willenskraft_max(nach_name, wk_bonus, chrom)
            preis = erfahrung.kosten_willenskraft(wk_stand)
            if preis > verfuegbar:
                continue
            wk_bonus += 1
            verfuegbar -= preis
            ausgegeben += preis
            gekauft.append(f"Willenskraft → {wk_bonus}")
            continue

        eintrag = nach_id.get(trait_def_id)
        if eintrag is None:
            continue
        aktuell = nach_name.get(eintrag["name"], 0)
        if aktuell >= eintrag["max"]:
            continue
        preis = erfahrung.kosten(eintrag["category"], aktuell)
        if preis is None or preis > verfuegbar:
            continue
        neu = aktuell + 1
        await traits_repository.set_rating(campaign_id, person_id, trait_def_id, neu, None)
        nach_name[eintrag["name"]] = neu
        verfuegbar -= preis
        ausgegeben += preis
        gekauft.append(f"{eintrag['name']} → {neu}")

    await update_node(
        "Person", PERSON_FIELDS, campaign_id, person_id,
        {"willenskraftBonus": wk_bonus, "erfahrungAusgegeben": ausgegeben},
    )
    return gekauft


async def _kaufe_und_rueste_aus(campaign_id: str, person_id: str, budget_geld: int, charakterkontext: str) -> list[str]:
    """Lässt die KI im Tutorial-Shop einkaufen (ki_einkauf.einkaufen) und
    rüstet/verbaut jedes gekaufte Stück sofort — Mark: "wichtig ist das die
    Gegenstände ausgerüstet und eingebaut werden und nicht nur mitgeführt"."""
    ergebnis = await ki_einkauf.einkaufen(campaign_id, person_id, budget_geld, charakterkontext)
    if ergebnis is None:
        return []
    for item_id in ergebnis.gekauftIds:
        gegenstand = await get_gegenstand(campaign_id, item_id)
        if gegenstand is None:
            continue
        if chirurgie.ist_chrom(gegenstand):
            await setze_verbaut(campaign_id, item_id, True)
        elif gegenstand.get("typ") not in _NICHT_AUTOMATISCH_AUSRUESTEN:
            await set_ablage(campaign_id, item_id, "AUSGERUESTET", None)
    return ergebnis.gekauft


async def fuehre_catchup_durch(
    campaign_id: str, npc_id: str, referenz_person_id: str, prozent: int, einstellungen: dict, ruleset: str
) -> CatchupErgebnis | None:
    """Der komplette Catch-up: EP + Vermögen vom Referenz-PC übernehmen
    (×prozent), auf den NPC schreiben, automatisch auf Werte verteilen und
    im Tutorial-Shop einkaufen+ausrüsten. `None`, wenn Referenz-PC oder NPC
    nicht existieren."""
    referenz = await get_node("Person", PERSON_FIELDS, campaign_id, referenz_person_id)
    npc = await get_node("Person", PERSON_FIELDS, campaign_id, npc_id)
    if referenz is None or npc is None:
        return None

    kampagnen_ep = int(einstellungen.get("kampagnenEP", 0) or 0)
    ref_gesamt = erfahrung_gesamt_person(referenz, kampagnen_ep)
    ref_gegenstaende = await list_gegenstaende(campaign_id, referenz_person_id)
    ref_vermoegen = vermoegen_person(referenz, ref_gegenstaende)

    budget_ep = berechne_budget(ref_gesamt, prozent)
    budget_geld = berechne_budget(ref_vermoegen, prozent)

    npc_extra_ep = int(npc.get("extraEP") or 0)
    alt_erfahrung = int(npc.get("erfahrung") or 0)
    neue_erfahrung = ziel_erfahrung(budget_ep, kampagnen_ep, npc_extra_ep)
    await update_node("Person", PERSON_FIELDS, campaign_id, npc_id, {"erfahrung": neue_erfahrung})
    await hooks.charakterentwicklung(
        campaign_id, person_id=npc_id, art="ERFAHRUNG_VERGEBEN",
        alt=str(alt_erfahrung), neu=str(neue_erfahrung), kosten_oder_menge=neue_erfahrung - alt_erfahrung,
        sl_notiz=f"Catch-up zu {referenz.get('name', '')} ({prozent}%)",
    )

    charakterkontext = (
        f"Name: {npc.get('name', '')}\nKonzept: {npc.get('konzept', '')}\nWeg: {npc.get('weg', 'KEINER')}"
    )
    steigerungen = await _verteile_ep_automatisch(campaign_id, npc_id, ruleset, charakterkontext)

    if budget_geld > 0:
        npc_aktuell = await get_node("Person", PERSON_FIELDS, campaign_id, npc_id)
        vorhandenes_kapital = int((npc_aktuell or {}).get("kapital") or 0)
        await update_node("Person", PERSON_FIELDS, campaign_id, npc_id, {"kapital": vorhandenes_kapital + budget_geld})
        gekauft = await _kaufe_und_rueste_aus(campaign_id, npc_id, vorhandenes_kapital + budget_geld, charakterkontext)
    else:
        gekauft = []

    return CatchupErgebnis(
        referenzName=referenz.get("name", ""),
        budgetEp=budget_ep,
        budgetGeld=budget_geld,
        erfahrungGesamt=neue_erfahrung + kampagnen_ep + npc_extra_ep,
        gekauft=gekauft,
        steigerungen=steigerungen,
    )
