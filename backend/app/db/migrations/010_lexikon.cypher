// Spieler-Lexikon (09.10.2026): ENTDECKT/FAVORISIERT sind reine Kanten ohne
// eigenen Knotentyp, brauchen daher keinen Unique-Constraint — aber ein
// Index auf der ENTDECKT-Quelle (Person) hilft der Neuberechnung, die pro PC
// arbeitet (siehe app/lexikon/entdeckung.py).
CREATE INDEX entdeckt_seit IF NOT EXISTS FOR ()-[r:ENTDECKT]-() ON (r.seit);
