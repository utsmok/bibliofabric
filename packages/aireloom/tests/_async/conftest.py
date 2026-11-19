"""Fake HTTP plumbing for the AIREloom test suite.

``AireloomClient`` is built against test base URLs; pytest-httpx intercepts
every request it makes. ``load`` serves trimmed real payloads from
``tests/fixtures/``.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from aireloom import AireloomClient, AireloomSettings

GRAPH_URL = "https://graph.test"
SCHOLIX_URL = "https://scholix.test"
TOKEN_URL = "https://auth.test/realms/openaire/protocol/openid-connect/token"

FIXTURES = Path(__file__).parent.parent / "fixtures"


def load(name: str) -> Any:
    """Return one trimmed real payload from the fixtures directory."""
    return json.loads((FIXTURES / name).read_text())


def make_settings(**overrides: Any) -> AireloomSettings:
    """Settings for tests: no throttling, no credentials unless passed in."""
    defaults: dict[str, Any] = {
        "base_url": GRAPH_URL,
        "scholix_base_url": SCHOLIX_URL,
        "token_url": TOKEN_URL,
        "mailto": None,
        "openaire_client_id": None,
        "openaire_client_secret": None,
        "max_requests_per_second": None,
        "scholix_max_requests_per_second": None,
    }
    defaults.update(overrides)
    return AireloomSettings(**defaults)


@pytest.fixture
def settings() -> AireloomSettings:
    return make_settings()


@pytest.fixture
async def client(settings: AireloomSettings):
    """Anonymous client whose HTTP traffic pytest-httpx captures."""
    async with AireloomClient(settings=settings) as aireloom:
        yield aireloom


def json_response(payload: Any) -> dict[str, Any]:
    """``add_response(**json_response(x))`` mocks a 200 JSON reply."""
    return {"json": payload}


def params_of(request: Any) -> dict[str, str]:
    """Query parameters of a captured request as a plain dict."""
    return dict(request.url.params)
