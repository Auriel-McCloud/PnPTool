"""Was bei Annahme einer Verhandlung tatsächlich passiert.

Eine Dispatch-Tabelle nach `art` (siehe schemas.py::VerhandlungsArt) statt
einer grossen if/elif-Kette — ein neuer Anwendungsfall (z.B. künftig
"SHOP_KAUF" für den Warenkorb) fügt hier nur einen neuen Eintrag hinzu, ohne
Bestehendes anzufassen.

Jede Ausführungsfunktion bekommt die Verhandlung (Positionen, Gesamtbetrag,
Kontext) und liefert entweder ein Ergebnis-dict (für die Erfolgsmeldung im
Popup) oder wirft `VerhandlungsFehler` mit einer für den SL verständlichen
Meldung (z.B. Guthaben reicht nicht mehr — kann zwischen Vorschlag und
Antwort passiert sein).
"""

from app.entities import repository as entities_repository
from app.entities.repository import PERSON_FIELDS
from app.items import repository as items_repository
from app.kampf.ruestung import repariere


class VerhandlungsFehler(Exception):
    """Die Annahme lässt sich nicht ausführen (z.B. Guthaben reicht nicht mehr)."""


async def _ausfuehren_ruestung_reparatur(campaign_id: str, verhandlung: dict) -> dict:
    """Kontext: {"gegenstandId": str, "kaestchen": int}. Zieht das Kapital
    des Empfängers ab und repariert die Rüstung um `kaestchen`.

    Beide Prüfungen (Guthaben, Gegenstand noch vorhanden) laufen hier noch
    einmal, obwohl der Preis schon beim Vorschlag berechnet wurde — zwischen
    Vorschlag und Antwort kann Zeit vergehen, in der sich beides geändert
    haben kann (siehe haendler/routes.py::kauf für dasselbe Muster).
    """
    kontext = verhandlung["kontext"]
    gegenstand_id = kontext["gegenstandId"]
    kaestchen = int(kontext["kaestchen"])
    person_id = verhandlung["empfaengerPersonId"]

    person = await entities_repository.get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise VerhandlungsFehler("Empfänger nicht mehr gefunden")

    kapital = int(person.get("kapital") or 0)
    preis = verhandlung["gesamtbetrag"]
    if kapital < preis:
        raise VerhandlungsFehler(f"Guthaben reicht nicht mehr — {kapital}¥ verfügbar, {preis}¥ nötig")

    gegenstand = await items_repository.get_gegenstand(campaign_id, gegenstand_id)
    if gegenstand is None or gegenstand["typ"] != "Rüstung":
        raise VerhandlungsFehler("Die Rüstung ist nicht mehr auffindbar")

    ergebnis = repariere(gegenstand["ruestungKaestchenAktuell"], gegenstand["ruestungKaestchenMax"], kaestchen)
    aktualisiert = await items_repository.update_gegenstand(
        campaign_id, gegenstand_id, {"ruestungKaestchenAktuell": ergebnis["kaestchenNeu"]}
    )
    await entities_repository.update_node(
        "Person", PERSON_FIELDS, campaign_id, person_id, {"kapital": kapital - preis}
    )
    return {"gegenstand": aktualisiert, "kapitalNeu": kapital - preis}


# Dispatch-Tabelle: Verhandlungsart -> Ausführungsfunktion. Erweitern statt
# umbauen, wenn eine neue Art dazukommt.
_AUSFUEHRUNG = {
    "RUESTUNG_REPARATUR": _ausfuehren_ruestung_reparatur,
}


async def ausfuehren(campaign_id: str, verhandlung: dict) -> dict:
    """Führt die Nebenwirkung der Annahme aus. Wirft VerhandlungsFehler bei Problemen."""
    funktion = _AUSFUEHRUNG.get(verhandlung["art"])
    if funktion is None:
        raise VerhandlungsFehler(f"Unbekannte Verhandlungsart: {verhandlung['art']}")
    return await funktion(campaign_id, verhandlung)
