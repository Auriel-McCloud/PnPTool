"""KI-Endpunkte: Gemini generiert Inhalte direkt in die Ideenschmiede.

Typen landen als Entwurf (`istEntwurf=true`) in der Schmiede — außer
``verbindung``, die eine echte Kante anlegt (fehlende Enden als Entwurf):

- ``story``      — Wiki-Seite (Geschichte)
- ``charakter``  — NPC
- ``gegenstand`` — Gegenstands-Vorlage
- ``ort`` / ``event`` / ``fraktion`` — Welt-Entitäten
- ``verbindung`` — VERBINDUNG zwischen zwei Entitäten

Die Prompts und Ausgabe-Schemata stehen bewusst hier und nicht im Frontend:
damit hat nur eine Stelle Kontrolle darüber, was Gemini als Auftrag bekommt,
und das Frontend reicht nur den freien Wunsch des Spielleiters durch.
"""

import json
import logging
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.auth.dependencies import require_campaign_gm
from app.campaigns.repository import get_campaign, get_einstellungen
from app.entities.repository import EVENT_FIELDS, FRAKTION_FIELDS, ORT_FIELDS, PERSON_FIELDS, create_node, get_node
from app.entities.schemas import EventCreate, FraktionCreate, KurzLangEintrag, OrtCreate, PersonCreate
from app.haendler import ki_einkauf
from app.haendler import repository as haendler_repository
from app.hintergruende import repository as hintergruende_repository
from app.items.chrom import CHROM_TYPEN, KOERPERZONEN, STUFEN as CHROM_STUFEN, preis_fuer as chrom_preis_fuer, stufe_fuer_name, verlust_fuer as chrom_verlust_fuer
from app.items.repository import assign_copy, assign_owner, create_gegenstand
from app.items.routes import _create_data, _default_sichtbarkeit
from app.items.schemas import GEGENSTAND_TYPEN, GegenstandCreate
from app.items.waffenbonus import ki_schaden_roh, schaden_art_fuer_waffe, schaden_klemmen, waffenfelder
from app.ki.bildgenerierung import BildgenerierungFehler, generiere_bild
from app.ki.client import KiFehler, generiere_json, generiere_text
from app.ki import beratung as beratung_repo
from app.ki import massenjobs
from app.ereignisprotokoll import hooks
from app.ki.kontext import sammle_kontext, sammle_verbindungstypen_text
from app.ki.wiki_pruefung import (
    SweepAntwort,
    UebernehmenAntwort,
    pruefe_freitext,
    pruefe_seite,
    sweep,
    uebernehmen_befund,
)
from app.ki.auto_verknuepfung import (
    AnwendenErgebnis,
    BeziehungAnwendenErgebnis,
    BeziehungAnwendenInput,
    SweepVorschlaegeAntwort,
    VerknuepfungsVorschlag,
    VorschlaegeAntwort,
    anwenden as verknuepfung_anwenden,
    beziehung_anwenden as verknuepfung_beziehung_anwenden,
    beziehungsvorschlaege_aus_beschreibungen,
    sweep as verknuepfung_sweep,
    vorschlaege as verknuepfung_vorschlaege,
    vorschlaege_fuer_text as verknuepfung_vorschlaege_fuer_text,
)
from app.ki.verbindungs_normalisierung import (
    NormalisierungAnwendenErgebnis,
    NormalisierungAnwendenInput,
    NormalisierungsVorschlaegeAntwort,
    anwenden as verbindungstypen_anwenden,
    vorschlaege as verbindungstypen_vorschlaege,
)
from app.ki.wiki_import import (
    DokumentFormatFehler,
    DokumentZuGrossFehler,
    ERLAUBTE_ENDUNGEN,
    ImportAntwort,
    importiere as wiki_importiere,
)
from app.rassen import repository as rassen_repository
from app.regeln.vorlagen import archetyp_namen, nur_archetyp
from app.traits import erstellung
from app.traits.repository import list_catalog, set_rating, set_ratings_bulk, setze_maxima_bulk
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

_BERATUNG_SYSTEM = (
    _SYSTEM
    + " Du BERÄTST die Spielleitung: denkst mit, stellst Rückfragen, skizzierst "
    "Optionen. Du legst nichts in der Welt an. Nur die folgende freigegebene "
    "Kampagne ist Kanon — alles, was nur in diesem Gespräch vorkommt, ist eine "
    "unverbindliche Skizze, bis die Spielleitung daraus einen Entwurf macht. "
    "Erfinde keine Fakten über bestehende Entitäten, die nicht im Kanon stehen. "
    "Neue Ideen klar als Vorschlag kennzeichnen, nicht als etabliert. "
    "Antworten auf Deutsch, knapp und brauchbar. "
    "Bleib beim gestellten Thema: beantworte genau das, wonach gefragt wurde, "
    "und schweife nicht von dir aus in andere Richtungen ab. Wird z.B. nach "
    "einer Farbe für einen Gegenstand gefragt, gib eine Farbe (oder wenige "
    "Optionen dazu) — keine ungefragten Vorschläge für Plots, Hintergrundgeschichten "
    "oder andere Themen, in denen der Gegenstand vorkommen könnte. Erweitere den "
    "Rahmen der Antwort nur, wenn die Frage selbst offen oder vage gestellt ist, "
    "oder wenn die Spielleitung ausdrücklich nach mehr fragt."
)

_STORY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "titel": {"type": "STRING"},
        "inhalt": {"type": "STRING"},
    },
    "required": ["titel", "inhalt"],
}

# Für traitBoni (Bonus auf einen BESTEHENDEN Katalog-Trait) und
# neueFertigkeiten (komplett neue Fertigkeit) an KI-Gegenständen — "wert"
# meint hier Bonuswürfel/Fertigkeitshöhe (Mark-Bug 11.10.2026: ein
# Cyberware-Implantat mit "+1 auf Schusswaffen" landete nur im
# Beschreibungstext, weil es dafür überhaupt kein strukturiertes
# Ausgabefeld gab). Die Charaktererstellung braucht dieses {name,wert}-
# Muster seit der stufenweisen KI-Erstellung (13.10.2026) nicht mehr — dort
# liefert die KI nur noch Namens-Reihenfolgen, keine Punktwerte mehr.
_TRAIT_BONUS_EINTRAG = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "wert": {"type": "INTEGER"},
    },
    "required": ["name", "wert"],
}

def _charakter_konzept_schema(rassen_namen: list[str], archetypen: list[str] | None = None) -> dict:
    """Schema für Stufe 1 (13.10.2026, siehe erstellung.py::ki_konzept_text):
    Konzept-Text plus Rasse/Weg/Paket als echte Enums (kein Erfinden mehr
    möglich) und reine Prioritäts-Reihenfolgen statt Rohzahlen — die KI kann
    hier strukturell keine Arithmetik mehr falsch machen, weil es keine
    einzige Zahl zu liefern gibt.

    ambition und verlangen sind dasselbe Muster: nur ein Name aus den
    lokalen Archetyp-Vorlagen, nie freier Text. Fehlt die Vorlagendatei,
    gibt es die Felder gar nicht — der Server speichert dann leer.
    """
    def _attribut_rangfolge(namen: list[str]) -> dict:
        return {"type": "ARRAY", "items": {"type": "STRING", "enum": namen}}

    schema = {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"},
            "beschreibung": {"type": "STRING"},
            # SL-internes Notizfeld — siehe _NOTIZEN_HINWEIS.
            "notizen": {"type": "STRING"},
            # Kopfzeile des Papierblatts — reiner Text, keine Regelmechanik.
            "konzept": {"type": "STRING"},
            "alter": {"type": "STRING"},
            "ziel": {"type": "STRING"},
            "rasse": {"type": "STRING", "enum": rassen_namen},
            "weg": {"type": "STRING", "enum": ["KEINER", "MAGIER", "NEUROWEAVER", "HAERETIKER"]},
            "fertigkeitsPaket": {"type": "STRING", "enum": list(erstellung.FERTIGKEITS_PAKETE.keys())},
            # Reihenfolge statt Zahlen — der Server verteilt das Kontingent
            # der gewählten Rasse danach (erstellung.schwerpunkte_aus_rangfolge).
            "kategorienReihenfolge": {
                "type": "ARRAY",
                "items": {"type": "STRING", "enum": erstellung.ATTRIBUT_KATEGORIEN},
            },
            "attributReihenfolgeKoerperlich": _attribut_rangfolge(
                erstellung.ATTRIBUTE_JE_KATEGORIE["AttributKörperlich"]
            ),
            "attributReihenfolgeGesellschaftlich": _attribut_rangfolge(
                erstellung.ATTRIBUTE_JE_KATEGORIE["AttributGesellschaftlich"]
            ),
            "attributReihenfolgeGeistig": _attribut_rangfolge(
                erstellung.ATTRIBUTE_JE_KATEGORIE["AttributGeistig"]
            ),
        },
        "required": [
            "name", "beschreibung", "notizen", "konzept", "rasse", "weg",
            "fertigkeitsPaket", "kategorienReihenfolge",
            "attributReihenfolgeKoerperlich", "attributReihenfolgeGesellschaftlich",
            "attributReihenfolgeGeistig",
        ],
    }
    if archetypen:
        schema["properties"]["ambition"] = {"type": "STRING", "enum": list(archetypen)}
        schema["properties"]["verlangen"] = {"type": "STRING", "enum": list(archetypen)}
        schema["required"].extend(["ambition", "verlangen"])
    return schema


def _charakter_fertigkeiten_schema(
    erlaubte_fertigkeiten: list[str],
    hintergrund_pool: list[str],
    freebee_ziele: list[str],
    braucht_magie_bonus_feld: bool,
) -> dict:
    """Schema für Stufe 2: Fertigkeiten/Hintergründe/Freebees — wieder nur
    Namen/Reihenfolgen plus die zwei Geld-Freebee-Anzahlen (kleine, risikoarme
    Ganzzahlen). Die exakte Fertigkeiten-Verteilung, die Hintergrund-Summe und
    das Freebee-Budget rechnet ausschließlich der Server aus."""
    schema = {
        "type": "OBJECT",
        "properties": {
            "fertigkeitenReihenfolge": {
                "type": "ARRAY",
                "items": {"type": "STRING", "enum": erlaubte_fertigkeiten},
            },
            "hintergruendeReihenfolge": {
                "type": "ARRAY",
                "items": {"type": "STRING", "enum": hintergrund_pool},
            },
            "freebeeKredit": {"type": "INTEGER"},
            "freebeeEigenkapital": {"type": "INTEGER"},
            "freebeeZielReihenfolge": {
                "type": "ARRAY",
                "items": {"type": "STRING", "enum": freebee_ziele},
            },
        },
        "required": [
            "fertigkeitenReihenfolge", "hintergruendeReihenfolge",
            "freebeeKredit", "freebeeEigenkapital", "freebeeZielReihenfolge",
        ],
    }
    if braucht_magie_bonus_feld:
        schema["properties"]["magieBonusNutzen"] = {"type": "BOOLEAN"}
        schema["required"].append("magieBonusNutzen")
    return schema

_GEGENSTAND_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "beschreibung": {"type": "STRING"},
        # SL-internes Notizfeld — siehe _NOTIZEN_HINWEIS.
        "notizen": {"type": "STRING"},
        "typ": {"type": "STRING", "enum": GEGENSTAND_TYPEN},
        "preis": {"type": "INTEGER"},
        # Seltenheit 1 (überall verfügbar) bis 5 (Speziallabor/Schwarzmarkt) —
        # Grundlage für die automatische Shop-Bestückung (docs/api/haendler.md).
        "seltenheit": {"type": "INTEGER"},
        # Schaden 1–12, nur bei typ Waffe. Kachel und Kampf lesen kraft;
        # ohne dieses Feld blieb jede KI-Waffe auf 0.
        "schaden": {"type": "INTEGER"},
        "schadenArt": {"type": "STRING", "enum": ["", "schlag", "schwer", "aggraviert"]},
        # Bonus auf einen BESTEHENDEN Katalog-Trait, solange ausgerüstet/
        # verbaut (Cyberware/Bioware/Hexware/magische Gegenstände — z.B.
        # "+1 auf Schusswaffen"). Ohne dieses Feld landete so ein Effekt nur
        # im Beschreibungstext, nie als echte Mechanik (Mark-Bug 11.10.2026).
        "traitBoni": {"type": "ARRAY", "items": _TRAIT_BONUS_EINTRAG},
        # Komplett NEUE Fertigkeit, die es ohne den Gegenstand nicht gibt
        # (z.B. ein NeuroWeaving-Skill an einem Cyberdeck) — anderer
        # Mechanismus als traitBoni, siehe items/schemas.py::ausruestungsfertigkeiten.
        "neueFertigkeiten": {"type": "ARRAY", "items": _TRAIT_BONUS_EINTRAG},
        # NUR bei typ Cyberware/Bioware/Hexware: welche Qualität der Einbau hat.
        # Bestimmt serverseitig automatisch preis und wVerlust nach der Formel
        # in items/chrom.py — das hier eingetragene preis-Feld wird für diese
        # drei Typen ignoriert. Leer bei jedem anderen Typ.
        "qualitaetsstufe": {"type": "STRING", "enum": [""] + [s.name for s in CHROM_STUFEN]},
        # Welche Körperzone das Implantat belegt (nur Cyberware/Bioware/
        # Hexware). Leer = noch offen, SL entscheidet später.
        "koerperzone": {"type": "STRING", "enum": [""] + KOERPERZONEN},
        # Ist der Gegenstand ZUSÄTZLICH eine Waffe, obwohl typ nicht Waffe ist
        # (ausfahrbare Cyberklinge, Kraftarm-Faustschlag, Gift-Zahnimplantat, ...)?
        # Dann zählt schaden zusätzlich zum Bonus für die Qualitätsstufen-Formel.
        # Bei typ Waffe wird dieses Feld ignoriert (dort gilt es immer).
        "istWaffe": {"type": "BOOLEAN"},
    },
    "required": ["name", "beschreibung", "notizen", "typ", "preis", "seltenheit", "schaden"],
}

_WELT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "beschreibung": {"type": "STRING"},
        # SL-internes Notizfeld — siehe _NOTIZEN_HINWEIS.
        "notizen": {"type": "STRING"},
    },
    "required": ["name", "beschreibung", "notizen"],
}

_EVENT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "titel": {"type": "STRING"},
        "beschreibung": {"type": "STRING"},
        # SL-internes Notizfeld — siehe _NOTIZEN_HINWEIS.
        "notizen": {"type": "STRING"},
        "timestamp": {"type": "STRING"},
    },
    "required": ["titel", "beschreibung", "notizen"],
}

_KURZ_LANG_ITEM = {
    "type": "OBJECT",
    "properties": {
        "titel": {"type": "STRING"},
        "beschreibung": {"type": "STRING"},
    },
    "required": ["titel"],
}

_FRAKTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "beschreibung": {"type": "STRING"},
        # SL-internes Notizfeld — siehe _NOTIZEN_HINWEIS.
        "notizen": {"type": "STRING"},
        "ziele": {"type": "ARRAY", "items": _KURZ_LANG_ITEM},
        "ressourcen": {"type": "ARRAY", "items": _KURZ_LANG_ITEM},
    },
    "required": ["name", "beschreibung", "notizen"],
}

_VERBINDUNG_TYPEN = ("Person", "Ort", "Event", "Fraktion")

_VERBINDUNG_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "vonName": {"type": "STRING"},
        "vonTyp": {"type": "STRING", "enum": list(_VERBINDUNG_TYPEN)},
        "zuName": {"type": "STRING"},
        "zuTyp": {"type": "STRING", "enum": list(_VERBINDUNG_TYPEN)},
        "typ": {"type": "STRING"},
        "beschreibung": {"type": "STRING"},
    },
    "required": ["vonName", "vonTyp", "zuName", "zuTyp", "typ"],
}

# Trennt, was im Spiel sichtbar ist (beschreibung), von dem, was nur die SL
# sieht (notizen) — Mark empfand die generierten Entwürfe als zu knapp: die
# knackige Zusammenfassung kam gut an, aber Details aus dem Wunsch/Gespräch
# gingen verloren, weil es dafür kein Zielfeld gab (01.10.2026).
_NOTIZEN_HINWEIS = (
    " beschreibung bleibt eine knackige, kurze Zusammenfassung — das, was im "
    "Spiel sichtbar oder vorlesbar wäre. notizen ist das SL-interne Notizfeld: "
    "dort kommt ALLES rein, was im Wunsch/Gespräch an Details steckt und nicht "
    "in die knappe beschreibung passt — Hintergründe, Zahlen, Motive, "
    "Beziehungen, lose Ideen, offene Fragen. Lieber ausführlich als knapp; "
    "nichts Erwähntes soll verloren gehen."
)

_ORT_SYSTEM = (
    _SYSTEM
    + " Erschaffe einen einzelnen Ort in NeotopiA. name ist der Eigenname, "
    "beschreibung was man dort sieht, hört, riecht — kein Abenteuerplot."
    + _NOTIZEN_HINWEIS
)

_EVENT_SYSTEM = (
    _SYSTEM
    + " Erschaffe ein einzelnes Ereignis/eine Szene in NeotopiA. titel ist der "
    "Name, beschreibung was passiert ist oder passieren wird. timestamp nur "
    "setzen, wenn der Wunsch ein Datum/eine Uhrzeit vorgibt, sonst leer."
    + _NOTIZEN_HINWEIS
)

_FRAKTION_SYSTEM = (
    _SYSTEM
    + " Erschaffe eine einzelne Fraktion/Organisation in NeotopiA. name, "
    "beschreibung (was die Spielwelt über sie weiß). ziele und ressourcen "
    "sind kurze Listen mit titel + beschreibung — typisch 1–4 Einträge, "
    "keine Romane."
    + _NOTIZEN_HINWEIS
)

_VERBINDUNG_SYSTEM = (
    _SYSTEM
    + " Lege EINE Beziehung zwischen zwei Entitäten. vonTyp/zuTyp nur "
    "Person, Ort, Event oder Fraktion. Bevorzuge Namen aus der "
    "freigegebenen Welt; nur wenn wirklich nichts passt, neue Namen. "
    "typ ist die kurze Kantenbezeichnung (kennt, besitzt, feindet, …) — "
    "MAXIMAL 5 Wörter, je kürzer desto besser. Passt einer der bereits "
    "verwendeten Beziehungstypen (siehe unten), verwende ihn EXAKT statt "
    "eine eigene Formulierung für dasselbe Konzept zu erfinden; nur wenn "
    "wirklich keiner passt, einen neuen kurzen Typ prägen."
)


def _kurz_lang(roh) -> list[KurzLangEintrag]:
    """Ziele/Ressourcen der KI in KurzLangEintrag-Form."""
    if not isinstance(roh, list):
        return []
    out: list[KurzLangEintrag] = []
    for eintrag in roh:
        if not isinstance(eintrag, dict):
            continue
        titel = (eintrag.get("titel") or "").strip()
        if not titel:
            continue
        out.append(KurzLangEintrag(titel=titel, beschreibung=(eintrag.get("beschreibung") or "").strip()))
    return out


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
    "(nur Speziallabor/Schwarzmarkt). schaden: ganze Zahl. Bei typ "
    "Waffe Pflicht, 1 bis 12, nie 0 und nie ein Würfelausdruck (kein W6, kein "
    "Stärke-plus-X — nur die Stufe aus dem Regelwerk): 1 Schlagring, 2 Dolch, "
    "3 Schwert oder leichte Pistole, 4 schwere Pistole, Monofilament-Peitsche "
    "oder Gewehr, 5 Scharfschützengewehr, 6 MiniGun, 7 Raketenwerfer, "
    "8–12 nur Schiffswaffen (Raumschiff/Bordgeschütz). Ein "
    "Aufpreis für Tarnung, Smartlink oder Prototyp hebt die Stufe nicht. "
    "Bei jedem anderen Typ 0. schadenArt bei typ Waffe: schlag, schwer oder aggraviert "
    "(Schlag / Tödlich / Schwerheilbar). Fehlt sie, gilt Tödlich. Faust und Knüppel schlag, "
    "Klinge und Schusswaffe schwer, Explosion oder Brand aggraviert. Sonst leer. "
    "Gibt der Gegenstand im ausgerüsteten/verbauten Zustand einen Bonus auf eine "
    "BESTEHENDE Fertigkeit, ein Attribut oder eine Sphäre (typisch bei Cyberware/"
    "Bioware/Hexware und magischen Gegenständen, z.B. ein Reflex-Implantat mit "
    "+1 auf Schusswaffen, ein Kraftarm mit +2 auf Körperkraft) — das IMMER in "
    "traitBoni eintragen, nie nur in beschreibung/notizen erwähnen: name MUSS "
    "exakt einer der Namen aus dem unten mitgelieferten Fertigkeiten/Attribute/"
    "Sphären-Katalog sein (nicht übersetzen, nicht abkürzen, nicht erfinden), "
    "wert die Zahl der Bonuswürfel. Erschafft der Gegenstand stattdessen eine "
    "komplett NEUE Fertigkeit, die es ohne ihn gar nicht gibt (z.B. ein "
    "NeuroWeaving-Skill an einem Cyberdeck), trage das in neueFertigkeiten ein "
    "(name frei wählbar, wert die Fertigkeitshöhe). Ohne mechanischen Effekt "
    "bleiben traitBoni und neueFertigkeiten leere Listen. "
    "NUR bei typ Cyberware, Bioware oder Hexware zusätzlich: qualitaetsstufe "
    "nach der Qualität, die der Wunsch/die Beschreibung nahelegt — Hinterhof "
    "(billig und improvisiert zusammengeschustert, Baustellen-Doc), Straße "
    "(solide Ware ohne Anspruch), Klinik (ordentlich verbaut, halbwegs "
    "verträglich), Konzern (teure, saubere Arbeit) oder Maßanfertigung (das "
    "Beste, was Geld kaufen kann). Deutet nichts im Wunsch auf eine bestimmte "
    "Qualität hin, setze Straße. Das preis-Feld wird für diese drei Typen "
    "serverseitig aus Bonus und Qualitätsstufe berechnet und ignoriert — "
    "trotzdem eine plausible Zahl eintragen. koerperzone nur hier setzen, "
    "wenn der Wunsch eine bestimmte Körperzone nahelegt (Kopf, Arme, Torso, "
    "Beine), sonst leer lassen. Hat das Implantat selbst eine Waffenfunktion "
    "(ausfahrbare Klinge, Kraftarm-Faustschlag, Gift-Zahnimplantat, ...), "
    "setze istWaffe auf true und schaden/schadenArt wie bei typ Waffe — sonst "
    "bleibt istWaffe false. Bei jedem anderen Typ bleiben qualitaetsstufe und "
    "koerperzone leer und istWaffe false."
    + _NOTIZEN_HINWEIS
)

# Erklärt die Kopfzeilen-Begriffe, damit Gemini nicht rät, was „Ambition"
# von „Verlangen" unterscheidet. Stufe 1 von 2 (siehe erstellung.py::
# ki_konzept_text) — reiner Konzept-/Auswahl-Teil, keine Zahlen mehr hier.
_CHARAKTER_KONZEPT_SYSTEM = (
    _SYSTEM
    + " Erschaffe stimmige NPCs. Die Kopfzeile: konzept (kurze Rollenbeschreibung), "
    "alter, ziel (das konkrete nächste Vorhaben). "
    "ambition (langfristiges Wollen) und verlangen (innerer Antrieb) sind keine "
    "freien Texte: je genau ein Archetyp-Name aus dem Schema, exakt so, zwei "
    "verschiedene, nie eine eigene Formulierung und nie einen Erklärungstext."
    + _NOTIZEN_HINWEIS
)

# Stufe 2 von 2: Fertigkeiten/Hintergründe/Freebees — reine Namens-
# Priorisierung, die exakten Zahlen baut der Server (siehe _idee_anlegen).
_CHARAKTER_FERTIGKEITEN_SYSTEM = (
    _SYSTEM
    + " Du vervollständigst einen bereits begonnenen Charakterbogen: welche "
    "Fertigkeiten beherrscht die Figur am besten, welche Hintergründe passen "
    "zu ihr, und wie setzt sie ihr restliches Startkapital (Freebees) ein. "
    "Nenne ausschließlich Namen in Prioritätsreihenfolge (wichtigstes zuerst) "
    "— keine Zahlen, keine Punktewerte, das übernimmt der Server."
)


# Dieselben Typen für ✨-Idee und „Entwurf aus Beratung“ — alles, was die
# Schmiede (plus Verbindungen) anlegen kann.
KiIdeeTyp = Literal["story", "charakter", "gegenstand", "ort", "event", "fraktion", "verbindung"]


class KiIdeeInput(BaseModel):
    typ: KiIdeeTyp
    prompt: str


class BeratungNachrichtInput(BaseModel):
    text: str
    # Überschreibt für diese eine Nachricht den Kampagnen-Standard —
    # Dropdown im Beratungs-Popup, für den direkten A/B-Vergleich innerhalb
    # eines Gesprächs. None/"" lässt die Kampagnen-Einstellung gelten.
    provider: str | None = None


class BeratungEntwurfInput(BaseModel):
    typ: KiIdeeTyp


class UebernehmenInput(BaseModel):
    zitat: str
    vorschlag: str


class ObjektTextInput(BaseModel):
    """Für den ✨ KI-Knopf neben „SL-geheim“ an Beschreibung/Notizen-Feldern."""

    objektTyp: str
    objektName: str
    # Bisheriger Text des Feldes (reiner Text, vom Frontend per editor.getText()
    # geholt) — gibt der KI Anschluss an das, was schon dasteht.
    bisherigerText: str = ""
    prompt: str


class BildPromptInput(BaseModel):
    """Für den 'KI-Bild generieren'-Knopf an Personen-/Orts-/Gegenstands-Bildern."""

    objektTyp: str
    objektName: str
    bisherigeBeschreibung: str = ""
    notizen: str = ""


class BildGenerierenInput(BaseModel):
    """Provider je Aufruf wählbar (Commlink-Popup-Dropdown), anders als der
    Text-Provider (KI_PROVIDER in .env) — siehe app/ki/bildgenerierung.py."""

    provider: Literal["lokal", "cloud"]
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


def _name_wert_dict(roh) -> dict[str, int]:
    """KI-Listen aus {name, wert}-Einträgen (traitBoni/neueFertigkeiten) zu
    einem flachen dict, wie GegenstandCreate es erwartet."""
    if not isinstance(roh, list):
        return {}
    out: dict[str, int] = {}
    for eintrag in roh:
        if not isinstance(eintrag, dict):
            continue
        name = (eintrag.get("name") or "").strip()
        if not name:
            continue
        out[name] = _als_int(eintrag.get("wert"))
    return out


def _trait_boni_aus_ki(roh, katalog: list[dict]) -> dict[str, int]:
    """Nur Bonuswürfel auf tatsächlich existierende Katalog-Traits übernehmen.

    Die KI soll laut Prompt nur Katalog-Namen verwenden, hält sich aber nicht
    immer daran (vgl. _setze_traits bei der Charaktererstellung) — ein
    erfundener oder falsch geschriebener Name würfe sonst einen
    stillschweigend wirkungslosen traitBoni-Eintrag in die DB.
    """
    gueltige_namen = {t["name"] for t in katalog}
    return {
        name: wert
        for name, wert in _name_wert_dict(roh).items()
        if name in gueltige_namen and wert != 0
    }


def _chrom_felder_aus_ki(
    gegenstand_typ: str, ergebnis: dict, trait_boni: dict[str, int], ausr_fert: dict[str, int],
) -> dict:
    """preis/kraft/wVerlust/koerperzone/istWaffe/schaden für ein KI-Chrom-Item.

    Nur für Cyberware/Bioware/Hexware (siehe items/chrom.py::CHROM_TYPEN) —
    die KI wählt per Prompt nur noch die Qualitätsstufe passend zur
    Beschreibung (Hinterhof..Maßanfertigung), Preis und Willenskraft-Verlust
    errechnen sich daraus und aus dem Gesamtbonus — dieselbe Formel, die auch
    das manuelle Anlegen im Charakterbogen nutzt (Mark-Wunsch 12.10.2026: der
    Gegenstand soll vollständig erstellt werden, nicht erst manuell durch die
    SL vervollständigt).
    """
    if gegenstand_typ not in CHROM_TYPEN:
        return {}
    ist_waffe = bool(ergebnis.get("istWaffe"))
    schaden = schaden_klemmen(ergebnis.get("schaden"), typ="Waffe") if ist_waffe else 0
    schaden_art = schaden_art_fuer_waffe(ergebnis.get("schadenArt")) if ist_waffe else ""
    bonus = max(1, sum(trait_boni.values()) + sum(ausr_fert.values()) + schaden)
    stufe = stufe_fuer_name(ergebnis.get("qualitaetsstufe"))
    koerperzone = (ergebnis.get("koerperzone") or "").strip()
    if koerperzone not in KOERPERZONEN:
        koerperzone = ""
    return {
        "preis": chrom_preis_fuer(bonus, stufe.preis_je_bonus),
        "kraft": bonus,
        "wVerlust": chrom_verlust_fuer(bonus, stufe.preis_je_bonus),
        "koerperzone": koerperzone,
        "istWaffe": ist_waffe,
        "schaden": schaden,
        "schadenArt": schaden_art,
    }


# Attribute (Körperkraft, Entschlossenheit, ...) sind fundamental — 0 ist
# regeltechnisch nicht vorgesehen, jeder Charakter hat mindestens 1 in jedem.
# Fertigkeiten/Hintergründe dürfen dagegen 0 sein ("kann's einfach nicht").
_ATTRIBUT_MINDESTWERT = 1


def _rassen_fuer_ki(liste: list[dict]) -> dict[str, dict]:
    """Freigegebene Kampagnen-Rassen im Format von erstellung.pruefe()."""
    if not liste:
        return erstellung.RASSEN
    return {
        r["name"]: {
            "modifikatoren": r.get("modifikatoren") or {},
            "freiePunkte": r.get("freiePunkte") or [],
            "bonusFreebees": r.get("bonusFreebees") or 0,
            "gratisFertigkeitName": r.get("gratisFertigkeitName") or "",
            "gratisFertigkeitBonus": r.get("gratisFertigkeitBonus") or 0,
            "kannKredithai": r.get("kannKredithai") or False,
        }
        for r in liste
    }


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
    return await _idee_anlegen(campaign_id, body.typ, prompt)


async def _idee_anlegen(campaign_id: str, typ: str, prompt: str) -> dict:
    """Gemeinsamer Anlege-Pfad für ✨ KI und für „Entwurf aus Beratung“."""
    try:
        if typ == "story":
            kontext = await sammle_kontext(campaign_id)
            prompt_komplett = _mit_kontext(prompt, kontext)
            ergebnis = await generiere_json(prompt_komplett, _SYSTEM, _STORY_SCHEMA, campaign_id=campaign_id)
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
            await hooks.ki(
                campaign_id, anlass="idee-story", prompt=prompt,
                antwort_text=inhalt, uebernommen=True, betrifft_id=seite["id"],
            )
            return {"typ": "story", "id": seite["id"], "name": titel}

        if typ == "gegenstand":
            # Bevorzugt Bestehendes wiederverwenden, nur bei echter Lücke
            # etwas Neues erfinden — dasselbe Vorrang-Prinzip wie bei Story/
            # Charakter (_mit_kontext), Marks Entscheidung 22.09.2026: "beides,
            # bevorzugt Bestehendes wiederverwenden, nur bei Lücken etwas
            # Neues vorschlagen".
            kontext = await sammle_kontext(campaign_id)
            # Trait-Katalog wie bei der Charaktererstellung (_katalog_zu_text)
            # — ohne die exakten Namen würde die KI für traitBoni Fertigkeiten
            # erfinden/übersetzen statt bestehende zu treffen (z.B. "Feuerwaffen"
            # statt "Schusswaffen"), und der Bonus bliebe wirkungslos.
            campaign = await get_campaign(campaign_id)
            ruleset = campaign["ruleset"] if campaign else "neotopia"
            katalog = await list_catalog(ruleset)
            prompt_komplett = _mit_kontext(prompt, kontext)
            prompt_komplett += (
                "\n\nFertigkeiten/Attribute/Sphären-Katalog dieser Kampagne "
                "(NUR für traitBoni — exakte Namen übernehmen, nichts erfinden):\n"
                + await _katalog_zu_text(ruleset) + "\n"
            )
            ergebnis = await generiere_json(prompt_komplett, _GEGENSTAND_SYSTEM, _GEGENSTAND_SCHEMA, campaign_id=campaign_id)
            name = (ergebnis.get("name") or "").strip() or "Unbenannter Gegenstand"
            gegenstand_typ = ergebnis.get("typ") or "Sonstiges"
            if gegenstand_typ not in GEGENSTAND_TYPEN:
                # Die KI hat trotz Enum-Vorgabe daneben gegriffen — der Typ
                # ist nach dem Anlegen fix (schemas.py), deshalb hier ein
                # harter Fallback statt eines ungültigen/erfundenen Werts.
                gegenstand_typ = "Sonstiges"
            seltenheit = max(1, min(_als_int(ergebnis.get("seltenheit"), 1), 5))
            trait_boni = _trait_boni_aus_ki(ergebnis.get("traitBoni"), katalog)
            ausr_fert = _name_wert_dict(ergebnis.get("neueFertigkeiten"))
            # Cyberware/Bioware/Hexware: Preis/Kraft/WK-Verlust/Waffenfunktion
            # kommen aus der Qualitätsstufen-Formel statt direkt von der KI
            # (siehe _chrom_felder_aus_ki); jeder andere Typ nutzt wie bisher
            # waffenfelder() (nur bei typ Waffe, sonst leer).
            sonderfelder = _chrom_felder_aus_ki(gegenstand_typ, ergebnis, trait_boni, ausr_fert) or (
                waffenfelder(gegenstand_typ, ki_schaden_roh(ergebnis), ergebnis.get("schadenArt"))
            )
            # preis kommt bei Chrom-Typen aus sonderfelder (Qualitätsstufen-
            # Formel) statt direkt von der KI — sonst gäbe es das Keyword
            # doppelt an GegenstandCreate.
            preis = sonderfelder.pop("preis", max(0, _als_int(ergebnis.get("preis"))))
            gegenstand_body = GegenstandCreate(
                name=name,
                description=(ergebnis.get("beschreibung") or "").strip(),
                notes=(ergebnis.get("notizen") or "").strip(),
                typ=gegenstand_typ,
                preis=preis,
                seltenheit=seltenheit,
                istEntwurf=True,
                # Bonuswürfel auf bestehende Traits (z.B. Cyberware +1
                # Schusswaffen) — ohne das landete der Effekt nur im
                # Beschreibungstext, nie als echte Spielmechanik
                # (Mark-Bug 11.10.2026, siehe items/schemas.py::traitBoni).
                traitBoni=trait_boni,
                ausruestungsfertigkeiten=ausr_fert,
                **sonderfelder,
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
            await hooks.ki(
                campaign_id, anlass="idee-gegenstand", prompt=prompt,
                antwort_text=name, uebernommen=True, betrifft_id=gegenstand["id"],
            )
            return {"typ": "gegenstand", "id": gegenstand["id"], "name": name}

        if typ == "ort":
            kontext = await sammle_kontext(campaign_id)
            ergebnis = await generiere_json(_mit_kontext(prompt, kontext), _ORT_SYSTEM, _WELT_SCHEMA, campaign_id=campaign_id)
            name = (ergebnis.get("name") or "").strip() or "Unbenannter Ort"
            node = await create_node(
                "Ort",
                ORT_FIELDS,
                campaign_id,
                OrtCreate(
                    name=name,
                    description=(ergebnis.get("beschreibung") or "").strip(),
                    notes=(ergebnis.get("notizen") or "").strip(),
                    istEntwurf=True,
                    sichtbarkeit="GM",
                ).model_dump(),
            )
            await hooks.ki(
                campaign_id, anlass="idee-ort", prompt=prompt,
                antwort_text=name, uebernommen=True, betrifft_id=node["id"],
            )
            return {"typ": "ort", "id": node["id"], "name": name}

        if typ == "event":
            kontext = await sammle_kontext(campaign_id)
            ergebnis = await generiere_json(_mit_kontext(prompt, kontext), _EVENT_SYSTEM, _EVENT_SCHEMA, campaign_id=campaign_id)
            titel = (ergebnis.get("titel") or "").strip() or "Unbenanntes Ereignis"
            node = await create_node(
                "Event",
                EVENT_FIELDS,
                campaign_id,
                EventCreate(
                    title=titel,
                    timestamp=(ergebnis.get("timestamp") or "").strip(),
                    description=(ergebnis.get("beschreibung") or "").strip(),
                    notes=(ergebnis.get("notizen") or "").strip(),
                    istEntwurf=True,
                    sichtbarkeit="GM",
                ).model_dump(),
            )
            await hooks.ki(
                campaign_id, anlass="idee-event", prompt=prompt,
                antwort_text=titel, uebernommen=True, betrifft_id=node["id"],
            )
            return {"typ": "event", "id": node["id"], "name": titel}

        if typ == "fraktion":
            kontext = await sammle_kontext(campaign_id)
            ergebnis = await generiere_json(_mit_kontext(prompt, kontext), _FRAKTION_SYSTEM, _FRAKTION_SCHEMA, campaign_id=campaign_id)
            name = (ergebnis.get("name") or "").strip() or "Unbenannte Fraktion"
            node = await create_node(
                "Fraktion",
                FRAKTION_FIELDS,
                campaign_id,
                FraktionCreate(
                    name=name,
                    description=(ergebnis.get("beschreibung") or "").strip(),
                    notes=(ergebnis.get("notizen") or "").strip(),
                    ziele=_kurz_lang(ergebnis.get("ziele")),
                    ressourcen=_kurz_lang(ergebnis.get("ressourcen")),
                    istEntwurf=True,
                    sichtbarkeit="GM",
                ).model_dump(),
            )
            await hooks.ki(
                campaign_id, anlass="idee-fraktion", prompt=prompt,
                antwort_text=name, uebernommen=True, betrifft_id=node["id"],
            )
            return {"typ": "fraktion", "id": node["id"], "name": name}

        if typ == "verbindung":
            kontext = await sammle_kontext(campaign_id)
            typen_text = await sammle_verbindungstypen_text(campaign_id)
            prompt_mit_typen = (
                f"{prompt}\n\nBereits verwendete Beziehungstypen dieser Kampagne: {typen_text}"
            )
            ergebnis = await generiere_json(
                _mit_kontext(prompt_mit_typen, kontext), _VERBINDUNG_SYSTEM, _VERBINDUNG_SCHEMA, campaign_id=campaign_id
            )
            von_typ = ergebnis.get("vonTyp") or ""
            zu_typ = ergebnis.get("zuTyp") or ""
            von_name = (ergebnis.get("vonName") or "").strip()
            zu_name = (ergebnis.get("zuName") or "").strip()
            kanten_typ = (ergebnis.get("typ") or "").strip()
            if von_typ not in _VERBINDUNG_TYPEN or zu_typ not in _VERBINDUNG_TYPEN or not von_name or not zu_name or not kanten_typ:
                raise HTTPException(
                    status_code=422,
                    detail="Die KI hat keine gültige Verbindung geliefert.",
                )
            angelegt = await verknuepfung_beziehung_anwenden(
                campaign_id,
                BeziehungAnwendenInput(
                    typ1=von_typ,
                    name1=von_name,
                    typ2=zu_typ,
                    name2=zu_name,
                    beziehungstyp=kanten_typ,
                    beschreibung=(ergebnis.get("beschreibung") or "").strip(),
                ),
            )
            name = f"{von_name} — {kanten_typ} — {zu_name}"
            await hooks.ki(
                campaign_id, anlass="idee-verbindung", prompt=prompt,
                antwort_text=name, uebernommen=True, betrifft_id=angelegt.verbindungId,
            )
            return {"typ": "verbindung", "id": angelegt.verbindungId, "name": name}

        if typ != "charakter":
            raise HTTPException(status_code=422, detail="Unbekannter Ideen-Typ.")

        # charakter — zweistufiger, deterministischer Ablauf (13.10.2026,
        # Mark: die KI soll die Regeln nicht mehr selbst durchrechnen müssen
        # und dadurch keine Möglichkeit mehr haben, sie zu verletzen). Stufe 1
        # liefert Konzept/Rasse/Weg/Paket plus reine Prioritäten, Stufe 2
        # Fertigkeiten/Hintergründe/Freebee-Wünsche — in beiden Stufen nie
        # eine Zahl, die die KI selbst ausrechnen müsste. Die eigentliche
        # Arithmetik (Kontingente, Paketverteilung, Freebee-Budget) baut der
        # Server deterministisch aus den Prioritäten zusammen, siehe
        # erstellung.py::{schwerpunkte_aus_rangfolge, attributpunkte_aus_rangfolge,
        # fertigkeitpunkte_aus_rangfolge, hintergrundpunkte_aus_rangfolge,
        # freebees_aus_wunsch}. Ergebnis ist dadurch IMMER strukturell
        # regelkonform — kein Nachbesser-Versuch, kein 422 mehr nötig.
        kontext = await sammle_kontext(campaign_id)
        campaign = await get_campaign(campaign_id)
        ruleset = campaign["ruleset"] if campaign else "neotopia"
        katalog = await list_catalog(ruleset)
        rassen = _rassen_fuer_ki(await rassen_repository.liste_fuer_kampagne(campaign_id))
        einstellungen = await get_einstellungen(campaign_id)

        # --- Stufe 1: Konzept, Rasse, Weg, Paket, Attribut-Prioritäten -----
        archetypen = archetyp_namen()
        schema1 = _charakter_konzept_schema(sorted(rassen.keys()), archetypen)
        prompt1 = _mit_kontext(prompt, kontext) + "\n\n" + erstellung.ki_konzept_text(rassen, archetypen)
        konzept = await generiere_json(prompt1, _CHARAKTER_KONZEPT_SYSTEM, schema1, campaign_id=campaign_id)

        rasse_name = (konzept.get("rasse") or "").strip()
        if rasse_name not in rassen:
            rasse_name = next(iter(rassen), "Mensch")
        weg, magie_flavor = erstellung.normalisiere_weg(konzept.get("weg") or "KEINER")
        if weg not in ("KEINER", "MAGIER", "NEUROWEAVER"):
            weg = "KEINER"
            magie_flavor = "MAGIER"
        paket_id = konzept.get("fertigkeitsPaket") or "PROFI"
        if paket_id not in erstellung.FERTIGKEITS_PAKETE:
            paket_id = "PROFI"

        schwerpunkte = erstellung.schwerpunkte_aus_rangfolge(
            rasse_name, konzept.get("kategorienReihenfolge") or [], rassen
        )
        attribut_punkte: dict[str, int] = {}
        for kategorie, feld in (
            ("AttributKörperlich", "attributReihenfolgeKoerperlich"),
            ("AttributGesellschaftlich", "attributReihenfolgeGesellschaftlich"),
            ("AttributGeistig", "attributReihenfolgeGeistig"),
        ):
            attribut_punkte.update(
                erstellung.attributpunkte_aus_rangfolge(
                    kategorie, konzept.get(feld) or [], schwerpunkte.get(kategorie, 0)
                )
            )

        # --- Stufe 2: Fertigkeiten, Hintergründe, Freebees -----------------
        magie_trait = erstellung.MAGIE_TRAIT_JE_WEG.get(weg)
        erlaubte_kategorien = ({"Fertigkeit"} | erstellung.KATEGORIEN_JE_WEG.get(weg, set())) - {
            "Hexkraft", "NeuroWeavingWert",
        }
        erlaubte_fertigkeiten = [t["name"] for t in katalog if t["category"] in erlaubte_kategorien]
        # Derselbe Katalog wie im Baukasten/der echten Erstellung (13.10.2026,
        # Mark: vorher nutzte die KI die alte fest verdrahtete Liste aus
        # erstellung.py und lief damit am Baukasten-Katalog dieser Kampagne
        # vorbei — neu angelegte Hintergründe fehlten der KI, gelöschte bot
        # sie trotzdem an).
        hintergrund_katalog = await hintergruende_repository.pool_fuer_erstellung(campaign_id, einstellungen)
        hintergrund_pool = [h["name"] for h in hintergrund_katalog]
        freebee_ziele = sorted(
            set(erlaubte_fertigkeiten)
            | set(erstellung.ATTRIBUT_NAMEN_ALLE)
            | set(hintergrund_pool)
            | ({magie_trait} if magie_trait else set())
            | {"Willenskraft"}
        )
        braucht_magie_bonus_feld = bool(magie_trait) and paket_id == "PROFI"

        schema2 = _charakter_fertigkeiten_schema(
            erlaubte_fertigkeiten, hintergrund_pool, freebee_ziele, braucht_magie_bonus_feld
        )
        budget = erstellung.FREEBEES_GESAMT + int((rassen.get(rasse_name) or {}).get("bonusFreebees") or 0)
        katalog_beschreibung = {t["name"]: t.get("description") or "" for t in katalog}
        fertigkeiten_zeilen = "\n".join(
            f"- {name}" + (f": {katalog_beschreibung[name]}" if katalog_beschreibung.get(name) else "")
            for name in erlaubte_fertigkeiten
        )
        paket = erstellung.FERTIGKEITS_PAKETE[paket_id]
        slot_anzahl = sum(paket["verteilung"].values())
        prompt2 = (
            f"Figur: {(konzept.get('name') or '').strip() or '(unbenannt)'} — "
            f"Rasse {rasse_name}, Weg {weg}. Konzept: {(konzept.get('konzept') or '').strip() or '(keins)'}.\n\n"
            f"fertigkeitenReihenfolge: Paket {paket_id} verlangt genau {slot_anzahl} Fertigkeiten, "
            "wichtigste zuerst — nur Namen aus dieser Liste (nichts erfinden):\n"
            f"{fertigkeiten_zeilen}\n\n"
            f"hintergruendeReihenfolge: bis zu 4 Hintergründe aus {', '.join(hintergrund_pool)}, "
            "wichtigster zuerst (leer lassen ist auch ok).\n\n"
            f"Freebee-Budget dieser Figur: {budget}. freebeeKredit/freebeeEigenkapital: Anzahl der "
            f"Käufe (nicht Yen, je {erstellung.KAPITAL_JE_FREEBEE}¥, Kredit ist Schulden, "
            "Eigenkapital nicht) — mindestens ein Kauf Geld ist üblich. "
            "freebeeZielReihenfolge: restliche Freebee-Wünsche als Namen in Prioritätsreihenfolge "
            "(Attribute, Fertigkeiten, Hintergründe oder \"Willenskraft\") — reicht das Budget nicht "
            "für alle, werden die hinteren automatisch gestrichen."
        )
        if braucht_magie_bonus_feld:
            prompt2 += (
                f"\n\nmagieBonusNutzen: true, wenn der einzige 1er-Slot des Profi-Pakets statt einer "
                f"Fertigkeit auf {magie_trait} gehen soll (hebt ihn von "
                f"{erstellung.MAGIE_FIXWERT} auf {erstellung.MAGIE_FIXWERT + erstellung.MAGIE_FIXWERT_PROFI_BONUS})."
            )
        stufe2 = await generiere_json(prompt2, _CHARAKTER_FERTIGKEITEN_SYSTEM, schema2, campaign_id=campaign_id)

        magie_bonus = bool(stufe2.get("magieBonusNutzen")) if braucht_magie_bonus_feld else False
        fertigkeit_punkte = erstellung.fertigkeitpunkte_aus_rangfolge(
            paket_id, stufe2.get("fertigkeitenReihenfolge") or [], erlaubte_fertigkeiten,
            magie_bonus=magie_bonus, magie_trait=magie_trait,
        )
        hintergrund_punkte = erstellung.hintergrundpunkte_aus_rangfolge(
            stufe2.get("hintergruendeReihenfolge") or [], hintergrund_pool
        )

        auswahl_ohne_freebees = {
            "weg": weg,
            "rasse": rasse_name,
            "schwerpunkte": schwerpunkte,
            "attributPunkte": attribut_punkte,
            "fertigkeitsPaket": paket_id,
            "fertigkeitPunkte": fertigkeit_punkte,
            "hintergrundPunkte": hintergrund_punkte,
        }
        aktuelle_werte = erstellung.endwerte(auswahl_ohne_freebees, rassen)
        kategorie_von = {t["name"]: t["category"] for t in katalog}
        maximum_von = {t["name"]: t["defaultMax"] for t in katalog}
        maximum_von.update(erstellung.lebensmaxima(rasse_name, katalog, rassen))

        freebee_ergebnis = erstellung.freebees_aus_wunsch(
            budget,
            _als_int(stufe2.get("freebeeKredit")),
            _als_int(stufe2.get("freebeeEigenkapital")),
            stufe2.get("freebeeZielReihenfolge") or [],
            kategorie_von,
            set(hintergrund_pool),
            aktuelle_werte,
            maximum_von,
        )
        auswahl = {**auswahl_ohne_freebees, **freebee_ergebnis}

        # Sicherheitsnetz: der Server hat jede Zahl selbst konstruiert, das
        # hier sollte nie mehr anschlagen. Tut es das doch, ist es ein Bug in
        # der Berechnung oben, keine Regelverletzung der KI — darum ein 500
        # mit anderem Text als der alte "KI hat sich nicht an die Regeln
        # gehalten"-422, damit das im Fehlerfall nicht in die falsche
        # Richtung ermittelt wird.
        fehler = erstellung.pruefe(auswahl, katalog, rassen, einstellungen, hintergrund_katalog)
        if fehler:
            logging.getLogger(__name__).error(
                "Deterministisch gebaute KI-Charaktererstellung verletzt trotzdem die Regeln: %s",
                fehler,
            )
            raise HTTPException(
                status_code=500,
                detail="Interner Fehler beim Zusammenbauen der Charaktererstellung (kein KI-Regelverstoß).",
            )

        werte = erstellung.endwerte(auswahl, rassen)
        name = (konzept.get("name") or "").strip() or "Unbenannter Charakter"
        beschreibung = (konzept.get("beschreibung") or "").strip()
        vermoegen, schulden = erstellung.kapital(auswahl)
        werte = erstellung.wende_gratis_fertigkeit_an(werte, rassen.get(rasse_name, {}) or {}, katalog)
        person = await create_node(
            "Person",
            PERSON_FIELDS,
            campaign_id,
            PersonCreate(
                name=name,
                personType="NPC",
                description=beschreibung,
                notes=(konzept.get("notizen") or "").strip(),
                konzept=(konzept.get("konzept") or "").strip(),
                alter=(konzept.get("alter") or "").strip(),
                ambition=nur_archetyp(konzept.get("ambition"), archetypen),
                verlangen=nur_archetyp(konzept.get("verlangen"), archetypen),
                ziel=(konzept.get("ziel") or "").strip(),
                rasse=rasse_name,
                weg=weg,
                magieFlavor=magie_flavor if magie_flavor in ("MAGIER", "HAERETIKER") else "MAGIER",
                kapital=vermoegen,
                schulden=schulden,
                willenskraftBonus=int(auswahl.get("freebeeWillenskraft") or 0),
                erstellungAbgeschlossen=True,
                istEntwurf=True,
                sichtbarkeit="GM",
            ).model_dump(),
        )
        await set_ratings_bulk(campaign_id, person["id"], werte)
        await setze_maxima_bulk(
            campaign_id, person["id"], erstellung.lebensmaxima(rasse_name, katalog, rassen)
        )

        # Tutorial-Shop-Einkauf (11.10.2026, Marks Wunsch): der frisch
        # generierte Charakter lässt sein Freebee-Kapital nicht länger
        # ungenutzt liegen, sondern kauft sinnvoll aus dem bestehenden
        # Tutorial-Shop-Sortiment ein (kein Shop in der Kampagne = No-Op,
        # siehe ki_einkauf.py). Ein Fehler hier darf den Charakter nicht
        # kaputt machen — er bleibt dann halt unausgerüstet.
        try:
            staerkste_werte = sorted(werte.items(), key=lambda kv: -kv[1])[:8]
            kontext_text = (
                f"{name} — Rasse: {rasse_name or 'unbekannt'}, Weg: {weg}. "
                f"Konzept: {(konzept.get('konzept') or '').strip() or '(keins)'}. "
                "Stärkste Werte: "
                + (", ".join(f"{n} {w}" for n, w in staerkste_werte if w > 0) or "(keine)")
            )
            await ki_einkauf.einkaufen(campaign_id, person["id"], vermoegen, kontext_text)
        except Exception:
            logging.getLogger(__name__).exception(
                "KI-Einkauf nach Charaktererstellung fehlgeschlagen (person=%s)", person["id"]
            )

        await hooks.ki(
            campaign_id, anlass="idee-charakter", prompt=prompt,
            antwort_text=name, uebernommen=True, betrifft_id=person["id"],
        )
        return {"typ": "charakter", "id": person["id"], "name": name, "traits": len(werte)}

    except KiFehler as e:
        # 502 statt 500: der Fehler liegt an der externen KI, nicht an uns.
        raise HTTPException(status_code=502, detail=str(e))


# --- Massen-KI-Anlage (03.10.2026, Marks Wunsch) -------------------------
#
# "Lege mir N Gegenstände von Händler X / Stadtteile von Babel / NPCs in
# einer Bar an" — derselbe ✨-Weg wie eine einzelne Idee, nur N mal in Folge
# mit wachsendem "bereits erzeugt"-Hinweis in jedem einzelnen Aufruf, statt
# einem einzigen Array-Aufruf: so bekommt JEDER neue Eintrag die vollständige
# Namensliste der vorigen zu sehen (robuster gegen Dopplungen als ein
# Array-Schema mit bloßer "sei kreativ"-Anweisung) UND es bleibt exakt der
# bereits getestete Einzel-Anlege-Pfad (_idee_anlegen) — keine zweite,
# abweichende Anlegelogik für Gegenstand/Charakter/Ort. Kostenbewusst im
# selben Sinn wie der Wiki-Sweep: N kleine Aufrufe statt eines unkontrolliert
# teuren, dafür mit harter Obergrenze.
_MASSEN_ANZAHL_MIN = 1
_MASSEN_ANZAHL_MAX = 12

# V1 bewusst auf diese drei beschränkt (Marks Wunsch) — story/event/fraktion/
# verbindung liessen sich über denselben Mechanismus ergänzen, sind aber
# (noch) nicht angefragt.
MassenIdeeTyp = Literal["gegenstand", "charakter", "ort"]

_MASSEN_ZIEL_TYPEN = ("Person", "Ort", "Event", "Fraktion")
_MASSEN_ZIEL_FELDER = {"Person": PERSON_FIELDS, "Ort": ORT_FIELDS, "Event": EVENT_FIELDS, "Fraktion": FRAKTION_FIELDS}

# Welchem _VERBINDUNG_TYPEN-Entitätstyp entspricht ein frisch erzeugter
# Massen-Eintrag dieses Typs — Grundlage für die generische Beziehungskante
# (charakter -> Person, ort -> Ort). "gegenstand" fehlt bewusst: Gegenstände
# hängen nie an einer VERBINDUNG-Kante, sondern an BESITZT/VERKAUFT (siehe
# _gegenstand_verknuepfen).
_MASSEN_ENTITAETS_TYP = {"charakter": "Person", "ort": "Ort"}

# Default-Kantenbezeichnung, falls das Frontend keine eigene mitgibt —
# nur ein Vorschlag, die SL kann jede Kante später wie gewohnt umbenennen.
_MASSEN_STANDARD_BEZIEHUNG = {
    ("charakter", "Person"): "kennt",
    ("charakter", "Ort"): "ist in",
    ("charakter", "Event"): "war dabei bei",
    ("charakter", "Fraktion"): "ist Mitglied von",
    ("ort", "Ort"): "liegt in",
    ("ort", "Person"): "gehört zu",
    ("ort", "Event"): "ist Schauplatz von",
    ("ort", "Fraktion"): "wird kontrolliert von",
}


class MassenIdeeInput(BaseModel):
    typ: MassenIdeeTyp
    prompt: str
    anzahl: int = 5
    # Optionales Ziel, an das jeder erzeugte Eintrag verknüpft wird (z.B.
    # alle Gegenstände landen im Sortiment des Händlers, alle NPCs bekommen
    # eine Beziehungskante zum Ort "Bar").
    zielTyp: Literal["Person", "Ort", "Event", "Fraktion"] | None = None
    zielId: str | None = None
    beziehungstyp: str | None = None


class MassenBeratungInput(BaseModel):
    typ: MassenIdeeTyp
    anzahl: int = 5
    zielTyp: Literal["Person", "Ort", "Event", "Fraktion"] | None = None
    zielId: str | None = None
    beziehungstyp: str | None = None


class MassenEintrag(BaseModel):
    id: str
    name: str
    # True, wenn die optionale Ziel-Verknüpfung für DIESEN Eintrag geklappt
    # hat (z.B. False für Gegenstand+Ort, wofür es noch keinen Mechanismus
    # gibt — siehe _gegenstand_verknuepfen).
    verknuepft: bool = False


class MassenErgebnis(BaseModel):
    typ: str
    eintraege: list[MassenEintrag] = []


class MassenJobGestartet(BaseModel):
    """Sofortige Antwort beim Start — die eigentliche Arbeit läuft im
    Hintergrund weiter (siehe massenjobs.py), unabhängig von dieser Anfrage."""

    jobId: str
    gesamt: int


class MassenJobStatus(BaseModel):
    """Antwort auf das Polling — 'fertig' erst wahr, wenn alle Einträge
    erzeugt sind ODER ein Fehler abgebrochen hat (dann ist `fehler` gesetzt)."""

    fertig: bool
    erstellt: int
    gesamt: int
    ergebnis: MassenErgebnis | None = None
    fehler: str | None = None


async def _ziel_node(campaign_id: str, ziel_typ: str, ziel_id: str) -> dict | None:
    felder = _MASSEN_ZIEL_FELDER.get(ziel_typ)
    if felder is None:
        return None
    return await get_node(ziel_typ, felder, campaign_id, ziel_id)


def _massen_zusatz(
    index: int, anzahl: int, bereits: list[str], ziel_typ: str | None, ziel_name: str | None
) -> str:
    """Hängt an den Wunsch: welcher Eintrag das in der Serie ist, was schon
    erzeugt wurde (nicht wiederholen!) und worauf sich alles bezieht."""
    teile = [f"(Serie: Eintrag {index + 1} von {anzahl} zu genau diesem Wunsch.)"]
    if bereits:
        teile.append(
            "Bereits in dieser Serie erzeugt: " + ", ".join(bereits) + ". "
            "WICHTIG: erzeuge jetzt einen EINZELNEN, klar unterschiedlichen "
            "Eintrag — eigener Name, eigene Werte/Persönlichkeit/Zweck je "
            "nach Typ. Auf keinen Fall eine Wiederholung oder blosse "
            "Variation eines schon erzeugten Eintrags."
        )
    if ziel_name:
        teile.append(f"Bezieht sich auf: {ziel_typ} '{ziel_name}'.")
    return "\n\n" + " ".join(teile)


async def _gegenstand_verknuepfen(campaign_id: str, gegenstand_id: str, preis: int, ziel_typ: str, ziel_node: dict, ziel_id: str) -> bool:
    """Ordnet einen frisch erzeugten Gegenstand-Entwurf dem Ziel zu.

    Ziel ist ein Laden-Ort (istShop=true): Ware kommt ins Sortiment des
    Ortes (VERKAUFT-Kante). Ziel ist ein Verkäufer (istHaendler=true): dieselbe
    Kante, aber am Ort, den er betreibt — nicht an der Person. Ohne Laden
    bleibt die Ware unverknüpft (kein Inventar am Gesicht). Ziel ist eine
    normale Person: der bestehende "Zuweisen"-Knopf. Event/Fraktion: kein
    Platzierungs-Mechanismus, bleibt unverknüpft.
    """
    if ziel_typ == "Ort" and ziel_node.get("istShop"):
        return await haendler_repository.verkauft_hinzufuegen(campaign_id, ziel_id, gegenstand_id, preis)
    if ziel_typ == "Person":
        if ziel_node.get("istHaendler"):
            shop_id = await haendler_repository.shop_id_von_gesicht(campaign_id, ziel_id)
            if not shop_id:
                return False
            return await haendler_repository.verkauft_hinzufuegen(campaign_id, shop_id, gegenstand_id, preis)
        sichtbarkeit, sichtbar_fuer = await _default_sichtbarkeit(campaign_id, ziel_node, ziel_id)
        gegenstand = {"id": gegenstand_id, "einzigartig": False, "storyRelevant": False, "bildUrl": None}
        ergebnis = await assign_copy(campaign_id, gegenstand, ziel_id, sichtbarkeit, sichtbar_fuer)
        return ergebnis is not None
    return False


async def _massen_anlegen(
    campaign_id: str,
    typ: str,
    prompt: str,
    anzahl: int,
    ziel_typ: str | None,
    ziel_id: str | None,
    beziehungstyp: str | None,
    job: massenjobs.MassenJob | None = None,
) -> MassenErgebnis:
    """`job` ist optional gesetzt, wenn dies als Hintergrund-Job läuft (siehe
    massenjobs.py) — dann wird der Fortschritt nach jedem Eintrag eingetragen,
    damit das Frontend per Polling '3 von 9' anzeigen kann."""
    anzahl = max(_MASSEN_ANZAHL_MIN, min(anzahl, _MASSEN_ANZAHL_MAX))

    ziel_node: dict | None = None
    ziel_name: str | None = None
    if ziel_id:
        if not ziel_typ or ziel_typ not in _MASSEN_ZIEL_TYPEN:
            raise HTTPException(status_code=422, detail="zielTyp fehlt oder ist ungültig.")
        ziel_node = await _ziel_node(campaign_id, ziel_typ, ziel_id)
        if ziel_node is None:
            raise HTTPException(status_code=404, detail="Ziel-Entität nicht gefunden.")
        ziel_name = ziel_node.get("name") or ziel_node.get("title") or ""

    eintraege: list[MassenEintrag] = []
    bereits_namen: list[str] = []
    for i in range(anzahl):
        zusatz = _massen_zusatz(i, anzahl, bereits_namen, ziel_typ, ziel_name)
        ergebnis = await _idee_anlegen(campaign_id, typ, prompt + zusatz)
        name = ergebnis["name"]
        bereits_namen.append(name)
        verknuepft = False

        if ziel_id and ziel_node is not None:
            if typ == "gegenstand":
                preis = ergebnis.get("preis") or 0
                verknuepft = await _gegenstand_verknuepfen(
                    campaign_id, ergebnis["id"], preis, ziel_typ, ziel_node, ziel_id
                )
            elif typ in _MASSEN_ENTITAETS_TYP:
                neuer_typ = _MASSEN_ENTITAETS_TYP[typ]
                kanten_typ = (
                    beziehungstyp.strip()
                    if beziehungstyp and beziehungstyp.strip()
                    else _MASSEN_STANDARD_BEZIEHUNG.get((typ, ziel_typ), "verbunden mit")
                )
                await verknuepfung_beziehung_anwenden(
                    campaign_id,
                    BeziehungAnwendenInput(
                        typ1=neuer_typ,
                        name1=name,
                        zielId1=ergebnis["id"],
                        typ2=ziel_typ,
                        name2=ziel_name or "",
                        zielId2=ziel_id,
                        beziehungstyp=kanten_typ,
                        beschreibung="",
                    ),
                )
                verknuepft = True

        eintraege.append(MassenEintrag(id=ergebnis["id"], name=name, verknuepft=verknuepft))
        if job is not None:
            job.erstellt = len(eintraege)

    return MassenErgebnis(typ=typ, eintraege=eintraege)


@router.post("/massenidee", response_model=MassenJobGestartet)
async def ki_massenidee(campaign_id: str, body: MassenIdeeInput):
    """✨-Massen-Anlage: EIN Wunsch + Anzahl → N unterschiedliche Entwürfe,
    optional alle an ein Ziel verknüpft (Sortiment/Beziehung je nach Typ).

    Läuft als Hintergrund-Job (05.10.2026, Mark-Bugreport: auf Mobilfunk
    bricht der Browser eine Anfrage, die mehrere Minuten offen bleibt, eher
    ab als sie zu Ende zu warten — "Failed to fetch", ohne dass auch nur ein
    Eintrag entsteht). Diese Route antwortet sofort mit einer Job-ID, das
    Frontend fragt den Fortschritt über /massenjob/{jobId} ab."""
    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Der Wunsch darf nicht leer sein.")
    anzahl = max(_MASSEN_ANZAHL_MIN, min(body.anzahl, _MASSEN_ANZAHL_MAX))

    async def _arbeit(job: massenjobs.MassenJob) -> MassenErgebnis:
        return await _massen_anlegen(
            campaign_id, body.typ, prompt, anzahl, body.zielTyp, body.zielId, body.beziehungstyp, job=job
        )

    job_id = massenjobs.starten(anzahl, _arbeit)
    return MassenJobGestartet(jobId=job_id, gesamt=anzahl)


@router.post("/beratung/{beratung_id}/massenentwurf", response_model=MassenJobGestartet)
async def beratung_massenentwurf(campaign_id: str, beratung_id: str, body: MassenBeratungInput):
    """Wie /massenidee, nur N Entwürfe aus demselben Beratungsgespräch —
    ebenfalls ein Hintergrund-Job, siehe ki_massenidee oben."""
    stand = await beratung_repo.laden(campaign_id, beratung_id)
    if stand is None:
        raise HTTPException(status_code=404, detail="Beratung nicht gefunden")
    if not stand["nachrichten"]:
        raise HTTPException(status_code=422, detail="Noch kein Gespräch für einen Entwurf.")
    prompt = beratung_repo.gespraech_als_prompt(stand["nachrichten"])
    anzahl = max(_MASSEN_ANZAHL_MIN, min(body.anzahl, _MASSEN_ANZAHL_MAX))

    async def _arbeit(job: massenjobs.MassenJob) -> MassenErgebnis:
        return await _massen_anlegen(
            campaign_id, body.typ, prompt, anzahl, body.zielTyp, body.zielId, body.beziehungstyp, job=job
        )

    job_id = massenjobs.starten(anzahl, _arbeit)
    return MassenJobGestartet(jobId=job_id, gesamt=anzahl)


@router.get("/massenjob/{job_id}", response_model=MassenJobStatus)
async def massenjob_status(campaign_id: str, job_id: str):
    """Polling-Ziel für beide Massen-Anlage-Routen oben. `campaign_id` wird
    nicht gebraucht (die Job-ID ist bereits eindeutig), bleibt aber im Pfad,
    damit require_campaign_gm (Router-Abhängigkeit) greift — ein Job gehört
    zu einer Beratung/Kampagne, und nur deren SL soll den Fortschritt sehen."""
    job = massenjobs.status(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job nicht gefunden — entweder abgeschlossen und schon abgeholt, oder der Server wurde neugestartet.",
        )
    return MassenJobStatus(
        fertig=job.fertig, erstellt=job.erstellt, gesamt=job.gesamt, ergebnis=job.ergebnis, fehler=job.fehler
    )


def _beratung_system(kontext: str) -> str:
    if not kontext.strip():
        return (
            _BERATUNG_SYSTEM
            + " Die Kampagne hat noch keine freigegebenen Entitäten — "
            "es gibt also noch keinen Kanon."
        )
    return _BERATUNG_SYSTEM + "\n\nFreigegebene Welt (Kanon):\n" + kontext


@router.get("/beratung")
async def beratung_liste(campaign_id: str):
    """Gesprächsliste — nur SL, nie Spieler, nie im Kampagnenkontext."""
    return await beratung_repo.liste(campaign_id)


@router.post("/beratung")
async def beratung_neu(campaign_id: str):
    daten = await beratung_repo.anlegen(campaign_id)
    if daten is None:
        raise HTTPException(status_code=404, detail="Kampagne nicht gefunden")
    return daten


@router.get("/beratung/{beratung_id}")
async def beratung_lesen(campaign_id: str, beratung_id: str):
    daten = await beratung_repo.laden(campaign_id, beratung_id)
    if daten is None:
        raise HTTPException(status_code=404, detail="Beratung nicht gefunden")
    return daten


@router.delete("/beratung/{beratung_id}")
async def beratung_loeschen(campaign_id: str, beratung_id: str):
    if not await beratung_repo.loeschen(campaign_id, beratung_id):
        raise HTTPException(status_code=404, detail="Beratung nicht gefunden")
    return {"ok": True}


@router.post("/beratung/{beratung_id}/nachricht")
async def beratung_nachricht(
    campaign_id: str, beratung_id: str, body: BeratungNachrichtInput
):
    """Eine User-Nachricht, Antwort der KI. Kontext: nur Freigegebenes."""
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Die Nachricht darf nicht leer sein.")
    if len(text) > 8000:
        raise HTTPException(status_code=422, detail="Nachricht zu lang.")

    stand = await beratung_repo.laden(campaign_id, beratung_id)
    if stand is None:
        raise HTTPException(status_code=404, detail="Beratung nicht gefunden")

    kontext = await sammle_kontext(campaign_id)
    an_modell = beratung_repo.fuer_modell(stand["nachrichten"])
    an_modell.append({"rolle": "user", "text": text})
    try:
        antwort, antwort_provider = await generiere_text(
            an_modell, _beratung_system(kontext), provider=body.provider, campaign_id=campaign_id
        )
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))

    await beratung_repo.nachricht_anhaengen(campaign_id, beratung_id, "user", text)
    gespeichert = await beratung_repo.nachricht_anhaengen(
        campaign_id, beratung_id, "assistant", antwort, provider=antwort_provider
    )
    await hooks.ki(
        campaign_id,
        anlass="beratung",
        prompt=text,
        antwort_text=antwort,
        uebernommen=False,
        betrifft_id=beratung_id,
    )
    return gespeichert


@router.post("/beratung/{beratung_id}/entwurf")
async def beratung_entwurf(
    campaign_id: str, beratung_id: str, body: BeratungEntwurfInput
):
    """Legt aus dem Gespräch einen Ideenschmiede-Entwurf an (istEntwurf=true)."""
    stand = await beratung_repo.laden(campaign_id, beratung_id)
    if stand is None:
        raise HTTPException(status_code=404, detail="Beratung nicht gefunden")
    if not stand["nachrichten"]:
        raise HTTPException(status_code=422, detail="Noch kein Gespräch für einen Entwurf.")
    prompt = beratung_repo.gespraech_als_prompt(stand["nachrichten"])
    return await _idee_anlegen(campaign_id, body.typ, prompt)


@router.post("/wiki/import", response_model=ImportAntwort)
async def wiki_import(campaign_id: str, datei: UploadFile = File(...)):
    """Dokument-Import: SL lädt ein Word/PDF-Dokument hoch, die KI teilt es

    automatisch anhand seiner Struktur (Überschriften/Kapitel) in eine oder
    mehrere Wiki-Seiten-Entwürfe auf (istEntwurf=true, wie jede andere
    Ideenschmiede-Idee — SL muss jeden Entwurf noch einzeln prüfen und
    übernehmen, kein Autocommit). Pro erzeugter Seite läuft anschliessend
    automatisch die bestehende Auto-Verknüpfung.
    """
    dateiname = datei.filename or ""
    if not any(dateiname.lower().endswith(e) for e in ERLAUBTE_ENDUNGEN):
        raise HTTPException(
            status_code=422,
            detail=f"Nur folgende Dateiformate werden unterstützt: {', '.join(sorted(ERLAUBTE_ENDUNGEN))}",
        )

    inhalt = await datei.read()
    try:
        return await wiki_importiere(campaign_id, dateiname, inhalt)
    except (DokumentFormatFehler, DokumentZuGrossFehler) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except KiFehler as e:
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
            campaign_id=campaign_id,
        )
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))

    text = (ergebnis.get("text") or "").strip()
    await hooks.ki(
        campaign_id, anlass="objekt-text", prompt=objekt_prompt,
        antwort_text=text, uebernommen=False,
    )
    return {"text": text}


class ObjektTextPruefenInput(BaseModel):
    """Für den 🔍-Knopf im RichTextEditor, neben dem ✨-KI-Knopf."""

    text: str


@router.post("/objekt-text/pruefen")
async def ki_objekt_text_pruefen(campaign_id: str, body: ObjektTextPruefenInput):
    """Prüft ein Beschreibungs-/Notizen-Feld auf Rechtschreib-/Grammatik-/

    Logikfehler — dieselbe Prüfung wie im Wiki-Editor (app/ki/wiki_pruefung.py),
    nur ohne Seitenbezug/Prüfhash. Liefert die Befunde zur Vorschau zurück;
    das Übernehmen passiert clientseitig im Editor, hier wird nichts gespeichert.
    """
    try:
        befunde = await pruefe_freitext(campaign_id, body.text)
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"befunde": [b.model_dump() for b in befunde]}


class ObjektTextVerknuepfenInput(BaseModel):
    """Für den ⧉✨-Knopf im RichTextEditor bzw. der Ideenschmiede."""

    text: str


@router.post("/objekt-text/verknuepfung/vorschlaege", response_model=VorschlaegeAntwort)
async def ki_objekt_text_verknuepfung(campaign_id: str, body: ObjektTextVerknuepfenInput):
    """Auto-Verknüpfung für einen freien Text ohne Wiki-Seitenbezug.

    Dieselbe Erkennung wie im Wiki-Editor (app/ki/auto_verknuepfung.py), nur
    ohne Seiten-ID — für Ideenschmiede-Entwurfstexte und die generischen
    Beschreibungs-/Notizen-Felder (RichTextEditor). Ohne Wiki-Seite gibt es
    keinen Ort für einen Verweis-Chip, deshalb liefert diese Route zwar auch
    `verweise` zurück (zur Information), nur `beziehungen` sind über
    `/wiki/{seitenId}/verknuepfung/beziehung`-artige Anwenden-Routen wirklich
    verknüpfbar — siehe `wiki_verknuepfung_beziehung` unten, `seitenId` ist
    dort ohnehin nur Teil des URL-Pfads, die Kante hängt nicht an einer Seite.
    """
    try:
        return await verknuepfung_vorschlaege_fuer_text(campaign_id, body.text)
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))


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


@router.post("/wiki/verknuepfung/sweep-vorschlaege", response_model=SweepVorschlaegeAntwort)
async def wiki_verknuepfung_sweep(campaign_id: str):
    """Auto-Verknüpfung über ALLE Wiki-Seiten der Kampagne auf einmal.

    Für Altbestand, der vor der Auto-Verknüpfung (22.09.2026) angelegt wurde
    und nie einzeln durchsucht wurde. Überspringt Seiten, deren Text sich
    seit dem letzten Sweep nicht geändert hat (eigener Hash, unabhängig vom
    Rechtschreib-/Logik-Prüfhash). Legt nichts automatisch an — die Vorschläge
    werden gesammelt zurückgegeben, jeder einzeln über die bestehenden
    `/wiki/{seiten_id}/verknuepfung/anwenden`- bzw. `/beziehung`-Routen
    bestätigt (Marks Vorgabe: kein Autocommit in die Kampagne).
    """
    try:
        return await verknuepfung_sweep(campaign_id)
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/verknuepfung/beziehungen-aus-beschreibungen", response_model=VorschlaegeAntwort)
async def beziehungen_aus_beschreibungen(campaign_id: str):
    """Liest Beschreibung+Notizen ALLER Personen/Orte/Events/Fraktionen in
    einem KI-Aufruf und schlägt daraus neue VERBINDUNG-Kanten vor.

    Der "✨ Beziehungen aus Beschreibungen"-Knopf im Verbindungen-Bereich
    (03.10.2026, Marks Wunsch) — anders als die Wiki-Auto-Verknüpfung oben
    braucht das keine Wiki-Seite, sondern durchsucht direkt die Charakter-/
    Orts-/Fraktionsbögen. Beide Seiten einer vorgeschlagenen Beziehung
    existieren bereits (das sind bestehende Entitäten, keine Erwähnungen in
    freiem Text), `zielId` ist daher nie `None` — Anwenden läuft trotzdem
    über dieselbe `/wiki/{seitenId}/verknuepfung/beziehung`-Route wie überall
    sonst (Platzhalter-`seitenId`, die Kante hängt an den Entitäten).
    """
    try:
        return await beziehungsvorschlaege_aus_beschreibungen(campaign_id)
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/verbindungstypen/normalisierung/vorschlaege", response_model=NormalisierungsVorschlaegeAntwort)
async def verbindungstypen_normalisierung_vorschlaege(campaign_id: str):
    """Vergleicht alle in der Kampagne verwendeten Beziehungstyp-Strings und
    schlägt vor, welche sinngemäß dasselbe bedeuten — Grundlage für den
    "✨ Kantentypen normalisieren"-Knopf im Graph-Filter (24.10.2026, Marks
    Wunsch: Kantentypen ausblenden können lohnt sich erst, wenn nicht fünf
    Varianten von "kennt" nebeneinander existieren).
    """
    try:
        return await verbindungstypen_vorschlaege(campaign_id)
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/verbindungstypen/normalisierung/anwenden", response_model=NormalisierungAnwendenErgebnis)
async def verbindungstypen_normalisierung_anwenden(campaign_id: str, body: NormalisierungAnwendenInput):
    """Wendet EINEN bestätigten Normalisierungsvorschlag an: benennt alle
    betroffenen VERBINDUNG-Kanten auf den kanonischen Typ um. Kein KI-Aufruf
    mehr nötig, deshalb kein KiFehler-Handling hier."""
    return await verbindungstypen_anwenden(campaign_id, body.kanonisch, body.varianten)


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


# --- Bildgenerierung ----------------------------------------------------
# Ein Knopf am jeweils bestehenden Bild-Upload-Popup (Person/Ort/Gegenstand):
# 1. Prompt-Vorschlag aus Name+Beschreibung+Notizen (Text-KI, wiederverwendet
#    dieselbe sammle_kontext()/generiere_json()-Infrastruktur wie oben).
# 2. Nutzer bestätigt/editiert den Prompt, dann eigentliche Bildgenerierung
#    (lokal Fooocus ODER cloud Gemini, Nutzer wählt je Aufruf — siehe
#    app/ki/bildgenerierung.py). Speichert über denselben Upload-Mechanismus
#    wie ein manuell hochgeladenes Bild (entities/items routes.py), keine
#    zweite Ablage-Logik.

_BILD_PROMPT_SYSTEM = (
    _SYSTEM
    + " Du formulierst einen kurzen, bildhaften Prompt (2-4 Sätze, auf "
    "Englisch, für einen SDXL-Bildgenerator) für ein Portrait/eine Szene/ein "
    "Gegenstandsbild im Digital-Art-/Cyberpunk-Stil. Beschreibe Aussehen, "
    "Kleidung/Material, Stimmung und Umgebung so konkret wie möglich — keine "
    "Namen, keine Spielmechanik, kein Fließtext-Artikel. Zieh Beschreibung "
    "und Notizen heran, vor allem sichtbare Merkmale."
)

_BILD_PROMPT_SCHEMA = {
    "type": "OBJECT",
    "properties": {"prompt": {"type": "STRING"}},
    "required": ["prompt"],
}


def _bild_prompt_quelle(
    objekt_typ: str,
    objekt_name: str,
    beschreibung: str = "",
    notizen: str = "",
) -> str:
    """Baut den Text, den die Bild-Prompt-KI als Quelle bekommt.

    Beschreibung und Notizen getrennt, weil Aussehen oft in den Notizen
    steht und vorher stillschweigend ignoriert wurde.
    """
    teile = [f"{objekt_typ}: {objekt_name}"]
    beschreibung = (beschreibung or "").strip()
    notizen = (notizen or "").strip()
    if beschreibung:
        teile.append(f"Bisherige Beschreibung:\n{beschreibung}")
    if notizen:
        teile.append(f"Notizen:\n{notizen}")
    return "\n\n".join(teile)


async def _bild_prompt_vorschlagen(
    campaign_id: str,
    objekt_typ: str,
    objekt_name: str,
    beschreibung: str,
    notizen: str = "",
) -> str:
    """Gemeinsame Logik für den Prompt-Vorschlag — von der GM-Route UND der
    Spieler-Portrait-Route genutzt (players/routes.py ruft das direkt auf,
    da sie außerhalb dieses require_campaign_gm-Routers liegt)."""
    kontext = await sammle_kontext(campaign_id)
    prompt = _bild_prompt_quelle(objekt_typ, objekt_name, beschreibung, notizen)
    try:
        ergebnis = await generiere_json(_mit_kontext(prompt, kontext), _BILD_PROMPT_SYSTEM, _BILD_PROMPT_SCHEMA, campaign_id=campaign_id)
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))
    return (ergebnis.get("prompt") or "").strip()


@router.post("/bild-prompt")
async def ki_bild_prompt(campaign_id: str, body: BildPromptInput):
    """Schlägt einen Bild-Prompt vor (Schritt 1 des KI-Bild-Popups) — der
    Nutzer sieht ihn vorausgefüllt im Textfeld und kann ihn vor dem
    Generieren noch anpassen (Marks Entscheidung, siehe Aufgabenbeschreibung)."""
    prompt = await _bild_prompt_vorschlagen(
        campaign_id, body.objektTyp, body.objektName,
        body.bisherigeBeschreibung, body.notizen,
    )
    if not prompt:
        raise HTTPException(status_code=502, detail="Die KI hat keinen Prompt-Vorschlag geliefert.")
    await hooks.ki(
        campaign_id, anlass="bild-prompt", prompt=body.objektName,
        antwort_text=prompt, uebernommen=False,
    )
    return {"prompt": prompt}


@router.post("/bild-generieren")
async def ki_bild_generieren(campaign_id: str, body: BildGenerierenInput):
    """Generiert ein Bild (Schritt 2) und liefert es als rohe Bytes zur
    Vorschau zurück — speichert NICHTS. Das Popup zeigt das Bild an; erst
    „Übernehmen“ schickt es (als Datei) an die jeweils bestehende
    Upload-Route (Personen/Orte/Events/Fraktionen/Gegenstände/eigenes
    Portrait), genau wie ein manuell hochgeladenes Bild — dieselbe Route,
    kein zweiter Ablage-Mechanismus. `campaign_id` wird hier nur für den
    require_campaign_gm-Guard des Routers gebraucht, nicht für die
    Bildgenerierung selbst (die hängt an keiner Entität)."""
    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Der Prompt darf nicht leer sein.")

    try:
        inhalt, content_type = await generiere_bild(body.provider, prompt)
    except BildgenerierungFehler as e:
        raise HTTPException(status_code=502, detail=str(e))

    await hooks.ki(
        campaign_id, anlass="bild-generieren", prompt=prompt,
        antwort_text=f"{body.provider}: {len(inhalt)} Bytes", uebernommen=False,
    )
    return Response(content=inhalt, media_type=content_type)
