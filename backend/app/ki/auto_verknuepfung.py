"""Auto-Verknüpfung: KI erkennt Erwähnungen von Personen/Orten/Events/
Fraktionen im Wiki-Text und verknüpft sie automatisch als echte Graphkanten
(CLAUDE.md Punkt 3, präzisiert 20.09.2026).

Zwei Ebenen, in EINEM KI-Aufruf ermittelt (Mark ist kostenbewusst beim
LLM-Verbrauch — zwei Requests für denselben Text wären unnötig teuer):

- **Verweise** — jede erkannte Erwähnung bekommt einen echten
  ``entitaetsverweis``-Chip an der zitierten Textstelle (die klassische
  "Erwähnt in"-Verknüpfung zur Wiki-Seite).
- **Beziehungen** (22.09.2026, Marks Wunsch) — wo der Text eine KONKRETE
  Beziehung zwischen zwei erkannten Entitäten nahelegt (nicht nur zufällige
  Nähe im selben Absatz), schlägt die KI Typ + Kurzbeschreibung vor. Das
  ist eine echte ``VERBINDUNG``-Kante zwischen den beiden Entitäten selbst
  (der Beziehungsgraph, sonst über den "Beziehungen"-Tab gepflegt) — etwas
  ANDERES als der Verweis zur Wiki-Seite.

Drei Schritte, getrennt wie bei der Rechtschreib-/Logikprüfung
(``wiki_pruefung.py``):

- ``vorschlaege`` — liest eine Seite, lässt die KI Erwähnungen UND
  Beziehungen erkennen, gleicht Namen in Python (NICHT durch die KI) gegen
  die freigegebenen Entitäten ab. Nichts wird gespeichert.
- ``anwenden`` — fügt für EINEN bestätigten Verweis-Vorschlag einen echten
  ``entitaetsverweis``-Chip an der zitierten Textstelle ein. Existiert die
  erkannte Entität noch nicht, wird zuerst ein Entwurf in der Ideenschmiede
  angelegt (istEntwurf=true, SL-geheim) und der Chip zeigt auf diesen neuen
  Entwurf. Das Speichern der Seite löst danach ganz normal
  ``wiki/repository.py::_verweise_schreiben`` aus — die echte
  VERWEIST_AUF-Kante entsteht also über denselben Weg wie ein von Hand über
  den „⧉ Verknüpfen"-Knopf eingefügter Verweis.
- ``beziehung_anwenden`` — legt für EINEN bestätigten Beziehungs-Vorschlag
  eine echte ``VERBINDUNG``-Kante zwischen den zwei Entitäten an (dieselbe
  Route wie der "+ Neue Verbindung"-Knopf im Beziehungen-Tab). Fehlende
  Entitäten werden dabei ebenfalls als Entwurf angelegt — mit Dedup-Check
  (``_finde_oder_lege_an``), damit dieselbe neue Person nicht zweimal
  entsteht, wenn sie sowohl in einem Verweis- als auch in einem
  Beziehungs-Vorschlag auftaucht.

Bewusst PRO VORSCHLAG einzeln anzuwenden statt eines Sammel-Übernehmens:
neue Entitäten landen als Entwurf zur Prüfung durch den SL, kein
automatischer Autocommit in die Kampagne (Marks Vorgabe, 20.09.2026).
"""

import hashlib
import json

from pydantic import BaseModel

from app.db.neo4j_driver import get_driver
from app.entities.repository import (
    EVENT_FIELDS,
    FRAKTION_FIELDS,
    ORT_FIELDS,
    PERSON_FIELDS,
    create_node,
    create_verbindung,
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
    "Entitäten und den zu durchsuchenden Text. Zwei Aufgaben:\n\n"
    "1) VERWEISE: Finde jede Textstelle, die eine konkrete, benannte "
    "Person, einen konkreten Ort, ein konkretes Ereignis oder eine "
    "konkrete Fraktion/Organisation erwähnt — auch wenn sie NICHT in der "
    "bekannten Liste steht (dann ist es eine neue Erwähnung). Ignoriere "
    "allgemeine Begriffe ohne Eigennamen (\"ein Straßenhändler\", \"die "
    "Stadt\") — nur konkret benannte Dinge zählen. Für jeden Treffer: "
    "'zitat' ist die exakte, zusammenhängende Textstelle wie sie WÖRTLICH "
    "im Text steht (kurz — nur der Name, nicht der ganze Satz), 'typ' ist "
    "Person/Ort/Event/Fraktion, 'name' ist die kanonische Namensform — "
    "steht die Entität in der bekannten Liste, MUSS 'name' exakt (Zeichen "
    "für Zeichen) dem Listennamen entsprechen, sonst deine beste "
    "Einschätzung des vollen Namens. Erwähne jede Entität nur EINMAL, auch "
    "wenn sie mehrfach im Text vorkommt (nimm die erste Fundstelle).\n\n"
    "2) BEZIEHUNGEN: Wo der Text eine KONKRETE Beziehung zwischen zwei "
    "erwähnten Entitäten ausdrückt (z.B. \"arbeitet für\", \"ist "
    "verfeindet mit\", \"wohnt in\", \"Mitglied von\", \"hat Schulden "
    "bei\", \"war dabei bei\"), melde sie separat. NUR bei einer wirklich "
    "im Text ausgedrückten Beziehung — NIEMALS nur, weil zwei Namen im "
    "selben Satz oder Absatz stehen, ohne dass eine Beziehung zwischen "
    "ihnen beschrieben wird. name1/typ1 und name2/typ2 identifizieren die "
    "beiden Seiten (dieselben Namens-/Typregeln wie bei VERWEISE oben — "
    "wenn eine der beiden Seiten in der bekannten Liste steht, exakt deren "
    "Namen verwenden). 'beziehungstyp' ist eine kurze Bezeichnung der "
    "Beziehung aus Sicht von Seite 1 (z.B. \"Arbeitet für\", \"Feind\", "
    "\"Mitglied von\", \"Schulden bei\"), 'beschreibung' ist ein kurzer "
    "erklärender Satz, falls hilfreich (sonst leer)."
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
        "beziehungen": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "typ1": {"type": "STRING", "enum": list(_TYPEN)},
                    "name1": {"type": "STRING"},
                    "typ2": {"type": "STRING", "enum": list(_TYPEN)},
                    "name2": {"type": "STRING"},
                    "beziehungstyp": {"type": "STRING"},
                    "beschreibung": {"type": "STRING"},
                },
                "required": ["typ1", "name1", "typ2", "name2", "beziehungstyp"],
            },
        },
    },
    "required": ["vorschlaege", "beziehungen"],
}


class VerknuepfungsVorschlag(BaseModel):
    zitat: str
    typ: str
    name: str
    # Gesetzt, wenn "name" (normalisiert) zu einer freigegebenen Entität
    # dieses Typs passt — dann verknüpft "anwenden" direkt dorthin. Sonst
    # None: "anwenden" legt zuerst einen Entwurf mit diesem Namen an.
    zielId: str | None = None


class BeziehungsVorschlag(BaseModel):
    typ1: str
    name1: str
    zielId1: str | None = None
    typ2: str
    name2: str
    zielId2: str | None = None
    beziehungstyp: str
    beschreibung: str = ""


class VorschlaegeAntwort(BaseModel):
    verweise: list[VerknuepfungsVorschlag] = []
    beziehungen: list[BeziehungsVorschlag] = []


def _normalisiert(text: str) -> str:
    return " ".join(text.strip().casefold().split())


async def vorschlaege(campaign_id: str, seiten_id: str) -> VorschlaegeAntwort:
    """Lässt die KI Erwähnungen UND Beziehungen einer Wiki-Seite erkennen.

    Dünner Wrapper um ``_erkennen`` — lädt nur Seite und bekannte Entitäten.
    """
    seite = await repository.get_seite(campaign_id, seiten_id)
    if seite is None:
        return VorschlaegeAntwort()
    text = tiptap_zu_text(seite["inhalt"])
    if not text.strip():
        return VorschlaegeAntwort()

    entitaeten = await sammle_entitaeten(campaign_id)
    return await _erkennen(entitaeten, text)


async def vorschlaege_fuer_text(campaign_id: str, text: str) -> VorschlaegeAntwort:
    """Wie ``vorschlaege``, aber für einen freien Text ohne Wiki-Seitenbezug
    (Ideenschmiede-Entwurfstext, Beschreibungs-/Notizen-Feld einer Entität).

    Genutzt vom ✨-Knopf im generischen ``RichTextEditor`` — dort sind nur die
    **Beziehungen** anwendbar (echte VERBINDUNG-Kante), da ein Verweis-Chip
    ohne Wiki-Seite kein Ziel zum Einfügen hätte; das Frontend blendet die
    mitgelieferten ``verweise`` deshalb aus.
    """
    if not text.strip():
        return VorschlaegeAntwort()
    entitaeten = await sammle_entitaeten(campaign_id)
    return await _erkennen(entitaeten, text)


async def _erkennen(entitaeten: list[dict], text: str) -> VorschlaegeAntwort:
    """Ein KI-Aufruf: erkennt Erwähnungen UND Beziehungen in `text`, gleicht
    Namen gegen die mitgegebenen (bereits geladenen) Entitäten ab.

    Der Namensabgleich (Vorschlag → bestehende ID) passiert bewusst hier in
    Python, nicht durch die KI: die KI kennt keine IDs, nur Namen — ein
    Tippfehler oder eine leicht andere Schreibweise der KI dürfte niemals
    eine falsche ID erfinden.
    """
    liste_text = "\n".join(f"- {e['kind']}: {e['name']}" for e in entitaeten if e["name"]) or "(noch keine)"

    prompt = (
        f"Bekannte Entitäten dieser Kampagne:\n{liste_text}\n\n"
        f"Zu durchsuchender Text:\n{text}"
    )
    ergebnis = await generiere_json(prompt, _SYSTEM, _SCHEMA)

    # Schneller Nachschlage-Index: (typ, normalisierter Name) -> id.
    index = {(e["kind"], _normalisiert(e["name"])): e["id"] for e in entitaeten if e["name"]}

    verweise: list[VerknuepfungsVorschlag] = []
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
        verweise.append(VerknuepfungsVorschlag(zitat=zitat, typ=typ, name=name, zielId=ziel_id))

    beziehungen: list[BeziehungsVorschlag] = []
    gesehen_beziehungen: set[tuple] = set()
    for eintrag in ergebnis.get("beziehungen") or []:
        typ1 = eintrag.get("typ1") or ""
        name1 = (eintrag.get("name1") or "").strip()
        typ2 = eintrag.get("typ2") or ""
        name2 = (eintrag.get("name2") or "").strip()
        beziehungstyp = (eintrag.get("beziehungstyp") or "").strip()
        if typ1 not in _TYPEN or typ2 not in _TYPEN or not name1 or not name2 or not beziehungstyp:
            continue
        # Dieselbe Entität mit sich selbst ergäbe eine sinnlose Kante.
        if typ1 == typ2 and _normalisiert(name1) == _normalisiert(name2):
            continue
        schluessel = (typ1, _normalisiert(name1), typ2, _normalisiert(name2), beziehungstyp)
        if schluessel in gesehen_beziehungen:
            continue
        gesehen_beziehungen.add(schluessel)
        beziehungen.append(
            BeziehungsVorschlag(
                typ1=typ1,
                name1=name1,
                zielId1=index.get((typ1, _normalisiert(name1))),
                typ2=typ2,
                name2=name2,
                zielId2=index.get((typ2, _normalisiert(name2))),
                beziehungstyp=beziehungstyp,
                beschreibung=(eintrag.get("beschreibung") or "").strip(),
            )
        )

    return VorschlaegeAntwort(verweise=verweise, beziehungen=beziehungen)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SeitenVorschlaege(BaseModel):
    """Erkannte Vorschläge einer einzelnen Seite im Sweep — dieselben Felder
    wie ``VorschlaegeAntwort``, nur mit Seitenbezug für die Sammelübersicht."""

    seitenId: str
    titel: str
    verweise: list[VerknuepfungsVorschlag] = []
    beziehungen: list[BeziehungsVorschlag] = []


class SweepVorschlaegeAntwort(BaseModel):
    geprueft: int
    uebersprungen: int
    ergebnisse: list[SeitenVorschlaege] = []


async def sweep(campaign_id: str) -> SweepVorschlaegeAntwort:
    """Geht ALLE Wiki-Seiten der Kampagne auf Auto-Verknüpfung durch.

    Wie der Rechtschreib-/Logik-Sweep (``wiki_pruefung.sweep``): überspringt
    Seiten, deren Text sich seit dem letzten Durchlauf nicht geändert hat
    (eigener Hash, siehe ``wiki/repository.get_verknuepfhash``), damit nicht
    bei jedem Klick die ganze Kampagne neu gegen die KI läuft. Legt NICHTS
    automatisch an — liefert nur die Vorschläge zur Sammelübersicht, jeder
    einzeln bestätigt (Marks Vorgabe: kein Autocommit).
    """
    seiten = await repository.list_seiten(campaign_id)
    entitaeten = await sammle_entitaeten(campaign_id)

    geprueft = 0
    uebersprungen = 0
    ergebnisse: list[SeitenVorschlaege] = []

    for seite in seiten:
        text = tiptap_zu_text(seite["inhalt"])
        aktueller_hash = _hash(text)
        letzter_hash = await repository.get_verknuepfhash(campaign_id, seite["id"])
        if text.strip() and aktueller_hash == letzter_hash:
            uebersprungen += 1
            continue

        geprueft += 1
        antwort = await _erkennen(entitaeten, text) if text.strip() else VorschlaegeAntwort()
        await repository.set_verknuepfhash(campaign_id, seite["id"], aktueller_hash)
        if antwort.verweise or antwort.beziehungen:
            ergebnisse.append(
                SeitenVorschlaege(
                    seitenId=seite["id"],
                    titel=seite["titel"],
                    verweise=antwort.verweise,
                    beziehungen=antwort.beziehungen,
                )
            )

    return SweepVorschlaegeAntwort(geprueft=geprueft, uebersprungen=uebersprungen, ergebnisse=ergebnisse)


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


async def _bestehende_id(campaign_id: str, typ: str, name: str) -> str | None:
    """Sucht eine Entität dieses Typs mit exakt (normalisiert) diesem Namen.

    Grundlage für den Dedup-Schutz in ``beziehung_anwenden``: taucht dieselbe
    neue Person sowohl in einem Verweis- als auch in einem Beziehungs-
    Vorschlag auf und wurde der Verweis zuerst angewandt, soll die Beziehung
    NICHT eine zweite, doppelte Person anlegen, sondern die frisch entstandene
    wiederfinden. `sammle_entitaeten` liefert nur FREIGEGEBENE Entitäten
    (``istEntwurf=false``) — Entwürfe müssen hier also separat gesucht werden.
    """
    driver = get_driver()
    namensfeld = "title" if typ == "Event" else "name"
    query = f"""
        MATCH (n:{typ} {{campaignId: $campaign_id}})
        WHERE toLower(n.{namensfeld}) = toLower($name)
        RETURN n.id AS id
        LIMIT 1
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, name=name)
        record = await result.single()
        return record["id"] if record else None


async def _finde_oder_lege_an(campaign_id: str, typ: str, name: str, ziel_id: str | None) -> tuple[str, bool]:
    """Löst eine (typ, name, ziel_id)-Angabe zu einer echten ID auf.

    Gibt (id, neu_angelegt) zurück. `ziel_id` kommt vom Frontend-Vorschlag
    (mit den freigegebenen Entitäten zur Zeit der Erkennung abgeglichen) —
    zwischenzeitlich kann aber genau diese Entität schon als Entwurf über
    einen anderen Vorschlag entstanden sein (z.B. zuerst der Verweis, dann
    die Beziehung, die dieselbe Person nennt). Deshalb bei fehlender
    `ziel_id` zuerst nachschauen, bevor ein Duplikat entsteht.
    """
    if ziel_id:
        return ziel_id, False
    bestehend = await _bestehende_id(campaign_id, typ, name)
    if bestehend:
        return bestehend, False
    return await _entwurf_anlegen(campaign_id, typ, name), True


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

    ziel_id, neu_angelegt = await _finde_oder_lege_an(campaign_id, typ, name, ziel_id)

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


class BeziehungAnwendenInput(BaseModel):
    typ1: str
    name1: str
    zielId1: str | None = None
    typ2: str
    name2: str
    zielId2: str | None = None
    beziehungstyp: str
    beschreibung: str = ""


class BeziehungAnwendenErgebnis(BaseModel):
    verbindungId: str
    zielId1: str
    zielId2: str
    neuAngelegt1: bool
    neuAngelegt2: bool


async def beziehung_anwenden(campaign_id: str, eingabe: BeziehungAnwendenInput) -> BeziehungAnwendenErgebnis:
    """Legt eine echte VERBINDUNG-Kante zwischen zwei (ggf. neuen) Entitäten an.

    Fehlt eine der beiden Seiten noch, wird sie zuerst als SL-geheimer
    Entwurf angelegt (dieselbe Vorgabe wie bei den Verweisen: kein
    Autocommit in die Kampagne) — mit Dedup-Schutz über
    ``_finde_oder_lege_an``, falls dieselbe Entität bereits über einen
    anderen Vorschlag (Verweis oder frühere Beziehung) entstanden ist.
    """
    ziel_id1, neu1 = await _finde_oder_lege_an(campaign_id, eingabe.typ1, eingabe.name1, eingabe.zielId1)
    ziel_id2, neu2 = await _finde_oder_lege_an(campaign_id, eingabe.typ2, eingabe.name2, eingabe.zielId2)

    verbindung = await create_verbindung(
        campaign_id,
        {
            "vonKind": eingabe.typ1,
            "vonId": ziel_id1,
            "zuKind": eingabe.typ2,
            "zuId": ziel_id2,
            "typ": eingabe.beziehungstyp,
            "beschreibung": eingabe.beschreibung,
            "seit": "",
            "bis": "",
            "sichtbarkeit": "GM",
            "sichtbarFuer": [],
        },
    )

    return BeziehungAnwendenErgebnis(
        verbindungId=verbindung["id"],
        zielId1=ziel_id1,
        zielId2=ziel_id2,
        neuAngelegt1=neu1,
        neuAngelegt2=neu2,
    )
