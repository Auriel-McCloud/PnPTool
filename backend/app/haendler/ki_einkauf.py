"""KI-Charakter geht im Tutorial-Shop einkaufen (11.10.2026, Marks Wunsch).

Ein von der KI erzeugter Charakter (Ideenschmiede ✨-Charakter, Massenidee,
Mentor/Kontakt-Pipeline — alle laufen über `ki/routes.py::_idee_anlegen`)
bekam bisher Startkapital, gab aber nichts davon aus — wirkte unausgerüstet.
Diese Funktion lässt ihn im TUTORIAL-SHOP (derselbe Laden, den auch Spieler
im Freebees-Schritt sehen) sinnvoll einkaufen: Waffen/Rüstung/Cyberware/etc.
passend zu Konzept, Weg und Fertigkeiten.

Kauft NUR aus dem bestehenden Sortiment — erfindet nichts Neues (Mark füllt
den Tutorial-Shop gerade händisch, die KI soll genau DAS nutzen, dasselbe
Vorrang-Prinzip wie überall sonst in der Ideenschmiede: bevorzugt Bestehendes
wiederverwenden). Kein Tutorial-Shop in der Kampagne oder leeres Sortiment =
No-Op, kein Fehlerpfad.

Die KI muss ihr Budget NICHT komplett ausgeben (Marks Entscheidung
11.10.2026: "entscheidet selbst sinnvoll") — ein realistischer Bargeldrest
ist in Ordnung.

Läuft serverseitig ohne Viewer/HTTP-Request, anders als
`haendler/routes.py::kaufen` (kein Bestätigungs-Popup, kein fremder Käufer-
Kontext nötig) — nutzt aber denselben Kern-Mechanismus: Preis abziehen,
`assign_copy` für Vorlagen, echter Besitzerwechsel für Unikate. Bewusst OHNE
die Digital-Bestellung-Logik und das Rassen-Gratis-Erstkauf-Feature von
`kaufen()` — beides bringt für einen automatisch generierten Hintergrund-
Charakter keinen Mehrwert, der die zusätzliche Komplexität rechtfertigt.
"""

from pydantic import BaseModel

from app.entities.repository import PERSON_FIELDS, update_node
from app.haendler import repository as haendler_repository
from app.items import repository as items_repository
from app.ki.client import generiere_json

_SYSTEM = (
    "Du bist dieser Charakter und gehst in einem Laden einkaufen, bevor das "
    "Abenteuer beginnt (deutsches Cyberpunk-Pen-and-Paper NeotopiA). Wähle "
    "NUR aus der folgenden Liste bereits vorhandener Waren — erfinde NICHTS "
    "Neues und nenne keine gegenstandId, die nicht in der Liste steht. Kaufe, "
    "was zu Konzept/Fertigkeiten/Weg sinnvoll passt (ein Kampf-Charakter "
    "typischerweise eine Waffe, nicht automatisch jeder Magier Cyberware). "
    "Bleib innerhalb des Budgets: die Summe aller gewählten Preise darf es "
    "nicht überschreiten. Du musst nicht alles ausgeben — ein realistischer "
    "Rest Bargeld ist in Ordnung — aber ein spielbereiter Charakter hat "
    "meist mindestens etwas Grundausstattung, wenn das Sortiment dazu etwas "
    "hergibt. Nenne jede gewählte Ware höchstens einmal."
)

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "kaeufe": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "gegenstandId": {"type": "STRING"},
                },
                "required": ["gegenstandId"],
            },
        },
    },
    "required": ["kaeufe"],
}


class EinkaufErgebnis(BaseModel):
    gekauft: list[str] = []
    ausgegeben: int = 0
    kapitalRest: int = 0


async def einkaufen(
    campaign_id: str, person_id: str, budget: int, charakterkontext: str
) -> EinkaufErgebnis | None:
    """Lässt die KI für `person_id` im Tutorial-Shop der Kampagne einkaufen.

    `budget` ist das volle Freebee-Startkapital — wird NICHT zwangsläufig
    komplett verbraucht. Schreibt den tatsächlichen Rest als `kapital` auf
    die Person. Gibt None zurück (No-Op), wenn kein Tutorial-Shop existiert,
    das Sortiment leer ist, oder die KI nichts Gültiges ausgewählt hat.
    """
    if budget <= 0:
        return None
    shop = await haendler_repository.tutorial_shop(campaign_id)
    if shop is None:
        return None
    sortiment = await haendler_repository.sortiment(campaign_id, shop["id"])
    if not sortiment:
        return None

    def _preis(eintrag: dict) -> int:
        rabatt = eintrag.get("rabattProzent") or 0
        return int(eintrag["preis"]) * (100 - rabatt) // 100

    sortiment_index = {e["gegenstandId"]: e for e in sortiment}
    liste_text = "\n".join(
        f"- ({e['gegenstandId']}) {e['name']} [{e['typ']}, {_preis(e)}¥]" for e in sortiment
    )
    prompt = (
        f"Charakter:\n{charakterkontext}\n\nBudget: {budget}¥\n\n"
        f"Sortiment des Ladens:\n{liste_text}"
    )
    try:
        ergebnis = await generiere_json(prompt, _SYSTEM, _SCHEMA, campaign_id=campaign_id)
    except Exception:
        # KI-Fehler darf den Charakter nicht kaputt machen — er bleibt dann
        # halt unausgerüstet (derselbe Grundsatz wie der Bild-Schritt in
        # ki_vorschlag.py::ware_anlegen).
        return None

    rest = budget
    gekauft_namen: list[str] = []
    gesehen: set[str] = set()
    for eintrag in ergebnis.get("kaeufe") or []:
        gegenstand_id = (eintrag.get("gegenstandId") or "").strip()
        sortiment_eintrag = sortiment_index.get(gegenstand_id)
        if not sortiment_eintrag or gegenstand_id in gesehen:
            continue
        preis = _preis(sortiment_eintrag)
        if preis > rest:
            continue
        gegenstand = await items_repository.get_gegenstand(campaign_id, gegenstand_id)
        if gegenstand is None:
            continue
        if gegenstand["istVorlage"]:
            gekauft = await items_repository.assign_copy(
                campaign_id, gegenstand, person_id, "SPEZIFISCH", [person_id]
            )
        else:
            gekauft = await items_repository.transfer_owner(campaign_id, gegenstand_id, person_id)
            if gekauft:
                await haendler_repository.verkauft_entfernen(campaign_id, shop["id"], gegenstand_id)
        if not gekauft:
            continue
        gesehen.add(gegenstand_id)
        rest -= preis
        gekauft_namen.append(sortiment_eintrag["name"])

    if not gekauft_namen:
        return None

    await update_node("Person", PERSON_FIELDS, campaign_id, person_id, {"kapital": rest})
    return EinkaufErgebnis(gekauft=gekauft_namen, ausgegeben=budget - rest, kapitalRest=rest)
