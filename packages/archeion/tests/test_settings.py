"""Settings: defaults, environment prefix, cached loader (both variants)."""

from archeion import ArcheionSettings, get_settings

PREFIX_VARS = [
    "ARCHEION_MAX_REQUESTS_PER_SECOND",
    "ARCHEION_MAX_CONCURRENCY",
    "ARCHEION_TIMEOUT",
]


def test_defaults_follow_the_arxiv_terms_of_use(monkeypatch, tmp_path):
    for name in PREFIX_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = ArcheionSettings()
    assert settings.max_requests_per_second == 1 / 3
    assert settings.max_concurrency == 1


def test_environment_prefix(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ARCHEION_MAX_REQUESTS_PER_SECOND", "0.2")
    monkeypatch.setenv("ARCHEION_TIMEOUT", "12")
    settings = ArcheionSettings()
    assert settings.max_requests_per_second == 0.2
    assert settings.timeout == 12.0


def test_get_settings_is_cached(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    assert get_settings() is get_settings()
    get_settings.cache_clear()
