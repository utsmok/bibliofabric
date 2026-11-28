"""ISSN validation and normalization helpers.

The Portal routes require the hyphenated uppercase spelling; the compact
spelling answers 404 (verified 2026-11-27). The client therefore normalizes
every identifier with :func:`bibliofabric.ids.normalize_issn` and rejects
values that fail the check digit before a request is sent.
"""

from bibliofabric.exceptions import ConfigurationError
from bibliofabric.ids import normalize_issn

#: Length of an ISSN: seven stem digits plus the check digit.
ISSN_LENGTH = 8

#: Character weight for ISSN check digit computation: the first digit counts
#: 8, the last stem digit counts 2.
_WEIGHTS = range(8, 1, -1)


#: Modulus of the ISSN check digit computation.
ISSN_MODULUS = 11


def is_valid_issn(value: str) -> bool:
    """Return ``True`` when ``value`` is a syntactically valid ISSN.

    Valid means seven stem digits plus a check digit of ``0`` to ``9`` or
    ``X`` (case insensitive), with a check digit that matches the modulo 11
    computation of the stem.
    """
    compact = normalize_issn(value).replace("-", "")
    if len(compact) != ISSN_LENGTH or not compact[:7].isdigit():
        return False
    stem, check = compact[:7], compact[7]
    if check not in "0123456789X":
        return False
    total = sum(
        int(digit) * weight for digit, weight in zip(stem, _WEIGHTS, strict=True)
    )
    expected = (ISSN_MODULUS - total % ISSN_MODULUS) % ISSN_MODULUS
    expected_digit = "X" if expected == ISSN_MODULUS - 1 else str(expected)
    return check == expected_digit


def require_issn(value: str) -> str:
    """Return the hyphenated uppercase ISSN, or raise.

    The value must be a syntactically valid ISSN; a URL form such as
    ``https://portal.issn.org/resource/ISSN/0028-0836`` also works. Raises
    :class:`bibliofabric.exceptions.ConfigurationError` for anything else,
    because the Portal answers those with HTTP 400.
    """
    trimmed = value.strip()
    if "/" in trimmed:
        trimmed = trimmed.rstrip("/").rsplit("/", 1)[-1]
    normalized = normalize_issn(trimmed)
    if not is_valid_issn(normalized):
        raise ConfigurationError(
            f"{value!r} is not a valid ISSN (bad check digit or shape); "
            f"the Portal requires the hyphenated form, e.g. 0028-0836."
        )
    return normalized


__all__ = ["is_valid_issn", "require_issn"]
