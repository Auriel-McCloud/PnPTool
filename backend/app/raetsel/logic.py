"""Ring-Rätsel: eine oder zwei Ebenen um ein festes Ziel.

Menschen hängen an der Raum-Identität, nicht am Feld. Tür auf ist nicht
durchgehen. Leicht dreht den einen Ring gegen den Uhrzeigersinn. Mittel
wechselt zuerst die Ebene (gleiches Feld, anderer Ring) und dreht beim
nächsten Tür-zu beide Ringe, im Wechsel.

Felder, von oben, im Uhrzeigersinn ab Nord:

    7  0  1
    6  Z  2
    5  4  3

Gegen den Uhrzeigersinn wandert der Raum aus Feld 0 nach Feld 7.
Der Ausgang ist ein Feld, kein Raum: er bleibt liegen, die Räume wandern.
Spieler sehen ihn nicht.
"""

from __future__ import annotations

import copy

ANZAHL = 8
NAMEN_MAX = 16
SEITEN = ("N", "O", "S", "W")
NAME_MAX = 16
HISTORIE_MAX = 40
MODI = ("leicht", "mittel")

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
        "modus": "leicht",
        "drehung": 0,
        "takt": 0,
        "ringe": [[i for i in range(ANZAHL)], [i + ANZAHL for i in range(ANZAHL)]],
        "ausgaenge": [None, None],
        "namen": [str(i + 1) for i in range(NAMEN_MAX)],
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
    modus = roh.get("modus")
    basis["modus"] = modus if modus in MODI else "leicht"
    drehung = roh.get("drehung")
    basis["drehung"] = drehung if isinstance(drehung, int) and drehung >= 0 else 0
    takt = roh.get("takt")
    basis["takt"] = takt if isinstance(takt, int) and takt >= 0 else 0
    namen = roh.get("namen")
    if isinstance(namen, list):
        for i in range(NAMEN_MAX):
            if i < len(namen) and isinstance(namen[i], str) and namen[i].strip():
                basis["namen"][i] = _name(namen[i], i)
    basis["ringe"] = _ringe_aus(roh.get("ringe"), basis["drehung"])
    basis["ausgaenge"] = _ausgaenge_aus(roh.get("ausgaenge"))
    gruppen = roh.get("gruppen")
    if isinstance(gruppen, list):
        for i in range(2):
            if i < len(gruppen) and _ist_raum(gruppen[i], basis):
                basis["gruppen"][i] = gruppen[i]
    offen = roh.get("offen")
    if isinstance(offen, list):
        for i in range(2):
            if i < len(offen) and offen[i] is True and basis["gruppen"][i] is not None:
                basis["offen"][i] = True
    tuer = roh.get("tuer")
    if isinstance(tuer, dict) and _ist_raum(tuer.get("raum"), basis) and tuer.get("seite") in SEITEN:
        basis["tuer"] = {"raum": tuer["raum"], "seite": tuer["seite"]}
    basis["freigegeben"] = roh.get("freigegeben") is True
    historie = roh.get("historie")
    if isinstance(historie, list):
        basis["historie"] = [_schnappschuss_aus(eintrag) for eintrag in historie if isinstance(eintrag, dict)]
        basis["historie"] = [s for s in basis["historie"] if s is not None][-HISTORIE_MAX:]
    return basis


def tuer_zu(z: dict, raum: int, seite: str) -> dict:
    """Tür zu. Leicht dreht. Mittel wechselt die Ebene und dreht im Wechsel."""
    _pruefe_raum(raum, z)
    if seite not in SEITEN:
        raise ValueError("Diese Seite gibt es nicht.")
    neu = _kopie(z)
    _merken(neu)
    if neu["modus"] == "mittel":
        neu["ringe"], _ = _mittel_schritt(neu["ringe"], neu["takt"])
        neu["takt"] = neu["takt"] + 1
    else:
        neu["drehung"] = neu["drehung"] + 1
        neu["ringe"][0] = [raum_in_slot(neu["drehung"], slot) for slot in range(ANZAHL)]
    neu["tuer"] = {"raum": raum, "seite": seite}
    neu["offen"] = [g is not None for g in neu["gruppen"]]
    return neu


def gruppe_setzen(z: dict, index: int, raum: int | None) -> dict:
    """Lage der Gruppe. Dreht nicht — Tür auf ist nicht dasselbe wie durchgehen."""
    if index not in (0, 1):
        raise ValueError("Nur zwei Gruppen.")
    if raum is not None:
        _pruefe_raum(raum, z)
    neu = _kopie(z)
    _merken(neu)
    neu["gruppen"][index] = raum
    neu["offen"][index] = False
    return neu


def name_setzen(z: dict, raum: int, name: str) -> dict:
    _pruefe_raum(raum, z)
    neu = _kopie(z)
    _merken(neu)
    neu["namen"][raum] = _name(name, raum)
    return neu


def ausgang_setzen(z: dict, ring: int, slot: int | None) -> dict:
    """Ausgang ist ein Feld in der Mitte. Nochmal dasselbe Feld nimmt ihn weg."""
    if ring not in (0, 1) or (z["modus"] == "leicht" and ring != 0):
        raise ValueError("Diesen Ring gibt es hier nicht.")
    if slot is not None and not _ist_slot(slot):
        raise ValueError("Dieses Feld gibt es nicht.")
    neu = _kopie(z)
    _merken(neu)
    neu["ausgaenge"][ring] = None if slot is not None and neu["ausgaenge"][ring] == slot else slot
    return neu


def modus_setzen(z: dict, modus: str) -> dict:
    """Umschalter. Felder auf Start, Namen, Freigabe und Ausgänge bleiben."""
    if modus not in MODI:
        raise ValueError("Diesen Schwierigkeitsgrad gibt es nicht.")
    if z["modus"] == modus:
        return _kopie(z)
    neu = _kopie(z)
    _merken(neu)
    frisch = leer()
    neu["modus"] = modus
    neu["drehung"] = 0
    neu["takt"] = 0
    neu["ringe"] = frisch["ringe"]
    neu["tuer"] = None
    neu["offen"] = [False, False]
    neu["gruppen"] = [g if _ist_raum(g, neu) else None for g in neu["gruppen"]]
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
    neu["ausgaenge"] = list(alt.get("ausgaenge", [None, None]))
    neu["ringe"] = [list(ring) for ring in alt.get("ringe", neu["ringe"])]
    neu["tuer"] = None if alt["tuer"] is None else dict(alt["tuer"])
    neu["freigegeben"] = freigegeben
    neu["historie"] = rest
    return neu


def zuruecksetzen(z: dict) -> dict:
    """Startfelder. Namen, Freigabe, Modus und Ausgänge bleiben."""
    neu = leer()
    neu["modus"] = z["modus"]
    neu["namen"] = list(z["namen"])
    neu["freigegeben"] = z["freigegeben"]
    neu["ausgaenge"] = list(z["ausgaenge"])
    return neu


def fuer_draht(z: dict, rolle: str) -> dict:
    """Spieler sehen die Tafel nur nach Freigabe, nie den Ausgang und nie die Historie."""
    if rolle != "GM" and not z["freigegeben"]:
        return {"freigegeben": False}
    return {
        "modus": z["modus"],
        "drehung": z["drehung"],
        "takt": z["takt"],
        "naechster": "ebene" if z["modus"] == "mittel" and z["takt"] % 2 == 0 else "drehen",
        "ringe": _sichtbare_ringe(z),
        "ausgaenge": list(z["ausgaenge"]) if rolle == "GM" else [None, None],
        "namen": list(z["namen"]),
        "gruppen": list(z["gruppen"]),
        "offen": list(z["offen"]),
        "tuer": None if z["tuer"] is None else dict(z["tuer"]),
        "freigegeben": z["freigegeben"],
        "kannZurueck": bool(z["historie"]) if rolle == "GM" else False,
    }


def _mittel_schritt(ringe: list[list[int]], takt: int) -> tuple[list[list[int]], str]:
    if takt % 2 == 0:
        return [list(ringe[1]), list(ringe[0])], "ebene"
    return [[ring[(slot + 1) % ANZAHL] for slot in range(ANZAHL)] for ring in ringe], "drehen"


def _sichtbare_ringe(z: dict) -> list[list[int]]:
    if z["modus"] == "mittel":
        return [list(ring) for ring in z["ringe"]]
    return [[raum_in_slot(z["drehung"], slot) for slot in range(ANZAHL)]]


def _pruefe_raum(raum: int, z: dict) -> None:
    if not _ist_raum(raum, z):
        raise ValueError("Diesen Raum gibt es nicht.")


def _ist_raum(raum, z: dict) -> bool:
    obergrenze = NAMEN_MAX if z["modus"] == "mittel" else ANZAHL
    return isinstance(raum, int) and not isinstance(raum, bool) and 0 <= raum < obergrenze


def _ist_slot(slot) -> bool:
    return isinstance(slot, int) and not isinstance(slot, bool) and 0 <= slot < ANZAHL


def _name(name: str, raum: int) -> str:
    text = " ".join(name.split())
    if not text:
        return str(raum + 1)
    return text[:NAME_MAX]


def _ringe_aus(roh, drehung: int) -> list[list[int]]:
    gueltig = (
        isinstance(roh, list)
        and len(roh) == 2
        and all(isinstance(ring, list) and len(ring) == ANZAHL for ring in roh)
    )
    if gueltig:
        gesehen = [raum for ring in roh for raum in ring]
        if len(gesehen) == len(set(gesehen)) and all(_raum_id(raum) for raum in gesehen):
            return [list(ring) for ring in roh]
    start = [[i for i in range(ANZAHL)], [i + ANZAHL for i in range(ANZAHL)]]
    start[0] = [raum_in_slot(drehung, slot) for slot in range(ANZAHL)]
    return start


def _ausgaenge_aus(roh) -> list:
    aus = [None, None]
    if isinstance(roh, list):
        for i in range(2):
            if i < len(roh) and _ist_slot(roh[i]):
                aus[i] = roh[i]
    return aus


def _raum_id(raum) -> bool:
    return isinstance(raum, int) and not isinstance(raum, bool) and 0 <= raum < NAMEN_MAX


def _schnappschuss_aus(roh: dict) -> dict | None:
    try:
        stand = normalisiere(roh)
    except (TypeError, ValueError):
        return None
    stand["historie"] = []
    return _ohne_historie(stand)


def _ohne_historie(z: dict) -> dict:
    return {
        "modus": z["modus"],
        "drehung": z["drehung"],
        "takt": z["takt"],
        "ringe": [list(ring) for ring in z["ringe"]],
        "ausgaenge": list(z["ausgaenge"]),
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
