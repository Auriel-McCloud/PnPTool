"""Schulden/Mentor/Kontakte nach der Charaktererstellung: bestehende
System-NPCs wiederverwenden oder neu erzeugen — dieselbe Grund-Logik für
alle drei System-Hintergründe (siehe seed.py::SYSTEM_SCHLUESSEL).

Schulden/Kredithai bleibt bewusst ein reiner Stub ohne sofortige KI-Füllung
(Erstellung soll nicht auf einen LLM-Call warten und nicht extra kosten,
wenn schon ein Hai da ist). Mentor UND Kontakte nutzen seit 11.10.2026
(Marks Vorgabe) denselben vollen KI-Flow wie die Ideenschmiede-
Charaktererstellung (`ki/routes.py::_idee_anlegen`, inkl. Tutorial-Shop-
Einkauf) — Mentor sofort, Kontakte bewusst NICHT: die Hintergrund-Punkte
legen nur leere Platzhalter an, der Spieler befüllt jeden erst per eigenem
Wunsch, sobald er ihn im Spiel braucht (siehe kontakte/routes.py::
kontakt_generieren).
"""

from app.entities.repository import PERSON_FIELDS, create_node, list_nodes, update_node
from app.entities.schemas import PersonCreate
from app.hintergruende import repository
from app.hintergruende.kredithai import (
    bestehenden_kredithai,
    kredithai_rasse,
    schulden_beschreibung,
    schulden_punkte,
)
from app.hintergruende.mentor import bestehenden_mentor
from app.ki.routes import _idee_anlegen as ki_charakter_generieren
from app.kontakte import repository as kontakte_repository
from app.rassen import repository as rassen_repository


async def nach_erstellung(campaign_id: str, person_id: str, kredit_freebees: int) -> dict | None:
    """No-Op ohne Kredit. Sonst HAT_KREDITHAI + Schuldet + KENNT (Chat zu)."""
    rating = schulden_punkte(kredit_freebees)
    if rating <= 0:
        return None

    bestehend = await repository.hole_kredithai(campaign_id, person_id)
    hai_id = bestehend["haiId"] if bestehend else None
    if not hai_id:
        personen = await list_nodes("Person", PERSON_FIELDS, campaign_id)
        npcs = [n for n in personen if n.get("personType") == "NPC"]
        hai = bestehenden_kredithai(npcs)
        if hai:
            hai_id = hai["id"]
        else:
            rassen = await rassen_repository.liste_fuer_kampagne(campaign_id)
            stub = await create_node(
                "Person",
                PERSON_FIELDS,
                campaign_id,
                PersonCreate(
                    name="Kredithai",
                    personType="NPC",
                    description="Zwielichtiger Geldverleiher. Noch nicht ausgearbeitet.",
                    istKredithai=True,
                    istEntwurf=True,
                    sichtbarkeit="GM",
                    rasse=kredithai_rasse(rassen),
                    erstellungAbgeschlossen=True,
                ).model_dump(),
            )
            hai_id = stub["id"]

    await repository.setze_kredithai(campaign_id, person_id, hai_id, rating)
    await repository.setze_schuldet_verbindung(
        campaign_id, person_id, hai_id, schulden_beschreibung(kredit_freebees)
    )
    await kontakte_repository.anlegen(
        campaign_id, person_id, hai_id, stufe="GESEHEN", chat_offen=False
    )
    return {"haiId": hai_id, "rating": rating}


async def mentor_nach_erstellung(
    campaign_id: str, person_id: str, person_name: str, mentor_rating: int
) -> dict | None:
    """No-Op ohne Mentor-Punkte. Sonst HAT_MENTOR + KENNT (Chat zu, wie Hai).

    Ein bestehender markierter Mentor wird wiederverwendet (z.B. mehrere PCs
    mit demselben Lehrer) — sonst erzeugt die KI frisch einen vollen,
    spielbereiten NPC (Marks Vorgabe 11.10.2026: derselbe Flow wie
    Ideenschmiede-Charakter, inkl. Tutorial-Shop-Einkauf).
    """
    rating = max(0, min(int(mentor_rating), 5))
    if rating <= 0:
        return None

    bestehend = await repository.hole_mentor(campaign_id, person_id)
    mentor_id = bestehend["mentorId"] if bestehend else None
    if not mentor_id:
        personen = await list_nodes("Person", PERSON_FIELDS, campaign_id)
        npcs = [n for n in personen if n.get("personType") == "NPC"]
        gefunden = bestehenden_mentor(npcs)
        if gefunden:
            mentor_id = gefunden["id"]
        else:
            prompt = (
                f"Erzeuge einen Mentor-NPC für den Charakter {person_name}: "
                "jemand, der mehr weiß und diesem Charakter bisweilen etwas "
                "davon abgibt — passend zu dessen Konzept, Weg und Fertigkeiten."
            )
            erzeugt = await ki_charakter_generieren(campaign_id, "charakter", prompt)
            mentor_id = erzeugt["id"]
            await update_node("Person", PERSON_FIELDS, campaign_id, mentor_id, {"istMentor": True})

    await repository.setze_mentor(campaign_id, person_id, mentor_id, rating)
    await kontakte_repository.anlegen(campaign_id, person_id, mentor_id, stufe="GESEHEN", chat_offen=False)
    return {"mentorId": mentor_id, "rating": rating}


async def kontakte_nach_erstellung(campaign_id: str, person_id: str, kontakte_rating: int) -> list[str]:
    """No-Op ohne Kontakte-Punkte. Sonst N Blanko-Platzhalter (noch keine KI).

    Bewusst KEIN sofortiger KI-Call (Marks Entscheidung 11.10.2026): der
    Spieler tippt später selbst auf einen leeren Platz und beschreibt, wen
    er braucht — siehe kontakte/routes.py::kontakt_generieren. Idempotent
    bei erneuter Einreichung: zählt bestehende HAT_KONTAKTSLOT-Kanten und
    legt nur die fehlenden nach, nie Duplikate, nie Löschen bei sinkendem
    Rating (Marks Vorgabe: reversibel, kein Datenverlust).
    """
    rating = max(0, min(int(kontakte_rating), 5))
    if rating <= 0:
        return []

    bestehende = await repository.kontaktslots_der_person(campaign_id, person_id)
    fehlend = rating - len(bestehende)
    neue_ids: list[str] = []
    for _ in range(max(0, fehlend)):
        stub = await create_node(
            "Person",
            PERSON_FIELDS,
            campaign_id,
            PersonCreate(
                name="Unbekannter Kontakt",
                personType="NPC",
                description="Noch nicht ausgearbeitet — wird befüllt, sobald der Spieler ihn braucht.",
                istBlankoKontakt=True,
                sichtbarkeit="GM",
                erstellungAbgeschlossen=True,
            ).model_dump(),
        )
        await repository.fuege_kontaktslot_hinzu(campaign_id, person_id, stub["id"])
        await kontakte_repository.anlegen(campaign_id, person_id, stub["id"], stufe="GESEHEN", chat_offen=False)
        neue_ids.append(stub["id"])
    return neue_ids
