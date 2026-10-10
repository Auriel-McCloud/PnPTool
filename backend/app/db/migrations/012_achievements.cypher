// Achievement-Feature (10.10.2026): die Knoten-Constraints existierten schon
// seit der Ereignisprotokoll-Migration (006), hier kommt nur das fehlende
// Flag fuer den ENDBOSS_BESIEGT-Trigger dazu. Kein neues Constraint noetig,
// bestehende Person-Knoten bekommen das Feld einfach beim naechsten Lesen
// ueber den _decode()-Fallback (siehe repository.py) als false.
MATCH (p:Person)
WHERE p.istEndboss IS NULL
SET p.istEndboss = false;
