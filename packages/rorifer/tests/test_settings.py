"""Settings: defaults, environment prefix, cached loader (both variants)."""

import pytest
from rorifer import RoriferSettings, get_settings

PREFIX_VARS = [
    "RORIFER_MAX_REQUESTS_PER_SECOND",
    "RORIFER_MAX_CONCURRENCY",
    "RORIFER_RATE_LIMITS",
    "RORIFER_TIMEOUT",
]


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch, tmp_path):
    """Settings tests read neither the developer's shell nor a ``.env`` file."""
    for name in PREFIX_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)


def test_defaults():
    settings = RoriferSettings()
    assert settings.max_requests_per_second == 6.0
    assert settings.max_concurrency == 5
    assert settings.max_retries == 3
    assert settings.rate_limits == {"zenodo": 0.5}


def test_explicit_pace_drops_the_per_class_limits():
    """A caller who sets the overall pace alone means it for every request class."""
    settings = RoriferSettings(_env_file=None, max_requests_per_second=1_000_000.0)
    assert settings.rate_limits == {}
    assert RoriferSettings(_env_file=None).rate_limits == {"zenodo": 0.5}
    explicit = RoriferSettings(
        _env_file=None, max_requests_per_second=None, rate_limits={"zenodo": None}
    )
    assert explicit.max_requests_per_second is None
    assert explicit.rate_limits == {"zenodo": None}


def test_environment_prefix(monkeypatch):
    monkeypatch.setenv("RORIFER_MAX_REQUESTS_PER_SECOND", "2.5")
    monkeypatch.setenv("RORIFER_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("RORIFER_TIMEOUT", "12")
    settings = RoriferSettings()
    assert settings.max_requests_per_second == 2.5
    assert settings.max_concurrency == 1
    assert settings.timeout == 12.0
    assert settings.rate_limits == {}


def test_environment_can_set_the_rate_classes(monkeypatch):
    monkeypatch.setenv("RORIFER_MAX_REQUESTS_PER_SECOND", "2.5")
    monkeypatch.setenv("RORIFER_RATE_LIMITS", '{"zenodo": 0.25}')
    assert RoriferSettings().rate_limits == {"zenodo": 0.25}


def test_unrelated_prefix_is_ignored(monkeypatch):
    monkeypatch.setenv("RORIFERX_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("ALETHECA_MAX_CONCURRENCY", "1")
    assert RoriferSettings().max_concurrency == 5


def test_get_settings_is_cached(monkeypatch):
    monkeypatch.setenv("RORIFER_MAX_CONCURRENCY", "2")
    get_settings.cache_clear()
    assert get_settings().max_concurrency == 2
    monkeypatch.setenv("RORIFER_MAX_CONCURRENCY", "3")
    assert get_settings().max_concurrency == 2
    get_settings.cache_clear()


def test_user_agent_names_the_package():
    assert RoriferSettings().effective_user_agent().startswith("rorifer/")
