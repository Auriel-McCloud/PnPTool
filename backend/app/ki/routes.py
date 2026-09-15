"""KI-Endpunkte: Gemini generiert Inhalte direkt in die Ideenschmiede.

Zwei Typen, beide landen als Entwurf (`istEntwurf=true`) in der Schmiede:

- ``story``     — ein Story-Part. Gemini schreibt Titel + Fließtext, daraus
  wird eine Wiki-Seite (Geschichte).
- ``charakter`` — eine Charakter-Vorlage. Gemini erfindet Name + Beschreibung,
  daraus wird ein NPC.

Die Prompts und Ausgabe-Schemata stehen bewusst hier und nicht im Frontend:
damit hat nur eine Stelle Kontrolle darüber, was Gemini als Auftrag bekommt,
und das Frontend reicht nur den freien Wunsch des Spielleiters durch.
"""

import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import require_campaign_gm
from app.entities.repository import PERSON_FIELDS, create_node
from app.entities.schemas import PersonCreate
from app.ki.gemini import GeminiFehler, generiere_json
from app.wiki.repository import create_seite

router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/ki",
    tags=["ki"],
    dependencies=[Depends(require_campaign_gm)],
)

_SYSTEM = (
    "Du bist ein Spielleiter-Assistent für das Cyberpunk-Pen-and-Paper-Rollenspiel "
    "NeotopiA (WoD-artige Attribute, Shadowrun-Cyberware, Mage-Sphären). "
    "Du schreibst dicht, stimmig und auf Deutsch."
)

_STORY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "titel": {"type": "STRING"},
        "inhalt": {"type": "STRING"},
    },
    "required": ["titel", "inhalt"],
}

_CHARAKTER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "beschreibung": {"type": "STRING"},
    },
    "required": ["name", "beschreibung"],
}


class KiIdeeInput(BaseModel):
    typ: Literal["story", "charakter"]
    prompt: str


def _text_zu_dokument(text: str) -> str:
    """Fließtext in ein TipTap-Dokument umwandeln (Absätze = Paragraph-Nodes).

    Gemini liefert Fließtext, die Wiki-Seite speichert aber ein TipTap-JSON.
    Eine leere Zeile trennt einen neuen Absatz; ohne Absätze bleibt der ganze
    Text ein einziger Absatz.
    """
    absaetze = [a.strip() for a in text.split("\n\n") if a.strip()]
    if not absaetze and text.strip():
        absaetze = [text.strip()]
    content = [
        {"type": "paragraph", "content": [{"type": "text", "text": a}]}
        for a in absaetze
    ]
    return json.dumps({"type": "doc", "content": content}, ensure_ascii=False)


@router.post("/idee")
async def ki_idee(campaign_id: str, body: KiIdeeInput):
    """Generiert eine Idee und legt sie als Entwurf in der Schmiede an."""
    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Der Wunsch darf nicht leer sein.")

    try:
        if body.typ == "story":
            ergebnis = await generiere_json(prompt, _SYSTEM, _STORY_SCHEMA)
            titel = (ergebnis.get("titel") or "").strip() or "Unbenannter Story-Part"
            inhalt = (ergebnis.get("inhalt") or "").strip()
            seite = await create_seite(
                campaign_id,
                titel=titel,
                inhalt=_text_zu_dokument(inhalt),
                ist_entwurf=True,
                sichtbarkeit="GM",
                sichtbar_fuer=[],
            )
            if seite is None:
                raise HTTPException(status_code=404, detail="Kampagne nicht gefunden")
            return {"typ": "story", "id": seite["id"], "name": titel}

        # charakter
        ergebnis = await generiere_json(prompt, _SYSTEM, _CHARAKTER_SCHEMA)
        name = (ergebnis.get("name") or "").strip() or "Unbenannter Charakter"
        beschreibung = (ergebnis.get("beschreibung") or "").strip()
        person = await create_node(
            "Person",
            PERSON_FIELDS,
            campaign_id,
            PersonCreate(
                name=name,
                personType="NPC",
                description=beschreibung,
                istEntwurf=True,
                sichtbarkeit="GM",
            ).model_dump(),
        )
        return {"typ": "charakter", "id": person["id"], "name": name}

    except GeminiFehler as e:
        # 502 statt 500: der Fehler liegt an der externen KI, nicht an uns.
        raise HTTPException(status_code=502, detail=str(e))
