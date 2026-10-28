"""Hot-Gehen: Neurolink, eine Drohne pro Runde, Deck nur eingeklinkt.

Mark, 28.10.2026. Eine Cyberware wird per Häkchen im Umbauen zum Neurolink
(`istNeurolink`). Im Rucksack liegend schaltet sie nichts frei. Die
Deck-Zusatzaktionen zählen erst, wenn der Decker Hot ist. Der Rigger wählt
pro Kampfrunde eine Drohne; sie teilt seinen Initiative-Slot.
"""

from dataclasses import dataclass


def ist_neurolink(typ: str, verbaut: bool, ist_neurolink_flag: bool) -> bool:
    """Angeklickte, verbaute Cyberware. Der Name spielt keine Rolle."""
    return bool(verbaut) and bool(ist_neurolink_flag) and typ == "Cyberware"


def hat_neurolink(stuecke: list[dict]) -> bool:
    return any(
        ist_neurolink(s.get("typ") or "", bool(s.get("verbaut")), bool(s.get("istNeurolink")))
        for s in stuecke
    )


@dataclass(frozen=True)
class HotErgebnis:
    ok: bool
    fehler: str | None
    hot_drohne_id: str | None
    hot_runde: int


def booster_kandidaten(chrom: list[dict], deck: dict | None, matrix_hot: bool) -> list[dict]:
    """Woraus die Ampel schöpft. Das Deck nur, solange der Decker Hot ist."""
    kandidaten = [g for g in chrom if (g.get("zusatzaktionen") or 0) != 0]
    if matrix_hot and deck and (deck.get("zusatzaktionen") or 0) != 0:
        kandidaten.append(deck)
    return kandidaten


def staerkstes(kandidaten: list[dict]) -> dict | None:
    """Wie bisher: mehrere Booster, das mit den meisten Aktionen gewinnt.
    -1 (jede Runde) schlägt jede endliche Zahl."""
    if not kandidaten:
        return None
    return max(kandidaten, key=lambda g: 999 if g["zusatzaktionen"] < 0 else g["zusatzaktionen"])


def darf_drohne_waehlen(
    hot_drohne_id: str | None,
    hot_runde: int,
    kampf_runde: int | None,
) -> bool:
    """Eine Drohne pro Kampfrunde. Außerhalb eines Kampfes kein Deckel.

    Solange die Bleiben-Frage offen ist (noch Hot, Wahl aus einer früheren
    Runde), ist ein Wechsel keine neue Wahl — erst die Antwort zählt.
    """
    if kampf_runde is None:
        return True
    if hot_runde == kampf_runde:
        return False
    if hot_drohne_id and hot_runde < kampf_runde:
        return False
    return True


def bleiben_faellig(
    hot_drohne_id: str | None,
    hot_runde: int,
    kampf_runde: int | None,
    ist_dran: bool,
) -> bool:
    """Beim nächsten eigenen Slot: drin bleiben? Nur wenn er dran ist."""
    if not hot_drohne_id or kampf_runde is None or not ist_dran:
        return False
    return hot_runde < kampf_runde


def waehle_drohne(
    *,
    hat_neurolink: bool,
    hot_drohne_id: str | None,
    hot_runde: int,
    kampf_runde: int | None,
    drohne_id: str,
) -> HotErgebnis:
    if not hat_neurolink:
        return HotErgebnis(False, "Ohne verbauten Neurolink kein Hot.", hot_drohne_id, hot_runde)
    if not darf_drohne_waehlen(hot_drohne_id, hot_runde, kampf_runde):
        return HotErgebnis(False, "Diese Runde ist schon eine Drohne gewählt.", hot_drohne_id, hot_runde)
    return HotErgebnis(True, None, drohne_id, kampf_runde if kampf_runde is not None else 0)


def beantworte_bleiben(ja: bool, hot_drohne_id: str | None, kampf_runde: int | None) -> HotErgebnis:
    """Ja behält die Drohne. Nein klinkt aus und verbraucht die Wahl der Runde."""
    runde = kampf_runde if kampf_runde is not None else 0
    return HotErgebnis(True, None, hot_drohne_id if ja else None, runde)


def anzeige_name(rigger: str, drohne: str | None) -> str:
    if not drohne:
        return rigger
    return f"{rigger} · {drohne}"


def schneller(a: int, b: int) -> int:
    return max(a, b)


def hot_rueckschlag(hp_menge: int) -> int:
    """Hälfte des bei der Hot-Drohne angekommenen Schadens, als Schlag, aufgerundet.

    0 bleibt 0. 1 wird 1, 3 wird 2. Nur die Menge, die Art ist immer Schlag.
    """
    if hp_menge <= 0:
        return 0
    return (hp_menge + 1) // 2


def hot_anpassung(
    drohne: dict[str, int],
    rigger: dict[str, int],
    rigger_bonus: int,
    drohne_zusatz: dict[str, int] | None = None,
    rigger_zusatz: dict[str, int] | None = None,
) -> dict[str, int]:
    """Werte, die sich nur solange Hot ändern. Alles andere bleibt weg.

    Geschick bekommt Riggen obendrauf, gedeckelt durch den Konsolenbonus
    (negativ zählt als 0). Fahren und Fliegen nehmen den besseren Wert.
    Intelligenz und Geistesschärfe kommen vom Rigger — die Drohne hat sie nicht.
    """
    extra_drohne = drohne_zusatz or {}
    extra_rigger = rigger_zusatz or {}
    deckel = max(0, rigger_bonus)
    aufschlag = min(max(0, rigger.get("Riggen", 0)), deckel)
    neu: dict[str, int] = {}
    if aufschlag:
        neu["Geschick"] = drohne.get("Geschick", 0) + aufschlag
    for name in ("Fahren", "Fliegen"):
        von_drohne = drohne.get(name, extra_drohne.get(name, 0))
        von_rigger = rigger.get(name, extra_rigger.get(name, 0))
        if von_rigger > von_drohne:
            neu[name] = von_rigger
    neu["Intelligenz"] = rigger.get("Intelligenz", 0)
    neu["Geistesschärfe"] = rigger.get("Geistesschärfe", 0)
    return neu


def zusatz_mit_hot(gewaehlt: list[dict], rigger_zusatz: list[dict], fliegen: int | None) -> list[dict]:
    """Fliegen auf der Anzeige: besserer Wert, und borgen, wenn die Drohne ihn nicht hat.

    Schreibt nichts. `hotNurAnzeige` sagt dem Blatt, die Zahl nicht zu speichern.
    """
    if not fliegen:
        return [dict(z) for z in gewaehlt]
    neu = [dict(z) for z in gewaehlt]
    for z in neu:
        if z.get("name") == "Fliegen" and int(z.get("rating") or 0) < fliegen:
            z["rating"] = fliegen
            z["hotNurAnzeige"] = True
            return neu
    if any(z.get("name") == "Fliegen" for z in neu):
        return neu
    vorlage = next((z for z in rigger_zusatz if z.get("name") == "Fliegen"), None)
    if vorlage is None:
        return neu
    kopie = dict(vorlage)
    kopie["rating"] = fliegen
    kopie["hotNurAnzeige"] = True
    neu.append(kopie)
    return neu


def verbindung_bricht(gesundheit_uebrig: int) -> bool:
    """Dumpshock, wenn nach dem Treffer nichts mehr übrig ist. Kein eigener Schadenswurf."""
    return gesundheit_uebrig <= 0


def werte_mit_hot(werte: list[dict], katalog: list[dict], anpassung: dict[str, int]) -> tuple[list[dict], list[dict]]:
    """Legt die Hot-Zahlen auf eine Kopie der Werte. Originale bleiben.

    Intelligenz und Geistesschärfe kommen als geliehene Katalogzeilen zurück,
    weil eine Drohne sie sonst gar nicht auf dem Blatt hat.
    """
    geliehen = {"Intelligenz", "Geistesschärfe"}
    neu = [dict(w) for w in werte]
    nach_name = {w["name"]: w for w in neu}
    extra = []
    for name, rating in anpassung.items():
        if name in geliehen:
            vorlage = next((t for t in katalog if t.get("name") == name), None)
            if vorlage is None:
                continue
            extra.append(vorlage)
            neu.append({
                "traitDefId": vorlage["id"],
                "name": name,
                "category": vorlage.get("category") or "AttributGeistig",
                "rating": rating,
                "max": vorlage.get("defaultMax", 6),
                "hotNurAnzeige": True,
            })
            continue
        ziel = nach_name.get(name)
        if ziel is None:
            vorlage = next((t for t in katalog if t.get("name") == name), None)
            if vorlage is None:
                continue
            neu.append({
                "traitDefId": vorlage["id"],
                "name": name,
                "category": vorlage.get("category") or "",
                "rating": rating,
                "max": vorlage.get("defaultMax", 6),
                "hotNurAnzeige": True,
            })
            continue
        if ziel.get("rating") == rating:
            continue
        ziel["rating"] = rating
        ziel["hotNurAnzeige"] = True
    return neu, extra


def falte_hot(teilnehmer: list[dict], links: dict[str, tuple[str, str]]) -> list[dict]:
    """Hot-Drohne verschwindet als eigene Zeile und teilt den Slot des Riggers.

    `links` bildet die Personen-Kennung des Riggers auf (Drohnen-Kennung, Name)
    ab. Zusatzzüge bleiben unangetastet. Die Originale werden nicht verändert.
    """
    if not links:
        return [dict(t) for t in teilnehmer]
    by_person = {
        t["personId"]: t
        for t in teilnehmer
        if t.get("personId") and not t.get("zusatzzug")
    }
    versteckte_personen = {drohne_id for drohne_id, _ in links.values()}
    gefaltet = []
    for t in teilnehmer:
        pid = t.get("personId")
        if pid in versteckte_personen and not t.get("zusatzzug"):
            continue
        if pid in links and not t.get("zusatzzug"):
            drohne_id, drohne_name = links[pid]
            kopie = dict(t)
            kopie["name"] = anzeige_name(t.get("name") or "", drohne_name)
            kopie["hotMitName"] = drohne_name
            drohne = by_person.get(drohne_id)
            if drohne is not None:
                kopie["initiative"] = schneller(int(t.get("initiative") or 0), int(drohne.get("initiative") or 0))
            gefaltet.append(kopie)
            continue
        gefaltet.append(dict(t))
    return gefaltet


def am_zug_nach_faltung(am_zug: str | None, vorher: list[dict], gefaltet: list[dict], links: dict[str, tuple[str, str]]) -> str | None:
    """Zeigt der Zeiger auf die versteckte Hot-Drohne, springt er auf den Rigger."""
    if am_zug is None or any(t["id"] == am_zug for t in gefaltet):
        return am_zug
    versteckt = next((t for t in vorher if t["id"] == am_zug), None)
    if versteckt is None:
        return am_zug
    pid = versteckt.get("personId")
    for rigger_id, (drohne_id, _) in links.items():
        if pid == drohne_id:
            rigger = next(
                (t for t in gefaltet if t.get("personId") == rigger_id and not t.get("zusatzzug")),
                None,
            )
            return rigger["id"] if rigger else am_zug
    return am_zug
