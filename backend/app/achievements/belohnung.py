"""Belohnung einlösen — EP oder Hintergrund, fest am Achievement hinterlegt.

Siehe docs/wiki/entities/achievements.md, Abschnitt "Mechanische Belohnung":
Hintergrund lässt sich nach der Charaktererstellung sonst GAR NICHT mehr
steigern (LevelUp.tsx schließt die Kategorie bewusst aus) — eine
Achievement-Verleihung ist der einzige Weg dafür.
"""

from app.entities.repository import PERSON_FIELDS, get_node, update_node
from app.ereignisprotokoll import hooks
from app.traits import repository as traits_repository
from app.traits.erstellung import HINTERGRUND_MAX


async def _traitdef_id_fuer(campaign_id: str, ruleset: str, name: str) -> str | None:
    katalog = await traits_repository.list_catalog(ruleset)
    for eintrag in katalog:
        if eintrag["category"] == "Hintergrund" and eintrag["name"] == name:
            return eintrag["id"]
    return None


async def einloesen(
    campaign_id: str, ruleset: str, *, person_id: str, achievement: dict,
) -> None:
    """Schreibt die Belohnung eines Achievements auf die Person und loggt
    die Charakterentwicklung — ruft nichts auf, wenn belohnungsArt KEINE ist.
    """
    art = achievement.get("belohnungsArt") or "KEINE"
    menge = int(achievement.get("belohnungsMenge") or 0)
    if art == "KEINE" or menge <= 0:
        return

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        return

    if art == "EP":
        alt = int(person.get("erfahrung") or 0)
        neu = alt + menge
        await update_node("Person", PERSON_FIELDS, campaign_id, person_id, {"erfahrung": neu})
        await hooks.charakterentwicklung(
            campaign_id, person_id=person_id, art="ERFAHRUNG_VERGEBEN",
            alt=str(alt), neu=str(neu), kosten_oder_menge=menge,
            sl_notiz=f"Achievement: {achievement.get('name', '')}",
        )
        return

    if art == "HINTERGRUND":
        name = achievement.get("belohnungsHintergrund")
        if not name:
            return
        trait_def_id = await _traitdef_id_fuer(campaign_id, ruleset, name)
        if trait_def_id is None:
            return
        werte = await traits_repository.get_ratings_for_entity(campaign_id, person_id)
        aktuell = next((w["rating"] for w in werte if w["traitDefId"] == trait_def_id), 0)
        neu = min(HINTERGRUND_MAX, int(aktuell) + menge)
        await traits_repository.set_rating(campaign_id, person_id, trait_def_id, neu, None)
        await hooks.charakterentwicklung(
            campaign_id, person_id=person_id, art="STEIGERUNG",
            trait_def_id=trait_def_id, trait_name=name,
            alt=str(aktuell), neu=str(neu), kosten_oder_menge=0,
            sl_notiz=f"Achievement: {achievement.get('name', '')}",
        )
