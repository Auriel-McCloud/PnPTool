"""Fachlogik des Kampagnen-Wikis — ohne Datenbank, ohne FastAPI.

Bewusst reine Funktionen: Inhaltsverzeichnis, Verknüpfungen, Seitenbaum und
die "bis hierher freigeben"-Reihenfolge sind Fachregeln. Sie hier zu halten
macht sie ohne laufende Neo4j-Instanz testbar (wie app/entities/visibility.py).
"""

import json
import re

# Der TipTap-Knotentyp, der eine Verknüpfung auf eine Kampagnen-Entität trägt.
# Muss zur Frontend-Extension passen (frontend/src/richtext/EntitaetsVerweis.ts).
VERWEIS_TYP = "entitaetsverweis"

# Umlaute vor der Anker-Bildung ausschreiben. Reines Weglassen ergäbe aus
# "Straße" das unleserliche "strae"; Ankertexte tauchen aber in URLs auf.
_UMSCHRIFT = {
    "ä": "ae", "ö": "oe", "ü": "ue",
    "Ä": "ae", "Ö": "oe", "Ü": "ue",
    "ß": "ss",
}


def _laden(roh: str) -> dict | None:
    """TipTap-JSON einlesen. Kaputtes oder leeres bleibt folgenlos.

    Wiki-Inhalte kommen aus dem Editor, könnten aber auch aus einem Import
    oder einer alten Zeile stammen. Ein Parserfehler darf nie die ganze
    Seitenliste mit einem 500er herunterreissen.
    """
    if not roh:
        return None
    try:
        doc = json.loads(roh)
    except (json.JSONDecodeError, TypeError):
        return None
    return doc if isinstance(doc, dict) and doc.get("type") == "doc" else None


def _durchlaufen(knoten: dict):
    """Jeden Knoten des Dokuments liefern, egal wie tief verschachtelt.

    Wichtig für Tabellen: ein Verweis in einer Tabellenzelle liegt vier Ebenen
    unter dem Dokument und würde bei flacher Betrachtung übersehen.
    """
    yield knoten
    for kind in knoten.get("content") or []:
        if isinstance(kind, dict):
            yield from _durchlaufen(kind)


def _ist_geheim(knoten: dict) -> bool:
    return any(m.get("type") == "gmSecret" for m in knoten.get("marks") or [])


def _text_von(knoten: dict, viewer_role: str) -> str:
    """Reintext eines Knotens; für Nicht-SL ohne die geheim markierten Teile."""
    stuecke = []
    for teil in _durchlaufen(knoten):
        if teil.get("type") != "text":
            continue
        if viewer_role != "GM" and _ist_geheim(teil):
            continue
        stuecke.append(teil.get("text") or "")
    return "".join(stuecke).strip()


def anker_aus(titel: str) -> str:
    """Sprungmarke aus einem Überschriftentext."""
    text = titel
    for zeichen, ersatz in _UMSCHRIFT.items():
        text = text.replace(zeichen, ersatz)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def inhaltsverzeichnis(roh: str, viewer_role: str = "GM") -> list[dict]:
    """Baut das Inhaltsverzeichnis aus den Überschriften des Dokuments.

    Wird bei jedem Abruf neu erzeugt statt gespeichert — so kann es nicht
    veralten, wenn jemand eine Überschrift umbenennt.

    Für Nicht-SL fallen geheim markierte Überschriften komplett weg: Stünde
    "Der Verräter" im Verzeichnis, wäre der Plot verraten, auch wenn der
    Absatz darunter sauber redigiert ist.
    """
    doc = _laden(roh)
    if doc is None:
        return []

    eintraege: list[dict] = []
    vergeben: dict[str, int] = {}

    for knoten in _durchlaufen(doc):
        if knoten.get("type") != "heading":
            continue
        text = _text_von(knoten, viewer_role)
        if not text:
            continue

        anker = anker_aus(text) or "abschnitt"
        # Zwei gleichnamige Überschriften ergäben denselben Anker; der zweite
        # Sprung landete sonst immer beim ersten Vorkommen.
        vergeben[anker] = vergeben.get(anker, 0) + 1
        if vergeben[anker] > 1:
            anker = f"{anker}-{vergeben[anker]}"

        eintraege.append(
            {
                "stufe": int(knoten.get("attrs", {}).get("level") or 1),
                "text": text,
                "anker": anker,
            }
        )
    return eintraege


def verweise_sammeln(roh: str) -> list[dict]:
    """Alle Entitäts-Verknüpfungen einer Seite, doppelte zusammengefasst.

    Grundlage für die Graphbeziehungen (:WikiSeite)-[:VERWEIST_AUF]->(:Person)
    und damit für die Rückverweise am NPC ("Erwähnt in: Kapitel 1").

    Ob die Ziel-ID zur Kampagne gehört, prüft das Repository — hier wird nur
    gelesen, was im Dokument steht.
    """
    doc = _laden(roh)
    if doc is None:
        return []

    gefunden: list[dict] = []
    gesehen: set[tuple[str, str]] = set()

    for knoten in _durchlaufen(doc):
        if knoten.get("type") != VERWEIS_TYP:
            continue
        attrs = knoten.get("attrs") or {}
        ziel_id = attrs.get("zielId")
        ziel_typ = attrs.get("zielTyp")
        if not ziel_id or not ziel_typ:
            continue
        schluessel = (ziel_id, ziel_typ)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        gefunden.append({"zielId": ziel_id, "zielTyp": ziel_typ})
    return gefunden


def _sortiert(seiten: list[dict]) -> list[dict]:
    return sorted(seiten, key=lambda s: (s.get("sortierung") or 0, s.get("titel") or ""))


def baum_bauen(seiten: list[dict]) -> list[dict]:
    """Flache Seitenliste in den Seitenbaum überführen.

    Tabs sind Seiten ohne Elternteil, alles darunter sind Unterseiten —
    ein Typ, kein separates "Dokument" (bewusste Entscheidung, siehe
    docs/produktvision-wiki.md).

    Zwei Fälle, die sonst Inhalt verschlucken würden:
    - Verwaiste Seiten (Elternteil gelöscht oder für diesen Betrachter
      unsichtbar) kommen auf die oberste Ebene statt zu verschwinden.
    - Ein Zyklus durch fehlerhafte Daten darf die Anzeige nicht aufhängen.
    """
    knoten = {s["id"]: {**s, "kinder": []} for s in seiten}
    wurzeln: list[dict] = []

    for seite in _sortiert(seiten):
        eigener = knoten[seite["id"]]
        eltern_id = seite.get("parentId")

        if eltern_id and eltern_id in knoten and eltern_id != seite["id"]:
            # Zyklusschutz: läuft die Elternkette auf einen selbst zurück,
            # zählt die Seite als Wurzel statt sich selbst zu enthalten.
            lauf, tiefe = eltern_id, 0
            zyklisch = False
            while lauf and tiefe < len(seiten) + 1:
                if lauf == seite["id"]:
                    zyklisch = True
                    break
                lauf = knoten.get(lauf, {}).get("parentId")
                tiefe += 1
            if not zyklisch:
                knoten[eltern_id]["kinder"].append(eigener)
                continue

        wurzeln.append(eigener)

    return wurzeln


def _flach_in_lesereihenfolge(seiten: list[dict]) -> list[str]:
    """Seiten-IDs so, wie man sie von oben nach unten durchliest."""
    reihe: list[str] = []

    def absteigen(zweige: list[dict]):
        for zweig in zweige:
            reihe.append(zweig["id"])
            absteigen(zweig["kinder"])

    absteigen(baum_bauen(seiten))
    return reihe


def seiten_bis_einschliesslich(seiten: list[dict], seiten_id: str) -> list[str]:
    """Alle Seiten von vorn bis einschliesslich der genannten.

    Marks "was bisher geschah": Nach Session 3 gibt man einmal Kapitel 3 frei
    und die Gruppe hat alles bis dahin — statt jede Seite einzeln anzuklicken.

    Bewusst die Lesereihenfolge (Tiefensuche), nicht die Erstellungsreihenfolge:
    massgeblich ist, was im Seitenbaum vor der Zielseite steht.
    """
    reihe = _flach_in_lesereihenfolge(seiten)
    if seiten_id not in reihe:
        return []
    return reihe[: reihe.index(seiten_id) + 1]
