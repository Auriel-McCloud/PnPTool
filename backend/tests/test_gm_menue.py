"""GM-Menü-Layouts: leere/kaputte Speicherung wird zur Default-Form."""

from app.auth.menue import LEER_LAYOUT, normalisiere_layouts


def test_nichts_gespeichert_liefert_leere_slots():
    assert normalisiere_layouts(None) == {"pc": LEER_LAYOUT, "tablet": LEER_LAYOUT}


def test_json_wird_uebernommen():
    roh = '{"pc":{"ordnung":["pcs","wiki"],"ausgeblendet":["rassen"]},"tablet":{"ordnung":["kampf"],"ausgeblendet":[]}}'
    layouts = normalisiere_layouts(roh)
    assert layouts["pc"]["ordnung"] == ["pcs", "wiki"]
    assert layouts["pc"]["ausgeblendet"] == ["rassen"]
    assert layouts["tablet"]["ordnung"] == ["kampf"]


def test_muell_wird_verschluckt():
    assert normalisiere_layouts("{nein")["pc"] == LEER_LAYOUT
    assert normalisiere_layouts('{"pc": 5}')["pc"] == LEER_LAYOUT
