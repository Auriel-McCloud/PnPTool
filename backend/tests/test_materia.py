"""Tests für Materia-Fertigkeiten (29.10.2026, Marks FF7-Idee) — reine
Funktionen rund um den synthetischen traitDefId, der eine Materia-Fähigkeit
transparent ins normale EP-Steigern-Popup einschleust, siehe
app/traits/erfahrung.py::materia_schluessel/materia_entschluesseln und
docs/wiki/concepts/augments-ausruestung.md."""

from app.traits.erfahrung import kosten, materia_entschluesseln, materia_schluessel


class TestMateriaSchluessel:
    def test_rundreise(self):
        schluessel = materia_schluessel("item-123", "Blitz")
        assert materia_entschluesseln(schluessel) == ("item-123", "Blitz")

    def test_name_mit_doppelpunkten_bleibt_ganz(self):
        # Ein (unwahrscheinlicher, aber möglicher) Fertigkeitsname mit "::"
        # darf nicht an der zweiten Fundstelle abgeschnitten werden — nur
        # der ERSTE Doppelpunkt-Block nach dem Präfix trennt Gegenstand-ID
        # und Name, der Rest gehört komplett zum Namen.
        schluessel = materia_schluessel("item-123", "Stufe::Feuer")
        assert materia_entschluesseln(schluessel) == ("item-123", "Stufe::Feuer")

    def test_normaler_traitdefid_ist_kein_materia_schluessel(self):
        assert materia_entschluesseln("ganz-normale-uuid-1234") is None

    def test_leeres_praefix_ohne_rest_ist_ungueltig(self):
        assert materia_entschluesseln("materia::") is None
        assert materia_entschluesseln("materia::nur-eine-id-ohne-trenner") is None


class TestMateriaKostenkurve:
    def test_nutzt_dieselbe_kurve_wie_normale_fertigkeiten(self):
        # Mark: "ich habe vor dass das grundsätzlich nur skills sind" —
        # Materia kostet also exakt wie "Fertigkeit", keine eigene Tabelle.
        assert kosten("Fertigkeit", 0) == 3
        assert kosten("Fertigkeit", 1) == 2
        assert kosten("Fertigkeit", 5) == 10
