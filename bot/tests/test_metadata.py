import importlib.metadata
import pytest

def test_metadata():
    meta = importlib.metadata.metadata("dirty_launderer_bot")
    assert meta["Name"] == "dirty_launderer_bot"
    assert meta["Author"] == "The-Dirty-Launderer" or meta["Author"] == "Your Name"
    assert meta["Summary"] == "A Telegram bot for cleaning and sanitizing URLs" 