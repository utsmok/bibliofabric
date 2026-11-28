"""The Handle.net record behind a DOI, as served by ``/api/handles/``."""

from pydantic import BaseModel, ConfigDict


class HandleAdminValue(BaseModel):
    """The ``value`` of an ``HS_ADMIN`` entry: the administrator handle."""

    handle: str
    index: int
    permissions: str | None = None

    model_config = ConfigDict(extra="allow")


class HandleValueData(BaseModel):
    """The ``data`` object of one handle value.

    ``format`` is one of ``string``, ``base64``, ``hex``, ``admin``,
    ``vlist``, or ``site``. ``value`` is the decoded string for the first
    three formats, an :class:`HandleAdminValue` for ``admin``, and the raw
    extra fields carry the rarer ``vlist`` and ``site`` shapes.
    """

    format: str
    value: str | HandleAdminValue | None = None

    model_config = ConfigDict(extra="allow")


class HandleValue(BaseModel):
    """One entry of a handle record.

    ``type`` is ``URL`` for the landing page link, ``HS_ADMIN`` for the
    administrator entry, ``HS_ALIAS`` for an alias, or a numeric type such
    as ``700050``. ``ttl`` is the cache time in seconds; the timestamp is an
    ISO 8601 string.
    """

    index: int
    type: str
    data: HandleValueData
    ttl: int | str | None = None
    timestamp: str | None = None

    model_config = ConfigDict(extra="allow")


class HandleRecord(BaseModel):
    """The JSON object of ``GET /api/handles/{doi}``.

    ``responseCode`` 1 means success; 100 means handle not found (then the
    proxy answers HTTP 404 and ``message`` explains which part failed). 200
    means values not found, which arrives as HTTP 200 with no ``values``.
    """

    responseCode: int
    handle: str | None = None
    values: list[HandleValue] = []
    message: str | None = None

    model_config = ConfigDict(extra="allow")
