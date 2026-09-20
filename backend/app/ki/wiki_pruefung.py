"""Rechtschreib-/Grammatik-/Logikprüfung für Wiki-Seiten (CLAUDE.md Punkt 3).

Zwei Einstiege:

- ``pruefe_seite`` — eine einzelne Seite, aufgerufen über den "🔍 Prüfen"-
  Knopf direkt im Wiki-Editor (Story-Wiki UND Ideenschmiede-Wiki-Popup,
  da beide dieselbe ``WikiEditor``-Komponente einbetten).
- ``sweep`` — geht ALLE Seiten einer Kampagne durch, aber überspringt jede,
  deren Inhalt sich seit der letzten Prüfung nicht geändert hat (Hash-
  Vergleich über ``wiki/repository.get_pruefhash``/``set_pruefhash``).
  Für Marks "Prüf Fließtext!"-Knopf in den Kampagnen-Einstellungen, der
  bewusst nicht bei jedem Klick alles neu anfragt.

Logikfehler beziehen den freigegebenen Kampagnenkontext ein
(``app.ki.kontext.sammle_kontext``) — dieselbe Quelle wie beim KI-
Charaktergenerator, damit ein Widerspruch zu bereits bekannten Fakten
(z.B. ein Ort, der laut Wiki zerstört ist, taucht aber unversehrt in einer
späteren Szene auf) erkannt werden kann.

Ein Befund besteht aus einem wörtlichen ``zitat`` (die fehlerhafte
Textstelle, exakt wie sie im Fließtext steht) und einem ``vorschlag``
(Ersatztext). Die Anwendung (``uebernehmen_befund``) sucht dieses Zitat als
zusammenhängenden Textknoten im gespeicherten TipTap-Dokument und ersetzt
es direkt — funktioniert unabhängig davon, ob die Seite gerade im Editor
offen ist (wichtig für den Sweep, der über viele Seiten hinweg läuft, von
denen die meisten gerade nicht offen sind).
"""

import hashlib
import json

from pydantic import BaseModel

from app.ki.client import generiere_json
from app.ki.kontext import sammle_kontext, tiptap_zu_text
from app.wiki import repository

_SYSTEM = (
    "Du bist Lektor für ein deutsches Cyberpunk-Pen-and-Paper-Rollenspiel "
    "(NeotopiA). Du prüfst einen Wiki-Text auf Rechtschreib-, Grammatik- und "
    "Logik-/Konsistenzfehler. Melde NUR echte Fehler — keine Stilkritik, "
    "keine Geschmacksfragen, keine Vorschläge zur Wortwahl, wenn der Satz "
    "grammatisch korrekt ist. Ein Logikfehler ist NUR ein direkter "
    "WIDERSPRUCH zu einer Tatsache, die in der freigegebenen Welt der "
    "Kampagne bereits explizit so steht (z.B. ein Ort gilt dort als "
    "zerstört, taucht hier aber unversehrt auf; eine Person ist dort tot, "
    "handelt hier aber). Ein Name, Ort oder Ereignis, das in der "
    "freigegebenen Welt schlicht NICHT vorkommt, ist KEIN Fehler — das ist "
    "einfach neuer Inhalt, den der Autor gerade erst einführt, das ist "
    "normal und erwartet. Erwähne solche 'nicht gefunden'-Fälle nicht. "
    "Jedes 'zitat' muss WÖRTLICH und ZUSAMMENHÄNGEND so im Text vorkommen "
    "(exakte Zeichenfolge, keine Umformulierung des ganzen Satzes), damit "
    "es automatisch ersetzt werden kann — bei einem Logikfehler zitiere die "
    "kürzeste Textstelle, die den Widerspruch trägt (z.B. nur den falschen "
    "Namen oder die falsche Zahl), nicht den ganzen Absatz."
)

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "befunde": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "art": {
                        "type": "STRING",
                        "enum": ["rechtschreibung", "grammatik", "logik"],
                    },
                    "zitat": {"type": "STRING"},
                    "vorschlag": {"type": "STRING"},
                    "begruendung": {"type": "STRING"},
                },
                "required": ["art", "zitat", "vorschlag", "begruendung"],
            },
        },
    },
    "required": ["befunde"],
}


class PruefBefund(BaseModel):
    art: str
    zitat: str
    vorschlag: str
    begruendung: str = ""


class SeitenPruefung(BaseModel):
    seitenId: str
    titel: str
    befunde: list[PruefBefund] = []


class SweepAntwort(BaseModel):
    geprueft: int
    uebersprungen: int
    ergebnisse: list[SeitenPruefung] = []


class UebernehmenAntwort(BaseModel):
    ersetzt: bool
    inhalt: str = ""


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _prompt(text: str, kontext: str) -> str:
    teile = [f"Zu prüfender Text:\n{text}"]
    if kontext:
        teile.append(
            "Freigegebene Welt der Kampagne — nutze sie NUR, um Logik-/"
            f"Konsistenzfehler im obigen Text zu erkennen:\n{kontext}"
        )
    teile.append(
        "Gib jeden gefundenen Fehler einzeln zurück. Kein Fehler gefunden? "
        "Dann eine leere Liste."
    )
    return "\n\n".join(teile)


async def _pruefe_text(text: str, kontext: str) -> list[PruefBefund]:
    if not text.strip():
        return []
    ergebnis = await generiere_json(_prompt(text, kontext), _SYSTEM, _SCHEMA)
    befunde = []
    for eintrag in ergebnis.get("befunde") or []:
        zitat = (eintrag.get("zitat") or "").strip()
        vorschlag = (eintrag.get("vorschlag") or "").strip()
        if not zitat or not vorschlag or zitat not in text:
            # Ohne Fundstelle im Originaltext liesse sich der Vorschlag nicht
            # automatisch anwenden — solche Treffer sind für uns nutzlos und
            # würden am "Übernehmen"-Knopf nur ins Leere laufen.
            continue
        befunde.append(
            PruefBefund(
                art=eintrag.get("art") or "grammatik",
                zitat=zitat,
                vorschlag=vorschlag,
                begruendung=(eintrag.get("begruendung") or "").strip(),
            )
        )
    return befunde


async def pruefe_seite(campaign_id: str, seiten_id: str) -> list[PruefBefund]:
    """Prüft eine einzelne Seite und merkt sich den geprüften Textstand."""
    seite = await repository.get_seite(campaign_id, seiten_id)
    if seite is None:
        return []
    text = tiptap_zu_text(seite["inhalt"])
    kontext = await sammle_kontext(campaign_id)
    befunde = await _pruefe_text(text, kontext)
    await repository.set_pruefhash(campaign_id, seiten_id, _hash(text))
    return befunde


async def sweep(campaign_id: str) -> SweepAntwort:
    """Geht alle Seiten der Kampagne durch, überspringt unveränderte."""
    seiten = await repository.list_seiten(campaign_id)
    kontext = await sammle_kontext(campaign_id)

    geprueft = 0
    uebersprungen = 0
    ergebnisse: list[SeitenPruefung] = []

    for seite in seiten:
        text = tiptap_zu_text(seite["inhalt"])
        aktueller_hash = _hash(text)
        letzter_hash = await repository.get_pruefhash(campaign_id, seite["id"])
        if text.strip() and aktueller_hash == letzter_hash:
            uebersprungen += 1
            continue

        geprueft += 1
        befunde = await _pruefe_text(text, kontext)
        await repository.set_pruefhash(campaign_id, seite["id"], aktueller_hash)
        if befunde:
            ergebnisse.append(
                SeitenPruefung(seitenId=seite["id"], titel=seite["titel"], befunde=befunde)
            )

    return SweepAntwort(geprueft=geprueft, uebersprungen=uebersprungen, ergebnisse=ergebnisse)


def _text_ersetzen(knoten, zitat: str, vorschlag: str) -> bool:
    """Ersetzt das erste Vorkommen von `zitat` in einem TipTap-Textknoten.

    Läuft direkt auf dem geladenen Dokument (mutiert es in-place) und gibt
    True zurück, sobald ein Treffer ersetzt wurde. Ein Zitat, das über zwei
    unterschiedlich formatierte Textknoten hinweggeht (z.B. halb fett), wird
    bewusst NICHT gefunden — das deckt der Prompt ab, indem er kurze,
    zusammenhängende Zitate verlangt.
    """
    if isinstance(knoten, dict):
        if knoten.get("type") == "text" and isinstance(knoten.get("text"), str) and zitat in knoten["text"]:
            knoten["text"] = knoten["text"].replace(zitat, vorschlag, 1)
            return True
        for wert in knoten.values():
            if _text_ersetzen(wert, zitat, vorschlag):
                return True
    elif isinstance(knoten, list):
        for eintrag in knoten:
            if _text_ersetzen(eintrag, zitat, vorschlag):
                return True
    return False


async def uebernehmen_befund(
    campaign_id: str, seiten_id: str, zitat: str, vorschlag: str
) -> UebernehmenAntwort | None:
    """Wendet einen Korrekturvorschlag direkt im gespeicherten Dokument an.

    Funktioniert unabhängig davon, ob die Seite gerade im Editor offen ist —
    wichtig für Befunde aus dem Sweep, die über viele nicht-offene Seiten
    laufen. Findet sich das Zitat nicht mehr (z.B. weil die Seite inzwischen
    von Hand geändert wurde), bleibt die Seite unverändert und `ersetzt` ist
    False — die Fundstelle muss dann manuell korrigiert werden.
    """
    seite = await repository.get_seite(campaign_id, seiten_id)
    if seite is None:
        return None

    try:
        dokument = json.loads(seite["inhalt"])
    except (ValueError, TypeError):
        return UebernehmenAntwort(ersetzt=False, inhalt=seite["inhalt"])

    if not _text_ersetzen(dokument, zitat, vorschlag):
        return UebernehmenAntwort(ersetzt=False, inhalt=seite["inhalt"])

    neuer_inhalt = json.dumps(dokument, ensure_ascii=False)
    aktualisiert = await repository.update_seite(campaign_id, seiten_id, {"inhalt": neuer_inhalt})
    return UebernehmenAntwort(ersetzt=True, inhalt=aktualisiert["inhalt"] if aktualisiert else neuer_inhalt)
