"""Models for the SPARQL 1.1 JSON results of the query service."""

from pydantic import BaseModel, ConfigDict


class _SparqlModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class SparqlBindingValue(_SparqlModel):
    """One typed term of a result row.

    ``type`` is one of ``uri``, ``literal``, ``bnode`` (SPARQL 1.1 JSON),
    plus the Wikidata extensions ``literal-ext`` and ``unknown``. Literal
    terms carry ``xml:lang`` for language-tagged literals and ``datatype``
    (an XSD datatype IRI) for typed ones.
    """

    type: str
    value: str
    xml_lang: str | None = None
    datatype: str | None = None


SparqlBinding = dict[str, SparqlBindingValue]
"""One result row: variable name to typed term."""


class SparqlResults(_SparqlModel):
    """The ``results`` member with its ``bindings`` rows."""

    bindings: list[SparqlBinding] = []


class SparqlHead(_SparqlModel):
    """The ``head`` member with the result variables."""

    vars: list[str] = []


class SparqlResult(_SparqlModel):
    """A typed SPARQL 1.1 JSON result as the query service answers ``format=json``."""

    head: SparqlHead
    results: SparqlResults

    def rows(self) -> list[dict[str, str]]:
        """Return the bindings as plain ``variable -> value`` strings."""
        return [
            {variable: term.value for variable, term in binding.items()}
            for binding in self.results.bindings
        ]


__all__ = [
    "SparqlBinding",
    "SparqlBindingValue",
    "SparqlHead",
    "SparqlResult",
    "SparqlResults",
]
