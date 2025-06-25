# tests/conftest.py
import os

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# Useful for storing API keys locally for testing
load_dotenv()


@pytest.fixture(scope="session")
def api_token() -> str | None:
    """Fixture to provide the OpenAIRE API token from environment variables."""
    return os.getenv("AIRELOOM_OPENAIRE_API_TOKEN")
