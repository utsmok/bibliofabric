"""Models of the count rows."""

from bibliofabric import SafeStr
from pydantic import BaseModel, ConfigDict, field_validator


class Count(BaseModel):
    """The one row a count operation returns.

    The JSON representation carries the number as a string
    (``{"count": "1806"}``) even though the documentation types it as int;
    :attr:`count` coerces it.
    """

    count: int
    label: SafeStr = ""

    model_config = ConfigDict(extra="allow")

    @field_validator("count", mode="before")
    @classmethod
    def _coerce_count(cls, value: object) -> object:
        """Convert the documented-as-int but returned-as-string count."""
        if isinstance(value, str):
            return int(value)
        return value


__all__ = ["Count"]
