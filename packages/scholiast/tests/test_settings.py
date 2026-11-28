"""Settings: defaults, environment prefix, key handling, cached loader."""

from scholiast import ScholiastSettings, get_settings

PREFIX_VARS = [
    "SCHOLIAST_API_KEY",
    "SCHOLIAST_MAX_REQUESTS_PER_SECOND",
    "SCHOLIAST_MAX_CONCURRENCY",
    "SCHOLIAST_TIMEOUT",
]


def test_defaults(monkeypatch, tmp_path):
    for name in PREFIX_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = ScholiastSettings()
    assert settings.max_requests_per_second == 1.0
    assert settings.max_concurrency == 1
    assert settings.max_retries == 3
    assert settings.api_key is None


def test_environment_prefix(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SCHOLIAST_MAX_REQUESTS_PER_SECOND", "2.5")
    monkeypatch.setenv("SCHOLIAST_MAX_CONCURRENCY", "4")
    monkeypatch.setenv("SCHOLIAST_TIMEOUT", "12")
    monkeypatch.setenv("SCHOLIAST_API_KEY", "secret-value")
    settings = ScholiastSettings()
    assert settings.max_requests_per_second == 2.5
    assert settings.max_concurrency == 4
    assert settings.timeout == 12.0
    assert settings.api_key is not None
    assert settings.api_key.get_secret_value() == "secret-value"


def test_unrelated_prefix_is_ignored(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SCHOLIASTX_MAX_CONCURRENCY", "9")
    monkeypatch.setenv("ALETHECA_MAX_CONCURRENCY", "9")
    assert ScholiastSettings().max_concurrency == 1


def test_get_settings_is_cached(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SCHOLIAST_MAX_CONCURRENCY", "2")
    get_settings.cache_clear()
    assert get_settings().max_concurrency == 2
    monkeypatch.setenv("SCHOLIAST_MAX_CONCURRENCY", "3")
    assert get_settings().max_concurrency == 2
    get_settings.cache_clear()


def test_user_agent_names_the_package(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert ScholiastSettings().effective_user_agent().startswith("scholiast/")


def test_secret_is_not_exposed_in_repr(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SCHOLIAST_API_KEY", "secret-value")
    settings = ScholiastSettings()
    assert "secret-value" not in repr(settings)
    assert "secret-value" not in str(settings)
