"""Tests für die kampagnenweite Messenger-Option."""

from app.campaigns.repository import EINSTELLUNGEN_DEFAULTS


def test_messenger_ist_standardmaessig_deaktiviert():
    assert EINSTELLUNGEN_DEFAULTS["messengerAktiv"] is False
