"""Schulden / Kredithai — reine Auswahl- und Rating-Logik, ohne Datenbank.

Kredit-Freebees erzeugen den Systemhintergrund „Schulden“. Der Hai ist
entweder ein bestehender NPC mit Flag oder wird später per KI angelegt.
"""


def schulden_punkte(kredit_freebees: int) -> int:
    """1 Kredit-Freebee = 1 Schulden-Punkt. 0 Kredit = 0, kein Hai."""
    return max(0, int(kredit_freebees))


def bestehenden_kredithai(npcs: list[dict]) -> dict | None:
    """Den ältesten markierten Hai, sonst None (dann neu anlegen)."""
    hai = [n for n in npcs if n.get("istKredithai")]
    if not hai:
        return None
    return sorted(hai, key=lambda n: (n.get("erstelltAm") or "", n.get("id") or ""))[0]


def kredithai_rassenkandidaten(rassen: list[dict]) -> list[dict]:
    """Freigegebene Rassen mit Häkchen, sonst alle übergebenen.

    Kein hart verdrahteter Rassenname — Umbenennen im Baukasten darf
    die Auswahl nicht lautlos leeren.
    """
    markiert = [r for r in rassen if r.get("kannKredithai")]
    return markiert if markiert else list(rassen)
