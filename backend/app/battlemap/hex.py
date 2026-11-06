"""Axiale Hex-Geometrie für die Battlemap.

Punktiges Hex (pointy-top), Koordinaten (q, r). Distanz und Nachbarn sind
die Standardformeln; das Y für große Tokens sind drei zusammenhängende
Felder um einen Anker.
"""

from collections import deque

# Ost, Nordost, Nordwest, West, Südwest, Südost (pointy-top).
NACHBARN_DELTA = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))


def distanz(q1: int, r1: int, q2: int, r2: int) -> int:
    return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2


def nachbarn(q: int, r: int) -> list[tuple[int, int]]:
    return [(q + dq, r + dr) for dq, dr in NACHBARN_DELTA]


def y_felder(q: int, r: int, *, gross: bool, drehung: int = 0) -> set[tuple[int, int]]:
    """Belegte Hex: eins, oder drei im Y (Anker plus zwei aufeinanderfolgende Nachbarn)."""
    if not gross:
        return {(q, r)}
    k = drehung % 6
    dq1, dr1 = NACHBARN_DELTA[k]
    dq2, dr2 = NACHBARN_DELTA[(k + 1) % 6]
    return {(q, r), (q + dq1, r + dr1), (q + dq2, r + dr2)}


def reichweite(*, sportlichkeit: int, fliegen: int | None) -> int:
    """Laufen 3+Sportlichkeit, Drohnen 3+Fliegen×2. fliegen is not None = Drohne."""
    if fliegen is not None:
        return 3 + int(fliegen) * 2
    return 3 + int(sportlichkeit or 0)


def naechster_freier(q: int, r: int, belegt: set[tuple[int, int]]) -> tuple[int, int] | None:
    """Startfeld, sonst BFS zum nächsten nicht belegten Hex."""
    start = (q, r)
    if start not in belegt:
        return start
    gesehen = {start}
    warteschlange: deque[tuple[int, int]] = deque([start])
    while warteschlange:
        hier = warteschlange.popleft()
        for n in nachbarn(*hier):
            if n in gesehen:
                continue
            if n not in belegt:
                return n
            gesehen.add(n)
            warteschlange.append(n)
    return None


def drop_frei(
    q: int,
    r: int,
    *,
    gross: bool,
    eigene_id: str,
    belegt: dict[tuple[int, int], str],
    drehung: int = 0,
) -> bool:
    """Ob der Drop auf (q,r) niemanden außer uns überdeckt."""
    for feld in y_felder(q, r, gross=gross, drehung=drehung):
        besitzer = belegt.get(feld)
        if besitzer is not None and besitzer != eigene_id:
            return False
    return True


def spawn_platz(
    q: int,
    r: int,
    *,
    gross: bool,
    belegt: dict[tuple[int, int], str],
) -> tuple[int, int, int] | None:
    """Erstes freies Ankerfeld ab (q,r), mit passender Y-Drehung."""
    start = (q, r)
    gesehen = {start}
    warteschlange: deque[tuple[int, int]] = deque([start])
    while warteschlange:
        hq, hr = warteschlange.popleft()
        drehungen = range(6) if gross else (0,)
        for dreh in drehungen:
            if drop_frei(hq, hr, gross=gross, drehung=dreh, eigene_id="", belegt=belegt):
                return hq, hr, dreh
        for n in nachbarn(hq, hr):
            if n in gesehen:
                continue
            gesehen.add(n)
            warteschlange.append(n)
    return None
