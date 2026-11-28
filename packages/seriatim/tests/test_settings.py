"""Settings: defaults, environment prefix, cached loader."""

from seriatim import SeriatimSettings, get_settings

PREFIX_VARS = [
    "SERIATIM_MAX_REQUESTS_PER_SECOND",
    "SERIATIM_MAX_CONCURRENCY",
    "SERIATIM_TIMEOUT",
]


def test_defaults(monkeypatch, tmp_path):
    for name in PREFIX_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = SeriatimSettings(_env_file=None)
    assert settings.max_requests_per_second == 1.0
    assert settings.max_concurrency == 2
    assert settings.max_retries == 3
    assert settings.timeout == 30.0


def test_environment_prefix(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SERIATIM_MAX_REQUESTS_PER_SECOND", "0.5")
    monkeypatch.setenv("SERIATIM_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("SERIATIM_TIMEOUT", "12")
    settings = SeriatimSettings(_env_file=None)
    assert settings.max_requests_per_second == 0.5
    assert settings.max_concurrency == 1
    assert settings.timeout == 12.0


def test_unrelated_prefix_is_ignored(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SERIATIMX_MAX_CONCURRENCY", "1")
    monkeypatch.setenv("ALETHECA_MAX_CONCURRENCY", "1")
    assert SeriatimSettings(_env_file=None).max_concurrency == 2


def test_get_settings_is_cached(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SERIATIM_MAX_CONCURRENCY", "3")
    get_settings.cache_clear()
    assert get_settings().max_concurrency == 3
    monkeypatch.setenv("SERIATIM_MAX_CONCURRENCY", "4")
    assert get_settings().max_concurrency == 3
    get_settings.cache_clear()


def test_user_agent_names_the_package(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert (
        SeriatimSettings(_env_file=None).effective_user_agent().startswith("seriatim/")
    )
