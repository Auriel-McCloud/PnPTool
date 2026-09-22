"""Auto-Verknüpfung: KI erkennt Erwähnungen von Personen/Orten/Events/
Fraktionen im Wiki-Text und verknüpft sie automatisch als echte Graphkanten
(CLAUDE.md Punkt 3, präzisiert 20.09.2026).

Zwei Schritte, getrennt wie bei der Rechtschreib-/Logikprüfung
(``wiki_pruefung.py``):

- ``vorschlaege`` — liest eine Seite, lässt die KI Erwähnungen erkennen und
  gleicht sie in Python (NICHT durch die KI) gegen die freigegebenen
  Entitäten ab. Nichts wird gespeichert.
- ``anwenden`` — fügt für EINEN bestätigten Vorschlag einen echten
  ``entitaetsverweis``-Chip an der zitierten Textstelle ein. Existiert die
  erkannte Entität noch nicht, wird zuerst ein Entwurf in der Ideenschmiede
  angelegt (istEntwurf=true, SL-geheim) und der Chip zeigt auf diesen neuen
  Entwurf. Das Speichern der Seite löst danach ganz normal
  ``wiki/repository.py::_verweise_schreiben`` aus — die echte
  VERWEIST_AUF-Kante entsteht also über denselben Weg wie ein von Hand über
  den „⧉ Verknüpfen"-Knopf eingefügter Verweis.

Bewusst PRO VORSCHLAG einzeln anzuwenden statt eines Sammel-Übernehmens:
neue Entitäten landen als Entwurf zur Prüfung durch den SL, kein
automatischer Autocommit in die Kampagne (Marks Vorgabe, 20.09.2026).
"""

import json

from pydantic import BaseModel

from app.entities.repository import (
    EVENT_FIELDS,
    FRAKTION_FIELDS,
    ORT_FIELDS,
    PERSON_FIELDS,
    create_node,
)
from app.entities.schemas import EventCreate, FraktionCreate, OrtCreate, PersonCreate
from app.ki.client import generiere_json
from app.ki.kontext import sammle_entitaeten, tiptap_zu_text
from app.wiki import repository
from app.wiki.logic import VERWEIS_TYP

_TYPEN = ("Person", "Ort", "Event", "Fraktion")

_SYSTEM = (
    "Du hilfst, einen Wiki-Text eines deutschen Cyberpunk-Pen-and-Paper-"
    "Rollenspiels (NeotopiA) mit den Personen/Orten/Events/Fraktionen der "
    "Kampagne zu verknüpfen. Du bekommst eine Liste aller bereits bekannten "
    "Entitäten und den zu durchsuchenden Text. Finde jede Textstelle, die "
    "eine konkrete, benannte Person, einen konkreten Ort, ein konkretes "
    "Ereignis oder eine konkrete Fraktion/Organisation erwähnt — auch wenn "
    "sie NICHT in der bekannten Liste steht (dann ist es eine neue "
    "Erwähnung). Ignoriere allgemeine Begriffe ohne Eigennamen (\"ein "
    "Straßenhändler\", \"die Stadt\") — nur konkret benannte Dinge zählen. "
    "Für jeden Treffer: 'zitat' ist die exakte, zusammenhängende Textstelle "
    "wie sie WÖRTLICH im Text steht (kurz — nur der Name, nicht der ganze "
    "Satz), 'typ' ist Person/Ort/Event/Fraktion, 'name' ist die kanonische "
    "Namensform — steht die Entität in der bekannten Liste, MUSS 'name' "
    "exakt (Zeichen für Zeichen) dem Listennamen entsprechen, sonst deine "
    "beste Einschätzung des vollen Namens. Erwähne jede Entität nur EINMAL, "
    "auch wenn sie mehrfach im Text vorkommt (nimm die erste Fundstelle)."
)

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "vorschlaege": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "zitat": {"type": "STRING"},
                    "typ": {"type": "STRING", "enum": list(_TYPEN)},
                    "name": {"type": "STRING"},
                },
                "required": ["zitat", "typ", "name"],
            },
        },
    },
    "required": ["vorschlaege"],
}


class VerknuepfungsVorschlag(BaseModel):
    zitat: str
    typ: str
    name: str
    # Gesetzt, wenn "name" (normalisiert) zu einer freigegebenen Entität
    # dieses Typs passt — dann verknüpft "anwenden" direkt dorthin. Sonst
    # None: "anwenden" legt zuerst einen Entwurf mit diesem Namen an.
    zielId: str | None = None


def _normalisiert(text: str) -> str:
    return " ".join(text.strip().casefold().split())


async def vorschlaege(campaign_id: str, seiten_id: str) -> list[VerknuepfungsVorschlag]:
    """Lässt die KI Erwähnungen erkennen, gleicht sie gegen den Graphen ab.

    Der Namensabgleich (Vorschlag → bestehende ID) passiert bewusst hier in
    Python, nicht durch die KI: die KI kennt keine IDs, nur Namen — ein
    Tippfehler oder eine leicht andere Schreibweise der KI dürfte niemals
    eine falsche ID erfinden.
    """
    seite = await repository.get_seite(campaign_id, seiten_id)
    if seite is None:
        return []
    text = tiptap_zu_text(seite["inhalt"])
    if not text.strip():
        return []

    entitaeten = await sammle_entitaeten(campaign_id)
    liste_text = "\n".join(f"- {e['kind']}: {e['name']}" for e in entitaeten if e["name"]) or "(noch keine)"

    prompt = (
        f"Bekannte Entitäten dieser Kampagne:\n{liste_text}\n\n"
        f"Zu durchsuchender Text:\n{text}"
    )
    ergebnis = await generiere_json(prompt, _SYSTEM, _SCHEMA)

    # Schneller Nachschlage-Index: (typ, normalisierter Name) -> id.
    index = {(e["kind"], _normalisiert(e["name"])): e["id"] for e in entitaeten if e["name"]}

    gefunden: list[VerknuepfungsVorschlag] = []
    gesehen: set[str] = set()
    for eintrag in ergebnis.get("vorschlaege") or []:
        zitat = (eintrag.get("zitat") or "").strip()
        typ = eintrag.get("typ") or ""
        name = (eintrag.get("name") or "").strip()
        if not zitat or typ not in _TYPEN or not name or zitat not in text:
            # Ohne echte Fundstelle im Text liesse sich der Vorschlag nicht
            # automatisch einfügen (wie bei der Wiki-Prüfung) — verwerfen.
            continue
        if zitat in gesehen:
            continue
        gesehen.add(zitat)
        ziel_id = index.get((typ, _normalisiert(name)))
        gefunden.append(VerknuepfungsVorschlag(zitat=zitat, typ=typ, name=name, zielId=ziel_id))

    return gefunden


def _verweis_einfuegen(knoten, zitat: str, attrs: dict) -> bool:
    """Ersetzt die erste Fundstelle von `zitat` in einem Textknoten durch
    einen ``entitaetsverweis``-Chip, mitten im umgebenden Text gesplittet.

    Arbeitet direkt auf dem geladenen TipTap-Dokument (mutiert in-place),
    analog zu ``wiki_pruefung._text_ersetzen`` — nur dass hier kein Text
    ersetzt, sondern ein neuer Knoten zwischen zwei Textteile eingefügt
    wird. Marks (z.B. 🔒 SL-geheim) des ursprünglichen Textknotens bleiben
    auf beiden verbleibenden Textteilen erhalten, der Verweis-Chip selbst
    trägt nie eine Markierung.
    """
    if not isinstance(knoten, dict):
        return False

    content = knoten.get("content")
    if isinstance(content, list):
        for i, kind in enumerate(content):
            if (
                isinstance(kind, dict)
                and kind.get("type") == "text"
                and isinstance(kind.get("text"), str)
                and zitat in kind["text"]
            ):
                text = kind["text"]
                idx = text.index(zitat)
                vor, nach = text[:idx], text[idx + len(zitat):]
                marks = kind.get("marks")
                neu = []
                if vor:
                    stueck: dict = {"type": "text", "text": vor}
                    if marks:
                        stueck["marks"] = marks
                    neu.append(stueck)
                neu.append({"type": VERWEIS_TYP, "attrs": attrs})
                if nach:
                    stueck = {"type": "text", "text": nach}
                    if marks:
                        stueck["marks"] = marks
                    neu.append(stueck)
                knoten["content"] = content[:i] + neu + content[i + 1:]
                return True

        # Kein direkter Treffer auf dieser Ebene — in die Kinder absteigen.
        for kind in content:
            if _verweis_einfuegen(kind, zitat, attrs):
                return True

    return False


_CREATE_FUNKTIONEN = {
    "Person": lambda name: (
        "Person",
        PERSON_FIELDS,
        PersonCreate(name=name, personType="NPC", istEntwurf=True, sichtbarkeit="GM").model_dump(),
    ),
    "Ort": lambda name: (
        "Ort",
        ORT_FIELDS,
        OrtCreate(name=name, istEntwurf=True, sichtbarkeit="GM").model_dump(),
    ),
    "Event": lambda name: (
        "Event",
        EVENT_FIELDS,
        EventCreate(title=name, istEntwurf=True, sichtbarkeit="GM").model_dump(),
    ),
    "Fraktion": lambda name: (
        "Fraktion",
        FRAKTION_FIELDS,
        FraktionCreate(name=name, istEntwurf=True, sichtbarkeit="GM").model_dump(),
    ),
}


async def _entwurf_anlegen(campaign_id: str, typ: str, name: str) -> str:
    """Legt eine neue Entität als Entwurf an (Ideenschmiede), gibt ihre ID zurück."""
    label, fields, data = _CREATE_FUNKTIONEN[typ](name)
    node = await create_node(label, fields, campaign_id, data)
    return node["id"]


class AnwendenErgebnis(BaseModel):
    ersetzt: bool
    inhalt: str = ""
    zielId: str = ""
    neuAngelegt: bool = False


async def anwenden(
    campaign_id: str, seiten_id: str, zitat: str, typ: str, name: str, ziel_id: str | None
) -> AnwendenErgebnis | None:
    """Wendet EINEN Vorschlag an: fügt den Verweis-Chip ein und speichert.

    `ziel_id=None` legt zuerst einen Entwurf an (Marks Vorgabe: Entwurf zur
    Prüfung, kein Autocommit) — der Chip zeigt danach auf diesen neuen
    Entwurf, `ersetzt=False` kommt nur zurück, wenn das Zitat inzwischen
    nicht mehr im gespeicherten Text steht (z.B. weil die Seite von Hand
    geändert wurde, seit die Vorschläge geholt wurden).
    """
    if typ not in _TYPEN:
        return None
    seite = await repository.get_seite(campaign_id, seiten_id)
    if seite is None:
        return None

    neu_angelegt = False
    if not ziel_id:
        ziel_id = await _entwurf_anlegen(campaign_id, typ, name)
        neu_angelegt = True

    try:
        dokument = json.loads(seite["inhalt"])
    except (ValueError, TypeError):
        return AnwendenErgebnis(ersetzt=False, inhalt=seite["inhalt"], zielId=ziel_id, neuAngelegt=neu_angelegt)

    attrs = {"zielId": ziel_id, "zielTyp": typ, "label": name}
    if not _verweis_einfuegen(dokument, zitat, attrs):
        return AnwendenErgebnis(ersetzt=False, inhalt=seite["inhalt"], zielId=ziel_id, neuAngelegt=neu_angelegt)

    neuer_inhalt = json.dumps(dokument, ensure_ascii=False)
    aktualisiert = await repository.update_seite(campaign_id, seiten_id, {"inhalt": neuer_inhalt})
    return AnwendenErgebnis(
        ersetzt=True,
        inhalt=aktualisiert["inhalt"] if aktualisiert else neuer_inhalt,
        zielId=ziel_id,
        neuAngelegt=neu_angelegt,
    )
