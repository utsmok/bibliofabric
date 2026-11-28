"""The optional API token: settings plumbing, bearer header, page size cap."""

from zenotheca import ZenothecaSettings


def test_token_setting_loads_from_environment(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ZENOTHECA_API_TOKEN", "secret-value")
    settings = ZenothecaSettings()
    assert settings.api_token == "secret-value"


def test_token_is_hidden_from_repr(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ZENOTHECA_API_TOKEN", "secret-value")
    settings = ZenothecaSettings()
    assert "secret-value" not in repr(settings)


def test_token_is_unset_by_default(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ZENOTHECA_API_TOKEN", raising=False)
    assert ZenothecaSettings().api_token is None
