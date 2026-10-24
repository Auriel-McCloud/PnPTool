"""KI verteilt Catch-up-EP eines NPCs automatisch auf Werte (24.10.2026).

Gegenstück zu `app/haendler/ki_einkauf.py` (dort kauft die KI Ausrüstung von
einem Budget) — hier verteilt sie ein EP-Budget auf Attribute/Fertigkeiten,
nach demselben Grundsatz: die KI wählt nur aus der tatsächlich verfügbaren
Preisliste (keine erfundenen traitDefIds), der Server rechnet verbindlich ab
und validiert jeden Schritt neu (Preise hängen vom jeweils aktuellen Wert ab,
siehe app/traits/erfahrung.py::kosten).

Anders als beim Einkauf soll das EP-Budget eines Catch-up-NPCs **möglichst
vollständig** verbraucht werden — ein NPC mit übrig gelassenen EP wirkt nur
halb hochgezogen. "Realistischer Rest" wie beim Einkauf passt hier nicht.
"""

from pydantic import BaseModel

from app.ki.client import generiere_json

_SYSTEM = (
    "Du gleichst einen NPC in einem deutschen Cyberpunk-Pen-and-Paper "
    "(NeotopiA) an das Niveau der Spielergruppe an (Catch-up). Du bekommst "
    "eine Liste steigerbarer Werte mit ihrem jeweils nächsten Preis sowie "
    "ein EP-Budget. Wähle NUR aus der gegebenen Liste (per traitDefId, oder "
    "dem Sonderwert \"WILLENSKRAFT\") — erfinde nichts. Nenne jeden "
    "gewünschten Punkt als EIGENEN Listeneintrag in Kaufreihenfolge (dieselbe "
    "traitDefId darf mehrfach vorkommen, wenn mehrere Punkte eines Werts "
    "gewünscht sind — der Preis steigt mit jedem Punkt, das rechnet der "
    "Server nach). Verteile sinnvoll passend zu Konzept und Weg des "
    "Charakters (ein Kampf-NPC braucht Kampfwerte, kein wahlloses Verteilen). "
    "Nutze das Budget so vollständig wie möglich aus, ohne es zu überziehen — "
    "anders als beim Einkaufen soll hier nichts übrig bleiben."
)

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "steigerungen": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "traitDefId": {"type": "STRING"},
                },
                "required": ["traitDefId"],
            },
        },
    },
    "required": ["steigerungen"],
}


class VerteilungsVorschlag(BaseModel):
    traitDefIds: list[str] = []


async def vorschlag(
    campaign_id: str, charakterkontext: str, preisliste: list[dict], willenskraft: dict, budget: int
) -> VerteilungsVorschlag:
    """Fragt die KI nach einer priorisierten Kaufliste für `budget` EP.

    Gibt bei KI-Fehlern eine leere Liste zurück (No-Op) — derselbe Grundsatz
    wie bei `ki_einkauf.einkaufen`: ein NPC bleibt dann halt unverändert,
    bricht aber nicht den ganzen Catch-up ab (die EP/das Geld sind da bereits
    verbucht).
    """
    if budget <= 0 or not preisliste:
        return VerteilungsVorschlag()

    zeilen = "\n".join(
        f"- ({w['traitDefId']}) {w['name']} [{w['category']}, aktuell {w['aktuell']}, "
        f"nächster Punkt {w['kosten']} EP]"
        for w in preisliste
    )
    zeilen += f"\n- (WILLENSKRAFT) Willenskraft [aktuell {willenskraft['aktuell']}, nächster Punkt {willenskraft['kosten']} EP]"

    prompt = f"Charakter:\n{charakterkontext}\n\nEP-Budget: {budget}\n\nSteigerbare Werte:\n{zeilen}"
    try:
        ergebnis = await generiere_json(prompt, _SYSTEM, _SCHEMA, campaign_id=campaign_id)
    except Exception:
        return VerteilungsVorschlag()

    ids = [
        (e.get("traitDefId") or "").strip()
        for e in (ergebnis.get("steigerungen") or [])
        if (e.get("traitDefId") or "").strip()
    ]
    return VerteilungsVorschlag(traitDefIds=ids)
