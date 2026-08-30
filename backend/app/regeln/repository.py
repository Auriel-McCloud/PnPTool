"""Erklärungen zu Fachbegriffen — die Quelle fürs Tooltip-System.

Ein `Erklaerung`-Knoten je Begriff, **pro Regelwerk** und nicht pro Kampagne:
was Widerstandsfähigkeit bedeutet, ist in jeder NeotopiA-Runde dasselbe. Der
Schlüssel benennt, worum es geht:

* `trait:Körperkraft` — ein Wert aus dem Katalog
* `bogen:gesundheit` — ein abgeleiteter Wert des Blatts
* `regel:initiative` — ein Regelbegriff ohne eigenes Feld

Bewusst ein eigener Knoten statt einer Eigenschaft am `TraitDef`: erklärt
werden soll **alles** auf dem Blatt, und Gesundheit, Initiative oder I.C.E.
stehen gar nicht im Katalog. Ausserdem sollen die Texte später im Werkzeug
selbst überarbeitet werden (geplante Claude-/Gemini-Anbindung) — als eigener
Knoten lassen sie sich schreiben, ohne den Katalog anzufassen, den das
Seeding bei jedem Start neu setzt.
"""

from app.db.neo4j_driver import get_driver


async def list_erklaerungen(ruleset: str) -> list[dict]:
    driver = get_driver()
    query = """
        MATCH (e:Erklaerung {ruleset: $ruleset})
        RETURN e.schluessel AS schluessel, e.titel AS titel, e.text AS text,
               e.quelle AS quelle
        ORDER BY e.schluessel
    """
    async with driver.session() as session:
        result = await session.run(query, ruleset=ruleset)
        return [
            {
                "schluessel": r["schluessel"],
                "titel": r["titel"] or "",
                "text": r["text"] or "",
                # Woher der Text stammt: von Hand geschrieben oder von einem
                # Modell erzeugt. Damit später erkennbar bleibt, was noch
                # niemand gegengelesen hat.
                "quelle": r["quelle"] or "HAND",
            }
            async for r in result
        ]


async def setze_erklaerung(ruleset: str, schluessel: str, titel: str, text: str, quelle: str) -> dict:
    """Legt an oder überschreibt. Leerer Text löscht den Eintrag."""
    driver = get_driver()
    if not text.strip():
        async with driver.session() as session:
            await session.run(
                "MATCH (e:Erklaerung {ruleset: $ruleset, schluessel: $schluessel}) DETACH DELETE e",
                ruleset=ruleset,
                schluessel=schluessel,
            )
        return {"schluessel": schluessel, "titel": "", "text": "", "quelle": "HAND"}

    query = """
        MERGE (e:Erklaerung {ruleset: $ruleset, schluessel: $schluessel})
        SET e.id = $ruleset + ':' + $schluessel,
            e.titel = $titel, e.text = $text, e.quelle = $quelle
        RETURN e.schluessel AS schluessel, e.titel AS titel, e.text AS text, e.quelle AS quelle
    """
    async with driver.session() as session:
        result = await session.run(
            query, ruleset=ruleset, schluessel=schluessel, titel=titel, text=text, quelle=quelle
        )
        record = await result.single()
        return dict(record)
