"""Settings: defaults, environment prefix, cached loader."""

from hodoi import HodoiSettings, get_settings

PREFIX_VARS = [
    "HODOI_MAX_REQUESTS_PER_SECOND",
    "HODOI_MAX_CONCURRENCY",
    "HODOI_TIMEOUT",
    "HODOI_FOLLOW_REDIRECTS",
]


def test_defaults(monkeypatch, tmp_path):
    for name in PREFIX_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = HodoiSettings()
    assert settings.max_requests_per_second == 2.0
    assert settings.max_concurrency == 2
    assert settings.timeout == 60.0
    assert settings.max_retries == 3
    assert settings.follow_redirects is False


def test_environment_prefix(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HODOI_MAX_REQUESTS_PER_SECOND", "1")
    monkeypatch.setenv("HODOI_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("HODOI_TIMEOUT", "90")
    monkeypatch.setenv("HODOI_FOLLOW_REDIRECTS", "true")
    settings = HodoiSettings()
    assert settings.max_requests_per_second == 1.0
    assert settings.max_concurrency == 1
    assert settings.timeout == 90.0
    assert settings.follow_redirects is True


def test_unrelated_prefix_is_ignored(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HODOIX_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("ALETHECA_MAX_CONCURRENCY", "1")
    assert HodoiSettings().max_concurrency == 2


def test_get_settings_is_cached(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HODOI_MAX_CONCURRENCY", "3")
    get_settings.cache_clear()
    assert get_settings().max_concurrency == 3
    monkeypatch.setenv("HODOI_MAX_CONCURRENCY", "4")
    assert get_settings().max_concurrency == 3
    get_settings.cache_clear()


def test_user_agent_names_the_package(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert HodoiSettings().effective_user_agent().startswith("hodoi/")
