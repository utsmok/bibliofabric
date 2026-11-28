"""Settings: defaults, environment prefix, cached loader (both variants)."""

from zenotheca import ZenothecaSettings, get_settings

PREFIX_VARS = [
    "ZENOTHECA_MAX_REQUESTS_PER_SECOND",
    "ZENOTHECA_MAX_CONCURRENCY",
    "ZENOTHECA_TIMEOUT",
]


def test_defaults(monkeypatch, tmp_path):
    for name in PREFIX_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = ZenothecaSettings()
    assert settings.max_requests_per_second == 2.0
    assert settings.max_concurrency == 5
    assert settings.max_retries == 3


def test_environment_prefix(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ZENOTHECA_MAX_REQUESTS_PER_SECOND", "1.0")
    monkeypatch.setenv("ZENOTHECA_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("ZENOTHECA_TIMEOUT", "12")
    settings = ZenothecaSettings()
    assert settings.max_requests_per_second == 1.0
    assert settings.max_concurrency == 1
    assert settings.timeout == 12.0


def test_unrelated_prefix_is_ignored(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ZENOTHECAX_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("ALETHECA_MAX_CONCURRENCY", "1")
    assert ZenothecaSettings().max_concurrency == 5


def test_get_settings_is_cached(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ZENOTHECA_MAX_CONCURRENCY", "2")
    get_settings.cache_clear()
    assert get_settings().max_concurrency == 2
    monkeypatch.setenv("ZENOTHECA_MAX_CONCURRENCY", "3")
    assert get_settings().max_concurrency == 2
    get_settings.cache_clear()


def test_user_agent_names_the_package(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert ZenothecaSettings().effective_user_agent().startswith("zenotheca/")
