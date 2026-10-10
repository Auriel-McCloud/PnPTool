"""Reine Galerie-Helfer: Spieler-Portrait und Extra-Bilder dürfen sich nicht beißen."""

from app.entities.repository import galerie_primaer_ersetzen, galerie_url_entfernen


def test_ersetzen_haengt_erstes_bild_an():
    assert galerie_primaer_ersetzen([], "", "/neu.png") == [
        {"url": "/neu.png", "istPrimaer": True}
    ]


def test_ersetzen_tauscht_nur_das_primaerbild():
    vorher = [
        {"url": "/alt.png", "istPrimaer": True},
        {"url": "/extra.png", "istPrimaer": False},
    ]
    assert galerie_primaer_ersetzen(vorher, "/alt.png", "/neu.png") == [
        {"url": "/neu.png", "istPrimaer": True},
        {"url": "/extra.png", "istPrimaer": False},
    ]


def test_entfernen_befoerdert_das_naechste_bild():
    vorher = [
        {"url": "/alt.png", "istPrimaer": True},
        {"url": "/extra.png", "istPrimaer": False},
    ]
    rest, primaer = galerie_url_entfernen(vorher, "/alt.png")
    assert primaer == "/extra.png"
    assert rest == [{"url": "/extra.png", "istPrimaer": True}]


def test_entfernen_letztes_bild_leert_die_galerie():
    rest, primaer = galerie_url_entfernen(
        [{"url": "/alt.png", "istPrimaer": True}], "/alt.png"
    )
    assert rest == []
    assert primaer == ""
