"""Normalization of Zenodo identifiers found in the wild.

Zenodo record ids are numeric strings (``24378467``), concept ids are the
numeric ids of the version family (``6347574``), and community ids are
slugs (``ror-data``). Records, DOIs, and pages carry longer spellings of the
same ids; :func:`normalize_record_id` and :func:`normalize_community_slug`
reduce any of them to the bare value the API paths expect.
"""

from urllib.parse import urlsplit

from bibliofabric.exceptions import ConfigurationError

_ZENODO_HOSTS = frozenset({"zenodo.org", "www.zenodo.org"})


def normalize_record_id(value: str | int) -> str:
    """Return the bare numeric record or concept id behind ``value``.

    Accepts the bare id (``24378467``), a DOI
    (``10.5281/zenodo.24378467``), and Zenodo record URLs
    (``https://zenodo.org/records/24378467`` and the ``/api/records/`` and
    ``/record/`` variants). A value that does not resolve to a numeric id
    raises :class:`ConfigurationError`.
    """
    text = str(value).strip()
    if text.lower().startswith("10.5281/zenodo."):
        text = text.rsplit(".", 1)[-1]
    elif "://" in text:
        parts = urlsplit(text)
        if parts.hostname not in _ZENODO_HOSTS:
            raise ConfigurationError(
                f"Cannot read a Zenodo record id from {value!r}; pass the "
                "numeric id, a 10.5281/zenodo DOI, or a zenodo.org URL."
            )
        segments = [segment for segment in parts.path.split("/") if segment]
        if "records" not in segments and "record" not in segments:
            raise ConfigurationError(
                f"Cannot read a Zenodo record id from the path {parts.path!r}."
            )
        marker = "records" if "records" in segments else "record"
        text = segments[segments.index(marker) + 1]
    if not text.isdigit():
        raise ConfigurationError(
            f"{value!r} is not a Zenodo record or concept id (expected digits)."
        )
    return text


def normalize_community_slug(value: str) -> str:
    """Return the bare community slug behind ``value``.

    Accepts the bare slug (``ror-data``) and the community URL
    (``https://zenodo.org/communities/ror-data``).
    """
    text = value.strip()
    if "://" in text:
        parts = urlsplit(text)
        if parts.hostname not in _ZENODO_HOSTS:
            raise ConfigurationError(
                f"Cannot read a Zenodo community slug from {value!r}."
            )
        segments = [segment for segment in parts.path.split("/") if segment]
        if "communities" not in segments:
            raise ConfigurationError(
                f"Cannot read a Zenodo community slug from the path {parts.path!r}."
            )
        text = segments[segments.index("communities") + 1]
    if not text or "/" in text:
        raise ConfigurationError(f"{value!r} is not a Zenodo community slug.")
    return text


__all__ = ["normalize_community_slug", "normalize_record_id"]
