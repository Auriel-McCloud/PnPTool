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
from app.haendler import repository as haendler_repository
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


async def _ausfuehren_shop_kauf(campaign_id: str, verhandlung: dict) -> dict:
    """Kontext: {"haendlerId": str, "gegenstandId": str}. Führt den Kauf zum
    verhandelten Preis (Verhandlung.gesamtbetrag) durch — der eigentliche
    Kauf-Code liegt bewusst in haendler/repository.py, damit Vorlage-Kopie
    vs. Unikat-Besitzerwechsel nicht doppelt gepflegt wird (dasselbe Muster
    wie /haendler/{id}/kaufen, nur mit dem Verhandlungspreis statt dem
    Sortimentspreis). Nur bei physischen Käufen einsetzbar — digitale Käufe
    (Vertriebsart DIGITAL) kennen kein Verhandeln, siehe
    docs/api/haendler.md."""
    kontext = verhandlung["kontext"]
    haendler_id = kontext["haendlerId"]
    gegenstand_id = kontext["gegenstandId"]
    person_id = verhandlung["empfaengerPersonId"]
    preis = verhandlung["gesamtbetrag"]

    person = await entities_repository.get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        raise VerhandlungsFehler("Käufer nicht mehr gefunden")

    kapital = int(person.get("kapital") or 0)
    if kapital < preis:
        raise VerhandlungsFehler(f"Guthaben reicht nicht mehr — {kapital}¥ verfügbar, {preis}¥ nötig")

    gegenstand = await items_repository.get_gegenstand(campaign_id, gegenstand_id)
    if gegenstand is None:
        raise VerhandlungsFehler("Die Ware ist nicht mehr auffindbar")

    if gegenstand["istVorlage"]:
        gekauft = await items_repository.assign_copy(campaign_id, gegenstand, person_id, "SPEZIFISCH", [person_id])
    else:
        gekauft = await items_repository.transfer_owner(campaign_id, gegenstand_id, person_id)
        await haendler_repository.verkauft_entfernen(campaign_id, haendler_id, gegenstand_id)
    if gekauft is None:
        raise VerhandlungsFehler("Kauf fehlgeschlagen")

    kapital_neu = kapital - preis
    await entities_repository.update_node("Person", PERSON_FIELDS, campaign_id, person_id, {"kapital": kapital_neu})
    return {"gegenstand": gekauft, "kapitalNeu": kapital_neu}


async def _ausfuehren_gegenstand_weitergabe(campaign_id: str, verhandlung: dict) -> dict:
    """Kontext: {"gegenstandId": str}. Übergibt einen Gegenstand von Spieler
    zu Spieler — kein Geld beteiligt, deshalb keine Kapitalprüfung wie bei
    den anderen Verhandlungsarten. Prüft trotzdem noch einmal live, dass der
    Gegenstand tatsächlich noch beim erwarteten Absender liegt (zwischen
    Angebot und Antwort kann er anderweitig verschwunden sein, z.B. verkauft
    oder weggeworfen)."""
    kontext = verhandlung["kontext"]
    gegenstand_id = kontext["gegenstandId"]
    empfaenger_id = verhandlung["empfaengerPersonId"]

    gegenstand = await items_repository.get_gegenstand(campaign_id, gegenstand_id)
    if gegenstand is None:
        raise VerhandlungsFehler("Der Gegenstand ist nicht mehr auffindbar")

    aktueller_besitzer = await items_repository.get_owner_id(campaign_id, gegenstand_id)
    if aktueller_besitzer != kontext.get("absenderPersonId"):
        raise VerhandlungsFehler("Der Gegenstand gehört nicht mehr dem Absender")

    uebergeben = await items_repository.transfer_owner(campaign_id, gegenstand_id, empfaenger_id)
    if uebergeben is None:
        raise VerhandlungsFehler("Übergabe fehlgeschlagen")
    return {"gegenstand": uebergeben}


# Dispatch-Tabelle: Verhandlungsart -> Ausführungsfunktion. Erweitern statt
# umbauen, wenn eine neue Art dazukommt.
_AUSFUEHRUNG = {
    "RUESTUNG_REPARATUR": _ausfuehren_ruestung_reparatur,
    "SHOP_KAUF": _ausfuehren_shop_kauf,
    "GEGENSTAND_WEITERGABE": _ausfuehren_gegenstand_weitergabe,
}


async def ausfuehren(campaign_id: str, verhandlung: dict) -> dict:
    """Führt die Nebenwirkung der Annahme aus. Wirft VerhandlungsFehler bei Problemen."""
    funktion = _AUSFUEHRUNG.get(verhandlung["art"])
    if funktion is None:
        raise VerhandlungsFehler(f"Unbekannte Verhandlungsart: {verhandlung['art']}")
    return await funktion(campaign_id, verhandlung)
