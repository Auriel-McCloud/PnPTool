"""Seeds the TraitDef catalog for the built-in 'neotopia' ruleset.

Runs at every backend startup (see app/main.py). Uses a deterministic id
(ruleset:category:name) + MERGE, so it's idempotent — safe to run repeatedly
without duplicating or resetting GM-adjusted per-character ratings, which live
on the separate HAS_TRAIT relationship, not on TraitDef itself.
"""

from app.db.neo4j_driver import get_driver

# Kurze Definitionen fürs Tooltip UND für den KI-Prompt (app/ki/routes.py
# hängt genau diesen Text an den Katalog, damit die KI z.B. weiß, dass
# Feuermagie über "Kräfte" läuft, nicht über "Überleben"). Angelehnt an die
# Fertigkeits-Erklärungen aus dem WoD-Grundregelwerk (docs/reference/Regel
# Details - infotipp optionen.txt), aber auf NeotopiA/Cyberpunk umgeschrieben
# — kein "Magus"-Vokabular, sondern Straße, Konzerne, Chrom, Sprawl.
TRAIT_BESCHREIBUNGEN: dict[str, str] = {
    # --- Attribute Körperlich ---
    "Körperkraft": "Rohe Muskelkraft — heben, tragen, zuschlagen, Türen eintreten.",
    "Geschicklichkeit": "Reflexe, Balance, Feinmotorik — Zielen, Ausweichen, ruhige Hände.",
    "Widerstandsfähigkeit": "Zähigkeit — Schmerzen, Erschöpfung und Schaden wegstecken.",
    # --- Attribute Gesellschaftlich ---
    "Charisma": "Natürliche Ausstrahlung — Sympathie gewinnen, ohne sich anzustrengen.",
    "Manipulation": "Andere gezielt lenken — überreden, täuschen, unter Druck setzen.",
    "Fassung": "Innere Ruhe unter Stress — Nerven behalten, wenn andere durchdrehen.",
    # --- Attribute Geistig ---
    "Intelligenz": "Logik und Wissen anwenden — Probleme lösen, Zusammenhänge erkennen.",
    "Geistesschärfe": "Schnelle Auffassung — Details bemerken, rasch reagieren, im Vorteil bleiben.",
    "Entschlossenheit": "Willenskraft — durchhalten, wenn es hart wird, sich nicht brechen lassen.",
    # --- Fertigkeiten ---
    "Diebeshandwerk": "Schlösser knacken, Taschendiebstahl, Tresore, Sicherheitssysteme umgehen.",
    "Fahren": "Fahrzeuge sicher und unter Druck lenken — Verfolgungsjagden, Manöver.",
    "Handgemenge": "Waffenloser Nahkampf — Schläge, Tritte, Würfe, Klammergriffe.",
    "Handwerk": "Dinge von Hand bauen und reparieren — Mechanik, Elektronik, Werkstoffe.",
    "Heimlichkeit": "Unbemerkt bleiben — sich lautlos bewegen, in Schatten verschmelzen.",
    "Nahkampf": "Kampf mit Waffen — Messer, Stöcke, Klingen, Elektroschocker.",
    "Schusswaffen": "Umgang mit Feuerwaffen — Handhabung, Wartung, Treffsicherheit.",
    "Sportlichkeit": "Körperliche Fitness — Laufen, Klettern, Springen, Balance, Ausdauer.",
    "Überleben": "In Wildnis oder Straße zurechtkommen — Nahrung, Unterschlupf, Fallen, Feuer machen.",
    "Riggen": "Drohnen und Fahrzeuge per Fernsteuerung/Neuralverbindung führen.",
    "Anführen": "Leute zum Mitziehen bringen — Befehle geben, ein Team koordinieren.",
    "Ausflüchte": "Vertrauen gewinnen und ausnutzen — Lügen, Tricksen, Schwindeleien erkennen.",
    "Darbietung": "Auftreten vor Publikum — Musik, Schauspiel, Reden, Performance.",
    "Einschüchtern": "Angst einjagen — Drohgebärde, Präsenz, unterschwellige Gewaltandeutung.",
    "Etiketten": "Gesellschaftliche Umgangsformen — Konzernkreise, High Society, Verhandlungen.",
    "Menschenkenntnis": "Absichten und Lügen anderer durchschauen — Körpersprache, Tonfall lesen.",
    "Szenenkenntnis": "In der Unterwelt zuhause — Straßencodes, Schwarzmarkt, wer wen kennt.",
    "Tierkunde": "Umgang mit Tieren — verstehen, beruhigen, trainieren, versorgen.",
    "Überzeugen": "Andere durch Argumente und Auftreten auf die eigene Seite ziehen.",
    "Maker (Hardware)": "Cyberware, Drohnen und Gadgets bauen, modifizieren, aufrüsten.",
    "Ermitteln": "Spuren finden und verknüpfen — Beweise sichern, Zusammenhänge aufdecken.",
    "Finanzen": "Geldflüsse verstehen — Buchhaltung, Investitionen, Geldwäsche, Märkte lesen.",
    "Geisteswissenschaften": "Geschichte, Sprachen, Kultur, Recht — akademisches Allgemeinwissen.",
    "Medizin": "Wunden versorgen, Diagnosen stellen, medizinische Eingriffe durchführen.",
    "Naturwissenschaften": "Physik, Chemie, Biologie — technische und wissenschaftliche Theorie.",
    "Okkultismus": "Wissen über Magie, Sphären und das Übernatürliche — Theorie, nicht Praxis.",
    "Politik": "Machtstrukturen durchschauen — Konzernpolitik, Straßenpolitik, Bündnisse.",
    "Technologie": "Alltagselektronik bedienen und reparieren — Geräte, einfache Systeme.",
    "Wahrnehmung": "Aufmerksamkeit für Details — etwas bemerken, bevor es zu spät ist.",
    "Matrix": "Sich in der Matrix bewegen — Hacken, Icons lesen, digitale Spuren verfolgen.",
    # --- Hexkraft (Magiewert) ---
    "Hexkraft": "Rohe magische Macht — wie stark und zuverlässig ein Zauber wirkt.",
    # --- Sphären (was die Magie bewirken kann, nicht wie stark) ---
    "Korrespondenz": "Raum und Distanz manipulieren — Fernwahrnehmung, Teleportation, Dinge über Entfernung greifen.",
    "Entropie": "Zufall, Glück/Pech und Verfall lenken — Wahrscheinlichkeiten biegen, Systeme zersetzen, Schwachstellen finden.",
    "Kräfte": "Elementarenergie steuern — Feuer, Elektrizität, Schall, Licht, kinetische Wucht.",
    "Leben": "Lebendiges Gewebe formen — heilen, verwunden, mutieren, den eigenen Körper verändern.",
    "Materie": "Unbelebte Stoffe formen — Metall, Beton, Chemikalien verwandeln, verstärken oder erschaffen.",
    "Gedanken": "Bewusstsein beeinflussen — Gedanken lesen, Illusionen erzeugen, Willen beugen, Erinnerungen verändern.",
    "Ursprung": "Reine Energie an der Quelle anzapfen — Quintessenz ziehen, Dinge aus dem Nichts erschaffen, Auren lesen.",
    "Geister": "Mit der Astralebene und ihren Bewohnern interagieren — dorthin reisen, Geister rufen, binden, verbannen.",
    "Zeit": "Zeit wahrnehmen und verschieben — Vorausschau, Verlangsamung, kurze Sprünge vor oder zurück.",
    # --- NeuroWeaving (Matrix ohne Gerät) ---
    "NeuroWeaving": "Rohe Stärke beim Weben in der Matrix — wie stark und zuverlässig es wirkt.",
    "Brute Force": "Sicherheitssysteme direkt durchbrechen — roh, laut, aber effektiv.",
    "Schleichen": "Unbemerkt durch Systeme bewegen — Spuren verwischen, ICE umgehen.",
    "Daten Verarbeiten": "Große Datenmengen durchsuchen, filtern und auswerten.",
    "Kompilieren": "Eigene Programme/Effekte in Echtzeit zusammenbauen.",
}


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
    # NeuroWeaving: erst der Wert selbst, dann die vier Fertigkeiten.
    # Aufgebaut wie Hexkraft + Sphären — mit dem Unterschied, dass die
    # Fertigkeiten hier **mitgewürfelt** werden (Regelblatt Zeile 45/96),
    # während Sphären nur beschreiben, was möglich ist.
    ("NeuroWeaving", "NeuroWeavingWert", 10, 1),
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
    # Hexkraft ist der Magiewert selbst (nicht zu verwechseln mit den Sphären,
    # die nur beschreiben was möglich ist). Auf dem Blatt eine Reihe von zehn
    # Kästchen, daher Maximum 10 statt 5 wie bei Fähigkeiten. Kostet in der
    # Erstellung 5 Freebees wie ein Attribut.
    ("Hexkraft", "Hexkraft", 10, 1),
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

# Hintergründe haben ihre Beschreibung schon in HINTERGRUENDE (erstellung.py)
# — hier nachziehen, damit Tooltip/KI-Prompt aus derselben Quelle stammen wie
# der Erstellungs-Assistent, statt den Text ein zweites Mal zu pflegen.
TRAIT_BESCHREIBUNGEN.update({h["name"]: h["beschreibung"] for h in HINTERGRUENDE})


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
                    t.defaultMax = $defaultMax, t.sortOrder = $sortOrder,
                    t.description = $description
                """,
                id=trait_id,
                ruleset=ruleset,
                name=name,
                category=category,
                defaultMax=default_max,
                sortOrder=sort_order,
                description=TRAIT_BESCHREIBUNGEN.get(name, ""),
            )

        await _migriere_arete_zu_hexkraft(session)
        await _seed_trait_erklaerungen(session, ruleset)


async def _seed_trait_erklaerungen(session, ruleset: str) -> None:
    """Befüllt die Erklärungen (Tooltip-Text) aus TRAIT_BESCHREIBUNGEN.

    Ein von der Spielleitung von Hand geschriebener Text (`quelle='HAND'`)
    wird **nie** überschrieben. Ein noch unbearbeiteter KI-Text
    (`quelle='KI'`) darf dagegen aktualisiert werden — so kommen spätere
    Verbesserungen an TRAIT_BESCHREIBUNGEN auch bei bereits gesäten
    Kampagnen an, ohne echte Redaktionsarbeit der SL zu gefährden.
    """
    for name, text in TRAIT_BESCHREIBUNGEN.items():
        schluessel = f"trait:{name}"
        await session.run(
            """
            MERGE (e:Erklaerung {ruleset: $ruleset, schluessel: $schluessel})
            ON CREATE SET e.id = $ruleset + ':' + $schluessel,
                          e.titel = $name, e.text = $text, e.quelle = 'KI'
            ON MATCH SET e.titel = CASE WHEN e.quelle = 'HAND' THEN e.titel ELSE $name END,
                         e.text = CASE WHEN e.quelle = 'HAND' THEN e.text ELSE $text END
            """,
            ruleset=ruleset,
            schluessel=schluessel,
            name=name,
            text=text,
        )


# Alte Kennung aus der Zeit, als der Magiewert "Arete" hiess.
_ALT_ARETE_ID = "neotopia:Arete:Arete"
_HEXKRAFT_ID = "neotopia:Hexkraft:Hexkraft"


async def _migriere_arete_zu_hexkraft(session) -> None:
    """Einmalige Datenkorrektur: aus "Arete" wurde "Hexkraft".

    **Warum es diese Migration überhaupt braucht:** die TraitDef-Kennung ist
    `ruleset:category:name` (siehe oben). Beim Umbenennen im Katalog änderte
    sich damit auch die Kennung — `MERGE` legte also einen *neuen*, leeren
    Knoten `Hexkraft` an, während der alte `Arete`-Knoten mit allen daran
    hängenden Charakterwerten (`HAS_TRAIT`, dort liegt das `rating`) stehen
    blieb. Ergebnis vor dieser Korrektur: das Charakterblatt zeigte die alte
    Arete-Zeile mit den echten Punkten, die Kampfkarte den neuen, leeren
    Hexkraft-Wert — und weil "Arete" für `bogen.sichtbare_kategorien` keine
    Magie-Kategorie mehr ist, sah plötzlich *jeder* Charakter die Zeile.

    Hängt die Werte deshalb auf den Hexkraft-Knoten um und räumt den alten
    weg. Idempotent: nach dem ersten Lauf gibt es keinen Arete-Knoten mehr,
    danach tut sie nichts.

    Ist am Zielwert schon etwas eingetragen (jemand hat nach einem Neustart
    bereits Hexkraft gesetzt), bleibt der neuere Wert stehen — überschrieben
    wird nur eine noch leere 0.
    """
    ergebnis = await session.run(
        """
        MATCH (alt:TraitDef {id: $alt_id})
        MATCH (n)-[h:HAS_TRAIT]->(alt)
        MATCH (neu:TraitDef {id: $neu_id})
        MERGE (n)-[nh:HAS_TRAIT]->(neu)
          ON CREATE SET nh.rating = h.rating, nh.maxOverride = h.maxOverride
          ON MATCH SET nh.rating = CASE WHEN coalesce(nh.rating, 0) = 0 THEN h.rating ELSE nh.rating END
        DELETE h
        RETURN count(*) AS umgehaengt
        """,
        alt_id=_ALT_ARETE_ID,
        neu_id=_HEXKRAFT_ID,
    )
    datensatz = await ergebnis.single()
    umgehaengt = datensatz["umgehaengt"] if datensatz else 0

    # Erst wenn nichts mehr daran hängt — so kann die Migration niemals
    # Charakterwerte mitnehmen, auch wenn oben etwas schiefgegangen wäre.
    await session.run(
        """
        MATCH (alt:TraitDef {id: $alt_id})
        WHERE NOT ()-[:HAS_TRAIT]->(alt)
        DELETE alt
        """,
        alt_id=_ALT_ARETE_ID,
    )
    if umgehaengt:
        print(f"[seed] Arete → Hexkraft: {umgehaengt} Charakterwert(e) umgehängt")
