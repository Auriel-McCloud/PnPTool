"""Rast-Mechanik: Heilung über die Zeit, kein Würfeln.

Mark, 11.10.2026 (Korrektur 12.10.2026, siehe docs/api/rast.md): eine
SL-Aktion "Rasten" heilt einen oder mehrere PCs nach einer festen Formel.
Pro ausgewählter Person ist EIN Klick = EINE Rast:

1. `schadenSchlag` -> 0 (vollständig geheilt).
2. `schadenSchwer > 0` ("Tödlich" in der Anzeige): -1, sofort, jede Rast —
   kein Zähler, kein Warten.
3. Erst wenn `schadenSchwer` NACH Schritt 2 bei 0 steht UND noch
   `schadenAggraviert > 0` ("Schwerheilbar") da ist, läuft der persistente
   Zähler `schwerHeilZaehler` mit: += 1 pro Rast. Erreicht er dabei >= 7,
   läuft er über: -7, UND `schadenAggraviert` -1. Solange noch Tödlich-
   Schaden offen ist, bleibt der Zähler stehen — Schwerheilbar heilt erst,
   wenn der PC vom tödlichen Schaden runter ist (Mark: ursprünglich hatte
   die Formel das verkehrt herum, der Zähler lief nur MIT offenem Tödlich-
   Schaden und fror ein, sobald der bei 0 stand).
4. Ist die Person NACH 1-3 vollständig gesund, heilt JEDES getragene
   Rüstungsteil mit `istNatuerlich=true` und Kästchen-Defizit +1 (gecappt
   auf das live aus der Widerstandsfähigkeit berechnete Max, siehe
   `kampf/ruestung.py::anwende_natuerliche_ruestung`) — gilt auch schon in
   DIESER Rast, nicht erst ab der nächsten.

Daneben der Fallback-Knopf "Vollständige Heilung" — keine Bedingungen, kein
Würfeln, heilt sofort alles inklusive aller getragenen Rüstungsteile (auch
nicht-natürlicher) auf vollen Max.

Rechnet rein (keine Datenbankzugriffe), dieselbe Motivation wie
`kampf/ruestung.py`/`items/chirurgie.py`: die Formel steht an einer Stelle
und ist ohne DB testbar.
"""

# Wraparound-Schwelle für den Schwerheilbar-Heil-Zähler -> ein Punkt Schwerheilbar
# heilt erst, wenn SIEBEN Rasten OHNE offenen Tödlich-Schaden vergangen sind
# (Marks Vorgabe).
SCHWER_HEIL_SCHWELLE = 7


def person_aenderung(person: dict) -> dict:
    """Eine Rast für eine Person: Schritte 1-3 der Formel.

    Gibt NUR die geänderten Personenfelder zurück — der Aufrufer schreibt
    sie (siehe traits/routes.py::personen_rasten).
    """
    schwer = max(0, int(person.get("schadenSchwer") or 0))
    aggraviert = max(0, int(person.get("schadenAggraviert") or 0))
    zaehler = max(0, int(person.get("schwerHeilZaehler") or 0))

    if schwer > 0:
        schwer -= 1

    if schwer == 0 and aggraviert > 0:
        zaehler += 1
        if zaehler >= SCHWER_HEIL_SCHWELLE:
            zaehler -= SCHWER_HEIL_SCHWELLE
            aggraviert -= 1

    return {
        "schadenSchlag": 0,
        "schadenSchwer": schwer,
        "schadenAggraviert": aggraviert,
        "schwerHeilZaehler": zaehler,
    }


def ist_vollstaendig_gesund(aenderung: dict) -> bool:
    """Schritt 4 der Formel: NUR dann heilt natürliche Rüstung mit."""
    return (
        aenderung.get("schadenSchlag", 0) == 0
        and aenderung.get("schadenSchwer", 0) == 0
        and aenderung.get("schadenAggraviert", 0) == 0
    )


def ruestung_heilung(teile: list[dict]) -> list[dict]:
    """Welche Rüstungsteile bei einer Rast +1 Kästchen heilen.

    Nur `istNatuerlich`-Teile mit einem Kästchen-Defizit — normale Rüstung
    heilt über Rast nicht mit (die hat ihren eigenen Reparatur-Weg).
    `teile` muss bereits das LIVE berechnete Max tragen (siehe
    `kampf/ruestung.py::anwende_natuerliche_ruestung`); diese Funktion kennt
    nur die Kästchen-Zahlen, keine Widerstandsfähigkeit.
    """
    folgen: list[dict] = []
    for teil in teile:
        if not teil.get("istNatuerlich"):
            continue
        aktuell = int(teil.get("ruestungKaestchenAktuell") or 0)
        maximum = int(teil.get("ruestungKaestchenMax") or 0)
        if aktuell < maximum:
            folgen.append({"id": teil["id"], "ruestungKaestchenAktuell": aktuell + 1})
    return folgen


def vollheilung_person() -> dict:
    """Fallback-Knopf "für den Fall der Fälle": keine Bedingungen, kein
    Würfeln — setzt Schaden UND den Heil-Zähler auf 0."""
    return {
        "schadenSchlag": 0,
        "schadenSchwer": 0,
        "schadenAggraviert": 0,
        "schwerHeilZaehler": 0,
    }


def vollheilung_ruestung(teile: list[dict]) -> list[dict]:
    """Jedes getragene Rüstungsteil (auch nicht-natürliches) sofort auf den
    vollen Max — Gegenstück zu `ruestung_heilung`, ohne die
    `istNatuerlich`-Einschränkung."""
    folgen: list[dict] = []
    for teil in teile:
        aktuell = int(teil.get("ruestungKaestchenAktuell") or 0)
        maximum = int(teil.get("ruestungKaestchenMax") or 0)
        if aktuell < maximum:
            folgen.append({"id": teil["id"], "ruestungKaestchenAktuell": maximum})
    return folgen
