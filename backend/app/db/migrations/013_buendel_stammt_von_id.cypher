// Kampagnen-Bündel, Phase 1 (23.10.2026): stammtVonId ist eine stabile
// Herkunfts-Kennung, getrennt von der echten Neo4j-`id` (die bei jedem
// künftigen Bündel-Import in Phase 2 neu vergeben wird, siehe
// app/campaigns/buendel_export.py). Für NEUE Knoten setzen create_node()
// (app/entities/repository.py) sowie die Pendants in items/wiki/rassen/
// achievements das Feld ab sofort selbst bei der Erstellung. Dieser
// Nachtrag befüllt nur Bestandsdaten, die das Feld noch nicht kennen.
//
// Idempotent (WHERE stammtVonId IS NULL) wie jede andere Migration in
// diesem Ordner — unbedenklich bei jedem Backend-Neustart erneut
// auszuführen (apply_migrations() in app/db/migrate.py läuft bei jedem
// Start, siehe app/main.py::lifespan). Läuft beim nächsten Neustart des
// Backend-Containers automatisch mit, auch auf der Live-Datenbank nach dem
// Deploy dieses Branches — kein manueller Eingriff nötig.
MATCH (n)
WHERE (n:Ort OR n:Gegenstand OR n:Fraktion OR n:Person OR n:Gewaechs
       OR n:Event OR n:WikiSeite OR n:Rasse OR n:Achievement)
  AND n.stammtVonId IS NULL
SET n.stammtVonId = n.id;
