"""Welche Felder der Steckbrief-PATCH akzeptiert.

Die Charaktererstellung hält Name/Konzept/Alter nur im Browser, bis der
Assistent abschließt. Derselbe Endpunkt, der den Steckbrief nachträglich
ändert, muss Name und Alter deshalb auch als Entwurf schreiben können —
sonst ist ein Gerätewechsel (PC → Handy) ein leeres Formular.
"""

from app.traits.routes import SteckbriefUpdate


def test_steckbrief_nimmt_name_und_alter_fuer_entwurf():
    body = SteckbriefUpdate(
        name="Quill",
        konzept="der Held",
        alter="12",
        ambition="die Welt retten",
        verlangen="",
        ziel="",
    )
    dumped = body.model_dump()
    assert dumped["name"] == "Quill"
    assert dumped["konzept"] == "der Held"
    assert dumped["alter"] == "12"
    assert dumped["ambition"] == "die Welt retten"


def test_steckbrief_ohne_name_laesst_name_unangetastet():
    """None filtert update_node heraus — das Feld bleibt, wie es war."""
    body = SteckbriefUpdate(konzept="nur konzept")
    dumped = body.model_dump()
    assert dumped["name"] is None
    assert dumped["alter"] is None
    assert dumped["konzept"] == "nur konzept"
