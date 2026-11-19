"""Tests for stavrophora.config — StavrophoraSettings and get_settings."""

import pytest

from stavrophora.config import StavrophoraSettings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Clear the lru_cache on get_settings before and after every test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_default_settings():
    settings = StavrophoraSettings()
    assert settings.mailto is None
    assert settings.user_agent.startswith("stavrophora/")


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("STAVROPHORA_MAILTO", "env@example.org")
    settings = StavrophoraSettings()
    assert settings.mailto == "env@example.org"


def test_settings_explicit_mailto():
    settings = StavrophoraSettings(mailto="explicit@example.org")
    assert settings.mailto == "explicit@example.org"


def test_get_settings_cached():
    first = get_settings()
    second = get_settings()
    assert first is second


def test_settings_env_prefix():
    assert StavrophoraSettings.model_config["env_prefix"] == "STAVROPHORA_"
