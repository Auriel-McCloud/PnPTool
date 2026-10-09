// „Story relevant" (09.10.2026, Spieler-Lexikon): zeigeInGraph wird zu
// storyRelevant umbenannt — gleiche Bedeutung (MacGuffin-Objekte im
// Beziehungsgraph UND neu: Grundlage für die Lexikon-Entdeckungskette), nur
// klarerer Name. Bestandsdaten behalten ihren Wert, sonst Stolperstein 6
// (TraitDef-Umbenennen, siehe neo4j-datenmodell.md) — altes Feld bleibt
// zusätzlich stehen, falls irgendein Hand-Cypher-Pfad es noch liest.
MATCH (g:Gegenstand)
WHERE g.zeigeInGraph IS NOT NULL AND g.storyRelevant IS NULL
SET g.storyRelevant = g.zeigeInGraph;
