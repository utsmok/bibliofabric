"""Settings: defaults, environment prefix, cached loader."""

from opcitato import OpcitatoSettings, get_settings

PREFIX_VARS = [
    "OPCITATO_MAX_REQUESTS_PER_SECOND",
    "OPCITATO_MAX_CONCURRENCY",
    "OPCITATO_TIMEOUT",
]


def test_defaults(monkeypatch, tmp_path):
    for name in PREFIX_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = OpcitatoSettings()
    assert settings.max_requests_per_second == 3.0
    assert settings.max_concurrency == 3
    assert settings.max_retries == 3


def test_environment_prefix(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPCITATO_MAX_REQUESTS_PER_SECOND", "1.5")
    monkeypatch.setenv("OPCITATO_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("OPCITATO_TIMEOUT", "12")
    settings = OpcitatoSettings()
    assert settings.max_requests_per_second == 1.5
    assert settings.max_concurrency == 1
    assert settings.timeout == 12.0


def test_unrelated_prefix_is_ignored(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPCITATOX_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("ALETHECA_MAX_CONCURRENCY", "1")
    assert OpcitatoSettings().max_concurrency == 3


def test_get_settings_is_cached(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPCITATO_MAX_CONCURRENCY", "2")
    get_settings.cache_clear()
    assert get_settings().max_concurrency == 2
    monkeypatch.setenv("OPCITATO_MAX_CONCURRENCY", "3")
    assert get_settings().max_concurrency == 2
    get_settings.cache_clear()


def test_user_agent_names_the_package(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert OpcitatoSettings().effective_user_agent().startswith("opcitato/")
