"""Settings: defaults, environment prefix, cached loader (both variants)."""

from europaea import EuropaeaSettings, get_settings

PREFIX_VARS = [
    "EUROPAEA_MAX_REQUESTS_PER_SECOND",
    "EUROPAEA_MAX_CONCURRENCY",
    "EUROPAEA_TIMEOUT",
]


def test_defaults(monkeypatch, tmp_path):
    for name in PREFIX_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = EuropaeaSettings()
    assert settings.max_requests_per_second == 3.0
    assert settings.max_concurrency == 2
    assert settings.max_retries == 3
    assert settings.timeout >= 30.0


def test_environment_prefix(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EUROPAEA_MAX_REQUESTS_PER_SECOND", "2.5")
    monkeypatch.setenv("EUROPAEA_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("EUROPAEA_TIMEOUT", "45")
    settings = EuropaeaSettings()
    assert settings.max_requests_per_second == 2.5
    assert settings.max_concurrency == 1
    assert settings.timeout == 45.0


def test_unrelated_prefix_is_ignored(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EUROPAEAX_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("ALETHECA_MAX_CONCURRENCY", "1")
    assert EuropaeaSettings().max_concurrency == 2


def test_get_settings_is_cached(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EUROPAEA_MAX_CONCURRENCY", "2")
    get_settings.cache_clear()
    assert get_settings().max_concurrency == 2
    monkeypatch.setenv("EUROPAEA_MAX_CONCURRENCY", "3")
    assert get_settings().max_concurrency == 2
    get_settings.cache_clear()


def test_user_agent_names_the_package(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert EuropaeaSettings().effective_user_agent().startswith("europaea/")
