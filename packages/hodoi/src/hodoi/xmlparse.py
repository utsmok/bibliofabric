"""Readers for the XML answers of the DOI System proxy."""

from xml.etree import ElementTree

from bibliofabric import validate_model
from bibliofabric.exceptions import ConfigurationError

from .models import RedirectLocation


def parse_locations(text: str) -> list[RedirectLocation]:
    """Parse the XML of ``?action=showurls`` into :class:`RedirectLocation`.

    The proxy answers ``<locations><location ... /></locations>`` with every
    URL it could redirect to. Raises :class:`ConfigurationError` for a body
    that is not that document, and :class:`ValidationError` for a location
    without an ``href``.
    """
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as error:
        raise ConfigurationError(
            f"The proxy's redirect listing is not well-formed XML: {error}."
        ) from error
    if root.tag != "locations":
        raise ConfigurationError(
            f"The proxy's redirect listing has root {root.tag!r} instead of "
            "'locations'."
        )
    return [
        validate_model(RedirectLocation, dict(element.attrib))
        for element in root.iter("location")
    ]


__all__ = ["parse_locations"]
