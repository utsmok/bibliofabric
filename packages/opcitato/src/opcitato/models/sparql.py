"""Model of the SPARQL 1.1 JSON results of the two SPARQL endpoints."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SparqlTerm(BaseModel):
    """One typed term of a result row.

    ``type`` is ``uri``, ``literal``, or ``bnode``. A literal can carry a
    ``datatype`` (an XSD datatype IRI) or a language tag (``xml:lang`` in
    the payload, :attr:`xml_lang` on the model).
    """

    type: str
    value: str
    datatype: str | None = None
    xml_lang: str | None = Field(default=None, alias="xml:lang")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


SparqlBinding = dict[str, SparqlTerm]
"""One result row: variable name to typed term."""


class SparqlHead(BaseModel):
    """The ``head`` member: the result variables."""

    vars: list[str] = []

    model_config = ConfigDict(extra="allow")


class SparqlResults(BaseModel):
    """The ``results`` member with its ``bindings`` rows."""

    bindings: list[SparqlBinding]

    model_config = ConfigDict(extra="allow")


class SparqlResult(BaseModel):
    """A SPARQL 1.1 JSON result as the endpoints answer ``sparql-results+json``.

    A SELECT answer carries ``head`` and ``results``. An ASK answer carries
    ``head`` and ``boolean``. OpenCitations adds a ``meta`` object with the
    query time (``query-time-ms``) and the number of rows
    (``result-size-total``).
    """

    head: SparqlHead
    results: SparqlResults | None = None
    boolean: bool | None = None
    meta: dict[str, Any] = {}

    model_config = ConfigDict(extra="allow")

    def rows(self) -> list[dict[str, str]]:
        """Return the bindings as plain ``variable -> value`` strings.

        An ASK answer has no bindings and returns ``[]``; read
        :attr:`boolean` for it.
        """
        if self.results is None:
            return []
        return [
            {variable: term.value for variable, term in binding.items()}
            for binding in self.results.bindings
        ]


__all__ = [
    "SparqlBinding",
    "SparqlHead",
    "SparqlResult",
    "SparqlResults",
    "SparqlTerm",
]
