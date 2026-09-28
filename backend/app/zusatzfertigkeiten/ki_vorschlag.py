"""KI-Vorschläge für neue Zusatzfertigkeiten (Marks Wunsch, 28.09.2026:
"Mit einem KI Generierungs Button für Vorschläge").

Zweistufig wie haendler/ki_vorschlag.py: `vorschlaege()` liefert Kandidaten
zur Ansicht (nichts wird gespeichert), `uebernehmen()` legt EINEN
bestätigten Vorschlag im Katalog an — kein Sammel-Übernehmen, die SL prüft
jeden neuen Eintrag einzeln, bevor er für Spieler wählbar wird.

Die KI bekommt die bereits vorhandenen Zusatzfertigkeiten dieser Kampagne
mitgeteilt (keine Duplikate) sowie den NeotopiA-Cyberpunk-Kontext, damit Ton
und Umfang zu `docs/reference/Master/Optionale_Fertigkeiten.md` passen:
Kurzbeschreibung ein Satz, Detailbeschreibung ein Absatz.
"""

from pydantic import BaseModel

from app.ki.client import generiere_json
from app.zusatzfertigkeiten import repository

_SYSTEM = (
    "Du schlägst optionale Zusatzfertigkeiten für Charaktere in der Welt von "
    "NeotopiA vor (deutsches Cyberpunk-Pen-and-Paper-Rollenspiel). "
    "Zusatzfertigkeiten sind NICHT auf dem Standard-Charakterblatt — sie "
    "stehen nur zur Verfügung, wenn ein Charakter sie explizit lernt. Sie "
    "haben KEINE eigene Mechanik oder Boni, nur Name und Beschreibung, wie "
    "eine normale Fertigkeit. Du bekommst eine Liste bereits existierender "
    "Zusatzfertigkeiten dieser Kampagne — erfinde KEINE Duplikate oder "
    "Sinngleichen davon. Kurzbeschreibung: EIN prägnanter Satz. "
    "Detailbeschreibung: EIN Absatz (3-5 Sätze) im Ton eines Regelwerks — "
    "was die Fertigkeit umfasst, wer sie typischerweise trägt, wofür sie im "
    "Spiel nützlich ist. Setting: Konzerne, Straßenkultur, Magie ist seit "
    "rund hundert Jahren wieder öffentlich, Cyberware, Matrix/Netzwelt."
)

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "vorschlaege": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "kurzbeschreibung": {"type": "STRING"},
                    "detailbeschreibung": {"type": "STRING"},
                },
                "required": ["name", "kurzbeschreibung", "detailbeschreibung"],
            },
        },
    },
    "required": ["vorschlaege"],
}


class ZusatzfertigkeitVorschlag(BaseModel):
    name: str
    kurzbeschreibung: str = ""
    detailbeschreibung: str = ""


class VorschlaegeAntwort(BaseModel):
    vorschlaege: list[ZusatzfertigkeitVorschlag] = []


async def vorschlaege(campaign_id: str, anzahl: int = 5) -> VorschlaegeAntwort:
    """Lässt die KI neue Zusatzfertigkeiten für diese Kampagne vorschlagen."""
    bestehende = await repository.liste(campaign_id)
    liste_text = (
        "\n".join(f"- {z['name']}: {z['kurzbeschreibung']}" for z in bestehende)
        or "(noch keine Zusatzfertigkeiten in dieser Kampagne)"
    )
    prompt = (
        f"Bereits existierende Zusatzfertigkeiten dieser Kampagne:\n{liste_text}\n\n"
        f"Schlage {anzahl} NEUE, davon verschiedene Zusatzfertigkeiten vor."
    )
    ergebnis = await generiere_json(prompt, _SYSTEM, _SCHEMA)

    bekannte_namen = {z["name"].strip().lower() for z in bestehende}
    vorschlags_liste: list[ZusatzfertigkeitVorschlag] = []
    gesehen: set[str] = set()
    for eintrag in (ergebnis.get("vorschlaege") or [])[:anzahl]:
        name = (eintrag.get("name") or "").strip()
        schluessel = name.lower()
        if not name or schluessel in bekannte_namen or schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        vorschlags_liste.append(
            ZusatzfertigkeitVorschlag(
                name=name,
                kurzbeschreibung=(eintrag.get("kurzbeschreibung") or "").strip(),
                detailbeschreibung=(eintrag.get("detailbeschreibung") or "").strip(),
            )
        )
    return VorschlaegeAntwort(vorschlaege=vorschlags_liste)


async def uebernehmen(campaign_id: str, vorschlag: ZusatzfertigkeitVorschlag) -> dict:
    """Übernimmt EINEN bestätigten (ggf. vom SL editierten) Vorschlag in den Katalog."""
    return await repository.anlegen(
        campaign_id,
        {
            "name": vorschlag.name,
            "kurzbeschreibung": vorschlag.kurzbeschreibung,
            "detailbeschreibung": vorschlag.detailbeschreibung,
        },
    )
