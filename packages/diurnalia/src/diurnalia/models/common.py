"""Pydantic models shared by DOAJ journal and article records."""

from bibliofabric import SafeStr
from pydantic import BaseModel, ConfigDict


class Admin(BaseModel):
    """Flags that the DOAJ editorial team sets on a record.

    A search result carries ``ticked`` or nothing. The record routes add
    ``in_doaj``, and an article record also carries ``publisher_record_id``.
    """

    in_doaj: bool | None = None
    publisher_record_id: SafeStr | None = None
    sealed: bool | None = None
    ticked: bool | None = None

    model_config = ConfigDict(extra="allow")


class Subject(BaseModel):
    """One classification entry of a journal or article.

    ``scheme`` is ``LCC`` in current records; ``code`` and ``term`` carry
    the class code and its name.
    """

    scheme: SafeStr | None = None
    code: SafeStr | None = None
    term: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


__all__ = ["Admin", "Subject"]
