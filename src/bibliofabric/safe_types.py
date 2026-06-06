"""Shared Pydantic annotated types for safe API field access.

- ``SafeList[T]`` — coerces ``None`` → ``[]``, filters null elements
- ``SafeStr`` — coerces ``None`` → ``""``

Every type uses ``BeforeValidator`` so coercion happens *before* Pydantic's
core validation. This means:

* ``model_validate({"field": null})`` → field is ``[]`` / ``""``
* ``model_validate({"field": [null, {...}]})`` → null elements stripped
* ``model_validate({})`` → ``default_factory`` / ``default`` kicks in
"""

from typing import Annotated, TypeVar

from pydantic import BeforeValidator

T = TypeVar("T")

SafeList = Annotated[
    list[T],
    BeforeValidator(lambda v: [] if v is None else [x for x in v if x is not None]),
]
"""Annotated type for list fields that coerce ``None`` → ``[]`` and strip null entries.

Expects ``v`` to be ``list | None``. If the API returns a non-iterable scalar
when a list is expected, the validator will still pass it through (let Pydantic
raise ``ValidationError`` naturally).

Usage::

    class Product(BaseModel):
        pids: SafeList[Pid] = Field(default_factory=list)
        keywords: SafeList[str] = Field(default_factory=list)

Iterable without guards::

    [pid.value for pid in product.pids]  # always works
"""

SafeStr = Annotated[str, BeforeValidator(lambda v: "" if v is None else v)]
"""Annotated type for string fields that coerce ``None`` → ``""``.

Usage::

    class Container(BaseModel):
        name: SafeStr = ""

Safe to call string methods without guards::

    product.title.upper()  # never crashes
"""
