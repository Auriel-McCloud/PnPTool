"""Mentor-EP nach der Beschreibung ausgeben.

20 je Mentor-Punkt, Plan von der KI, Executor spart statt Resteverwertung.
Scheitert der Plan, bleiben die Punkte als extraEP liegen — der Kontakt
selbst ist dann schon angelegt.
"""

import logging

from app.entities.repository import PERSON_FIELDS, update_node
from app.ki.client import generiere_json
from app.traits.autosteigerung import WILLENSKRAFT, fuehre_plan_aus, mentor_ep
from app.traits.repository import get_ratings_for_entity, set_rating

logger = logging.getLogger(__name__)

_PLAN_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "plan": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["plan"],
}


async def ep_ausgeben(campaign_id: str, npc_id: str, rating: int, wunsch: str) -> None:
    """Gibt 20×Rating EP auf dem frischen Mentor aus. Wirft nicht."""
    budget = mentor_ep(rating)
    if budget <= 0:
        return
    try:
        ratings = await get_ratings_for_entity(campaign_id, npc_id)
        werte = {r["name"]: int(r["rating"] or 0) for r in ratings}
        kategorien = {r["name"]: r["category"] for r in ratings}
        maxima = {r["name"]: int(r["max"]) for r in ratings if r.get("max") is not None}
        erlaubt = [name for name, wert in werte.items() if wert > 0]
        if WILLENSKRAFT not in erlaubt:
            erlaubt.append(WILLENSKRAFT)
        roh = await generiere_json(
            (
                f"Mentor-Steigerungsplan, {budget} EP, Wunsch: {wunsch}. "
                "Geordnete Liste von Namen. Jeder Eintrag ist genau +1 auf einen "
                "schon vorhandenen Wert. Keine neuen Fertigkeiten. Nur diese Namen: "
                + ", ".join(erlaubt)
            ),
            "Du planst nur Steigerungen. Kein Fließtext.",
            _PLAN_SCHEMA,
            campaign_id=campaign_id,
        )
        plan = [str(name) for name in (roh.get("plan") or []) if str(name) in erlaubt or str(name) == WILLENSKRAFT]
        ergebnis = fuehre_plan_aus(werte, kategorien, plan, budget, maxima)
        by_name = {r["name"]: r for r in ratings}
        for name, neu in ergebnis.werte.items():
            if neu == werte.get(name, 0) or name not in by_name:
                continue
            await set_rating(campaign_id, npc_id, by_name[name]["traitDefId"], neu, None)
        if ergebnis.restbudget:
            await update_node(
                "Person", PERSON_FIELDS, campaign_id, npc_id, {"extraEP": ergebnis.restbudget}
            )
    except Exception:
        logger.exception("Mentor-EP konnte nicht ausgegeben werden (npc=%s)", npc_id)
        try:
            await update_node("Person", PERSON_FIELDS, campaign_id, npc_id, {"extraEP": budget})
        except Exception:
            logger.exception("Mentor-EP auch nicht als extraEP gespeichert (npc=%s)", npc_id)
