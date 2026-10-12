"""Fest verdrahtete System-Hintergründe vs. narrativer Seed.

Mentor, Kontakte und Schulden sind Mechanik (eigener Code), nicht Katalogzeilen.
Der Seed ist der alte Zehner-Katalog minus Mentor/Kontakte — editierbar.
"""

SYSTEM_SCHLUESSEL = ("MENTOR", "KONTAKTE", "SCHULDEN")

# Sichtbar im SL-Baukasten (HintergruendeVerwaltung.tsx) als eigene, nicht
# editierbare Zeilen — nur je Kampagne an-/abschaltbar über campaigns.py::
# EINSTELLUNGEN_DEFAULTS. Reine Anzeige-/Schalter-Metadaten, die Mechanik
# selbst steckt in mentor.py/kredithai.py/spawn.py.
SYSTEM_HINTERGRUENDE: list[dict[str, str]] = [
    {
        "schluessel": "MENTOR",
        "name": "Mentor",
        "beschreibung": (
            "Jemand, der mehr weiß als du und dir bisweilen etwas davon abgibt. "
            "Erzeugt bei Abschluss der Erstellung einen vollen KI-NPC inkl. Tutorial-Shop-Einkauf."
        ),
        "einstellung": "mentorAktiv",
    },
    {
        "schluessel": "KONTAKTE",
        "name": "Kontakte",
        "beschreibung": (
            "Leute, die ans Telefon gehen. Legt leere \"Unbekannter Kontakt\"-Plätze an, "
            "die der Spieler später selbst mit einem Wunsch befüllt."
        ),
        "einstellung": "kontakteAktiv",
    },
    {
        "schluessel": "SCHULDEN",
        "name": "Schulden",
        "beschreibung": (
            "Startkapital auf Pump über den Kredit-Freebee bei der Erstellung — "
            "ein Kredithai-NPC will es zurück."
        ),
        "einstellung": "schuldenAktiv",
    },
]

# Texte aus traits/erstellung.py::HINTERGRUENDE, Stand vor dem Baukasten.
NARRATIVE_SEED: list[dict[str, str]] = [
    {"name": "Ressourcen", "kurzbeschreibung": "Regelmäßiges Einkommen, das nicht vom nächsten Auftrag abhängt.", "detailbeschreibung": ""},
    {"name": "Straßenruf", "kurzbeschreibung": "Was man über dich erzählt, bevor du den Raum betrittst.", "detailbeschreibung": ""},
    {"name": "Verbündete", "kurzbeschreibung": "Einzelne, die für dich einstehen — und selbst etwas können.", "detailbeschreibung": ""},
    {"name": "Unterschlupf", "kurzbeschreibung": "Ein Ort, den außer dir niemand kennt. Größe und Ausstattung.", "detailbeschreibung": ""},
    {"name": "Schwarzmarkt", "kurzbeschreibung": "Zugang zu dem, was es offiziell nicht zu kaufen gibt.", "detailbeschreibung": ""},
    {"name": "Konzernzugang", "kurzbeschreibung": "Ausweis, Freigabe, ein Name in einer Datenbank.", "detailbeschreibung": ""},
    {"name": "Ausrüstung", "kurzbeschreibung": "Gerät über den Startbestand hinaus, das dir bereits gehört.", "detailbeschreibung": ""},
    {"name": "Geheimwissen", "kurzbeschreibung": "Etwas, das kaum jemand weiß — und das jemand geheim halten will.", "detailbeschreibung": ""},
]
