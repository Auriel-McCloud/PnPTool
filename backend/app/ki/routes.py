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
from app.items.repository import create_gegenstand
from app.items.routes import _create_data
from app.items.schemas import GEGENSTAND_TYPEN, GegenstandCreate
from app.ki.client import KiFehler, generiere_json
from app.ki.kontext import sammle_kontext
from app.ki.wiki_pruefung import (
    SweepAntwort,
    UebernehmenAntwort,
    pruefe_seite,
    sweep,
    uebernehmen_befund,
)
from app.ki.auto_verknuepfung import (
    AnwendenErgebnis,
    BeziehungAnwendenErgebnis,
    BeziehungAnwendenInput,
    VerknuepfungsVorschlag,
    VorschlaegeAntwort,
    anwenden as verknuepfung_anwenden,
    beziehung_anwenden as verknuepfung_beziehung_anwenden,
    vorschlaege as verknuepfung_vorschlaege,
)
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

_GEGENSTAND_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "beschreibung": {"type": "STRING"},
        "typ": {"type": "STRING", "enum": GEGENSTAND_TYPEN},
        "preis": {"type": "INTEGER"},
        # Seltenheit 1 (überall verfügbar) bis 5 (Speziallabor/Schwarzmarkt) —
        # Grundlage für die automatische Shop-Bestückung (docs/api/haendler.md).
        "seltenheit": {"type": "INTEGER"},
    },
    "required": ["name", "beschreibung", "typ", "preis", "seltenheit"],
}

# Der Typ ist seit 22.09.2026 nach dem Anlegen fix (siehe items/schemas.py) —
# die KI muss ihn deshalb beim ersten Wurf richtig treffen, kein Nachbessern
# per Dropdown mehr möglich. Deshalb der Katalog explizit im Prompt.
_GEGENSTAND_SYSTEM = (
    _SYSTEM
    + " Erfinde einen einzelnen Gegenstand aus der Welt von NeotopiA — Waffe, "
    "Ausrüstung, Kuriosität, was zum Wunsch passt. typ MUSS exakt einer der "
    "folgenden Werte sein (nichts anderes, keine Erfindung): "
    + ", ".join(GEGENSTAND_TYPEN)
    + ". preis in Nuyen, realistisch für den Typ (eine Lederjacke kostet "
    "anders als ein Cyberdeck). seltenheit 1 (überall erhältlich) bis 5 "
    "(nur Speziallabor/Schwarzmarkt)."
)

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
    typ: Literal["story", "charakter", "gegenstand"]
    prompt: str


class UebernehmenInput(BaseModel):
    zitat: str
    vorschlag: str


class ObjektTextInput(BaseModel):
    """Für den ✨ KI-Knopf neben „SL-geheim" an Beschreibung/Notizen-Feldern."""

    objektTyp: str
    objektName: str
    # Bisheriger Text des Feldes (reiner Text, vom Frontend per editor.getText()
    # geholt) — gibt der KI Anschluss an das, was schon dasteht.
    bisherigerText: str = ""
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
    """Hängt die freigegebene Kampagnenwelt an den Wunsch, wenn es eine gibt.

    Bewusst scharf formuliert (22.09.2026, Mark-Bug): Gemini erfand bei einem
    Story-Part "Proxima Centauri", obwohl die Kampagne bereits "Omikron²
    Eridiani" als Sternensystem freigegeben hatte — die weiche Formulierung
    von vorher ("füge das Neue darin ein") reichte nicht. Jetzt eine
    ausdrückliche Vorrang-Regel: Bestehendes verwenden statt Neues erfinden,
    wenn es thematisch passt.
    """
    if not kontext:
        return prompt
    return (
        f"{prompt}\n\n"
        f"Freigegebene Welt der Kampagne — das ist ALLES, was in dieser Kampagne "
        f"bereits existiert (Personen, Orte, Events, Fraktionen, Gegenstände, "
        f"Wiki-Wissen). Für alles, was du erwähnst (Orte, Sternensysteme, "
        f"Fraktionen, Personen, Organisationen, ...): verwende VORRANGIG etwas "
        f"aus dieser Liste, wenn es thematisch passt — erfinde nur dann etwas "
        f"komplett Neues, wenn wirklich nichts Passendes existiert. Erfinde "
        f"insbesondere KEINEN neuen Namen für etwas, das in der Liste bereits "
        f"unter einem anderen Namen vorkommt:\n{kontext}"
    )


def _als_int(wert, standard: int = 0) -> int:
    try:
        return int(wert)
    except (TypeError, ValueError):
        return standard


# Attribute (Körperkraft, Entschlossenheit, ...) sind fundamental — 0 ist
# regeltechnisch nicht vorgesehen, jeder Charakter hat mindestens 1 in jedem.
# Fertigkeiten/Hintergründe dürfen dagegen 0 sein ("kann's einfach nicht").
_ATTRIBUT_MINDESTWERT = 1


async def _katalog_zu_text(ruleset: str) -> str:
    """Trait-Katalog als kompakte, gruppierte Liste für den Prompt.

    Mit Beschreibung pro Trait — sonst rät die KI aus dem bloßen Namen (z.B.
    ordnet sie Feuermagie "Überleben" statt "Kräfte" zu, weil beide Namen ganz
    grob nach "irgendwas Wildnis-Feuer-mäßiges" klingen).
    """
    katalog = await list_catalog(ruleset)
    gruppen: dict[str, list[str]] = {}
    for t in katalog:
        eintrag = f"{t['name']} (max {t['defaultMax']})"
        if t.get("description"):
            eintrag += f": {t['description']}"
        gruppen.setdefault(t["category"], []).append(eintrag)
    return "\n".join(f"{kategorie}:\n  " + "\n  ".join(namen) for kategorie, namen in gruppen.items())


async def _setze_traits(campaign_id: str, person_id: str, ruleset: str, wahl: list[dict]) -> int:
    """Übernimmt Gemini's/Mistral's Trait-Wahl (name→rating) auf den Charakterbogen.

    Nur Namen, die es im Katalog gibt, werden gesetzt; Werte werden auf
    [0, defaultMax] geklemmt. Gibt die Anzahl gesetzter Traits zurück.
    """
    katalog = await list_catalog(ruleset)
    name_zu_def = {t["name"]: t for t in katalog}
    gesetzt: set[str] = set()
    for eintrag in wahl:
        name = (eintrag.get("name") or "").strip()
        definier = name_zu_def.get(name)
        if definier is None:
            continue
        rating = max(0, min(_als_int(eintrag.get("rating")), definier["defaultMax"]))
        # Attribute dürfen nie 0 sein (siehe unten) — direkt hier abfangen,
        # falls die KI ein Attribut explizit mit rating=0 zurückgibt statt
        # es einfach wegzulassen.
        if definier["category"].startswith("Attribut"):
            rating = max(rating, _ATTRIBUT_MINDESTWERT)
        await set_rating(campaign_id, person_id, definier["id"], rating, None)
        gesetzt.add(name)

    # Attribute sind fundamental — jeder Charakter hat 1-6 in allen neun,
    # nie 0 (0 hieße "Attribut existiert praktisch nicht", was regeltechnisch
    # nicht vorgesehen ist). Die KI kann eines vergessen oder mit 0 angeben;
    # das hier ist ein harter Nachbearbeitungsschritt, unabhängig vom Modell.
    for t in katalog:
        if t["category"].startswith("Attribut") and t["name"] not in gesetzt:
            await set_rating(campaign_id, person_id, t["id"], _ATTRIBUT_MINDESTWERT, None)
            gesetzt.add(t["name"])

    return len(gesetzt)


@router.post("/idee")
async def ki_idee(campaign_id: str, body: KiIdeeInput):
    """Generiert eine Idee und legt sie als Entwurf in der Schmiede an."""
    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Der Wunsch darf nicht leer sein.")

    try:
        if body.typ == "story":
            kontext = await sammle_kontext(campaign_id)
            prompt_komplett = _mit_kontext(prompt, kontext)
            ergebnis = await generiere_json(prompt_komplett, _SYSTEM, _STORY_SCHEMA)
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

        if body.typ == "gegenstand":
            # Bevorzugt Bestehendes wiederverwenden, nur bei echter Lücke
            # etwas Neues erfinden — dasselbe Vorrang-Prinzip wie bei Story/
            # Charakter (_mit_kontext), Marks Entscheidung 22.09.2026: "beides,
            # bevorzugt Bestehendes wiederverwenden, nur bei Lücken etwas
            # Neues vorschlagen".
            kontext = await sammle_kontext(campaign_id)
            prompt_komplett = _mit_kontext(prompt, kontext)
            ergebnis = await generiere_json(prompt_komplett, _GEGENSTAND_SYSTEM, _GEGENSTAND_SCHEMA)
            name = (ergebnis.get("name") or "").strip() or "Unbenannter Gegenstand"
            typ = ergebnis.get("typ") or "Sonstiges"
            if typ not in GEGENSTAND_TYPEN:
                # Die KI hat trotz Enum-Vorgabe daneben gegriffen — der Typ
                # ist nach dem Anlegen fix (schemas.py), deshalb hier ein
                # harter Fallback statt eines ungültigen/erfundenen Werts.
                typ = "Sonstiges"
            seltenheit = max(1, min(_als_int(ergebnis.get("seltenheit"), 1), 5))
            gegenstand_body = GegenstandCreate(
                name=name,
                description=(ergebnis.get("beschreibung") or "").strip(),
                typ=typ,
                preis=max(0, _als_int(ergebnis.get("preis"))),
                seltenheit=seltenheit,
                istEntwurf=True,
            )
            # _create_data ist derselbe Helfer wie in items/routes.py::create_vorlage
            # (SL-Vorlage anlegen) — garantiert dieselbe Feldbefüllung, keine
            # zweite, abweichende Kopie der Anlege-Logik.
            gegenstand = await create_gegenstand(
                campaign_id,
                None,  # besitzerlos = Vorlage, wie jeder andere Ideenschmiede-Entwurf
                _create_data(gegenstand_body, True, "GM", []),
            )
            if gegenstand is None:
                raise HTTPException(status_code=404, detail="Kampagne nicht gefunden")
            return {"typ": "gegenstand", "id": gegenstand["id"], "name": name}

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

    except KiFehler as e:
        # 502 statt 500: der Fehler liegt an der externen KI, nicht an uns.
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/wiki/{seiten_id}/pruefen")
async def wiki_seite_pruefen(campaign_id: str, seiten_id: str):
    """Prüft eine einzelne Wiki-Seite auf Rechtschreib-/Grammatik-/Logikfehler.

    Der "🔍 Prüfen"-Knopf im Wiki-Editor (Story-Wiki und Ideenschmiede-
    Wiki-Popup teilen sich dieselbe Editor-Komponente). Merkt sich den
    geprüften Textstand — taucht diese Seite später im Sweep auf und hat
    sich seither nichts geändert, wird sie dort übersprungen.
    """
    try:
        befunde = await pruefe_seite(campaign_id, seiten_id)
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"befunde": [b.model_dump() for b in befunde]}


@router.post("/wiki/pruefen-alle", response_model=SweepAntwort)
async def wiki_sweep(campaign_id: str):
    """Prüft alle Wiki-Seiten der Kampagne, überspringt unveränderte.

    Marks "Prüf Fließtext!"-Knopf in den Kampagnen-Einstellungen — bewusst
    ein Sweep statt einer Dauerprüfung: er will das nur ab und zu anstoßen,
    nicht bei jedem Tastendruck KI-Kosten verursachen.
    """
    try:
        return await sweep(campaign_id)
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/wiki/{seiten_id}/pruefung/uebernehmen", response_model=UebernehmenAntwort)
async def wiki_befund_uebernehmen(campaign_id: str, seiten_id: str, body: UebernehmenInput):
    """Übernimmt einen Korrekturvorschlag: ersetzt das Zitat im Seitentext.

    Funktioniert auch für Seiten, die gerade nicht im Editor offen sind
    (Sweep-Ergebnisse können viele Seiten gleichzeitig betreffen).
    """
    ergebnis = await uebernehmen_befund(campaign_id, seiten_id, body.zitat, body.vorschlag)
    if ergebnis is None:
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")
    return ergebnis


_OBJEKT_TEXT_SYSTEM = (
    _SYSTEM
    + " Du schreibst einen kurzen Fließtext-Zusatz für die Beschreibung oder "
    "Notizen eines einzelnen Kampagnenobjekts (Person, Ort, Event, Fraktion "
    "oder Gegenstand) — kein ganzer Artikel, keine Überschriften, nur "
    "zusammenhängender Fließtext in ein bis drei Absätzen, der zum bisherigen "
    "Text passt und ihn sinnvoll fortsetzt oder ergänzt, ohne ihn zu wiederholen."
)


@router.post("/objekt-text")
async def ki_objekt_text(campaign_id: str, body: ObjektTextInput):
    """Generiert einen Textvorschlag für ein einzelnes Objekt (✨-Knopf im
    RichTextEditor, neben „SL-geheim"). Liefert nur den Vorschlag zur
    Vorschau zurück — die Übernahme (Anhängen ans Feld) macht das Frontend,
    hier wird nichts gespeichert.
    """
    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Der Wunsch darf nicht leer sein.")

    kontext = await sammle_kontext(campaign_id)
    teile = [
        f"{body.objektTyp}: {body.objektName}",
    ]
    if body.bisherigerText.strip():
        teile.append(f"Bisheriger Text dieses Feldes:\n{body.bisherigerText.strip()}")
    teile.append(f"Wunsch: {prompt}")
    objekt_prompt = "\n\n".join(teile)

    try:
        ergebnis = await generiere_json(
            _mit_kontext(objekt_prompt, kontext),
            _OBJEKT_TEXT_SYSTEM,
            {"type": "OBJECT", "properties": {"text": {"type": "STRING"}}, "required": ["text"]},
        )
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {"text": (ergebnis.get("text") or "").strip()}


class AnwendenVerknuepfungInput(BaseModel):
    zitat: str
    typ: str
    name: str
    # None = Entität existiert noch nicht, "anwenden" legt einen Entwurf an.
    zielId: str | None = None


@router.post("/wiki/{seiten_id}/verknuepfung/vorschlaege", response_model=VorschlaegeAntwort)
async def wiki_verknuepfung_vorschlaege(campaign_id: str, seiten_id: str):
    """Auto-Verknüpfung, Schritt 1: erkennt Erwähnungen UND Beziehungen in

    einem einzigen KI-Aufruf (Mark ist kostenbewusst — zwei Requests für
    denselben Text wären unnötig teuer). Verweise sind die klassische
    "Erwähnt in"-Verknüpfung zur Wiki-Seite, Beziehungen sind echte
    VERBINDUNG-Kanten zwischen den erwähnten Entitäten selbst (der
    Beziehungsgraph, sonst über den "Beziehungen"-Tab gepflegt).
    """
    try:
        return await verknuepfung_vorschlaege(campaign_id, seiten_id)
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/wiki/{seiten_id}/verknuepfung/anwenden",
    response_model=AnwendenErgebnis,
)
async def wiki_verknuepfung_anwenden(campaign_id: str, seiten_id: str, body: AnwendenVerknuepfungInput):
    """Auto-Verknüpfung, Schritt 2: wendet EINEN bestätigten Vorschlag an.

    Ohne `zielId` legt das zuerst einen Entwurf in der Ideenschmiede an
    (Marks Vorgabe: Vorschlag zur Prüfung, kein Autocommit) und verknüpft
    dorthin.
    """
    ergebnis = await verknuepfung_anwenden(campaign_id, seiten_id, body.zitat, body.typ, body.name, body.zielId)
    if ergebnis is None:
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")
    return ergebnis


@router.post(
    "/wiki/{seiten_id}/verknuepfung/beziehung",
    response_model=BeziehungAnwendenErgebnis,
)
async def wiki_verknuepfung_beziehung(campaign_id: str, seiten_id: str, body: BeziehungAnwendenInput):
    """Auto-Verknüpfung, Schritt 2b: wendet EINEN bestätigten Beziehungs-

    Vorschlag an — legt eine echte VERBINDUNG-Kante zwischen den zwei
    Entitäten an (dieselbe Kante wie der "+ Neue Verbindung"-Knopf im
    Beziehungen-Tab). `seiten_id` ist nur Teil des URL-Pfads für denselben
    Aufbau wie die anderen Auto-Verknüpfungs-Routen — die Kante selbst
    hängt nicht an der Wiki-Seite, sondern direkt an den zwei Entitäten.
    """
    return await verknuepfung_beziehung_anwenden(campaign_id, body)
