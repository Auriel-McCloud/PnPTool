CREATE CONSTRAINT kiberatung_id IF NOT EXISTS FOR (n:KiBeratung) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT kiberatungnachricht_id IF NOT EXISTS FOR (n:KiBeratungNachricht) REQUIRE n.id IS UNIQUE;
