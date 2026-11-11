"""Reine Fachlogik der Critter-Pets — ohne Datenbank, ohne WebSocket.

Mark, 11.11.2026: das Pet läuft nur zu eingeloggten Party-Mitgliedern, nie
zur Spielleitung. Verlässt es einen Bildschirm am Rand, taucht es bei einem
anderen Mitglied auf der Gegenseite wieder auf — nicht in derselben Sekunde.
"""

import random

# Welche Sprites es gibt. Der Name ist zugleich der Ordner unter
# frontend/public/pets/. Jeder Critter kann später ein eigenes bekommen.
# `baerbel` (11.11.2026) ist kein Tier, sondern ein Gegenstand: die sprechende
# Bibel/das Zauberbuch, das fliegt (frontend/src/pets/flug.ts).
PET_ARTEN = ("drache", "baerbel")

# Häufchen bleiben liegen, wenn das Pet weiterzieht — aber nicht unbegrenzt.
# Wird es mehr, verschwindet das älteste (je Art gezählt).
HAEUFCHEN_MAX = 12

# Was ein Pet auf einem Bildschirm hinterlassen kann: Häufchen und
# Brandflecken vom Feuerniesen (Mark, 11.11.2026). Beides bleibt liegen,
# bis der Spieler es wegmacht (antippen bzw. sauberwischen).
# Bärbel verliert stattdessen Seiten, die zerknittert liegen bleiben; ihr
# Tentakelmonster hinterlässt Schleim (wegwischen wie Brandflecken).
SPUR_ARTEN = ("haeufchen", "brand", "seite", "schleim")

# Spuren, die vom Element herunterfallen können (neue Lage wird gemerkt).
FALLENDE_SPUREN = ("haeufchen", "seite")

# Pause zwischen „rechts raus“ und „links rein“ beim nächsten Tablet.
UNTERWEGS_MIN_S = 3.0
UNTERWEGS_MAX_S = 12.0

# Meldet ein Tablet nie „raus“ (Browser eingefroren, Akku leer, ohne dass
# die Leitung zuging), zieht der Server das Pet nach dieser Zeit selbst weiter.
# Großzügig: er darf bis zu 5 Minuten auf einem Popup schlafen (Mark, 11.11.),
# dazu kommen Besuch und Kletterei.
HOECHSTE_VERWEILDAUER_S = 600.0


def naechster_wirt(online: list[str], aktuell: str | None, zufall: random.Random | None = None) -> str | None:
    """Auf wessen Tablet geht es als Nächstes?

    Bevorzugt jemand anderen als den bisherigen Wirt. Ist nur einer da, kommt
    das Pet eben zu ihm zurück — es läuft raus und nach der Pause wieder rein.
    """
    if not online:
        return None
    z = zufall or random
    andere = sorted(p for p in online if p != aktuell)
    return z.choice(andere) if andere else sorted(online)[0]


def gegenseite(seite: str) -> str:
    """Rechts raus heißt beim Nächsten links rein — und umgekehrt."""
    return "links" if seite == "rechts" else "rechts"


def anteil(wert: float) -> float:
    """Bildschirmposition als Anteil 0..1 — Tablets sind verschieden groß."""
    return min(1.0, max(0.0, float(wert)))


def online_mitglieder(mitglieder: list[str], online: set[str]) -> list[str]:
    return sorted(m for m in mitglieder if m in online)
