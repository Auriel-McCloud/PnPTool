"""Tests für Ki-Tama-Fertigkeiten (29.10.2026, Marks FF7-Idee, 30.10.2026
umbenannt von "Materia" zu "Ki-Tama" — jap. "Tama" = Perle/Kugel + "Ki" =
KI-Kristall) — reine Funktionen rund um den synthetischen traitDefId, der
eine Ki-Tama-Fähigkeit transparent ins normale EP-Steigern-Popup
einschleust, siehe app/traits/erfahrung.py::kitama_schluessel/
kitama_entschluesseln und docs/wiki/concepts/augments-ausruestung.md."""

from app.traits.erfahrung import kitama_entschluesseln, kitama_schluessel, kosten


class TestKiTamaSchluessel:
    def test_rundreise(self):
        schluessel = kitama_schluessel("item-123", "Blitz")
        assert kitama_entschluesseln(schluessel) == ("item-123", "Blitz")

    def test_name_mit_doppelpunkten_bleibt_ganz(self):
        # Ein (unwahrscheinlicher, aber möglicher) Fertigkeitsname mit "::"
        # darf nicht an der zweiten Fundstelle abgeschnitten werden — nur
        # der ERSTE Doppelpunkt-Block nach dem Präfix trennt Gegenstand-ID
        # und Name, der Rest gehört komplett zum Namen.
        schluessel = kitama_schluessel("item-123", "Stufe::Feuer")
        assert kitama_entschluesseln(schluessel) == ("item-123", "Stufe::Feuer")

    def test_normaler_traitdefid_ist_kein_kitama_schluessel(self):
        assert kitama_entschluesseln("ganz-normale-uuid-1234") is None

    def test_leeres_praefix_ohne_rest_ist_ungueltig(self):
        assert kitama_entschluesseln("kitama::") is None
        assert kitama_entschluesseln("kitama::nur-eine-id-ohne-trenner") is None


class TestKiTamaKostenkurve:
    def test_nutzt_dieselbe_kurve_wie_normale_fertigkeiten(self):
        # Mark: "ich habe vor dass das grundsätzlich nur skills sind" —
        # Ki-Tama kostet also exakt wie "Fertigkeit", keine eigene Tabelle.
        assert kosten("Fertigkeit", 0) == 3
        assert kosten("Fertigkeit", 1) == 2
        assert kosten("Fertigkeit", 5) == 10
