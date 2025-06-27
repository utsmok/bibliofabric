# aireloom/resources/base_client.py
"""Defines the base class for all OpenAIRE API resource clients in the aireloom library."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aireloom.client import AireloomClient


class BaseResourceClient:
    """
    Base class for all resource clients.
    """

    def __init__(self, api_client: "AireloomClient"):
        """
        Initialize the base resource client.

        Args:
            api_client: An instance of AireloomClient.
        """
        self._api_client = api_client
