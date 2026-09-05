"""Suchen, Sortieren und Filtern von Personen, Orten und Events.

Reine Funktionen ohne Datenbank — deshalb testbar (tests/test_entitaeten_filter.py).

**Wichtig zur Reihenfolge:** gesucht wird immer auf der bereits durch
`visibility.filter_entities_for_viewer` gelaufenen Liste. Sonst könnte ein
Spieler einen 🔒-markierten Satz finden, indem er danach sucht — der Treffer
allein verriete, dass der Satz existiert, obwohl der Text selbst redigiert
ausgeliefert wird.

Der Beziehungsfilter arbeitet auf den echten `VERBINDUNG`-Kanten des Graphen
(repository.list_verbindungen), nicht auf einem Sonderfeld an der Entität.
Damit gilt für jede Zuordnung, die die Spielleitung ohnehin schon pflegt:
"wer ist in der 3Heavens Bar", "wer ist Gegner beim Überfall", "wer gehört zu
Gruppe X" sind dieselbe Abfrage mit anderem Ziel.
"""

import json
import unicodedata
from typing import Iterable, Literal

# Erlaubte Sortierungen. Als Literal in der Route verwendet, damit ein
# unbekannter Wert 422 gibt statt still auf die Vorgabe zurückzufallen —
# ein Tippfehler im Frontend soll auffallen.
Sortierung = Literal["name", "name-ab", "sichtbarkeit", "verbindungen", "zeitpunkt"]

SORTIERUNGEN: tuple[str, ...] = ("name", "name-ab", "sichtbarkeit", "verbindungen", "zeitpunkt")

# SL-geheim zuerst: die Spielleitung will beim Durchsehen erkennen, was noch
# nicht freigegeben ist, nicht was längst offen liegt.
_SICHTBARKEIT_RANG = {"GM": 0, "SPEZIFISCH": 1, "ALLE": 2}


def normalisiere(text: str) -> str:
    """Kleinschreibung ohne Umlaute — damit "Uberfall" auch "Überfall" findet.

    Am Spieltisch tippt niemand Umlaute sauber, und auf dem Tablet erst recht
    nicht. NFKD zerlegt "ü" in "u" + Trema, die kombinierenden Zeichen fallen
    weg. ß wird vorher ersetzt, es hat keine Zerlegung.
    """
    ohne_ss = text.replace("ß", "ss").replace("ẞ", "ss")
    zerlegt = unicodedata.normalize("NFKD", ohne_ss)
    return "".join(z for z in zerlegt if not unicodedata.combining(z)).casefold()


def klartext(roh: str | None) -> str:
    """Holt den lesbaren Text aus einem TipTap-Dokument.

    Beschreibung und Notizen liegen als TipTap-JSON in einem String. Ohne
    diese Umwandlung würde eine Suche nach "text" in jedem Dokument anschlagen,
    weil der Typname `"text"` im JSON steht. Altbestand in Klartext (vor dem
    Rich-Text-Umbau) geht unverändert durch.
    """
    if not roh:
        return ""
    try:
        dokument = json.loads(roh)
    except (json.JSONDecodeError, TypeError):
        return roh
    if not isinstance(dokument, dict):
        return roh

    stuecke: list[str] = []

    def sammle(knoten: object) -> None:
        if isinstance(knoten, dict):
            if knoten.get("type") == "text" and isinstance(knoten.get("text"), str):
                stuecke.append(knoten["text"])
            inhalt = knoten.get("content")
            if isinstance(inhalt, list):
                for kind in inhalt:
                    sammle(kind)
        elif isinstance(knoten, list):
            for kind in knoten:
                sammle(kind)

    sammle(dokument)
    return " ".join(stuecke)


def durchsuchbarer_text(entitaet: dict, namensfeld: str) -> str:
    """Alles, worin gesucht wird: Name/Titel, Zeitpunkt, Beschreibung, Notizen."""
    teile = [
        str(entitaet.get(namensfeld) or ""),
        str(entitaet.get("timestamp") or ""),
        klartext(entitaet.get("description")),
        klartext(entitaet.get("notes")),
    ]
    return normalisiere(" ".join(teile))


def nach_suche(entitaeten: list[dict], begriff: str | None, namensfeld: str = "name") -> list[dict]:
    """Alle Wörter des Begriffs müssen vorkommen (UND, nicht Phrase).

    "chrome bar" findet den Eintrag, in dem beides steht, unabhängig von der
    Reihenfolge — beim Suchen tippt man Stichwörter, keine Sätze.
    """
    if not begriff or not begriff.strip():
        return entitaeten
    woerter = [w for w in normalisiere(begriff).split() if w]
    if not woerter:
        return entitaeten
    return [e for e in entitaeten if all(w in durchsuchbarer_text(e, namensfeld) for w in woerter)]


def _kante_beruehrt(kante: dict, entitaets_id: str) -> str | None:
    """Gibt die Gegenseite zurück, wenn die Kante diese Entität berührt.

    Bewusst richtungsunabhängig: ob die Spielleitung "Kira → trifft sich in →
    Bar" oder "Bar → Stammgast → Kira" angelegt hat, ist eine Frage des
    Erzählens, nicht der Zugehörigkeit.
    """
    if kante.get("vonId") == entitaets_id:
        return kante.get("zuId")
    if kante.get("zuId") == entitaets_id:
        return kante.get("vonId")
    return None


def verbindungszahl(entitaeten: Iterable[dict], kanten: list[dict]) -> dict[str, int]:
    """Wie viele sichtbare Verbindungen je Entität — für Anzeige und Sortierung."""
    zahl = {e["id"]: 0 for e in entitaeten}
    for kante in kanten:
        for seite in ("vonId", "zuId"):
            kennung = kante.get(seite)
            if kennung in zahl:
                zahl[kennung] += 1
    return zahl


def nach_beziehung(
    entitaeten: list[dict],
    kanten: list[dict],
    ziel_id: str | None = None,
    typ: str | None = None,
) -> list[dict]:
    """Nur Entitäten, die über eine echte Graphkante passen.

    `ziel_id` — verbunden mit genau dieser Entität (Ort, Event, Person,
    Gegenstand). `typ` — über eine Verbindung dieser Bezeichnung. Beides
    zusammen: "Gegner beim Überfall auf die Bank". Nur `typ`: "alle Gegner,
    egal wo".

    Die Kantenliste muss bereits sichtbarkeitsgefiltert sein — eine geheime
    Verbindung darf einen Spieler nicht auf einen NPC stossen lassen.
    """
    if not ziel_id and not typ:
        return entitaeten

    typ_norm = normalisiere(typ) if typ else None

    def passt(entitaet: dict) -> bool:
        for kante in kanten:
            gegenseite = _kante_beruehrt(kante, entitaet["id"])
            if gegenseite is None:
                continue
            if ziel_id and gegenseite != ziel_id:
                continue
            if typ_norm and normalisiere(str(kante.get("typ") or "")) != typ_norm:
                continue
            return True
        return False

    return [e for e in entitaeten if passt(e)]


def sortiere(
    entitaeten: list[dict],
    sortierung: str | None,
    namensfeld: str = "name",
    kanten: list[dict] | None = None,
) -> list[dict]:
    """Sortiert eine bereits gefilterte Liste.

    Der Name ist immer der zweite Schlüssel: sonst springt die Liste bei
    Gleichstand von Aufruf zu Aufruf, und mitten im Spiel sucht man den
    Eintrag, der eben noch woanders stand.
    """

    def name_von(e: dict) -> str:
        return normalisiere(str(e.get(namensfeld) or ""))

    if sortierung in (None, "", "name"):
        return sorted(entitaeten, key=name_von)
    if sortierung == "name-ab":
        return sorted(entitaeten, key=name_von, reverse=True)
    if sortierung == "sichtbarkeit":
        return sorted(
            entitaeten,
            key=lambda e: (_SICHTBARKEIT_RANG.get(e.get("sichtbarkeit") or "GM", 0), name_von(e)),
        )
    if sortierung == "verbindungen":
        zahl = verbindungszahl(entitaeten, kanten or [])
        return sorted(entitaeten, key=lambda e: (-zahl.get(e["id"], 0), name_von(e)))
    if sortierung == "zeitpunkt":
        # Leerer Zeitpunkt ans Ende: ein Event ohne Angabe ist noch nicht
        # eingeordnet, es gehört nicht vor "Session 1".
        return sorted(
            entitaeten,
            key=lambda e: (
                0 if str(e.get("timestamp") or "").strip() else 1,
                normalisiere(str(e.get("timestamp") or "")),
                name_von(e),
            ),
        )
    return sorted(entitaeten, key=name_von)


def filteroptionen(
    entitaeten: list[dict],
    kanten: list[dict],
    knoten_beschriftung: dict[str, tuple[str, str]],
) -> dict:
    """Womit sich diese Liste tatsächlich filtern lässt.

    Nur Beziehungsarten und Ziele, zu denen es echte Kanten von mindestens
    einer der übergebenen Entitäten gibt. Ein Dropdown, das ins Leere führt,
    ist schlimmer als keins — man sucht dann den Fehler bei sich.

    `knoten_beschriftung` bildet Entitäts-ID auf (Art, Name) ab; sie muss aus
    einer bereits sichtbarkeitsgefilterten Quelle stammen, sonst verriete ein
    Filterziel den Namen eines geheimen NPCs.
    """
    eigene = {e["id"] for e in entitaeten}
    typen: set[str] = set()
    ziele: dict[str, int] = {}

    for kante in kanten:
        for meine_seite, andere_seite in (("vonId", "zuId"), ("zuId", "vonId")):
            if kante.get(meine_seite) not in eigene:
                continue
            typ = str(kante.get("typ") or "").strip()
            if typ:
                typen.add(typ)
            gegenueber = kante.get(andere_seite)
            # Eine Kante zwischen zwei Einträgen derselben Liste (NPC kennt
            # NPC) taucht zweimal auf — einmal je Richtung. Das ist gewollt:
            # beide Seiten sind ein gültiges Filterziel.
            if gegenueber and gegenueber in knoten_beschriftung:
                ziele[gegenueber] = ziele.get(gegenueber, 0) + 1

    ziel_liste = [
        {
            "id": kennung,
            "kind": knoten_beschriftung[kennung][0],
            "label": knoten_beschriftung[kennung][1],
            "anzahl": anzahl,
        }
        for kennung, anzahl in ziele.items()
    ]
    # Nach Art gruppiert, darin alphabetisch: Orte stehen beisammen, Events
    # beisammen. Wer nach "der Bar" filtern will, sucht nicht in einer nach
    # Trefferzahl sortierten Liste.
    ziel_liste.sort(key=lambda z: (z["kind"], normalisiere(z["label"])))
    return {"typen": sorted(typen, key=normalisiere), "ziele": ziel_liste}
