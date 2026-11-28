"""Settings: defaults, environment prefix, cached loader (both variants)."""

from orchis import OrchisSettings, get_settings

PREFIX_VARS = [
    "ORCHIS_MAX_REQUESTS_PER_SECOND",
    "ORCHIS_MAX_CONCURRENCY",
    "ORCHIS_TIMEOUT",
    "ORCHIS_ACCESS_TOKEN",
]


def test_defaults(monkeypatch, tmp_path):
    for name in PREFIX_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = OrchisSettings()
    assert settings.max_requests_per_second == 4.0
    assert settings.max_concurrency == 4
    assert settings.max_retries == 3
    assert settings.access_token is None


def test_environment_prefix(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ORCHIS_MAX_REQUESTS_PER_SECOND", "2.5")
    monkeypatch.setenv("ORCHIS_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("ORCHIS_TIMEOUT", "12")
    monkeypatch.setenv("ORCHIS_ACCESS_TOKEN", "token-from-env")
    settings = OrchisSettings()
    assert settings.max_requests_per_second == 2.5
    assert settings.max_concurrency == 1
    assert settings.timeout == 12.0
    assert settings.access_token == "token-from-env"


def test_unrelated_prefix_is_ignored(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ORCHISX_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("ALETHECA_MAX_CONCURRENCY", "1")
    assert OrchisSettings().max_concurrency == 4


def test_get_settings_is_cached(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ORCHIS_MAX_CONCURRENCY", "2")
    get_settings.cache_clear()
    assert get_settings().max_concurrency == 2
    monkeypatch.setenv("ORCHIS_MAX_CONCURRENCY", "3")
    assert get_settings().max_concurrency == 2
    get_settings.cache_clear()


def test_user_agent_names_the_package(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert OrchisSettings().effective_user_agent().startswith("orchis/")
