"""Tutorial-Shop bleibt für Spieler lesbar, auch wenn der Ort GM-sichtbar ist.

Der Ort soll nicht auf der Karte auftauchen (sichtbarkeit GM). Der
Freebees-Schritt muss Sortiment und Kauf trotzdem sehen — sonst zeigt das
Popup „führt gerade nichts“, obwohl Ware eingetragen ist.
"""

from app.entities.visibility import shop_fuer_viewer_sichtbar


def test_tutorial_shop_ist_fuer_spieler_lesbar_obwohl_ort_gm():
    shop = {"istTutorialShop": True, "sichtbarkeit": "GM", "sichtbarFuer": []}
    assert shop_fuer_viewer_sichtbar(shop, "PLAYER", "person-1") is True


def test_normaler_gm_shop_bleibt_fuer_spieler_unsichtbar():
    shop = {"istTutorialShop": False, "sichtbarkeit": "GM", "sichtbarFuer": []}
    assert shop_fuer_viewer_sichtbar(shop, "PLAYER", "person-1") is False


def test_gm_sieht_jeden_shop():
    shop = {"istTutorialShop": False, "sichtbarkeit": "GM", "sichtbarFuer": []}
    assert shop_fuer_viewer_sichtbar(shop, "GM", None) is True


def test_tutorial_rest_unterschritten_ist_keins():
    from app.traits.erstellung import tutorial_rest

    assert tutorial_rest(80_000, 68_000) == 12_000
    assert tutorial_rest(10_000, 68_000) is None
    assert tutorial_rest(68_000, 68_000) == 0
