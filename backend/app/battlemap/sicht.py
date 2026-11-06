"""Letzte Sicht auf der Battlemap, ohne Datenbank.

Vorne sind drei von sechs Hex-Richtungen. Dahinter bleibt der Stand vom
letzten Hinsehen. Versteckt schlägt den Kegel. Rundumsicht sieht immer
den aktuellen Stand. Die Party teilt die Augen nicht.
"""

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


def sieht_live(auge: dict, ziel: dict) -> bool:
    """Liegt das Ziel im vorderen Halbkreis dieses Auges, oder sieht es rundum?"""
    if auge.get("hexQ") is None or ziel.get("hexQ") is None:
        return False
    if auge.get("rundumsicht"):
        return True
    richtung = sektor(int(auge["hexQ"]), int(auge["hexR"]), int(ziel["hexQ"]), int(ziel["hexR"]))
    if richtung is None:
        return True
    return richtung in vorderkegel(int(auge.get("blickrichtung") or 0))


def _schnappschuss(token: dict) -> dict:
    return {feld: token.get(feld) for feld in SICHT_FELDER if feld != "veraltet"}


def start_speicher(teilnehmer: list[dict]) -> dict:
    """Kampfbeginn: jedes Auge kennt den aktuellen Stand, auch hinten."""
    augen = [t for t in teilnehmer if not t.get("zusatzzug") and t.get("hexQ") is not None]
    speicher: dict = {}
    for auge in augen:
        kontrolleur = auge.get("besitzerId") or auge.get("personId")
        ged = {}
        for ziel in augen:
            if ziel.get("versteckt") and not gehoert(ziel, kontrolleur):
                continue
            ged[ziel["id"]] = _schnappschuss(ziel)
        speicher[auge["id"]] = ged
    return speicher


def aktualisiere(teilnehmer: list[dict], speicher: dict | None) -> dict:
    """Vorderen Halbkreis auffrischen. Hinten bleibt der alte Stand."""
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
            if sieht_live(auge, ziel):
                if verborgen:
                    ged.pop(ziel["id"], None)
                else:
                    ged[ziel["id"]] = _schnappschuss(ziel)
        neu[auge["id"]] = {k: v for k, v in ged.items() if k in lebendig}
    return {k: v for k, v in neu.items() if k in lebendig}


def ansicht(teilnehmer: list[dict], speicher: dict | None, *, rolle: str, person_id: str | None) -> list[dict]:
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
            if sieht_live(auge, ziel) and not (ziel.get("versteckt") and not gehoert(ziel, person_id)):
                live.add(tid)
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
