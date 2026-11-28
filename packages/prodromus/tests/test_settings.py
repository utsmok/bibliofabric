"""Settings: defaults, environment prefix, cached loader."""

from prodromus import ProdromusSettings, get_settings


def test_defaults(monkeypatch, tmp_path):
    for name in ("PRODROMUS_MAX_REQUESTS_PER_SECOND", "PRODROMUS_MAX_CONCURRENCY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = ProdromusSettings()
    assert settings.max_requests_per_second == 1.0
    assert settings.max_concurrency == 1


def test_environment_prefix(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PRODROMUS_MAX_REQUESTS_PER_SECOND", "0.5")
    assert ProdromusSettings().max_requests_per_second == 0.5


def test_get_settings_is_cached(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    assert get_settings() is get_settings()
    get_settings.cache_clear()
