"""The ``{"value": ...}`` wrappers ORCID uses for text, numbers, and dates.

Almost every scalar in an ORCID document is wrapped as ``{"value": ...}``
with optional attributes such as ``transient``. Use the ``text`` property
(or the module-level :func:`text` helper) instead of walking dictionaries.
"""

from pydantic import BaseModel, ConfigDict


class TextValue(BaseModel):
    """A wrapped text value, for example ``{"value": "2020"}``."""

    value: str | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @property
    def text(self) -> str | None:
        """The unwrapped text, or ``None``."""
        return self.value


class IntValue(BaseModel):
    """A wrapped integer value, used for epoch-millisecond timestamps."""

    value: int | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @property
    def text(self) -> str | None:
        """The value as text, or ``None``."""
        return None if self.value is None else str(self.value)


def text(value: TextValue | IntValue | None) -> str | None:
    """Return the wrapped text of a ``value`` object, or ``None``.

    Works on any model with a ``text`` property, so callers never walk the
    wrapper dictionaries themselves.
    """
    if value is None:
        return None
    return value.text


__all__ = ["IntValue", "TextValue", "text"]
