"""Internal redaction helpers for logs and exception messages."""

import re
from collections.abc import Mapping

_SENSITIVE_QUERY_PARAMETER = re.compile(
    r"([?&](?:access[_-]?token|api[_-]?key|client[_-]?secret|"
    r"password|secret|token|key|sig|signature)=)([^&#\s]*)",
    re.IGNORECASE,
)

_SENSITIVE_HEADER_MARKERS = ("authorization", "token", "key", "secret", "cookie")

__all__ = ["sanitize_headers", "sanitize_url"]


def sanitize_url(url: object) -> str:
    """Redact credential query parameters from a URL before it is logged."""
    return _SENSITIVE_QUERY_PARAMETER.sub(r"\1***", str(url))


def sanitize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Return a copy of ``headers`` with credential values replaced by ``***``.

    ``mailto`` and other contact parameters are not considered secrets and are
    left in place.
    """
    redacted: dict[str, str] = {}
    for name, value in headers.items():
        lowered = name.lower()
        redacted[name] = (
            "***"
            if any(marker in lowered for marker in _SENSITIVE_HEADER_MARKERS)
            else value
        )
    return redacted
