"""Utility helpers for the bibliofabric framework."""

from __future__ import annotations

from typing import Any


def safe_dig(obj: Any, *path: str, default: Any = None) -> Any:
    """Safely traverse nested attribute/dict paths.

    Traverses a chain of attributes (on objects) or keys (on dicts).
    Returns ``default`` if any step fails (missing attribute/key, None value).

    Args:
        obj: Root object or dict.
        *path: Sequence of attribute/key names to traverse.
        default: Value to return on failure (default None).

    Returns:
        The value at the end of the path, or ``default``.

    Examples::

        safe_dig(
            product, "container", "name"
        )  # returns "" or the name
        safe_dig(
            product,
            "indicators",
            "citationImpact",
            "citationCount",
            default=0,
        )
    """
    current = obj
    for key in path:
        if current is None:
            return default
        if isinstance(current, dict):
            if key not in current:
                return default
            current = current[key]
        else:
            current = getattr(current, key, default)
            if current is default:
                return default
    return current


class DigMixin:
    """Mixin that adds a ``.dig()`` method to any Pydantic model.

    Usage::

        class MyModel(BaseModel, DigMixin): ...


        model.dig("container", "name")  # safe chained access
    """

    def dig(self, *path: str, default: Any = None) -> Any:
        """Safely traverse nested attributes.

        Args:
            *path: Attribute names to traverse.
            default: Value to return on failure.

        Returns:
            Value at path, or ``default``.
        """
        return safe_dig(self, *path, default=default)
