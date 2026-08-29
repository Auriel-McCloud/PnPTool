"""Abgeleitete Werte des Charakterbogens.

Diese Werte werden **nicht gespeichert**, sondern aus Attributen berechnet —
sonst laufen sie auseinander, sobald jemand ein Attribut ändert. Quelle:
docs/regeln-neotopia.md.
"""

# Welche Wege welche Bereiche des Blatts freischalten. Auf dem Blatt steht
# "Arete != NeuroWeaving": beides zugleich gibt es nicht.
BEREICHE_JE_WEG: dict[str, set[str]] = {
    "KEINER": set(),
    "MAGIER": {"Arete", "Sphäre"},
    "TECHNOMANCER": {"NeuroWeaving"},
}

# Grundwert der Gesundheit, auf den die Widerstandsfähigkeit addiert wird.
GESUNDHEIT_GRUNDWERT = 5


def _wert(werte: dict[str, int], name: str) -> int:
    return werte.get(name, 0)


def gesundheit_max(werte: dict[str, int]) -> int:
    """Gesundheit = 5 + Widerstandsfähigkeit."""
    return GESUNDHEIT_GRUNDWERT + _wert(werte, "Widerstandsfähigkeit")


def willenskraft_max(werte: dict[str, int]) -> int:
    """Willenskraft = Entschlossenheit + Fassung."""
    return _wert(werte, "Entschlossenheit") + _wert(werte, "Fassung")


def ice_max(weg: str, werte: dict[str, int], commlink_cyberwall: int = 0) -> int:
    """Matrix-Verteidigung (I.C.E. / Cyber Wall).

    **Technomancer:** Fassung + Geistesschärfe. Er trägt seine Abwehr in sich
    und braucht kein Gerät. *Weicht bewusst von Zeile 99 des Regelblatts ab,
    wo Willenskraft steht* — Mark hat das am 29.08.2026 geändert, weil die
    Willenskraft beim NeuroWeaving verbraucht wird und ihn sonst jede Aktion
    zugleich verwundbar gemacht hätte.

    **Alle anderen:** der Cyberwall-Wert ihres Commlinks. Ohne Commlink ist
    der Wert 0 — dann ist man aber auch offline und schlicht nicht angreifbar.
    Der Unterschied zwischen "ungeschützt" und "nicht erreichbar" liegt also
    nicht im Wert, sondern darin, ob überhaupt ein Gerät da ist.
    """
    if weg == "TECHNOMANCER":
        return _wert(werte, "Fassung") + _wert(werte, "Geistesschärfe")
    return commlink_cyberwall


def initiative(werte: dict[str, int], cyberware_mod: int = 0) -> int:
    """Initiative = Geistesschärfe + Geschicklichkeit + Cyberware-Modifikator."""
    return _wert(werte, "Geistesschärfe") + _wert(werte, "Geschicklichkeit") + cyberware_mod


def sichtbare_kategorien(weg: str, alle: set[str]) -> set[str]:
    """Welche Trait-Kategorien für diesen Charakter überhaupt gelten.

    Attribute und Fertigkeiten hat jeder. Arete und Sphären sieht nur ein
    Magier, NeuroWeaving nur ein Technomancer — wer nichts davon gewählt hat,
    bekommt diese Bereiche gar nicht erst zu sehen.
    """
    besonders = {"Arete", "Sphäre", "NeuroWeaving"}
    grundlage = {k for k in alle if k not in besonders}
    return grundlage | BEREICHE_JE_WEG.get(weg, set())


def bogen_uebersicht(person: dict, werte: dict[str, int], commlink_cyberwall: int = 0) -> dict:
    """Alles, was sich aus Attributen und Zustand ergibt — fertig fürs Blatt."""
    weg = person.get("weg") or "KEINER"
    g_max = gesundheit_max(werte)
    w_max = willenskraft_max(werte)
    i_max = ice_max(weg, werte, commlink_cyberwall)
    erfahrung = int(person.get("erfahrung") or 0)
    ausgegeben = int(person.get("erfahrungAusgegeben") or 0)

    return {
        "weg": weg,
        "rasse": person.get("rasse") or "",
        "gesundheitMax": g_max,
        "gesundheitSchaden": min(int(person.get("gesundheitSchaden") or 0), g_max),
        "willenskraftMax": w_max,
        "willenskraftVerbraucht": min(int(person.get("willenskraftVerbraucht") or 0), w_max),
        "iceMax": i_max,
        "iceSchaden": min(int(person.get("iceSchaden") or 0), i_max),
        # Ohne Gerät ist man nicht angreifbar — für die Anzeige ein
        # Unterschied ums Ganze gegenüber "Wert 0, aber online".
        "offline": weg != "TECHNOMANCER" and commlink_cyberwall <= 0,
        "initiative": initiative(werte),
        "erfahrungGesamt": erfahrung,
        "erfahrungVerfuegbar": max(0, erfahrung - ausgegeben),
    }
