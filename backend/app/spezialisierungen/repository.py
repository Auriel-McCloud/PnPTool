"""Fertigkeiten-Spezialisierungen: benannte oder noch leere Slots pro Person.

`(:Person)-[:HAT_SPEZIALISIERUNG]->(:Spezialisierung {id, campaignId,
personId, traitDefId, text, quelle, benanntVonSpieler, erstelltAm})` ist eine
EIGENE Relation/eigenes Label, KEINE `HAS_TRAIT`-Relationship-Property wie bei
normalen Fertigkeitswerten (siehe app/traits/repository.py). Grund: eine
Spezialisierung ist eine bespoke Instanz PRO CHARAKTER mit mehreren
unabhängigen Feldern (Text, Quelle, wer sie benannt hat) und eigenen
Edit-Rechten — eine Relationship-Property kann weder eine unbegrenzte Liste
solcher Instanzen noch deren einzelne Sperrzustände sauber abbilden. Das
unterscheidet diesen Fall bewusst von Zusatzfertigkeiten
(app/zusatzfertigkeiten/repository.py): dort teilen sich alle Personen EINEN
Katalogknoten plus eine einfache `rating`-Property — hier ist jeder Slot ein
eigenständiger, nicht geteilter Knoten. Die CRUD-Code-FORM (anlegen/aendern,
`_decode`-Helfer, campaign-scoping) ist trotzdem an jenem Modul orientiert.

Die automatische Vergabe (Schwelle 4 → ein Slot, Schwelle 6 → ein zweiter)
lebt HIER als reine Funktion (`automatische_slot_anzahl`) plus
`automatisch_anlegen`; aufgerufen wird sie aus app/traits/repository.py, und
zwar aus `set_rating`/`steigere`/`set_ratings_bulk` selbst (nicht aus jeder
einzelnen Route) — das deckt jeden Pfad ab, der ein Fertigkeits-Rating
anheben kann: GM-Punktklick, EP-Steigerung, Charaktererstellung/-korrektur,
und jede künftige NPC-Autosteigerung, die irgendwann einen dieser drei
Wege nutzt (aktuell: `traits/autosteigerung.py` ist reine Berechnung ohne
eigenen Persistenz-Call, siehe Feature-Bericht).
"""

import uuid
from datetime import datetime, timezone

from app.db.neo4j_driver import get_driver

# Fertigkeit-Kategorien im Sinne DIESER Mechanik: die 30 Kern-Fertigkeiten
# (Kategorie "Fertigkeit") UND die NeuroWeaving-Fertigkeiten (Kategorie
# "NeuroWeaving" — aktuell SECHS: Brute Force/Schleichen/Daten Verarbeiten/
# Kompilieren/Electronic Warfare/Matrix-Navigation, siehe traits/seed.py
# NEOTOPIA_TRAITS; am 22.09.2026 von ursprünglich vier auf sechs erweitert).
# Sie zählen laut traits/erstellung.py mechanisch als Fertigkeit.
#
# NICHT "NeuroWeavingWert" (der Grundwert selbst, mechanisch wie Hexkraft
# behandelt — siehe Probe.tsx NUR_WILLENSKRAFT) und NICHT Attribute.
FERTIGKEIT_KATEGORIEN = frozenset({"Fertigkeit", "NeuroWeaving"})

# Sphären-Spezialisierung (23.10.2026, Folge-Feature zur Fertigkeiten-
# Spezialisierung, mit Mark im Chat durchgesprochen): eigene Schwellen
# (2/4/6 statt 4/6, siehe SPHAERE_SCHWELLEN unten) und bewusst OHNE
# Würfelpool-Bonus (Sphären werden in Probe.tsx gar nicht gewürfelt, siehe
# istSphaere-Zweig) — der Slot selbst ist bei Sphären reiner Freitext/
# Flavor (die ausformulierte Stufe-6-Fähigkeit), kein Mechanik-Bonus.
SPHAERE_KATEGORIEN = frozenset({"Sphäre"})

# Vereinigung beider Gruppen — für jeden Code-Pfad, der NUR wissen muss
# "kennt diese Kategorie überhaupt Spezialisierungs-Slots" (Auto-Grant-Hook,
# Kauf-Route, Vorschläge-Route), ohne nach der konkreten Schwelle zu fragen.
ALLE_SPEZIALISIERUNGS_KATEGORIEN = FERTIGKEIT_KATEGORIEN | SPHAERE_KATEGORIEN

# Automatische Vergabe-Schwellen: bei 4 der erste Slot, bei 6 der zweite.
# NICHT kumulativ dazwischen — 4→5 vergibt nichts (Marks Vorgabe: nur beim
# ÜBERSCHREITEN einer Schwelle, nicht bei jedem Punkt).
AUTOMATISCHE_SCHWELLEN = (4, 6)

# Sphären bekommen DREI Slots statt zwei — Mark wollte sie früher und
# dichter gestaffelt, weil Sphären-Werte ohnehin seltener steigen als
# normale Fertigkeiten (23.10.2026).
SPHAERE_SCHWELLEN = (2, 4, 6)


def schwellen_fuer(category: str) -> tuple[int, ...]:
    """Welche Schwellen-Tupel für diese Kategorie gelten — Sphären eigene
    (2/4/6), alles andere in ALLE_SPEZIALISIERUNGS_KATEGORIEN die normalen
    (4/6). Eine Kategorie, die gar keine Spezialisierung kennt, landet hier
    nie (die Aufrufer prüfen das vorher selbst gegen
    ALLE_SPEZIALISIERUNGS_KATEGORIEN)."""
    return SPHAERE_SCHWELLEN if category in SPHAERE_KATEGORIEN else AUTOMATISCHE_SCHWELLEN


def automatische_slot_anzahl(alt: int, neu: int, schwellen: tuple[int, ...] = AUTOMATISCHE_SCHWELLEN) -> int:
    """Wie viele neue automatische Slots der Sprung von `alt` auf `neu` auslöst.

    `alt < schwelle <= neu` zählt jede überschrittene Schwelle einzeln — ein
    Sprung von z.B. 3 direkt auf 6 (Spielleitung setzt den Wert von Hand,
    oder ein frisch erstellter Charakter startet schon auf 6) überspringt
    dabei KEINE Schwelle: alle Schwellen im Intervall `(alt, neu]` werden
    vergeben (bei Sphären also bis zu drei auf einen Schlag).

    Ein Sinken des Werts (`neu < alt`) vergibt dadurch von selbst nie etwas
    — kein Sonderfall nötig. Und weil diese Funktion nur ADDIERT, nie
    löscht, verschwindet ein bereits vergebener Slot beim späteren Sinken
    des Ratings nicht wieder (Marks ausdrückliche Vorgabe).
    """
    return sum(1 for schwelle in schwellen if alt < schwelle <= neu)


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


FELDER = """
    s.id AS id, s.campaignId AS campaignId, s.personId AS personId,
    s.traitDefId AS traitDefId, s.text AS text, s.quelle AS quelle,
    s.benanntVonSpieler AS benanntVonSpieler, s.erstelltAm AS erstelltAm
"""


def _decode(record: dict) -> dict:
    daten = dict(record)
    daten["text"] = daten.get("text") or ""
    daten["quelle"] = daten.get("quelle") or "automatisch"
    daten["benanntVonSpieler"] = bool(daten.get("benanntVonSpieler"))
    daten["erstelltAm"] = daten.get("erstelltAm") or ""
    return daten


async def fuer_person(campaign_id: str, person_id: str) -> list[dict]:
    """Alle Spezialisierungen einer Person, über alle Fertigkeiten hinweg —
    das Charakterblatt gruppiert sie clientseitig nach traitDefId."""
    driver = get_driver()
    query = f"""
        MATCH (:Person {{id: $person_id, campaignId: $campaign_id}})-[:HAT_SPEZIALISIERUNG]->(s:Spezialisierung)
        RETURN {FELDER}
        ORDER BY s.erstelltAm
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id)
        return [_decode(dict(rec)) async for rec in result]


async def hole(campaign_id: str, person_id: str, spezialisierung_id: str) -> dict | None:
    driver = get_driver()
    query = f"""
        MATCH (:Person {{id: $person_id, campaignId: $campaign_id}})-[:HAT_SPEZIALISIERUNG]->(s:Spezialisierung {{id: $id}})
        RETURN {FELDER}
    """
    async with driver.session() as session:
        result = await session.run(query, campaign_id=campaign_id, person_id=person_id, id=spezialisierung_id)
        record = await result.single()
        return _decode(dict(record)) if record else None


async def _anlegen(campaign_id: str, person_id: str, trait_def_id: str, quelle: str) -> dict:
    driver = get_driver()
    neue_id = str(uuid.uuid4())
    query = f"""
        MATCH (p:Person {{id: $person_id, campaignId: $campaign_id}})
        CREATE (s:Spezialisierung {{
            id: $id, campaignId: $campaign_id, personId: $person_id,
            traitDefId: $trait_def_id, text: '', quelle: $quelle,
            benanntVonSpieler: false, erstelltAm: $jetzt
        }})
        CREATE (p)-[:HAT_SPEZIALISIERUNG]->(s)
        RETURN {FELDER}
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, person_id=person_id, trait_def_id=trait_def_id,
            id=neue_id, quelle=quelle, jetzt=_jetzt(),
        )
        record = await result.single()
        return _decode(dict(record))


async def automatisch_anlegen(campaign_id: str, person_id: str, trait_def_id: str, anzahl: int) -> list[dict]:
    """Legt `anzahl` neue, noch unbenannte Slots an (Schwelle 4/6 überschritten).

    Einzelne CREATE-Aufrufe statt eines Batch-Cyphers: bei maximal zwei
    Slots je Rating-Änderung unproblematisch, und es nutzt denselben
    Code-Pfad wie ein gekaufter Slot (`_anlegen`) statt eine zweite
    Query-Variante zu pflegen.
    """
    return [await _anlegen(campaign_id, person_id, trait_def_id, "automatisch") for _ in range(max(0, anzahl))]


async def gekauft_anlegen(campaign_id: str, person_id: str, trait_def_id: str) -> dict:
    """Ein einzelner, für 4 EP gekaufter Slot — siehe spezialisierungen/routes.py::kaufen."""
    return await _anlegen(campaign_id, person_id, trait_def_id, "gekauft")


async def benennen(
    campaign_id: str, person_id: str, spezialisierung_id: str, text: str, *, als_spieler: bool
) -> dict | None:
    """Setzt/ändert den Text eines Slots.

    Die Sperre ("nachträglich ändert nur die SL") prüft die Route VORHER
    (routes.py::benennen) — hier wird nur geschrieben, ohne erneute Prüfung,
    genau wie `traits/repository.py::steigere` den Preis nicht selbst prüft.
    """
    driver = get_driver()
    query = f"""
        MATCH (:Person {{id: $person_id, campaignId: $campaign_id}})-[:HAT_SPEZIALISIERUNG]->(s:Spezialisierung {{id: $id}})
        SET s.text = $text, s.benanntVonSpieler = $als_spieler
        RETURN {FELDER}
    """
    async with driver.session() as session:
        result = await session.run(
            query, campaign_id=campaign_id, person_id=person_id, id=spezialisierung_id,
            text=text, als_spieler=als_spieler,
        )
        record = await result.single()
        return _decode(dict(record)) if record else None
