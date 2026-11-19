"""Annotated pydantic types for tolerant API field access.

``SafeStr`` coerces ``None`` to ``""``. ``SafeList`` coerces ``None`` to ``[]``,
strips null entries from lists, and turns a scalar string into a single-element
list instead of a character list. Coercion runs before pydantic validation, so
defaults still apply when the API omits the field.
"""

from collections.abc import Iterable
from typing import Annotated, Any, TypeVar

from pydantic import BeforeValidator

T = TypeVar("T")


def _safe_list_value(value: Any) -> Any:
    if value is None:
        return []
    if isinstance(value, str | bytes):
        return [value]
    if isinstance(value, dict) or not isinstance(value, Iterable):
        # Let pydantic raise a clear error for scalars that are not strings.
        return value
    return [item for item in value if item is not None]


def _safe_str_value(value: Any) -> Any:
    return "" if value is None else value


SafeList = Annotated[list[T], BeforeValidator(_safe_list_value)]
"""List field that coerces ``None`` to ``[]``, strips null entries, and wraps
scalar strings into ``[value]``."""

SafeStr = Annotated[str, BeforeValidator(_safe_str_value)]
"""String field that coerces ``None`` to ``""``."""
