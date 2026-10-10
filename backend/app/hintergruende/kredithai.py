"""Schulden / Kredithai — reine Auswahl- und Rating-Logik, ohne Datenbank.

Kredit-Freebees erzeugen den Systemhintergrund „Schulden“. Der Hai ist
entweder ein bestehender NPC mit Flag oder ein Stub in der Schmiede.
"""

from app.traits.erstellung import KAPITAL_JE_FREEBEE


def schulden_punkte(kredit_freebees: int) -> int:
    """1 Kredit-Freebee = 1 Schulden-Punkt. 0 Kredit = 0, kein Hai."""
    return max(0, int(kredit_freebees))


def schulden_yen(kredit_freebees: int) -> int:
    """Yen-Betrag, der in der Verbindungsbeschreibung steht."""
    return schulden_punkte(kredit_freebees) * KAPITAL_JE_FREEBEE


def schulden_beschreibung(kredit_freebees: int) -> str:
    """Text auf VERBINDUNG.typ Schuldet, z.B. '30.000¥ aus der Erstellung'."""
    yen = schulden_yen(kredit_freebees)
    return f"{yen:,}¥ aus der Erstellung".replace(",", ".")


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


def kredithai_rasse(rassen: list[dict]) -> str:
    """Erste Kandidatin. Leer, wenn die Kampagne keine Rasse hat."""
    kandidaten = kredithai_rassenkandidaten(rassen)
    if not kandidaten:
        return ""
    return (kandidaten[0].get("name") or "").strip()
