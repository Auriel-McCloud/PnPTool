"""Letzte Sicht auf der Battlemap, ohne Datenbank.

Vorne sind drei von sechs Hex-Richtungen. Dahinter bleibt der Stand vom
letzten Hinsehen. Versteckt schlägt den Kegel. Rundumsicht sieht immer
den aktuellen Stand. Die Party teilt die Augen nicht.
"""

import math

from app.battlemap.hex import NACHBARN_DELTA

# Felder, die ein Spieler von einem Token sehen darf. Keine Wahrheit
# außerhalb der eigenen Augen.
SICHT_FELDER = (
    "id",
    "name",
    "personId",
    "personType",
    "begleiterId",
    "hexQ",
    "hexR",
    "hexDrehung",
    "bildUrl",
    "istGross",
    "istDrohne",
    "istFahrzeug",
    "istCritter",
    "besitzerId",
    "blickrichtung",
    "rundumsicht",
    "versteckt",
    "veraltet",
)


def sektor(von_q: int, von_r: int, nach_q: int, nach_r: int) -> int | None:
    """Hex-Richtung 0–5 vom Beobachter zum Ziel. None = dasselbe Feld."""
    dq, dr = nach_q - von_q, nach_r - von_r
    if dq == 0 and dr == 0:
        return None
    dx, dz = dq, dr
    dy = -dx - dz
    best_i = 0
    best = None
    for i, (nq, nr) in enumerate(NACHBARN_DELTA):
        nx, nz = nq, nr
        ny = -nx - nz
        punkt = dx * nx + dy * ny + dz * nz
        if best is None or punkt > best:
            best = punkt
            best_i = i
    return best_i


def vorderkegel(blick: int) -> set[int]:
    """Drei von sechs: die Blickrichtung und die beiden Nachbarn."""
    b = int(blick) % 6
    return {(b - 1) % 6, b, (b + 1) % 6}


def gehoert(token: dict, person_id: str | None) -> bool:
    if not person_id:
        return False
    if token.get("personId") == person_id:
        return True
    return token.get("besitzerId") == person_id


def zentrum(q: float, r: float) -> tuple[float, float]:
    """Hex-Mitte in Einheiten, unabhängig von Pixelgröße und Ursprung."""
    return (math.sqrt(3) * (q + r / 2), 1.5 * r)


def _orientierung(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segmente_kreuzen(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], d: tuple[float, float]) -> bool:
    """Echte Kreuzung. Ein bloßes Antippen der Enden blockiert nicht."""
    eps = 1e-8
    d1 = _orientierung(c, d, a)
    d2 = _orientierung(c, d, b)
    d3 = _orientierung(a, b, c)
    d4 = _orientierung(a, b, d)
    if abs(d1) < eps or abs(d2) < eps or abs(d3) < eps or abs(d4) < eps:
        return False
    return (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0)


def blockiert(von_q: int, von_r: int, nach_q: int, nach_r: int, waende: list[dict] | None) -> bool:
    """Schneidet die Sichtlinie eine Wand? Dasselbe Feld bleibt frei."""
    if not waende or (von_q == nach_q and von_r == nach_r):
        return False
    a = zentrum(von_q, von_r)
    b = zentrum(nach_q, nach_r)
    for wand in waende:
        try:
            c = (float(wand["ax"]), float(wand["ay"]))
            d = (float(wand["bx"]), float(wand["by"]))
        except (KeyError, TypeError, ValueError):
            continue
        if segmente_kreuzen(a, b, c, d):
            return True
    return False


def im_kegel(auge: dict, ziel: dict) -> bool:
    """Vorderer Halbkreis, oder rundum. Noch ohne Wand."""
    if auge.get("hexQ") is None or ziel.get("hexQ") is None:
        return False
    if auge.get("rundumsicht"):
        return True
    richtung = sektor(int(auge["hexQ"]), int(auge["hexR"]), int(ziel["hexQ"]), int(ziel["hexR"]))
    if richtung is None:
        return True
    return richtung in vorderkegel(int(auge.get("blickrichtung") or 0))


def sieht_live(auge: dict, ziel: dict, waende: list[dict] | None = None) -> bool:
    """Kegel oder Rundumsicht, und keine Wand dazwischen."""
    if not im_kegel(auge, ziel):
        return False
    return not blockiert(int(auge["hexQ"]), int(auge["hexR"]), int(ziel["hexQ"]), int(ziel["hexR"]), waende)


def _schnappschuss(token: dict) -> dict:
    return {feld: token.get(feld) for feld in SICHT_FELDER if feld != "veraltet"}


def start_speicher(teilnehmer: list[dict], waende: list[dict] | None = None) -> dict:
    """Kampfbeginn: jedes Auge kennt den Stand, den es sehen kann. Wände auch bei Rundumsicht."""
    augen = [t for t in teilnehmer if not t.get("zusatzzug") and t.get("hexQ") is not None]
    speicher: dict = {}
    for auge in augen:
        kontrolleur = auge.get("besitzerId") or auge.get("personId")
        ged = {}
        for ziel in augen:
            if ziel["id"] != auge["id"] and blockiert(int(auge["hexQ"]), int(auge["hexR"]), int(ziel["hexQ"]), int(ziel["hexR"]), waende):
                continue
            if ziel.get("versteckt") and not gehoert(ziel, kontrolleur):
                continue
            ged[ziel["id"]] = _schnappschuss(ziel)
        speicher[auge["id"]] = ged
    return speicher


def aktualisiere(teilnehmer: list[dict], speicher: dict | None, waende: list[dict] | None = None) -> dict:
    """Vorderen Halbkreis auffrischen. Hinten bleibt der alte Stand. Eine Wand löscht, was man gerade anschaut."""
    neu = {k: dict(v) for k, v in (speicher or {}).items()}
    augen = [t for t in teilnehmer if not t.get("zusatzzug") and t.get("hexQ") is not None]
    lebendig = {t["id"] for t in augen}
    for auge in augen:
        kontrolleur = auge.get("besitzerId") or auge.get("personId")
        ged = dict(neu.get(auge["id"]) or {})
        for ziel in augen:
            if ziel["id"] == auge["id"]:
                ged[ziel["id"]] = _schnappschuss(ziel)
                continue
            verborgen = bool(ziel.get("versteckt")) and not gehoert(ziel, kontrolleur)
            if im_kegel(auge, ziel):
                if verborgen or blockiert(int(auge["hexQ"]), int(auge["hexR"]), int(ziel["hexQ"]), int(ziel["hexR"]), waende):
                    ged.pop(ziel["id"], None)
                else:
                    ged[ziel["id"]] = _schnappschuss(ziel)
        for tid, snap in list(ged.items()):
            if tid == auge["id"] or not isinstance(snap, dict) or snap.get("hexQ") is None:
                continue
            if blockiert(int(auge["hexQ"]), int(auge["hexR"]), int(snap["hexQ"]), int(snap["hexR"]), waende):
                ged.pop(tid, None)
        neu[auge["id"]] = {k: v for k, v in ged.items() if k in lebendig}
    return {k: v for k, v in neu.items() if k in lebendig}


def ansicht(
    teilnehmer: list[dict],
    speicher: dict | None,
    *,
    rolle: str,
    person_id: str | None,
    waende: list[dict] | None = None,
) -> list[dict]:
    """Was dieser Betrachter auf die Karte bekommt. Die SL sieht die Wahrheit."""
    roh = [t for t in teilnehmer if not t.get("zusatzzug")]
    if rolle == "GM":
        return [dict(t) for t in roh]
    eigene = [t for t in roh if gehoert(t, person_id)]
    live: set[str] = set()
    geister: dict[str, dict] = {}
    for auge in eigene:
        if auge.get("hexQ") is None:
            continue
        ged = (speicher or {}).get(auge["id"]) or {}
        for tid, snap in ged.items():
            ziel = next((t for t in roh if t["id"] == tid), None)
            if ziel is None or ziel.get("hexQ") is None:
                continue
            if sieht_live(auge, ziel, waende) and not (ziel.get("versteckt") and not gehoert(ziel, person_id)):
                live.add(tid)
            elif snap.get("hexQ") is None or blockiert(
                int(auge["hexQ"]), int(auge["hexR"]), int(snap["hexQ"]), int(snap["hexR"]), waende
            ):
                continue
            else:
                geister.setdefault(tid, snap)
    for auge in eigene:
        live.add(auge["id"])
    out = []
    for t in roh:
        if t["id"] in live:
            zeile = dict(t)
            zeile["veraltet"] = False
            out.append(zeile)
        elif t["id"] in geister:
            snap = geister[t["id"]]
            zeile = dict(t)
            zeile["hexQ"] = snap.get("hexQ")
            zeile["hexR"] = snap.get("hexR")
            zeile["blickrichtung"] = snap.get("blickrichtung")
            zeile["veraltet"] = True
            zeile["versteckt"] = False
            out.append(zeile)
    return out


def ansicht_waende(
    teilnehmer: list[dict],
    *,
    rolle: str,
    person_id: str | None,
    waende: list[dict] | None,
) -> list[dict]:
    """Aktuelle Positionen, 360 Grad, Wände blockieren. Kein Gedächtnis.

    Ohne eigene Figur auf der Karte gibt es keinen Standpunkt, also alles.
    """
    roh = [t for t in teilnehmer if not t.get("zusatzzug")]
    if rolle == "GM" or not waende:
        return [dict(t) for t in roh]
    eigene = [t for t in roh if gehoert(t, person_id) and t.get("hexQ") is not None]
    if not eigene:
        return [dict(t) for t in roh]
    sichtbar: set[str] = set()
    for auge in eigene:
        sichtbar.add(auge["id"])
        for ziel in roh:
            if ziel.get("hexQ") is None or ziel["id"] in sichtbar:
                continue
            if ziel.get("versteckt") and not gehoert(ziel, person_id):
                continue
            if not blockiert(int(auge["hexQ"]), int(auge["hexR"]), int(ziel["hexQ"]), int(ziel["hexR"]), waende):
                sichtbar.add(ziel["id"])
    return [dict(t) for t in roh if t["id"] in sichtbar]
