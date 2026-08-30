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
    # Der Wert selbst und die vier Fertigkeiten dazu.
    "TECHNOMANCER": {"NeuroWeavingWert", "NeuroWeaving"},
}

# Grundwert der Gesundheit, auf den die Widerstandsfähigkeit addiert wird.
GESUNDHEIT_GRUNDWERT = 5


def _wert(werte: dict[str, int], name: str) -> int:
    return werte.get(name, 0)


def gesundheit_max(werte: dict[str, int]) -> int:
    """Gesundheit = 5 + Widerstandsfähigkeit."""
    return GESUNDHEIT_GRUNDWERT + _wert(werte, "Widerstandsfähigkeit")


def willenskraft_max(werte: dict[str, int], bonus: int = 0) -> int:
    """Willenskraft = Entschlossenheit + Fassung, plus gekaufte Punkte.

    Der Bonus wird gespeichert statt abgeleitet: Willenskraft lässt sich mit
    Freebees und später mit Erfahrung einzeln steigern, ohne dass sich eines
    der beiden Attribute ändert.
    """
    return _wert(werte, "Entschlossenheit") + _wert(werte, "Fassung") + max(0, bonus)


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
    besonders = {"Arete", "Sphäre", "NeuroWeavingWert", "NeuroWeaving"}
    grundlage = {k for k in alle if k not in besonders}
    return grundlage | BEREICHE_JE_WEG.get(weg, set())


def bogen_uebersicht(person: dict, werte: dict[str, int], commlink_cyberwall: int = 0) -> dict:
    """Alles, was sich aus Attributen und Zustand ergibt — fertig fürs Blatt."""
    weg = person.get("weg") or "KEINER"
    g_max = gesundheit_max(werte)
    w_max = willenskraft_max(werte, int(person.get("willenskraftBonus") or 0))
    i_max = ice_max(weg, werte, commlink_cyberwall)
    erfahrung = int(person.get("erfahrung") or 0)
    ausgegeben = int(person.get("erfahrungAusgegeben") or 0)

    # Schaden nach Art. Zusammen dürfen sie die Gesundheit nicht übersteigen;
    # gekürzt wird beim leichtesten zuerst, denn schwerer Schaden verdrängt
    # in der World of Darkness den leichteren, nicht umgekehrt.
    aggraviert = max(0, int(person.get("schadenAggraviert") or 0))
    schwer = max(0, int(person.get("schadenSchwer") or 0))
    schlag = max(0, int(person.get("schadenSchlag") or 0))
    aggraviert = min(aggraviert, g_max)
    schwer = min(schwer, g_max - aggraviert)
    schlag = min(schlag, g_max - aggraviert - schwer)

    return {
        "weg": weg,
        "rasse": person.get("rasse") or "",
        "gesundheitMax": g_max,
        "schadenAggraviert": aggraviert,
        "schadenSchwer": schwer,
        "schadenSchlag": schlag,
        "gesundheitSchaden": aggraviert + schwer + schlag,
        "willenskraftMax": w_max,
        "willenskraftVerbraucht": min(int(person.get("willenskraftVerbraucht") or 0), w_max),
        "iceMax": i_max,
        "iceSchaden": min(int(person.get("iceSchaden") or 0), i_max),
        # Ohne Gerät ist man nicht angreifbar — für die Anzeige ein
        # Unterschied ums Ganze gegenüber "Wert 0, aber online".
        "offline": weg != "TECHNOMANCER" and commlink_cyberwall <= 0,
        "initiative": initiative(werte),
        "erfahrungGesamt": erfahrung,
        "erfahrungAusgegeben": ausgegeben,
        "erfahrungVerfuegbar": max(0, erfahrung - ausgegeben),
        # Kopfzeile des Papierblatts (Zeilen 3-7). Reiner Text, den das
        # Blatt anzeigt und die Erstellung füllt.
        "konzept": person.get("konzept") or "",
        "alter": person.get("alter") or "",
        "ambition": person.get("ambition") or "",
        "verlangen": person.get("verlangen") or "",
        "ziel": person.get("ziel") or "",
        "kapital": int(person.get("kapital") or 0),
        "schulden": int(person.get("schulden") or 0),
        # Bestandscharaktere kennen das Feld nicht — wer bereits Werte hat,
        # gilt trotzdem als erstellt. Sonst bekaeme Ryu Tanaka beim naechsten
        # Oeffnen die Erstellung vorgesetzt und wuerde dabei ueberschrieben.
        "erstellungAbgeschlossen": bool(person.get("erstellungAbgeschlossen"))
        or any(w > 0 for w in werte.values()),
    }


def zustand_verboten(rolle: str, vorher: dict, aenderung: dict) -> str | None:
    """Was ein Spieler an seinem Zustand **nicht** ändern darf.

    Gibt den Grund zurück, oder None wenn alles in Ordnung ist.

    Bisher genau eine Regel (Mark, 30.08.2026): **Willenskraft ausgeben darf
    der Spieler, wiederherstellen nicht.** Sie kommt zurück, wenn die
    Spielleitung es sagt — sonst wäre der Vorrat unbegrenzt und das Erzwingen
    von Erfolgen gratis.

    Schaden bleibt bewusst in beide Richtungen offen: Verletzungen heilen nach
    eigenen Regeln über Nacht, und wer sich vertippt hat, soll das ohne
    Nachfrage richtigstellen können.
    """
    if rolle == "GM":
        return None
    neu = aenderung.get("willenskraftVerbraucht")
    if neu is not None and neu < int(vorher.get("willenskraftVerbraucht") or 0):
        return "Willenskraft stellt die Spielleitung wieder her."
    return None
