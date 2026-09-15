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
from app.campaigns.repository import get_campaign
from app.entities.repository import PERSON_FIELDS, create_node
from app.entities.schemas import PersonCreate
from app.ki.gemini import GeminiFehler, generiere_json
from app.ki.kontext import sammle_kontext
from app.traits.repository import list_catalog, set_rating
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
        # Kopfzeile des Papierblatts — reiner Text, keine Regelmechanik.
        "konzept": {"type": "STRING"},
        "alter": {"type": "STRING"},
        "ambition": {"type": "STRING"},
        "verlangen": {"type": "STRING"},
        "ziel": {"type": "STRING"},
        "rasse": {"type": "STRING"},
        "weg": {"type": "STRING", "enum": ["KEINER", "MAGIER", "NEUROWEAVER"]},
        "kapital": {"type": "INTEGER"},
        "schulden": {"type": "INTEGER"},
        # Werte auf dem Charakterbogen — nur Traits aus dem vorgegebenen Katalog.
        "traits": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "rating": {"type": "INTEGER"},
                },
                "required": ["name", "rating"],
            },
        },
    },
    "required": ["name", "beschreibung", "konzept", "rasse", "weg", "traits"],
}

# Erklärt die Kopfzeilen-Begriffe, damit Gemini nicht rät, was „Ambition"
# von „Verlangen" unterscheidet.
_CHARAKTER_SYSTEM = (
    _SYSTEM
    + " Erschaffe stimmige NPCs. Die Kopfzeile: konzept (kurze Rollenbeschreibung), "
    "alter, ambition (was der Charakter langfristig erreichen will), verlangen "
    "(sein innerer Antrieb/Sucht), ziel (das konkrete nächste Vorhaben). "
    "rasse ist eine NeotopiA-Rasse (Mensch, Ork, Elf, Zwerg, Troll). "
    "weg: KEINER, MAGIER oder NEUROWEAVER — nur MAGIER, wenn der Charakter Magie "
    "wirkt, nur NEUROWEAVER, wenn er NeuroWeaving nutzt, sonst KEINER. "
    "kapital und schulden sind Zahlen (Nuyen)."
)


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


def _mit_kontext(prompt: str, kontext: str) -> str:
    """Hängt die freigegebene Kampagnenwelt an den Wunsch, wenn es eine gibt."""
    if not kontext:
        return prompt
    return (
        f"{prompt}\n\n"
        f"Freigegebene Welt der Kampagne — füge das Neue darin ein und knüpfe es "
        f"an passende bestehende Personen, Orte oder Fraktionen an:\n{kontext}"
    )


def _als_int(wert, standard: int = 0) -> int:
    try:
        return int(wert)
    except (TypeError, ValueError):
        return standard


async def _katalog_zu_text(ruleset: str) -> str:
    """Trait-Katalog als kompakte, gruppierte Liste für den Prompt."""
    katalog = await list_catalog(ruleset)
    gruppen: dict[str, list[str]] = {}
    for t in katalog:
        gruppen.setdefault(t["category"], []).append(f"{t['name']} (max {t['defaultMax']})")
    return "\n".join(f"{kategorie}: {', '.join(namen)}" for kategorie, namen in gruppen.items())


async def _setze_traits(campaign_id: str, person_id: str, ruleset: str, wahl: list[dict]) -> int:
    """Übernimmt Gemini's Trait-Wahl (name→rating) auf den Charakterbogen.

    Nur Namen, die es im Katalog gibt, werden gesetzt; Werte werden auf
    [0, defaultMax] geklemmt. Gibt die Anzahl gesetzter Traits zurück.
    """
    katalog = await list_catalog(ruleset)
    name_zu_def = {t["name"]: t for t in katalog}
    gesetzt = 0
    for eintrag in wahl:
        name = (eintrag.get("name") or "").strip()
        definier = name_zu_def.get(name)
        if definier is None:
            continue
        rating = max(0, min(_als_int(eintrag.get("rating")), definier["defaultMax"]))
        await set_rating(campaign_id, person_id, definier["id"], rating, None)
        gesetzt += 1
    return gesetzt


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
        kontext = await sammle_kontext(campaign_id)
        campaign = await get_campaign(campaign_id)
        ruleset = campaign["ruleset"] if campaign else "neotopia"
        katalog_text = await _katalog_zu_text(ruleset)

        prompt_komplett = _mit_kontext(prompt, kontext)
        prompt_komplett += (
            "\n\nTrait-Katalog für den Charakterbogen (Name — Kategorie, Max-Wert):\n"
            f"{katalog_text}\n"
            "Setze die 9 Attribute sinnvoll und nur die Fertigkeiten/Hintergründe, "
            "die zum Charakter passen (rating > 0). Hexkraft und Sphären nur bei "
            "Weg MAGIER, NeuroWeaving nur bei NEUROWEAVER."
        )

        ergebnis = await generiere_json(prompt_komplett, _CHARAKTER_SYSTEM, _CHARAKTER_SCHEMA)
        name = (ergebnis.get("name") or "").strip() or "Unbenannter Charakter"
        beschreibung = (ergebnis.get("beschreibung") or "").strip()
        weg = ergebnis.get("weg") or "KEINER"
        if weg not in ("KEINER", "MAGIER", "NEUROWEAVER"):
            weg = "KEINER"
        person = await create_node(
            "Person",
            PERSON_FIELDS,
            campaign_id,
            PersonCreate(
                name=name,
                personType="NPC",
                description=beschreibung,
                konzept=(ergebnis.get("konzept") or "").strip(),
                alter=(ergebnis.get("alter") or "").strip(),
                ambition=(ergebnis.get("ambition") or "").strip(),
                verlangen=(ergebnis.get("verlangen") or "").strip(),
                ziel=(ergebnis.get("ziel") or "").strip(),
                rasse=(ergebnis.get("rasse") or "").strip(),
                weg=weg,
                kapital=_als_int(ergebnis.get("kapital")),
                schulden=_als_int(ergebnis.get("schulden")),
                istEntwurf=True,
                sichtbarkeit="GM",
            ).model_dump(),
        )
        anzahl_traits = await _setze_traits(campaign_id, person["id"], ruleset, ergebnis.get("traits") or [])
        return {"typ": "charakter", "id": person["id"], "name": name, "traits": anzahl_traits}

    except GeminiFehler as e:
        # 502 statt 500: der Fehler liegt an der externen KI, nicht an uns.
        raise HTTPException(status_code=502, detail=str(e))
