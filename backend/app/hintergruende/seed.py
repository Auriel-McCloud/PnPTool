"""Fest verdrahtete System-Hintergründe vs. narrativer Seed.

Mentor und Kontakte sind Mechanik (eigener Code), nicht Katalogzeilen.
Der Seed ist der alte Zehner-Katalog minus diese zwei — editierbar.
"""

SYSTEM_SCHLUESSEL = ("MENTOR", "KONTAKTE")

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
