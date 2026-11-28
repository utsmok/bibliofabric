"""Typed models for the OAI-PMH answers of Zenodo.

The metadata payload of an OAI record depends on the metadata prefix
(``oai_dc``, ``marcxml``, ...), so :attr:`OaiRecord.metadata` keeps the raw
XML string of the metadata element plus the prefix and its namespace;
modeling every metadata schema is out of scope.
"""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel


class OaiResumptionToken(BaseModel):
    """An OAI-PMH resumption token with its attributes."""

    token: str = ""
    expiration_date: str | None = None
    complete_list_size: int | None = None
    cursor: int | None = None

    model_config = {"extra": "allow"}


class OaiHeader(BaseModel):
    """The header of an OAI record (identifier, datestamp, sets)."""

    identifier: SafeStr | None = None
    datestamp: SafeStr | None = None
    set_spec: SafeList[str] = []
    status: str | None = None

    model_config = {"extra": "allow"}

    @property
    def deleted(self) -> bool:
        """Whether the record carries ``status="deleted"``."""
        return self.status == "deleted"


class OaiRecord(BaseModel):
    """One OAI-PMH record.

    ``metadata`` is the raw XML string of the metadata element, tagged with
    the ``metadata_prefix`` that produced it and the namespace URI of that
    prefix. ``about`` holds the raw XML strings of the ``about`` elements.
    """

    header: OaiHeader | None = None
    metadata: str | None = None
    about: SafeList[str] = []
    metadata_prefix: str | None = None
    metadata_namespace: str | None = None

    model_config = {"extra": "allow"}


class OaiMetadataFormat(BaseModel):
    """One metadata prefix offered by the repository."""

    metadata_prefix: SafeStr | None = None
    schema_url: SafeStr | None = None
    metadata_namespace: SafeStr | None = None

    model_config = {"extra": "allow"}


class OaiSet(BaseModel):
    """One OAI-PMH set (``setSpec``, ``setName``, optional description)."""

    set_spec: SafeStr | None = None
    set_name: SafeStr | None = None
    set_description: str | None = None

    model_config = {"extra": "allow"}


class OaiIdentify(BaseModel):
    """The ``Identify`` answer of the repository."""

    repository_name: SafeStr | None = None
    base_url: SafeStr | None = None
    protocol_version: SafeStr | None = None
    earliest_datestamp: SafeStr | None = None
    deleted_record: SafeStr | None = None
    granularity: SafeStr | None = None
    admin_emails: SafeList[str] = []

    model_config = {"extra": "allow"}


class OaiRequest(BaseModel):
    """The ``request`` element of an answer, with its query attributes."""

    url: SafeStr | None = None
    params: dict[str, str] = {}

    model_config = {"extra": "allow"}


class OaiError(BaseModel):
    """An OAI-PMH error (``code`` plus optional text)."""

    code: SafeStr | None = None
    message: str | None = None

    model_config = {"extra": "allow"}


class OaiFormats(BaseModel):
    """The answer of ``ListMetadataFormats``."""

    formats: list[OaiMetadataFormat] = []
    request: OaiRequest | None = None
    response_date: str | None = None

    model_config = {"extra": "allow"}


class OaiIdentifyResponse(BaseModel):
    """The answer of ``Identify``."""

    identify: OaiIdentify | None = None
    request: OaiRequest | None = None
    response_date: str | None = None

    model_config = {"extra": "allow"}


class OaiSets(BaseModel):
    """One page of ``ListSets``."""

    sets: list[OaiSet] = []
    resumption_token: OaiResumptionToken | None = None
    request: OaiRequest | None = None
    response_date: str | None = None

    model_config = {"extra": "allow"}


class OaiIdentifiers(BaseModel):
    """One page of ``ListIdentifiers``."""

    headers: list[OaiHeader] = []
    resumption_token: OaiResumptionToken | None = None
    request: OaiRequest | None = None
    response_date: str | None = None

    model_config = {"extra": "allow"}


class OaiRecords(BaseModel):
    """One page of ``ListRecords``."""

    records: list[OaiRecord] = []
    resumption_token: OaiResumptionToken | None = None
    request: OaiRequest | None = None
    response_date: str | None = None

    model_config = {"extra": "allow"}


class OaiRecordResponse(BaseModel):
    """The answer of ``GetRecord``."""

    record: OaiRecord | None = None
    request: OaiRequest | None = None
    response_date: str | None = None

    model_config = {"extra": "allow"}


__all__ = [
    "OaiError",
    "OaiFormats",
    "OaiHeader",
    "OaiIdentify",
    "OaiIdentifyResponse",
    "OaiIdentifiers",
    "OaiMetadataFormat",
    "OaiRecord",
    "OaiRecordResponse",
    "OaiRecords",
    "OaiRequest",
    "OaiResumptionToken",
    "OaiSets",
]
