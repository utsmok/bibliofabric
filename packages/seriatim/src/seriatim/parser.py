"""Parsers for the JSON-LD record nodes of the ISSN Portal.

``parse_issn_record`` and ``parse_issn_l`` validate one JSON-LD node into
the typed models and keep the untouched node on the ``raw`` attribute.
"""

from typing import Any

from bibliofabric.exceptions import ConfigurationError, validate_model
from bibliofabric.ids import normalize_issn

from .models import IssnLRecord, SeriatimRecord


def parse_issn_record(node: Any) -> SeriatimRecord:
    """Validate one ``/resource/ISSN`` JSON-LD node into a typed record.

    The node must be a single JSON object (the Portal answers one node, not
    an ``@graph`` array). ``record.raw`` holds the untouched node.
    """
    record = _validate_node(node, SeriatimRecord)
    record.raw = dict(node)
    return record


def parse_issn_l(node: Any) -> IssnLRecord:
    """Validate one ``/resource/ISSN-L`` JSON-LD node into a typed record.

    ``record.raw`` holds the untouched node.
    """
    record = _validate_node(node, IssnLRecord)
    record.raw = dict(node)
    return record


def record_issn(record: SeriatimRecord) -> str:
    """Return the normalized ISSN of a record.

    Reads the ``#ISSN`` identifier node first and falls back to the
    ``identifier`` key, so cancelled records work too. Raises
    :class:`bibliofabric.exceptions.ConfigurationError` when the record
    carries no usable ISSN.
    """
    value = record.issn or record.identifier
    if not value:
        raise ConfigurationError(
            f"The record of {record.id or '<unknown>'} carries no ISSN value."
        )
    return normalize_issn(value)


def _validate_node[M: SeriatimRecord | IssnLRecord](node: Any, model: type[M]) -> M:
    """Validate one JSON-LD node against ``model``."""
    if not isinstance(node, dict):
        raise ConfigurationError(
            f"Expected one JSON-LD object for {model.__name__}, got "
            f"{type(node).__name__}."
        )
    return validate_model(model, node)


__all__ = ["parse_issn_l", "parse_issn_record", "record_issn"]
