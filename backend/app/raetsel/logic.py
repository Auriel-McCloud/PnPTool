"""Ring-Rätsel: acht Räume um ein festes Ziel, eine Ebene.

Menschen hängen an der Raum-Identität, nicht am Feld. Eine Tür zu dreht alle
acht Räume ein Feld gegen den Uhrzeigersinn. Ob die Gruppe durch die Tür
gegangen ist, weiß das Tool nicht — die Lage setzt die SL danach selbst.

Felder, von oben, im Uhrzeigersinn ab Nord:

    7  0  1
    6  Z  2
    5  4  3

Gegen den Uhrzeigersinn wandert der Raum aus Feld 0 nach Feld 7.
"""

from __future__ import annotations

import copy

ANZAHL = 8
SEITEN = ("N", "O", "S", "W")
NAME_MAX = 16
HISTORIE_MAX = 40

# Welche Tür eines Feldes zur Mitte zeigt. Ecken haben zwei Innenkanten.
_MITTE = {
    0: ("S",),
    1: ("S", "W"),
    2: ("W",),
    3: ("W", "N"),
    4: ("N",),
    5: ("N", "O"),
    6: ("O",),
    7: ("O", "S"),
}

_SEITE_NAME = {"N": "Nord", "O": "Ost", "S": "Süd", "W": "West"}


def leer() -> dict:
    return {
        "drehung": 0,
        "namen": [str(i + 1) for i in range(ANZAHL)],
        "gruppen": [None, None],
        "offen": [False, False],
        "tuer": None,
        "freigegeben": False,
        "historie": [],
    }


def slot_von_raum(drehung: int, raum: int) -> int:
    """Feld, in dem dieser Raum nach so vielen Schritten gegen den Uhrzeigersinn liegt."""
    return (raum - drehung) % ANZAHL


def raum_in_slot(drehung: int, slot: int) -> int:
    return (slot + drehung) % ANZAHL


def mitte_seiten(slot: int) -> tuple[str, ...]:
    return _MITTE[slot]


def seite_name(seite: str) -> str:
    return _SEITE_NAME[seite]


def normalisiere(roh) -> dict:
    """Kaputtes JSON wird zum leeren Ring, kein Absturz der Tafel."""
    if not isinstance(roh, dict):
        return leer()
    basis = leer()
    drehung = roh.get("drehung")
    basis["drehung"] = drehung if isinstance(drehung, int) and drehung >= 0 else 0
    namen = roh.get("namen")
    if isinstance(namen, list):
        for i in range(ANZAHL):
            if i < len(namen) and isinstance(namen[i], str) and namen[i].strip():
                basis["namen"][i] = _name(namen[i], i)
    gruppen = roh.get("gruppen")
    if isinstance(gruppen, list):
        for i in range(2):
            if i < len(gruppen) and _ist_raum(gruppen[i]):
                basis["gruppen"][i] = gruppen[i]
    offen = roh.get("offen")
    if isinstance(offen, list):
        for i in range(2):
            if i < len(offen) and offen[i] is True and basis["gruppen"][i] is not None:
                basis["offen"][i] = True
    tuer = roh.get("tuer")
    if isinstance(tuer, dict) and _ist_raum(tuer.get("raum")) and tuer.get("seite") in SEITEN:
        basis["tuer"] = {"raum": tuer["raum"], "seite": tuer["seite"]}
    basis["freigegeben"] = roh.get("freigegeben") is True
    historie = roh.get("historie")
    if isinstance(historie, list):
        basis["historie"] = [_schnappschuss_aus(eintrag) for eintrag in historie if isinstance(eintrag, dict)]
        basis["historie"] = [s for s in basis["historie"] if s is not None][-HISTORIE_MAX:]
    return basis


def tuer_zu(z: dict, raum: int, seite: str) -> dict:
    """Tür zu: Ring dreht, die Gruppe bleibt im Raum und muss neu bestätigt werden."""
    _pruefe_raum(raum)
    if seite not in SEITEN:
        raise ValueError("Diese Seite gibt es nicht.")
    neu = _kopie(z)
    _merken(neu)
    neu["drehung"] = neu["drehung"] + 1
    neu["tuer"] = {"raum": raum, "seite": seite}
    neu["offen"] = [g is not None for g in neu["gruppen"]]
    return neu


def gruppe_setzen(z: dict, index: int, raum: int | None) -> dict:
    """Lage der Gruppe. Dreht nicht — Tür auf ist nicht dasselbe wie durchgehen."""
    if index not in (0, 1):
        raise ValueError("Nur zwei Gruppen.")
    if raum is not None:
        _pruefe_raum(raum)
    neu = _kopie(z)
    _merken(neu)
    neu["gruppen"][index] = raum
    neu["offen"][index] = False
    return neu


def name_setzen(z: dict, raum: int, name: str) -> dict:
    _pruefe_raum(raum)
    neu = _kopie(z)
    _merken(neu)
    neu["namen"][raum] = _name(name, raum)
    return neu


def freigabe_setzen(z: dict, an: bool) -> dict:
    """Keine Historie: Zurück soll die Sicht der Spieler nicht mit umwerfen."""
    neu = _kopie(z)
    neu["freigegeben"] = bool(an)
    return neu


def zurueck(z: dict) -> dict:
    if not z["historie"]:
        return _kopie(z)
    neu = _kopie(z)
    alt = neu["historie"].pop()
    rest = neu["historie"]
    freigegeben = neu["freigegeben"]
    neu = leer()
    neu.update(alt)
    neu["namen"] = list(alt["namen"])
    neu["gruppen"] = list(alt["gruppen"])
    neu["offen"] = list(alt["offen"])
    neu["tuer"] = None if alt["tuer"] is None else dict(alt["tuer"])
    neu["freigegeben"] = freigegeben
    neu["historie"] = rest
    return neu


def zuruecksetzen(z: dict) -> dict:
    """Startfelder. Namen und Freigabe bleiben, die Schritte nicht."""
    neu = leer()
    neu["namen"] = list(z["namen"])
    neu["freigegeben"] = z["freigegeben"]
    return neu


def fuer_draht(z: dict, rolle: str) -> dict:
    """Spieler sehen die Tafel nur nach Freigabe, und nie den Rückgängig-Stapel."""
    if rolle != "GM" and not z["freigegeben"]:
        return {"freigegeben": False}
    return {
        "drehung": z["drehung"],
        "namen": list(z["namen"]),
        "gruppen": list(z["gruppen"]),
        "offen": list(z["offen"]),
        "tuer": None if z["tuer"] is None else dict(z["tuer"]),
        "freigegeben": z["freigegeben"],
        "kannZurueck": bool(z["historie"]) if rolle == "GM" else False,
    }


def _pruefe_raum(raum: int) -> None:
    if not _ist_raum(raum):
        raise ValueError("Diesen Raum gibt es nicht.")


def _ist_raum(raum) -> bool:
    return isinstance(raum, int) and not isinstance(raum, bool) and 0 <= raum < ANZAHL


def _name(name: str, raum: int) -> str:
    text = " ".join(name.split())
    if not text:
        return str(raum + 1)
    return text[:NAME_MAX]


def _schnappschuss_aus(roh: dict) -> dict | None:
    try:
        stand = normalisiere(roh)
    except (TypeError, ValueError):
        return None
    stand["historie"] = []
    return _ohne_historie(stand)


def _ohne_historie(z: dict) -> dict:
    return {
        "drehung": z["drehung"],
        "namen": list(z["namen"]),
        "gruppen": list(z["gruppen"]),
        "offen": list(z["offen"]),
        "tuer": None if z["tuer"] is None else dict(z["tuer"]),
        "freigegeben": z["freigegeben"],
    }


def _kopie(z: dict) -> dict:
    return copy.deepcopy(z)


def _merken(z: dict) -> None:
    z["historie"].append(_ohne_historie(z))
    if len(z["historie"]) > HISTORIE_MAX:
        del z["historie"][0]
