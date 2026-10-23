"""Ambition/Verlangen: nur Namen aus den lokalen Archetyp-Vorlagen."""

import json

from app.ki.routes import _charakter_konzept_schema
from app.regeln import vorlagen
from app.regeln.vorlagen import nur_archetyp


def test_nur_archetyp_nimmt_nur_den_kanonischen_namen():
    namen = ["Hacker", "Einzelgänger"]
    assert nur_archetyp("hacker", namen) == "Hacker"
    assert nur_archetyp("  Einzelgänger  ", namen) == "Einzelgänger"
    assert nur_archetyp("Die Welt retten", namen) == ""
    assert nur_archetyp("Hacker — die Schlüssel dazu", namen) == ""
    assert nur_archetyp("Hacker", []) == ""
    assert nur_archetyp(None, namen) == ""


def test_archetyp_namen_liest_nur_namen(tmp_path, monkeypatch):
    datei = tmp_path / "vorlagen.local.json"
    datei.write_text(
        json.dumps(
            {
                "ambition": [
                    {"name": "Hacker", "text": "langer Erklärungstext"},
                    {"name": " hacker ", "text": "duplikat"},
                    {"name": "", "text": "leer"},
                    "kein-dict",
                    {"name": "Einzelgänger", "text": "auch lang"},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(vorlagen, "VORLAGEN_DATEI", datei)
    assert vorlagen.archetyp_namen() == ["Hacker", "Einzelgänger"]


def test_schema_ohne_vorlagen_laesst_ambition_weg():
    schema = _charakter_konzept_schema(["Mensch"], [])
    assert "ambition" not in schema["properties"]
    assert "verlangen" not in schema["properties"]
    assert "ambition" not in schema["required"]


def test_schema_mit_vorlagen_ist_enum():
    schema = _charakter_konzept_schema(["Mensch"], ["Hacker", "Einzelgänger"])
    assert schema["properties"]["ambition"]["enum"] == ["Hacker", "Einzelgänger"]
    assert schema["properties"]["verlangen"]["enum"] == ["Hacker", "Einzelgänger"]
    assert "ambition" in schema["required"]
    assert "verlangen" in schema["required"]
