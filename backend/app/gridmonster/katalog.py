"""GridMonster-Katalog: Attribute, Fertigkeiten und feste Werte.

Stand Grundgerüst 26.11.2026 — die Regeln selbst stehen in Marks persönlichem
Wiki (`concepts/gridmonster.md`), hier nur, was das Blatt zum Anzeigen und
Speichern braucht. Alles liegt als `TraitDef` mit `ruleset: 'gridmonster'`
neben dem NeotopiA-Katalog; die Werte einer Figur hängen wie bei NeotopiA per
`HAS_TRAIT {rating}` an der `Person`.

Bewusst neutral benannt: Die Stufen heißen hier „Stufe 1–5“, nicht nach den
Digimon-Stufen (Ausbildung/Rookie/…) — das Repo soll ohne fremde Begriffe
auskommen; Anzeigenamen sind später eine Einstellung.
"""

RULESET = "gridmonster"
REGELSYSTEM_NAME = "GridMonster"

# Würfelleiter (W10 entfällt, Mark 25.11.2026). 0 = Fertigkeit nicht gelernt.
WUERFEL = [4, 6, 8, 12, 20]

# Stufe → Angriffswürfel / passive Verteidigung („Verteidigung = Würfel der
# Stufe darunter“, von Mark als Grobgerüst angenommen 25.11.2026).
STUFEN = [
    {"stufe": 1, "angriff": 4, "verteidigung": 2},
    {"stufe": 2, "angriff": 6, "verteidigung": 4},
    {"stufe": 3, "angriff": 8, "verteidigung": 6},
    {"stufe": 4, "angriff": 12, "verteidigung": 8},
    {"stufe": 5, "angriff": 20, "verteidigung": 12},
]

# (Attribut, [(Fertigkeit, nur_fuer)]) — nur_fuer: None = beide,
# "monster" / "mensch" = nur diese Figurenart.
# Menschen haben keine Mystik (Mark 25.11.2026); ein Ersatz (Neko-Vorschlag
# „Technik“) ist noch offen und deshalb NICHT eingetragen.
ATTRIBUTE: list[tuple[str, list[tuple[str, str | None]]]] = [
    ("Kraft", [("Ausdauer", None), ("Athletik", None), ("Einschüchtern", None)]),
    ("Präzision", [("Nahkampf", None), ("Fernkampf", None), ("Handwerk", None), ("Kunst", None)]),
    ("Zähigkeit", [("Widerstand", None), ("Durchhaltevermögen", None), ("Abhärtung", None), ("Willenskraft", None)]),
    ("Agilität", [("Schleichen", None), ("Reflexe", None), ("Taschendiebstahl", None), ("Akrobatik", None)]),
    ("Schläue", [("Wahrnehmung", None), ("Instinkt", None), ("Mystik", "monster"), ("Finesse", None)]),
]

# Feste Zahlen (kein Würfel). (Name, nur_fuer, min, max, Startwert Monster, Startwert Mensch)
# Startwerte sind Annahmen fürs Basteln (LP-Faustregel aus dem Wiki: Rookie ~30).
WERTE: list[tuple[str, str | None, int, int | None, int, int]] = [
    ("Stufe", "monster", 1, 5, 2, 0),
    ("Level", None, 1, None, 1, 1),
    ("Lebenspunkte", None, 0, None, 30, 10),
    ("Energie", "monster", 0, None, 10, 0),
    ("Tamer-Level", "mensch", 1, 4, 0, 1),
    ("Deckkapazität", "mensch", 0, None, 0, 10),
]

ATTRIBUT_START = 4  # jedes Attribut startet auf W4


def trait_id(kategorie: str, name: str) -> str:
    return f"{RULESET}:{kategorie}:{name}"


def gilt_fuer(nur_fuer: str | None, ist_monster: bool) -> bool:
    if nur_fuer is None:
        return True
    return nur_fuer == ("monster" if ist_monster else "mensch")


def katalog_eintraege() -> list[dict]:
    """Alle TraitDefs in Seed-Form (id, name, category, sortOrder, …)."""
    eintraege: list[dict] = []
    for a_index, (attribut, fertigkeiten) in enumerate(ATTRIBUTE):
        eintraege.append({
            "id": trait_id("attribut", attribut), "name": attribut, "category": "attribut",
            "sortOrder": a_index + 1, "defaultMax": 20, "attribut": None, "nurFuer": None,
        })
        for f_index, (fertigkeit, nur) in enumerate(fertigkeiten):
            eintraege.append({
                "id": trait_id("fertigkeit", fertigkeit), "name": fertigkeit, "category": "fertigkeit",
                "sortOrder": (a_index + 1) * 10 + f_index, "defaultMax": 20,
                "attribut": attribut, "nurFuer": nur,
            })
    for w_index, (wert, nur, _min, maximum, _sm, _sh) in enumerate(WERTE):
        eintraege.append({
            "id": trait_id("wert", wert), "name": wert, "category": "wert",
            "sortOrder": w_index + 1, "defaultMax": maximum or 0, "attribut": None, "nurFuer": nur,
        })
    return eintraege


def startwerte(ist_monster: bool) -> dict[str, int]:
    """Werte einer frisch angelegten Figur: Attribute W4, Fertigkeiten 0, feste Werte laut Tabelle."""
    werte: dict[str, int] = {}
    for attribut, fertigkeiten in ATTRIBUTE:
        werte[trait_id("attribut", attribut)] = ATTRIBUT_START
        for fertigkeit, nur in fertigkeiten:
            if gilt_fuer(nur, ist_monster):
                werte[trait_id("fertigkeit", fertigkeit)] = 0
    for wert, nur, _min, _max, start_monster, start_mensch in WERTE:
        if gilt_fuer(nur, ist_monster):
            werte[trait_id("wert", wert)] = start_monster if ist_monster else start_mensch
    return werte


def pruefe_wert(trait: str, wert: int, ist_monster: bool) -> str | None:
    """Fehlertext oder None, wenn `wert` für dieses Feld dieser Figurenart erlaubt ist."""
    for attribut, fertigkeiten in ATTRIBUTE:
        if trait == trait_id("attribut", attribut):
            return None if wert in WUERFEL else f"{attribut}: nur W4/W6/W8/W12/W20"
        for fertigkeit, nur in fertigkeiten:
            if trait == trait_id("fertigkeit", fertigkeit):
                if not gilt_fuer(nur, ist_monster):
                    return f"{fertigkeit} gibt es für diese Figur nicht"
                return None if wert == 0 or wert in WUERFEL else f"{fertigkeit}: nur –/W4/W6/W8/W12/W20"
    for name, nur, minimum, maximum, _sm, _sh in WERTE:
        if trait == trait_id("wert", name):
            if not gilt_fuer(nur, ist_monster):
                return f"{name} gibt es für diese Figur nicht"
            if wert < minimum or (maximum is not None and wert > maximum):
                return f"{name}: {minimum}–{maximum if maximum is not None else '∞'}"
            return None
    return "Unbekanntes Feld"


def katalog_antwort() -> dict:
    """Katalog fürs Frontend (Blatt-Aufbau)."""
    return {
        "wuerfel": WUERFEL,
        "stufen": STUFEN,
        "attribute": [
            {
                "id": trait_id("attribut", a),
                "name": a,
                "fertigkeiten": [
                    {"id": trait_id("fertigkeit", f), "name": f, "nurFuer": nur} for f, nur in fs
                ],
            }
            for a, fs in ATTRIBUTE
        ],
        "werte": [
            {"id": trait_id("wert", n), "name": n, "nurFuer": nur, "min": mi, "max": ma}
            for n, nur, mi, ma, _sm, _sh in WERTE
        ],
    }
