"""Seeds the TraitDef catalog for the built-in 'neotopia' ruleset.

Runs at every backend startup (see app/main.py). Uses a deterministic id
(ruleset:category:name) + MERGE, so it's idempotent — safe to run repeatedly
without duplicating or resetting GM-adjusted per-character ratings, which live
on the separate HAS_TRAIT relationship, not on TraitDef itself.
"""

from app.db.neo4j_driver import get_driver

# (name, category, defaultMax, sortOrder) — aus Neotopia.xlsx (Charakterblatt-Sheet)
NEOTOPIA_TRAITS: list[tuple[str, str, int, int]] = [
    # Attribute Körperlich (6 Punkte)
    ("Körperkraft", "AttributKörperlich", 6, 1),
    ("Geschicklichkeit", "AttributKörperlich", 6, 2),
    ("Widerstandsfähigkeit", "AttributKörperlich", 6, 3),
    # Attribute Gesellschaftlich
    ("Charisma", "AttributGesellschaftlich", 6, 1),
    ("Manipulation", "AttributGesellschaftlich", 6, 2),
    ("Fassung", "AttributGesellschaftlich", 6, 3),
    # Attribute Geistig
    ("Intelligenz", "AttributGeistig", 6, 1),
    ("Geistesschärfe", "AttributGeistig", 6, 2),
    ("Entschlossenheit", "AttributGeistig", 6, 3),
    # Fertigkeiten (5 Punkte)
    ("Diebeshandwerk", "Fertigkeit", 5, 1),
    ("Fahren", "Fertigkeit", 5, 2),
    ("Handgemenge", "Fertigkeit", 5, 3),
    ("Handwerk", "Fertigkeit", 5, 4),
    ("Heimlichkeit", "Fertigkeit", 5, 5),
    ("Nahkampf", "Fertigkeit", 5, 6),
    ("Schusswaffen", "Fertigkeit", 5, 7),
    ("Sportlichkeit", "Fertigkeit", 5, 8),
    ("Überleben", "Fertigkeit", 5, 9),
    ("Riggen", "Fertigkeit", 5, 10),
    ("Anführen", "Fertigkeit", 5, 11),
    ("Ausflüchte", "Fertigkeit", 5, 12),
    ("Darbietung", "Fertigkeit", 5, 13),
    ("Einschüchtern", "Fertigkeit", 5, 14),
    ("Etiketten", "Fertigkeit", 5, 15),
    ("Menschenkenntnis", "Fertigkeit", 5, 16),
    ("Szenenkenntnis", "Fertigkeit", 5, 17),
    ("Tierkunde", "Fertigkeit", 5, 18),
    ("Überzeugen", "Fertigkeit", 5, 19),
    ("Maker (Hardware)", "Fertigkeit", 5, 20),
    ("Ermitteln", "Fertigkeit", 5, 21),
    ("Finanzen", "Fertigkeit", 5, 22),
    ("Geisteswissenschaften", "Fertigkeit", 5, 23),
    ("Medizin", "Fertigkeit", 5, 24),
    ("Naturwissenschaften", "Fertigkeit", 5, 25),
    ("Okkultismus", "Fertigkeit", 5, 26),
    ("Politik", "Fertigkeit", 5, 27),
    ("Technologie", "Fertigkeit", 5, 28),
    ("Wahrnehmung", "Fertigkeit", 5, 29),
    ("Matrix", "Fertigkeit", 5, 30),
    # NeuroWeaving
    ("Brute Force", "NeuroWeaving", 5, 1),
    ("Schleichen", "NeuroWeaving", 5, 2),
    ("Daten Verarbeiten", "NeuroWeaving", 5, 3),
    ("Kompilieren", "NeuroWeaving", 5, 4),
    # Sphären
    ("Korrespondenz", "Sphäre", 5, 1),
    ("Entropie", "Sphäre", 5, 2),
    ("Kräfte", "Sphäre", 5, 3),
    ("Leben", "Sphäre", 5, 4),
    ("Materie", "Sphäre", 5, 5),
    ("Gedanken", "Sphäre", 5, 6),
    ("Ursprung", "Sphäre", 5, 7),
    ("Geister", "Sphäre", 5, 8),
    ("Zeit", "Sphäre", 5, 9),
    # Arete ist der Magiewert selbst (nicht zu verwechseln mit den Sphären,
    # die nur beschreiben was möglich ist). Auf dem Blatt eine Reihe von zehn
    # Kästchen, daher Maximum 10 statt 5 wie bei Fähigkeiten. Kostet in der
    # Erstellung 5 Freebees wie ein Attribut.
    ("Arete", "Arete", 10, 1),
]

# Hintergründe stehen **nicht** im Regelwerk — siehe traits/erstellung.py.
# Sie liegen trotzdem im selben Katalog wie alles andere: dadurch erscheinen
# sie ohne Zusatzarbeit auf dem Blatt, lassen sich mit Erfahrung steigern und
# vom Spielleiter überschreiben. Die Liste kommt aus erstellung.py, damit
# Erstellung und Katalog nicht auseinanderlaufen können.
from app.traits.erstellung import HINTERGRUENDE, HINTERGRUND_KATEGORIE, HINTERGRUND_MAX  # noqa: E402

NEOTOPIA_TRAITS += [
    (h["name"], HINTERGRUND_KATEGORIE, HINTERGRUND_MAX, i + 1) for i, h in enumerate(HINTERGRUENDE)
]


async def seed_traits() -> None:
    driver = get_driver()
    ruleset = "neotopia"
    async with driver.session() as session:
        for name, category, default_max, sort_order in NEOTOPIA_TRAITS:
            trait_id = f"{ruleset}:{category}:{name}"
            await session.run(
                """
                MERGE (t:TraitDef {id: $id})
                SET t.ruleset = $ruleset, t.name = $name, t.category = $category,
                    t.defaultMax = $defaultMax, t.sortOrder = $sortOrder
                """,
                id=trait_id,
                ruleset=ruleset,
                name=name,
                category=category,
                defaultMax=default_max,
                sortOrder=sort_order,
            )
