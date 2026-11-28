"""Settings: defaults, environment prefix, rate classes, cached loader."""

from quiddita import QuidditaSettings, get_settings

PREFIX_VARS = [
    "QUIDDITA_MAX_REQUESTS_PER_SECOND",
    "QUIDDITA_MAX_CONCURRENCY",
    "QUIDDITA_TIMEOUT",
]


def test_defaults(monkeypatch, tmp_path):
    for name in PREFIX_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = QuidditaSettings()
    assert settings.max_requests_per_second == 2.0
    assert settings.max_concurrency == 1
    assert settings.rate_limits == {"sparql": 0.5}
    assert settings.max_retries == 3


def test_environment_prefix(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QUIDDITA_MAX_REQUESTS_PER_SECOND", "1.0")
    monkeypatch.setenv("QUIDDITA_MAX_CONCURRENCY", "2")
    monkeypatch.setenv("QUIDDITA_TIMEOUT", "12")
    settings = QuidditaSettings()
    assert settings.max_requests_per_second == 1.0
    assert settings.max_concurrency == 2
    assert settings.timeout == 12.0


def test_sparql_rate_class_override():
    settings = QuidditaSettings(_env_file=None, rate_limits={"sparql": 0.2})
    assert settings.rate_limits == {"sparql": 0.2}


def test_unrelated_prefix_is_ignored(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QUIDDITAX_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("ALETHECA_MAX_CONCURRENCY", "1")
    assert QuidditaSettings().max_concurrency == 1


def test_get_settings_is_cached(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QUIDDITA_MAX_CONCURRENCY", "2")
    get_settings.cache_clear()
    assert get_settings().max_concurrency == 2
    monkeypatch.setenv("QUIDDITA_MAX_CONCURRENCY", "3")
    assert get_settings().max_concurrency == 2
    get_settings.cache_clear()


def test_user_agent_names_the_package(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert QuidditaSettings().effective_user_agent().startswith("quiddita/")
