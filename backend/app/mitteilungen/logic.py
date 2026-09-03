"""Fachlogik der SL-Mitteilungen — ohne Datenbank, ohne WebSocket.

Eine Mitteilung ist ein Popup der Spielleitung: "Würfelt für Initiative",
eine Warnung, später ein Bild oder eine Karte. Sie hat bewusst **keinen
Absender** — sie kommt aus der Spielwelt, nicht von einer Person
(docs/phase-5-messenger.md).

Sie wird gespeichert und nicht nur gesendet: Wessen Tablet gerade schläft,
soll die Initiative-Ansage nachlesen können statt sie zu verpassen.
"""

# Was eine Mitteilung sein kann. TEXT ist gebaut; BILD ist vorgesehen und
# wird bereits durchgereicht, damit später kein Datenmodell wandern muss.
ARTEN = ("TEXT", "BILD")


def empfaenger_aufloesen(an_alle: bool, empfaenger_ids: list[str], alle_pc_ids: list[str]) -> list[str]:
    """Wer bekommt die Mitteilung wirklich?

    `an_alle` gewinnt über eine mitgegebene Liste — sonst wäre unklar, was
    gilt, wenn beides gesetzt ist.

    Genannte IDs werden gegen die Spielercharaktere der Kampagne geprüft:
    Eine Person-ID aus einer fremden Kampagne darf nicht durchrutschen.
    Reihenfolge bleibt erhalten, Doppelte fallen weg.
    """
    if an_alle:
        return list(alle_pc_ids)

    erlaubt = set(alle_pc_ids)
    gesehen: set[str] = set()
    ergebnis: list[str] = []
    for pid in empfaenger_ids:
        if pid in erlaubt and pid not in gesehen:
            gesehen.add(pid)
            ergebnis.append(pid)
    return ergebnis


def darf_empfangen(mitteilung: dict, viewer_role: str, viewer_person_id: str | None) -> bool:
    """Darf dieser Betrachter die Mitteilung sehen?

    Die Spielleitung sieht alles (sie hat es geschrieben). Ein Spieler sieht
    Rundrufe und was ausdrücklich an seinen Charakter ging.

    Ein Spieler ohne beanspruchten Charakter bekommt nur Rundrufe — er kann
    nicht Empfänger einer gerichteten Mitteilung sein.
    """
    if viewer_role == "GM":
        return True
    if mitteilung.get("anAlle"):
        return True
    if viewer_person_id is None:
        return False
    return viewer_person_id in (mitteilung.get("empfaengerIds") or [])


def ist_ungelesen(mitteilung: dict, viewer_person_id: str | None) -> bool:
    """Gelesen wird pro Person vermerkt, nicht global.

    Sonst würde das Abhaken eines Spielers die Meldung bei allen anderen
    verschwinden lassen.
    """
    if viewer_person_id is None:
        return False
    return viewer_person_id not in (mitteilung.get("gelesenVon") or [])


def zaehle_ungelesen(mitteilungen: list[dict], viewer_role: str, viewer_person_id: str | None) -> int:
    """Zahl fürs Blitz-Symbol — nur was diesen Betrachter betrifft."""
    return sum(
        1
        for m in mitteilungen
        if darf_empfangen(m, viewer_role, viewer_person_id) and ist_ungelesen(m, viewer_person_id)
    )


def fuer_viewer(mitteilungen: list[dict], viewer_role: str, viewer_person_id: str | None) -> list[dict]:
    """Filtert eine Liste auf das, was der Betrachter sehen darf."""
    return [m for m in mitteilungen if darf_empfangen(m, viewer_role, viewer_person_id)]
