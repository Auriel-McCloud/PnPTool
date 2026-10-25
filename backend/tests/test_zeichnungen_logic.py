"""Tests für die reine Berechtigungslogik des Whiteboards (keine DB nötig)."""

from app.zeichnungen.logic import darf_zeichnen

GM = "GM"
SPIELER = "PLAYER"
KIRA = "kira-id"
BOSS = "boss-id"


class TestDarfZeichnen:
    def test_gm_darf_immer_zeichnen(self):
        board = {"spielerDuerfenZeichnen": False, "sichtbarkeit": "GM", "sichtbarFuer": []}
        assert darf_zeichnen(board, GM, None) is True

    def test_spieler_ohne_freigabe_darf_nicht(self):
        board = {"spielerDuerfenZeichnen": False, "sichtbarkeit": "ALLE", "sichtbarFuer": []}
        assert darf_zeichnen(board, SPIELER, KIRA) is False

    def test_spieler_mit_freigabe_und_sichtbarkeit_alle_darf(self):
        board = {"spielerDuerfenZeichnen": True, "sichtbarkeit": "ALLE", "sichtbarFuer": []}
        assert darf_zeichnen(board, SPIELER, KIRA) is True

    def test_spieler_mit_freigabe_aber_board_fuer_ihn_unsichtbar_darf_nicht(self):
        """Freigabe allein reicht nicht — wer das Board gar nicht sehen darf,
        darf erst recht nicht hineinzeichnen (Sichtbarkeit bleibt die äußere Grenze)."""
        board = {"spielerDuerfenZeichnen": True, "sichtbarkeit": "SPEZIFISCH", "sichtbarFuer": [BOSS]}
        assert darf_zeichnen(board, SPIELER, KIRA) is False

    def test_spieler_mit_freigabe_und_spezifisch_passend_darf(self):
        board = {"spielerDuerfenZeichnen": True, "sichtbarkeit": "SPEZIFISCH", "sichtbarFuer": [KIRA]}
        assert darf_zeichnen(board, SPIELER, KIRA) is True

    def test_fehlendes_feld_wird_als_false_behandelt(self):
        """Bestandsdaten/defensiver Default: kein Flag heißt keine Freigabe."""
        board = {"sichtbarkeit": "ALLE", "sichtbarFuer": []}
        assert darf_zeichnen(board, SPIELER, KIRA) is False
