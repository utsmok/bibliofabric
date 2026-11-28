"""Pydantic models for Semantic Scholar patents."""

from typing import Any

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict


class Patent(BaseModel):
    """A patent record from the Academic Graph patent routes.

    Like papers, patents answer ``ucid`` (plus ``title`` on some routes)
    even without ``fields``; the other fields appear only when asked for
    in ``fields``. Party names (``inventors``, ``assignees``,
    ``applicants``) are free-form entries the API returns as strings or
    objects depending on the record.
    """

    ucid: SafeStr | None = None
    preferredUcid: SafeStr | None = None
    title: SafeStr | None = None
    abstract: SafeStr | None = None
    briefSummary: SafeStr | None = None
    corpusId: int | None = None
    docNumber: SafeStr | None = None
    docType: SafeStr | None = None
    kind: SafeStr | None = None
    office: SafeStr | None = None
    applicationKey: SafeStr | None = None
    applicationNumber: SafeStr | None = None
    applicationUcids: SafeList[str] = []
    assignees: SafeList[Any] = []
    applicants: SafeList[Any] = []
    inventors: SafeList[Any] = []
    inventorCountries: SafeList[str] = []
    cpcCodes: SafeList[str] = []
    claims: SafeList[Any] = []
    claimCount: int | None = None
    citedUcids: SafeList[str] = []
    citedApplicationCount: int | None = None
    citedForeignCount: int | None = None
    citedNplCount: int | None = None
    citedNplResolvedCount: int | None = None
    citedPaperCorpusIds: SafeList[int] = []
    citedPatentCount: int | None = None
    filingDate: SafeStr | None = None
    filingYear: int | None = None
    publicationDate: SafeStr | None = None
    publicationYear: int | None = None
    indexedAt: SafeStr | None = None
    source: SafeStr | None = None
    specificationChars: int | None = None
    stage: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class PatentCitations(BaseModel):
    """The envelope of ``/patent/outbound-citations/{paper_id}``.

    ``data`` holds the citing patents; ``citingPaperInfo`` holds the
    source paper.
    """

    data: SafeList[Patent] = []
    citingPaperInfo: dict | None = None
    next: int | None = None
    offset: int | None = None

    model_config = ConfigDict(extra="allow")


__all__ = ["Patent", "PatentCitations"]
