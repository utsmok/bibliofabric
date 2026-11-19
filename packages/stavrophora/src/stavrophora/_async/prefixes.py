"""Prefixes resource: ``/prefixes/{prefix}`` and its works scope.

Crossref serves no ``/prefixes`` list route (verified live: 404); prefixes
are only addressable individually.
"""

from typing import Any
from urllib.parse import quote

from bibliofabric.exceptions import ConfigurationError

from ..models import Prefix
from .dialect import CrossrefResourceClient
from .works import ScopedWorksResource


class PrefixesResource(CrossrefResourceClient[Prefix]):
    """Typed client for the Crossref ``/prefixes/{prefix}`` route."""

    path = "prefixes"
    model = Prefix

    def works(self, prefix: str | int) -> ScopedWorksResource:
        """Return a works client bound to ``prefixes/{prefix}/works``."""
        prefix = quote(str(prefix).strip(), safe="")
        return ScopedWorksResource(self._client, path=f"prefixes/{prefix}/works")

    def search(self, *_args: Any, **_kwargs: Any) -> Any:
        """Not supported: Crossref serves no ``/prefixes`` list route."""
        raise ConfigurationError(
            "Crossref has no /prefixes list route; use get(prefix) or works(prefix)."
        )

    def count(self, *_args: Any, **_kwargs: Any) -> Any:
        """Not supported: Crossref serves no ``/prefixes`` list route."""
        raise ConfigurationError(
            "Crossref has no /prefixes list route; use get(prefix) or works(prefix)."
        )

    def iterate(self, *_args: Any, **_kwargs: Any) -> Any:
        """Not supported: Crossref serves no ``/prefixes`` list route."""
        raise ConfigurationError(
            "Crossref has no /prefixes list route; use get(prefix) or works(prefix)."
        )
