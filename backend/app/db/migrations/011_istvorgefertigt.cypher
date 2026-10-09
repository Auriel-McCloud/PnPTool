// Vorgefertigte Charaktere (08.10.2026): bisher galt jeder abgeschlossene,
// niemandem zugeordnete PC automatisch als "vorgefertigt" im Ersteinstiegs-
// Fenster. Jetzt gibt es dafür ein echtes Feld (istVorgefertigt), das die
// Spielleitung bewusst setzt. Damit bestehende PCs nicht plötzlich aus der
// Auswahlliste verschwinden, markiert diese einmalige Migration alle
// aktuell unclaimed+abgeschlossenen PCs als vorgefertigt. Idempotent: das
// `IS NULL`-Kriterium greift nach dem ersten Lauf nicht mehr, weil das Feld
// dann überall gesetzt ist (egal ob true oder false).
MATCH (p:Person {personType: 'PC'})
WHERE p.istVorgefertigt IS NULL
  AND coalesce(p.erstellungAbgeschlossen, false) = true
  AND coalesce(p.istEntwurf, false) = false
  AND NOT EXISTS { MATCH (:Spieler)-[:SPIELT]->(p) }
SET p.istVorgefertigt = true;
