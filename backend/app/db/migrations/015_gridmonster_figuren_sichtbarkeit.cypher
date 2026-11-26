// GridMonster-Figuren (26.11.2026): das Grundgerüst legte Personen ohne
// Sichtbarkeits-Felder an, die allgemeine Personenliste (/personen) lehnte
// sie dann ab. Seit heute setzt gridmonster/repository.py::anlegen sie, diese
// Migration zieht den Altbestand nach. Idempotent über IS NULL.
MATCH (p:Person)
WHERE p.istMonster IS NOT NULL AND p.sichtbarkeit IS NULL
SET p.sichtbarkeit = 'ALLE',
    p.sichtbarFuer = coalesce(p.sichtbarFuer, []),
    p.notizenSichtbarkeit = coalesce(p.notizenSichtbarkeit, 'GM'),
    p.notizenSichtbarFuer = coalesce(p.notizenSichtbarFuer, []);
