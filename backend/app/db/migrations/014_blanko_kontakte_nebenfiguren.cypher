// Nebenfiguren (10.11.2026): leere Kontakt- und Mentor-Plaetze aus dem
// Kontakte-Hintergrund standen bisher als NPC in der NPC-Liste. Seit heute
// legt spawn.py sie als Nebenfigur an - diese einmalige Migration zieht den
// Altbestand nach. Idempotent: das IS-NULL-Kriterium greift nach dem ersten
// Lauf nicht mehr. Die Befuellung (kontakte/routes.py::kontakt_generieren)
// erkennt den Platz weiter an istBlankoKontakt.
MATCH (p:Person)
WHERE coalesce(p.istBlankoKontakt, false) = true
  AND p.istNebenfigur IS NULL
SET p.istNebenfigur = true;
